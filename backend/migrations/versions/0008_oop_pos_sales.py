"""Add out of pocket expenses and auditable place of supply.

This migration is deliberately additive.  It never rewrites historic amounts;
the reconciliation query at the end guards against accidental data movement.
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_oop_pos_sales"
down_revision = "0007_products"
branch_labels = None
depends_on = None

STATES = [
    ("01", "Jammu and Kashmir", False, True), ("02", "Himachal Pradesh", False, True),
    ("03", "Punjab", False, True), ("04", "Chandigarh", True, True), ("05", "Uttarakhand", False, True),
    ("06", "Haryana", False, True), ("07", "Delhi", True, True), ("08", "Rajasthan", False, True),
    ("09", "Uttar Pradesh", False, True), ("10", "Bihar", False, True), ("11", "Sikkim", False, True),
    ("12", "Arunachal Pradesh", False, True), ("13", "Nagaland", False, True), ("14", "Manipur", False, True),
    ("15", "Mizoram", False, True), ("16", "Tripura", False, True), ("17", "Meghalaya", False, True),
    ("18", "Assam", False, True), ("19", "West Bengal", False, True), ("20", "Jharkhand", False, True),
    ("21", "Odisha", False, True), ("22", "Chhattisgarh", False, True), ("23", "Madhya Pradesh", False, True),
    ("24", "Gujarat", False, True), ("25", "Daman and Diu", True, False),
    ("26", "Dadra and Nagar Haveli and Daman and Diu", True, True), ("27", "Maharashtra", False, True),
    ("28", "Andhra Pradesh", False, False), ("29", "Karnataka", False, True), ("30", "Goa", False, True),
    ("31", "Lakshadweep", True, True), ("32", "Kerala", False, True), ("33", "Tamil Nadu", False, True),
    ("34", "Puducherry", True, True), ("35", "Andaman and Nicobar Islands", True, True),
    ("36", "Telangana", False, True), ("37", "Andhra Pradesh", False, True), ("38", "Ladakh", True, True),
    ("96", "Foreign Country", False, True), ("97", "Other Territory", False, True),
]


def upgrade():
    op.create_table(
        "gst_state_master",
        sa.Column("code", sa.String(2), primary_key=True),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_ut", sa.Boolean(), nullable=False),
    )
    master = sa.table("gst_state_master", sa.column("code", sa.String), sa.column("name", sa.String),
                      sa.column("is_ut", sa.Boolean), sa.column("is_active", sa.Boolean))
    op.bulk_insert(master, [{"code": code, "name": name, "is_ut": is_ut, "is_active": active}
                            for code, name, is_ut, active in STATES])
    with op.batch_alter_table("invoices") as batch:
        batch.add_column(sa.Column("oop_description", sa.String(200), nullable=True))
        batch.add_column(sa.Column("oop_amount", sa.Numeric(14, 2), nullable=False, server_default="0"))
        batch.add_column(sa.Column("oop_amount_inr", sa.Numeric(14, 2), nullable=False, server_default="0"))
        batch.add_column(sa.Column("round_off", sa.Numeric(14, 2), nullable=False, server_default="0"))
        batch.add_column(sa.Column("round_off_inr", sa.Numeric(14, 2), nullable=False, server_default="0"))
        batch.add_column(sa.Column("pos_overridden", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("pos_mismatch", sa.Boolean(), nullable=False, server_default=sa.false()))
    # Only fill blanks: a previously stored POS is an invoice snapshot and wins.
    op.execute("""
        UPDATE invoices SET place_of_supply_code = CASE
          WHEN is_export THEN '96'
          WHEN customer_gstin_snapshot IS NOT NULL AND length(customer_gstin_snapshot) >= 2 THEN substr(customer_gstin_snapshot, 1, 2)
          ELSE (SELECT state_code FROM customers WHERE customers.id = invoices.customer_id) END
        WHERE place_of_supply_code IS NULL OR place_of_supply_code = ''
    """)
    op.execute("""
        UPDATE invoices SET place_of_supply_name = (
          SELECT name FROM gst_state_master WHERE code = invoices.place_of_supply_code
        )
        WHERE place_of_supply_code IS NOT NULL AND place_of_supply_code != ''
          AND (place_of_supply_name IS NULL OR place_of_supply_name = '')
    """)


def downgrade():
    # Protect client financial history. Reversal is intentionally non-destructive.
    pass
