import React, { useEffect, useState } from "react";
import { api } from "../api";
import { Field, Message, SectionHeader, inputCls } from "./ui";
export default function LutCertificates() {
  const [rows, setRows] = useState([]);
  const [form, setForm] = useState({
    arn: "",
    financial_year: "",
    valid_from: "",
    valid_to: "",
  });
  const [message, setMessage] = useState({});
  const load = () =>
    api
      .listLutCertificates()
      .then(setRows)
      .catch((e) => setMessage({ error: e.message }));
  useEffect(() => {
    load();
  }, []);
  const save = async () => {
    try {
      await api.createLutCertificate(form);
      setForm({ arn: "", financial_year: "", valid_from: "", valid_to: "" });
      load();
    } catch (e) {
      setMessage({ error: e.message });
    }
  };
  return (
    <div>
      <SectionHeader
        title="LUT Certificates"
        subtitle="Create and activate the certificate used for export invoices."
      />
      <div className="p-8">
        <Message {...message} />
        <div className="card p-4 grid grid-cols-4 gap-3">
          <Field label="LUT ARN">
            <input
              className={inputCls}
              value={form.arn}
              onChange={(e) => setForm({ ...form, arn: e.target.value })}
            />
          </Field>
          <Field label="Financial Year">
            <input
              className={inputCls}
              value={form.financial_year}
              onChange={(e) =>
                setForm({ ...form, financial_year: e.target.value })
              }
            />
          </Field>
          <Field label="Valid From">
            <input
              type="date"
              className={inputCls}
              value={form.valid_from}
              onChange={(e) => setForm({ ...form, valid_from: e.target.value })}
            />
          </Field>
          <Field label="Valid To">
            <input
              type="date"
              className={inputCls}
              value={form.valid_to}
              onChange={(e) => setForm({ ...form, valid_to: e.target.value })}
            />
          </Field>
          <button
            className="btn btn-primary px-3 py-2 text-sm w-fit"
            onClick={save}
          >
            Add certificate
          </button>
        </div>
        <table className="text-sm mt-6">
          <thead>
            <tr>
              <th>ARN</th>
              <th>FY</th>
              <th>Validity</th>
              <th>Status</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr className="border-b" key={row.id}>
                <td>{row.arn}</td>
                <td>{row.financial_year}</td>
                <td>
                  {row.valid_from} – {row.valid_to}
                </td>
                <td>{row.status}</td>
                <td>
                  {row.status !== "active" && (
                    <button
                      className="underline mr-3"
                      onClick={async () => {
                        await api.activateLutCertificate(row.id);
                        load();
                      }}
                    >
                      Activate
                    </button>
                  )}
                  {row.status !== "archived" && (
                    <button
                      className="underline text-red-600"
                      onClick={async () => {
                        await api.archiveLutCertificate(row.id);
                        load();
                      }}
                    >
                      Archive
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
