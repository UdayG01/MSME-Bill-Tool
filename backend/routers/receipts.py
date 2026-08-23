from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db import schemas, get_db
from core.session import get_current_session
from services import receipt_service

router = APIRouter(prefix="/receipts", tags=["receipts"])


@router.get("", response_model=list[schemas.ReceiptOut])
def list_receipts(session=Depends(get_current_session), db: Session = Depends(get_db)):
    return receipt_service.list_receipts(db, session["tenant_id"])


@router.post("", response_model=schemas.ReceiptOut, status_code=201)
def create_receipt(payload: schemas.ReceiptIn, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return receipt_service.create_receipt(db, session["tenant_id"], payload)


@router.put("/{receipt_id}", response_model=schemas.ReceiptOut)
def update_receipt(receipt_id: str, payload: schemas.ReceiptUpdate, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return receipt_service.update_receipt(db, session["tenant_id"], receipt_id, payload)


@router.post("/{receipt_id}/void", response_model=schemas.ReceiptOut)
def void_receipt(receipt_id: str, payload: schemas.ReasonIn, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return receipt_service.void_receipt(db, session["tenant_id"], receipt_id, payload.reason)


@router.post("/{receipt_id}/restore", response_model=schemas.ReceiptOut)
def restore_receipt(receipt_id: str, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return receipt_service.restore_receipt(db, session["tenant_id"], receipt_id)
