import React, { useEffect, useState } from 'react';
import { api } from '../api/client.js';

const emptyForm = { name: '', address: '', country: 'India', is_foreign: false, gstin: '', payment_terms_days: 30 };

export default function Customers() {
  const [customers, setCustomers] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [message, setMessage] = useState('');

  const load = () => api.listCustomers().then(setCustomers).catch(() => {});
  useEffect(() => { load(); }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    let updated = { ...form, [name]: type === 'checkbox' ? checked : value };
    if (name === 'is_foreign' && checked) {
      updated.gstin = '';
      updated.country = updated.country === 'India' ? '' : updated.country;
    }
    if (name === 'is_foreign' && !checked) {
      updated.country = 'India';
    }
    setForm(updated);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    try {
      const payload = { ...form, payment_terms_days: parseInt(form.payment_terms_days, 10) };
      await api.createCustomer(payload);
      setMessage('Customer added successfully.');
      setForm(emptyForm);
      load();
    } catch (err) {
      setMessage(`Error: ${err.message}`);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Customer Master</h1>

      <form onSubmit={handleSubmit} className="card space-y-4">
        <div>
          <label className="label-text">Customer Name<span className="text-red-500"> *</span></label>
          <input type="text" name="name" value={form.name} onChange={handleChange} required className="input-field" />
        </div>
        <div>
          <label className="label-text">Address<span className="text-red-500"> *</span></label>
          <textarea name="address" value={form.address} onChange={handleChange} required className="input-field" rows={2} />
        </div>

        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" name="is_foreign" checked={form.is_foreign} onChange={handleChange} />
          This is a foreign (export) customer
        </label>

        {form.is_foreign ? (
          <div>
            <label className="label-text">Country<span className="text-red-500"> *</span></label>
            <input type="text" name="country" value={form.country} onChange={handleChange} required className="input-field" />
            <p className="text-xs text-gray-500 mt-1">GSTIN is not applicable for foreign customers and will be left blank.</p>
          </div>
        ) : (
          <div>
            <label className="label-text">GSTIN<span className="text-red-500"> *</span></label>
            <input type="text" name="gstin" value={form.gstin} onChange={handleChange} required className="input-field" placeholder="e.g. 09AALCG2086N1ZY" />
          </div>
        )}

        <div>
          <label className="label-text">Payment Terms (days)<span className="text-red-500"> *</span></label>
          <input type="number" name="payment_terms_days" min="1" value={form.payment_terms_days} onChange={handleChange} required className="input-field" />
          <p className="text-xs text-gray-500 mt-1">Mandatory — the invoice due date is calculated automatically from this.</p>
        </div>

        <button type="submit" className="btn-primary">Add Customer</button>
        {message && <p className={`text-sm ${message.startsWith('Error') ? 'text-red-600' : 'text-green-700'}`}>{message}</p>}
      </form>

      <div className="card">
        <h2 className="text-sm font-semibold text-brand-dark uppercase tracking-wide mb-3">Existing Customers</h2>
        {customers.length === 0 ? (
          <p className="text-sm text-gray-500">No customers added yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="py-2">Name</th><th>Type</th><th>GSTIN / Country</th><th>Payment Terms</th>
              </tr>
            </thead>
            <tbody>
              {customers.map((c) => (
                <tr key={c.id} className="border-b border-gray-100">
                  <td className="py-2">{c.name}</td>
                  <td>{c.is_foreign ? 'Export' : 'Domestic'}</td>
                  <td>{c.is_foreign ? c.country : c.gstin}</td>
                  <td>{c.payment_terms_days} days</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
