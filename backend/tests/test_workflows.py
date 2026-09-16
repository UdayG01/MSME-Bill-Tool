from datetime import date
from io import BytesIO
import re

from PIL import Image as PILImage, ImageDraw


def assert_status(response, expected):
    assert response.status_code == expected, response.text
    return response


def pdf_page_count(content: bytes) -> int:
    return len(re.findall(rb"/Type\s*/Page\b", content))


def signup(client):
    assert_status(client.post("/auth/signup", json={
        "company_name": "Acme Services",
        "email": "owner@example.com",
        "password": "test-password",
    }), 201)
    assert_status(client.put("/company", json={
        "company_name": "Acme Services Private Limited",
        "address": "Bengaluru, Karnataka",
        "gstin": "29ABCDE1234F1Z5",
        "state_code": "29",
        "invoice_prefix": "ACME",
        "bank_name": "Example Bank",
        "bank_account": "1234567890",
        "bank_ifsc": "EXAM0001234",
    }), 200)


def customer_payload(name="Northwind", area="South"):
    return {
        "name": name,
        "address": "Bengaluru",
        "gstin": "29AAAAA0000A1Z5",
        "country": "India",
        "is_foreign": False,
        "area": area,
        "state_code": "29",
        "credit_days": 30,
    }


def test_state_codes_are_validated_before_a_database_write(client):
    signup(client)
    response = client.put("/company", json={"state_code": "Haryana"})
    assert response.status_code == 422
    assert "two-digit code" in response.text


def test_authenticated_live_exchange_rate_endpoint(client, monkeypatch):
    signup(client)
    monkeypatch.setattr(
        "routers.exchange_rates.current_rate_to_inr",
        lambda currency: {
            "base_currency": currency.upper(),
            "quote_currency": "INR",
            "rate": "85.25",
            "rate_date": str(date.today()),
            "source": "Frankfurter",
        },
    )
    response = assert_status(client.get("/exchange-rates/usd/inr"), 200).json()
    assert response["base_currency"] == "USD"
    assert float(response["rate"]) == 85.25
    assert response["source"] == "Frankfurter"

    response = client.post("/customers", json={**customer_payload(), "state_code": "Haryana"})
    assert response.status_code == 422
    assert "two-digit code" in response.text


def invoice_payload(customer_id, rate=1000):
    return {
        "customer_id": customer_id,
        "invoice_date": str(date.today()),
        "order_no": "PO-100",
        "order_date": str(date.today()),
        "gst_rate": 18,
        "items": [{"description": "Consulting", "category": "Services", "qty": 1, "rate": rate}],
    }


def test_invoice_lifecycle_pdf_and_customer_archival(client):
    signup(client)
    customer = assert_status(client.post("/customers", json=customer_payload()), 201).json()
    draft = assert_status(client.post("/invoices", json=invoice_payload(customer["id"])), 201).json()
    assert draft["status"] == "draft"
    assert draft["invoice_no"] is None

    updated_payload = invoice_payload(customer["id"], rate=1200)
    draft = assert_status(client.put(f"/invoices/{draft['id']}", json=updated_payload), 200).json()
    assert float(draft["total"]) == 1416
    assert draft["order_no"] == "PO-100"
    assert draft["order_date"] == str(date.today())

    issued = assert_status(client.post(f"/invoices/{draft['id']}/issue"), 200).json()
    assert issued["status"] == "issued"
    assert issued["invoice_no"].startswith("ACME/")
    assert issued["customer_area_snapshot"] == "South"
    edited = assert_status(client.put(f"/invoices/{draft['id']}", json=updated_payload), 200).json()
    assert edited["status"] == "issued"
    assert edited["invoice_no"] == issued["invoice_no"]

    pdf = assert_status(client.get(f"/invoices/{draft['id']}/pdf"), 200)
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF")
    assert pdf_page_count(pdf.content) == 1

    archived = assert_status(client.post(f"/customers/{customer['id']}/archive"), 200).json()
    assert archived["is_archived"] is True
    assert_status(client.post("/invoices", json=invoice_payload(customer["id"])), 404)
    assert_status(client.post(f"/customers/{customer['id']}/restore"), 200)
    assert_status(client.delete(f"/customers/{customer['id']}"), 409)


def test_current_logo_is_used_when_an_older_invoice_has_no_logo_snapshot(client):
    signup(client)
    customer = assert_status(client.post("/customers", json=customer_payload()), 201).json()
    draft = assert_status(client.post("/invoices", json=invoice_payload(customer["id"])), 201).json()
    invoice = assert_status(client.post(f"/invoices/{draft['id']}/issue"), 200).json()

    logo_file = BytesIO()
    logo_image = PILImage.new("RGB", (300, 300), "white")
    ImageDraw.Draw(logo_image).rectangle((100, 105, 200, 185), fill="black")
    logo_image.save(logo_file, format="JPEG")
    logo = logo_file.getvalue()
    uploaded = assert_status(client.post(
        "/company/media/logo",
        files={"file": ("logo.jpg", logo, "image/jpeg")},
    ), 201).json()
    assert uploaded["width"] < 150
    assert uploaded["height"] < 130

    preview = assert_status(client.post("/company/invoice-preview", json={
        "company_name": "Preview Company",
        "logo_asset_id": uploaded["id"],
    }), 200)
    assert preview.content.startswith(b"%PDF")
    assert b"/Subtype /Image" in preview.content

    pdf = assert_status(client.get(f"/invoices/{invoice['id']}/pdf"), 200)
    assert b"/Subtype /Image" in pdf.content

    assert_status(client.delete("/company/media/logo"), 204)
    assert assert_status(client.get("/company"), 200).json()["logo_asset_id"] is None


def test_receipts_credit_notes_reports_and_cancellation_rules(client):
    signup(client)
    customer = assert_status(client.post("/customers", json=customer_payload()), 201).json()
    draft = assert_status(client.post("/invoices", json=invoice_payload(customer["id"])), 201).json()
    invoice = assert_status(client.post(f"/invoices/{draft['id']}/issue"), 200).json()

    receipt_data = {
        "invoice_id": invoice["id"], "amount": 500, "date": str(date.today()),
        "mode": "Bank Transfer", "reference": "UTR-1",
    }
    receipt = assert_status(client.post("/receipts", json=receipt_data), 201).json()
    assert_status(client.post("/receipts", json={**receipt_data, "amount": 1000}), 409)
    receipt = assert_status(client.put(f"/receipts/{receipt['id']}", json={
        "amount": 400, "date": str(date.today()), "mode": "UPI", "reference": "UPI-1",
    }), 200).json()
    assert float(receipt["amount"]) == 400

    note = assert_status(client.post(f"/invoices/{invoice['id']}/credit-notes", json={
        "date": str(date.today()), "reason": "Service adjustment",
        "items": [{"description": "Adjustment", "category": "Services", "qty": 1, "rate": 100}],
    }), 201).json()
    assert float(note["total"]) == 118
    note_pdf = assert_status(client.get(f"/credit-notes/{note['id']}/pdf"), 200)
    assert note_pdf.content.startswith(b"%PDF")

    rows = assert_status(client.get("/reports/receivables"), 200).json()
    assert len(rows) == 1
    assert float(rows[0]["paid"]) == 400
    assert float(rows[0]["credited"]) == 118
    assert float(rows[0]["balance"]) == 662
    area = assert_status(client.get("/reports/sales/area-wise"), 200).json()
    product = assert_status(client.get("/reports/sales/product-wise"), 200).json()
    assert float(area[0]["total"]) == float(product[0]["total"]) == 900

    assert_status(client.post(f"/invoices/{invoice['id']}/cancel", json={"reason": "Entered in error"}), 409)
    assert_status(client.put(f"/invoices/{invoice['id']}", json=invoice_payload(customer["id"], rate=1300)), 409)
    assert_status(client.delete(f"/invoices/{invoice['id']}"), 409)
    assert_status(client.post(f"/receipts/{receipt['id']}/void", json={"reason": "Wrong bank entry"}), 200)
    assert_status(client.post(f"/credit-notes/{note['id']}/cancel", json={"reason": "Wrong adjustment"}), 200)
    assert_status(client.post(f"/invoices/{invoice['id']}/cancel", json={"reason": "Entered in error"}), 200)
    assert_status(client.post(f"/receipts/{receipt['id']}/restore"), 409)


def test_products_catalog_crud_and_invoice_autofill_payload(client):
    signup(client)
    product = assert_status(client.post("/products", json={
        "name": "Monthly compliance retainer",
        "description": "GST and MSME filing support",
        "hsn_sac": "9982",
        "amount": 2500,
    }), 201).json()
    assert product["name"] == "Monthly compliance retainer"
    assert float(product["amount"]) == 2500

    product = assert_status(client.put(f"/products/{product['id']}", json={
        "name": "Monthly compliance retainer",
        "description": "GST, MSME, and advisory support",
        "hsn_sac": "9982",
        "amount": 3000,
    }), 200).json()
    assert product["description"] == "GST, MSME, and advisory support"

    products = assert_status(client.get("/products?include_archived=true"), 200).json()
    assert [row["id"] for row in products] == [product["id"]]

    customer = assert_status(client.post("/customers", json=customer_payload()), 201).json()
    invoice = assert_status(client.post("/invoices", json={
        "customer_id": customer["id"],
        "invoice_date": str(date.today()),
        "gst_rate": 18,
        "items": [{
            "item_name": product["name"],
            "item_description": product["description"],
            "hsn_sac": product["hsn_sac"],
            "qty": 2,
            "rate": product["amount"],
        }],
    }), 201).json()
    assert invoice["items"][0]["item_name"] == product["name"]
    assert invoice["items"][0]["hsn_sac"] == "9982"
    assert float(invoice["subtotal"]) == 6000

    archived = assert_status(client.post(f"/products/{product['id']}/archive"), 200).json()
    assert archived["is_archived"] is True
    assert_status(client.post(f"/products/{product['id']}/restore"), 200)
    assert_status(client.delete(f"/products/{product['id']}"), 204)


def test_tenant_isolation(client):
    signup(client)
    first_customer = assert_status(client.post("/customers", json=customer_payload()), 201).json()
    assert_status(client.post("/auth/logout"), 200)
    assert_status(client.post("/auth/signup", json={
        "company_name": "Second Company", "email": "second@example.com", "password": "test-password",
    }), 201)
    assert assert_status(client.get("/customers?include_archived=true"), 200).json() == []
    assert_status(client.get(f"/customers/{first_customer['id']}"), 404)


def test_export_values_freeze_and_full_receipt_records_forex_without_false_balance(client):
    signup(client)
    assert_status(client.put("/settings/billing", json={
        "base_currency": "INR",
        "allow_export_invoicing": True,
        "require_valid_lut_for_export": True,
        "terms_notes": "",
        "tagline": "",
    }), 200)
    customer = assert_status(client.post("/customers", json={
        "name": "Overseas Customer",
        "address": "Singapore",
        "gstin": "",
        "country": "Singapore",
        "is_foreign": True,
        "area": "Export",
        "state_code": "",
        "credit_days": 30,
    }), 201).json()
    lut = assert_status(client.post("/lut-certificates", json={
        "arn": "AD290626000001",
        "financial_year": "2026-27",
        "valid_from": "2020-04-01",
        "valid_to": "2099-03-31",
    }), 201).json()
    assert_status(client.post(f"/lut-certificates/{lut['id']}/activate"), 200)

    payload = {
        "customer_id": customer["id"],
        "invoice_date": str(date.today()),
        "gst_rate": 0,
        "document_currency": "USD",
        "exchange_rate_to_inr": 80,
        "items": [{"item_name": "Export service", "hsn_sac": "9983", "qty": 1, "rate": 100}],
    }
    draft = assert_status(client.post("/invoices", json=payload), 201).json()
    assert float(draft["total"]) == 8000
    assert_status(client.put(f"/invoices/{draft['id']}", json={**payload, "exchange_rate_to_inr": 81}), 409)
    invoice = assert_status(client.post(f"/invoices/{draft['id']}/issue"), 200).json()

    receipt = assert_status(client.post("/receipts", json={
        "invoice_id": invoice["id"],
        "amount": 8500,
        "date": str(date.today()),
        "mode": "Bank Transfer",
        "reference": "FIRC-UTR-1",
        "receipt_currency": "USD",
        "foreign_amount": 100,
        "exchange_rate_to_inr": 85,
        "firc_number": "FIRC-1",
    }), 201).json()
    assert float(receipt["amount"]) == 8500
    assert float(receipt["applied_amount_inr"]) == 8000
    assert float(receipt["forex_gain_loss_inr"]) == 500
    assert assert_status(client.get("/reports/receivables"), 200).json() == []

    loss_draft = assert_status(client.post("/invoices", json=payload), 201).json()
    loss_invoice = assert_status(client.post(f"/invoices/{loss_draft['id']}/issue"), 200).json()
    loss_receipt = assert_status(client.post("/receipts", json={
        "invoice_id": loss_invoice["id"],
        "amount": 7500,
        "date": str(date.today()),
        "mode": "Bank Transfer",
        "reference": "FIRC-UTR-2",
        "receipt_currency": "USD",
        "foreign_amount": 100,
        "exchange_rate_to_inr": 75,
        "firc_number": "FIRC-2",
    }), 201).json()
    assert float(loss_receipt["amount"]) == 7500
    assert float(loss_receipt["applied_amount_inr"]) == 8000
    assert float(loss_receipt["forex_gain_loss_inr"]) == -500
    assert assert_status(client.get("/reports/receivables"), 200).json() == []


def test_twenty_item_invoice_generates_multiple_pdf_pages(client):
    signup(client)
    customer = assert_status(client.post("/customers", json=customer_payload()), 201).json()
    payload = invoice_payload(customer["id"])
    payload["items"] = [
        {
            "item_name": f"Professional service line {index}",
            "item_description": "Detailed service description that wraps cleanly beneath the item name.",
            "hsn_sac": "9983",
            "qty": 1,
            "rate": 100,
        }
        for index in range(1, 21)
    ]
    draft = assert_status(client.post("/invoices", json=payload), 201).json()
    invoice = assert_status(client.post(f"/invoices/{draft['id']}/issue"), 200).json()
    pdf = assert_status(client.get(f"/invoices/{invoice['id']}/pdf"), 200)
    assert pdf_page_count(pdf.content) >= 2
