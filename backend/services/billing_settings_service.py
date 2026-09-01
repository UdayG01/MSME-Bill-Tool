from sqlalchemy.orm import Session

from db import models, schemas


def get_settings(db: Session, tenant_id: str) -> models.BillingSettings:
    settings = db.query(models.BillingSettings).filter_by(tenant_id=tenant_id).first()
    if not settings:
        settings = models.BillingSettings(tenant_id=tenant_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def update_settings(db: Session, tenant_id: str, payload: schemas.BillingSettingsUpdate) -> models.BillingSettings:
    settings = get_settings(db, tenant_id)
    for key, value in payload.model_dump().items():
        setattr(settings, key, value.upper() if key == "base_currency" else value)
    db.commit()
    db.refresh(settings)
    return settings
