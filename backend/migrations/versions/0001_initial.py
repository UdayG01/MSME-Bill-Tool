"""Original application schema baseline."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("tenants",
        sa.Column("id", sa.String(12), primary_key=True), sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("address", sa.String(2000)), sa.Column("gstin", sa.String(15)), sa.Column("cin", sa.String(21)),
        sa.Column("state_code", sa.String(2)), sa.Column("email", sa.String(254)), sa.Column("phone", sa.String(30)),
        sa.Column("logo_text", sa.String(255)), sa.Column("invoice_prefix", sa.String(50)), sa.Column("bank_name", sa.String(255)),
        sa.Column("bank_account", sa.String(50)), sa.Column("bank_ifsc", sa.String(20)), sa.Column("created_at", sa.DateTime()))
    op.create_table("users",
        sa.Column("id", sa.String(12), primary_key=True), sa.Column("tenant_id", sa.String(12), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("email", sa.String(254), nullable=False), sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(30)), sa.Column("created_at", sa.DateTime()), sa.UniqueConstraint("email", name="uq_users_email"))
    op.create_index("ix_users_email", "users", ["email"])
    op.create_table("lut_master",
        sa.Column("id", sa.String(12), primary_key=True), sa.Column("tenant_id", sa.String(12), sa.ForeignKey("tenants.id"), nullable=False, unique=True),
        sa.Column("lut_no", sa.String(100)), sa.Column("lut_date", sa.Date()), sa.Column("valid_from", sa.Date()), sa.Column("valid_to", sa.Date()))
    op.create_table("customers",
        sa.Column("id", sa.String(12), primary_key=True), sa.Column("tenant_id", sa.String(12), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False), sa.Column("address", sa.String(2000)), sa.Column("gstin", sa.String(15)),
        sa.Column("country", sa.String(100)), sa.Column("is_foreign", sa.Boolean()), sa.Column("area", sa.String(255)),
        sa.Column("credit_days", sa.Integer()), sa.Column("created_at", sa.DateTime()))
    op.create_index("ix_customers_tenant_id", "customers", ["tenant_id"])
    op.create_table("invoice_counters",
        sa.Column("id", sa.String(12), primary_key=True), sa.Column("tenant_id", sa.String(12), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("fy_label", sa.String(9), nullable=False), sa.Column("last_seq", sa.Integer(), nullable=False),
        sa.UniqueConstraint("tenant_id", "fy_label", name="uq_tenant_fy"))
    op.create_table("invoices",
        sa.Column("id", sa.String(12), primary_key=True), sa.Column("tenant_id", sa.String(12), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("customer_id", sa.String(12), sa.ForeignKey("customers.id"), nullable=False), sa.Column("invoice_no", sa.String(100), nullable=False),
        sa.Column("fy_label", sa.String(9), nullable=False), sa.Column("seq_no", sa.Integer(), nullable=False), sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("order_no", sa.String(100)), sa.Column("order_date", sa.Date()), sa.Column("gst_rate", sa.Numeric(5, 2)),
        sa.Column("subtotal", sa.Numeric(14, 2)), sa.Column("gst_amount", sa.Numeric(14, 2)), sa.Column("total", sa.Numeric(14, 2)),
        sa.Column("is_export", sa.Boolean()), sa.Column("lut_no_snapshot", sa.String(100)), sa.Column("lut_date_snapshot", sa.Date()),
        sa.Column("credit_days", sa.Integer()), sa.Column("created_at", sa.DateTime()),
        sa.UniqueConstraint("tenant_id", "fy_label", "seq_no", name="uq_invoice_number"))
    op.create_index("ix_invoices_tenant_id", "invoices", ["tenant_id"])
    op.create_table("invoice_items",
        sa.Column("id", sa.String(12), primary_key=True), sa.Column("invoice_id", sa.String(12), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("description", sa.String(2000)), sa.Column("category", sa.String(255)), sa.Column("qty", sa.Numeric(12, 2)),
        sa.Column("rate", sa.Numeric(14, 2)), sa.Column("amount", sa.Numeric(14, 2)))
    op.create_index("ix_invoice_items_invoice_id", "invoice_items", ["invoice_id"])
    op.create_table("receipts",
        sa.Column("id", sa.String(12), primary_key=True), sa.Column("tenant_id", sa.String(12), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("invoice_id", sa.String(12), sa.ForeignKey("invoices.id"), nullable=False), sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("date", sa.Date(), nullable=False), sa.Column("mode", sa.String(50)), sa.Column("reference", sa.String(255)), sa.Column("created_at", sa.DateTime()))
    op.create_index("ix_receipts_tenant_id", "receipts", ["tenant_id"])
    op.create_index("ix_receipts_invoice_id", "receipts", ["invoice_id"])


def downgrade():
    for table in ("receipts", "invoice_items", "invoices", "invoice_counters", "customers", "lut_master", "users", "tenants"):
        op.drop_table(table)
