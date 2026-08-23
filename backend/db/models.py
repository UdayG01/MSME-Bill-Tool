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

    id = Column(String, primary_key=True, default=gen_id)
    company_name = Column(String, nullable=False, default="")
    address = Column(String, default="")
    gstin = Column(String, default="")
    cin = Column(String, default="")
    state_code = Column(String, default="")
    email = Column(String, default="")
    phone = Column(String, default="")
    logo_text = Column(String, default="")
    invoice_prefix = Column(String, default="INV")
    bank_name = Column(String, default="")
    bank_account = Column(String, default="")
    bank_ifsc = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="tenant", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="tenant", cascade="all, delete-orphan")
    lut = relationship("LutMaster", back_populates="tenant", uselist=False, cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_id)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="owner")
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="users")


class LutMaster(Base):
    __tablename__ = "lut_master"

    id = Column(String, primary_key=True, default=gen_id)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, unique=True)
    lut_no = Column(String, default="")
    lut_date = Column(Date, nullable=True)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)

    tenant = relationship("Tenant", back_populates="lut")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True, default=gen_id)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    address = Column(String, default="")
    gstin = Column(String, default="")
    country = Column(String, default="India")
    is_foreign = Column(Boolean, default=False)
    area = Column(String, default="")
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

    id = Column(String, primary_key=True, default=gen_id)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    fy_label = Column(String, nullable=False)
    last_seq = Column(Integer, default=0, nullable=False)


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (UniqueConstraint("tenant_id", "fy_label", "seq_no", name="uq_invoice_number"),)

    id = Column(String, primary_key=True, default=gen_id)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)

    invoice_no = Column(String, nullable=True)
    fy_label = Column(String, nullable=True)
    seq_no = Column(Integer, nullable=True)
    status = Column(String, nullable=False, default="draft", index=True)

    invoice_date = Column(Date, nullable=False)
    order_no = Column(String, default="")
    order_date = Column(Date, nullable=True)
    gst_rate = Column(Numeric(5, 2), default=0)
    subtotal = Column(Numeric(14, 2), default=0)
    gst_amount = Column(Numeric(14, 2), default=0)
    total = Column(Numeric(14, 2), default=0)

    is_export = Column(Boolean, default=False)
    lut_no_snapshot = Column(String, default="")
    lut_date_snapshot = Column(Date, nullable=True)
    credit_days = Column(Integer, default=30)

    company_name_snapshot = Column(String, default="")
    company_address_snapshot = Column(String, default="")
    company_gstin_snapshot = Column(String, default="")
    company_cin_snapshot = Column(String, default="")
    company_email_snapshot = Column(String, default="")
    company_phone_snapshot = Column(String, default="")
    bank_name_snapshot = Column(String, default="")
    bank_account_snapshot = Column(String, default="")
    bank_ifsc_snapshot = Column(String, default="")
    customer_name_snapshot = Column(String, default="")
    customer_address_snapshot = Column(String, default="")
    customer_gstin_snapshot = Column(String, default="")
    customer_country_snapshot = Column(String, default="")
    customer_area_snapshot = Column(String, default="")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    issued_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(String, default="")

    tenant = relationship("Tenant", back_populates="invoices")
    customer = relationship("Customer", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    receipts = relationship("Receipt", back_populates="invoice", cascade="all, delete-orphan")
    credit_notes = relationship("CreditNote", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(String, primary_key=True, default=gen_id)
    invoice_id = Column(String, ForeignKey("invoices.id"), nullable=False, index=True)
    description = Column(String, default="")
    category = Column(String, default="")
    qty = Column(Numeric(12, 2), default=1)
    rate = Column(Numeric(14, 2), default=0)
    amount = Column(Numeric(14, 2), default=0)

    invoice = relationship("Invoice", back_populates="items")


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(String, primary_key=True, default=gen_id)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    invoice_id = Column(String, ForeignKey("invoices.id"), nullable=False, index=True)
    amount = Column(Numeric(14, 2), nullable=False)
    date = Column(Date, nullable=False)
    mode = Column(String, default="")
    reference = Column(String, default="")
    status = Column(String, nullable=False, default="active", index=True)
    voided_at = Column(DateTime, nullable=True)
    void_reason = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    invoice = relationship("Invoice", back_populates="receipts")


class CreditNoteCounter(Base):
    __tablename__ = "credit_note_counters"
    __table_args__ = (UniqueConstraint("tenant_id", "fy_label", name="uq_credit_note_tenant_fy"),)

    id = Column(String, primary_key=True, default=gen_id)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    fy_label = Column(String, nullable=False)
    last_seq = Column(Integer, default=0, nullable=False)


class CreditNote(Base):
    __tablename__ = "credit_notes"
    __table_args__ = (UniqueConstraint("tenant_id", "fy_label", "seq_no", name="uq_credit_note_number"),)

    id = Column(String, primary_key=True, default=gen_id)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    invoice_id = Column(String, ForeignKey("invoices.id"), nullable=False, index=True)
    credit_note_no = Column(String, nullable=False)
    fy_label = Column(String, nullable=False)
    seq_no = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    reason = Column(String, nullable=False)
    gst_rate = Column(Numeric(5, 2), default=0)
    subtotal = Column(Numeric(14, 2), default=0)
    gst_amount = Column(Numeric(14, 2), default=0)
    total = Column(Numeric(14, 2), default=0)
    status = Column(String, nullable=False, default="active", index=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    invoice = relationship("Invoice", back_populates="credit_notes")
    items = relationship("CreditNoteItem", back_populates="credit_note", cascade="all, delete-orphan")


class CreditNoteItem(Base):
    __tablename__ = "credit_note_items"

    id = Column(String, primary_key=True, default=gen_id)
    credit_note_id = Column(String, ForeignKey("credit_notes.id"), nullable=False, index=True)
    description = Column(String, default="")
    category = Column(String, default="")
    qty = Column(Numeric(12, 2), default=1)
    rate = Column(Numeric(14, 2), default=0)
    amount = Column(Numeric(14, 2), default=0)

    credit_note = relationship("CreditNote", back_populates="items")
