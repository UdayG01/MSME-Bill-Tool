from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from routers import auth, company, credit_notes, customers, invoices, receipts, reports
from services.errors import ServiceError

settings = get_settings()
app = FastAPI(title="MSME Billing & Receivable Tool")


@app.exception_handler(ServiceError)
def service_error_handler(_request: Request, exc: ServiceError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.frontend_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(company.router)
app.include_router(credit_notes.router)
app.include_router(customers.router)
app.include_router(invoices.router)
app.include_router(receipts.router)
app.include_router(reports.router)


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.app_env}
