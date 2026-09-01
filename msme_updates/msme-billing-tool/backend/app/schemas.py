from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ---------- Company ----------
class CompanyBase(BaseModel):
    name: str
    address: str
    gstin: str
    cin: Optional[str] = None
    udyam_number: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    tagline: Optional[str] = None
    terms_notes: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_ifsc: Optional[str] = None
    upi_id: Optional[str] = None
    intl_bank_name: Optional[str] = None
    intl_bank_account: Optional[str] = None
    intl_swift_code: Optional[str] = None
    intl_bank_address: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyOut(CompanyBase):
    id: int
    logo_path: Optional[str] = None
    signature_path: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- LUT ----------
class LUTBase(BaseModel):
    lut_arn: str
    financial_year: str
    valid_from: date
    valid_to: date
    is_active: bool = True


class LUTCreate(LUTBase):
    pass


class LUTOut(LUTBase):
    id: int

    class Config:
        from_attributes = True


# ---------- Customer ----------
class CustomerBase(BaseModel):
    name: str
    address: str
    country: str = "India"
    is_foreign: bool = False
    gstin: Optional[str] = None
    payment_terms_days: int = Field(..., gt=0, description="Mandatory — every customer must have payment terms")


class CustomerCreate(CustomerBase):
    pass


class CustomerOut(CustomerBase):
    id: int
    state_code: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- Invoice ----------
class InvoiceItemIn(BaseModel):
    description: str
    note: Optional[str] = None
    hsn_sac: str
    qty: float = 1.0
    rate: float


class InvoiceItemOut(InvoiceItemIn):
    id: int
    amount: float

    class Config:
        from_attributes = True


class InvoiceCreate(BaseModel):
    customer_id: int
    invoice_date: date
    order_no: Optional[str] = None
    order_date: Optional[date] = None
    items: List[InvoiceItemIn]
    gst_rate: float = 18.0

    # Export-specific — required only when the customer is foreign
    currency_code: Optional[str] = "INR"
    exchange_rate: Optional[float] = None  # manual entry, required for export invoices


class InvoiceOut(BaseModel):
    id: int
    invoice_no: str
    fy_label: str
    invoice_date: date
    order_no: Optional[str]
    order_date: Optional[date]
    customer_id: int
    is_export: bool
    place_of_supply_state: Optional[str]
    place_of_supply_code: Optional[str]
    tax_type: str
    reverse_charge: bool
    gst_rate: float
    subtotal_inr: float
    cgst_amount: float
    sgst_amount: float
    igst_amount: float
    total_inr: float
    currency_code: str
    exchange_rate: Optional[float]
    subtotal_foreign: Optional[float]
    total_foreign: Optional[float]
    lut_arn: Optional[str]
    lut_validity: Optional[str]
    payment_terms_days: int
    due_date: date
    status: str
    items: List[InvoiceItemOut]

    class Config:
        from_attributes = True


# ---------- Receipt ----------
class ReceiptCreate(BaseModel):
    invoice_id: int
    receipt_date: date
    amount_inr: float
    foreign_amount_received: Optional[float] = None
    exchange_rate_at_receipt: Optional[float] = None
    firc_number: Optional[str] = None
    notes: Optional[str] = None


class ReceiptOut(ReceiptCreate):
    id: int
    forex_gain_loss: Optional[float] = None

    class Config:
        from_attributes = True


# ---------- Reports ----------
class AgeingBucket(BaseModel):
    label: str
    count: int
    total_inr: float


class AgeingReportOut(BaseModel):
    as_of: date
    buckets: List[AgeingBucket]
    total_outstanding_inr: float
