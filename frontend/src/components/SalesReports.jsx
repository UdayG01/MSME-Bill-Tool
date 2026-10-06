import React, { useEffect, useState } from "react";
import { api } from "../api";
import { formatMoney } from "../utils/format";
import { Message, SectionHeader } from "./ui";
export default function SalesReports() {
  const [area, setArea] = useState(null);
  const [product, setProduct] = useState(null);
  const [register, setRegister] = useState(null);
  const [error, setError] = useState("");
  const [registerError, setRegisterError] = useState("");
  useEffect(() => {
    Promise.all([api.salesByArea(), api.salesByProduct()])
      .then(([a, p]) => {
        setArea(a);
        setProduct(p);
      })
      .catch((e) => setError(e.message));
    api.salesRegister()
      .then(setRegister)
      .catch((e) => { setRegister([]); setRegisterError(e.message); });
  }, []);
  const Chart = ({ title, rows }) => (
    <div className="card p-5">
      <div className="text-[11px] uppercase text-slate-500 mb-4">
        {title} — pre-tax, net of credits
      </div>
      {rows?.map((r) => (
        <div className="mb-3" key={r.key}>
          <div className="flex justify-between text-sm">
            <span>{r.key}</span>
            <span>₹{formatMoney(r.total)}</span>
          </div>
          <div className="h-2 rounded mt-1" style={{ background: "#EEE9DD" }}>
            <div
              className="h-2 rounded"
              style={{
                background: "#C9A227",
                width: `${rows[0]?.total ? Math.max(0, (Number(r.total) / Number(rows[0].total)) * 100) : 0}%`,
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
  return (
    <div>
      <SectionHeader
        title="Sales Reports"
        subtitle="Current reports use a consistent pre-tax sales basis."
      />
      <div className="p-8">
        <Message error={error} />
        {!area ? (
          "Loading…"
        ) : (
          <div className="grid grid-cols-2 gap-6">
            <Chart title="Area-wise" rows={area} />
            <Chart title="Product / service-wise" rows={product} />
          </div>
        )}
        <div className="card mt-6 p-5">
          <div className="mb-4 text-[11px] uppercase text-slate-500">Sales Register — issued invoices</div>
          {registerError && <div className="mb-3 text-sm text-amber-800">{registerError}</div>}
          <div className="overflow-x-auto">
            <table className="min-w-[950px] text-sm">
              <thead><tr className="border-b text-left"><th className="p-2">Invoice</th><th className="p-2">Date</th><th className="p-2">Customer</th><th className="p-2 text-right">Taxable Value</th><th className="p-2 text-right">GST</th><th className="p-2 text-right">Out of Pocket Exp.</th><th className="p-2 text-right">Invoice Total</th><th className="p-2">Place of Supply</th></tr></thead>
              <tbody>{register?.map((row) => <tr className="border-b" key={row.invoice_no}><td className="p-2">{row.invoice_no}</td><td className="p-2">{row.invoice_date}</td><td className="p-2">{row.customer_name}</td><td className="p-2 text-right">₹{formatMoney(row.taxable_value)}</td><td className="p-2 text-right">₹{formatMoney(row.gst)}</td><td className="p-2 text-right">₹{formatMoney(row.oop_amount)}</td><td className="p-2 text-right">₹{formatMoney(row.invoice_total)}</td><td className="p-2">{row.place_of_supply_code} - {row.place_of_supply_name}</td></tr>)}</tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
