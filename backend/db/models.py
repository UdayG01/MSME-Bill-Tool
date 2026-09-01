import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String(12), primary_key=True, default=gen_id)
    company_name = Column(String(255), nullable=False, default="")
    address = Column(String(2000), default="")
    gstin = Column(String(15), default="")
    cin = Column(String(21), default="")
    state_code = Column(String(2), default="")
    email = Column(String(254), default="")
    phone = Column(String(30), default="")
    logo_text = Column(String(255), default="")
    invoice_prefix = Column(String(50), default="INV")
    bank_name = Column(String(255), default="")
    bank_account = Column(String(50), default="")
    bank_ifsc = Column(String(20), default="")
    udyam_number = Column(String(100), default="")
    upi_id = Column(String(255), default="")
    intl_bank_name = Column(String(255), default="")
    intl_bank_account = Column(String(100), default="")
    intl_swift_code = Column(String(50), default="")
    intl_bank_address = Column(String(2000), default="")
    logo_asset_id = Column(String(12), nullable=True)
    signature_asset_id = Column(String(12), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="tenant", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="tenant", cascade="all, delete-orphan")
    lut = relationship("LutMaster", back_populates="tenant", uselist=False, cascade="all, delete-orphan")
    lut_certificates = relationship("LutCertificate", back_populates="tenant", cascade="all, delete-orphan")
    billing_settings = relationship("BillingSettings", back_populates="tenant", uselist=False, cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(String(12), primary_key=True, default=gen_id)
    tenant_id = Column(String(12), ForeignKey("tenants.id"), nullable=False)
    email = Column(String(254), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(30), default="owner")
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="users")


class LutMaster(Base):
    __tablename__ = "lut_master"

    id = Column(String(12), primary_key=True, default=gen_id)
    tenant_id = Column(String(12), ForeignKey("tenants.id"), nullable=False, unique=True)
    lut_no = Column(String(100), default="")
    lut_date = Column(Date, nullable=True)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)

    tenant = relationship("Tenant", back_populates="lut")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(12), primary_key=True, default=gen_id)
    tenant_id = Column(String(12), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    address = Column(String(2000), default="")
    gstin = Column(String(15), default="")
    country = Column(String(100), default="India")
    is_foreign = Column(Boolean, default=False)
    area = Column(String(255), default="")
    state_code = Column(String(20), default="")
    credit_days = Column(Integer, default=30)
    is_archived = Column(Boolean, default=False, nullable=False)
    archived_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="customers")
    invoices = relationship("Invoice", back_populates="customer")


class InvoiceCounter(Base):
    __tablename__ = "invoice_counters"
    __table_args__ = (UniqueConstraint("tenant_id", "fy_label", name="uq_tenant_fy"),)

    id = Column(String(12), primary_key=True, default=gen_id)
    tenant_id = Column(String(12), ForeignKey("tenants.id"), nullable=False)
    fy_label = Column(String(9), nullable=False)
    last_seq = Column(Integer, default=0, nullable=False)


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (UniqueConstraint("tenant_id", "fy_label", "seq_no", name="uq_invoice_number"),)

    id = Column(String(12), primary_key=True, default=gen_id)
    tenant_id = Column(String(12), ForeignKey("tenants.id"), nullable=False, index=True)
    customer_id = Column(String(12), ForeignKey("customers.id"), nullable=False)

    invoice_no = Column(String(100), nullable=True)
    fy_label = Column(String(9), nullable=True)
    seq_no = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="draft", index=True)

    invoice_date = Column(Date, nullable=False)
    order_no = Column(String(100), default="")
    order_date = Column(Date, nullable=True)
    gst_rate = Column(Numeric(5, 2), default=0)
    subtotal = Column(Numeric(14, 2), default=0)
    gst_amount = Column(Numeric(14, 2), default=0)
    total = Column(Numeric(14, 2), default=0)

    is_export = Column(Boolean, default=False)
    lut_no_snapshot = Column(String(100), default="")
    lut_date_snapshot = Column(Date, nullable=True)
    credit_days = Column(Integer, default=30)
    due_date = Column(Date, nullable=True)
    tax_treatment = Column(String(50), default="")
    place_of_supply_code = Column(String(20), default="")
    place_of_supply_name = Column(String(255), default="")
    cgst_amount = Column(Numeric(14, 2), default=0)
    sgst_amount = Column(Numeric(14, 2), default=0)
    igst_amount = Column(Numeric(14, 2), default=0)
    document_currency = Column(String(3), default="INR")
    exchange_rate_to_inr = Column(Numeric(18, 6), nullable=True)
    document_subtotal = Column(Numeric(14, 2), nullable=True)
    document_total = Column(Numeric(14, 2), nullable=True)
    lut_certificate_id = Column(String(12), nullable=True)
    lut_valid_from_snapshot = Column(Date, nullable=True)
    lut_valid_to_snapshot = Column(Date, nullable=True)

    company_name_snapshot = Column(String(255), default="")
    company_address_snapshot = Column(String(2000), default="")
    company_gstin_snapshot = Column(String(15), default="")
    company_cin_snapshot = Column(String(21), default="")
    company_email_snapshot = Column(String(254), default="")
    company_phone_snapshot = Column(String(30), default="")
    bank_name_snapshot = Column(String(255), default="")
    bank_account_snapshot = Column(String(50), default="")
    bank_ifsc_snapshot = Column(String(20), default="")
    customer_name_snapshot = Column(String(255), default="")
    customer_address_snapshot = Column(String(2000), default="")
    customer_gstin_snapshot = Column(String(15), default="")
    customer_country_snapshot = Column(String(100), default="")
    customer_area_snapshot = Column(String(255), default="")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    issued_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(String(2000), default="")

    tenant = relationship("Tenant", back_populates="invoices")
    customer = relationship("Customer", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    receipts = relationship("Receipt", back_populates="invoice", cascade="all, delete-orphan")
    credit_notes = relationship("CreditNote", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(String(12), primary_key=True, default=gen_id)
    invoice_id = Column(String(12), ForeignKey("invoices.id"), nullable=False, index=True)
    description = Column(String(2000), default="")
    category = Column(String(255), default="")
    hsn_sac = Column(String(50), default="")
    qty = Column(Numeric(12, 2), default=1)
    rate = Column(Numeric(14, 2), default=0)
    amount = Column(Numeric(14, 2), default=0)

    invoice = relationship("Invoice", back_populates="items")


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(String(12), primary_key=True, default=gen_id)
    tenant_id = Column(String(12), ForeignKey("tenants.id"), nullable=False, index=True)
    invoice_id = Column(String(12), ForeignKey("invoices.id"), nullable=False, index=True)
    amount = Column(Numeric(14, 2), nullable=False)
    date = Column(Date, nullable=False)
    mode = Column(String(50), default="")
    reference = Column(String(255), default="")
    receipt_currency = Column(String(3), default="INR")
    foreign_amount = Column(Numeric(14, 2), nullable=True)
    exchange_rate_to_inr = Column(Numeric(18, 6), nullable=True)
    firc_number = Column(String(255), default="")
    forex_gain_loss_inr = Column(Numeric(14, 2), nullable=True)
    status = Column(String(20), nullable=False, default="active", index=True)
    voided_at = Column(DateTime, nullable=True)
    void_reason = Column(String(2000), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    invoice = relationship("Invoice", back_populates="receipts")


class CreditNoteCounter(Base):
    __tablename__ = "credit_note_counters"
    __table_args__ = (UniqueConstraint("tenant_id", "fy_label", name="uq_credit_note_tenant_fy"),)

    id = Column(String(12), primary_key=True, default=gen_id)
    tenant_id = Column(String(12), ForeignKey("tenants.id"), nullable=False)
    fy_label = Column(String(9), nullable=False)
    last_seq = Column(Integer, default=0, nullable=False)


class CreditNote(Base):
    __tablename__ = "credit_notes"
    __table_args__ = (UniqueConstraint("tenant_id", "fy_label", "seq_no", name="uq_credit_note_number"),)

    id = Column(String(12), primary_key=True, default=gen_id)
    tenant_id = Column(String(12), ForeignKey("tenants.id"), nullable=False, index=True)
    invoice_id = Column(String(12), ForeignKey("invoices.id"), nullable=False, index=True)
    credit_note_no = Column(String(100), nullable=False)
    fy_label = Column(String(9), nullable=False)
    seq_no = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    reason = Column(String(2000), nullable=False)
    gst_rate = Column(Numeric(5, 2), default=0)
    subtotal = Column(Numeric(14, 2), default=0)
    gst_amount = Column(Numeric(14, 2), default=0)
    total = Column(Numeric(14, 2), default=0)
    status = Column(String(20), nullable=False, default="active", index=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(String(2000), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    invoice = relationship("Invoice", back_populates="credit_notes")
    items = relationship("CreditNoteItem", back_populates="credit_note", cascade="all, delete-orphan")


class CreditNoteItem(Base):
    __tablename__ = "credit_note_items"

    id = Column(String(12), primary_key=True, default=gen_id)
    credit_note_id = Column(String(12), ForeignKey("credit_notes.id"), nullable=False, index=True)
    description = Column(String(2000), default="")
    category = Column(String(255), default="")
    qty = Column(Numeric(12, 2), default=1)
    rate = Column(Numeric(14, 2), default=0)
    amount = Column(Numeric(14, 2), default=0)

    credit_note = relationship("CreditNote", back_populates="items")


class BillingSettings(Base):
    __tablename__ = "billing_settings"

    id = Column(String(12), primary_key=True, default=gen_id)
    tenant_id = Column(String(12), ForeignKey("tenants.id"), nullable=False, unique=True)
    base_currency = Column(String(3), nullable=False, default="INR")
    allow_export_invoicing = Column(Boolean, nullable=False, default=False)
    require_valid_lut_for_export = Column(Boolean, nullable=False, default=True)
    terms_notes = Column(String(4000), default="")
    tagline = Column(String(255), default="")
    tenant = relationship("Tenant", back_populates="billing_settings")


class TaxJurisdiction(Base):
    __tablename__ = "tax_jurisdictions"
    __table_args__ = (UniqueConstraint("tenant_id", "country_code", "code", name="uq_tax_jurisdiction"),)

    id = Column(String(12), primary_key=True, default=gen_id)
    tenant_id = Column(String(12), ForeignKey("tenants.id"), nullable=False, index=True)
    country_code = Column(String(2), nullable=False, default="IN")
    code = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)


class LutCertificate(Base):
    __tablename__ = "lut_certificates"
    __table_args__ = (UniqueConstraint("tenant_id", "arn", name="uq_lut_certificate_arn"),)

    id = Column(String(12), primary_key=True, default=gen_id)
    tenant_id = Column(String(12), ForeignKey("tenants.id"), nullable=False, index=True)
    arn = Column(String(100), nullable=False)
    financial_year = Column(String(9), nullable=False)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="inactive")
    created_at = Column(DateTime, default=datetime.utcnow)
    tenant = relationship("Tenant", back_populates="lut_certificates")


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id = Column(String(12), primary_key=True, default=gen_id)
    tenant_id = Column(String(12), ForeignKey("tenants.id"), nullable=False, index=True)
    purpose = Column(String(30), nullable=False)
    storage_key = Column(String(500), nullable=False, unique=True)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    checksum = Column(String(64), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
