import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/company", tags=["company"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "uploads")
LOGO_DIR = os.path.join(UPLOAD_DIR, "logos")
SIGNATURE_DIR = os.path.join(UPLOAD_DIR, "signatures")
os.makedirs(LOGO_DIR, exist_ok=True)
os.makedirs(SIGNATURE_DIR, exist_ok=True)


def _get_or_404(db: Session):
    company = db.query(models.Company).filter_by(tenant_id="default").first()
    if not company:
        raise HTTPException(status_code=404, detail="Company Master not set up yet.")
    return company


@router.get("", response_model=schemas.CompanyOut)
def get_company(db: Session = Depends(get_db)):
    return _get_or_404(db)


@router.post("", response_model=schemas.CompanyOut)
def create_or_update_company(payload: schemas.CompanyCreate, db: Session = Depends(get_db)):
    company = db.query(models.Company).filter_by(tenant_id="default").first()
    if company:
        for field, value in payload.model_dump().items():
            setattr(company, field, value)
    else:
        company = models.Company(tenant_id="default", **payload.model_dump())
        db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.post("/logo", response_model=schemas.CompanyOut)
def upload_logo(file: UploadFile = File(...), db: Session = Depends(get_db)):
    company = _get_or_404(db)
    ext = os.path.splitext(file.filename)[1] or ".png"
    dest_path = os.path.join(LOGO_DIR, f"company_logo{ext}")
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    company.logo_path = dest_path
    db.commit()
    db.refresh(company)
    return company


@router.post("/signature", response_model=schemas.CompanyOut)
def upload_signature(file: UploadFile = File(...), db: Session = Depends(get_db)):
    company = _get_or_404(db)
    ext = os.path.splitext(file.filename)[1] or ".png"
    dest_path = os.path.join(SIGNATURE_DIR, f"authorized_signature{ext}")
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    company.signature_path = dest_path
    db.commit()
    db.refresh(company)
    return company
