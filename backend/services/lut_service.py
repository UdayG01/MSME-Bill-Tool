from datetime import date

from sqlalchemy.orm import Session

from db import models, schemas
from services.errors import ServiceError


def list_certificates(db: Session, tenant_id: str):
    return db.query(models.LutCertificate).filter_by(tenant_id=tenant_id).order_by(models.LutCertificate.valid_from.desc()).all()


def create_certificate(db: Session, tenant_id: str, payload: schemas.LutCertificateIn):
    if payload.valid_to < payload.valid_from:
        raise ServiceError(400, "LUT valid-to date must not precede valid-from date")
    record = models.LutCertificate(tenant_id=tenant_id, **payload.model_dump())
    db.add(record); db.commit(); db.refresh(record)
    return record


def set_status(db: Session, tenant_id: str, certificate_id: str, status: str):
    record = db.query(models.LutCertificate).filter_by(id=certificate_id, tenant_id=tenant_id).first()
    if not record:
        raise ServiceError(404, "LUT certificate not found")
    if status == "active":
        db.query(models.LutCertificate).filter_by(tenant_id=tenant_id, status="active").update({"status": "inactive"})
    record.status = status
    db.commit(); db.refresh(record)
    return record


def valid_active_lut(db: Session, tenant_id: str, on_date: date):
    return db.query(models.LutCertificate).filter(
        models.LutCertificate.tenant_id == tenant_id, models.LutCertificate.status == "active",
        models.LutCertificate.valid_from <= on_date, models.LutCertificate.valid_to >= on_date,
    ).first()
