"""Add drafts, archival, receipt reversals, snapshots, and credit notes."""
from alembic import op
import sqlalchemy as sa

revision = "0002_record_lifecycle"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("customers") as batch:
        batch.add_column(sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("archived_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))

    with op.batch_alter_table("invoices") as batch:
        batch.alter_column("invoice_no", existing_type=sa.String(), nullable=True)
        batch.alter_column("fy_label", existing_type=sa.String(), nullable=True)
        batch.alter_column("seq_no", existing_type=sa.Integer(), nullable=True)
        batch.add_column(sa.Column("status", sa.String(), nullable=False, server_default="issued"))
        for name in (
            "company_name_snapshot", "company_address_snapshot", "company_gstin_snapshot", "company_cin_snapshot",
            "company_email_snapshot", "company_phone_snapshot", "bank_name_snapshot", "bank_account_snapshot",
            "bank_ifsc_snapshot", "customer_name_snapshot", "customer_address_snapshot", "customer_gstin_snapshot",
            "customer_country_snapshot", "customer_area_snapshot",
        ):
            batch.add_column(sa.Column(name, sa.String(), nullable=True, server_default=""))
        batch.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("issued_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("cancelled_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("cancellation_reason", sa.String(), nullable=True, server_default=""))
        batch.create_index("ix_invoices_status", ["status"])

    with op.batch_alter_table("receipts") as batch:
        batch.add_column(sa.Column("status", sa.String(), nullable=False, server_default="active"))
        batch.add_column(sa.Column("voided_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("void_reason", sa.String(), nullable=True, server_default=""))
        batch.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))
        batch.create_index("ix_receipts_status", ["status"])

    # Preserve the original values on already-issued legacy documents so later
    # edits to company or customer masters cannot rewrite historical invoices.
    op.execute(sa.text("""
        UPDATE invoices SET
            issued_at = COALESCE(issued_at, created_at),
            updated_at = COALESCE(updated_at, created_at),
            company_name_snapshot = COALESCE((SELECT company_name FROM tenants WHERE tenants.id = invoices.tenant_id), ''),
            company_address_snapshot = COALESCE((SELECT address FROM tenants WHERE tenants.id = invoices.tenant_id), ''),
            company_gstin_snapshot = COALESCE((SELECT gstin FROM tenants WHERE tenants.id = invoices.tenant_id), ''),
            company_cin_snapshot = COALESCE((SELECT cin FROM tenants WHERE tenants.id = invoices.tenant_id), ''),
            company_email_snapshot = COALESCE((SELECT email FROM tenants WHERE tenants.id = invoices.tenant_id), ''),
            company_phone_snapshot = COALESCE((SELECT phone FROM tenants WHERE tenants.id = invoices.tenant_id), ''),
            bank_name_snapshot = COALESCE((SELECT bank_name FROM tenants WHERE tenants.id = invoices.tenant_id), ''),
            bank_account_snapshot = COALESCE((SELECT bank_account FROM tenants WHERE tenants.id = invoices.tenant_id), ''),
            bank_ifsc_snapshot = COALESCE((SELECT bank_ifsc FROM tenants WHERE tenants.id = invoices.tenant_id), ''),
            customer_name_snapshot = COALESCE((SELECT name FROM customers WHERE customers.id = invoices.customer_id), ''),
            customer_address_snapshot = COALESCE((SELECT address FROM customers WHERE customers.id = invoices.customer_id), ''),
            customer_gstin_snapshot = COALESCE((SELECT gstin FROM customers WHERE customers.id = invoices.customer_id), ''),
            customer_country_snapshot = COALESCE((SELECT country FROM customers WHERE customers.id = invoices.customer_id), ''),
            customer_area_snapshot = COALESCE((SELECT area FROM customers WHERE customers.id = invoices.customer_id), '')
    """))

    op.create_table("credit_note_counters",
        sa.Column("id", sa.String(), primary_key=True), sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("fy_label", sa.String(), nullable=False), sa.Column("last_seq", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("tenant_id", "fy_label", name="uq_credit_note_tenant_fy"))
    op.create_table("credit_notes",
        sa.Column("id", sa.String(), primary_key=True), sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("invoice_id", sa.String(), sa.ForeignKey("invoices.id"), nullable=False), sa.Column("credit_note_no", sa.String(), nullable=False),
        sa.Column("fy_label", sa.String(), nullable=False), sa.Column("seq_no", sa.Integer(), nullable=False), sa.Column("date", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False), sa.Column("gst_rate", sa.Numeric(5, 2)), sa.Column("subtotal", sa.Numeric(14, 2)),
        sa.Column("gst_amount", sa.Numeric(14, 2)), sa.Column("total", sa.Numeric(14, 2)), sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("cancelled_at", sa.DateTime()), sa.Column("cancellation_reason", sa.String(), server_default=""), sa.Column("created_at", sa.DateTime()),
        sa.UniqueConstraint("tenant_id", "fy_label", "seq_no", name="uq_credit_note_number"))
    op.create_index("ix_credit_notes_tenant_id", "credit_notes", ["tenant_id"])
    op.create_index("ix_credit_notes_invoice_id", "credit_notes", ["invoice_id"])
    op.create_index("ix_credit_notes_status", "credit_notes", ["status"])
    op.create_table("credit_note_items",
        sa.Column("id", sa.String(), primary_key=True), sa.Column("credit_note_id", sa.String(), sa.ForeignKey("credit_notes.id"), nullable=False),
        sa.Column("description", sa.String()), sa.Column("category", sa.String()), sa.Column("qty", sa.Numeric(12, 2)),
        sa.Column("rate", sa.Numeric(14, 2)), sa.Column("amount", sa.Numeric(14, 2)))
    op.create_index("ix_credit_note_items_credit_note_id", "credit_note_items", ["credit_note_id"])


def downgrade():
    op.drop_table("credit_note_items")
    op.drop_table("credit_notes")
    op.drop_table("credit_note_counters")
    with op.batch_alter_table("receipts") as batch:
        batch.drop_index("ix_receipts_status")
        for name in ("updated_at", "void_reason", "voided_at", "status"):
            batch.drop_column(name)
    with op.batch_alter_table("invoices") as batch:
        batch.drop_index("ix_invoices_status")
        for name in ("cancellation_reason", "cancelled_at", "issued_at", "updated_at", "customer_area_snapshot", "customer_country_snapshot", "customer_gstin_snapshot", "customer_address_snapshot", "customer_name_snapshot", "bank_ifsc_snapshot", "bank_account_snapshot", "bank_name_snapshot", "company_phone_snapshot", "company_email_snapshot", "company_cin_snapshot", "company_gstin_snapshot", "company_address_snapshot", "company_name_snapshot", "status"):
            batch.drop_column(name)
        batch.alter_column("seq_no", existing_type=sa.Integer(), nullable=False)
        batch.alter_column("fy_label", existing_type=sa.String(), nullable=False)
        batch.alter_column("invoice_no", existing_type=sa.String(), nullable=False)
    with op.batch_alter_table("customers") as batch:
        for name in ("updated_at", "archived_at", "is_archived"):
            batch.drop_column(name)
