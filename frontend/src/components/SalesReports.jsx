import React, { useEffect, useState } from "react";
import { api } from "../api";
import { formatMoney } from "../utils/format";
import { Message, SectionHeader } from "./ui";
export default function SalesReports() {
  const [area, setArea] = useState(null);
  const [product, setProduct] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    Promise.all([api.salesByArea(), api.salesByProduct()])
      .then(([a, p]) => {
        setArea(a);
        setProduct(p);
      })
      .catch((e) => setError(e.message));
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
      </div>
    </div>
  );
}
