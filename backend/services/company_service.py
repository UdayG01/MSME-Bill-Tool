from sqlalchemy.orm import Session

from db import models, schemas
from services.errors import ServiceError


def get_company(db: Session, tenant_id: str) -> models.Tenant:
    tenant = db.get(models.Tenant, tenant_id)
    if not tenant:
        raise ServiceError(404, "Company not found")
    return tenant


def update_company(db: Session, tenant_id: str, payload: schemas.CompanyUpdate) -> models.Tenant:
    tenant = get_company(db, tenant_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tenant, field, value or "")
    db.commit()
    db.refresh(tenant)
    return tenant


def get_lut(db: Session, tenant_id: str) -> models.LutMaster:
    lut = db.query(models.LutMaster).filter_by(tenant_id=tenant_id).first()
    if not lut:
        lut = models.LutMaster(tenant_id=tenant_id)
        db.add(lut)
        db.commit()
        db.refresh(lut)
    return lut


def update_lut(db: Session, tenant_id: str, payload: schemas.LutUpdate) -> models.LutMaster:
    lut = get_lut(db, tenant_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "lut_no":
            value = value or ""
        setattr(lut, field, value)
    db.commit()
    db.refresh(lut)
    return lut
