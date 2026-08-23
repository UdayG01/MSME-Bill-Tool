"""Upgrade a fresh database or safely adopt the legacy SQLite schema."""
from pathlib import Path
import sys

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from core.config import get_settings  # noqa: E402


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.migration_database_url, pool_pre_ping=True)
    tables = set(inspect(engine).get_table_names())
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))

    if "tenants" in tables and "alembic_version" not in tables:
        required_legacy_tables = {"users", "customers", "invoices", "invoice_items", "receipts"}
        if not required_legacy_tables.issubset(tables):
            missing = ", ".join(sorted(required_legacy_tables - tables))
            raise RuntimeError(f"Database looks partially initialized; missing tables: {missing}")
        print("Adopting existing legacy schema at revision 0001_initial")
        command.stamp(config, "0001_initial")

    command.upgrade(config, "head")
    print("Database is at the latest migration revision")


if __name__ == "__main__":
    main()
