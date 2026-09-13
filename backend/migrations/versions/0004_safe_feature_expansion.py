"""Additive feature expansion; intentionally never deletes tenant data."""
from alembic import op
import sqlalchemy as sa

revision = "0004_safe_feature_expansion"
down_revision = "0003_configurable_billing"
branch_labels = None
depends_on = None


def upgrade():
    # No table is rebuilt, truncated, dropped, or seeded in this migration.
    with op.batch_alter_table("invoice_counters") as batch:
        batch.add_column(sa.Column("configured_at", sa.DateTime(), nullable=True))
    with op.batch_alter_table("invoice_items") as batch:
        batch.add_column(sa.Column("item_name", sa.String(500), nullable=True, server_default=""))
        batch.add_column(sa.Column("item_description", sa.String(2000), nullable=True, server_default=""))
    with op.batch_alter_table("invoices") as batch:
        batch.add_column(sa.Column("lut_financial_year_snapshot", sa.String(9), nullable=True, server_default=""))
        batch.add_column(sa.Column("reverse_charge", sa.Boolean(), nullable=True, server_default=sa.false()))
        for name, type_ in (("company_udyam_snapshot", sa.String(100)), ("company_upi_snapshot", sa.String(255)), ("intl_bank_name_snapshot", sa.String(255)), ("intl_bank_account_snapshot", sa.String(100)), ("intl_swift_code_snapshot", sa.String(50)), ("intl_bank_address_snapshot", sa.String(2000)), ("terms_notes_snapshot", sa.String(4000)), ("tagline_snapshot", sa.String(255))):
            batch.add_column(sa.Column(name, type_, nullable=True, server_default=""))
    op.execute(sa.text("UPDATE invoice_items SET item_name = COALESCE(NULLIF(description, ''), ''), item_description = COALESCE(item_description, '') WHERE item_name IS NULL OR item_name = ''"))


def downgrade():
    # A data-preserving release must not provide an accidental destructive rollback.
    pass
