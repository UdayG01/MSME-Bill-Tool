from datetime import date
import csv
from io import StringIO
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from db import schemas, get_db
from core.session import get_current_session
from services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/receivables", response_model=list[schemas.ReceivableRow])
def receivables(as_of: date | None = Query(default=None), session=Depends(get_current_session), db: Session = Depends(get_db)):
    return report_service.receivables(db, session["tenant_id"], as_of)


@router.get("/sales/area-wise", response_model=list[schemas.SalesBreakdownRow])
def sales_area_wise(session=Depends(get_current_session), db: Session = Depends(get_db)):
    return report_service.sales_area_wise(db, session["tenant_id"])


@router.get("/sales/product-wise", response_model=list[schemas.SalesBreakdownRow])
def sales_product_wise(session=Depends(get_current_session), db: Session = Depends(get_db)):
    return report_service.sales_product_wise(db, session["tenant_id"])


@router.get("/sales-register", response_model=list[schemas.SalesRegisterRow])
def sales_register(from_date: date | None = None, to_date: date | None = None,
                   session=Depends(get_current_session), db: Session = Depends(get_db)):
    return report_service.sales_register(db, session["tenant_id"], from_date, to_date)


@router.get("/gstr1", response_model=list[schemas.Gstr1InvoiceRow])
def gstr1(from_date: date | None = None, to_date: date | None = None,
          session=Depends(get_current_session), db: Session = Depends(get_db)):
    return report_service.gstr1_invoices(db, session["tenant_id"], from_date, to_date)


@router.get("/gstr1.csv")
def gstr1_csv(from_date: date | None = None, to_date: date | None = None,
              session=Depends(get_current_session), db: Session = Depends(get_db)):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Invoice No", "Invoice Date", "Recipient GSTIN", "Place of Supply", "Taxable Value", "GST", "Invoice Value"])
    for row in report_service.gstr1_invoices(db, session["tenant_id"], from_date, to_date):
        writer.writerow([row.invoice_no, row.invoice_date, row.recipient_gstin, row.place_of_supply_code, row.taxable_value, row.gst_amount, row.invoice_value])
    return Response(output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=gstr1.csv"})
