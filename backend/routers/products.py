from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from db import schemas, get_db
from core.session import get_current_session
from services import product_service

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[schemas.ProductOut])
def list_products(include_archived: bool = Query(False), session=Depends(get_current_session), db: Session = Depends(get_db)):
    return product_service.list_products(db, session["tenant_id"], include_archived)


@router.get("/{product_id}", response_model=schemas.ProductOut)
def get_product(product_id: str, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return product_service.get_product(db, session["tenant_id"], product_id)


@router.post("", response_model=schemas.ProductOut, status_code=201)
def create_product(payload: schemas.ProductIn, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return product_service.create_product(db, session["tenant_id"], payload)


@router.put("/{product_id}", response_model=schemas.ProductOut)
def update_product(product_id: str, payload: schemas.ProductIn, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return product_service.update_product(db, session["tenant_id"], product_id, payload)


@router.post("/{product_id}/archive", response_model=schemas.ProductOut)
def archive_product(product_id: str, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return product_service.set_archived(db, session["tenant_id"], product_id, True)


@router.post("/{product_id}/restore", response_model=schemas.ProductOut)
def restore_product(product_id: str, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return product_service.set_archived(db, session["tenant_id"], product_id, False)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: str, session=Depends(get_current_session), db: Session = Depends(get_db)):
    product_service.delete_product(db, session["tenant_id"], product_id)
