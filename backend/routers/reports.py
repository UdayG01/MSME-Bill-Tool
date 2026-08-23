from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db import schemas, get_db
from core.session import get_current_session
from services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/receivables", response_model=list[schemas.ReceivableRow])
def receivables(session=Depends(get_current_session), db: Session = Depends(get_db)):
    return report_service.receivables(db, session["tenant_id"])


@router.get("/sales/area-wise", response_model=list[schemas.SalesBreakdownRow])
def sales_area_wise(session=Depends(get_current_session), db: Session = Depends(get_db)):
    return report_service.sales_area_wise(db, session["tenant_id"])


@router.get("/sales/product-wise", response_model=list[schemas.SalesBreakdownRow])
def sales_product_wise(session=Depends(get_current_session), db: Session = Depends(get_db)):
    return report_service.sales_product_wise(db, session["tenant_id"])
