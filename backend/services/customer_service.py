from datetime import datetime

from sqlalchemy.orm import Session

from db import models, schemas
from services.errors import ServiceError


def get_customer(db: Session, tenant_id: str, customer_id: str) -> models.Customer:
    customer = db.query(models.Customer).filter_by(id=customer_id, tenant_id=tenant_id).first()
    if not customer:
        raise ServiceError(404, "Customer not found")
    return customer


def list_customers(db: Session, tenant_id: str, include_archived: bool = False):
    query = db.query(models.Customer).filter_by(tenant_id=tenant_id)
    if not include_archived:
        query = query.filter(models.Customer.is_archived.is_(False))
    return query.order_by(models.Customer.name).all()


def create_customer(db: Session, tenant_id: str, payload: schemas.CustomerIn) -> models.Customer:
    data = payload.model_dump()
    if data["is_foreign"]:
        data["gstin"] = ""
    customer = models.Customer(tenant_id=tenant_id, **data)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def update_customer(db: Session, tenant_id: str, customer_id: str, payload: schemas.CustomerIn) -> models.Customer:
    customer = get_customer(db, tenant_id, customer_id)
    data = payload.model_dump()
    if data["is_foreign"]:
        data["gstin"] = ""
    for field, value in data.items():
        setattr(customer, field, value)
    db.commit()
    db.refresh(customer)
    return customer


def set_archived(db: Session, tenant_id: str, customer_id: str, archived: bool) -> models.Customer:
    customer = get_customer(db, tenant_id, customer_id)
    customer.is_archived = archived
    customer.archived_at = datetime.utcnow() if archived else None
    db.commit()
    db.refresh(customer)
    return customer


def delete_unused_customer(db: Session, tenant_id: str, customer_id: str) -> None:
    customer = get_customer(db, tenant_id, customer_id)
    if customer.invoices:
        raise ServiceError(409, "Customer has invoices and must be archived instead")
    db.delete(customer)
    db.commit()
