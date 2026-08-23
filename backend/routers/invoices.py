from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from db import schemas, get_db
from core.session import get_current_session
from services import invoice_service
from services.pdf_service import build_invoice_pdf

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("", response_model=list[schemas.InvoiceOut])
def list_invoices(session=Depends(get_current_session), db: Session = Depends(get_db)):
    return invoice_service.list_invoices(db, session["tenant_id"])


@router.post("", response_model=schemas.InvoiceOut, status_code=201)
def create_invoice(payload: schemas.InvoiceCreate, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return invoice_service.create_draft(db, session["tenant_id"], payload)


@router.put("/{invoice_id}", response_model=schemas.InvoiceOut)
def update_invoice(invoice_id: str, payload: schemas.InvoiceCreate, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return invoice_service.update_draft(db, session["tenant_id"], invoice_id, payload)


@router.delete("/{invoice_id}", status_code=204)
def delete_invoice(invoice_id: str, session=Depends(get_current_session), db: Session = Depends(get_db)):
    invoice_service.delete_draft(db, session["tenant_id"], invoice_id)


@router.post("/{invoice_id}/issue", response_model=schemas.InvoiceOut)
def issue_invoice(invoice_id: str, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return invoice_service.issue_invoice(db, session["tenant_id"], invoice_id)


@router.post("/{invoice_id}/cancel", response_model=schemas.InvoiceOut)
def cancel_invoice(invoice_id: str, payload: schemas.ReasonIn, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return invoice_service.cancel_invoice(db, session["tenant_id"], invoice_id, payload.reason)


@router.get("/{invoice_id}/pdf")
def invoice_pdf(invoice_id: str, download: bool = Query(False), session=Depends(get_current_session), db: Session = Depends(get_db)):
    invoice = invoice_service.get_invoice(db, session["tenant_id"], invoice_id)
    filename = f"{(invoice.invoice_no or 'draft').replace('/', '-')}.pdf"
    disposition = "attachment" if download else "inline"
    return Response(
        content=build_invoice_pdf(invoice),
        media_type="application/pdf",
        headers={"Content-Disposition": f'{disposition}; filename="{filename}"'},
    )


@router.get("/{invoice_id}", response_model=schemas.InvoiceOut)
def get_invoice(invoice_id: str, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return invoice_service.get_invoice(db, session["tenant_id"], invoice_id)
