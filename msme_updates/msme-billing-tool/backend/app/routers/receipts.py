from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/receipts", tags=["receipts"])


@router.get("", response_model=List[schemas.ReceiptOut])
def list_receipts(invoice_id: int = None, db: Session = Depends(get_db)):
    query = db.query(models.Receipt).filter_by(tenant_id="default")
    if invoice_id:
        query = query.filter_by(invoice_id=invoice_id)
    return query.order_by(models.Receipt.receipt_date.desc()).all()


@router.post("", response_model=schemas.ReceiptOut)
def create_receipt(payload: schemas.ReceiptCreate, db: Session = Depends(get_db)):
    invoice = db.query(models.Invoice).filter_by(id=payload.invoice_id, tenant_id="default").first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")

    forex_gain_loss = None
    if invoice.is_export:
        if not payload.foreign_amount_received or not payload.exchange_rate_at_receipt:
            raise HTTPException(
                status_code=400,
                detail="Foreign amount received and exchange rate at receipt are required for export invoice receipts."
            )
        # Forex gain/loss = realized INR value vs. the INR equivalent frozen at invoice creation,
        # proportional to the fraction of the invoice being settled by this receipt.
        proportion = payload.foreign_amount_received / invoice.total_foreign if invoice.total_foreign else 0
        inr_equivalent_portion = invoice.total_inr * proportion
        inr_realized = payload.foreign_amount_received * payload.exchange_rate_at_receipt
        forex_gain_loss = round(inr_realized - inr_equivalent_portion, 2)

    receipt = models.Receipt(
        tenant_id="default",
        invoice_id=payload.invoice_id, receipt_date=payload.receipt_date, amount_inr=payload.amount_inr,
        foreign_amount_received=payload.foreign_amount_received,
        exchange_rate_at_receipt=payload.exchange_rate_at_receipt,
        forex_gain_loss=forex_gain_loss, firc_number=payload.firc_number, notes=payload.notes,
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return receipt
