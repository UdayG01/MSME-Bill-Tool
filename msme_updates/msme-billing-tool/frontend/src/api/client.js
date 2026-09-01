const BASE = '/api';

async function handleResponse(res) {
  if (!res.ok) {
    let detail = 'Something went wrong.';
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch (e) {}
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  // Company
  getCompany: () => fetch(`${BASE}/company`).then(handleResponse),
  saveCompany: (payload) =>
    fetch(`${BASE}/company`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(handleResponse),
  uploadLogo: (file) => {
    const form = new FormData();
    form.append('file', file);
    return fetch(`${BASE}/company/logo`, { method: 'POST', body: form }).then(handleResponse);
  },
  uploadSignature: (file) => {
    const form = new FormData();
    form.append('file', file);
    return fetch(`${BASE}/company/signature`, { method: 'POST', body: form }).then(handleResponse);
  },

  // LUT
  listLUT: () => fetch(`${BASE}/lut`).then(handleResponse),
  createLUT: (payload) =>
    fetch(`${BASE}/lut`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(handleResponse),

  // Customers
  listCustomers: () => fetch(`${BASE}/customers`).then(handleResponse),
  getCustomer: (id) => fetch(`${BASE}/customers/${id}`).then(handleResponse),
  createCustomer: (payload) =>
    fetch(`${BASE}/customers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(handleResponse),
  updateCustomer: (id, payload) =>
    fetch(`${BASE}/customers/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(handleResponse),

  // Invoices
  listInvoices: () => fetch(`${BASE}/invoices`).then(handleResponse),
  getInvoice: (id) => fetch(`${BASE}/invoices/${id}`).then(handleResponse),
  createInvoice: (payload) =>
    fetch(`${BASE}/invoices`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(handleResponse),
  invoicePdfUrl: (id) => `${BASE}/invoices/${id}/pdf`,

  // Receipts
  listReceipts: (invoiceId) =>
    fetch(`${BASE}/receipts${invoiceId ? `?invoice_id=${invoiceId}` : ''}`).then(handleResponse),
  createReceipt: (payload) =>
    fetch(`${BASE}/receipts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(handleResponse),

  // Reports
  getAgeingReport: (asOf) =>
    fetch(`${BASE}/reports/ageing${asOf ? `?as_of=${asOf}` : ''}`).then(handleResponse),
};
