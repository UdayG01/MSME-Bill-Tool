from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from db import models, schemas
from services.errors import ServiceError
from services.financial import active_credit_total, active_receipts_total, money


def get_receipt(db: Session, tenant_id: str, receipt_id: str) -> models.Receipt:
    receipt = db.query(models.Receipt).filter_by(id=receipt_id, tenant_id=tenant_id).first()
    if not receipt:
        raise ServiceError(404, "Receipt not found")
    return receipt


def _issued_invoice(db: Session, tenant_id: str, invoice_id: str) -> models.Invoice:
    invoice = db.query(models.Invoice).filter_by(id=invoice_id, tenant_id=tenant_id).first()
    if not invoice:
        raise ServiceError(404, "Invoice not found")
    if invoice.status != "issued":
        raise ServiceError(409, "Receipts can only be recorded against issued invoices")
    return invoice


def _maximum_receipt(db: Session, invoice: models.Invoice, exclude_id: str | None = None) -> Decimal:
    return money(Decimal(invoice.total) - active_credit_total(db, invoice.id) - active_receipts_total(db, invoice.id, exclude_id))


def list_receipts(db: Session, tenant_id: str):
    return db.query(models.Receipt).filter_by(tenant_id=tenant_id).order_by(models.Receipt.date.desc()).all()


def create_receipt(db: Session, tenant_id: str, payload: schemas.ReceiptIn) -> models.Receipt:
    invoice = _issued_invoice(db, tenant_id, payload.invoice_id)
    if payload.amount > _maximum_receipt(db, invoice):
        raise ServiceError(409, "Receipt exceeds the current outstanding balance")
    receipt = models.Receipt(tenant_id=tenant_id, **payload.model_dump())
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return receipt


def update_receipt(db: Session, tenant_id: str, receipt_id: str, payload: schemas.ReceiptUpdate) -> models.Receipt:
    receipt = get_receipt(db, tenant_id, receipt_id)
    if receipt.status != "active":
        raise ServiceError(409, "Only active receipts can be edited")
    invoice = _issued_invoice(db, tenant_id, receipt.invoice_id)
    if payload.amount > _maximum_receipt(db, invoice, receipt.id):
        raise ServiceError(409, "Receipt exceeds the current outstanding balance")
    for field, value in payload.model_dump().items():
        setattr(receipt, field, value)
    db.commit()
    db.refresh(receipt)
    return receipt


def void_receipt(db: Session, tenant_id: str, receipt_id: str, reason: str) -> models.Receipt:
    receipt = get_receipt(db, tenant_id, receipt_id)
    if receipt.status != "active":
        raise ServiceError(409, "Receipt is already voided")
    receipt.status = "voided"
    receipt.voided_at = datetime.utcnow()
    receipt.void_reason = reason.strip()
    db.commit()
    db.refresh(receipt)
    return receipt


def restore_receipt(db: Session, tenant_id: str, receipt_id: str) -> models.Receipt:
    receipt = get_receipt(db, tenant_id, receipt_id)
    if receipt.status != "voided":
        raise ServiceError(409, "Receipt is already active")
    invoice = _issued_invoice(db, tenant_id, receipt.invoice_id)
    if Decimal(receipt.amount) > _maximum_receipt(db, invoice):
        raise ServiceError(409, "Restoring this receipt would overpay the invoice")
    receipt.status = "active"
    receipt.voided_at = None
    receipt.void_reason = ""
    db.commit()
    db.refresh(receipt)
    return receipt
