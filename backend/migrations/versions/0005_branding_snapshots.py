"""Add immutable branding references to issued invoices."""
from alembic import op
import sqlalchemy as sa

revision = "0005_branding_snapshots"
down_revision = "0004_safe_feature_expansion"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("invoices") as batch:
        batch.add_column(sa.Column("logo_asset_id_snapshot", sa.String(12), nullable=True))
        batch.add_column(sa.Column("signature_asset_id_snapshot", sa.String(12), nullable=True))


def downgrade():
    # Never remove production document history through a migration rollback.
    pass
