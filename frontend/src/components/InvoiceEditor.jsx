import React, { useEffect, useState } from "react";
import { api } from "../api";
import { formatMoney, todayISO } from "../utils/format";
import { Field, Message, SectionHeader, inputCls } from "./ui";
const uid = () => Math.random().toString(36).slice(2);
const blank = () => ({
  id: uid(),
  item_name: "",
  item_description: "",
  hsn_sac: "",
  category: "",
  qty: 1,
  rate: 0,
});
const RATE_RANGES = {
  USD: [50, 120], EUR: [55, 140], GBP: [65, 165], AED: [12, 35], SGD: [35, 110],
};
export default function InvoiceEditor({
  customers,
  products = [],
  invoice,
  onSaved,
  onDone,
}) {
  const [customerId, setCustomerId] = useState("");
  const [date, setDate] = useState(todayISO());
  const [orderNumber, setOrderNumber] = useState("");
  const [orderDate, setOrderDate] = useState("");
  const [gst, setGst] = useState(18);
  const [currency, setCurrency] = useState("USD");
  const [rate, setRate] = useState("");
  const [referenceRate, setReferenceRate] = useState(null);
  const [referenceRateError, setReferenceRateError] = useState("");
  const [reverse, setReverse] = useState(false);
  const [items, setItems] = useState([blank()]);
  const [productPickerId, setProductPickerId] = useState(null);
  const [productSearch, setProductSearch] = useState("");
  const [message, setMessage] = useState({});
  useEffect(() => {
    if (invoice) {
      setCustomerId(invoice.customer_id);
      setDate(invoice.invoice_date);
      setOrderNumber(invoice.order_no || "");
      setOrderDate(invoice.order_date || "");
      setGst(Number(invoice.gst_rate));
      setCurrency(invoice.document_currency || "USD");
      setRate(invoice.exchange_rate_to_inr || "");
      setReverse(invoice.reverse_charge);
      setItems(invoice.items.map((i) => ({ ...i, id: i.id || uid() })));
    }
  }, [invoice]);
  const customer = customers.find((c) => c.id === customerId);
  const customerOptions = customers.filter((c) => !c.is_archived || c.id === customerId);
  const isExport = customer?.is_foreign;
  const isIssued = invoice?.status === "issued";
  const frozenExport = Boolean(invoice?.is_export);
  const expectedRate = RATE_RANGES[currency];
  const unusualRate = expectedRate && Number(rate) > 0 && (Number(rate) < expectedRate[0] || Number(rate) > expectedRate[1]);
  useEffect(() => {
    if (!isExport || frozenExport) {
      setReferenceRate(null);
      setReferenceRateError("");
      return undefined;
    }
    let cancelled = false;
    setReferenceRate(null);
    setReferenceRateError("");
    api.getLiveExchangeRate(currency)
      .then((value) => {
        if (!cancelled) setReferenceRate(value);
      })
      .catch((error) => {
        if (!cancelled) setReferenceRateError(error.message);
      });
    return () => {
      cancelled = true;
    };
  }, [isExport, frozenExport, currency]);
  const update = (id, key, value) =>
    setItems(items.map((i) => (i.id === id ? { ...i, [key]: value } : i)));
  const applyProduct = (itemId, productId) => {
    const product = products.find((p) => p.id === productId);
    if (!product) return;
    setItems(items.map((item) => (
      item.id === itemId
        ? {
            ...item,
            item_name: product.name,
            item_description: product.description,
            hsn_sac: product.hsn_sac,
            rate: product.amount,
          }
        : item
    )));
    setProductPickerId(null);
    setProductSearch("");
  };
  const matchingProducts = products.filter((product) => {
    const term = productSearch.trim().toLowerCase();
    if (!term) return true;
    return [product.name, product.description, product.hsn_sac]
      .join(" ")
      .toLowerCase()
      .includes(term);
  });
  const subtotal = items.reduce(
    (s, i) => s + Number(i.qty || 0) * Number(i.rate || 0),
    0,
  );
  const save = async (issue) => {
    try {
      const payload = {
        customer_id: customerId,
        invoice_date: date,
        order_no: orderNumber,
        order_date: orderDate || null,
        gst_rate: Number(gst),
        reverse_charge: reverse,
        document_currency: isExport ? currency : "INR",
        exchange_rate_to_inr: isExport ? Number(rate) : null,
        items: items.map((i) => ({
          ...i,
          description: i.item_description || i.item_name,
          qty: Number(i.qty),
          rate: Number(i.rate),
        })),
      };
      const draft = invoice
        ? await api.updateInvoice(invoice.id, payload)
        : await api.createInvoice(payload);
      if (issue) await api.issueInvoice(draft.id);
      await onSaved();
      onDone();
    } catch (e) {
      setMessage({ error: e.message });
    }
  };
  return (
    <div>
      <SectionHeader
        title={invoice ? `Edit ${isIssued ? "Issued" : "Draft"} Invoice` : "New Invoice"}
        subtitle={isIssued ? "Issued invoices can be edited until receipts or credit notes are applied." : "Drafts are editable until issued."}
      />
      <div className="p-8">
        <Message {...message} />
        <div className="grid grid-cols-[400px_minmax(0,1fr)] gap-8">
          <div className="flex flex-col gap-3">
            <Field label="Customer">
              <select
                disabled={frozenExport}
                className={inputCls}
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value)}
              >
                <option value="">Select customer</option>
                {customerOptions.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}{c.is_archived ? " (archived)" : ""}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Invoice date">
              <input
                type="date"
                className={inputCls}
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </Field>
            <Field label="Customer PO / Order Number">
              <input
                className={inputCls}
                maxLength={100}
                value={orderNumber}
                onChange={(e) => setOrderNumber(e.target.value)}
              />
            </Field>
            <Field label="PO / Order Date">
              <input
                type="date"
                className={inputCls}
                value={orderDate}
                onChange={(e) => setOrderDate(e.target.value)}
              />
            </Field>
            <Field label="GST rate">
              <input
                disabled={isExport}
                type="number"
                className={inputCls}
                value={isExport ? 0 : gst}
                onChange={(e) => setGst(e.target.value)}
              />
            </Field>
            <label>
              <input
                type="checkbox"
                checked={reverse}
                onChange={(e) => setReverse(e.target.checked)}
              />{" "}
              Reverse charge applicable
            </label>
            {isExport && (
              <>
                <Field label="Currency">
                  <select
                    disabled={frozenExport}
                    className={inputCls}
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                  >
                    {["USD", "EUR", "GBP", "AED", "SGD"].map((c) => (
                      <option key={c}>{c}</option>
                    ))}
                  </select>
                </Field>
                <Field label="Exchange rate to INR">
                  <input
                    disabled={frozenExport}
                    type="number"
                    className={inputCls}
                    value={rate}
                    onChange={(e) => setRate(e.target.value)}
                  />
                </Field>
                {!frozenExport && (
                  <div className="rounded border border-sky-200 bg-sky-50 px-3 py-2 text-sm text-slate-700">
                    {referenceRate && (
                      <>
                        <div>
                          Live reference: <b>1 {referenceRate.base_currency} = INR {Number(referenceRate.rate).toFixed(4)}</b>
                          <span className="text-slate-500"> ({referenceRate.source}, {referenceRate.rate_date})</span>
                        </div>
                        <button
                          type="button"
                          className="mt-1 text-sky-700 underline"
                          onClick={() => setRate(String(referenceRate.rate))}
                        >
                          Use this reference rate
                        </button>
                      </>
                    )}
                    {!referenceRate && !referenceRateError && "Fetching live reference rate…"}
                    {referenceRateError && (
                      <span className="text-amber-700">
                        {referenceRateError} You can still enter the rate manually.
                      </span>
                    )}
                  </div>
                )}
                {frozenExport && (
                  <div className="rounded border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600">
                    Currency, exchange rate, quantity, and rate are frozen from draft creation. Create a new draft to change financial values.
                  </div>
                )}
                {unusualRate && (
                  <div className="text-amber-700 text-sm">
                    Check exchange rate; {currency}/INR is outside the usual data-entry range of {expectedRate[0]}–{expectedRate[1]}.
                  </div>
                )}
              </>
            )}
          </div>
          <div className="min-w-0">
            {items.map((i) => (
              <div className="card mb-3 p-4 shadow-sm" key={i.id}>
                <div className="grid grid-cols-[40px_minmax(120px,1fr)_minmax(150px,1.2fr)_90px_70px_90px] gap-3 items-start">
                  <div className="pt-[22px]">
                    <button
                      type="button"
                      className="btn btn-primary flex h-10 w-10 items-center justify-center shadow-sm transition hover:bg-[#26394A] active:translate-y-px"
                      title="Select product"
                      aria-label="Select product"
                      onClick={() =>
                        setProductPickerId(productPickerId === i.id ? null : i.id)
                      }
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
                        <circle cx="11" cy="11" r="7" />
                        <path d="m20 20-3.5-3.5" />
                      </svg>
                    </button>
                  </div>
                  <Field label="Item Name">
                    <input
                      className="w-full rounded border bg-white px-3 py-2 text-sm shadow-inner min-w-0 h-10"
                      value={i.item_name}
                      onChange={(e) => update(i.id, "item_name", e.target.value)}
                    />
                  </Field>
                  <Field label="Description">
                    <textarea
                      className="w-full rounded border bg-white px-3 py-2 text-sm shadow-inner min-w-0 h-16 resize-none"
                      value={i.item_description}
                      onChange={(e) =>
                        update(i.id, "item_description", e.target.value)
                      }
                    />
                  </Field>
                  <Field label="HSN/SAC">
                    <input
                      className="w-full rounded border bg-white px-3 py-2 text-sm shadow-inner min-w-0 h-10"
                      value={i.hsn_sac}
                      onChange={(e) => update(i.id, "hsn_sac", e.target.value)}
                    />
                  </Field>
                  <Field label="Qty">
                    <input
                      type="number"
                      disabled={frozenExport}
                      className="w-full rounded border bg-white px-3 py-2 text-sm shadow-inner min-w-0 h-10"
                      value={i.qty}
                      onChange={(e) => update(i.id, "qty", e.target.value)}
                    />
                  </Field>
                  <Field label="Rate">
                    <input
                      type="number"
                      disabled={frozenExport}
                      className="w-full rounded border bg-white px-3 py-2 text-sm shadow-inner min-w-0 h-10"
                      value={i.rate}
                      onChange={(e) => update(i.id, "rate", e.target.value)}
                    />
                  </Field>
                </div>
                {productPickerId === i.id && (
                  <div className="mt-3 ml-[52px] w-full max-w-xl border-t pt-3">
                    <div className="rounded border border-slate-200 bg-white shadow-sm">
                      <div className="border-b border-slate-100 p-2">
                        <input
                          className={inputCls}
                          autoFocus
                          placeholder="Search products by name, description, or HSN/SAC"
                          value={productSearch}
                          onChange={(e) => setProductSearch(e.target.value)}
                        />
                      </div>
                      <div className="max-h-56 overflow-y-auto">
                        {matchingProducts.map((product) => (
                          <button
                            key={product.id}
                            type="button"
                            className="grid w-full grid-cols-[1fr_auto] gap-3 border-b border-slate-100 px-3 py-2 text-left text-sm transition hover:bg-[#F5F3EE]"
                            onClick={() => applyProduct(i.id, product.id)}
                          >
                            <span className="min-w-0">
                              <span className="block font-semibold text-slate-800">{product.name}</span>
                              <span className="block truncate text-xs text-slate-500">
                                {product.description || "No description"}{product.hsn_sac ? ` - HSN/SAC ${product.hsn_sac}` : ""}
                              </span>
                            </span>
                            <span className="whitespace-nowrap text-slate-700">
                              INR {formatMoney(product.amount)}
                            </span>
                          </button>
                        ))}
                        {matchingProducts.length === 0 && (
                          <div className="px-3 py-4 text-sm text-slate-500">
                            No matching products.
                          </div>
                        )}
                      </div>
                      <div className="flex justify-end p-2">
                        <button
                          type="button"
                          className="btn btn-outline px-3 py-1.5 text-sm"
                          onClick={() => {
                            setProductPickerId(null);
                            setProductSearch("");
                          }}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
            <button
              className="btn btn-outline px-3 py-2 text-sm"
              onClick={() => setItems([...items, blank()])}
            >
              Add line
            </button>
            <div className="mt-4">
              Subtotal: {isExport ? currency : "INR"} {formatMoney(subtotal)}
            </div>
            <button
              className="btn btn-outline px-4 py-2 text-sm mt-4"
              onClick={() => save(false)}
            >
              {isIssued ? "Save Changes" : "Save Draft"}
            </button>
            {!isIssued && (
              <button
                className="btn btn-primary px-4 py-2 text-sm mt-4 ml-3"
                onClick={() => save(true)}
              >
                Save & Issue
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
