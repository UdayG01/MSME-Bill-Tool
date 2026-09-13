import React, { useEffect, useState } from "react";
import { api } from "../api";
import { inputCls, inputStyle } from "./ui";

export default function BillingSettings() {
  const [form, setForm] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  useEffect(() => {
    api
      .getBillingSettings()
      .then(setForm)
      .catch((e) => setError(e.message));
  }, []);
  if (!form) return <div className="p-8">Loading…</div>;
  const save = async () => {
    try {
      await api.updateBillingSettings(form);
      setSuccess("Billing settings saved.");
      setError("");
    } catch (e) {
      setError(e.message);
    }
  };
  return (
    <div>
      <div className="px-8 pt-8 pb-5 border-b">
        <h1 className="serif text-2xl">Billing Settings</h1>
        <p className="text-sm text-slate-500">
          Configure export invoices, terms and invoice banner.
        </p>
      </div>
      <div className="p-8 max-w-3xl">
        <div className="flex flex-col gap-4">
          {error && <div className="text-red-700">{error}</div>}
          {success && <div className="text-green-700">{success}</div>}
          <label>
            <input
              type="checkbox"
              checked={form.allow_export_invoicing}
              onChange={(e) =>
                setForm({ ...form, allow_export_invoicing: e.target.checked })
              }
            />{" "}
            Enable export invoicing
          </label>
          <label>
            <input
              type="checkbox"
              checked={form.require_valid_lut_for_export}
              disabled
            />{" "}
            A valid active LUT is required for export invoices
          </label>
          <label>
            Terms &amp; Notes (one bullet per line)
            <textarea
              rows="5"
              className={inputCls}
              style={inputStyle}
              value={form.terms_notes}
              onChange={(e) =>
                setForm({ ...form, terms_notes: e.target.value })
              }
            />
          </label>
          <label>
            Campaign tagline
            <input
              className={inputCls}
              style={inputStyle}
              value={form.tagline}
              onChange={(e) => setForm({ ...form, tagline: e.target.value })}
            />
          </label>
          <button
            className="btn btn-primary px-4 py-2 text-sm w-fit"
            onClick={save}
          >
            Save settings
          </button>
        </div>
      </div>
    </div>
  );
}
