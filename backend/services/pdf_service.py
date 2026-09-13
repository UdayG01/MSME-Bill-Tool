from decimal import Decimal
from datetime import date
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlencode
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
import qrcode
from PIL import UnidentifiedImageError

from db import models
from core.config import get_settings
from services.media_service import prepare_image

PAGE_MARGIN = 15 * mm
CONTENT_WIDTH = A4[0] - (2 * PAGE_MARGIN)
CURRENCY_UNITS = {
    "INR": ("Rupees", "Paise"),
    "USD": ("US Dollars", "Cents"),
    "EUR": ("Euros", "Cents"),
    "GBP": ("Pounds Sterling", "Pence"),
    "AED": ("UAE Dirhams", "Fils"),
    "SGD": ("Singapore Dollars", "Cents"),
}


def _amount_words(value, currency="INR") -> str:
    """Compact English formatter for invoice amounts; supports all allowed currencies."""
    major, minor = CURRENCY_UNITS.get(currency, (currency, "Cents"))
    n = Decimal(value).quantize(Decimal(".01")); whole, fraction = int(n), int((n % 1) * 100)
    ones = ("Zero One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve Thirteen Fourteen Fifteen Sixteen Seventeen Eighteen Nineteen".split())
    tens = "Zero Ten Twenty Thirty Forty Fifty Sixty Seventy Eighty Ninety".split()
    def words(number):
        if number < 20: return ones[number]
        if number < 100: return tens[number // 10] + (" " + ones[number % 10] if number % 10 else "")
        if number < 1000: return words(number // 100) + " Hundred" + (" " + words(number % 100) if number % 100 else "")
        for scale, label in ((1_000_000_000, "Billion"), (1_000_000, "Million"), (1000, "Thousand")):
            if number >= scale: return words(number // scale) + " " + label + (" " + words(number % scale) if number % scale else "")
        return "Zero"
    return f"{major} {words(whole)} and {minor} {words(fraction)} Only"


def _asset_image(invoice, asset_id, width, height):
    if not asset_id:
        return None
    owner = invoice if hasattr(invoice, "_sa_instance_state") else invoice.tenant
    session = owner._sa_instance_state.session
    asset = session.query(models.MediaAsset).filter_by(id=asset_id, tenant_id=invoice.tenant_id).first() if session else None
    path = Path(get_settings().media_storage_path) / asset.storage_key if asset else None
    if not path or not path.is_file():
        return None
    try:
        content, _, _ = prepare_image(path.read_bytes(), asset.mime_type)
        source = BytesIO(content)
        return Image(source, width=width, height=height, kind="proportional")
    except (UnidentifiedImageError, OSError):
        return None


def _upi_qr(invoice):
    upi = invoice.company_upi_snapshot
    if invoice.is_export or not upi or not invoice.invoice_no: return None
    payload = "upi://pay?" + urlencode({"pa": upi, "pn": invoice.company_name_snapshot or invoice.tenant.company_name, "am": f"{Decimal(invoice.total):.2f}", "cu": "INR", "tn": invoice.invoice_no})
    image = qrcode.make(payload); data = BytesIO(); image.save(data, format="PNG"); data.seek(0)
    return Image(data, width=28 * mm, height=28 * mm)


def _fmt(value, currency="INR") -> str:
    return f"{currency} {Decimal(value):,.2f}"


def _document(title: str):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=PAGE_MARGIN,
        leftMargin=PAGE_MARGIN,
        topMargin=PAGE_MARGIN,
        bottomMargin=PAGE_MARGIN,
        title=title,
    )
    return buffer, doc


def _metadata_table(rows):
    table = Table(rows, colWidths=[30 * mm, 60 * mm, 28 * mm, CONTENT_WIDTH - 118 * mm])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f2f2f2")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f2f2f2")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def _items_table(items, currency="INR", styles=None):
    rows = [["#", "Item / description", "HSN/SAC", "Qty", "Rate", "Amount"]]
    for index, item in enumerate(items, start=1):
        name = escape(getattr(item, "item_name", "") or item.description)
        detail = escape(getattr(item, "item_description", "") or "")
        rows.append([
            str(index), Paragraph(f"<b>{name}</b>{'<br/><font size=7 color=\"#666666\">' + detail + '</font>' if detail else ''}", styles["Normal"]) if styles else name, getattr(item, "hsn_sac", "") or "-", f"{Decimal(item.qty):,.2f}",
            _fmt(item.rate, currency), _fmt(item.amount, currency),
        ])
    table = Table(rows, colWidths=[10 * mm, 82 * mm, 20 * mm, 14 * mm, 24 * mm, 30 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1C2B39")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def _totals_table(subtotal, gst_rate, gst_amount, total, total_label="Total", currency="INR", treatment="", cgst=0, sgst=0, igst=0):
    # Use the shared printable width; the blank first column keeps the monetary
    # summary visually right-aligned while preserving the section edge.
    rows = [["", "Subtotal", _fmt(subtotal, currency)]]
    if treatment == "cgst_sgst":
        rows.extend([["", f"CGST @ {Decimal(gst_rate) / 2:g}%", _fmt(cgst, currency)], ["", f"SGST @ {Decimal(gst_rate) / 2:g}%", _fmt(sgst, currency)]])
    elif treatment == "igst": rows.append(["", f"IGST @ {Decimal(gst_rate):g}%", _fmt(igst, currency)])
    elif treatment == "export_lut": rows.append(["", "IGST @ 0.00% (Export under LUT)", _fmt(0, currency)])
    else: rows.append(["", f"GST @ {Decimal(gst_rate):g}%", _fmt(gst_amount, currency)])
    rows.append(["", total_label, _fmt(total, currency)])
    table = Table(rows, colWidths=[CONTENT_WIDTH - 90 * mm, 50 * mm, 40 * mm])
    table.setStyle(TableStyle([
        ("GRID", (1, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("FONTNAME", (1, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (1, -1), (-1, -1), colors.HexColor("#f2f2f2")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def _footer(canvas, doc, invoice: models.Invoice) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#cccccc"))
    canvas.line(PAGE_MARGIN, 11 * mm, A4[0] - PAGE_MARGIN, 11 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#555555"))
    company = invoice.company_name_snapshot or invoice.tenant.company_name
    number = invoice.invoice_no or "Draft invoice"
    canvas.drawString(PAGE_MARGIN, 7 * mm, f"{company} | {number}")
    canvas.drawRightString(A4[0] - PAGE_MARGIN, 7 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build_invoice_pdf(invoice: models.Invoice) -> bytes:
    buffer, doc = _document(invoice.invoice_no or "Draft invoice")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SmallMuted", parent=styles["Normal"], fontSize=8, leading=10, textColor=colors.HexColor("#555555")))
    styles.add(ParagraphStyle(name="CompanyName", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=16, leading=19, textColor=colors.HexColor("#1C2B39"), spaceAfter=4))
    styles.add(ParagraphStyle(name="CompanyAddress", parent=styles["Normal"], fontSize=9.5, leading=12.5, textColor=colors.HexColor("#273746"), spaceAfter=3))
    styles.add(ParagraphStyle(name="CompanyMeta", parent=styles["Normal"], fontSize=8, leading=10.5, textColor=colors.HexColor("#555555")))
    styles.add(ParagraphStyle(name="InvoiceTitle", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=16, leading=19, textColor=colors.HexColor("#1C2B39"), spaceBefore=0, spaceAfter=8))
    status = invoice.status.upper()
    title = "TAX INVOICE" if not invoice.is_export else "EXPORT INVOICE UNDER LUT"
    if getattr(invoice, "is_preview", False):
        title = f"{title} - PREVIEW"
    elif invoice.status != "issued":
        title = f"{title} - {status}"
    company_address = escape(invoice.company_address_snapshot or invoice.tenant.address or "").replace("\n", "<br/>")
    company_details = [
        Paragraph(escape(invoice.company_name_snapshot or invoice.tenant.company_name), styles["CompanyName"]),
        Spacer(1, 1.8 * mm),
        Paragraph(company_address, styles["CompanyAddress"]),
        Spacer(1, 1.2 * mm),
        Paragraph(
            f"GSTIN: {escape(invoice.company_gstin_snapshot or invoice.tenant.gstin or '-')} &nbsp;&nbsp; "
            f"CIN: {escape(invoice.company_cin_snapshot or invoice.tenant.cin or '-')} &nbsp;&nbsp; Udyam: {escape(invoice.company_udyam_snapshot or '-')}<br/>"
            f"Email: {escape(invoice.company_email_snapshot or '-')} &nbsp;&nbsp; Mobile: {escape(invoice.company_phone_snapshot or '-')}",
            styles["CompanyMeta"],
        ),
    ]
    # Older invoices may have been issued before branding was configured. In
    # that case, use the current company logo; an existing snapshot still wins.
    logo_id = invoice.logo_asset_id_snapshot or invoice.tenant.logo_asset_id
    logo = _asset_image(invoice, logo_id, 26 * mm, 16 * mm)
    header = Table(
        [[logo, company_details]] if logo else [[company_details]],
        colWidths=[32 * mm, CONTENT_WIDTH - 32 * mm] if logo else [CONTENT_WIDTH],
    )
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
        ("LINEBELOW", (0, 0), (-1, -1), 1.2, colors.HexColor("#1C2B39")),
    ]))
    place_of_supply = "-"
    if invoice.place_of_supply_name and invoice.place_of_supply_code:
        place_of_supply = f"{invoice.place_of_supply_name} (State Code: {invoice.place_of_supply_code})"
    story = [
        header,
        Spacer(1, 6 * mm),
        Paragraph(title, styles["InvoiceTitle"]),
        _metadata_table([
            ["Invoice number", invoice.invoice_no or "DRAFT", "Invoice date", str(invoice.invoice_date)],
            ["Order number", invoice.order_no or "-", "Order date", str(invoice.order_date or "-")],
            *([["LUT ARN", invoice.lut_no_snapshot or "-", "LUT Financial Year", invoice.lut_financial_year_snapshot or "-"]] if invoice.is_export else []),
            ["Customer", invoice.customer_name_snapshot or invoice.customer.name, "Country", invoice.customer_country_snapshot or invoice.customer.country],
            ["Bill to", invoice.customer_address_snapshot or invoice.customer.address or "-", "GSTIN", invoice.customer_gstin_snapshot or invoice.customer.gstin or "-"],
            ["Place of supply", place_of_supply, "Reverse charge", "Yes" if invoice.reverse_charge else "No"],
        ]),
        Spacer(1, 6 * mm),
        _items_table(invoice.items, invoice.document_currency if invoice.is_export else "INR", styles),
    ]
    terms = [line.strip() for line in (invoice.terms_notes_snapshot or "Payment is due as per agreed terms.\nInterest may apply under the MSMED Act.\nReport discrepancies within seven days.").splitlines() if line.strip()]
    if invoice.is_export: terms.insert(0, "Supply meant for export under Letter of Undertaking (LUT) without payment of Integrated Tax")
    domestic_upi = f"<br/>UPI: {escape(invoice.company_upi_snapshot)}" if invoice.company_upi_snapshot else ""
    bank = (f"International Bank: {escape(invoice.intl_bank_name_snapshot or '-')}<br/>Account: {escape(invoice.intl_bank_account_snapshot or '-')} &nbsp;&nbsp; SWIFT: {escape(invoice.intl_swift_code_snapshot or '-')}<br/>Address: {escape(invoice.intl_bank_address_snapshot or '-')}<br/>All bank charges outside India to be borne by the remitter." if invoice.is_export else f"Bank: {escape(invoice.bank_name_snapshot or '-')} &nbsp;&nbsp; Account: {escape(invoice.bank_account_snapshot or '-')} &nbsp;&nbsp; IFSC: {escape(invoice.bank_ifsc_snapshot or '-')}" + domestic_upi )
    def boxed(title, body):
        table = Table([[Paragraph(f"<b>{title}</b><br/>{body}", styles["SmallMuted"])]], colWidths=[CONTENT_WIDTH]); table.setStyle(TableStyle([("BOX", (0,0), (-1,-1), .4, colors.HexColor("#cccccc")), ("PADDING", (0,0), (-1,-1), 5)])); return table
    closing = [Spacer(1, 6 * mm), Paragraph(f"Amount in Words: {_amount_words(invoice.document_total if invoice.is_export else invoice.total, invoice.document_currency if invoice.is_export else 'INR')}", styles["SmallMuted"]), boxed("Bank Details", bank), boxed("Terms & Notes", "<br/>".join("• " + escape(line) for line in terms))]
    closing.insert(0, _totals_table(
        invoice.document_subtotal if invoice.is_export else invoice.subtotal,
        invoice.gst_rate, invoice.gst_amount,
        invoice.document_total if invoice.is_export else invoice.total,
        currency=invoice.document_currency if invoice.is_export else "INR",
        treatment=invoice.tax_treatment, cgst=invoice.cgst_amount,
        sgst=invoice.sgst_amount, igst=invoice.igst_amount,
    ))
    closing.insert(0, Spacer(1, 5 * mm))
    qr = _upi_qr(invoice)
    if qr: closing.append(Table([[qr, Paragraph("Scan to pay via UPI", styles["SmallMuted"])]], colWidths=[32 * mm, CONTENT_WIDTH - 32 * mm]))
    signature_id = invoice.signature_asset_id_snapshot or invoice.tenant.signature_asset_id
    signature = _asset_image(invoice, signature_id, 35 * mm, 15 * mm) or Spacer(35 * mm, 15 * mm)
    closing.append(Table([[signature], [Paragraph("Authorized Signatory", styles["SmallMuted"])]], colWidths=[CONTENT_WIDTH], hAlign="RIGHT"))
    if invoice.tagline_snapshot: closing.append(Paragraph(escape(invoice.tagline_snapshot), ParagraphStyle("Tagline", parent=styles["Normal"], alignment=1, textColor=colors.white, backColor=colors.HexColor("#1C2B39"), spaceBefore=4, spaceAfter=2)))
    story.append(KeepTogether(closing))
    if invoice.status == "cancelled":
        story.extend([Spacer(1, 6 * mm), Paragraph(
            f"CANCELLED - {escape(invoice.cancellation_reason)}",
            ParagraphStyle(name="Cancelled", parent=styles["Heading2"], textColor=colors.red),
        )])
    footer = lambda canvas, page_doc: _footer(canvas, page_doc, invoice)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()


def build_company_preview_pdf(tenant: models.Tenant, billing_settings, values: dict) -> bytes:
    """Render a sample invoice with submitted company details without saving them."""
    company = {
        field: values.get(field, getattr(tenant, field, None))
        for field in (
            "company_name", "address", "gstin", "cin", "email", "phone",
            "bank_name", "bank_account", "bank_ifsc", "udyam_number", "upi_id",
            "intl_bank_name", "intl_bank_account", "intl_swift_code",
            "intl_bank_address", "logo_asset_id", "signature_asset_id", "state_code",
        )
    }
    state_code = (company["gstin"] or "")[:2] or company["state_code"] or "29"
    sample_customer = SimpleNamespace(
        name="Sample Customer",
        address="Sample billing address",
        gstin=f"{state_code}AAAAA0000A1Z5",
        country="India",
    )
    sample_item = SimpleNamespace(
        item_name="Sample product or service",
        item_description="Description shown below the item name",
        description="Sample product or service",
        hsn_sac="9983",
        qty=Decimal("1"),
        rate=Decimal("1000"),
        amount=Decimal("1000"),
    )
    preview = SimpleNamespace(
        tenant=tenant,
        tenant_id=tenant.id,
        is_preview=True,
        is_export=False,
        status="issued",
        invoice_no="SAMPLE/0001",
        invoice_date=date.today(),
        order_no="PO-0001",
        order_date=date.today(),
        reverse_charge=False,
        place_of_supply_code=state_code,
        place_of_supply_name="Sample State",
        customer=sample_customer,
        customer_name_snapshot=sample_customer.name,
        customer_address_snapshot=sample_customer.address,
        customer_gstin_snapshot=sample_customer.gstin,
        customer_country_snapshot=sample_customer.country,
        items=[sample_item],
        document_currency="INR",
        subtotal=Decimal("1000"),
        gst_rate=Decimal("18"),
        gst_amount=Decimal("180"),
        total=Decimal("1180"),
        tax_treatment="cgst_sgst",
        cgst_amount=Decimal("90"),
        sgst_amount=Decimal("90"),
        igst_amount=Decimal("0"),
        document_subtotal=Decimal("1000"),
        document_total=Decimal("1180"),
        lut_no_snapshot="",
        lut_financial_year_snapshot="",
        terms_notes_snapshot=billing_settings.terms_notes or "",
        tagline_snapshot=billing_settings.tagline or "",
        logo_asset_id_snapshot=company["logo_asset_id"] or None,
        signature_asset_id_snapshot=company["signature_asset_id"] or None,
        company_name_snapshot=company["company_name"] or "Company Name",
        company_address_snapshot=company["address"] or "Company address",
        company_gstin_snapshot=company["gstin"] or "",
        company_cin_snapshot=company["cin"] or "",
        company_udyam_snapshot=company["udyam_number"] or "",
        company_email_snapshot=company["email"] or "",
        company_phone_snapshot=company["phone"] or "",
        company_upi_snapshot=company["upi_id"] or "",
        bank_name_snapshot=company["bank_name"] or "",
        bank_account_snapshot=company["bank_account"] or "",
        bank_ifsc_snapshot=company["bank_ifsc"] or "",
        intl_bank_name_snapshot=company["intl_bank_name"] or "",
        intl_bank_account_snapshot=company["intl_bank_account"] or "",
        intl_swift_code_snapshot=company["intl_swift_code"] or "",
        intl_bank_address_snapshot=company["intl_bank_address"] or "",
    )
    return build_invoice_pdf(preview)


def build_credit_note_pdf(note: models.CreditNote) -> bytes:
    invoice = note.invoice
    buffer, doc = _document(note.credit_note_no)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(escape(invoice.company_name_snapshot or invoice.tenant.company_name), styles["Title"]),
        Paragraph(escape(invoice.company_address_snapshot or invoice.tenant.address or ""), styles["Normal"]),
        Spacer(1, 7 * mm),
        Paragraph("CREDIT NOTE", styles["Heading1"]),
        _metadata_table([
            ["Credit note", note.credit_note_no, "Date", str(note.date)],
            ["Against invoice", invoice.invoice_no or "-", "Invoice date", str(invoice.invoice_date)],
            ["Customer", invoice.customer_name_snapshot or invoice.customer.name, "GSTIN", invoice.customer_gstin_snapshot or "-"],
            ["Reason", note.reason, "Status", note.status.upper()],
        ]),
        Spacer(1, 6 * mm),
        _items_table(note.items),
        Spacer(1, 5 * mm),
        _totals_table(note.subtotal, note.gst_rate, note.gst_amount, note.total, "Total credit"),
    ]
    if note.status == "cancelled":
        story.extend([Spacer(1, 6 * mm), Paragraph(
            f"CANCELLED - {escape(note.cancellation_reason)}",
            ParagraphStyle(name="CancelledCredit", parent=styles["Heading2"], textColor=colors.red),
        )])
    doc.build(story)
    return buffer.getvalue()
