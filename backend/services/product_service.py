from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db import models, schemas
from services.errors import ServiceError


def get_product(db: Session, tenant_id: str, product_id: str) -> models.Product:
    product = db.query(models.Product).filter_by(id=product_id, tenant_id=tenant_id).first()
    if not product:
        raise ServiceError(404, "Product not found")
    return product


def list_products(db: Session, tenant_id: str, include_archived: bool = False):
    query = db.query(models.Product).filter_by(tenant_id=tenant_id)
    if not include_archived:
        query = query.filter(models.Product.is_archived.is_(False))
    return query.order_by(models.Product.name).all()


def _apply(product: models.Product, payload: schemas.ProductIn) -> None:
    product.name = payload.name.strip()
    product.description = payload.description.strip()
    product.hsn_sac = payload.hsn_sac.strip()
    product.amount = payload.amount


def create_product(db: Session, tenant_id: str, payload: schemas.ProductIn) -> models.Product:
    product = models.Product(tenant_id=tenant_id)
    _apply(product, payload)
    db.add(product)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ServiceError(409, "A product with this name already exists")
    db.refresh(product)
    return product


def update_product(db: Session, tenant_id: str, product_id: str, payload: schemas.ProductIn) -> models.Product:
    product = get_product(db, tenant_id, product_id)
    _apply(product, payload)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ServiceError(409, "A product with this name already exists")
    db.refresh(product)
    return product


def set_archived(db: Session, tenant_id: str, product_id: str, archived: bool) -> models.Product:
    product = get_product(db, tenant_id, product_id)
    product.is_archived = archived
    product.archived_at = datetime.utcnow() if archived else None
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, tenant_id: str, product_id: str) -> None:
    product = get_product(db, tenant_id, product_id)
    db.delete(product)
    db.commit()
