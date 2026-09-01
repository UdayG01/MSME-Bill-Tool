from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/reports", tags=["reports"])

# Ageing buckets, defined once so the boundaries stay consistent everywhere they're used
BUCKET_DEFS = [
    ("Not due", None, -1),
    ("1-30 days", 0, 30),
    ("31-60 days", 31, 60),
    ("61-90 days", 61, 90),
    ("90+ days", 91, None),
]


@router.get("/ageing", response_model=schemas.AgeingReportOut)
def ageing_report(as_of: date = None, db: Session = Depends(get_db)):
    as_of = as_of or date.today()

    invoices = db.query(models.Invoice).filter_by(tenant_id="default", status="Issued").all()

    # Outstanding = total_inr minus receipts already recorded against that invoice (in INR)
    receipts_by_invoice = {}
    for r in db.query(models.Receipt).filter_by(tenant_id="default").all():
        receipts_by_invoice.setdefault(r.invoice_id, 0.0)
        receipts_by_invoice[r.invoice_id] += r.amount_inr

    bucket_totals = {label: {"count": 0, "total": 0.0} for label, _, _ in BUCKET_DEFS}
    total_outstanding = 0.0

    for inv in invoices:
        received = receipts_by_invoice.get(inv.id, 0.0)
        outstanding = round(inv.total_inr - received, 2)
        if outstanding <= 0:
            continue

        days_overdue = (as_of - inv.due_date).days
        if days_overdue < 0:
            bucket_label = "Not due"
        elif days_overdue <= 30:
            bucket_label = "1-30 days"
        elif days_overdue <= 60:
            bucket_label = "31-60 days"
        elif days_overdue <= 90:
            bucket_label = "61-90 days"
        else:
            bucket_label = "90+ days"

        bucket_totals[bucket_label]["count"] += 1
        bucket_totals[bucket_label]["total"] += outstanding
        total_outstanding += outstanding

    buckets = [
        schemas.AgeingBucket(label=label, count=bucket_totals[label]["count"], total_inr=round(bucket_totals[label]["total"], 2))
        for label, _, _ in BUCKET_DEFS
    ]

    return schemas.AgeingReportOut(as_of=as_of, buckets=buckets, total_outstanding_inr=round(total_outstanding, 2))
