"""
Sequential invoice numbering, per financial year, per tenant.

Preserves the design decision from the original build: a unique constraint
on (tenant_id, fy_label) on InvoiceCounter, combined with retry-on-conflict,
so two near-simultaneous invoice creations can never receive the same
sequence number. This matters because InvoiceCounter increments happen in
their own short transaction before the full Invoice row is written.
"""
import time
from datetime import date
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import models
from .gst_utils import financial_year_label

MAX_RETRIES = 5
PREFIX = "INV"


def get_next_invoice_number(db: Session, tenant_id: str, invoice_date: date) -> tuple[str, str, int]:
    """Returns (invoice_no, fy_label, seq_no). Retries on unique-constraint
    conflicts, which can occur if two requests race to create the counter
    row for a brand-new financial year at the same time."""
    fy_label = financial_year_label(invoice_date)

    for attempt in range(MAX_RETRIES):
        try:
            counter = (
                db.query(models.InvoiceCounter)
                .filter_by(tenant_id=tenant_id, fy_label=fy_label)
                .with_for_update(read=False)
                .first()
            )
            if counter is None:
                counter = models.InvoiceCounter(tenant_id=tenant_id, fy_label=fy_label, last_seq_no=0)
                db.add(counter)
                db.flush()  # raises IntegrityError here if another request just inserted the same row

            counter.last_seq_no += 1
            seq_no = counter.last_seq_no
            db.flush()

            invoice_no = f"{PREFIX}/{fy_label}/{str(seq_no).zfill(4)}"
            return invoice_no, fy_label, seq_no

        except IntegrityError:
            db.rollback()
            time.sleep(0.05 * (attempt + 1))
            continue

    raise RuntimeError("Could not allocate a unique invoice number after several attempts. Please try again.")
