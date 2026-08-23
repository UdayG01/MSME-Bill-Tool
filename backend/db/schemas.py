from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class SignupIn(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class CompanyUpdate(BaseModel):
    company_name: Optional[str] = None
    address: Optional[str] = None
    gstin: Optional[str] = None
    cin: Optional[str] = None
    state_code: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    logo_text: Optional[str] = None
    invoice_prefix: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_ifsc: Optional[str] = None


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    company_name: str
    address: str
    gstin: str
    cin: str
    state_code: str
    email: str
    phone: str
    logo_text: str
    invoice_prefix: str
    bank_name: str
    bank_account: str
    bank_ifsc: str


class LutUpdate(BaseModel):
    lut_no: Optional[str] = None
    lut_date: Optional[date] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None


class LutOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    lut_no: str
    lut_date: Optional[date]
    valid_from: Optional[date]
    valid_to: Optional[date]


class CustomerIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    address: str = ""
    gstin: str = ""
    country: str = "India"
    is_foreign: bool = False
    area: str = ""
    credit_days: int = Field(default=30, ge=0, le=3650)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Customer name is required")
        return value


class CustomerOut(CustomerIn):
    model_config = ConfigDict(from_attributes=True)
    id: str
    is_archived: bool
    archived_at: Optional[datetime]


class InvoiceItemIn(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    category: str = ""
    qty: Decimal = Field(default=Decimal("1"), gt=0)
    rate: Decimal = Field(default=Decimal("0"), ge=0)

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Line item description is required")
        return value


class InvoiceItemOut(InvoiceItemIn):
    model_config = ConfigDict(from_attributes=True)
    id: str
    amount: Decimal


class InvoiceCreate(BaseModel):
    customer_id: str
    invoice_date: date
    order_no: str = ""
    order_date: Optional[date] = None
    gst_rate: Decimal = Field(default=Decimal("18"), ge=0, le=100)
    items: list[InvoiceItemIn] = Field(min_length=1)


class InvoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    invoice_no: Optional[str]
    fy_label: Optional[str]
    seq_no: Optional[int]
    status: str
    invoice_date: date
    order_no: str
    order_date: Optional[date]
    customer_id: str
    gst_rate: Decimal
    subtotal: Decimal
    gst_amount: Decimal
    total: Decimal
    is_export: bool
    lut_no_snapshot: str
    lut_date_snapshot: Optional[date]
    credit_days: int
    customer_name_snapshot: str
    customer_address_snapshot: str
    customer_gstin_snapshot: str
    customer_country_snapshot: str
    customer_area_snapshot: str
    issued_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    cancellation_reason: str
    items: list[InvoiceItemOut]


class ReasonIn(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class ReceiptIn(BaseModel):
    invoice_id: str
    amount: Decimal = Field(gt=0)
    date: date
    mode: str = ""
    reference: str = ""


class ReceiptUpdate(BaseModel):
    amount: Decimal = Field(gt=0)
    date: date
    mode: str = ""
    reference: str = ""


class ReceiptOut(ReceiptIn):
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: str
    voided_at: Optional[datetime]
    void_reason: str


class CreditNoteItemIn(InvoiceItemIn):
    pass


class CreditNoteItemOut(CreditNoteItemIn):
    model_config = ConfigDict(from_attributes=True)
    id: str
    amount: Decimal


class CreditNoteCreate(BaseModel):
    date: date
    reason: str = Field(min_length=3, max_length=500)
    items: list[CreditNoteItemIn] = Field(min_length=1)


class CreditNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    invoice_id: str
    credit_note_no: str
    fy_label: str
    seq_no: int
    date: date
    reason: str
    gst_rate: Decimal
    subtotal: Decimal
    gst_amount: Decimal
    total: Decimal
    status: str
    cancelled_at: Optional[datetime]
    cancellation_reason: str
    items: list[CreditNoteItemOut]


class ReceivableRow(BaseModel):
    invoice_id: str
    invoice_no: str
    customer_name: str
    invoice_date: date
    due_date: date
    invoice_total: Decimal
    credited: Decimal
    paid: Decimal
    balance: Decimal
    days_overdue: int
    bucket: str


class SalesBreakdownRow(BaseModel):
    key: str
    total: Decimal
