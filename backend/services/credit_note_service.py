from datetime import datetime
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db import models, schemas
from core.utils import fy_label_for
from services.errors import ServiceError
from services.financial import invoice_balance, invoice_totals
from services.invoice_service import get_invoice


def get_credit_note(db: Session, tenant_id: str, credit_note_id: str) -> models.CreditNote:
    note = db.query(models.CreditNote).filter_by(id=credit_note_id, tenant_id=tenant_id).first()
    if not note:
        raise ServiceError(404, "Credit note not found")
    return note


def list_credit_notes(db: Session, tenant_id: str):
    return db.query(models.CreditNote).filter_by(tenant_id=tenant_id).order_by(models.CreditNote.created_at.desc()).all()


def list_for_invoice(db: Session, tenant_id: str, invoice_id: str):
    return get_invoice(db, tenant_id, invoice_id).credit_notes


def create_credit_note(db: Session, tenant_id: str, invoice_id: str, payload: schemas.CreditNoteCreate) -> models.CreditNote:
    invoice = get_invoice(db, tenant_id, invoice_id)
    if invoice.status != "issued":
        raise ServiceError(409, "Only issued invoices can receive credit notes")
    gst_rate, subtotal, gst_amount, total = invoice_totals(payload.items, Decimal(invoice.gst_rate), invoice.is_export)
    if total > invoice_balance(db, invoice):
        raise ServiceError(409, "Credit note exceeds the current outstanding balance")
    fy_label = fy_label_for(payload.date)
    for attempt in range(3):
        try:
            counter = db.query(models.CreditNoteCounter).filter_by(tenant_id=tenant_id, fy_label=fy_label).with_for_update().first()
            if not counter:
                counter = models.CreditNoteCounter(tenant_id=tenant_id, fy_label=fy_label, last_seq=0)
                db.add(counter)
                db.flush()
            counter.last_seq += 1
            note = models.CreditNote(
                tenant_id=tenant_id,
                invoice_id=invoice.id,
                credit_note_no=f"CN/{fy_label}/{counter.last_seq:04d}",
                fy_label=fy_label,
                seq_no=counter.last_seq,
                date=payload.date,
                reason=payload.reason.strip(),
                gst_rate=gst_rate,
                subtotal=subtotal,
                gst_amount=gst_amount,
                total=total,
            )
            for item in payload.items:
                note.items.append(models.CreditNoteItem(
                    description=item.description,
                    category=item.category,
                    qty=item.qty,
                    rate=item.rate,
                    amount=Decimal(item.qty) * Decimal(item.rate),
                ))
            db.add(note)
            db.commit()
            db.refresh(note)
            return note
        except IntegrityError:
            db.rollback()
            if attempt == 2:
                raise ServiceError(409, "Could not allocate a unique credit-note number; retry")
    raise ServiceError(409, "Could not create credit note")


def cancel_credit_note(db: Session, tenant_id: str, credit_note_id: str, reason: str) -> models.CreditNote:
    note = get_credit_note(db, tenant_id, credit_note_id)
    if note.status != "active":
        raise ServiceError(409, "Credit note is already cancelled")
    note.status = "cancelled"
    note.cancelled_at = datetime.utcnow()
    note.cancellation_reason = reason.strip()
    db.commit()
    db.refresh(note)
    return note
