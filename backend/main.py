import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from core.config import get_settings
from routers import auth, billing_settings, company, credit_notes, customers, invoices, lut_certificates, receipts, reports, tax
from services.errors import ServiceError

settings = get_settings()
app = FastAPI(title="MSME Billing & Receivable Tool")
logger = logging.getLogger(__name__)


@app.exception_handler(ServiceError)
def service_error_handler(_request: Request, exc: ServiceError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(SQLAlchemyError)
def database_error_handler(request: Request, exc: SQLAlchemyError):
    logger.exception("Database error while handling %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "The data could not be saved. Check the field values and try again."},
    )


@app.exception_handler(Exception)
def unexpected_error_handler(request: Request, exc: Exception):
    logger.exception("Unexpected error while handling %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "The request could not be completed. Please try again."},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.frontend_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(billing_settings.router)
app.include_router(company.router)
app.include_router(credit_notes.router)
app.include_router(customers.router)
app.include_router(invoices.router)
app.include_router(lut_certificates.router)
app.include_router(receipts.router)
app.include_router(reports.router)
app.include_router(tax.router)


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.app_env}
