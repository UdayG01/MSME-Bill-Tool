import React from "react";

export const inputCls =
  "w-full border rounded px-2.5 py-1.5 text-sm bg-white min-w-0";
export const inputStyle = { borderColor: "#D8D2C2" };
const STATUS_COLORS = {
  issued: ["#EAF4EC", "#2F6F4E"],
  draft: ["#FFF5D9", "#8A6810"],
  cancelled: ["#FBEAE5", "#B4472A"],
  active: ["#EAF4EC", "#2F6F4E"],
  voided: ["#EEE", "#666"],
};
export function Field({ label, children, hint }) {
  return (
    <label className="block">
      <span className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500 mb-1">
        {label}
      </span>
      {children}
      {hint && (
        <span className="block text-[11px] text-slate-400 mt-1">{hint}</span>
      )}
    </label>
  );
}
export function SectionHeader({ title, subtitle, right }) {
  return (
    <div
      className="flex items-start justify-between px-8 pt-8 pb-5 border-b"
      style={{ borderColor: "#E4DFD3" }}
    >
      <div>
        <h1 className="serif text-2xl">{title}</h1>
        {subtitle && (
          <p className="text-[13px] text-slate-500 mt-1">{subtitle}</p>
        )}
      </div>
      {right}
    </div>
  );
}
export function Message({ error, success }) {
  if (!error && !success) return null;
  return (
    <div
      className="card p-3 text-sm mb-4"
      style={{
        background: error ? "#FBEAE5" : "#EEF6EF",
        borderColor: error ? "#E7B3A5" : "#BFE0C4",
      }}
    >
      {error || success}
    </div>
  );
}
export function Status({ value }) {
  const pair = STATUS_COLORS[value] || STATUS_COLORS.draft;
  return (
    <span
      className="text-[11px] px-2 py-0.5 rounded"
      style={{ background: pair[0], color: pair[1] }}
    >
      {value}
    </span>
  );
}
