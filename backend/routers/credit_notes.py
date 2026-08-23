from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from db import schemas, get_db
from core.session import get_current_session
from services import credit_note_service
from services.pdf_service import build_credit_note_pdf

router = APIRouter(tags=["credit notes"])


@router.get("/credit-notes", response_model=list[schemas.CreditNoteOut])
def list_credit_notes(session=Depends(get_current_session), db: Session = Depends(get_db)):
    return credit_note_service.list_credit_notes(db, session["tenant_id"])


@router.get("/invoices/{invoice_id}/credit-notes", response_model=list[schemas.CreditNoteOut])
def invoice_credit_notes(invoice_id: str, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return credit_note_service.list_for_invoice(db, session["tenant_id"], invoice_id)


@router.post("/invoices/{invoice_id}/credit-notes", response_model=schemas.CreditNoteOut, status_code=201)
def create_credit_note(invoice_id: str, payload: schemas.CreditNoteCreate, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return credit_note_service.create_credit_note(db, session["tenant_id"], invoice_id, payload)


@router.post("/credit-notes/{credit_note_id}/cancel", response_model=schemas.CreditNoteOut)
def cancel_credit_note(credit_note_id: str, payload: schemas.ReasonIn, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return credit_note_service.cancel_credit_note(db, session["tenant_id"], credit_note_id, payload.reason)


@router.get("/credit-notes/{credit_note_id}/pdf")
def credit_note_pdf(credit_note_id: str, download: bool = Query(False), session=Depends(get_current_session), db: Session = Depends(get_db)):
    note = credit_note_service.get_credit_note(db, session["tenant_id"], credit_note_id)
    filename = f"{note.credit_note_no.replace('/', '-')}.pdf"
    disposition = "attachment" if download else "inline"
    return Response(
        content=build_credit_note_pdf(note),
        media_type="application/pdf",
        headers={"Content-Disposition": f'{disposition}; filename="{filename}"'},
    )
