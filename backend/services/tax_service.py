from decimal import Decimal

from sqlalchemy.orm import Session

from db import models
from services.errors import ServiceError
from services.financial import money


def _jurisdiction_name(db: Session, tenant_id: str, code: str) -> str:
    if not code:
        return ""
    jurisdiction = db.query(models.TaxJurisdiction).filter_by(
        tenant_id=tenant_id, country_code="IN", code=code, is_active=True
    ).first()
    return jurisdiction.name if jurisdiction else ""


def calculate_invoice_tax(db: Session, tenant_id: str, tenant: models.Tenant, customer: models.Customer, subtotal: Decimal, gst_rate: Decimal):
    """Return the tax snapshot. Rates remain an explicit invoice input; the
    jurisdiction catalogue is tenant-owned data used for display/validation."""
    if customer.is_foreign:
        return {"rate": Decimal("0"), "gst": Decimal("0"), "cgst": Decimal("0"), "sgst": Decimal("0"), "igst": Decimal("0"), "treatment": "export_lut", "place_code": "", "place_name": ""}
    supplier_code = (tenant.state_code or tenant.gstin[:2]).strip()
    customer_code = (customer.state_code or customer.gstin[:2]).strip()
    if not supplier_code or not customer_code:
        raise ServiceError(400, "Supplier and customer state codes are required for GST calculation")
    tax = money(subtotal * Decimal(gst_rate) / Decimal("100"))
    if supplier_code == customer_code:
        cgst = money(tax / 2)
        return {"rate": Decimal(gst_rate), "gst": money(cgst * 2), "cgst": cgst, "sgst": cgst, "igst": Decimal("0"), "treatment": "cgst_sgst", "place_code": customer_code, "place_name": _jurisdiction_name(db, tenant_id, customer_code)}
    return {"rate": Decimal(gst_rate), "gst": tax, "cgst": Decimal("0"), "sgst": Decimal("0"), "igst": tax, "treatment": "igst", "place_code": customer_code, "place_name": _jurisdiction_name(db, tenant_id, customer_code)}
