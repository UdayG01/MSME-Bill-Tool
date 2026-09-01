# Project Progress & Next Session Plan

**Date**: 2026-09-01

## Summary of Progress to Date (2026-09-01)

### 1. Production Hosting Moved to Hostinger VPS / CyberPanel

- Changed the production architecture from Vercel, Railway, and Neon to a Hostinger VPS running CyberPanel/OpenLiteSpeed, FastAPI, and MariaDB.
- Added `DEPLOYMENT_CYBERPANEL.md`, a detailed production runbook covering domain setup, system dependencies, the backend systemd service, OpenLiteSpeed reverse proxy configuration, frontend static hosting, environment variables, HTTPS, backups, and rollback guidance.
- Added deployment assets:
  - `deployment/cyberpanel/msme-bill-backend.service` for the FastAPI service.
  - `deployment/cyberpanel/frontend/.htaccess` for the frontend deployment.
- Updated `README.md` so the CyberPanel runbook is the current deployment reference; the original Neon/Railway/Vercel path is clearly marked as legacy.

### 2. MariaDB Support and SQLite Migration

- Added MySQL/MariaDB database URL normalization through the PyMySQL driver.
- Replaced the optional local PostgreSQL Docker setup with MariaDB 10.11, including UTF-8 configuration and a health check.
- Added `backend/scripts/migrate_sqlite_to_database.py` to import a legacy SQLite database into a fresh MariaDB/MySQL database.
- The importer preserves the supported business records, populates required lifecycle/snapshot fields where needed, rejects non-empty targets, and verifies copied row counts after the import.
- Updated application requirements and the environment example for the MariaDB deployment path.

### 3. Configurable Billing, Tax, and Export Compliance

- Added a new Alembic migration (`0003_configurable_billing.py`) for billing configuration, tax jurisdiction, LUT certificate, media asset, and additional invoice/receipt fields.
- Added tenant-level billing settings for base currency, export invoicing, valid-LUT requirements, default terms/notes, and a billing tagline.
- Added tax-jurisdiction management and tax calculation services to support tax treatment, place of supply, and CGST/SGST/IGST values.
- Added LUT certificate management, including validity dates and active status. Issuing an export invoice can now require an active, valid LUT certificate and snapshots its relevant details on the invoice.
- Added HSN/SAC support for invoice line items, customer state codes, invoice due dates, Udyam/UPI details, and international bank details.
- Added foreign-currency invoice and receipt fields, exchange-rate handling, FIRC reference support, and calculated foreign-exchange gain/loss data.
- Added API routers and services for billing settings, tax jurisdictions, and LUT certificates.

### 4. Invoice and Branding Improvements

- Updated the invoice workflow so domestic invoices use the configured base currency, while export invoices require a non-INR currency and exchange rate when export billing is enabled.
- Updated the frontend invoice editor to capture line-item HSN/SAC, export invoice currency, and the INR exchange rate.
- Added secure private-media configuration for company branding assets. Logo and signature uploads are stored outside `public_html`, subject to size and image validation limits.
- Extended the CyberPanel backup procedure to archive private branding media along with MariaDB backups.

### 5. Packaged Update Reference

- Added `msme_updates/msme-billing-tool/`, containing a separate application/update reference package.

### 6. Git Activity

Three commits were created today:

```text
db97926 cyberpanel hostinger deployment mysql migration
7579d5a adding new invoice design and compliance rules for tax exchange currency etc.
03e8ed1 edit DEPLOYMENT_CYBERPANEL.md
```

---

## Plan for Next Session

1. **Validate Locally**

   - Create or repair `backend/.venv`, install `backend/requirements.txt`, and run the Alembic upgrade.
   - Run the backend test suite and the frontend production build.
   - Exercise domestic and export invoice flows, including LUT validation, tax split, foreign currency, and receipt exchange-rate calculations.

2. **Prepare the VPS**

   - Follow `DEPLOYMENT_CYBERPANEL.md` to create the MariaDB database/user, application user, application directory, private media directory, systemd service, and OpenLiteSpeed proxy/static-site configuration.
   - Configure the production environment file with strong secret values and the approved frontend origin.

3. **Migrate and Verify Data**

   - Back up the current SQLite database.
   - Apply migrations to the fresh MariaDB database.
   - Run `migrate_sqlite_to_database.py` only if existing local records must be retained, then confirm its row-count verification output.

4. **Deploy and Smoke-Test**

   - Deploy the backend and frontend to their `api-billing` and `billing` subdomains.
   - Confirm HTTPS, the backend health endpoint, login, invoice/receipt workflows, PDF generation, and protected branding media handling.
   - Test and schedule the database-and-media backup procedure.

5. **Setup Github Actions**

   - Setup Github Actions CI/CD for easier updates directly to the repo
   - Automatic testing and backend api health checks
   - reload backend and re-live the app.


