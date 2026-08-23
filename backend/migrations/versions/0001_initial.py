"""Original application schema baseline."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("tenants",
        sa.Column("id", sa.String(), primary_key=True), sa.Column("company_name", sa.String(), nullable=False),
        sa.Column("address", sa.String()), sa.Column("gstin", sa.String()), sa.Column("cin", sa.String()),
        sa.Column("state_code", sa.String()), sa.Column("email", sa.String()), sa.Column("phone", sa.String()),
        sa.Column("logo_text", sa.String()), sa.Column("invoice_prefix", sa.String()), sa.Column("bank_name", sa.String()),
        sa.Column("bank_account", sa.String()), sa.Column("bank_ifsc", sa.String()), sa.Column("created_at", sa.DateTime()))
    op.create_table("users",
        sa.Column("id", sa.String(), primary_key=True), sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("email", sa.String(), nullable=False), sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("role", sa.String()), sa.Column("created_at", sa.DateTime()), sa.UniqueConstraint("email", name="uq_users_email"))
    op.create_index("ix_users_email", "users", ["email"])
    op.create_table("lut_master",
        sa.Column("id", sa.String(), primary_key=True), sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False, unique=True),
        sa.Column("lut_no", sa.String()), sa.Column("lut_date", sa.Date()), sa.Column("valid_from", sa.Date()), sa.Column("valid_to", sa.Date()))
    op.create_table("customers",
        sa.Column("id", sa.String(), primary_key=True), sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False), sa.Column("address", sa.String()), sa.Column("gstin", sa.String()),
        sa.Column("country", sa.String()), sa.Column("is_foreign", sa.Boolean()), sa.Column("area", sa.String()),
        sa.Column("credit_days", sa.Integer()), sa.Column("created_at", sa.DateTime()))
    op.create_index("ix_customers_tenant_id", "customers", ["tenant_id"])
    op.create_table("invoice_counters",
        sa.Column("id", sa.String(), primary_key=True), sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("fy_label", sa.String(), nullable=False), sa.Column("last_seq", sa.Integer(), nullable=False),
        sa.UniqueConstraint("tenant_id", "fy_label", name="uq_tenant_fy"))
    op.create_table("invoices",
        sa.Column("id", sa.String(), primary_key=True), sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("customer_id", sa.String(), sa.ForeignKey("customers.id"), nullable=False), sa.Column("invoice_no", sa.String(), nullable=False),
        sa.Column("fy_label", sa.String(), nullable=False), sa.Column("seq_no", sa.Integer(), nullable=False), sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("order_no", sa.String()), sa.Column("order_date", sa.Date()), sa.Column("gst_rate", sa.Numeric(5, 2)),
        sa.Column("subtotal", sa.Numeric(14, 2)), sa.Column("gst_amount", sa.Numeric(14, 2)), sa.Column("total", sa.Numeric(14, 2)),
        sa.Column("is_export", sa.Boolean()), sa.Column("lut_no_snapshot", sa.String()), sa.Column("lut_date_snapshot", sa.Date()),
        sa.Column("credit_days", sa.Integer()), sa.Column("created_at", sa.DateTime()),
        sa.UniqueConstraint("tenant_id", "fy_label", "seq_no", name="uq_invoice_number"))
    op.create_index("ix_invoices_tenant_id", "invoices", ["tenant_id"])
    op.create_table("invoice_items",
        sa.Column("id", sa.String(), primary_key=True), sa.Column("invoice_id", sa.String(), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("description", sa.String()), sa.Column("category", sa.String()), sa.Column("qty", sa.Numeric(12, 2)),
        sa.Column("rate", sa.Numeric(14, 2)), sa.Column("amount", sa.Numeric(14, 2)))
    op.create_index("ix_invoice_items_invoice_id", "invoice_items", ["invoice_id"])
    op.create_table("receipts",
        sa.Column("id", sa.String(), primary_key=True), sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("invoice_id", sa.String(), sa.ForeignKey("invoices.id"), nullable=False), sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("date", sa.Date(), nullable=False), sa.Column("mode", sa.String()), sa.Column("reference", sa.String()), sa.Column("created_at", sa.DateTime()))
    op.create_index("ix_receipts_tenant_id", "receipts", ["tenant_id"])
    op.create_index("ix_receipts_invoice_id", "receipts", ["invoice_id"])


def downgrade():
    for table in ("receipts", "invoice_items", "invoices", "invoice_counters", "customers", "lut_master", "users", "tenants"):
        op.drop_table(table)

