from datetime import date, datetime
from decimal import Decimal
from typing import Optional

import re
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


def _validate_state_code(value: str | None) -> str | None:
    if value is None:
        return value
    value = value.strip()
    if value and (len(value) != 2 or not value.isdigit()):
        raise ValueError("GST state code must be a two-digit code, for example 06 for Haryana")
    return value


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
    udyam_number: Optional[str] = None
    upi_id: Optional[str] = None
    intl_bank_name: Optional[str] = None
    intl_bank_account: Optional[str] = None
    intl_swift_code: Optional[str] = None
    intl_bank_address: Optional[str] = None
    logo_asset_id: Optional[str] = None
    signature_asset_id: Optional[str] = None

    @field_validator("state_code")
    @classmethod
    def validate_state_code(cls, value: str | None) -> str | None:
        return _validate_state_code(value)


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
    udyam_number: str
    upi_id: str
    intl_bank_name: str
    intl_bank_account: str
    intl_swift_code: str
    intl_bank_address: str
    logo_asset_id: Optional[str]
    signature_asset_id: Optional[str]


class CustomerIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    address: str = ""
    gstin: str = ""
    country: str = "India"
    is_foreign: bool = False
    area: str = ""
    state_code: str = ""
    credit_days: int = Field(ge=0, le=3650)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Customer name is required")
        return value

    @field_validator("state_code")
    @classmethod
    def validate_state_code(cls, value: str) -> str:
        return _validate_state_code(value) or ""

    @model_validator(mode="after")
    def validate_customer_type(self):
        self.gstin = self.gstin.strip().upper()
        self.country = self.country.strip()
        if self.is_foreign:
            if not self.country or self.country.lower() == "india":
                raise ValueError("Foreign customers require a non-India country")
            self.gstin, self.state_code = "", ""
        else:
            if not re.fullmatch(r"[0-9]{2}[A-Z0-9]{13}", self.gstin):
                raise ValueError("Domestic customers require a valid 15-character GSTIN")
            self.country, self.state_code = "India", self.gstin[:2]
        return self


class CustomerOut(CustomerIn):
    model_config = ConfigDict(from_attributes=True)
    id: str
    is_archived: bool
    archived_at: Optional[datetime]


class ProductIn(BaseModel):
    name: str = Field(min_length=1, max_length=500)
    description: str = Field(default="", max_length=2000)
    hsn_sac: str = Field(default="", max_length=50)
    amount: Decimal = Field(default=Decimal("0"), ge=0)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Product name is required")
        return value


class ProductOut(ProductIn):
    model_config = ConfigDict(from_attributes=True)
    id: str
    is_archived: bool
    archived_at: Optional[datetime]


class InvoiceItemIn(BaseModel):
    description: str = Field(default="", max_length=2000)
    item_name: str = Field(default="", max_length=500)
    item_description: str = Field(default="", max_length=2000)
    category: str = ""
    hsn_sac: str = ""
    qty: Decimal = Field(default=Decimal("1"), gt=0)
    rate: Decimal = Field(default=Decimal("0"), ge=0)

    @model_validator(mode="after")
    def normalize_line_item(self):
        self.item_name = self.item_name.strip() or self.description.strip()
        if not self.item_name:
            raise ValueError("Line item name is required")
        self.item_description = self.item_description.strip()
        self.description = self.item_description or self.item_name
        return self


class InvoiceItemOut(InvoiceItemIn):
    model_config = ConfigDict(from_attributes=True)
    id: str
    amount: Decimal


class InvoiceCreate(BaseModel):
    customer_id: str
    invoice_date: date
    order_no: str = Field(default="", max_length=100)
    order_date: Optional[date] = None
    gst_rate: Decimal = Field(default=Decimal("18"), ge=0, le=100)
    items: list[InvoiceItemIn] = Field(min_length=1)
    document_currency: str = Field(default="INR", min_length=3, max_length=3)
    exchange_rate_to_inr: Optional[Decimal] = Field(default=None, gt=0)
    reverse_charge: bool = False


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
    tax_treatment: str
    place_of_supply_code: str
    place_of_supply_name: str
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    due_date: Optional[date]
    document_currency: str
    exchange_rate_to_inr: Optional[Decimal]
    document_subtotal: Optional[Decimal]
    document_total: Optional[Decimal]
    is_export: bool
    reverse_charge: bool
    lut_no_snapshot: str
    lut_date_snapshot: Optional[date]
    lut_financial_year_snapshot: str
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
    # Required for domestic receipts. Export receipts derive realised INR from
    # foreign_amount and exchange_rate_to_inr in the service layer.
    amount: Optional[Decimal] = Field(default=None, gt=0)
    date: date
    mode: str = ""
    reference: str = ""
    receipt_currency: str = Field(default="INR", min_length=3, max_length=3)
    foreign_amount: Optional[Decimal] = Field(default=None, gt=0)
    exchange_rate_to_inr: Optional[Decimal] = Field(default=None, gt=0)
    firc_number: str = ""


class ReceiptUpdate(BaseModel):
    amount: Optional[Decimal] = Field(default=None, gt=0)
    date: date
    mode: str = ""
    reference: str = ""
    receipt_currency: str = Field(default="INR", min_length=3, max_length=3)
    foreign_amount: Optional[Decimal] = Field(default=None, gt=0)
    exchange_rate_to_inr: Optional[Decimal] = Field(default=None, gt=0)
    firc_number: str = ""


class ReceiptOut(ReceiptIn):
    model_config = ConfigDict(from_attributes=True)
    id: str
    amount: Decimal
    status: str
    voided_at: Optional[datetime]
    void_reason: str
    applied_amount_inr: Optional[Decimal]
    forex_gain_loss_inr: Optional[Decimal]


class BillingSettingsUpdate(BaseModel):
    base_currency: str = Field(default="INR", min_length=3, max_length=3)
    allow_export_invoicing: bool = False
    require_valid_lut_for_export: bool = True
    terms_notes: str = ""
    tagline: str = ""

    @field_validator("base_currency")
    @classmethod
    def base_currency_must_be_inr(cls, value: str) -> str:
        if value.upper() != "INR":
            raise ValueError("The domestic base currency must be INR")
        return "INR"


class InvoiceNumberSetupIn(BaseModel):
    next_invoice_number: int = Field(ge=1, le=9_999_999)


class InvoiceNumberSetupOut(BaseModel):
    financial_year: str
    next_invoice_number: int
    locked: bool
    manual_setup_available: bool
    invoice_prefix: str


class ExchangeRateReferenceOut(BaseModel):
    base_currency: str
    quote_currency: str
    rate: Decimal
    rate_date: date
    source: str


class MediaAssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    purpose: str
    mime_type: str
    file_size: int
    width: int
    height: int


class BillingSettingsOut(BillingSettingsUpdate):
    model_config = ConfigDict(from_attributes=True)


class TaxJurisdictionIn(BaseModel):
    country_code: str = Field(default="IN", min_length=2, max_length=2)
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=255)
    is_active: bool = True


class TaxJurisdictionOut(TaxJurisdictionIn):
    model_config = ConfigDict(from_attributes=True)
    id: str


class LutCertificateIn(BaseModel):
    arn: str = Field(min_length=1, max_length=100)
    financial_year: str = Field(min_length=4, max_length=9)
    valid_from: date
    valid_to: date


class LutCertificateOut(LutCertificateIn):
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: str


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
