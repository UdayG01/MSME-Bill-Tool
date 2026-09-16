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
  };
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
        <div className="grid grid-cols-2 gap-6">
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
          <div>
            {items.map((i) => (
              <div className="card p-3 grid grid-cols-6 gap-2 mb-3" key={i.id}>
                <Field label="Product">
                  <select
                    className={inputCls}
                    defaultValue=""
                    onChange={(e) => {
                      applyProduct(i.id, e.target.value);
                      e.target.value = "";
                    }}
                  >
                    <option value="">Manual entry</option>
                    {products.map((product) => (
                      <option key={product.id} value={product.id}>
                        {product.name}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Item Name">
                  <input
                    className={inputCls}
                    value={i.item_name}
                    onChange={(e) => update(i.id, "item_name", e.target.value)}
                  />
                </Field>
                <Field label="Description">
                  <textarea
                    className={inputCls}
                    value={i.item_description}
                    onChange={(e) =>
                      update(i.id, "item_description", e.target.value)
                    }
                  />
                </Field>
                <Field label="HSN/SAC">
                  <input
                    className={inputCls}
                    value={i.hsn_sac}
                    onChange={(e) => update(i.id, "hsn_sac", e.target.value)}
                  />
                </Field>
                <Field label="Qty">
                  <input
                    type="number"
                    disabled={frozenExport}
                    className={inputCls}
                    value={i.qty}
                    onChange={(e) => update(i.id, "qty", e.target.value)}
                  />
                </Field>
                <Field label="Rate">
                  <input
                    type="number"
                    disabled={frozenExport}
                    className={inputCls}
                    value={i.rate}
                    onChange={(e) => update(i.id, "rate", e.target.value)}
                  />
                </Field>
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
