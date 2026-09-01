import React, { useEffect, useState } from 'react';
import { api } from '../api/client.js';

export default function LUTSetup() {
  const [luts, setLuts] = useState([]);
  const [form, setForm] = useState({ lut_arn: '', financial_year: '', valid_from: '', valid_to: '', is_active: true });
  const [message, setMessage] = useState('');

  const load = () => api.listLUT().then(setLuts).catch(() => {});
  useEffect(() => { load(); }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm({ ...form, [name]: type === 'checkbox' ? checked : value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    try {
      await api.createLUT(form);
      setMessage('LUT added successfully.');
      setForm({ lut_arn: '', financial_year: '', valid_from: '', valid_to: '', is_active: true });
      load();
    } catch (err) {
      setMessage(`Error: ${err.message}`);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">LUT Master</h1>
      <p className="text-sm text-gray-500">
        A Letter of Undertaking (LUT) is required to issue zero-rated export invoices. Add your LUT for each financial year here — the active one is picked up automatically when you create an export invoice.
      </p>

      <form onSubmit={handleSubmit} className="card space-y-4">
        <Field label="LUT ARN (Application Reference Number)" name="lut_arn" value={form.lut_arn} onChange={handleChange} required />
        <Field label="Financial Year" name="financial_year" value={form.financial_year} onChange={handleChange} placeholder="2026-27" required />
        <div className="grid grid-cols-2 gap-4">
          <Field label="Valid From" name="valid_from" type="date" value={form.valid_from} onChange={handleChange} required />
          <Field label="Valid To" name="valid_to" type="date" value={form.valid_to} onChange={handleChange} required />
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" name="is_active" checked={form.is_active} onChange={handleChange} />
          Mark as active LUT (used for new export invoices)
        </label>
        <button type="submit" className="btn-primary">Add LUT</button>
        {message && <p className={`text-sm ${message.startsWith('Error') ? 'text-red-600' : 'text-green-700'}`}>{message}</p>}
      </form>

      <div className="card">
        <h2 className="text-sm font-semibold text-brand-dark uppercase tracking-wide mb-3">Existing LUTs</h2>
        {luts.length === 0 ? (
          <p className="text-sm text-gray-500">No LUT added yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="py-2">ARN</th><th>FY</th><th>Valid From</th><th>Valid To</th><th>Status</th>
              </tr>
            </thead>
            <tbody>
              {luts.map((l) => (
                <tr key={l.id} className="border-b border-gray-100">
                  <td className="py-2">{l.lut_arn}</td>
                  <td>{l.financial_year}</td>
                  <td>{l.valid_from}</td>
                  <td>{l.valid_to}</td>
                  <td>{l.is_active ? <span className="text-green-700">Active</span> : 'Inactive'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function Field({ label, name, value, onChange, required, type = 'text', placeholder }) {
  return (
    <div>
      <label className="label-text">{label}{required && <span className="text-red-500"> *</span>}</label>
      <input type={type} name={name} value={value || ''} onChange={onChange} required={required} placeholder={placeholder} className="input-field" />
    </div>
  );
}
