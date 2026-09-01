from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.session import get_current_session
from db import get_db, schemas
from services import lut_service

router = APIRouter(prefix="/lut-certificates", tags=["LUT certificates"])


@router.get("", response_model=list[schemas.LutCertificateOut])
def list_lut_certificates(session=Depends(get_current_session), db: Session = Depends(get_db)):
    return lut_service.list_certificates(db, session["tenant_id"])


@router.post("", response_model=schemas.LutCertificateOut, status_code=201)
def create_lut_certificate(payload: schemas.LutCertificateIn, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return lut_service.create_certificate(db, session["tenant_id"], payload)


@router.post("/{certificate_id}/activate", response_model=schemas.LutCertificateOut)
def activate_lut_certificate(certificate_id: str, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return lut_service.set_status(db, session["tenant_id"], certificate_id, "active")


@router.post("/{certificate_id}/archive", response_model=schemas.LutCertificateOut)
def archive_lut_certificate(certificate_id: str, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return lut_service.set_status(db, session["tenant_id"], certificate_id, "archived")
