# Project Progress & Next Session Plan

**Date**: 2026-07-27  

## Summary of Progress to Date (2026-07-27)

### 1. Backend Architecture Restructuring
- Restructured the backend codebase into a clean, scalable modular package layout under `backend/`.
- Isolated database logic into `backend/db/` (`database.py`, `models.py`, `schemas.py`).
- Extracted session handling into `backend/core/session.py`.
- Separated API endpoints into dedicated routers (`routers/auth.py`, `company.py`, `lut.py`, `customers.py`, `invoices.py`, `receipts.py`, `reports.py`).

### 2. Frontend UI Fixes & Line Item Enhancements
- Fixed line item input rendering in `frontend/src/App.jsx` on the **New Invoice** screen:
  - Fixed QTY input field truncation by increasing its grid span allocation from `col-span-1` to `col-span-2`.
  - Added `min-w-0` to input classes to ensure number spinner arrows and input text fit properly.
  - Standardized column layout across Description, Category, Qty, Rate, and Amount.
  - Added a formatted **AMOUNT** header and aligned line item totals with delete buttons cleanly.

---

## Plan for Next Session

1. **WSGI Compatibility**:
   - **Option A**: Use `a2wsgi` to adapt the current FastAPI (ASGI) application to WSGI format.
   - **Option B**: Port the backend API from FastAPI to Flask if native WSGI execution is preferred.

2. **Deployment Strategy & Hosting Architecture Evaluation**:
   - Configure hosting setup on PythonAnywhere and perform a cost comparison.
   - Evaluate deployment strategies to determine optimal infrastructure for our use-case:
     - **Strategy 1 (All-in-One PythonAnywhere)**: Host full stack (FastAPI/Flask app, SQLite/Postgres DB, static assets) on PythonAnywhere.
     - **Strategy 2 (All-in-One Self-Hosted / Current Server)**: Host full application on our current server space if hardware resources, cost-to-performance ratio, and flexibility outperform PythonAnywhere.
     - **Strategy 3 (Hybrid Architecture)**: Run the Python web application/API on PythonAnywhere, while routing database (Postgres) and file storage to our dedicated server space.
   - Compare tradeoffs across each strategy regarding latency, database connection pooling, maintenance overhead, security, and monthly cost.

3. **Server Space, Resource & Cost Assessment**:
   - Evaluate storage, memory, CPU limits, and database disk footprint for our MSME Billing workload.
   - Compare existing server space and bandwidth availability against PythonAnywhere pricing tiers and quota limits.

4. **Git Version Control & Repository Update**:
   - Stage, commit, and push all recent refactoring changes, UI fixes, and log updates to Git (`git add .`, `git commit`, `git push`).
