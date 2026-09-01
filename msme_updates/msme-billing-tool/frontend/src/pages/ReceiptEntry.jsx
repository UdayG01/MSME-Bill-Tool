import React, { useEffect, useState } from 'react';
import { api } from '../api/client.js';

export default function ReceiptEntry() {
  const [invoices, setInvoices] = useState([]);
  const [invoiceId, setInvoiceId] = useState('');
  const [receiptDate, setReceiptDate] = useState(new Date().toISOString().slice(0, 10));
  const [amountInr, setAmountInr] = useState('');
  const [foreignAmount, setForeignAmount] = useState('');
  const [exchangeRateAtReceipt, setExchangeRateAtReceipt] = useState('');
  const [fircNumber, setFircNumber] = useState('');
  const [notes, setNotes] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => { api.listInvoices().then(setInvoices).catch(() => {}); }, []);

  const selectedInvoice = invoices.find((inv) => inv.id === parseInt(invoiceId, 10));
  const isExport = selectedInvoice?.is_export;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); setResult(null);
    if (!invoiceId) { setError('Select an invoice.'); return; }
    setSubmitting(true);
    try {
      const payload = {
        invoice_id: parseInt(invoiceId, 10),
        receipt_date: receiptDate,
        amount_inr: isExport
          ? parseFloat(foreignAmount) * parseFloat(exchangeRateAtReceipt)
          : parseFloat(amountInr),
        foreign_amount_received: isExport ? parseFloat(foreignAmount) : null,
        exchange_rate_at_receipt: isExport ? parseFloat(exchangeRateAtReceipt) : null,
        firc_number: isExport ? (fircNumber || null) : null,
        notes: notes || null,
      };
      const receipt = await api.createReceipt(payload);
      setResult(receipt);
      setAmountInr(''); setForeignAmount(''); setExchangeRateAtReceipt(''); setFircNumber(''); setNotes('');
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Receipt Entry</h1>

      <form onSubmit={handleSubmit} className="card space-y-4">
        <div>
          <label className="label-text">Invoice<span className="text-red-500"> *</span></label>
          <select value={invoiceId} onChange={(e) => setInvoiceId(e.target.value)} required className="input-field">
            <option value="">Select an invoice...</option>
            {invoices.map((inv) => (
              <option key={inv.id} value={inv.id}>
                {inv.invoice_no} — {inv.is_export ? `${inv.currency_code} ${inv.total_foreign?.toFixed(2)}` : `INR ${inv.total_inr.toFixed(2)}`}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="label-text">Receipt Date<span className="text-red-500"> *</span></label>
          <input type="date" value={receiptDate} onChange={(e) => setReceiptDate(e.target.value)} required className="input-field" />
        </div>

        {isExport ? (
          <>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label-text">Foreign Amount Received ({selectedInvoice.currency_code})<span className="text-red-500"> *</span></label>
                <input type="number" step="0.01" value={foreignAmount} onChange={(e) => setForeignAmount(e.target.value)} required className="input-field" />
              </div>
              <div>
                <label className="label-text">Exchange Rate at Receipt<span className="text-red-500"> *</span></label>
                <input type="number" step="0.0001" value={exchangeRateAtReceipt} onChange={(e) => setExchangeRateAtReceipt(e.target.value)} required className="input-field" />
              </div>
            </div>
            <div>
              <label className="label-text">FIRC Number (Foreign Inward Remittance Certificate)</label>
              <input type="text" value={fircNumber} onChange={(e) => setFircNumber(e.target.value)} className="input-field" />
            </div>
            {foreignAmount && exchangeRateAtReceipt && (
              <p className="text-xs text-gray-500">
                Realized INR value: {(parseFloat(foreignAmount) * parseFloat(exchangeRateAtReceipt)).toFixed(2)}
              </p>
            )}
          </>
        ) : (
          <div>
            <label className="label-text">Amount (INR)<span className="text-red-500"> *</span></label>
            <input type="number" step="0.01" value={amountInr} onChange={(e) => setAmountInr(e.target.value)} required className="input-field" />
          </div>
        )}

        <div>
          <label className="label-text">Notes</label>
          <input type="text" value={notes} onChange={(e) => setNotes(e.target.value)} className="input-field" />
        </div>

        <button type="submit" disabled={submitting} className="btn-primary">
          {submitting ? 'Recording...' : 'Record Receipt'}
        </button>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </form>

      {result && (
        <div className="card bg-green-50 border-green-200">
          <p className="text-green-800 font-medium">Receipt recorded successfully.</p>
          {result.forex_gain_loss !== null && result.forex_gain_loss !== undefined && (
            <p className="text-sm mt-2">
              Forex {result.forex_gain_loss >= 0 ? 'Gain' : 'Loss'}: INR {Math.abs(result.forex_gain_loss).toFixed(2)}
              <span className="text-gray-500"> — the difference between the exchange rate at invoicing and at receipt.</span>
            </p>
          )}
        </div>
      )}
    </div>
  );
}
