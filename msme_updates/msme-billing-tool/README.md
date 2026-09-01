# MSME Billing Utility — Revised Package (Phase 1)

This is the updated build incorporating everything scoped in our Phase 1
conversation: domestic GST compliance fixes, export/LUT invoicing in
foreign currency, branding, and commercial completeness.

## What's new in this revision

**Domestic invoice compliance:**
- Automatic IGST vs CGST+SGST detection, based on supplier vs customer
  GSTIN state codes (previously showed a generic "GST" figure regardless
  of place of supply)
- Place of Supply printed on every invoice
- HSN/SAC column properly labelled (was just "Category" before)
- Reverse Charge Applicable line

**Export invoicing (new):**
- Foreign currency invoices (USD/EUR/GBP/AED/SGD), selected per customer
- Manual exchange rate entry per invoice — used only for internal
  records, never printed on the invoice itself
- Zero-rated under LUT, with the LUT declaration folded into Terms & Notes
  (not a heavy standalone box) and LUT ARN/validity shown in the invoice
  meta table
- International wire transfer bank details (SWIFT, bank address) instead
  of domestic IFSC
- All internal reporting (ageing, receivables) uses a frozen INR
  equivalent computed at invoice creation — the ledger itself is always
  single-currency, so ageing/MIS logic never has to convert on the fly
- Forex gain/loss automatically calculated at receipt time, based on the
  difference between the invoicing exchange rate and the realized rate
- FIRC (Foreign Inward Remittance Certificate) number capture on receipts

**Branding & commercial completeness:**
- Company logo upload, shown top-left on every invoice
- Authorized signature image upload, shown in the signature block
  (no more printing and manually signing each invoice)
- Udyam Registration Number field, printed next to GSTIN/CIN
- Campaign tagline field — a single line you update manually, shown as a
  banner at the bottom of every invoice
- Terms & Notes box with sensible defaults, editable in Company Master
- Mandatory Payment Terms field on every customer — invoice due dates are
  now always computed automatically, never left blank
- UPI ID + QR code on domestic invoices (skipped automatically for
  export invoices, where it's not applicable)
- Amount in words, in the invoice's own currency

**Layout fixes:**
- All tables now consistently span the full printable A4 width
- Multi-page invoices repeat the item table header on every page, and
  keep totals/signature/bank details together so they never get
  orphaned across a page break

## What's deliberately NOT in this phase

Per our phased roadmap, these are scoped for later and intentionally
left out for now:
- Bulk/recurring invoicing, credit/debit notes (Phase 3)
- CRM features — follow-up logs, tags, automated reminders (Phase 4)
- Customer-wise reports, DSO, Statement of Account (Phase 5)
- PostgreSQL migration, multi-user roles (Phase 6)

## Project structure

```
msme-billing-tool/
├── backend/                  FastAPI + SQLAlchemy + SQLite
│   ├── app/
│   │   ├── models.py          Database tables
│   │   ├── schemas.py         Request/response validation
│   │   ├── gst_utils.py        IGST/CGST-SGST logic, state codes
│   │   ├── invoice_numbering.py  Sequential FY-based numbering
│   │   ├── pdf_generator.py    Domestic + export invoice PDF templates
│   │   ├── main.py             App entrypoint
│   │   └── routers/            company, lut, customers, invoices, receipts, reports
│   └── requirements.txt
├── frontend/                 React (Vite) + Tailwind
│   └── src/pages/             CompanySetup, LUTSetup, Customers, CreateInvoice,
│                               InvoiceList, ReceiptEntry, AgeingReport
├── setup.bat                 Windows: installs everything (run once)
└── start.bat                 Windows: launches both servers
```

## Running locally (Windows)

1. Double-click `setup.bat` — installs Python and Node dependencies.
   Requires Python 3.10+ and Node.js 18+ already installed.
2. Double-click `start.bat` — opens two server windows and your browser
   to `http://localhost:5173`.
3. First-time use: go to **Company Setup** and fill in your details
   (including logo/signature upload), then **LUT Master** if you'll be
   issuing export invoices, then **Customers**, then start creating
   invoices.

## Deploying to your existing hosting

Since the tool is already live on your website infrastructure rather
than Render.com, you (or whoever manages that hosting) will need to:

1. Replace the backend code with the `backend/` folder here (keep the
   existing database file if you want to preserve invoices already
   issued — it's the `msme_billing.db` file, untouched by this update
   since no existing table columns were removed, only added).
2. Run `pip install -r requirements.txt` on the server to pick up the
   two new dependencies (`qrcode`, `num2words`) alongside existing ones.
3. Replace the frontend code with the `frontend/` folder and rebuild
   (`npm install && npm run build`), then redeploy the built `dist/`
   folder the same way it's served today.
4. No environment variable or config changes are required — the only
   new setting is optional (`DATABASE_URL`, if you ever move off SQLite).

If you're not sure how your current hosting is structured, let me know
and I can walk through it step by step once you have access details.

## Known limitations to be aware of

- Exchange rate entry is manual with no automated sanity-check yet
  (e.g. flagging a rate that looks implausibly different from typical
  market range) — worth adding once real usage starts.
- Logo/signature images are stored as local files on the server;
  fine for a single-tenant deployment, but would need to move to
  cloud storage (S3-equivalent) if this ever becomes multi-tenant.
- CORS is currently wide open (`allow_origins=["*"]`) since the app
  runs on your own infrastructure — tighten this to your exact domain
  before/if this is ever exposed more broadly.
