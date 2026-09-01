from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas
from ..database import get_db
from ..gst_utils import extract_state_code

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("", response_model=List[schemas.CustomerOut])
def list_customers(db: Session = Depends(get_db)):
    return db.query(models.Customer).filter_by(tenant_id="default").order_by(models.Customer.name).all()


@router.get("/{customer_id}", response_model=schemas.CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).filter_by(id=customer_id, tenant_id="default").first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")
    return customer


@router.post("", response_model=schemas.CustomerOut)
def create_customer(payload: schemas.CustomerCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()

    # Foreign customers never carry a GSTIN — auto-suppress even if one was typed in
    if data.get("is_foreign"):
        data["gstin"] = None
        state_code = None
    else:
        if not data.get("gstin"):
            raise HTTPException(status_code=400, detail="GSTIN is required for domestic customers.")
        state_code = extract_state_code(data["gstin"])

    customer = models.Customer(tenant_id="default", state_code=state_code, **data)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.put("/{customer_id}", response_model=schemas.CustomerOut)
def update_customer(customer_id: int, payload: schemas.CustomerCreate, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).filter_by(id=customer_id, tenant_id="default").first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")
    data = payload.model_dump()
    if data.get("is_foreign"):
        data["gstin"] = None
        customer.state_code = None
    else:
        customer.state_code = extract_state_code(data.get("gstin") or "")
    for field, value in data.items():
        setattr(customer, field, value)
    db.commit()
    db.refresh(customer)
    return customer
