import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client.js';

export default function InvoiceList() {
  const [invoices, setInvoices] = useState([]);
  const [customers, setCustomers] = useState({});

  useEffect(() => {
    api.listInvoices().then(setInvoices).catch(() => {});
    api.listCustomers().then((list) => {
      const map = {};
      list.forEach((c) => { map[c.id] = c; });
      setCustomers(map);
    }).catch(() => {});
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Invoices</h1>
        <Link to="/invoices/new" className="btn-primary">+ New Invoice</Link>
      </div>

      <div className="card overflow-x-auto">
        {invoices.length === 0 ? (
          <p className="text-sm text-gray-500">No invoices created yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="py-2">Invoice No.</th><th>Date</th><th>Customer</th>
                <th>Type</th><th>Total</th><th>Due Date</th><th>Status</th><th></th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => (
                <tr key={inv.id} className="border-b border-gray-100">
                  <td className="py-2 font-medium">{inv.invoice_no}</td>
                  <td>{inv.invoice_date}</td>
                  <td>{customers[inv.customer_id]?.name || '—'}</td>
                  <td>{inv.is_export ? `Export (${inv.currency_code})` : 'Domestic'}</td>
                  <td>
                    {inv.is_export
                      ? `${inv.currency_code} ${inv.total_foreign?.toFixed(2)}`
                      : `INR ${inv.total_inr.toFixed(2)}`}
                  </td>
                  <td>{inv.due_date}</td>
                  <td>{inv.status}</td>
                  <td>
                    <a href={api.invoicePdfUrl(inv.id)} target="_blank" rel="noreferrer" className="text-brand-dark underline text-xs">
                      PDF
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
