from datetime import date


def assert_status(response, expected):
    assert response.status_code == expected, response.text
    return response


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

    issued = assert_status(client.post(f"/invoices/{draft['id']}/issue"), 200).json()
    assert issued["status"] == "issued"
    assert issued["invoice_no"].startswith("ACME/")
    assert issued["customer_area_snapshot"] == "South"
    assert_status(client.put(f"/invoices/{draft['id']}", json=updated_payload), 409)

    pdf = assert_status(client.get(f"/invoices/{draft['id']}/pdf"), 200)
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF")

    archived = assert_status(client.post(f"/customers/{customer['id']}/archive"), 200).json()
    assert archived["is_archived"] is True
    assert_status(client.post("/invoices", json=invoice_payload(customer["id"])), 404)
    assert_status(client.post(f"/customers/{customer['id']}/restore"), 200)
    assert_status(client.delete(f"/customers/{customer['id']}"), 409)


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
    assert_status(client.post(f"/receipts/{receipt['id']}/void", json={"reason": "Wrong bank entry"}), 200)
    assert_status(client.post(f"/credit-notes/{note['id']}/cancel", json={"reason": "Wrong adjustment"}), 200)
    assert_status(client.post(f"/invoices/{invoice['id']}/cancel", json={"reason": "Entered in error"}), 200)
    assert_status(client.post(f"/receipts/{receipt['id']}/restore"), 409)


def test_tenant_isolation(client):
    signup(client)
    first_customer = assert_status(client.post("/customers", json=customer_payload()), 201).json()
    assert_status(client.post("/auth/logout"), 200)
    assert_status(client.post("/auth/signup", json={
        "company_name": "Second Company", "email": "second@example.com", "password": "test-password",
    }), 201)
    assert assert_status(client.get("/customers?include_archived=true"), 200).json() == []
    assert_status(client.get(f"/customers/{first_customer['id']}"), 404)
