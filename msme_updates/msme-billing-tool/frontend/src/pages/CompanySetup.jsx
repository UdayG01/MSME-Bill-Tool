import React, { useEffect, useState } from 'react';
import { api } from '../api/client.js';

const emptyForm = {
  name: '', address: '', gstin: '', cin: '', udyam_number: '',
  email: '', mobile: '', tagline: '', terms_notes: '',
  bank_name: '', bank_account: '', bank_ifsc: '', upi_id: '',
  intl_bank_name: '', intl_bank_account: '', intl_swift_code: '', intl_bank_address: '',
};

export default function CompanySetup() {
  const [form, setForm] = useState(emptyForm);
  const [company, setCompany] = useState(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [logoFile, setLogoFile] = useState(null);
  const [sigFile, setSigFile] = useState(null);

  useEffect(() => {
    api.getCompany()
      .then((data) => {
        setCompany(data);
        setForm({ ...emptyForm, ...data });
      })
      .catch(() => {}); // no company yet — that's fine, form starts empty
  }, []);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage('');
    try {
      const saved = await api.saveCompany(form);
      setCompany(saved);
      if (logoFile) await api.uploadLogo(logoFile);
      if (sigFile) await api.uploadSignature(sigFile);
      const refreshed = await api.getCompany();
      setCompany(refreshed);
      setMessage('Company details saved successfully.');
    } catch (err) {
      setMessage(`Error: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Company Master</h1>
      <p className="text-sm text-gray-500">
        These details print on every invoice — domestic and export. Set this up once; it applies to all future invoices automatically.
      </p>

      <form onSubmit={handleSave} className="card space-y-5">
        <Section title="Basic Details">
          <Field label="Company Name" name="name" value={form.name} onChange={handleChange} required />
          <Field label="Address" name="address" value={form.address} onChange={handleChange} textarea required />
          <div className="grid grid-cols-2 gap-4">
            <Field label="GSTIN" name="gstin" value={form.gstin} onChange={handleChange} required />
            <Field label="CIN" name="cin" value={form.cin} onChange={handleChange} />
          </div>
          <Field label="Udyam Registration Number" name="udyam_number" value={form.udyam_number} onChange={handleChange} placeholder="UDYAM-DL-10-0090884" />
          <div className="grid grid-cols-2 gap-4">
            <Field label="Contact Email" name="email" value={form.email} onChange={handleChange} />
            <Field label="Mobile" name="mobile" value={form.mobile} onChange={handleChange} />
          </div>
        </Section>

        <Section title="Branding">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label-text">Company Logo</label>
              <input type="file" accept="image/*" onChange={(e) => setLogoFile(e.target.files[0])} className="text-sm" />
              {company?.logo_path && <p className="text-xs text-green-700 mt-1">Logo currently on file.</p>}
            </div>
            <div>
              <label className="label-text">Authorized Signature</label>
              <input type="file" accept="image/*" onChange={(e) => setSigFile(e.target.files[0])} className="text-sm" />
              {company?.signature_path && <p className="text-xs text-green-700 mt-1">Signature currently on file.</p>}
            </div>
          </div>
          <Field label="Campaign Tagline" name="tagline" value={form.tagline} onChange={handleChange}
                 placeholder="A single punchline shown on every invoice — update it whenever you run a new campaign." />
          <Field label="Terms & Notes (one per line)" name="terms_notes" value={form.terms_notes} onChange={handleChange} textarea
                 placeholder="Leave blank to use sensible defaults, or enter your own — one line per bullet point." />
        </Section>

        <Section title="Domestic Bank Details">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Bank Name" name="bank_name" value={form.bank_name} onChange={handleChange} />
            <Field label="Account Number" name="bank_account" value={form.bank_account} onChange={handleChange} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Field label="IFSC Code" name="bank_ifsc" value={form.bank_ifsc} onChange={handleChange} />
            <Field label="UPI ID" name="upi_id" value={form.upi_id} onChange={handleChange} placeholder="yourname@bank" />
          </div>
        </Section>

        <Section title="International Bank Details (for Export Invoices)">
          <Field label="Bank Name & Branch" name="intl_bank_name" value={form.intl_bank_name} onChange={handleChange} />
          <div className="grid grid-cols-2 gap-4">
            <Field label="Account Number" name="intl_bank_account" value={form.intl_bank_account} onChange={handleChange} />
            <Field label="SWIFT Code" name="intl_swift_code" value={form.intl_swift_code} onChange={handleChange} />
          </div>
          <Field label="Bank Address" name="intl_bank_address" value={form.intl_bank_address} onChange={handleChange} textarea />
        </Section>

        <div className="flex items-center gap-4 pt-2">
          <button type="submit" disabled={saving} className="btn-primary">
            {saving ? 'Saving...' : 'Save Company Details'}
          </button>
          {message && (
            <span className={`text-sm ${message.startsWith('Error') ? 'text-red-600' : 'text-green-700'}`}>{message}</span>
          )}
        </div>
      </form>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div className="space-y-3">
      <h2 className="text-sm font-semibold text-brand-dark uppercase tracking-wide border-b border-gray-200 pb-2">{title}</h2>
      {children}
    </div>
  );
}

function Field({ label, name, value, onChange, required, textarea, placeholder }) {
  return (
    <div>
      <label className="label-text">{label}{required && <span className="text-red-500"> *</span>}</label>
      {textarea ? (
        <textarea name={name} value={value || ''} onChange={onChange} required={required} placeholder={placeholder}
                   className="input-field" rows={2} />
      ) : (
        <input type="text" name={name} value={value || ''} onChange={onChange} required={required} placeholder={placeholder}
               className="input-field" />
      )}
    </div>
  );
}
