from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from db import schemas, get_db
from core.session import get_current_session
from services import customer_service

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=list[schemas.CustomerOut])
def list_customers(include_archived: bool = Query(False), session=Depends(get_current_session), db: Session = Depends(get_db)):
    return customer_service.list_customers(db, session["tenant_id"], include_archived)


@router.get("/{customer_id}", response_model=schemas.CustomerOut)
def get_customer(customer_id: str, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return customer_service.get_customer(db, session["tenant_id"], customer_id)


@router.post("", response_model=schemas.CustomerOut, status_code=201)
def create_customer(payload: schemas.CustomerIn, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return customer_service.create_customer(db, session["tenant_id"], payload)


@router.put("/{customer_id}", response_model=schemas.CustomerOut)
def update_customer(customer_id: str, payload: schemas.CustomerIn, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return customer_service.update_customer(db, session["tenant_id"], customer_id, payload)


@router.post("/{customer_id}/archive", response_model=schemas.CustomerOut)
def archive_customer(customer_id: str, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return customer_service.set_archived(db, session["tenant_id"], customer_id, True)


@router.post("/{customer_id}/restore", response_model=schemas.CustomerOut)
def restore_customer(customer_id: str, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return customer_service.set_archived(db, session["tenant_id"], customer_id, False)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: str, session=Depends(get_current_session), db: Session = Depends(get_db)):
    customer_service.delete_unused_customer(db, session["tenant_id"], customer_id)
