import React from "react";
import { formatMoney } from "../utils/format";

export default function Dashboard({
  invoices,
  customers,
  balanceForInvoice,
  setTab,
}) {
  const issued = invoices.filter((i) => i.status === "issued");
  const outstanding = issued.reduce(
    (sum, invoice) => sum + balanceForInvoice(invoice).balance,
    0,
  );
  const cards = [
    [
      "Issued sales",
      `₹${formatMoney(issued.reduce((s, i) => s + Number(i.total), 0))}`,
    ],
    ["Outstanding", `₹${formatMoney(outstanding)}`],
    ["Active customers", customers.filter((c) => !c.is_archived).length],
    ["Draft invoices", invoices.filter((i) => i.status === "draft").length],
  ];
  return (
    <div>
      <div className="px-8 pt-8 pb-5 border-b">
        <h1 className="serif text-2xl">Dashboard</h1>
        <p className="text-sm text-slate-500">
          Billing and receivable overview.
        </p>
      </div>
      <div className="p-8">
        <div className="grid grid-cols-4 gap-4">
          {cards.map(([label, value]) => (
            <div className="card p-4" key={label}>
              <div className="text-[11px] uppercase text-slate-500">
                {label}
              </div>
              <div className="serif text-xl mt-2 tnum">{value}</div>
            </div>
          ))}
        </div>
        <div className="card p-5 mt-6">
          <div className="text-[11px] uppercase text-slate-500 mb-3">
            Quick actions
          </div>
          <div className="flex gap-3">
            <button
              className="btn btn-primary px-3 py-2 text-sm"
              onClick={() => setTab("invoice")}
            >
              New invoice
            </button>
            <button
              className="btn btn-outline px-3 py-2 text-sm"
              onClick={() => setTab("receipts")}
            >
              Record receipt
            </button>
            <button
              className="btn btn-outline px-3 py-2 text-sm"
              onClick={() => setTab("receivables")}
            >
              View receivables
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
