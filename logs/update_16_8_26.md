# Project Progress & Next Session Plan

**Date**: 2026-08-16

## Summary of Progress to Date (2026-08-16)

### 1. Deployment Direction Finalized

- Decided to use:
  - **Vercel Hobby** for the React frontend.
  - **Railway** for the FastAPI backend.
  - **Neon PostgreSQL** for the production database.
- PythonAnywhere was not selected because the application uses FastAPI/ASGI and we also want an easier path for deploying future applications.
- Added a detailed deployment reference in `DEPLOYMENT.md`.
- Updated `README.md` with the current features, project structure, local setup, deployment overview, and proposed future improvements.

### 2. Backend Code Cleanup

- Kept FastAPI endpoints inside `backend/routers/`.
- Added `backend/services/` for the actual business functions used by the routers.
- Routers are now mainly responsible for receiving requests and returning responses.
- Invoice, receipt, customer, company, credit-note, report, authentication, and PDF logic is now separated into service files.
- This should make future edits easier because business rules no longer need to be mixed with API route definitions.

### 3. Database and Deployment Configuration

- Moved the local SQLite database from `backend/msme_billing.db` to:

  ```text
  backend/db/msme_billing.db
  ```

- Created and verified a backup at:

  ```text
  backups/20260816_113734/msme_billing.db
  ```

- The working database and backup had matching file hashes, and SQLite's integrity check returned `ok`.
- Added environment-based database configuration so the app can use either local SQLite or Neon PostgreSQL.
- Added Alembic database migrations instead of creating tables directly whenever the backend starts.
- Added `upgrade_database.py` to create or update database tables.
- Added `migrate_sqlite_to_postgres.py` to copy existing SQLite records into a prepared Neon database.
- Added `.env.example` and `.gitignore`.
- Database files, backups, `.env`, virtual environments, `node_modules`, and frontend build files are excluded from Git.
- Added `docker-compose.yml` only as an optional way to test PostgreSQL locally. It is not required for the Vercel + Railway + Neon deployment.

### 4. Invoice and Customer Workflows

- Added editable invoice drafts.
- Invoice numbers are assigned only when a draft is issued.
- Issued invoices cannot be edited directly.
- Added invoice cancellation with a required reason.
- Cancellation is blocked while active receipts or credit notes still exist.
- Added company and customer snapshots so later master-data edits do not rewrite an already-issued invoice.
- Added customer editing, archival, and restoration.
- Customers with invoice history cannot be permanently deleted and should be archived instead.

### 5. Receipt and Credit-Note Workflows

- Added receipt editing.
- Added receipt voiding and restoration so incorrect entries can be corrected without silently deleting history.
- Added checks to prevent receipts from exceeding the outstanding invoice balance.
- Added credit-note creation and cancellation.
- Added separate financial-year numbering for credit notes.
- Credit notes reduce receivables and current sales reports.

### 6. Invoice and Credit-Note Documents

- Added actual PDF generation for invoices.
- Added PDF generation for credit notes.
- PDFs can be viewed or downloaded from the frontend.
- Cancelled documents show their cancelled status and reason.

### 7. Frontend Updates

- Updated the frontend to use `VITE_API_BASE_URL` instead of a fixed localhost backend URL.
- Added screens/actions for:
  - Draft invoice creation and editing.
  - Invoice issuing and cancellation.
  - Invoice PDF viewing and downloading.
  - Customer editing, archival, and restoration.
  - Receipt editing, voiding, and restoration.
  - Credit-note creation, cancellation, and PDF viewing.
- Kept the current reports simple, but made area-wise and product-wise sales use the same pre-GST, net-of-credit basis.

### 8. Tests and Verification

- Added backend tests for:
  - Tenant separation.
  - Invoice draft and issue rules.
  - Customer archival.
  - Invoice and credit-note PDFs.
  - Receipt correction and overpayment protection.
  - Credit notes and cancellation rules.
  - Receivables and sales reports.
- Added a GitHub Actions workflow to run backend tests and build the frontend after code is pushed.
- The frontend production build completed successfully.
- Backend tests have not yet been run locally because the old `backend/venv` points to a Python installation that no longer exists.

### 9. Git Status

- Initialized a local Git repository using the `main` branch.
- Created the first local commit:

  ```text
  9885125 Prepare MSME billing app for deployment
  ```

- No GitHub remote repository has been connected yet.
- This log was created after the first commit, so it must be included in the next commit.

---

## Plan for Next Session

1. **Create and Connect the GitHub Repository**

   - Create an empty private repository on GitHub.
   - Do not add another README, `.gitignore`, or license on GitHub.
   - Commit this new log and push the project:

   ```powershell
   cd C:\Work\MSME_Bill_Tool
   git add .
   git commit -m "Add August 16 project update"
   git remote add origin https://github.com/<username>/MSME_Bill_Tool.git
   git push -u origin main
   ```

2. **Check GitHub Actions**

   - Open the repository's **Actions** tab.
   - Confirm that the backend tests and frontend build pass.
   - If the backend tests fail, fix them before beginning deployment.

3. **Repair the Local Python Environment**

   - Install Python 3.12 if it is not already installed.
   - Create a new environment at `backend/.venv`.
   - Install `backend/requirements.txt`.
   - Run `python scripts/upgrade_database.py` and `pytest` from the backend directory.

4. **Create the Neon Database**

   - Create a Neon project.
   - Copy the pooled connection string for the application.
   - Copy the direct connection string for database migrations.
   - Run `upgrade_database.py` against Neon.
   - Run `migrate_sqlite_to_postgres.py` once if the existing SQLite records need to be preserved.

5. **Deploy the FastAPI Backend to Railway**

   - Connect the GitHub repository.
   - Set the Railway root directory to `/backend`.
   - Add the Neon connection strings and other variables listed in `DEPLOYMENT.md`.
   - Deploy and generate a public Railway domain.
   - Verify the `/health` endpoint.

6. **Deploy the Frontend to Vercel**

   - Import the same GitHub repository.
   - Set the Vercel root directory to `frontend`.
   - Set `VITE_API_BASE_URL` to the Railway backend URL.
   - Deploy and copy the Vercel production URL.

7. **Finish the Frontend/Backend Connection**

   - Set Railway `FRONTEND_ORIGINS` to the exact Vercel production URL.
   - Redeploy Railway.
   - Run the complete browser smoke test listed in `DEPLOYMENT.md`.

8. **Link the Application From the Company Website**

   - Initially use the Vercel production URL.
   - Later, consider `billing.<company-domain>` for Vercel and `api.<company-domain>` for Railway.

## Features Intentionally Left for Later

- Fiscal-period locking.
- A complete audit-history screen.
- Detailed CGST/SGST/IGST and place-of-supply handling.
- Stronger LUT/export validation.
- Date, financial-year, and customer report filters.
- Report exports, collection reports, cash-flow view, and drill-down.
- Persistent login sessions for multiple backend workers.

Refer to `DEPLOYMENT.md` for deployment commands and `README.md` for the current application scope and structure.
