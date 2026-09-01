from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.session import get_current_session
from db import get_db, schemas
from services import billing_settings_service

router = APIRouter(prefix="/settings/billing", tags=["billing settings"])


@router.get("", response_model=schemas.BillingSettingsOut)
def get_billing_settings(session=Depends(get_current_session), db: Session = Depends(get_db)):
    return billing_settings_service.get_settings(db, session["tenant_id"])


@router.put("", response_model=schemas.BillingSettingsOut)
def update_billing_settings(payload: schemas.BillingSettingsUpdate, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return billing_settings_service.update_settings(db, session["tenant_id"], payload)
