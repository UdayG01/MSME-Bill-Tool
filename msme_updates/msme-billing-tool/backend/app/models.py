"""
Core data models.

Design notes (kept from earlier build + this round's decisions):
- InvoiceCounter enforces one unique invoice number per (tenant_id, fy_label)
  via a DB-level unique constraint, with retry-on-conflict logic in
  invoice_numbering.py. This prevents duplicate invoice numbers even
  under concurrent requests.
- Money is always stored in two places for export invoices: the foreign
  currency amount (what's printed on the invoice) and a frozen INR
  equivalent (what every internal report — ageing, MIS, receivables —
  actually uses). The INR equivalent is computed once at creation time
  and never recalculated, so historical reports stay stable even if
  exchange rates are corrected later.
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey,
    UniqueConstraint, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class Company(Base):
    """Single-tenant company master. Only one row is expected per deployment
    today, but tenant_id is threaded through for future multi-tenant use."""
    __tablename__ = "company"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, default="default", index=True)

    name = Column(String, nullable=False)
    address = Column(Text, nullable=False)
    gstin = Column(String, nullable=False)
    cin = Column(String, nullable=True)
    udyam_number = Column(String, nullable=True)

    email = Column(String, nullable=True)
    mobile = Column(String, nullable=True)

    logo_path = Column(String, nullable=True)
    signature_path = Column(String, nullable=True)
    tagline = Column(String, nullable=True)
    terms_notes = Column(Text, nullable=True)  # newline-separated bullets

    # Domestic bank details
    bank_name = Column(String, nullable=True)
    bank_account = Column(String, nullable=True)
    bank_ifsc = Column(String, nullable=True)
    upi_id = Column(String, nullable=True)

    # International bank details (for export invoices)
    intl_bank_name = Column(String, nullable=True)
    intl_bank_account = Column(String, nullable=True)
    intl_swift_code = Column(String, nullable=True)
    intl_bank_address = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class LUT(Base):
    """Letter of Undertaking master — required for zero-rated export invoices."""
    __tablename__ = "lut_master"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, default="default", index=True)

    lut_arn = Column(String, nullable=False)
    financial_year = Column(String, nullable=False)  # e.g. "2026-27"
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, server_default=func.now())


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, default="default", index=True)

    name = Column(String, nullable=False)
    address = Column(Text, nullable=False)
    country = Column(String, default="India")
    is_foreign = Column(Boolean, default=False)  # drives export invoice template

    gstin = Column(String, nullable=True)  # suppressed/blank for foreign customers
    state_code = Column(String, nullable=True)  # first 2 digits of GSTIN, cached

    # Mandatory — every customer must have payment terms before invoices can be raised
    payment_terms_days = Column(Integer, nullable=False, default=30)

    created_at = Column(DateTime, server_default=func.now())

    invoices = relationship("Invoice", back_populates="customer")


class InvoiceCounter(Base):
    """Tracks the next sequence number per (tenant, financial year).
    Unique constraint prevents two invoices from ever getting the same number,
    even under concurrent requests — invoice_numbering.py retries on conflict."""
    __tablename__ = "invoice_counters"
    __table_args__ = (UniqueConstraint("tenant_id", "fy_label", name="uq_tenant_fy"),)

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, default="default", index=True)
    fy_label = Column(String, nullable=False)  # e.g. "2026-27"
    last_seq_no = Column(Integer, nullable=False, default=0)


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("tenant_id", "fy_label", "seq_no", name="uq_invoice_seq"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, default="default", index=True)

    invoice_no = Column(String, nullable=False, index=True)  # e.g. INV/2026-27/0001
    fy_label = Column(String, nullable=False)
    seq_no = Column(Integer, nullable=False)

    invoice_date = Column(Date, nullable=False)
    order_no = Column(String, nullable=True)
    order_date = Column(Date, nullable=True)

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    customer = relationship("Customer", back_populates="invoices")

    is_export = Column(Boolean, default=False)
    place_of_supply_state = Column(String, nullable=True)   # e.g. "Uttar Pradesh"
    place_of_supply_code = Column(String, nullable=True)     # e.g. "09"
    tax_type = Column(String, nullable=False, default="CGST_SGST")  # CGST_SGST | IGST | IGST_ZERO
    reverse_charge = Column(Boolean, default=False)

    gst_rate = Column(Float, default=18.0)

    # Domestic currency figures (always populated, even for export — as the
    # frozen INR equivalent used by every internal report)
    subtotal_inr = Column(Float, nullable=False, default=0.0)
    cgst_amount = Column(Float, default=0.0)
    sgst_amount = Column(Float, default=0.0)
    igst_amount = Column(Float, default=0.0)
    total_inr = Column(Float, nullable=False, default=0.0)

    # Export-only currency figures
    currency_code = Column(String, default="INR")
    exchange_rate = Column(Float, nullable=True)  # manually entered, frozen at creation
    subtotal_foreign = Column(Float, nullable=True)
    total_foreign = Column(Float, nullable=True)

    # LUT reference (export invoices only)
    lut_arn = Column(String, nullable=True)
    lut_validity = Column(String, nullable=True)

    payment_terms_days = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=False)

    status = Column(String, default="Issued")  # Draft | Issued | Cancelled

    created_at = Column(DateTime, server_default=func.now())

    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    receipts = relationship("Receipt", back_populates="invoice")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    invoice = relationship("Invoice", back_populates="items")

    description = Column(String, nullable=False)
    note = Column(String, nullable=True)  # secondary detail line
    hsn_sac = Column(String, nullable=False)
    qty = Column(Float, nullable=False, default=1.0)
    rate = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)  # qty * rate, in the invoice's own currency


class Receipt(Base):
    """Payment receipt against an invoice. For export invoices, captures both
    the foreign amount received and the realized INR value, so forex gain/loss
    can be derived without disturbing the invoice's original frozen INR value."""
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, default="default", index=True)

    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    invoice = relationship("Invoice", back_populates="receipts")

    receipt_date = Column(Date, nullable=False)

    # Domestic receipts populate these directly
    amount_inr = Column(Float, nullable=False)

    # Export receipts additionally populate these
    foreign_amount_received = Column(Float, nullable=True)
    exchange_rate_at_receipt = Column(Float, nullable=True)
    forex_gain_loss = Column(Float, nullable=True)  # positive = gain, negative = loss

    firc_number = Column(String, nullable=True)  # Foreign Inward Remittance Certificate ref

    notes = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
