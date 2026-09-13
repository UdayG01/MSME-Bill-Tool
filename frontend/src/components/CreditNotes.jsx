import React, { useState } from "react";
import { api } from "../api";
import { formatMoney, todayISO } from "../utils/format";
import { Field, Message, SectionHeader, Status, inputCls } from "./ui";
const uid = () => Math.random().toString(36).slice(2);
const blank = () => ({
  id: uid(),
  description: "",
  category: "",
  qty: 1,
  rate: 0,
});
export default function CreditNotes({
  invoices,
  creditNotes,
  balanceForInvoice,
  onChanged,
}) {
  const [invoiceId, setInvoiceId] = useState("");
  const [date, setDate] = useState(todayISO());
  const [reason, setReason] = useState("");
  const [items, setItems] = useState([blank()]);
  const [message, setMessage] = useState({});
  const issued = invoices.filter(
    (i) => i.status === "issued" && balanceForInvoice(i).balance > 0,
  );
  const update = (id, key, value) =>
    setItems(items.map((i) => (i.id === id ? { ...i, [key]: value } : i)));
  const save = async () => {
    try {
      await api.createCreditNote(invoiceId, {
        date,
        reason,
        items: items.map(({ description, category, qty, rate }) => ({
          description,
          category,
          qty: Number(qty),
          rate: Number(rate),
        })),
      });
      setInvoiceId("");
      setReason("");
      setItems([blank()]);
      await onChanged();
      setMessage({ success: "Credit note created." });
    } catch (e) {
      setMessage({ error: e.message });
    }
  };
  return (
    <div>
      <SectionHeader
        title="Credit Notes"
        subtitle="Reduce issued invoices without rewriting history."
      />
      <div className="p-8">
        <Message {...message} />
        <div className="card p-5 mb-6">
          <div className="grid grid-cols-3 gap-4">
            <Field label="Invoice">
              <select
                className={inputCls}
                value={invoiceId}
                onChange={(e) => setInvoiceId(e.target.value)}
              >
                <option value="">Select invoice</option>
                {issued.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.invoice_no}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Date">
              <input
                type="date"
                className={inputCls}
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </Field>
            <Field label="Reason">
              <input
                className={inputCls}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
            </Field>
          </div>
          {items.map((item) => (
            <div className="grid grid-cols-5 gap-2 mt-3" key={item.id}>
              <input
                placeholder="Description"
                className={inputCls}
                value={item.description}
                onChange={(e) => update(item.id, "description", e.target.value)}
              />
              <input
                placeholder="Category"
                className={inputCls}
                value={item.category}
                onChange={(e) => update(item.id, "category", e.target.value)}
              />
              <input
                type="number"
                className={inputCls}
                value={item.qty}
                onChange={(e) => update(item.id, "qty", e.target.value)}
              />
              <input
                type="number"
                className={inputCls}
                value={item.rate}
                onChange={(e) => update(item.id, "rate", e.target.value)}
              />
              <button
                onClick={() => setItems(items.filter((i) => i.id !== item.id))}
              >
                ×
              </button>
            </div>
          ))}
          <button
            className="btn btn-outline px-3 py-2 text-sm mt-3"
            onClick={() => setItems([...items, blank()])}
          >
            Add line
          </button>
          <button
            className="btn btn-primary px-3 py-2 text-sm mt-3 ml-3"
            disabled={!invoiceId}
            onClick={save}
          >
            Create credit note
          </button>
        </div>
        <table className="text-sm">
          <thead>
            <tr>
              <th>Date</th>
              <th>Credit note</th>
              <th>Invoice</th>
              <th>Total</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {creditNotes.map((n) => (
              <tr className="border-b" key={n.id}>
                <td>{n.date}</td>
                <td>{n.credit_note_no}</td>
                <td>
                  {invoices.find((i) => i.id === n.invoice_id)?.invoice_no}
                </td>
                <td>₹{formatMoney(n.total)}</td>
                <td>
                  <Status value={n.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
