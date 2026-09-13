import React, { useState } from "react";
import { api } from "../api";
import { formatMoney } from "../utils/format";
import { Message, SectionHeader, Status } from "./ui";
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
        subtitle="Draft, issued, and cancelled invoices. Issued financial data is immutable."
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
                      <>
                        <button
                          className="underline mr-2"
                          onClick={() => onEdit(invoice)}
                        >
                          Edit
                        </button>
                        <button
                          className="underline mr-2"
                          onClick={() =>
                            action(() => api.issueInvoice(invoice.id))
                          }
                        >
                          Issue
                        </button>
                        <button
                          className="underline text-red-600"
                          onClick={() =>
                            action(() => api.deleteInvoice(invoice.id))
                          }
                        >
                          Delete
                        </button>
                      </>
                    )}
                    {invoice.status !== "draft" && (
                      <button
                        className="underline"
                        onClick={() => api.invoicePdf(invoice.id, false)}
                      >
                        PDF
                      </button>
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
