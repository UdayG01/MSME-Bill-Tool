import React, { useEffect, useState } from "react";
import { api } from "../api";
import { Field, Message, SectionHeader, inputCls, inputStyle } from "./ui";

const COMPANY_FIELDS = [
  ["company_name", "Company Name"],
  ["address", "Address"],
  ["gstin", "GSTIN"],
  ["cin", "CIN"],
  ["udyam_number", "Udyam Registration Number"],
  ["state_code", "State Code"],
  ["email", "Email"],
  ["phone", "Phone"],
  ["invoice_prefix", "Invoice Prefix"],
  ["bank_name", "Domestic Bank Name"],
  ["bank_account", "Domestic Account"],
  ["bank_ifsc", "Domestic IFSC"],
  ["upi_id", "UPI ID"],
  ["intl_bank_name", "International Bank / Branch"],
  ["intl_bank_account", "International Account"],
  ["intl_swift_code", "SWIFT Code"],
  ["intl_bank_address", "International Bank Address"],
];
const MEDIA_RULES = {
  logo: {
    label: "Logo",
    maxBytes: 2 * 1024 * 1024,
    hint: "PNG or JPEG, up to 2 MB. A clear horizontal image works best; transparent PNG is recommended.",
  },
  signature: {
    label: "Signature",
    maxBytes: 1024 * 1024,
    hint: "PNG or JPEG, up to 1 MB. Use a tightly cropped image; transparent PNG is recommended.",
  },
};

export default function CompanySetup({ company, onSaved }) {
  const [form, setForm] = useState(company);
  const [message, setMessage] = useState({});
  const [uploading, setUploading] = useState("");
  useEffect(() => {
    setForm(company);
  }, [company]);
  const save = async () => {
    try {
      await api.updateCompany(form);
      await onSaved();
      setMessage({ success: "Company details saved." });
    } catch (e) {
      setMessage({ error: e.message });
    }
  };
  const upload = async (purpose, file) => {
    if (!file) return;
    const rule = MEDIA_RULES[purpose];
    if (!["image/png", "image/jpeg"].includes(file.type)) {
      setMessage({ error: `${rule.label} upload failed: choose a PNG or JPEG image.` });
      return;
    }
    if (file.size > rule.maxBytes) {
      setMessage({
        error: `${rule.label} upload failed: the file must be ${rule.maxBytes / 1024 / 1024} MB or smaller.`,
      });
      return;
    }
    setUploading(purpose);
    setMessage({});
    try {
      const asset = await api.uploadCompanyMedia(purpose, file);
      setForm((current) => ({
        ...current,
        [`${purpose}_asset_id`]: asset.id,
      }));
      await onSaved();
      setMessage({ success: `${rule.label} uploaded successfully.` });
    } catch (e) {
      setMessage({ error: `${rule.label} upload failed: ${e.message}` });
    } finally {
      setUploading("");
    }
  };
  const remove = async (purpose) => {
    const label = purpose === "logo" ? "logo" : "signature";
    if (!window.confirm(`Remove the current company ${label}?`)) return;
    try {
      await api.removeCompanyMedia(purpose);
      setForm((current) => ({
        ...current,
        [`${purpose}_asset_id`]: null,
      }));
      await onSaved();
      setMessage({ success: `Company ${label} removed.` });
    } catch (e) {
      setMessage({ error: e.message });
    }
  };
  const previewInvoice = async () => {
    try {
      await api.previewCompanyInvoice(form);
    } catch (e) {
      setMessage({ error: e.message });
    }
  };
  return (
    <div>
      <SectionHeader
        title="Company Setup"
        subtitle="These details are snapshotted when an invoice is issued."
      />
      <div className="p-8 max-w-3xl">
        <Message {...message} />
        <div className="grid grid-cols-2 gap-4">
          {COMPANY_FIELDS.map(([key, label]) => (
            <Field key={key} label={label}>
              {key === "address" || key === "intl_bank_address" ? (
                <textarea
                  className={inputCls}
                  style={inputStyle}
                  value={form[key] || ""}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                />
              ) : (
                <input
                  className={inputCls}
                  style={inputStyle}
                  value={form[key] || ""}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                />
              )}
            </Field>
          ))}
        </div>
        <div className="grid grid-cols-2 gap-4 mt-5">
          {[
            ["logo", "Company logo"],
            ["signature", "Authorized signature"],
          ].map(([purpose, label]) => {
            const assetId = form[`${purpose}_asset_id`];
            return (
              <div className="card p-4" key={purpose}>
                <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 mb-2">
                  {label}
                </div>
                <div className="h-28 rounded border border-slate-200 bg-slate-50 flex items-center justify-center p-3 mb-3">
                  {assetId ? (
                    <img
                      src={api.companyMediaUrl(assetId)}
                      alt={`Current ${label.toLowerCase()}`}
                      className="max-w-full max-h-full object-contain"
                      onError={() => setMessage({
                        error: `The stored ${purpose} could not be loaded. Upload the image again.`,
                      })}
                    />
                  ) : (
                    <span className="text-sm text-slate-500">
                      No {purpose} uploaded
                    </span>
                  )}
                </div>
                <input
                  className="block w-full text-sm"
                  type="file"
                  accept="image/png,image/jpeg"
                  disabled={Boolean(uploading)}
                  onChange={(e) => {
                    const input = e.currentTarget;
                    upload(purpose, input.files[0]).finally(() => {
                      input.value = "";
                    });
                  }}
                />
                <p className="text-xs text-slate-500 mt-2">
                  {MEDIA_RULES[purpose].hint}
                </p>
                {uploading === purpose && (
                  <p className="text-sm text-slate-600 mt-2">Uploading…</p>
                )}
                {assetId && (
                  <button
                    type="button"
                    className="text-sm text-red-600 underline mt-3"
                    onClick={() => remove(purpose)}
                  >
                    Remove {purpose}
                  </button>
                )}
              </div>
            );
          })}
        </div>
        <div className="flex gap-3 mt-5">
          <button
            className="btn btn-primary px-4 py-2 text-sm"
            onClick={save}
          >
            Save company
          </button>
          <button
            className="btn btn-outline px-4 py-2 text-sm"
            onClick={previewInvoice}
          >
            Preview sample invoice
          </button>
        </div>
      </div>
    </div>
  );
}
