from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db import schemas, get_db
from core.session import get_current_session
from services import company_service

router = APIRouter(tags=["company"])


@router.get("/company", response_model=schemas.CompanyOut)
def get_company(session=Depends(get_current_session), db: Session = Depends(get_db)):
    return company_service.get_company(db, session["tenant_id"])


@router.put("/company", response_model=schemas.CompanyOut)
def update_company(payload: schemas.CompanyUpdate, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return company_service.update_company(db, session["tenant_id"], payload)


@router.get("/lut", response_model=schemas.LutOut)
def get_lut(session=Depends(get_current_session), db: Session = Depends(get_db)):
    return company_service.get_lut(db, session["tenant_id"])


@router.put("/lut", response_model=schemas.LutOut)
def update_lut(payload: schemas.LutUpdate, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return company_service.update_lut(db, session["tenant_id"], payload)
