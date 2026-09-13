import React, { useEffect, useState } from "react";
import { api } from "../api";
import { formatMoney, todayISO } from "../utils/format";
import { Field, Message, SectionHeader, inputCls, inputStyle } from "./ui";
export default function Receivables() {
  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");
  const [asOf, setAsOf] = useState(todayISO());
  useEffect(() => {
    setRows(null);
    api
      .receivablesReport(asOf)
      .then(setRows)
      .catch((e) => setError(e.message));
  }, [asOf]);
  if (error)
    return (
      <div className="p-8">
        <Message error={error} />
      </div>
    );
  if (!rows) return <div className="p-8">Loading…</div>;
  return (
    <div>
      <SectionHeader
        title="Receivable & Overdue"
        subtitle="Issued invoices less active receipts and credit notes."
        right={
          <Field label="As of date">
            <input
              type="date"
              className={inputCls}
              style={inputStyle}
              value={asOf}
              onChange={(e) => setAsOf(e.target.value)}
            />
          </Field>
        }
      />
      <div className="p-8">
        <div className="mb-4">
          Total outstanding:{" "}
          <b>₹{formatMoney(rows.reduce((s, r) => s + Number(r.balance), 0))}</b>
        </div>
        <table className="text-sm">
          <thead>
            <tr className="text-left border-b">
              <th>Invoice</th>
              <th>Customer</th>
              <th>Due date</th>
              <th>Total</th>
              <th>Paid</th>
              <th>Credit</th>
              <th>Balance</th>
              <th>Ageing</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr className="border-b" key={r.invoice_id}>
                <td className="py-2">{r.invoice_no}</td>
                <td>{r.customer_name}</td>
                <td>{r.due_date}</td>
                <td>₹{formatMoney(r.invoice_total)}</td>
                <td>₹{formatMoney(r.paid)}</td>
                <td>₹{formatMoney(r.credited)}</td>
                <td>₹{formatMoney(r.balance)}</td>
                <td>{r.bucket}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
