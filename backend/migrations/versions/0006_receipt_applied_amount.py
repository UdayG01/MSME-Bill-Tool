"""Separate realised cash from the INR amount applied to receivables.

This migration is additive. It preserves every receipt and backfills the new
column; no existing tables, rows, or financial values are removed.
"""
from decimal import Decimal, ROUND_HALF_UP

from alembic import op
import sqlalchemy as sa


revision = "0006_receipt_applied_amount"
down_revision = "0005_branding_snapshots"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("receipts") as batch:
        batch.add_column(sa.Column("applied_amount_inr", sa.Numeric(14, 2), nullable=True))

    bind = op.get_bind()
    metadata = sa.MetaData()
    receipts = sa.Table("receipts", metadata, autoload_with=bind)
    invoices = sa.Table("invoices", metadata, autoload_with=bind)
    rows = bind.execute(
        sa.select(
            receipts.c.id,
            receipts.c.amount,
            receipts.c.foreign_amount,
            invoices.c.total,
            invoices.c.document_total,
            invoices.c.is_export,
        ).select_from(receipts.join(invoices, receipts.c.invoice_id == invoices.c.id))
    )
    cent = Decimal("0.01")
    for row in rows:
        applied = Decimal(row.amount)
        if row.is_export and row.foreign_amount and row.document_total and Decimal(row.document_total) > 0:
            applied = (
                Decimal(row.total) * Decimal(row.foreign_amount) / Decimal(row.document_total)
            ).quantize(cent, rounding=ROUND_HALF_UP)
        bind.execute(
            receipts.update().where(receipts.c.id == row.id).values(applied_amount_inr=applied)
        )


def downgrade():
    # Preserve production accounting history; no destructive downgrade.
    pass
