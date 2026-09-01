"""Add configurable tax, export billing, LUT history, and document metadata."""
from alembic import op
import sqlalchemy as sa

revision = "0003_configurable_billing"
down_revision = "0002_record_lifecycle"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("tenants") as batch:
        for name, type_ in (("udyam_number", sa.String(100)), ("upi_id", sa.String(255)), ("intl_bank_name", sa.String(255)), ("intl_bank_account", sa.String(100)), ("intl_swift_code", sa.String(50)), ("intl_bank_address", sa.String(2000)), ("logo_asset_id", sa.String(12)), ("signature_asset_id", sa.String(12))):
            batch.add_column(sa.Column(name, type_, nullable=True))
    with op.batch_alter_table("customers") as batch:
        batch.add_column(sa.Column("state_code", sa.String(20), nullable=False, server_default=""))
    with op.batch_alter_table("invoice_items") as batch:
        batch.add_column(sa.Column("hsn_sac", sa.String(50), nullable=False, server_default=""))
    with op.batch_alter_table("invoices") as batch:
        for name, type_ in (("due_date", sa.Date()), ("tax_treatment", sa.String(50)), ("place_of_supply_code", sa.String(20)), ("place_of_supply_name", sa.String(255)), ("cgst_amount", sa.Numeric(14, 2)), ("sgst_amount", sa.Numeric(14, 2)), ("igst_amount", sa.Numeric(14, 2)), ("document_currency", sa.String(3)), ("exchange_rate_to_inr", sa.Numeric(18, 6)), ("document_subtotal", sa.Numeric(14, 2)), ("document_total", sa.Numeric(14, 2)), ("lut_certificate_id", sa.String(12)), ("lut_valid_from_snapshot", sa.Date()), ("lut_valid_to_snapshot", sa.Date())):
            batch.add_column(sa.Column(name, type_, nullable=True))
    with op.batch_alter_table("receipts") as batch:
        for name, type_ in (("receipt_currency", sa.String(3)), ("foreign_amount", sa.Numeric(14, 2)), ("exchange_rate_to_inr", sa.Numeric(18, 6)), ("firc_number", sa.String(255)), ("forex_gain_loss_inr", sa.Numeric(14, 2))):
            batch.add_column(sa.Column(name, type_, nullable=True))
    op.create_table("billing_settings", sa.Column("id", sa.String(12), primary_key=True), sa.Column("tenant_id", sa.String(12), sa.ForeignKey("tenants.id"), nullable=False, unique=True), sa.Column("base_currency", sa.String(3), nullable=False), sa.Column("allow_export_invoicing", sa.Boolean(), nullable=False), sa.Column("require_valid_lut_for_export", sa.Boolean(), nullable=False), sa.Column("terms_notes", sa.String(4000)), sa.Column("tagline", sa.String(255)))
    op.create_table("tax_jurisdictions", sa.Column("id", sa.String(12), primary_key=True), sa.Column("tenant_id", sa.String(12), sa.ForeignKey("tenants.id"), nullable=False), sa.Column("country_code", sa.String(2), nullable=False), sa.Column("code", sa.String(20), nullable=False), sa.Column("name", sa.String(255), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False), sa.UniqueConstraint("tenant_id", "country_code", "code", name="uq_tax_jurisdiction"))
    op.create_index("ix_tax_jurisdictions_tenant_id", "tax_jurisdictions", ["tenant_id"])
    op.create_table("lut_certificates", sa.Column("id", sa.String(12), primary_key=True), sa.Column("tenant_id", sa.String(12), sa.ForeignKey("tenants.id"), nullable=False), sa.Column("arn", sa.String(100), nullable=False), sa.Column("financial_year", sa.String(9), nullable=False), sa.Column("valid_from", sa.Date(), nullable=False), sa.Column("valid_to", sa.Date(), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime()), sa.UniqueConstraint("tenant_id", "arn", name="uq_lut_certificate_arn"))
    op.create_index("ix_lut_certificates_tenant_id", "lut_certificates", ["tenant_id"])
    op.create_table("media_assets", sa.Column("id", sa.String(12), primary_key=True), sa.Column("tenant_id", sa.String(12), sa.ForeignKey("tenants.id"), nullable=False), sa.Column("purpose", sa.String(30), nullable=False), sa.Column("storage_key", sa.String(500), nullable=False, unique=True), sa.Column("mime_type", sa.String(100), nullable=False), sa.Column("file_size", sa.Integer(), nullable=False), sa.Column("width", sa.Integer(), nullable=False), sa.Column("height", sa.Integer(), nullable=False), sa.Column("checksum", sa.String(64), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime()))
    op.create_index("ix_media_assets_tenant_id", "media_assets", ["tenant_id"])


def downgrade():
    op.drop_table("media_assets"); op.drop_table("lut_certificates"); op.drop_table("tax_jurisdictions"); op.drop_table("billing_settings")
    with op.batch_alter_table("receipts") as batch:
        for name in ("forex_gain_loss_inr", "firc_number", "exchange_rate_to_inr", "foreign_amount", "receipt_currency"): batch.drop_column(name)
    with op.batch_alter_table("invoices") as batch:
        for name in ("lut_valid_to_snapshot", "lut_valid_from_snapshot", "lut_certificate_id", "document_total", "document_subtotal", "exchange_rate_to_inr", "document_currency", "igst_amount", "sgst_amount", "cgst_amount", "place_of_supply_name", "place_of_supply_code", "tax_treatment", "due_date"): batch.drop_column(name)
    with op.batch_alter_table("invoice_items") as batch: batch.drop_column("hsn_sac")
    with op.batch_alter_table("customers") as batch: batch.drop_column("state_code")
    with op.batch_alter_table("tenants") as batch:
        for name in ("signature_asset_id", "logo_asset_id", "intl_bank_address", "intl_swift_code", "intl_bank_account", "intl_bank_name", "upi_id", "udyam_number"): batch.drop_column(name)
