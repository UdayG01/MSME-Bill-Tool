const BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail || body);
    } catch (_) {}
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

async function openPdf(path, filename, download = false) {
  const preview = download ? null : window.open("", "_blank");
  const res = await fetch(`${BASE_URL}${path}?download=${download}`, { credentials: "include" });
  if (!res.ok) {
    preview?.close();
    throw new Error("Could not generate PDF");
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  if (download) {
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  } else {
    if (preview) preview.location.href = url;
    else window.open(url, "_blank", "noopener,noreferrer");
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  }
}

export const api = {
  signup: (data) => request("/auth/signup", { method: "POST", body: JSON.stringify(data) }),
  login: (data) => request("/auth/login", { method: "POST", body: JSON.stringify(data) }),
  logout: () => request("/auth/logout", { method: "POST" }),
  me: () => request("/auth/me"),

  getCompany: () => request("/company"),
  updateCompany: (data) => request("/company", { method: "PUT", body: JSON.stringify(data) }),
  getLut: () => request("/lut"),
  updateLut: (data) => request("/lut", { method: "PUT", body: JSON.stringify(data) }),
  getBillingSettings: () => request("/settings/billing"),
  updateBillingSettings: (data) => request("/settings/billing", { method: "PUT", body: JSON.stringify(data) }),
  listTaxJurisdictions: () => request("/tax-jurisdictions"),
  createTaxJurisdiction: (data) => request("/tax-jurisdictions", { method: "POST", body: JSON.stringify(data) }),
  updateTaxJurisdiction: (id, data) => request(`/tax-jurisdictions/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  listLutCertificates: () => request("/lut-certificates"),
  createLutCertificate: (data) => request("/lut-certificates", { method: "POST", body: JSON.stringify(data) }),
  activateLutCertificate: (id) => request(`/lut-certificates/${id}/activate`, { method: "POST" }),
  archiveLutCertificate: (id) => request(`/lut-certificates/${id}/archive`, { method: "POST" }),

  listCustomers: (includeArchived = true) => request(`/customers?include_archived=${includeArchived}`),
  createCustomer: (data) => request("/customers", { method: "POST", body: JSON.stringify(data) }),
  updateCustomer: (id, data) => request(`/customers/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  archiveCustomer: (id) => request(`/customers/${id}/archive`, { method: "POST" }),
  restoreCustomer: (id) => request(`/customers/${id}/restore`, { method: "POST" }),
  deleteCustomer: (id) => request(`/customers/${id}`, { method: "DELETE" }),

  listInvoices: () => request("/invoices"),
  createInvoice: (data) => request("/invoices", { method: "POST", body: JSON.stringify(data) }),
  updateInvoice: (id, data) => request(`/invoices/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  issueInvoice: (id) => request(`/invoices/${id}/issue`, { method: "POST" }),
  cancelInvoice: (id, reason) => request(`/invoices/${id}/cancel`, { method: "POST", body: JSON.stringify({ reason }) }),
  deleteInvoice: (id) => request(`/invoices/${id}`, { method: "DELETE" }),
  getInvoice: (id) => request(`/invoices/${id}`),
  invoicePdf: (id, download = false) => openPdf(`/invoices/${id}/pdf`, "invoice.pdf", download),

  listReceipts: () => request("/receipts"),
  createReceipt: (data) => request("/receipts", { method: "POST", body: JSON.stringify(data) }),
  updateReceipt: (id, data) => request(`/receipts/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  voidReceipt: (id, reason) => request(`/receipts/${id}/void`, { method: "POST", body: JSON.stringify({ reason }) }),
  restoreReceipt: (id) => request(`/receipts/${id}/restore`, { method: "POST" }),

  listCreditNotes: () => request("/credit-notes"),
  createCreditNote: (invoiceId, data) => request(`/invoices/${invoiceId}/credit-notes`, { method: "POST", body: JSON.stringify(data) }),
  cancelCreditNote: (id, reason) => request(`/credit-notes/${id}/cancel`, { method: "POST", body: JSON.stringify({ reason }) }),
  creditNotePdf: (id, download = false) => openPdf(`/credit-notes/${id}/pdf`, "credit-note.pdf", download),

  receivablesReport: () => request("/reports/receivables"),
  salesByArea: () => request("/reports/sales/area-wise"),
  salesByProduct: () => request("/reports/sales/product-wise"),
};
