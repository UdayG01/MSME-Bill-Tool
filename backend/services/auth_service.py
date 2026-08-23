from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db import models, schemas
from core.security import hash_password, verify_password
from services.errors import ServiceError


def signup(db: Session, payload: schemas.SignupIn) -> tuple[models.User, models.Tenant]:
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise ServiceError(400, "An account with this email already exists")
    tenant = models.Tenant(company_name=payload.company_name.strip())
    db.add(tenant)
    db.flush()
    user = models.User(
        tenant_id=tenant.id,
        email=str(payload.email).lower(),
        hashed_password=hash_password(payload.password),
        role="owner",
    )
    db.add_all([user, models.LutMaster(tenant_id=tenant.id)])
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ServiceError(400, "An account with this email already exists")
    return user, tenant


def login(db: Session, payload: schemas.LoginIn) -> models.User:
    user = db.query(models.User).filter(models.User.email == str(payload.email).lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise ServiceError(401, "Invalid email or password")
    return user


def current_identity(db: Session, user_id: str, tenant_id: str) -> dict:
    tenant = db.get(models.Tenant, tenant_id)
    if not tenant:
        raise ServiceError(401, "Account is no longer available")
    return {"user_id": user_id, "tenant_id": tenant_id, "company_name": tenant.company_name}
