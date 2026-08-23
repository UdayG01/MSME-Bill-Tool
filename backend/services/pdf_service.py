from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from db import models


def _fmt(value) -> str:
    return f"INR {Decimal(value):,.2f}"


def _document(title: str):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=title,
    )
    return buffer, doc


def _metadata_table(rows):
    table = Table(rows, colWidths=[30 * mm, 60 * mm, 28 * mm, 52 * mm])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f2f2f2")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f2f2f2")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def _items_table(items):
    rows = [["#", "Description", "Category", "Qty", "Rate", "Amount"]]
    for index, item in enumerate(items, start=1):
        rows.append([
            str(index), item.description, item.category or "-", f"{Decimal(item.qty):,.2f}",
            _fmt(item.rate), _fmt(item.amount),
        ])
    table = Table(rows, colWidths=[10 * mm, 60 * mm, 30 * mm, 18 * mm, 28 * mm, 34 * mm], repeatRows=1)
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


def _totals_table(subtotal, gst_rate, gst_amount, total, total_label="Total"):
    table = Table([
        ["Subtotal", _fmt(subtotal)],
        [f"GST @ {Decimal(gst_rate):g}%", _fmt(gst_amount)],
        [total_label, _fmt(total)],
    ], colWidths=[50 * mm, 40 * mm], hAlign="RIGHT")
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f2f2f2")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def build_invoice_pdf(invoice: models.Invoice) -> bytes:
    buffer, doc = _document(invoice.invoice_no or "Draft invoice")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SmallMuted", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#555555")))
    status = invoice.status.upper()
    title = "TAX INVOICE" if not invoice.is_export else "EXPORT INVOICE UNDER LUT"
    if invoice.status != "issued":
        title = f"{title} - {status}"
    story = [
        Paragraph(escape(invoice.company_name_snapshot or invoice.tenant.company_name), styles["Title"]),
        Paragraph(escape(invoice.company_address_snapshot or invoice.tenant.address or ""), styles["Normal"]),
        Paragraph(
            f"GSTIN: {escape(invoice.company_gstin_snapshot or invoice.tenant.gstin or '-')} &nbsp;&nbsp; "
            f"CIN: {escape(invoice.company_cin_snapshot or invoice.tenant.cin or '-')}",
            styles["SmallMuted"],
        ),
        Spacer(1, 8 * mm),
        Paragraph(title, styles["Heading1"]),
        _metadata_table([
            ["Invoice number", invoice.invoice_no or "DRAFT", "Invoice date", str(invoice.invoice_date)],
            ["Order number", invoice.order_no or "-", "Order date", str(invoice.order_date or "-")],
            ["Customer", invoice.customer_name_snapshot or invoice.customer.name, "Country", invoice.customer_country_snapshot or invoice.customer.country],
            ["Bill to", invoice.customer_address_snapshot or invoice.customer.address or "-", "GSTIN", invoice.customer_gstin_snapshot or invoice.customer.gstin or "-"],
        ]),
        Spacer(1, 6 * mm),
        _items_table(invoice.items),
        Spacer(1, 5 * mm),
        _totals_table(invoice.subtotal, invoice.gst_rate, invoice.gst_amount, invoice.total),
    ]
    if invoice.is_export:
        story.extend([Spacer(1, 5 * mm), Paragraph(
            f"Supply under LUT without payment of integrated tax. LUT: {escape(invoice.lut_no_snapshot or '-')} "
            f"dated {invoice.lut_date_snapshot or '-'}.", styles["SmallMuted"],
        )])
    story.extend([Spacer(1, 7 * mm), Paragraph(
        f"Bank: {escape(invoice.bank_name_snapshot or '-')} &nbsp;&nbsp; "
        f"Account: {escape(invoice.bank_account_snapshot or '-')} &nbsp;&nbsp; "
        f"IFSC: {escape(invoice.bank_ifsc_snapshot or '-')}",
        styles["SmallMuted"],
    )])
    if invoice.status == "cancelled":
        story.extend([Spacer(1, 6 * mm), Paragraph(
            f"CANCELLED - {escape(invoice.cancellation_reason)}",
            ParagraphStyle(name="Cancelled", parent=styles["Heading2"], textColor=colors.red),
        )])
    doc.build(story)
    return buffer.getvalue()


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
