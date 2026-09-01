from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/lut", tags=["lut"])


@router.get("", response_model=List[schemas.LUTOut])
def list_lut(db: Session = Depends(get_db)):
    return db.query(models.LUT).filter_by(tenant_id="default").order_by(models.LUT.valid_from.desc()).all()


@router.post("", response_model=schemas.LUTOut)
def create_lut(payload: schemas.LUTCreate, db: Session = Depends(get_db)):
    lut = models.LUT(tenant_id="default", **payload.model_dump())
    db.add(lut)
    db.commit()
    db.refresh(lut)
    return lut


@router.get("/active", response_model=schemas.LUTOut)
def get_active_lut(db: Session = Depends(get_db)):
    lut = (
        db.query(models.LUT)
        .filter_by(tenant_id="default", is_active=True)
        .order_by(models.LUT.valid_from.desc())
        .first()
    )
    if not lut:
        raise HTTPException(status_code=404, detail="No active LUT found. Add one in LUT Master before creating export invoices.")
    return lut
