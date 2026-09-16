const BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

function errorDetail(detail) {
  if (Array.isArray(detail)) {
    return detail.map((error) => {
      const field = error.loc?.filter((part) => part !== "body").join(". ");
      return field ? `${field}: ${error.msg}` : error.msg;
    }).join("; ");
  }
  return typeof detail === "string" ? detail : JSON.stringify(detail);
}

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      credentials: "include",
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
  } catch (error) {
    throw new Error(`Unable to reach the server. Check your internet connection and try again. (${error.message})`);
  }
  if (!res.ok) {
    let detail = `Request failed (HTTP ${res.status}${res.statusText ? `: ${res.statusText}` : ""})`;
    try {
      const body = await res.json();
      detail = errorDetail(body.detail || body);
    } catch (_) {}
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

async function upload(path, file) {
  const body = new FormData(); body.append("file", file);
  let res;
  try {
    res = await fetch(`${BASE_URL}${path}`, { method: "POST", credentials: "include", body });
  } catch (error) {
    throw new Error(`Unable to reach the server (${error.message})`);
  }
  if (!res.ok) {
    let detail = `Request failed (HTTP ${res.status})`;
    try {
      const data = await res.json();
      if (data.detail) detail = errorDetail(data.detail);
    } catch (_) {}
    throw new Error(detail);
  }
  return res.json();
}

async function openPdf(path, filename, download = false, options = {}) {
  const preview = download ? null : window.open("", "_blank");
  const res = await fetch(`${BASE_URL}${path}?download=${download}`, {
    credentials: "include",
    ...options,
  });
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
  uploadCompanyMedia: (purpose, file) => upload(`/company/media/${purpose}`, file),
  removeCompanyMedia: (purpose) => request(`/company/media/${purpose}`, { method: "DELETE" }),
  companyMediaUrl: (assetId) => `${BASE_URL}/company/media/${assetId}`,
  previewCompanyInvoice: (data) => openPdf("/company/invoice-preview", "invoice-preview.pdf", false, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  }),
  getBillingSettings: () => request("/settings/billing"),
  updateBillingSettings: (data) => request("/settings/billing", { method: "PUT", body: JSON.stringify(data) }),
  listLutCertificates: () => request("/lut-certificates"),
  createLutCertificate: (data) => request("/lut-certificates", { method: "POST", body: JSON.stringify(data) }),
  activateLutCertificate: (id) => request(`/lut-certificates/${id}/activate`, { method: "POST" }),
  archiveLutCertificate: (id) => request(`/lut-certificates/${id}/archive`, { method: "POST" }),

  listCustomers: (includeArchived = true) => request(`/customers?include_archived=${includeArchived}`),
  createCustomer: (data) => request("/customers", { method: "POST", body: JSON.stringify(data) }),
  updateCustomer: (id, data) => request(`/customers/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  archiveCustomer: (id) => request(`/customers/${id}/archive`, { method: "POST" }),
  restoreCustomer: (id) => request(`/customers/${id}/restore`, { method: "POST" }),

  listProducts: (includeArchived = true) => request(`/products?include_archived=${includeArchived}`),
  createProduct: (data) => request("/products", { method: "POST", body: JSON.stringify(data) }),
  updateProduct: (id, data) => request(`/products/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  archiveProduct: (id) => request(`/products/${id}/archive`, { method: "POST" }),
  restoreProduct: (id) => request(`/products/${id}/restore`, { method: "POST" }),
  deleteProduct: (id) => request(`/products/${id}`, { method: "DELETE" }),

  listInvoices: () => request("/invoices"),
  createInvoice: (data) => request("/invoices", { method: "POST", body: JSON.stringify(data) }),
  updateInvoice: (id, data) => request(`/invoices/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  issueInvoice: (id) => request(`/invoices/${id}/issue`, { method: "POST" }),
  deleteInvoice: (id) => request(`/invoices/${id}`, { method: "DELETE" }),
  invoicePdf: (id, download = false) => openPdf(`/invoices/${id}/pdf`, "invoice.pdf", download),

  listReceipts: () => request("/receipts"),
  createReceipt: (data) => request("/receipts", { method: "POST", body: JSON.stringify(data) }),

  listCreditNotes: () => request("/credit-notes"),
  createCreditNote: (invoiceId, data) => request(`/invoices/${invoiceId}/credit-notes`, { method: "POST", body: JSON.stringify(data) }),

  receivablesReport: (asOf) => request(`/reports/receivables${asOf ? `?as_of=${asOf}` : ""}`),
  getLiveExchangeRate: (currency) => request(`/exchange-rates/${currency}/inr`),
  getNumberingSetup: () => request("/invoices/numbering-setup"),
  setNumberingSetup: (data) => request("/invoices/numbering-setup", { method: "PUT", body: JSON.stringify(data) }),
  salesByArea: () => request("/reports/sales/area-wise"),
  salesByProduct: () => request("/reports/sales/product-wise"),
};
