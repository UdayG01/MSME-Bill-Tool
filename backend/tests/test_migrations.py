import os
from datetime import date
from decimal import Decimal
from pathlib import Path
import subprocess
import sys

import sqlalchemy as sa


BACKEND_DIR = Path(__file__).resolve().parents[1]


def _upgrade(database_url: str, revision: str) -> None:
    environment = {
        **os.environ,
        "APP_ENV": "test",
        "DATABASE_URL": database_url,
        "MIGRATION_DATABASE_URL": database_url,
    }
    subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", revision],
        cwd=BACKEND_DIR,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )


def test_receipt_migration_preserves_rows_and_backfills_frozen_inr(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'pre_change.db').as_posix()}"
    _upgrade(database_url, "0005_branding_snapshots")
    engine = sa.create_engine(database_url)
    metadata = sa.MetaData()
    metadata.reflect(bind=engine)
    tenants = metadata.tables["tenants"]
    customers = metadata.tables["customers"]
    invoices = metadata.tables["invoices"]
    receipts = metadata.tables["receipts"]

    with engine.begin() as connection:
        connection.execute(tenants.insert().values(id="tenant-1", company_name="Existing Client"))
        connection.execute(customers.insert().values(id="customer-1", tenant_id="tenant-1", name="Existing Overseas Customer"))
        connection.execute(invoices.insert().values(
            id="invoice-1",
            tenant_id="tenant-1",
            customer_id="customer-1",
            invoice_no="INV/2026-27/0001",
            fy_label="2026-27",
            seq_no=1,
            invoice_date=date(2026, 9, 1),
            total=Decimal("8000.00"),
            document_total=Decimal("100.00"),
            is_export=True,
        ))
        connection.execute(receipts.insert().values(
            id="receipt-1",
            tenant_id="tenant-1",
            invoice_id="invoice-1",
            amount=Decimal("8500.00"),
            date=date(2026, 9, 10),
            receipt_currency="USD",
            foreign_amount=Decimal("100.00"),
            exchange_rate_to_inr=Decimal("85.00"),
            forex_gain_loss_inr=Decimal("500.00"),
        ))

    _upgrade(database_url, "head")
    upgraded = sa.MetaData()
    upgraded.reflect(bind=engine)
    with engine.connect() as connection:
        receipt = connection.execute(
            sa.select(upgraded.tables["receipts"]).where(upgraded.tables["receipts"].c.id == "receipt-1")
        ).mappings().one()
        assert connection.scalar(sa.select(sa.func.count()).select_from(upgraded.tables["tenants"])) == 1
        assert connection.scalar(sa.select(sa.func.count()).select_from(upgraded.tables["invoices"])) == 1
        assert connection.scalar(sa.select(sa.func.count()).select_from(upgraded.tables["receipts"])) == 1
        assert Decimal(receipt["amount"]) == Decimal("8500.00")
        assert Decimal(receipt["applied_amount_inr"]) == Decimal("8000.00")
        assert Decimal(receipt["forex_gain_loss_inr"]) == Decimal("500.00")
