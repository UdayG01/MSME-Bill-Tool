"""Add reusable products for invoice line autofill."""

from alembic import op
import sqlalchemy as sa


revision = "0007_products"
down_revision = "0006_receipt_applied_amount"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "products",
        sa.Column("id", sa.String(length=12), nullable=False),
        sa.Column("tenant_id", sa.String(length=12), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column("hsn_sac", sa.String(length=50), nullable=True),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_product_tenant_name"),
    )
    op.create_index(op.f("ix_products_tenant_id"), "products", ["tenant_id"], unique=False)


def downgrade():
    # Preserve client product catalogues; no destructive downgrade.
    pass
