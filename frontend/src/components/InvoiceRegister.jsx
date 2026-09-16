import React, { useState } from "react";
import { api } from "../api";
import { formatMoney } from "../utils/format";
import { Message, SectionHeader, Status } from "./ui";

function PdfButton({ invoice }) {
  return (
    <button
      className="inline-flex h-7 w-7 items-center justify-center rounded border border-slate-300 text-slate-700 hover:bg-slate-100"
      title="Export PDF"
      aria-label="Export PDF"
      onClick={() => api.invoicePdf(invoice.id, false)}
    >
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        className="h-4 w-4"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <path d="M14 2v6h6" />
        <path d="M12 18v-6" />
        <path d="m9 15 3 3 3-3" />
      </svg>
    </button>
  );
}

export default function InvoiceRegister({
  invoices,
  customers,
  balanceForInvoice,
  onChanged,
  onEdit,
}) {
  const [message, setMessage] = useState({});
  const action = async (fn) => {
    try {
      await fn();
      await onChanged();
    } catch (e) {
      setMessage({ error: e.message });
    }
  };
  return (
    <div>
      <SectionHeader
        title="Invoice Register"
        subtitle="Draft, issued, and cancelled invoices with guarded edit and delete actions."
      />
      <div className="p-8">
        <Message {...message} />
        <div className="min-w-0 overflow-x-auto">
          <table className="text-sm table-fixed min-w-[840px]">
          <colgroup>
            <col className="w-[13%]" />
            <col className="w-[13%]" />
            <col className="w-[23%]" />
            <col className="w-[12%]" />
            <col className="w-[12%]" />
            <col className="w-[12%]" />
            <col className="w-[15%]" />
          </colgroup>
          <thead>
            <tr className="border-b text-left">
              <th className="px-3 pb-2">Invoice</th>
              <th className="px-3 pb-2">Date</th>
              <th className="px-3 pb-2">Customer</th>
              <th className="px-3 pb-2">Status</th>
              <th className="px-3 pb-2 text-right">Total</th>
              <th className="px-3 pb-2 text-right">Balance</th>
              <th className="px-3 pb-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {invoices.map((invoice) => {
              const customer = customers.find(
                (c) => c.id === invoice.customer_id,
              );
              const amounts = balanceForInvoice(invoice);
              return (
                <tr className="border-b" key={invoice.id}>
                  <td className="px-3 py-2 break-words">{invoice.invoice_no || "Draft"}</td>
                  <td className="px-3 py-2 whitespace-nowrap">{invoice.invoice_date}</td>
                  <td className="px-3 py-2 break-words">{invoice.customer_name_snapshot || customer?.name}</td>
                  <td className="px-3 py-2">
                    <Status value={invoice.status} />
                  </td>
                  <td className="px-3 py-2 text-right whitespace-nowrap">
                    ₹{formatMoney(invoice.total)}
                  </td>
                  <td className="px-3 py-2 text-right whitespace-nowrap">
                    ₹{formatMoney(amounts.balance)}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap">
                    {invoice.status === "draft" && (
                      <div className="flex items-center gap-3">
                        <div className="flex items-center gap-2">
                          <button
                            className="underline"
                            onClick={() => onEdit(invoice)}
                          >
                            Edit
                          </button>
                          <button
                            className="underline text-red-600"
                            onClick={() =>
                              window.confirm("Delete this draft invoice?")
                                ? action(() => api.deleteInvoice(invoice.id))
                                : undefined
                            }
                          >
                            Delete
                          </button>
                        </div>
                        <button
                          className="underline"
                          onClick={() =>
                            action(() => api.issueInvoice(invoice.id))
                          }
                        >
                          Issue
                        </button>
                      </div>
                    )}
                    {invoice.status === "issued" && (
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <button
                            className="underline"
                            onClick={() => onEdit(invoice)}
                          >
                            Edit
                          </button>
                          <button
                            className="underline text-red-600"
                            onClick={() =>
                              window.confirm("Delete this issued invoice?")
                                ? action(() => api.deleteInvoice(invoice.id))
                                : undefined
                            }
                          >
                            Delete
                          </button>
                        </div>
                        <PdfButton invoice={invoice} />
                      </div>
                    )}
                    {invoice.status === "cancelled" && (
                      <div className="flex justify-end">
                        <PdfButton invoice={invoice} />
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
