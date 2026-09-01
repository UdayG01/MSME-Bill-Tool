# MSME Billing and Receivable Control Tool

A tenant-isolated billing application for small businesses that need to manage customers, invoices, receipts, credit notes, receivables, and basic sales analysis.

For the Hostinger VPS, CyberPanel, and MariaDB production procedure, use [the CyberPanel deployment runbook](DEPLOYMENT_CYBERPANEL.md).

## What the application does

- Company and bank-detail setup, plus an LUT master for exports.
- Customer creation, editing, safe archival, and restoration.
- Editable invoice drafts. A permanent financial-year number is allocated only when a draft is issued.
- Immutable issued invoices with company/customer snapshots, controlled cancellation, and PDF view/download.
- Receipt creation and correction, with void/restore history and overpayment protection.
- Credit notes with their own financial-year numbering, cancellation, and PDF documents.
- Receivable ageing based on issued invoices less active receipts and active credit notes.
- Area-wise and product/service-wise sales reports using the same pre-GST, net-of-credit basis.
- Tenant isolation: every business can access only its own records.

The implemented scope solves the current purpose: day-to-day billing and receivable control for an early-stage, single-instance deployment. It is not intended to replace GST filing or a full accounting/ERP system.

## Architecture

```text
billing.grovisor.co.in (React/Vite static frontend via OpenLiteSpeed)
             |
             v
api-billing.grovisor.co.in (OpenLiteSpeed reverse proxy -> FastAPI)
             |
             v
MariaDB on the same Hostinger VPS
```

```text
backend/
  core/       environment configuration, security, and sessions
  db/         SQLAlchemy models, schemas, database connection, local SQLite DB
  migrations/ Alembic schema history
  routers/    thin FastAPI HTTP endpoints
  services/   business rules used by routers
  scripts/    database upgrade and SQLite-to-MariaDB migration utilities
  tests/      API workflow tests
frontend/     React/Vite user interface
```

Keeping HTTP handling in `routers/` and business rules in `services/` is intentional. Future edits to invoice calculations or lifecycle rules normally belong in a service; changes to URLs, request parameters, or response types belong in a router/schema.

## Database layout and backups

The local SQLite database is [backend/db/msme_billing.db](backend/db/msme_billing.db). It is ignored by Git. A verified pre-change backup was created at `backups/20260816_113734/msme_billing.db`; the entire `backups/` directory is also ignored by Git.

Production uses `DATABASE_URL` with the local MariaDB server on the VPS. The development default remains SQLite.

### Why migrations are needed

`Base.metadata.create_all()` can create missing tables, but it does not reliably evolve existing tables when columns, indexes, constraints, or data rules change. Alembic migrations:

- give every schema change a version and an ordered upgrade;
- preserve existing invoice/customer data while adding new fields;
- make local, test, and MariaDB schemas reproducible;
- let each VPS deployment upgrade only what has not run yet;
- provide a reviewable downgrade path for schema changes.

`scripts/upgrade_database.py` safely handles both cases. On a fresh database it runs every migration. On the original SQLite schema it first marks the existing tables as the baseline and then applies only the lifecycle changes.

## Local setup

Prerequisites: Python 3.12 (3.11 also works), Node.js 20+, and npm.

```powershell
Copy-Item .env.example .env
py -3.12 -m venv backend/.venv
backend\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
cd backend
python scripts/upgrade_database.py
pytest
cd ..\frontend
npm ci
npm run build
```

Return to the repository root and run `run.bat` to open the backend at `http://localhost:8000` and frontend at `http://localhost:5173`. API documentation is at `http://localhost:8000/docs`.

If Docker is available, run the same MariaDB version used on the VPS locally:

```powershell
docker compose up -d mariadb
$env:DATABASE_URL="mysql+pymysql://msme:local_dev_only@localhost:3306/msme_billing?charset=utf8mb4"
$env:MIGRATION_DATABASE_URL=$env:DATABASE_URL
cd backend
python scripts/upgrade_database.py
```

## Legacy hosted deployment notes

> The remaining Neon, Railway, and Vercel notes below describe the original deployment option. They are not the current production path and do not match the MariaDB driver now used by this repository. Use [DEPLOYMENT_CYBERPANEL.md](DEPLOYMENT_CYBERPANEL.md) for this application.

### 1. Put the code in GitHub

Create a Git repository if this directory still has none, commit the source files, and push it to a private GitHub repository. `.env`, databases, backups, virtual environments, and build output are already excluded by `.gitignore`.

### 2. Create the Neon database

1. Create a Neon project and database.
2. In **Connect**, copy both connection strings:
   - pooled string (hostname contains `-pooler`) for `DATABASE_URL`;
   - direct/unpooled string for `MIGRATION_DATABASE_URL` and data migration.
3. Keep both values secret and include their required SSL query parameters.

The app normalizes `postgresql://` to SQLAlchemy's Psycopg 3 driver automatically.

To copy the existing SQLite records, run this once from a trusted local machine before deployment:

```powershell
backend\.venv\Scripts\Activate.ps1
$env:DATABASE_URL="<NEON_POOLED_CONNECTION_STRING>"
$env:MIGRATION_DATABASE_URL="<NEON_DIRECT_CONNECTION_STRING>"
cd backend
python scripts/upgrade_database.py
python scripts/migrate_sqlite_to_postgres.py
```

The import refuses to write if the target business tables already contain data and verifies every copied table's row count. If the existing SQLite data is not needed, skip the import script; Railway will create the schema automatically.

### 3. Deploy FastAPI on Railway

1. In Railway, create a project from the GitHub repository and add one service.
2. Set its **Root Directory** to `/backend`.
3. Set the config-file path to `/backend/railway.json` if Railway does not detect it automatically.
4. Add these variables:

```text
APP_ENV=production
DATABASE_URL=<NEON_POOLED_CONNECTION_STRING>
MIGRATION_DATABASE_URL=<NEON_DIRECT_CONNECTION_STRING>
FRONTEND_ORIGINS=https://temporary.example.com
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=none
SESSION_TTL_SECONDS=28800
LOG_LEVEL=INFO
```

5. Deploy. The configured start command applies pending migrations before starting one Uvicorn worker.
6. In **Settings > Networking**, generate a public Railway domain.
7. Open `https://<railway-domain>/health`; it should return `{"status":"ok","environment":"production"}`.

One worker is deliberate because the current opaque login sessions live in process memory. A deployment/restart can log users out, but invoices, customers, company data, receipts, and credit notes remain safely stored in Neon. Moving sessions to a database/Redis is only needed for multiple backend replicas or restart-persistent logins.

### 4. Deploy React on Vercel Hobby

1. Import the same GitHub repository as a new Vercel project.
2. Set **Root Directory** to `frontend` and keep the detected Vite settings (`npm run build`, output `dist`).
3. Add this environment variable for Production and Preview:

```text
VITE_API_BASE_URL=https://<railway-domain>
```

4. Deploy and copy the production Vercel URL.
5. In Railway, replace the placeholder `FRONTEND_ORIGINS` with the exact Vercel URL, without a trailing slash, and redeploy.
6. Test signup/login, customer creation, draft issue, invoice PDF, receipt entry, credit note, and receivables.

The included `frontend/vercel.json` sends client-side routes back to `index.html`. Vite only exposes build-time environment variables prefixed with `VITE_`.

### 5. Link it from the company website

The Vercel production URL is already public and can be used directly as the link on the main company website. For a cleaner address, attach a subdomain such as `billing.example.com` to Vercel. Optionally attach `api.example.com` to Railway, change `VITE_API_BASE_URL`, and set `FRONTEND_ORIGINS=https://billing.example.com`.

With frontend and API on sibling company subdomains, `SESSION_COOKIE_SAMESITE=lax` can be used. When using unrelated `vercel.app` and `railway.app` domains, retain `none` with secure cookies; browser privacy settings may still restrict cross-site cookies, so company subdomains are the more reliable production arrangement.

## Deployment checklist

- `/health` works on Railway.
- Vercel contains the correct `VITE_API_BASE_URL` and has been rebuilt after changing it.
- Railway `FRONTEND_ORIGINS` exactly matches every allowed frontend origin (comma-separated if needed).
- No Neon URL or `.env` file is committed.
- `python scripts/upgrade_database.py` reports the latest revision.
- The GitHub Actions `CI` workflow passes for backend tests and the frontend build.
- Existing SQLite-to-Neon row counts were reviewed if data was imported.
- Signup/login and all core financial workflows pass a browser smoke test.

## Proposed features and improvements (not implemented)

These are explicitly deferred from the current release:

- Fiscal-period locking and a complete audit-history/event log.
- Detailed GST treatment such as place of supply, CGST/SGST versus IGST, HSN/SAC, rounding policies, and filing integrations.
- Stronger export/LUT validity and invoice-compliance validation.
- Report filters by date, financial year, and customer; spreadsheet/PDF exports; GST breakdown, collection reports, cash-flow view, and drill-down.
- Database/Redis-backed login sessions, password reset, email verification, user administration, and multi-worker backend scaling.
- Automated browser end-to-end tests, monitoring/error tracking, scheduled backups, and a disaster-recovery drill.

Consult a chartered accountant before treating generated documents or totals as tax-filing advice.

## Official deployment references

- [Railway FastAPI deployment](https://docs.railway.com/guides/fastapi)
- [Railway monorepo root directories](https://docs.railway.com/deployments/monorepo)
- [Neon Python connections](https://neon.com/docs/guides/python)
- [Neon connection pooling](https://neon.com/docs/connect/connection-pooling)
- [Vercel monorepos](https://vercel.com/docs/monorepos)
- [Vite on Vercel](https://vercel.com/docs/frameworks/frontend/vite)
