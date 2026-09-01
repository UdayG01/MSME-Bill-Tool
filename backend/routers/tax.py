from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.session import get_current_session
from db import models, get_db, schemas
from services.errors import ServiceError

router = APIRouter(prefix="/tax-jurisdictions", tags=["tax"])


@router.get("", response_model=list[schemas.TaxJurisdictionOut])
def list_jurisdictions(session=Depends(get_current_session), db: Session = Depends(get_db)):
    return db.query(models.TaxJurisdiction).filter_by(tenant_id=session["tenant_id"]).order_by(models.TaxJurisdiction.code).all()


@router.post("", response_model=schemas.TaxJurisdictionOut, status_code=201)
def create_jurisdiction(payload: schemas.TaxJurisdictionIn, session=Depends(get_current_session), db: Session = Depends(get_db)):
    existing = db.query(models.TaxJurisdiction).filter_by(tenant_id=session["tenant_id"], country_code=payload.country_code.upper(), code=payload.code).first()
    if existing:
        raise ServiceError(409, "Tax jurisdiction already exists")
    item = models.TaxJurisdiction(tenant_id=session["tenant_id"], **{**payload.model_dump(), "country_code": payload.country_code.upper()})
    db.add(item); db.commit(); db.refresh(item)
    return item


@router.put("/{jurisdiction_id}", response_model=schemas.TaxJurisdictionOut)
def update_jurisdiction(jurisdiction_id: str, payload: schemas.TaxJurisdictionIn, session=Depends(get_current_session), db: Session = Depends(get_db)):
    item = db.query(models.TaxJurisdiction).filter_by(id=jurisdiction_id, tenant_id=session["tenant_id"]).first()
    if not item:
        raise ServiceError(404, "Tax jurisdiction not found")
    for key, value in payload.model_dump().items(): setattr(item, key, value.upper() if key == "country_code" else value)
    db.commit(); db.refresh(item)
    return item
