# Deploy to Hostinger VPS with CyberPanel and MariaDB

This runbook deploys the billing frontend at `https://billing.grovisor.co.in` and the FastAPI backend at `https://api-billing.grovisor.co.in`. MariaDB runs locally on the same VPS. The backend is never exposed directly to the internet; OpenLiteSpeed serves the frontend and reverse-proxies the API over localhost.

## Target layout

```text
/home/grovisor.co.in/apps/msme_bill_app/       private application files
  backend/
  frontend/
  .env                                         production secrets, never public
  logs/

/home/grovisor.co.in/public_html/billing/      built frontend only
  index.html
  assets/
  .htaccess
```

CyberPanel may choose a slightly different document-root path when it creates `billing.grovisor.co.in`. This VPS uses `/home/grovisor.co.in/public_html/billing`. Use the path displayed in **Websites > List Websites > Manage** for that site in every command below. Do not place `backend/`, `.env`, a virtual environment, backups, or the SQLite database inside `public_html`.

## 1. Prepare DNS, CyberPanel sites, and TLS

1. In Cloudflare DNS, create `A` records for `billing.grovisor.co.in` and `api-billing.grovisor.co.in`, both pointing to this VPS public IP. Keep the records **DNS only** (grey cloud) while CyberPanel issues the initial Let's Encrypt certificates.
2. In CyberPanel, create the two subdomains under the `grovisor.co.in` website. In the **Domain Name** field, enter the complete hostname, not only its first label: `billing.grovisor.co.in`, then `api-billing.grovisor.co.in`. Use document roots `public_html/billing` and `public_html/api` respectively. The document root for `api-billing.grovisor.co.in` will not serve application files, but the website is required for its virtual host and SSL certificate. CyberPanel's local DNS zone can remain in place for server-side administration; Cloudflare is the public authoritative DNS provider.
3. In CyberPanel, issue Let's Encrypt certificates for both sites. Confirm these URLs open with HTTPS before continuing:

```text
https://billing.grovisor.co.in
https://api-billing.grovisor.co.in
```

After both certificates are issued and the application works, you may enable Cloudflare proxying (orange cloud) for the two records. Set Cloudflare SSL/TLS encryption mode to **Full (strict)** so Cloudflare validates the certificates installed by CyberPanel. Do not use Flexible SSL.

## 2. Upload the source code

From PowerShell on the development computer, run this from the repository root. It creates a Windows-native ZIP that excludes Git history, local virtual environments, build output, SQLite data, backups, and environment secrets.

```powershell
$archivePath = Join-Path $env:USERPROFILE "Downloads\msme_bill_app.zip"
$stagePath = Join-Path $env:TEMP ("msme_bill_stage_" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $stagePath | Out-Null

robocopy $PWD $stagePath /E /XD .git .venv venv node_modules dist backups /XF .env *.db *.zip | Out-Null
if ($LASTEXITCODE -gt 7) { throw "Staging files failed with exit code $LASTEXITCODE" }

$stagedItems = Get-ChildItem -LiteralPath $stagePath -Force | ForEach-Object FullName
Compress-Archive -LiteralPath $stagedItems -DestinationPath $archivePath -CompressionLevel Optimal -Force
Remove-Item -LiteralPath $stagePath -Recurse -Force

$verifyPath = Join-Path $env:TEMP ("msme_bill_verify_" + [guid]::NewGuid())
Expand-Archive -LiteralPath $archivePath -DestinationPath $verifyPath -ErrorAction Stop
Remove-Item -LiteralPath $verifyPath -Recurse -Force
```

The resulting `msme_bill_app.zip` is in your Downloads folder. The final `Expand-Archive` command verifies it using Windows' own extraction engine. It is not necessary to extract the ZIP manually before uploading it.

Upload it to the VPS:

```powershell
scp $archivePath root@YOUR_VPS_IP:/root/
```

The archive is written outside the repository, so it cannot include itself while it is being created.

On the VPS, extract it into the private application directory:

```bash
mkdir -p /home/grovisor.co.in/apps/msme_bill_app
unzip /root/msme_bill_app.zip -d /home/grovisor.co.in/apps/msme_bill_app
```

If the archive creates an additional top-level folder, move its contents into `/home/grovisor.co.in/apps/msme_bill_app` so that `backend/` and `frontend/` are direct children. Verify:

```bash
ls -la /home/grovisor.co.in/apps/msme_bill_app
```

For later releases, repeat the archive/upload process, stop the service, extract the new version over the existing source, reinstall dependencies if `backend/requirements.txt` changed, rebuild the frontend, run migrations, and start the service.

## 3. Create the MariaDB database

MariaDB 10.11 is already installed on this VPS. In CyberPanel, use **Databases > Create Database** and select the `grovisor.co.in` website.

Use these values where CyberPanel permits them:

```text
Database: grov_msme_billing_db
User:     grov_msme_user
```

CyberPanel may enforce its own prefix. Use the complete database and username it displays after creation. Generate and record a long random password. In phpMyAdmin, confirm the database collation is `utf8mb4_unicode_ci`; InnoDB is the normal storage engine.

Do not create a remote database connection. The application uses `127.0.0.1`, so MariaDB remains reachable only within the VPS.

Useful checks as root:

```bash
mysql --version
mysql -e "SHOW VARIABLES LIKE 'datadir';"
systemctl status mariadb --no-pager
```

## 4. Configure and install the backend

Install system packages once:

```bash
apt update
apt install -y python3-venv python3-pip nodejs npm unzip
node --version
npm --version
```

Node.js must be version 20, 21, or 22. If Ubuntu's package gives an older version, install a supported Node.js release before building the frontend.

Create `/home/grovisor.co.in/apps/msme_bill_app/.env` with restrictive permissions:

```bash
cd /home/grovisor.co.in/apps/msme_bill_app
nano .env
chmod 600 .env
```

Use this content, replacing the placeholders. If the password contains `@`, `:`, `/`, `?`, `#`, or `%`, URL-encode those characters before placing it in the connection URL.

```env
APP_ENV=production
DATABASE_URL=mysql+pymysql://grov_msme_user:URL_ENCODED_PASSWORD@127.0.0.1:3306/grov_msme_billing_db?charset=utf8mb4
MIGRATION_DATABASE_URL=mysql+pymysql://grov_msme_user:URL_ENCODED_PASSWORD@127.0.0.1:3306/grov_msme_billing_db?charset=utf8mb4
FRONTEND_ORIGINS=https://billing.grovisor.co.in
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=lax
SESSION_TTL_SECONDS=28800
LOG_LEVEL=INFO
```

Install dependencies and create the schema:

```bash
cd /home/grovisor.co.in/apps/msme_bill_app/backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python scripts/upgrade_database.py
```

If local SQLite records must be retained, copy the current `backend/db/msme_billing.db` to the VPS before this step, then run the importer only after `upgrade_database.py` completes:

```bash
python scripts/migrate_sqlite_to_database.py
```

The importer refuses a non-empty target database and prints verified row counts. Skip it for a brand-new production database.

Create a service account and install the systemd unit:

```bash
useradd --system --no-create-home --shell /usr/sbin/nologin msmebill
mkdir -p /home/grovisor.co.in/apps/msme_bill_app/logs
chown -R msmebill:msmebill /home/grovisor.co.in/apps/msme_bill_app
cp /home/grovisor.co.in/apps/msme_bill_app/deployment/cyberpanel/msme-bill-backend.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now msme-bill-backend
systemctl status msme-bill-backend --no-pager
curl http://127.0.0.1:8001/health
```

The expected response is `{"status":"ok","environment":"production"}`. Inspect failures with:

```bash
journalctl -u msme-bill-backend -n 100 --no-pager
```

## 5. Build and publish the frontend

Build the React app with the production API address. The value is compiled into static files, so it must be set before each build.

```bash
cd /home/grovisor.co.in/apps/msme_bill_app/frontend
npm ci
VITE_API_BASE_URL=https://api-billing.grovisor.co.in npm run build
```

Copy only the built files to the document root displayed by CyberPanel for `billing.grovisor.co.in`:

```bash
cp -a dist/. /home/grovisor.co.in/public_html/billing/
cp /home/grovisor.co.in/apps/msme_bill_app/deployment/cyberpanel/frontend/.htaccess /home/grovisor.co.in/public_html/billing/.htaccess
```

The `.htaccess` rule returns `index.html` for unknown paths, allowing browser refreshes on React routes instead of a 404.

## 6. Reverse-proxy the API through OpenLiteSpeed

In CyberPanel's OpenLiteSpeed WebAdmin, edit the virtual host for `api-billing.grovisor.co.in` and add a proxy context that forwards all paths to:

```text
http://127.0.0.1:8001
```

The exact screen labels vary by CyberPanel release. The required result is an external application of type **Proxy** with address `127.0.0.1:8001`, and a context for URI `/` that uses that proxy application. Do not proxy to `0.0.0.0:8001`, and do not open port `8001` in Hostinger's firewall.

Gracefully restart OpenLiteSpeed after saving the virtual-host configuration:

```bash
systemctl restart lsws
curl https://api-billing.grovisor.co.in/health
```

The second command must return the same health JSON over HTTPS. If it does not, check OpenLiteSpeed's error log and `journalctl -u msme-bill-backend` before changing application code.

## 7. Verify the deployed app

1. Open `https://billing.grovisor.co.in` in an incognito window.
2. Sign up or log in. The browser network panel should show a successful `POST https://api-billing.grovisor.co.in/auth/login` and a secure `msme_session` cookie for the API host.
3. Create company details and a customer.
4. Create and issue an invoice, then open its PDF.
5. Record a receipt and verify receivable totals.
6. Create a credit note, then log out and back in.
7. Refresh a non-root frontend route to confirm the SPA rewrite works.

## 8. Backups and routine operations

Create a private backup directory outside `public_html`:

```bash
mkdir -p /home/grovisor.co.in/backups/msme_bill_app
chmod 700 /home/grovisor.co.in/backups/msme_bill_app
```

Create `/usr/local/sbin/backup-msme-bill`:

```bash
#!/usr/bin/env bash
set -euo pipefail
backup_dir=/home/grovisor.co.in/backups/msme_bill_app
timestamp=$(date +%F_%H%M%S)
mysqldump --single-transaction --routines --triggers grov_msme_billing_db | gzip > "$backup_dir/msme_billing_$timestamp.sql.gz"
find "$backup_dir" -type f -name 'msme_billing_*.sql.gz' -mtime +14 -delete
```

Make it executable, test it once, and schedule it daily at 02:15:

```bash
chmod 700 /usr/local/sbin/backup-msme-bill
/usr/local/sbin/backup-msme-bill
crontab -e
```

Add this cron line:

```cron
15 2 * * * /usr/local/sbin/backup-msme-bill
```

The MySQL password must be available to `mysqldump` without appearing in the command line. The cleanest approach is a root-only `/root/.my.cnf` file containing the database credentials. Store a copy of the encrypted backups off the VPS as well; a backup that shares the server's disk does not protect against VPS loss.

For an application update:

```bash
systemctl stop msme-bill-backend
cd /home/grovisor.co.in/apps/msme_bill_app/backend
source .venv/bin/activate
pip install -r requirements.txt
python scripts/upgrade_database.py
systemctl start msme-bill-backend
systemctl status msme-bill-backend --no-pager
```

Rebuild and copy the frontend whenever `frontend/` changes. Restart OpenLiteSpeed only when its configuration changes.

## Troubleshooting

- `502 Bad Gateway`: `systemctl status msme-bill-backend --no-pager`, then `journalctl -u msme-bill-backend -n 100 --no-pager`.
- API returns a CORS error: ensure `FRONTEND_ORIGINS` is exactly `https://billing.grovisor.co.in`, with no trailing slash, then restart the service.
- Login succeeds but the browser immediately appears logged out: confirm both subdomains use HTTPS and `SESSION_COOKIE_SECURE=true` and `SESSION_COOKIE_SAMESITE=lax`.
- Database connection error: verify the complete CyberPanel-generated database/user names and test with `mysql -u USER -p DATABASE` from the VPS.
- React route returns 404 after refresh: verify that `.htaccess` was copied into the actual billing site document root and that OpenLiteSpeed allows rewrite rules for the vhost.
