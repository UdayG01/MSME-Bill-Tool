from datetime import datetime
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db import models, schemas
from core.utils import fy_label_for
from services.errors import ServiceError
from services.financial import active_credit_total, active_receipts_total, invoice_totals


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
    effective_rate, subtotal, gst_amount, total = invoice_totals(payload.items, payload.gst_rate, customer.is_foreign)
    invoice.customer_id = customer.id
    invoice.invoice_date = payload.invoice_date
    invoice.order_no = payload.order_no
    invoice.order_date = payload.order_date
    invoice.gst_rate = effective_rate
    invoice.subtotal = subtotal
    invoice.gst_amount = gst_amount
    invoice.total = total
    invoice.is_export = customer.is_foreign
    invoice.credit_days = customer.credit_days
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
