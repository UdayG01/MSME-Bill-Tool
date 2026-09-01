import React, { useEffect, useState } from 'react';
import { api } from '../api/client.js';

const CURRENCIES = ['USD', 'EUR', 'GBP', 'AED', 'SGD'];
const emptyItem = { description: '', note: '', hsn_sac: '', qty: 1, rate: '' };

export default function CreateInvoice() {
  const [customers, setCustomers] = useState([]);
  const [customerId, setCustomerId] = useState('');
  const [invoiceDate, setInvoiceDate] = useState(new Date().toISOString().slice(0, 10));
  const [orderNo, setOrderNo] = useState('');
  const [orderDate, setOrderDate] = useState('');
  const [items, setItems] = useState([{ ...emptyItem }]);
  const [gstRate, setGstRate] = useState(18);
  const [currencyCode, setCurrencyCode] = useState('USD');
  const [exchangeRate, setExchangeRate] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => { api.listCustomers().then(setCustomers).catch(() => {}); }, []);

  const selectedCustomer = customers.find((c) => c.id === parseInt(customerId, 10));
  const isExport = selectedCustomer?.is_foreign;

  const updateItem = (idx, field, value) => {
    const updated = [...items];
    updated[idx] = { ...updated[idx], [field]: value };
    setItems(updated);
  };
  const addItem = () => setItems([...items, { ...emptyItem }]);
  const removeItem = (idx) => setItems(items.filter((_, i) => i !== idx));

  const subtotal = items.reduce((sum, it) => sum + (parseFloat(it.qty) || 0) * (parseFloat(it.rate) || 0), 0);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setResult(null);
    if (!customerId) { setError('Select a customer.'); return; }
    if (isExport && (!exchangeRate || parseFloat(exchangeRate) <= 0)) {
      setError('Exchange rate is required for export invoices.');
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        customer_id: parseInt(customerId, 10),
        invoice_date: invoiceDate,
        order_no: orderNo || null,
        order_date: orderDate || null,
        items: items.map((it) => ({
          description: it.description, note: it.note || null, hsn_sac: it.hsn_sac,
          qty: parseFloat(it.qty), rate: parseFloat(it.rate),
        })),
        gst_rate: isExport ? 0 : parseFloat(gstRate),
        currency_code: isExport ? currencyCode : 'INR',
        exchange_rate: isExport ? parseFloat(exchangeRate) : null,
      };
      const invoice = await api.createInvoice(payload);
      setResult(invoice);
      setItems([{ ...emptyItem }]);
      setOrderNo(''); setOrderDate('');
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Create Invoice</h1>

      <form onSubmit={handleSubmit} className="card space-y-5">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label-text">Customer<span className="text-red-500"> *</span></label>
            <select value={customerId} onChange={(e) => setCustomerId(e.target.value)} required className="input-field">
              <option value="">Select a customer...</option>
              {customers.map((c) => (
                <option key={c.id} value={c.id}>{c.name} {c.is_foreign ? '(Export)' : ''}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label-text">Invoice Date<span className="text-red-500"> *</span></label>
            <input type="date" value={invoiceDate} onChange={(e) => setInvoiceDate(e.target.value)} required className="input-field" />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label-text">Order Number</label>
            <input type="text" value={orderNo} onChange={(e) => setOrderNo(e.target.value)} className="input-field" />
          </div>
          <div>
            <label className="label-text">Order Date</label>
            <input type="date" value={orderDate} onChange={(e) => setOrderDate(e.target.value)} className="input-field" />
          </div>
        </div>

        {selectedCustomer && (
          <div className="bg-brand-light rounded-md p-3 text-sm text-gray-700">
            {isExport ? (
              <span>Export customer — invoice will be zero-rated under LUT, printed in foreign currency. Payment terms: {selectedCustomer.payment_terms_days} days.</span>
            ) : (
              <span>Domestic customer ({selectedCustomer.gstin}) — GST will be auto-calculated as IGST or CGST+SGST based on place of supply. Payment terms: {selectedCustomer.payment_terms_days} days.</span>
            )}
          </div>
        )}

        {isExport && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label-text">Invoice Currency<span className="text-red-500"> *</span></label>
              <select value={currencyCode} onChange={(e) => setCurrencyCode(e.target.value)} className="input-field">
                {CURRENCIES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="label-text">Exchange Rate (1 {currencyCode} = ? INR)<span className="text-red-500"> *</span></label>
              <input type="number" step="0.0001" value={exchangeRate} onChange={(e) => setExchangeRate(e.target.value)}
                     className="input-field" placeholder="e.g. 83.50" />
              <p className="text-xs text-gray-500 mt-1">Manually entered — used only for internal GST/MIS records, not printed on the invoice.</p>
            </div>
          </div>
        )}

        {!isExport && (
          <div className="w-40">
            <label className="label-text">GST Rate (%)</label>
            <input type="number" step="0.01" value={gstRate} onChange={(e) => setGstRate(e.target.value)} className="input-field" />
          </div>
        )}

        <div>
          <label className="label-text mb-2">Line Items<span className="text-red-500"> *</span></label>
          <div className="space-y-3">
            {items.map((item, idx) => (
              <div key={idx} className="border border-gray-200 rounded-md p-3 space-y-2">
                <div className="grid grid-cols-12 gap-2">
                  <input type="text" placeholder="Description" value={item.description}
                         onChange={(e) => updateItem(idx, 'description', e.target.value)}
                         className="input-field col-span-5" required />
                  <input type="text" placeholder="HSN/SAC" value={item.hsn_sac}
                         onChange={(e) => updateItem(idx, 'hsn_sac', e.target.value)}
                         className="input-field col-span-2" required />
                  <input type="number" step="0.01" placeholder="Qty" value={item.qty}
                         onChange={(e) => updateItem(idx, 'qty', e.target.value)}
                         className="input-field col-span-1" required />
                  <input type="number" step="0.01" placeholder="Rate" value={item.rate}
                         onChange={(e) => updateItem(idx, 'rate', e.target.value)}
                         className="input-field col-span-2" required />
                  <div className="col-span-2 flex items-center justify-end">
                    <span className="text-sm text-gray-600 mr-2">
                      {((parseFloat(item.qty) || 0) * (parseFloat(item.rate) || 0)).toFixed(2)}
                    </span>
                    {items.length > 1 && (
                      <button type="button" onClick={() => removeItem(idx)} className="text-red-500 text-xs">Remove</button>
                    )}
                  </div>
                </div>
                <input type="text" placeholder="Detail note (optional, appears under description)" value={item.note}
                       onChange={(e) => updateItem(idx, 'note', e.target.value)} className="input-field text-sm" />
              </div>
            ))}
          </div>
          <button type="button" onClick={addItem} className="btn-secondary mt-2 text-xs">+ Add Line Item</button>
        </div>

        <div className="text-right text-sm text-gray-700">
          Subtotal: <span className="font-semibold">{subtotal.toFixed(2)} {isExport ? currencyCode : 'INR'}</span>
        </div>

        <button type="submit" disabled={submitting} className="btn-primary">
          {submitting ? 'Creating Invoice...' : 'Create Invoice'}
        </button>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </form>

      {result && (
        <div className="card bg-green-50 border-green-200">
          <p className="text-green-800 font-medium">Invoice {result.invoice_no} created successfully.</p>
          <a href={api.invoicePdfUrl(result.id)} target="_blank" rel="noreferrer" className="btn-primary inline-block mt-3">
            Download / View PDF
          </a>
        </div>
      )}
    </div>
  );
}
