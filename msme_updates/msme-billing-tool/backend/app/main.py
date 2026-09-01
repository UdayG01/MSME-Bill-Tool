from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .database import Base, engine
from .routers import company, lut, customers, invoices, receipts, reports

Base.metadata.create_all(bind=engine)

app = FastAPI(title="MSME Billing Utility", version="1.1.0")

# NOTE (production readiness, Phase 6 of the roadmap): lock this down to the
# real domain (e.g. https://billing.grovisor.co.in) before wider client use.
# Left permissive here since the app is served from your own hosting.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(company.router)
app.include_router(lut.router)
app.include_router(customers.router)
app.include_router(invoices.router)
app.include_router(receipts.router)
app.include_router(reports.router)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
