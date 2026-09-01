from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db import models, schemas
from core.utils import fy_label_for
from services.errors import ServiceError
from services.financial import active_credit_total, active_receipts_total, invoice_totals
from services import billing_settings_service, lut_service, tax_service


def get_invoice(db: Session, tenant_id: str, invoice_id: str) -> models.Invoice:
    invoice = db.query(models.Invoice).filter_by(id=invoice_id, tenant_id=tenant_id).first()
    if not invoice:
        raise ServiceError(404, "Invoice not found")
    return invoice


def list_invoices(db: Session, tenant_id: str):
    return db.query(models.Invoice).filter_by(tenant_id=tenant_id).order_by(models.Invoice.created_at.desc()).all()


def _replace_items(db: Session, invoice: models.Invoice, items) -> None:
    invoice.items.clear()
    db.flush()
    for item in items:
        invoice.items.append(models.InvoiceItem(
            description=item.description,
            category=item.category,
            hsn_sac=item.hsn_sac,
            qty=item.qty,
            rate=item.rate,
            amount=Decimal(item.qty) * Decimal(item.rate),
        ))


def _active_customer(db: Session, tenant_id: str, customer_id: str) -> models.Customer:
    customer = db.query(models.Customer).filter_by(id=customer_id, tenant_id=tenant_id, is_archived=False).first()
    if not customer:
        raise ServiceError(404, "Active customer not found")
    return customer


def _apply_draft(db: Session, invoice: models.Invoice, payload: schemas.InvoiceCreate, customer: models.Customer) -> None:
    tenant = db.get(models.Tenant, invoice.tenant_id)
    settings = billing_settings_service.get_settings(db, invoice.tenant_id)
    currency = payload.document_currency.upper()
    if customer.is_foreign:
        if not settings.allow_export_invoicing:
            raise ServiceError(409, "Export invoicing is not enabled in billing settings")
        if currency == "INR" or not payload.exchange_rate_to_inr:
            raise ServiceError(400, "Export invoices require a foreign currency and exchange rate")
    elif currency != settings.base_currency:
        raise ServiceError(400, "Domestic invoices must use the configured base currency")
    document_subtotal = sum((Decimal(item.qty) * Decimal(item.rate) for item in payload.items), Decimal("0"))
    subtotal_inr = document_subtotal if not customer.is_foreign else document_subtotal * Decimal(payload.exchange_rate_to_inr)
    tax = tax_service.calculate_invoice_tax(db, invoice.tenant_id, tenant, customer, subtotal_inr, payload.gst_rate)
    effective_rate, subtotal, gst_amount, total = tax["rate"], subtotal_inr, tax["gst"], subtotal_inr + tax["gst"]
    invoice.customer_id = customer.id
    invoice.invoice_date = payload.invoice_date
    invoice.order_no = payload.order_no
    invoice.order_date = payload.order_date
    invoice.gst_rate = effective_rate
    invoice.subtotal = subtotal
    invoice.gst_amount = gst_amount
    invoice.total = total
    invoice.is_export = customer.is_foreign
    invoice.document_currency = currency
    invoice.exchange_rate_to_inr = payload.exchange_rate_to_inr if customer.is_foreign else None
    invoice.document_subtotal = document_subtotal if customer.is_foreign else subtotal
    invoice.document_total = document_subtotal if customer.is_foreign else total
    invoice.tax_treatment = tax["treatment"]
    invoice.place_of_supply_code = tax["place_code"]
    invoice.place_of_supply_name = tax["place_name"]
    invoice.cgst_amount = tax["cgst"]
    invoice.sgst_amount = tax["sgst"]
    invoice.igst_amount = tax["igst"]
    invoice.credit_days = customer.credit_days
    invoice.due_date = payload.invoice_date + timedelta(days=customer.credit_days or 0)
    _replace_items(db, invoice, payload.items)


def create_draft(db: Session, tenant_id: str, payload: schemas.InvoiceCreate) -> models.Invoice:
    customer = _active_customer(db, tenant_id, payload.customer_id)
    invoice = models.Invoice(tenant_id=tenant_id, customer_id=customer.id, invoice_date=payload.invoice_date, status="draft")
    db.add(invoice)
    _apply_draft(db, invoice, payload, customer)
    db.commit()
    db.refresh(invoice)
    return invoice


def update_draft(db: Session, tenant_id: str, invoice_id: str, payload: schemas.InvoiceCreate) -> models.Invoice:
    invoice = get_invoice(db, tenant_id, invoice_id)
    if invoice.status != "draft":
        raise ServiceError(409, "Only draft invoices can be edited")
    customer = _active_customer(db, tenant_id, payload.customer_id)
    _apply_draft(db, invoice, payload, customer)
    db.commit()
    db.refresh(invoice)
    return invoice


def delete_draft(db: Session, tenant_id: str, invoice_id: str) -> None:
    invoice = get_invoice(db, tenant_id, invoice_id)
    if invoice.status != "draft":
        raise ServiceError(409, "Only draft invoices can be deleted")
    db.delete(invoice)
    db.commit()


def issue_invoice(db: Session, tenant_id: str, invoice_id: str) -> models.Invoice:
    invoice = get_invoice(db, tenant_id, invoice_id)
    if invoice.status != "draft":
        raise ServiceError(409, "Only draft invoices can be issued")
    if not invoice.items:
        raise ServiceError(400, "Invoice must have at least one line item")
    tenant = db.get(models.Tenant, tenant_id)
    customer = invoice.customer
    lut = db.query(models.LutMaster).filter_by(tenant_id=tenant_id).first()
    settings = billing_settings_service.get_settings(db, tenant_id)
    export_lut = None
    if invoice.is_export and settings.require_valid_lut_for_export:
        export_lut = lut_service.valid_active_lut(db, tenant_id, invoice.invoice_date)
        if not export_lut:
            raise ServiceError(409, "A valid active LUT certificate is required to issue this export invoice")
    fy_label = fy_label_for(invoice.invoice_date)

    for attempt in range(3):
        try:
            counter = db.query(models.InvoiceCounter).filter_by(tenant_id=tenant_id, fy_label=fy_label).with_for_update().first()
            if not counter:
                counter = models.InvoiceCounter(tenant_id=tenant_id, fy_label=fy_label, last_seq=0)
                db.add(counter)
                db.flush()
            counter.last_seq += 1
            invoice.seq_no = counter.last_seq
            invoice.fy_label = fy_label
            invoice.invoice_no = f"{tenant.invoice_prefix or 'INV'}/{fy_label}/{invoice.seq_no:04d}"
            invoice.status = "issued"
            invoice.issued_at = datetime.utcnow()
            invoice.lut_no_snapshot = lut.lut_no if invoice.is_export and lut else ""
            invoice.lut_date_snapshot = lut.lut_date if invoice.is_export and lut else None
            if export_lut:
                invoice.lut_certificate_id = export_lut.id
                invoice.lut_no_snapshot = export_lut.arn
                invoice.lut_valid_from_snapshot = export_lut.valid_from
                invoice.lut_valid_to_snapshot = export_lut.valid_to
            snapshot_fields = {
                "company_name_snapshot": "company_name",
                "company_address_snapshot": "address",
                "company_gstin_snapshot": "gstin",
                "company_cin_snapshot": "cin",
                "company_email_snapshot": "email",
                "company_phone_snapshot": "phone",
                "bank_name_snapshot": "bank_name",
                "bank_account_snapshot": "bank_account",
                "bank_ifsc_snapshot": "bank_ifsc",
            }
            for target, source in snapshot_fields.items():
                setattr(invoice, target, getattr(tenant, source) or "")
            for field in ("name", "address", "gstin", "country", "area"):
                target = f"customer_{field}_snapshot"
                setattr(invoice, target, getattr(customer, field) or "")
            db.commit()
            db.refresh(invoice)
            return invoice
        except IntegrityError:
            db.rollback()
            invoice = get_invoice(db, tenant_id, invoice_id)
            if attempt == 2:
                raise ServiceError(409, "Could not allocate a unique invoice number; retry")
    raise ServiceError(409, "Could not issue invoice")


def cancel_invoice(db: Session, tenant_id: str, invoice_id: str, reason: str) -> models.Invoice:
    invoice = get_invoice(db, tenant_id, invoice_id)
    if invoice.status != "issued":
        raise ServiceError(409, "Only issued invoices can be cancelled")
    if active_receipts_total(db, invoice.id) > 0 or active_credit_total(db, invoice.id) > 0:
        raise ServiceError(409, "Void active receipts and credit notes before cancelling this invoice")
    invoice.status = "cancelled"
    invoice.cancelled_at = datetime.utcnow()
    invoice.cancellation_reason = reason.strip()
    db.commit()
    db.refresh(invoice)
    return invoice
