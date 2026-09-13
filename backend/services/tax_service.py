from decimal import Decimal

from sqlalchemy.orm import Session

from db import models
from services.errors import ServiceError
from services.financial import money

GST_STATES = {"01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab", "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana", "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh", "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh", "13": "Nagaland", "14": "Manipur", "15": "Mizoram", "16": "Tripura", "17": "Meghalaya", "18": "Assam", "19": "West Bengal", "20": "Jharkhand", "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat", "26": "Dadra and Nagar Haveli and Daman and Diu", "27": "Maharashtra", "29": "Karnataka", "30": "Goa", "31": "Lakshadweep", "32": "Kerala", "33": "Tamil Nadu", "34": "Puducherry", "35": "Andaman and Nicobar Islands", "36": "Telangana", "37": "Andhra Pradesh", "38": "Ladakh", "97": "Other Territory"}


def _jurisdiction_name(db: Session, tenant_id: str, code: str) -> str:
    if not code:
        return ""
    jurisdiction = db.query(models.TaxJurisdiction).filter_by(
        tenant_id=tenant_id, country_code="IN", code=code, is_active=True
    ).first()
    return jurisdiction.name if jurisdiction else GST_STATES.get(code, "")


def calculate_invoice_tax(db: Session, tenant_id: str, tenant: models.Tenant, customer: models.Customer, subtotal: Decimal, gst_rate: Decimal):
    """Return the tax snapshot. Rates remain an explicit invoice input; the
    jurisdiction catalogue is tenant-owned data used for display/validation."""
    if customer.is_foreign:
        return {"rate": Decimal("0"), "gst": Decimal("0"), "cgst": Decimal("0"), "sgst": Decimal("0"), "igst": Decimal("0"), "treatment": "export_lut", "place_code": "", "place_name": ""}
    supplier_code = (tenant.gstin or "")[:2]
    customer_code = (customer.gstin or "")[:2]
    if supplier_code not in GST_STATES or customer_code not in GST_STATES:
        raise ServiceError(400, "Valid supplier and customer GSTINs are required for GST calculation")
    tax = money(subtotal * Decimal(gst_rate) / Decimal("100"))
    if supplier_code == customer_code:
        cgst = money(tax / 2)
        return {"rate": Decimal(gst_rate), "gst": money(cgst * 2), "cgst": cgst, "sgst": cgst, "igst": Decimal("0"), "treatment": "cgst_sgst", "place_code": customer_code, "place_name": _jurisdiction_name(db, tenant_id, customer_code)}
    return {"rate": Decimal(gst_rate), "gst": tax, "cgst": Decimal("0"), "sgst": Decimal("0"), "igst": tax, "treatment": "igst", "place_code": customer_code, "place_name": _jurisdiction_name(db, tenant_id, customer_code)}
