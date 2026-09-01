import os
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas
from ..database import get_db
from ..gst_utils import determine_tax_type, state_name_from_code, extract_state_code
from ..invoice_numbering import get_next_invoice_number
from ..pdf_generator import generate_domestic_invoice_pdf, generate_export_invoice_pdf, CURRENCY_INFO

router = APIRouter(prefix="/api/invoices", tags=["invoices"])

GENERATED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "generated_invoices")
os.makedirs(GENERATED_DIR, exist_ok=True)


def _get_company(db: Session) -> models.Company:
    company = db.query(models.Company).filter_by(tenant_id="default").first()
    if not company:
        raise HTTPException(status_code=400, detail="Set up Company Master before creating invoices.")
    return company


@router.get("", response_model=List[schemas.InvoiceOut])
def list_invoices(db: Session = Depends(get_db)):
    return db.query(models.Invoice).filter_by(tenant_id="default").order_by(models.Invoice.id.desc()).all()


@router.get("/{invoice_id}", response_model=schemas.InvoiceOut)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.query(models.Invoice).filter_by(id=invoice_id, tenant_id="default").first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    return invoice


@router.post("", response_model=schemas.InvoiceOut)
def create_invoice(payload: schemas.InvoiceCreate, db: Session = Depends(get_db)):
    company = _get_company(db)
    customer = db.query(models.Customer).filter_by(id=payload.customer_id, tenant_id="default").first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")

    if not payload.items:
        raise HTTPException(status_code=400, detail="At least one line item is required.")

    is_export = customer.is_foreign
    tax_type = determine_tax_type(company.gstin, customer.gstin or "", is_export)

    subtotal = sum(item.qty * item.rate for item in payload.items)
    gst_rate = payload.gst_rate

    exchange_rate = None
    subtotal_foreign = None
    total_foreign = None
    currency_code = "INR"
    lut_arn = None
    lut_validity = None

    cgst_amount = sgst_amount = igst_amount = 0.0

    if is_export:
        if not payload.exchange_rate or payload.exchange_rate <= 0:
            raise HTTPException(status_code=400, detail="Exchange rate is required for export invoices (manual entry).")
        if not payload.currency_code or payload.currency_code == "INR":
            raise HTTPException(status_code=400, detail="Select a foreign currency for export invoices.")

        active_lut = (
            db.query(models.LUT)
            .filter_by(tenant_id="default", is_active=True)
            .order_by(models.LUT.valid_from.desc())
            .first()
        )
        if not active_lut:
            raise HTTPException(status_code=400, detail="No active LUT found. Add one in LUT Master before creating export invoices.")

        currency_code = payload.currency_code
        exchange_rate = payload.exchange_rate
        subtotal_foreign = subtotal
        total_foreign = subtotal_foreign  # zero-rated — no tax added
        subtotal_inr = round(subtotal_foreign * exchange_rate, 2)
        total_inr = subtotal_inr  # zero-rated
        lut_arn = active_lut.lut_arn
        lut_validity = f"FY {active_lut.financial_year}"
        place_of_supply_state = None
        place_of_supply_code = None
    else:
        subtotal_inr = subtotal
        tax_amount = round(subtotal * gst_rate / 100, 2)
        if tax_type == "IGST":
            igst_amount = tax_amount
        else:
            cgst_amount = round(tax_amount / 2, 2)
            sgst_amount = round(tax_amount / 2, 2)
        total_inr = subtotal_inr + tax_amount
        place_of_supply_code = customer.state_code
        place_of_supply_state = state_name_from_code(customer.state_code) if customer.state_code else None

    payment_terms_days = customer.payment_terms_days
    due_date = payload.invoice_date + timedelta(days=payment_terms_days)

    invoice_no, fy_label, seq_no = get_next_invoice_number(db, "default", payload.invoice_date)

    invoice = models.Invoice(
        tenant_id="default",
        invoice_no=invoice_no, fy_label=fy_label, seq_no=seq_no,
        invoice_date=payload.invoice_date, order_no=payload.order_no, order_date=payload.order_date,
        customer_id=customer.id, is_export=is_export,
        place_of_supply_state=place_of_supply_state, place_of_supply_code=place_of_supply_code,
        tax_type=tax_type, reverse_charge=False, gst_rate=gst_rate,
        subtotal_inr=subtotal_inr, cgst_amount=cgst_amount, sgst_amount=sgst_amount, igst_amount=igst_amount,
        total_inr=total_inr, currency_code=currency_code, exchange_rate=exchange_rate,
        subtotal_foreign=subtotal_foreign, total_foreign=total_foreign,
        lut_arn=lut_arn, lut_validity=lut_validity,
        payment_terms_days=payment_terms_days, due_date=due_date, status="Issued",
    )
    db.add(invoice)
    db.flush()

    for item in payload.items:
        db.add(models.InvoiceItem(
            invoice_id=invoice.id, description=item.description, note=item.note,
            hsn_sac=item.hsn_sac, qty=item.qty, rate=item.rate, amount=round(item.qty * item.rate, 2),
        ))

    db.commit()
    db.refresh(invoice)
    return invoice


def _render_invoice_pdf(invoice: models.Invoice, db: Session) -> str:
    company = _get_company(db)
    customer = invoice.customer

    company_dict = dict(
        name=company.name, address=company.address, gstin=company.gstin, cin=company.cin,
        udyam_number=company.udyam_number, email=company.email, mobile=company.mobile,
        logo_path=company.logo_path, signature_path=company.signature_path, tagline=company.tagline,
        terms_notes=company.terms_notes, bank_name=company.bank_name, bank_account=company.bank_account,
        bank_ifsc=company.bank_ifsc, upi_id=company.upi_id, intl_bank_name=company.intl_bank_name,
        intl_bank_account=company.intl_bank_account, intl_swift_code=company.intl_swift_code,
        intl_bank_address=company.intl_bank_address,
    )
    customer_dict = dict(name=customer.name, address=customer.address, country=customer.country, gstin=customer.gstin)
    items = [dict(description=i.description, note=i.note, hsn_sac=i.hsn_sac, qty=i.qty, rate=i.rate) for i in invoice.items]

    out_path = os.path.join(GENERATED_DIR, f"{invoice.invoice_no.replace('/', '_')}.pdf")

    if invoice.is_export:
        curr = CURRENCY_INFO.get(invoice.currency_code, {"symbol": invoice.currency_code, "words_unit": invoice.currency_code, "words_subunit": "Cents"})
        invoice_dict = dict(
            invoice_no=invoice.invoice_no, invoice_date=invoice.invoice_date.strftime("%d-%m-%Y"),
            order_no=invoice.order_no, order_date=invoice.order_date.strftime("%d-%m-%Y") if invoice.order_date else None,
            currency_code=invoice.currency_code, currency_symbol=curr["symbol"],
            currency_words_unit=curr["words_unit"], currency_words_subunit=curr["words_subunit"],
            reverse_charge=invoice.reverse_charge, payment_terms_days=invoice.payment_terms_days,
            due_date=invoice.due_date.strftime("%d-%m-%Y"), lut_arn=invoice.lut_arn, lut_validity=invoice.lut_validity,
        )
        generate_export_invoice_pdf(company_dict, customer_dict, invoice_dict, items, out_path)
    else:
        invoice_dict = dict(
            invoice_no=invoice.invoice_no, invoice_date=invoice.invoice_date.strftime("%d-%m-%Y"),
            order_no=invoice.order_no, order_date=invoice.order_date.strftime("%d-%m-%Y") if invoice.order_date else None,
            place_of_supply_state=invoice.place_of_supply_state, place_of_supply_code=invoice.place_of_supply_code,
            tax_type=invoice.tax_type, reverse_charge=invoice.reverse_charge, gst_rate=invoice.gst_rate,
            payment_terms_days=invoice.payment_terms_days, due_date=invoice.due_date.strftime("%d-%m-%Y"),
        )
        generate_domestic_invoice_pdf(company_dict, customer_dict, invoice_dict, items, out_path)

    return out_path


@router.get("/{invoice_id}/pdf")
def download_invoice_pdf(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.query(models.Invoice).filter_by(id=invoice_id, tenant_id="default").first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    path = _render_invoice_pdf(invoice, db)
    filename = f"{invoice.invoice_no.replace('/', '_')}.pdf"
    return FileResponse(path, media_type="application/pdf", filename=filename)
