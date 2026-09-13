import React, { useState } from "react";
import { api } from "../api";
import { formatMoney, todayISO } from "../utils/format";
import { Field, Message, SectionHeader, Status, inputCls } from "./ui";
export default function Receipts({
  invoices,
  receipts,
  balanceForInvoice,
  onChanged,
}) {
  const [form, setForm] = useState({
    invoice_id: "",
    amount: "",
    foreign_amount: "",
    exchange_rate_to_inr: "",
    firc_number: "",
    date: todayISO(),
    mode: "Bank Transfer",
    reference: "",
  });
  const [message, setMessage] = useState({});
  const issued = invoices.filter((i) => i.status === "issued");
  const selected = issued.find((i) => i.id === form.invoice_id);
  const exportInvoice = selected?.is_export;
  const realized =
    Number(form.foreign_amount || 0) * Number(form.exchange_rate_to_inr || 0);
  const save = async () => {
    try {
      const payload = {
        ...form,
        amount: exportInvoice ? realized : Number(form.amount),
        foreign_amount: exportInvoice ? Number(form.foreign_amount) : null,
        exchange_rate_to_inr: exportInvoice
          ? Number(form.exchange_rate_to_inr)
          : null,
        receipt_currency: exportInvoice ? selected.document_currency : "INR",
      };
      await api.createReceipt(payload);
      setForm({
        invoice_id: "",
        amount: "",
        foreign_amount: "",
        exchange_rate_to_inr: "",
        firc_number: "",
        date: todayISO(),
        mode: "Bank Transfer",
        reference: "",
      });
      await onChanged();
      setMessage({ success: "Receipt recorded." });
    } catch (e) {
      setMessage({ error: e.message });
    }
  };
  return (
    <div>
      <SectionHeader
        title="Receipts"
        subtitle="Record domestic or export receipts."
      />
      <div className="p-8 grid grid-cols-3 gap-6">
        <div className="card p-5 h-fit">
          <Message {...message} />
          <div className="flex flex-col gap-3">
            <Field label="Invoice">
              <select
                className={inputCls}
                value={form.invoice_id}
                onChange={(e) =>
                  setForm({ ...form, invoice_id: e.target.value })
                }
              >
                <option value="">Select invoice</option>
                {issued.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.invoice_no}
                  </option>
                ))}
              </select>
            </Field>
            {selected && (
              <div className="text-xs">
                Outstanding: ₹{formatMoney(balanceForInvoice(selected).balance)}
              </div>
            )}
            {exportInvoice ? (
              <>
                <Field label={`Foreign amount (${selected.document_currency})`}>
                  <input
                    type="number"
                    className={inputCls}
                    value={form.foreign_amount}
                    onChange={(e) =>
                      setForm({ ...form, foreign_amount: e.target.value })
                    }
                  />
                </Field>
                <Field label="Realized exchange rate to INR">
                  <input
                    type="number"
                    className={inputCls}
                    value={form.exchange_rate_to_inr}
                    onChange={(e) =>
                      setForm({ ...form, exchange_rate_to_inr: e.target.value })
                    }
                  />
                </Field>
                <Field label="FIRC number (optional)">
                  <input
                    className={inputCls}
                    value={form.firc_number}
                    onChange={(e) =>
                      setForm({ ...form, firc_number: e.target.value })
                    }
                  />
                </Field>
                <div className="text-sm">Realized INR: ₹{formatMoney(realized)}</div>
              </>
            ) : (
              <Field label="Amount (INR)">
                <input
                  type="number"
                  className={inputCls}
                  value={form.amount}
                  onChange={(e) => setForm({ ...form, amount: e.target.value })}
                />
              </Field>
            )}
            <Field label="Date">
              <input
                type="date"
                className={inputCls}
                value={form.date}
                onChange={(e) => setForm({ ...form, date: e.target.value })}
              />
            </Field>
            <Field label="Mode">
              <input
                className={inputCls}
                value={form.mode}
                onChange={(e) => setForm({ ...form, mode: e.target.value })}
              />
            </Field>
            <Field label="Reference">
              <input
                className={inputCls}
                value={form.reference}
                onChange={(e) =>
                  setForm({ ...form, reference: e.target.value })
                }
              />
            </Field>
            <button
              className="btn btn-primary px-3 py-2 text-sm"
              onClick={save}
            >
              Record receipt
            </button>
          </div>
        </div>
        <div className="col-span-2">
          <table className="text-sm">
            <thead>
              <tr>
                <th>Date</th>
                <th>Invoice</th>
                <th>Realized INR</th>
                <th>Applied to invoice</th>
                <th>Forex gain/loss</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {receipts.map((r) => (
                <tr className="border-b" key={r.id}>
                  <td>{r.date}</td>
                  <td>
                    {invoices.find((i) => i.id === r.invoice_id)?.invoice_no}
                  </td>
                  <td>₹{formatMoney(r.amount)}</td>
                  <td>₹{formatMoney(r.applied_amount_inr ?? r.amount)}</td>
                  <td>
                    {r.forex_gain_loss_inr == null
                      ? "—"
                      : `₹${formatMoney(r.forex_gain_loss_inr)}`}
                  </td>
                  <td>
                    <Status value={r.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
