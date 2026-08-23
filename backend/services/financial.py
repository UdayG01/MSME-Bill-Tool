from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func
from sqlalchemy.orm import Session

from db import models

MONEY = Decimal("0.01")


def money(value: Decimal | int | str) -> Decimal:
    return Decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)


def invoice_totals(items, gst_rate: Decimal, is_export: bool) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    subtotal = money(sum((Decimal(item.qty) * Decimal(item.rate) for item in items), Decimal("0")))
    effective_rate = Decimal("0") if is_export else Decimal(gst_rate)
    gst_amount = money(subtotal * effective_rate / Decimal("100"))
    return effective_rate, subtotal, gst_amount, money(subtotal + gst_amount)


def active_receipts_total(db: Session, invoice_id: str, exclude_id: str | None = None) -> Decimal:
    query = db.query(func.coalesce(func.sum(models.Receipt.amount), 0)).filter(
        models.Receipt.invoice_id == invoice_id,
        models.Receipt.status == "active",
    )
    if exclude_id:
        query = query.filter(models.Receipt.id != exclude_id)
    return money(query.scalar() or 0)


def active_credit_total(db: Session, invoice_id: str) -> Decimal:
    value = db.query(func.coalesce(func.sum(models.CreditNote.total), 0)).filter(
        models.CreditNote.invoice_id == invoice_id,
        models.CreditNote.status == "active",
    ).scalar()
    return money(value or 0)


def invoice_balance(db: Session, invoice: models.Invoice) -> Decimal:
    if invoice.status != "issued":
        return Decimal("0.00")
    return money(
        Decimal(invoice.total)
        - active_credit_total(db, invoice.id)
        - active_receipts_total(db, invoice.id)
    )

