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


def _prepare_values(db: Session, invoice: models.Invoice, data: dict, exclude_id: str | None = None) -> dict:
    """Calculate cash realised separately from the receivable carrying value.

    An export customer settles the invoice in its document currency. Exchange
    movement belongs in forex gain/loss and must not create an overpayment or
    leave customer debt behind.
    """
    maximum = _maximum_receipt(db, invoice, exclude_id)
    if invoice.is_export:
        if data["receipt_currency"] != invoice.document_currency or not data["foreign_amount"] or not data["exchange_rate_to_inr"]:
            raise ServiceError(400, "Export receipts require the invoice currency, foreign amount, and exchange rate")
        if not invoice.document_total or Decimal(invoice.document_total) <= 0:
            raise ServiceError(409, "The export invoice has no valid foreign-currency total")
        realised = money(Decimal(data["foreign_amount"]) * Decimal(data["exchange_rate_to_inr"]))
        applied = money(Decimal(invoice.total) * Decimal(data["foreign_amount"]) / Decimal(invoice.document_total))
        # Tolerate only a one-paise proportional rounding difference on the
        # final instalment; genuine excess foreign payment remains blocked.
        if applied > maximum:
            if applied - maximum <= Decimal("0.01"):
                applied = maximum
            else:
                raise ServiceError(409, "Receipt exceeds the current outstanding balance")
        data["amount"] = realised
        data["applied_amount_inr"] = applied
        data["forex_gain_loss_inr"] = money(realised - applied)
    else:
        if data["amount"] is None:
            raise ServiceError(400, "Domestic receipts require an INR amount")
        amount = money(Decimal(data["amount"]))
        if amount > maximum:
            raise ServiceError(409, "Receipt exceeds the current outstanding balance")
        data.update({
            "amount": amount,
            "applied_amount_inr": amount,
            "receipt_currency": "INR",
            "foreign_amount": None,
            "exchange_rate_to_inr": None,
            "firc_number": "",
            "forex_gain_loss_inr": None,
        })
    return data


def list_receipts(db: Session, tenant_id: str):
    return db.query(models.Receipt).filter_by(tenant_id=tenant_id).order_by(models.Receipt.date.desc()).all()


def create_receipt(db: Session, tenant_id: str, payload: schemas.ReceiptIn) -> models.Receipt:
    invoice = _issued_invoice(db, tenant_id, payload.invoice_id)
    data = _prepare_values(db, invoice, payload.model_dump())
    receipt = models.Receipt(tenant_id=tenant_id, **data)
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return receipt


def update_receipt(db: Session, tenant_id: str, receipt_id: str, payload: schemas.ReceiptUpdate) -> models.Receipt:
    receipt = get_receipt(db, tenant_id, receipt_id)
    if receipt.status != "active":
        raise ServiceError(409, "Only active receipts can be edited")
    invoice = _issued_invoice(db, tenant_id, receipt.invoice_id)
    data = _prepare_values(db, invoice, payload.model_dump(), receipt.id)
    for field, value in data.items():
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
    applied = Decimal(receipt.applied_amount_inr if receipt.applied_amount_inr is not None else receipt.amount)
    if applied > _maximum_receipt(db, invoice):
        raise ServiceError(409, "Restoring this receipt would overpay the invoice")
    receipt.status = "active"
    receipt.voided_at = None
    receipt.void_reason = ""
    db.commit()
    db.refresh(receipt)
    return receipt
