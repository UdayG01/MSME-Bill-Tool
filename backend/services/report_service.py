from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from db import models, schemas
from services.financial import money


def _bucket(days_overdue: int) -> str:
    if days_overdue <= 0:
        return "Not due"
    if days_overdue <= 30:
        return "1-30 days"
    if days_overdue <= 60:
        return "31-60 days"
    if days_overdue <= 90:
        return "61-90 days"
    return "90+ days"


def receivables(db: Session, tenant_id: str, as_of: date | None = None):
    today = as_of or date.today()
    rows = []
    invoices = db.query(models.Invoice).filter(
        models.Invoice.tenant_id == tenant_id, models.Invoice.invoice_date <= today
    ).all()
    for invoice in invoices:
        if invoice.status == "draft":
            continue
        # Reconstruct the lifecycle at the requested date instead of applying
        # today's cancellation/void state to a historical report.
        issued_on = invoice.issued_at.date() if invoice.issued_at else invoice.invoice_date
        cancelled_on = invoice.cancelled_at.date() if invoice.cancelled_at else None
        if issued_on > today or (cancelled_on and cancelled_on <= today):
            continue
        paid = money(sum((Decimal(receipt.applied_amount_inr if receipt.applied_amount_inr is not None else receipt.amount) for receipt in invoice.receipts
                          if receipt.date <= today
                          and receipt.created_at.date() <= today
                          and (receipt.status == "active" or (receipt.voided_at and receipt.voided_at.date() > today))), Decimal("0")))
        credited = money(sum((Decimal(note.total) for note in invoice.credit_notes
                              if note.date <= today
                              and note.created_at.date() <= today
                              and (note.status == "active" or (note.cancelled_at and note.cancelled_at.date() > today))), Decimal("0")))
        balance = money(Decimal(invoice.total) - paid - credited)
        if balance <= Decimal("0.00"):
            continue
        due_date = invoice.due_date or invoice.invoice_date + timedelta(days=invoice.credit_days or 0)
        days_overdue = (today - due_date).days
        rows.append(schemas.ReceivableRow(
            invoice_id=invoice.id,
            invoice_no=invoice.invoice_no or "",
            customer_name=invoice.customer_name_snapshot or invoice.customer.name,
            invoice_date=invoice.invoice_date,
            due_date=due_date,
            invoice_total=invoice.total,
            credited=credited,
            paid=paid,
            balance=balance,
            days_overdue=days_overdue,
            bucket=_bucket(days_overdue),
        ))
    return sorted(rows, key=lambda row: row.days_overdue, reverse=True)


def sales_area_wise(db: Session, tenant_id: str):
    totals = defaultdict(lambda: Decimal("0"))
    invoices = db.query(models.Invoice).filter_by(tenant_id=tenant_id, status="issued").all()
    for invoice in invoices:
        key = invoice.customer_area_snapshot or invoice.customer.area or "Unspecified"
        totals[key] += Decimal(invoice.subtotal)
        totals[key] -= sum(
            (Decimal(note.subtotal) for note in invoice.credit_notes if note.status == "active"),
            Decimal("0"),
        )
    return [schemas.SalesBreakdownRow(key=key, total=money(total)) for key, total in sorted(totals.items(), key=lambda row: row[1], reverse=True)]


def sales_product_wise(db: Session, tenant_id: str):
    totals = defaultdict(lambda: Decimal("0"))
    invoices = db.query(models.Invoice).filter_by(tenant_id=tenant_id, status="issued").all()
    for invoice in invoices:
        for item in invoice.items:
            totals[item.category or "Unspecified"] += Decimal(item.amount)
        for note in invoice.credit_notes:
            if note.status == "active":
                for item in note.items:
                    totals[item.category or "Unspecified"] -= Decimal(item.amount)
    return [schemas.SalesBreakdownRow(key=key, total=money(total)) for key, total in sorted(totals.items(), key=lambda row: row[1], reverse=True)]
