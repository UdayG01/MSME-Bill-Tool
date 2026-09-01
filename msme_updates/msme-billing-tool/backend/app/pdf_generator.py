"""
Invoice PDF generation.

Two templates, selected automatically based on invoice.is_export:
- Domestic: IGST or CGST+SGST breakdown, Place of Supply, HSN/SAC, reverse
  charge line, UPI QR code, amount in words in INR.
- Export: foreign-currency-only display, LUT declaration folded into
  Terms & Notes, international wire transfer bank details, no UPI/QR.

Both share the same header (logo + company details), Bill To block,
item table with repeating header row on page breaks, Terms & Notes box,
signature image, and marketing tagline banner — so branding stays
consistent regardless of invoice type.
"""
import os
import qrcode
from num2words import num2words
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

PAGE_W, PAGE_H = A4
MARGIN = 12 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

_styles = getSampleStyleSheet()
h1 = ParagraphStyle('h1', parent=_styles['Normal'], fontName='Helvetica-Bold', fontSize=15, alignment=TA_LEFT, spaceAfter=3)
small_left = ParagraphStyle('small_left', parent=_styles['Normal'], fontSize=8.5, alignment=TA_LEFT, leading=12)
title_style = ParagraphStyle('title', parent=_styles['Normal'], fontName='Helvetica-Bold', fontSize=13, alignment=TA_CENTER, spaceBefore=8, spaceAfter=8)
label = ParagraphStyle('label', parent=_styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=12)
normal = ParagraphStyle('normal', parent=_styles['Normal'], fontSize=9, leading=12)
normal_right = ParagraphStyle('normal_right', parent=_styles['Normal'], fontSize=9, leading=12, alignment=TA_RIGHT)
small_note = ParagraphStyle('small_note', parent=_styles['Normal'], fontSize=8, leading=11, textColor=colors.HexColor('#444444'))
cell_hdr = ParagraphStyle('cell_hdr', parent=_styles['Normal'], fontName='Helvetica-Bold', fontSize=9, alignment=TA_CENTER, textColor=colors.white)
cell = ParagraphStyle('cell', parent=_styles['Normal'], fontSize=8.5, alignment=TA_LEFT, leading=11)
cell_c = ParagraphStyle('cell_c', parent=_styles['Normal'], fontSize=8.5, alignment=TA_CENTER, leading=11)
cell_r = ParagraphStyle('cell_r', parent=_styles['Normal'], fontSize=8.5, alignment=TA_RIGHT, leading=11)
tagline_style = ParagraphStyle('tagline', parent=_styles['Normal'], fontName='Helvetica-BoldOblique', fontSize=10, alignment=TA_CENTER, textColor=colors.white, leading=13)
terms_body = ParagraphStyle('terms_body', parent=_styles['Normal'], fontSize=7.8, leading=11)

ITEM_COLS = [8*mm, 88*mm, 22*mm, 14*mm, 26*mm, CONTENT_W - (8+88+22+14+26)*mm]


def _words_for_amount(amount, unit_name, subunit_name, lang='en'):
    whole = int(amount)
    sub = round((amount - whole) * 100)
    words = num2words(whole, lang=lang).replace(',', '').title()
    text = f"{unit_name} {words} Only"
    if sub:
        sub_words = num2words(sub, lang=lang).title()
        text = f"{unit_name} {words} and {sub_words} {subunit_name} Only"
    return text


def _generate_upi_qr(upi_id: str, amount: float, payee_name: str, invoice_no: str, out_path: str):
    upi_string = f"upi://pay?pa={upi_id}&pn={payee_name}&am={amount:.2f}&cu=INR&tn={invoice_no}"
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(upi_string)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(out_path)
    return out_path


def _header_block(company: dict, invoice_meta: dict, extra_meta_row=None):
    blocks = []
    logo_cell = Image(company['logo_path'], width=26*mm, height=16*mm) if company.get('logo_path') and os.path.exists(company['logo_path']) else Paragraph("", normal)
    details_cell = [
        Paragraph(company['name'], h1),
        Paragraph(company['address'], small_left),
        Paragraph(f"GSTIN: {company['gstin']} &nbsp;|&nbsp; CIN: {company.get('cin') or '-'}", small_left),
        Paragraph(f"Udyam Reg. No: {company.get('udyam_number') or '-'}", small_left),
        Paragraph(f"Email: {company.get('email') or '-'} &nbsp;|&nbsp; Mobile: {company.get('mobile') or '-'}", small_left),
    ]
    header_table = Table([[logo_cell, details_cell]], colWidths=[30*mm, CONTENT_W - 30*mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    blocks.append(header_table)
    blocks.append(Paragraph(invoice_meta['title'], title_style))

    meta_rows = [
        [Paragraph("Invoice Number", label), Paragraph(invoice_meta['invoice_no'], normal),
         Paragraph("Invoice Date", label), Paragraph(invoice_meta['invoice_date'], normal)],
        [Paragraph("Order Number", label), Paragraph(invoice_meta.get('order_no') or '-', normal),
         Paragraph("Order Date", label), Paragraph(invoice_meta.get('order_date') or '-', normal)],
    ]
    meta_rows.append(invoice_meta['row3'])
    meta_rows.append([Paragraph("Payment Terms", label), Paragraph(invoice_meta['payment_terms'], normal),
                       Paragraph("Due Date", label), Paragraph(invoice_meta['due_date'], normal)])
    if extra_meta_row:
        meta_rows.append(extra_meta_row)

    mw = [32*mm, CONTENT_W/2 - 32*mm, 44*mm, CONTENT_W/2 - 44*mm]
    meta_table = Table(meta_rows, colWidths=mw)
    meta_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#999999')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 6), ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    blocks.append(meta_table)
    blocks.append(Spacer(1, 8))
    return blocks


def _billto_block(customer: dict, show_gstin: bool):
    if show_gstin:
        row2 = [Paragraph(f"<b>{customer['name']}</b>", normal), Paragraph(f"<b>GSTIN:</b> {customer.get('gstin') or '-'}", normal)]
    else:
        row2 = [Paragraph(f"<b>{customer['name']}</b>", normal), Paragraph(f"<b>Country:</b> {customer['country']}", normal)]
    billto_data = [[Paragraph("Bill To", label), ""], row2, [Paragraph(customer['address'], normal), ""]]
    bw = [CONTENT_W * 0.6, CONTENT_W * 0.4]
    billto_table = Table(billto_data, colWidths=bw)
    style = [
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#999999')),
        ('SPAN', (0,0), (1,0)),
        ('SPAN', (0,2), (1,2)),
        ('BACKGROUND', (0,0), (1,0), colors.HexColor('#f2f2f2')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 6), ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]
    billto_table.setStyle(TableStyle(style))
    return [billto_table, Spacer(1, 8)]


def _items_table(line_items: list, currency_symbol: str):
    item_header = [
        Paragraph("#", cell_hdr), Paragraph("Description", cell_hdr),
        Paragraph("HSN/SAC", cell_hdr), Paragraph("Qty", cell_hdr),
        Paragraph(f"Rate ({currency_symbol})", cell_hdr), Paragraph(f"Amount ({currency_symbol})", cell_hdr)
    ]
    rows = [item_header]
    subtotal = 0.0
    for idx, item in enumerate(line_items, 1):
        amount = item['qty'] * item['rate']
        subtotal += amount
        desc = item['description']
        if item.get('note'):
            desc += f"<br/><font size=7.5 color='#555555'>{item['note']}</font>"
        rows.append([
            Paragraph(str(idx), cell_c), Paragraph(desc, cell), Paragraph(item['hsn_sac'], cell_c),
            Paragraph(f"{item['qty']:.2f}", cell_c), Paragraph(f"{item['rate']:,.2f}", cell_r),
            Paragraph(f"{amount:,.2f}", cell_r),
        ])
    items_table = Table(rows, colWidths=ITEM_COLS, repeatRows=1)
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2f4858')),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#999999')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 5), ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f7f8f9')]),
    ]))
    return items_table, subtotal


def _terms_table(terms_list: list):
    terms_items = "".join([f"&bull; {t}<br/>" for t in terms_list])
    terms_para = Paragraph(f"<b>Terms &amp; Notes</b><br/>{terms_items}", terms_body)
    terms_table = Table([[terms_para]], colWidths=[CONTENT_W])
    terms_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#cccccc')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fafafa')),
        ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    return terms_table


def _signature_block(company: dict):
    if company.get('signature_path') and os.path.exists(company['signature_path']):
        sig_img_cell = Image(company['signature_path'], width=32*mm, height=13*mm)
    else:
        sig_img_cell = Paragraph("<br/><br/>", normal)
    sig_data = [
        ["", Paragraph(f"For {company['name']}", normal_right)],
        ["", sig_img_cell],
        ["", Paragraph("Authorized Signatory", normal_right)],
    ]
    sig_table = Table(sig_data, colWidths=[CONTENT_W - 65*mm, 65*mm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (1,1), (1,1), 'RIGHT'),
        ('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    return sig_table


def _tagline_table(tagline: str):
    tagline_table = Table([[Paragraph(tagline, tagline_style)]], colWidths=[CONTENT_W])
    tagline_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#2f4858')),
        ('TOPPADDING', (0,0), (-1,-1), 8), ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10), ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    return tagline_table


def _page_footer(invoice_no: str, company_name: str):
    def on_page(canvas, doc_):
        canvas.saveState()
        canvas.setFont('Helvetica', 7.5)
        canvas.setFillColor(colors.HexColor('#777777'))
        canvas.drawRightString(PAGE_W - MARGIN, MARGIN * 0.5, f"Page {doc_.page}")
        canvas.drawString(MARGIN, MARGIN * 0.5, f"{invoice_no}  |  {company_name}")
        canvas.restoreState()
    return on_page


def generate_domestic_invoice_pdf(company: dict, customer: dict, invoice: dict, line_items: list, out_path: str):
    """
    invoice dict expected keys: invoice_no, invoice_date, order_no, order_date,
    place_of_supply_state, place_of_supply_code, tax_type ('CGST_SGST'|'IGST'),
    reverse_charge (bool), gst_rate, payment_terms_days, due_date
    """
    doc = SimpleDocTemplate(out_path, pagesize=A4, topMargin=MARGIN, bottomMargin=MARGIN, leftMargin=MARGIN, rightMargin=MARGIN)
    story = []

    row3 = [
        Paragraph("Place of Supply", label),
        Paragraph(f"{invoice['place_of_supply_state']} (State Code: {invoice['place_of_supply_code']})", normal),
        Paragraph("Reverse Charge Applicable", label),
        Paragraph("Yes" if invoice['reverse_charge'] else "No", normal),
    ]
    invoice_meta = dict(
        title="TAX INVOICE", invoice_no=invoice['invoice_no'], invoice_date=invoice['invoice_date'],
        order_no=invoice.get('order_no'), order_date=invoice.get('order_date'),
        row3=row3, payment_terms=f"{invoice['payment_terms_days']} Days", due_date=invoice['due_date'],
    )
    story.extend(_header_block(company, invoice_meta))
    story.extend(_billto_block(customer, show_gstin=True))

    items_table, subtotal = _items_table(line_items, "INR")
    story.append(items_table)
    story.append(Spacer(1, 8))

    gst_rate = invoice['gst_rate']
    if invoice['tax_type'] == 'IGST':
        tax_total = subtotal * gst_rate / 100
        totals_rows = [
            [Paragraph("Subtotal", normal), Paragraph(f"{subtotal:,.2f}", normal_right)],
            [Paragraph(f"IGST @ {gst_rate:.2f}%", normal), Paragraph(f"{tax_total:,.2f}", normal_right)],
        ]
    else:
        half = gst_rate / 2
        tax_total = subtotal * gst_rate / 100
        totals_rows = [
            [Paragraph("Subtotal", normal), Paragraph(f"{subtotal:,.2f}", normal_right)],
            [Paragraph(f"CGST @ {half:.2f}%", normal), Paragraph(f"{tax_total/2:,.2f}", normal_right)],
            [Paragraph(f"SGST @ {half:.2f}%", normal), Paragraph(f"{tax_total/2:,.2f}", normal_right)],
        ]
    grand_total = subtotal + tax_total
    totals_rows.append([Paragraph("<b>Total</b>", normal), Paragraph(f"<b>INR {grand_total:,.2f}</b>", normal_right)])

    totals_table = Table(totals_rows, colWidths=[CONTENT_W - 56*mm, 56*mm], hAlign='RIGHT')
    totals_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#999999')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('LINEABOVE', (0,-1), (-1,-1), 1, colors.HexColor('#2f4858')),
        ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    words_para = Paragraph(f"<b>Amount in Words:</b> {_words_for_amount(grand_total, 'Rupees', 'Paise')}", normal)

    qr_path = out_path + "_qr.png"
    has_upi = bool(company.get('upi_id'))
    if has_upi:
        _generate_upi_qr(company['upi_id'], grand_total, company['name'], invoice['invoice_no'], qr_path)
        bank_para = Paragraph(
            f"<b>Bank Details</b><br/>Bank: {company.get('bank_name') or '-'}<br/>"
            f"Account Number: {company.get('bank_account') or '-'}<br/>IFSC: {company.get('bank_ifsc') or '-'}<br/>"
            f"<font size=7.5 color='#555555'>Payment to be made to the above account only.</font>", normal)
        upi_para = Paragraph(f"<b>Pay via UPI</b><br/>UPI ID: {company['upi_id']}", normal)
        qr_img = Image(qr_path, width=24*mm, height=24*mm)
        bw = CONTENT_W - 24*mm - 55*mm
        bank_table = Table([[bank_para, upi_para, qr_img]], colWidths=[bw, 55*mm, 24*mm])
        bank_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#999999')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (2,0), (2,0), 'CENTER'),
            ('LEFTPADDING', (0,0), (-1,-1), 7), ('RIGHTPADDING', (0,0), (-1,-1), 7),
            ('TOPPADDING', (0,0), (-1,-1), 7), ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ]))
    else:
        bank_para = Paragraph(
            f"<b>Bank Details</b><br/>Bank: {company.get('bank_name') or '-'}<br/>"
            f"Account Number: {company.get('bank_account') or '-'}<br/>IFSC: {company.get('bank_ifsc') or '-'}", normal)
        bank_table = Table([[bank_para]], colWidths=[CONTENT_W])
        bank_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#999999')),
            ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 7), ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ]))

    default_terms = [
        "Payment due within the agreed payment terms from the invoice date.",
        "Interest under the MSMED Act, 2006 applies on delayed payments beyond the due date.",
        "Any discrepancy in this invoice must be reported within 7 days of receipt.",
    ]
    terms_list = (company.get('terms_notes').split('\n') if company.get('terms_notes') else default_terms)
    terms_table = _terms_table(terms_list)
    sig_table = _signature_block(company)
    disclaimer = Paragraph("This is a computer-generated invoice.", small_note)

    closing_items = [
        totals_table, Spacer(1, 5), words_para, Spacer(1, 6),
        bank_table, Spacer(1, 6), terms_table, Spacer(1, 8),
        sig_table, Spacer(1, 5), disclaimer,
    ]
    if company.get('tagline'):
        closing_items.extend([Spacer(1, 4), _tagline_table(company['tagline'])])
    story.append(KeepTogether(closing_items))

    doc.build(story, onFirstPage=_page_footer(invoice['invoice_no'], company['name']),
               onLaterPages=_page_footer(invoice['invoice_no'], company['name']))

    if has_upi and os.path.exists(qr_path):
        os.remove(qr_path)

    return out_path


def generate_export_invoice_pdf(company: dict, customer: dict, invoice: dict, line_items: list, out_path: str):
    """
    invoice dict expected keys: invoice_no, invoice_date, order_no, order_date,
    currency_code, currency_symbol, currency_words_unit, currency_words_subunit,
    reverse_charge, payment_terms_days, due_date, lut_arn, lut_validity
    """
    doc = SimpleDocTemplate(out_path, pagesize=A4, topMargin=MARGIN, bottomMargin=MARGIN, leftMargin=MARGIN, rightMargin=MARGIN)
    story = []

    row3 = [
        Paragraph("Invoice Currency", label), Paragraph(invoice['currency_code'], normal),
        Paragraph("Reverse Charge Applicable", label), Paragraph("Yes" if invoice['reverse_charge'] else "No", normal),
    ]
    invoice_meta = dict(
        title="TAX INVOICE \u2013 EXPORT", invoice_no=invoice['invoice_no'], invoice_date=invoice['invoice_date'],
        order_no=invoice.get('order_no'), order_date=invoice.get('order_date'),
        row3=row3, payment_terms=f"{invoice['payment_terms_days']} Days", due_date=invoice['due_date'],
    )
    extra_row = [
        Paragraph("LUT ARN", label), Paragraph(invoice['lut_arn'], normal),
        Paragraph("LUT Valid", label), Paragraph(invoice['lut_validity'], normal),
    ]
    story.extend(_header_block(company, invoice_meta, extra_meta_row=extra_row))
    story.extend(_billto_block(customer, show_gstin=False))

    sym = invoice['currency_symbol']
    items_table, subtotal = _items_table(line_items, sym)
    story.append(items_table)
    story.append(Spacer(1, 8))

    totals_rows = [
        [Paragraph("Subtotal", normal), Paragraph(f"{sym} {subtotal:,.2f}", normal_right)],
        [Paragraph("IGST @ 0.00% (Export under LUT)", normal), Paragraph(f"{sym} 0.00", normal_right)],
        [Paragraph("<b>Total</b>", normal), Paragraph(f"<b>{sym} {subtotal:,.2f}</b>", normal_right)],
    ]
    totals_table = Table(totals_rows, colWidths=[CONTENT_W - 62*mm, 62*mm], hAlign='RIGHT')
    totals_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#999999')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('LINEABOVE', (0,-1), (-1,-1), 1, colors.HexColor('#2f4858')),
        ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    words_para = Paragraph(
        f"<b>Amount in Words:</b> {_words_for_amount(subtotal, invoice['currency_words_unit'], invoice['currency_words_subunit'])}",
        normal)

    bank_para = Paragraph(
        f"<b>Bank Details (for International Wire Transfer)</b><br/>"
        f"Beneficiary Name: {company['name']}<br/>Bank: {company.get('intl_bank_name') or '-'}<br/>"
        f"Account Number: {company.get('intl_bank_account') or '-'}<br/>SWIFT Code: {company.get('intl_swift_code') or '-'}<br/>"
        f"Bank Address: {company.get('intl_bank_address') or '-'}<br/>"
        f"<font size=7.5 color='#555555'>All bank charges outside India to be borne by the remitter.</font>", normal)
    bank_table = Table([[bank_para]], colWidths=[CONTENT_W])
    bank_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#999999')),
        ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 7), ('BOTTOMPADDING', (0,0), (-1,-1), 7),
    ]))

    default_terms = [
        "Supply meant for export under Letter of Undertaking (LUT) without payment of Integrated Tax.",
        "Payment due within the agreed payment terms from the invoice date.",
        "This invoice is issued for export of services under LUT, zero-rated for GST purposes.",
        "Any discrepancy in this invoice must be reported within 7 days of receipt.",
    ]
    terms_list = (company.get('terms_notes').split('\n') if company.get('terms_notes') else default_terms)
    if not any('LUT' in t for t in terms_list):
        terms_list = [default_terms[0]] + terms_list
    terms_table = _terms_table(terms_list)
    sig_table = _signature_block(company)
    disclaimer = Paragraph("This is a computer-generated invoice.", small_note)

    closing_items = [
        totals_table, Spacer(1, 5), words_para, Spacer(1, 6),
        bank_table, Spacer(1, 6), terms_table, Spacer(1, 8),
        sig_table, Spacer(1, 5), disclaimer,
    ]
    if company.get('tagline'):
        closing_items.extend([Spacer(1, 4), _tagline_table(company['tagline'])])
    story.append(KeepTogether(closing_items))

    doc.build(story, onFirstPage=_page_footer(invoice['invoice_no'], company['name']),
               onLaterPages=_page_footer(invoice['invoice_no'], company['name']))
    return out_path


CURRENCY_INFO = {
    "USD": {"symbol": "$", "words_unit": "US Dollars", "words_subunit": "Cents"},
    "EUR": {"symbol": "\u20ac", "words_unit": "Euros", "words_subunit": "Cents"},
    "GBP": {"symbol": "\u00a3", "words_unit": "Pounds Sterling", "words_subunit": "Pence"},
    "AED": {"symbol": "AED", "words_unit": "UAE Dirhams", "words_subunit": "Fils"},
    "SGD": {"symbol": "S$", "words_unit": "Singapore Dollars", "words_subunit": "Cents"},
}
