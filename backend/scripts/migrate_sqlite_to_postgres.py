"""Copy the legacy SQLite data into an already-migrated PostgreSQL database.

Run from backend after `alembic upgrade head` against Neon:
    python scripts/migrate_sqlite_to_postgres.py
"""
import argparse
import os
from pathlib import Path

from sqlalchemy import MetaData, create_engine, inspect, select

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = BACKEND_DIR / "db" / "msme_billing.db"
TABLE_ORDER = [
    "tenants", "users", "lut_master", "customers", "invoice_counters",
    "invoices", "invoice_items", "receipts",
    "credit_note_counters", "credit_notes", "credit_note_items",
]


def normalize_postgres_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--target", default=os.getenv("MIGRATION_DATABASE_URL") or os.getenv("DATABASE_URL"))
    args = parser.parse_args()
    if not args.target:
        raise SystemExit("Set MIGRATION_DATABASE_URL to Neon's direct connection URL")

    source_engine = create_engine(f"sqlite:///{Path(args.source).resolve().as_posix()}")
    target_engine = create_engine(normalize_postgres_url(args.target), pool_pre_ping=True)
    source_meta, target_meta = MetaData(), MetaData()
    source_meta.reflect(bind=source_engine)
    target_meta.reflect(bind=target_engine)

    with target_engine.connect() as connection:
        nonempty = [name for name in TABLE_ORDER if name in target_meta.tables and connection.execute(select(target_meta.tables[name]).limit(1)).first()]
    if nonempty:
        raise SystemExit(f"Target is not empty ({', '.join(nonempty)}). Use a fresh Neon database.")

    tenant_lookup = {}
    customer_lookup = {}
    copied = {}
    with source_engine.connect() as source, target_engine.begin() as target:
        for table_name in TABLE_ORDER:
            if table_name not in source_meta.tables or table_name not in target_meta.tables:
                continue
            source_table = source_meta.tables[table_name]
            target_table = target_meta.tables[table_name]
            target_columns = {column.name for column in target_table.columns}
            rows = [dict(row._mapping) for row in source.execute(select(source_table))]
            prepared = []
            for row in rows:
                data = {key: value for key, value in row.items() if key in target_columns}
                if table_name == "customers":
                    data.setdefault("is_archived", False)
                    customer_lookup[row["id"]] = row
                elif table_name == "tenants":
                    tenant_lookup[row["id"]] = row
                elif table_name == "invoices":
                    tenant = tenant_lookup.get(row["tenant_id"], {})
                    customer = customer_lookup.get(row["customer_id"], {})
                    status = row.get("status") or "issued"
                    data.update(
                        status=status,
                        issued_at=row.get("issued_at") or (row.get("created_at") if status == "issued" else None),
                        company_name_snapshot=row.get("company_name_snapshot") or tenant.get("company_name", ""),
                        company_address_snapshot=row.get("company_address_snapshot") or tenant.get("address", ""),
                        company_gstin_snapshot=row.get("company_gstin_snapshot") or tenant.get("gstin", ""),
                        company_cin_snapshot=row.get("company_cin_snapshot") or tenant.get("cin", ""),
                        company_email_snapshot=row.get("company_email_snapshot") or tenant.get("email", ""),
                        company_phone_snapshot=row.get("company_phone_snapshot") or tenant.get("phone", ""),
                        bank_name_snapshot=row.get("bank_name_snapshot") or tenant.get("bank_name", ""),
                        bank_account_snapshot=row.get("bank_account_snapshot") or tenant.get("bank_account", ""),
                        bank_ifsc_snapshot=row.get("bank_ifsc_snapshot") or tenant.get("bank_ifsc", ""),
                        customer_name_snapshot=row.get("customer_name_snapshot") or customer.get("name", ""),
                        customer_address_snapshot=row.get("customer_address_snapshot") or customer.get("address", ""),
                        customer_gstin_snapshot=row.get("customer_gstin_snapshot") or customer.get("gstin", ""),
                        customer_country_snapshot=row.get("customer_country_snapshot") or customer.get("country", ""),
                        customer_area_snapshot=row.get("customer_area_snapshot") or customer.get("area", ""),
                    )
                elif table_name == "receipts":
                    data.setdefault("status", "active")
                prepared.append(data)
            if prepared:
                target.execute(target_table.insert(), prepared)
            copied[table_name] = len(prepared)

    with target_engine.connect() as target:
        for table_name, expected in copied.items():
            table = target_meta.tables[table_name]
            actual = len(target.execute(select(table.c.id)).all())
            if actual != expected:
                raise RuntimeError(f"Validation failed for {table_name}: expected {expected}, found {actual}")
            print(f"{table_name}: {actual} rows")
    print("Migration complete and row counts verified.")


if __name__ == "__main__":
    main()
