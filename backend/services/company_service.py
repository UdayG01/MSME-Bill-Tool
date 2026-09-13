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
