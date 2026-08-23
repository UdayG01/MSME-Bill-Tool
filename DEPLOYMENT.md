# Deployment Runbook

This runbook deploys the application using:

- Neon PostgreSQL for persistent business data.
- Railway for the FastAPI backend.
- Vercel Hobby for the React/Vite frontend.

Follow the sections in order. Values written as `<PLACEHOLDER>` must be replaced with real values.

## 1. Local prerequisites and verification

Install:

- Python 3.12.
- Node.js 20 or 22.
- Git.
- A GitHub account.

The old `backend/venv` is not usable because it references a removed Python installation. Create a new environment without deleting the old one:

```powershell
cd C:\Work\MSME_Bill_Tool
py -3.12 -m venv backend/.venv
backend\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

Upgrade the local SQLite database and run the backend tests:

```powershell
cd backend
python scripts/upgrade_database.py
pytest
```

Build the frontend:

```powershell
cd ..\frontend
npm ci
npm run build
cd ..
```

Do not continue until `pytest` and `npm run build` pass.

## 2. Confirm the local database backup

The working SQLite database should be located at:

```text
backend/db/msme_billing.db
```

A pre-change backup is located at:

```text
backups/20260816_113734/msme_billing.db
```

Before migrating important data, make another timestamped copy outside the repository or in a secure backup location. Never commit database files or connection strings to Git.

## 3. Create and push the Git repository

This directory did not originally contain a Git repository. Create one and push it to a private GitHub repository:

```powershell
cd C:\Work\MSME_Bill_Tool
git init
git add .
git commit -m "Prepare MSME billing app for deployment"
git branch -M main
git remote add origin <GITHUB_REPOSITORY_URL>
git push -u origin main
```

Confirm on GitHub that none of the following were uploaded:

- `.env`
- `backend/db/msme_billing.db`
- `backups/`
- `backend/.venv/` or `backend/venv/`
- `frontend/node_modules/`

Wait for the GitHub Actions `CI` workflow to pass.

## 4. Create the Neon PostgreSQL database

1. Sign in to Neon and create a project.
2. Create or select the production database.
3. Open the **Connect** dialog.
4. Copy the pooled connection string. Its hostname normally contains `-pooler`.
5. Disable connection pooling in the dialog and copy the direct connection string.

Use the strings as follows:

```text
DATABASE_URL=<NEON_POOLED_CONNECTION_STRING>
MIGRATION_DATABASE_URL=<NEON_DIRECT_CONNECTION_STRING>
```

Keep the SSL parameters provided by Neon. Do not put either URL in a committed file.

Official references:

- [Neon Python connection guide](https://neon.com/docs/guides/python)
- [Neon connection pooling](https://neon.com/docs/connect/connection-pooling)

## 5. Create the Neon schema and migrate SQLite data

Run the migration from a trusted local terminal with the new Python environment active:

```powershell
cd C:\Work\MSME_Bill_Tool
backend\.venv\Scripts\Activate.ps1
$env:DATABASE_URL="<NEON_POOLED_CONNECTION_STRING>"
$env:MIGRATION_DATABASE_URL="<NEON_DIRECT_CONNECTION_STRING>"
cd backend
python scripts/upgrade_database.py
python scripts/migrate_sqlite_to_postgres.py
```

Expected behavior:

- `upgrade_database.py` creates the Neon schema and records its Alembic version.
- `migrate_sqlite_to_postgres.py` refuses to import if the target business tables already contain data.
- The import prints and verifies row counts for every copied table.

Save the printed row counts with your deployment notes. If the existing SQLite records are not required, run only `upgrade_database.py` and skip the import.

Do not repeatedly run the import against the same Neon database.

## 6. Deploy the FastAPI backend to Railway

1. Sign in to Railway and create a new project.
2. Choose **Deploy from GitHub repo** and select the repository.
3. Create/select the backend service.
4. In service settings, set **Root Directory** to `/backend`.
5. If the configuration is not detected automatically, set its path to `/backend/railway.json`.
6. Add the environment variables below.

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

The frontend URL is not known yet, so `FRONTEND_ORIGINS` temporarily contains a non-localhost placeholder. It must be replaced after the Vercel deployment.

7. Deploy the backend.
8. Review the deployment logs. They should show that the database is at the latest migration revision and that Uvicorn started successfully.
9. Open **Settings > Networking** and choose **Generate Domain**.
10. Record the resulting URL as `<RAILWAY_BACKEND_URL>`.

Verify:

```text
https://<RAILWAY_BACKEND_URL>/health
https://<RAILWAY_BACKEND_URL>/docs
```

The health response should resemble:

```json
{"status":"ok","environment":"production"}
```

Railway is configured to run one Uvicorn worker because login sessions are currently process-local. A restart may log users out, but all business records remain in Neon.

Official references:

- [Railway FastAPI deployment](https://docs.railway.com/guides/fastapi)
- [Railway monorepo deployment](https://docs.railway.com/deployments/monorepo)

## 7. Deploy the React frontend to Vercel Hobby

1. Sign in to Vercel and choose **Add New > Project**.
2. Import the same GitHub repository.
3. Set **Root Directory** to `frontend`.
4. Confirm that Vercel detects Vite.
5. Use the following settings if they are not detected:

```text
Build Command: npm run build
Output Directory: dist
Install Command: npm install or npm ci
```

6. Add this environment variable for Production and Preview:

```text
VITE_API_BASE_URL=https://<RAILWAY_BACKEND_URL>
```

7. Deploy.
8. Record the production URL as `<VERCEL_FRONTEND_URL>`.

Official references:

- [Vercel monorepos](https://vercel.com/docs/monorepos)
- [Vite on Vercel](https://vercel.com/docs/frameworks/frontend/vite)

## 8. Connect Vercel to Railway

Return to the Railway backend service and replace the placeholder:

```text
FRONTEND_ORIGINS=https://<VERCEL_FRONTEND_URL>
```

Requirements:

- Include `https://`.
- Do not include a trailing slash.
- If multiple frontend origins are required, separate them with commas.

Redeploy or restart the Railway service after saving the variable.

If `VITE_API_BASE_URL` was changed after the Vercel build, redeploy Vercel because Vite variables are embedded during the build.

## 9. Production smoke test

Open the Vercel production URL in a private/incognito browser window and test in this order:

1. Create a test company account or log in with an imported account.
2. Save company and bank details.
3. Create and edit a customer.
4. Create an invoice draft.
5. Edit the draft and issue it.
6. View and download its PDF.
7. Record and edit a receipt.
8. Void and restore a receipt.
9. Create and view a credit-note PDF.
10. Check receivables and both sales reports.
11. Log out and log in again.

If login succeeds but subsequent API requests return `401`, inspect browser cookie restrictions and the Railway CORS variables. Unrelated `vercel.app` and `railway.app` domains require:

```text
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=none
```

Some browser privacy settings can still block cross-site cookies. Custom sibling domains are the more reliable configuration.

## 10. Add company subdomains

A public Vercel URL can be linked from the main company website immediately. A cleaner long-term configuration is:

```text
billing.example.com -> Vercel
api.example.com     -> Railway
```

After configuring the DNS records requested by Vercel and Railway:

1. Set Vercel `VITE_API_BASE_URL=https://api.example.com` and redeploy.
2. Set Railway `FRONTEND_ORIGINS=https://billing.example.com` and redeploy.
3. Change Railway `SESSION_COOKIE_SAMESITE=lax` because the frontend and API are now sibling sites under the same company domain.
4. Repeat the production smoke test.
5. Add `https://billing.example.com` as the link on the main company website.

## 11. Post-deployment checks

- GitHub CI is passing.
- Railway `/health` returns production status.
- Railway logs contain no migration or database connection errors.
- Vercel uses the current API URL.
- Railway allows the exact current frontend origin.
- Signup/login and the complete invoice workflow work in a private browser window.
- Imported record counts match the SQLite counts.
- No secrets or database files are visible in GitHub.
- The SQLite backup is stored securely until the Neon data has been verified.

## 12. Updating the application later

For normal code updates:

```powershell
git add .
git commit -m "Describe the update"
git push
```

Wait for GitHub CI. Vercel and Railway should build the new commit automatically. Railway runs `scripts/upgrade_database.py` before starting, so new Alembic migrations are applied in order.

Before deploying a migration that changes or removes data, make a Neon backup/branch and test the migration there first.

## 13. Troubleshooting quick reference

### Railway cannot connect to Neon

- Recopy both Neon strings.
- Confirm that SSL query parameters remain present.
- Use the pooled string for `DATABASE_URL` and direct string for `MIGRATION_DATABASE_URL`.
- Check that the variables contain no extra quotes or whitespace in Railway.

### Browser reports a CORS error

- Confirm `FRONTEND_ORIGINS` exactly matches the browser's frontend origin.
- Remove a trailing slash.
- Redeploy Railway after changing it.

### Frontend calls localhost

- Set `VITE_API_BASE_URL` in Vercel.
- Redeploy Vercel after setting it.
- Inspect the production build rather than a previous preview URL.

### Database migration refuses to import

The target already contains business data. Do not bypass the protection. Create a fresh Neon database/branch or determine which import already populated it.

### Users are logged out after a backend deployment

This is expected in the current single-worker version because login sessions are held in backend memory. Financial and master data remain stored in Neon.

