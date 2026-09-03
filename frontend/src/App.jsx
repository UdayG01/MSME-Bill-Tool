import React, { useEffect, useState } from "react";
import { api } from "./api";

const todayISO = () => new Date().toISOString().slice(0, 10);
const uid = () => Math.random().toString(36).slice(2, 10);
const money = (value) => (Number(value) || 0).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const inputCls = "w-full border rounded px-2.5 py-1.5 text-sm bg-white min-w-0";
const inputStyle = { borderColor: "#D8D2C2" };
const blankCustomer = { name: "", address: "", gstin: "", country: "India", is_foreign: false, area: "", state_code: "", credit_days: 30 };
const blankItem = () => ({ id: uid(), description: "", category: "", hsn_sac: "", qty: 1, rate: 0 });

function Field({ label, children, hint }) {
  return <label className="block"><span className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500 mb-1">{label}</span>{children}{hint && <span className="block text-[11px] text-slate-400 mt-1">{hint}</span>}</label>;
}

function SectionHeader({ title, subtitle, right }) {
  return <div className="flex items-start justify-between px-8 pt-8 pb-5 border-b" style={{ borderColor: "#E4DFD3" }}><div><h1 className="serif text-2xl">{title}</h1>{subtitle && <p className="text-[13px] text-slate-500 mt-1">{subtitle}</p>}</div>{right}</div>;
}

function Message({ error, success }) {
  if (!error && !success) return null;
  return <div className="card p-3 text-sm mb-4" style={{ background: error ? "#FBEAE5" : "#EEF6EF", borderColor: error ? "#E7B3A5" : "#BFE0C4" }}>{error || success}</div>;
}

function AuthScreen({ onAuthed }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ company_name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async () => {
    setBusy(true); setError("");
    try { mode === "signup" ? await api.signup(form) : await api.login(form); onAuthed(); }
    catch (e) { setError(e.message); }
    finally { setBusy(false); }
  };
  return <div className="min-h-screen flex items-center justify-center" style={{ background: "#F5F3EE" }}><div className="card p-8 w-full max-w-sm">
    <div className="serif text-xl mb-1">Khata<span style={{ color: "#C9A227" }}>Bandh</span></div><div className="text-[13px] text-slate-500 mb-6">Billing &amp; Receivable Control</div>
    <div className="flex flex-col gap-3">{mode === "signup" && <Field label="Company name"><input className={inputCls} style={inputStyle} value={form.company_name} onChange={(e) => setForm({ ...form, company_name: e.target.value })} /></Field>}
      <Field label="Email"><input type="email" className={inputCls} style={inputStyle} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></Field>
      <Field label="Password"><input type="password" className={inputCls} style={inputStyle} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /></Field>
      <Message error={error} /><button className="btn btn-primary text-sm px-3 py-2" onClick={submit} disabled={busy}>{busy ? "Please wait…" : mode === "signup" ? "Create account" : "Log in"}</button>
      <button className="text-[12px] text-slate-500 underline" onClick={() => setMode(mode === "signup" ? "login" : "signup")}>{mode === "signup" ? "Already have an account? Log in" : "New company? Sign up"}</button>
    </div></div></div>;
}

const NAV = [
  ["dashboard", "Dashboard"], ["company", "Company Setup"], ["lut", "LUT Master (Exports)"], ["customers", "Customers"],
  ["invoice", "New Invoice"], ["invoices", "Invoice Register"], ["receipts", "Receipt Entry"], ["credits", "Credit Notes"],
  ["receivables", "Receivable / Overdue"], ["sales", "Sales Reports"],
];

export default function App() {
  const [authed, setAuthed] = useState(null);
  const [tab, setTab] = useState("dashboard");
  const [company, setCompany] = useState(null);
  const [lut, setLut] = useState(null);
  const [customers, setCustomers] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [receipts, setReceipts] = useState([]);
  const [creditNotes, setCreditNotes] = useState([]);
  const [editingInvoice, setEditingInvoice] = useState(null);
  const [loadError, setLoadError] = useState("");

  useEffect(() => { api.me().then(() => setAuthed(true)).catch(() => setAuthed(false)); }, []);
  const loadAll = async () => {
    setLoadError("");
    try {
      const [c, l, custs, invs, recs, credits] = await Promise.all([api.getCompany(), api.getLut(), api.listCustomers(true), api.listInvoices(), api.listReceipts(), api.listCreditNotes()]);
      setCompany(c); setLut(l); setCustomers(custs); setInvoices(invs); setReceipts(recs); setCreditNotes(credits);
    } catch (e) { setLoadError(e.message); }
  };
  useEffect(() => { if (authed) loadAll(); }, [authed]);

  const balanceForInvoice = (invoice) => {
    if (invoice.status !== "issued") return { paid: 0, credited: 0, balance: 0 };
    const paid = receipts.filter((r) => r.invoice_id === invoice.id && r.status === "active").reduce((sum, r) => sum + Number(r.amount), 0);
    const credited = creditNotes.filter((n) => n.invoice_id === invoice.id && n.status === "active").reduce((sum, n) => sum + Number(n.total), 0);
    return { paid, credited, balance: Number(invoice.total) - paid - credited };
  };
  const editDraft = (invoice) => { setEditingInvoice(invoice); setTab("invoice"); };
  const logout = async () => { await api.logout(); setAuthed(false); };

  if (authed === null) return <div className="min-h-screen flex items-center justify-center">Loading…</div>;
  if (!authed) return <AuthScreen onAuthed={() => setAuthed(true)} />;
  if (!company) return <div className="min-h-screen flex items-center justify-center"><div><Message error={loadError} /><span>Loading your ledger…</span></div></div>;

  return <div className="w-full min-h-screen flex" style={{ background: "#F5F3EE", color: "#1C2B39", fontFamily: "Inter, -apple-system, sans-serif" }}>
    <style>{`.serif{font-family:Georgia,'Times New Roman',serif}.tnum{font-variant-numeric:tabular-nums}input:focus,select:focus,textarea:focus{outline:2px solid #C9A227;outline-offset:1px}table{border-collapse:collapse;width:100%}.btn{border-radius:4px;font-weight:600}.btn:disabled{opacity:.45}.btn-primary{background:#1C2B39;color:#F5F3EE}.btn-outline{border:1px solid #1C2B39;color:#1C2B39;background:transparent}.btn-danger{background:#B4472A;color:white}.card{background:#FFF;border:1px solid #E4DFD3;border-radius:6px}`}</style>
    <aside className="w-60 shrink-0" style={{ background: "#1C2B39" }}><div className="px-5 py-6 border-b" style={{ borderColor: "#2A3D4F" }}><div className="serif text-lg text-white">Khata<span style={{ color: "#C9A227" }}>Bandh</span></div><div className="text-[11px] text-slate-400 mt-0.5">{company.company_name}</div></div>
      <nav className="py-3">{NAV.map(([id, label]) => <button key={id} onClick={() => { setTab(id); if (id === "invoice") setEditingInvoice(null); }} className="w-full px-5 py-2.5 text-[13px] text-left" style={{ background: tab === id ? "#0F1C28" : "transparent", color: tab === id ? "#C9A227" : "#C7CDD3", borderLeft: tab === id ? "3px solid #C9A227" : "3px solid transparent" }}>{label}</button>)}</nav>
      <button onClick={logout} className="mx-5 mt-4 text-[12px] text-slate-400 underline">Log out</button></aside>
    <main className="flex-1 min-w-0 overflow-y-auto">{loadError && <div className="m-4"><Message error={loadError} /></div>}
      {tab === "dashboard" && <Dashboard invoices={invoices} customers={customers} balanceForInvoice={balanceForInvoice} setTab={setTab} />}
      {tab === "company" && <CompanySetup company={company} onSaved={loadAll} />}
      {tab === "lut" && <LutMaster lut={lut} onSaved={loadAll} />}
      {tab === "customers" && <Customers customers={customers} onChanged={loadAll} />}
      {tab === "invoice" && <InvoiceEditor company={company} customers={customers.filter((c) => !c.is_archived)} invoice={editingInvoice} onSaved={loadAll} onDone={() => { setEditingInvoice(null); setTab("invoices"); }} />}
      {tab === "invoices" && <InvoiceRegister invoices={invoices} customers={customers} balanceForInvoice={balanceForInvoice} onChanged={loadAll} onEdit={editDraft} />}
      {tab === "receipts" && <Receipts invoices={invoices} customers={customers} receipts={receipts} balanceForInvoice={balanceForInvoice} onChanged={loadAll} />}
      {tab === "credits" && <CreditNotes invoices={invoices} customers={customers} creditNotes={creditNotes} balanceForInvoice={balanceForInvoice} onChanged={loadAll} />}
      {tab === "receivables" && <Receivables />}{tab === "sales" && <SalesReports />}
    </main>
  </div>;
}

function Dashboard({ invoices, customers, balanceForInvoice, setTab }) {
  const issued = invoices.filter((i) => i.status === "issued");
  const outstanding = issued.reduce((sum, invoice) => sum + balanceForInvoice(invoice).balance, 0);
  const cards = [["Issued sales", `₹${money(issued.reduce((s, i) => s + Number(i.total), 0))}`], ["Outstanding", `₹${money(outstanding)}`], ["Active customers", customers.filter((c) => !c.is_archived).length], ["Draft invoices", invoices.filter((i) => i.status === "draft").length]];
  return <div><SectionHeader title="Dashboard" subtitle="Billing and receivable overview." /><div className="p-8"><div className="grid grid-cols-4 gap-4">{cards.map(([label, value]) => <div className="card p-4" key={label}><div className="text-[11px] uppercase text-slate-500">{label}</div><div className="serif text-xl mt-2 tnum">{value}</div></div>)}</div>
    <div className="card p-5 mt-6"><div className="text-[11px] uppercase text-slate-500 mb-3">Quick actions</div><div className="flex gap-3"><button className="btn btn-primary px-3 py-2 text-sm" onClick={() => setTab("invoice")}>New invoice</button><button className="btn btn-outline px-3 py-2 text-sm" onClick={() => setTab("receipts")}>Record receipt</button><button className="btn btn-outline px-3 py-2 text-sm" onClick={() => setTab("receivables")}>View receivables</button></div></div></div></div>;
}

function CompanySetup({ company, onSaved }) {
  const [form, setForm] = useState(company); const [message, setMessage] = useState({});
  const fields = [["company_name", "Company Name"], ["address", "Address"], ["gstin", "GSTIN"], ["cin", "CIN"], ["state_code", "State Code"], ["email", "Email"], ["phone", "Phone"], ["invoice_prefix", "Invoice Prefix"], ["bank_name", "Bank Name"], ["bank_account", "Bank Account"], ["bank_ifsc", "Bank IFSC"]];
  const save = async () => { try { await api.updateCompany(form); await onSaved(); setMessage({ success: "Company details saved." }); } catch (e) { setMessage({ error: e.message }); } };
  return <div><SectionHeader title="Company Setup" subtitle="These details are snapshotted when an invoice is issued." /><div className="p-8 max-w-3xl"><Message {...message} /><div className="grid grid-cols-2 gap-4">{fields.map(([key, label]) => <Field key={key} label={label} hint={key === "state_code" ? "Two-digit GST state code, e.g. 06 for Haryana." : undefined}>{key === "address" ? <textarea className={inputCls} style={inputStyle} value={form[key] || ""} onChange={(e) => setForm({ ...form, [key]: e.target.value })} /> : <input className={inputCls} style={inputStyle} maxLength={key === "state_code" ? 2 : undefined} inputMode={key === "state_code" ? "numeric" : undefined} value={form[key] || ""} onChange={(e) => setForm({ ...form, [key]: e.target.value })} />}</Field>)}</div><button className="btn btn-primary px-4 py-2 text-sm mt-5" onClick={save}>Save company</button></div></div>;
}

function LutMaster({ lut, onSaved }) {
  const [form, setForm] = useState(lut); const [message, setMessage] = useState({});
  const save = async () => { try { await api.updateLut(form); await onSaved(); setMessage({ success: "LUT details saved." }); } catch (e) { setMessage({ error: e.message }); } };
  return <div><SectionHeader title="LUT Master" subtitle="Stored for export invoice snapshots; validity is not enforced in this version." /><div className="p-8 max-w-2xl"><Message {...message} /><div className="grid grid-cols-2 gap-4">{[["lut_no", "LUT ARN / Number", "text"], ["lut_date", "LUT Date", "date"], ["valid_from", "Valid From", "date"], ["valid_to", "Valid To", "date"]].map(([key, label, type]) => <Field key={key} label={label}><input type={type} className={inputCls} style={inputStyle} value={form[key] || ""} onChange={(e) => setForm({ ...form, [key]: e.target.value || null })} /></Field>)}</div><button className="btn btn-primary px-4 py-2 text-sm mt-5" onClick={save}>Save LUT</button></div></div>;
}

function Customers({ customers, onChanged }) {
  const [form, setForm] = useState(blankCustomer); const [editing, setEditing] = useState(null); const [showArchived, setShowArchived] = useState(false); const [message, setMessage] = useState({});
  const save = async () => { try { editing ? await api.updateCustomer(editing, form) : await api.createCustomer(form); setForm(blankCustomer); setEditing(null); await onChanged(); setMessage({ success: editing ? "Customer updated." : "Customer created." }); } catch (e) { setMessage({ error: e.message }); } };
  const edit = (customer) => { setEditing(customer.id); setForm({ name: customer.name, address: customer.address, gstin: customer.gstin, country: customer.country, is_foreign: customer.is_foreign, area: customer.area, state_code: customer.state_code || "", credit_days: customer.credit_days }); };
  const toggleArchive = async (customer) => { try { customer.is_archived ? await api.restoreCustomer(customer.id) : await api.archiveCustomer(customer.id); await onChanged(); } catch (e) { setMessage({ error: e.message }); } };
  const visible = customers.filter((c) => showArchived || !c.is_archived);
  return <div><SectionHeader title="Customers" subtitle="Edit active customers or archive them without breaking historical invoices." right={<label className="text-sm"><input type="checkbox" checked={showArchived} onChange={(e) => setShowArchived(e.target.checked)} /> Show archived</label>} /><div className="p-8 grid grid-cols-3 gap-6"><div className="card p-5 h-fit"><Message {...message} /><div className="font-semibold mb-3">{editing ? "Edit customer" : "Add customer"}</div><div className="flex flex-col gap-3">
    <Field label="Name"><input className={inputCls} style={inputStyle} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></Field><Field label="Address"><textarea className={inputCls} style={inputStyle} value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} /></Field><Field label="Country"><input className={inputCls} style={inputStyle} value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })} /></Field>
    <label className="text-sm"><input type="checkbox" checked={form.is_foreign} onChange={(e) => setForm({ ...form, is_foreign: e.target.checked })} /> Foreign client</label>{!form.is_foreign && <><Field label="GSTIN"><input className={inputCls} style={inputStyle} value={form.gstin} onChange={(e) => setForm({ ...form, gstin: e.target.value })} /></Field><Field label="State code" hint="Two-digit GST state code, e.g. 06 for Haryana."><input maxLength={2} inputMode="numeric" className={inputCls} style={inputStyle} value={form.state_code} onChange={(e) => setForm({ ...form, state_code: e.target.value })} /></Field></>}
    <Field label="Area / Region"><input className={inputCls} style={inputStyle} value={form.area} onChange={(e) => setForm({ ...form, area: e.target.value })} /></Field><Field label="Credit days"><input type="number" min="0" className={inputCls} style={inputStyle} value={form.credit_days} onChange={(e) => setForm({ ...form, credit_days: Number(e.target.value) })} /></Field>
    <button className="btn btn-primary px-3 py-2 text-sm" onClick={save}>{editing ? "Update customer" : "Add customer"}</button>{editing && <button className="text-sm underline" onClick={() => { setEditing(null); setForm(blankCustomer); }}>Cancel editing</button>}
  </div></div><div className="col-span-2"><table className="text-sm"><thead><tr className="text-left border-b"><th className="py-2">Name</th><th>Country</th><th>State code</th><th>Area</th><th>Credit</th><th>Status</th><th></th></tr></thead><tbody>{visible.map((c) => <tr key={c.id} className="border-b"><td className="py-2">{c.name}</td><td>{c.country}</td><td>{c.state_code || "—"}</td><td>{c.area || "—"}</td><td>{c.credit_days} days</td><td>{c.is_archived ? "Archived" : "Active"}</td><td className="flex gap-2 py-2"><button className="underline" onClick={() => edit(c)} disabled={c.is_archived}>Edit</button><button className="underline" onClick={() => toggleArchive(c)}>{c.is_archived ? "Restore" : "Archive"}</button></td></tr>)}</tbody></table></div></div></div>;
}

function InvoiceEditor({ company, customers, invoice, onSaved, onDone }) {
  const [customerId, setCustomerId] = useState(""); const [invoiceDate, setInvoiceDate] = useState(todayISO()); const [orderNo, setOrderNo] = useState(""); const [orderDate, setOrderDate] = useState(""); const [gstRate, setGstRate] = useState(18); const [documentCurrency, setDocumentCurrency] = useState("INR"); const [exchangeRate, setExchangeRate] = useState(""); const [items, setItems] = useState([blankItem()]); const [message, setMessage] = useState({}); const [busy, setBusy] = useState(false);
  useEffect(() => { if (invoice) { setCustomerId(invoice.customer_id); setInvoiceDate(invoice.invoice_date); setOrderNo(invoice.order_no || ""); setOrderDate(invoice.order_date || ""); setGstRate(Number(invoice.gst_rate)); setDocumentCurrency(invoice.document_currency || "INR"); setExchangeRate(invoice.exchange_rate_to_inr || ""); setItems(invoice.items.map((item) => ({ ...item, id: item.id || uid() }))); } }, [invoice]);
  const customer = customers.find((c) => c.id === customerId); const isExport = customer?.is_foreign;
  const subtotal = items.reduce((s, item) => s + Number(item.qty || 0) * Number(item.rate || 0), 0); const gst = isExport ? 0 : subtotal * Number(gstRate || 0) / 100;
  const payload = () => ({ customer_id: customerId, invoice_date: invoiceDate, order_no: orderNo, order_date: orderDate || null, gst_rate: Number(gstRate), document_currency: isExport ? documentCurrency : "INR", exchange_rate_to_inr: isExport ? Number(exchangeRate) : null, items: items.map(({ description, category, hsn_sac, qty, rate }) => ({ description, category, hsn_sac, qty: Number(qty), rate: Number(rate) })) });
  const persist = async (issue) => { setBusy(true); setMessage({}); try { const draft = invoice ? await api.updateInvoice(invoice.id, payload()) : await api.createInvoice(payload()); if (issue) await api.issueInvoice(draft.id); await onSaved(); onDone(); } catch (e) { setMessage({ error: e.message }); } finally { setBusy(false); } };
  const updateItem = (id, key, value) => setItems(items.map((item) => item.id === id ? { ...item, [key]: value } : item));
  return <div><SectionHeader title={invoice ? "Edit Draft Invoice" : "New Invoice"} subtitle="Drafts are editable. Issuing allocates the permanent financial-year invoice number." /><div className="p-8"><Message {...message} /><div className="grid grid-cols-2 gap-8"><div className="flex flex-col gap-4"><div className="card p-4"><div className="serif">{company.company_name}</div><div className="text-sm text-slate-500 whitespace-pre-line">{company.address}</div></div>
    <Field label="Customer"><select className={inputCls} style={inputStyle} value={customerId} onChange={(e) => setCustomerId(e.target.value)}><option value="">Select customer…</option>{customers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></Field>
    <div className="grid grid-cols-2 gap-3"><Field label="Invoice date"><input type="date" className={inputCls} style={inputStyle} value={invoiceDate} onChange={(e) => setInvoiceDate(e.target.value)} /></Field><Field label="GST rate %"><input disabled={isExport} type="number" min="0" max="100" className={inputCls} style={inputStyle} value={isExport ? 0 : gstRate} onChange={(e) => setGstRate(e.target.value)} /></Field><Field label="Order number"><input className={inputCls} style={inputStyle} value={orderNo} onChange={(e) => setOrderNo(e.target.value)} /></Field><Field label="Order date"><input type="date" className={inputCls} style={inputStyle} value={orderDate} onChange={(e) => setOrderDate(e.target.value)} /></Field></div>{isExport && <div className="grid grid-cols-2 gap-3 mt-3"><Field label="Invoice currency"><input maxLength="3" className={inputCls} style={inputStyle} value={documentCurrency} onChange={(e) => setDocumentCurrency(e.target.value.toUpperCase())} /></Field><Field label="Exchange rate to INR"><input type="number" min="0.000001" step="any" className={inputCls} style={inputStyle} value={exchangeRate} onChange={(e) => setExchangeRate(e.target.value)} /></Field></div>}</div>
    <div className="flex flex-col gap-3">{items.map((item) => <div className="card p-3 grid grid-cols-12 gap-2 items-end" key={item.id}><div className="col-span-4"><Field label="Description"><input className={inputCls} style={inputStyle} value={item.description} onChange={(e) => updateItem(item.id, "description", e.target.value)} /></Field></div><div className="col-span-3"><Field label="Category"><input className={inputCls} style={inputStyle} value={item.category} onChange={(e) => updateItem(item.id, "category", e.target.value)} /></Field></div><div className="col-span-2"><Field label="Qty"><input type="number" min="0.01" step="any" className={inputCls} style={inputStyle} value={item.qty} onChange={(e) => updateItem(item.id, "qty", e.target.value)} /></Field></div><div className="col-span-2"><Field label="Rate"><input type="number" min="0" step="any" className={inputCls} style={inputStyle} value={item.rate} onChange={(e) => updateItem(item.id, "rate", e.target.value)} /></Field></div><button className="col-span-1 text-red-600" onClick={() => setItems(items.filter((i) => i.id !== item.id))}>×</button></div>)}
      <button className="btn btn-outline px-3 py-2 text-sm w-fit" onClick={() => setItems([...items, blankItem()])}>Add line</button><div className="card p-4 ml-auto w-72 text-sm"><div className="flex justify-between"><span>Subtotal</span><b>₹{money(subtotal)}</b></div><div className="flex justify-between"><span>GST</span><b>₹{money(gst)}</b></div><div className="flex justify-between border-t mt-2 pt-2"><span>Total</span><b>₹{money(subtotal + gst)}</b></div></div>
      <div className="flex gap-3"><button disabled={busy} className="btn btn-outline px-4 py-2 text-sm" onClick={() => persist(false)}>Save Draft</button><button disabled={busy} className="btn btn-primary px-4 py-2 text-sm" onClick={() => persist(true)}>Save &amp; Issue</button>{invoice && <button className="text-sm underline" onClick={onDone}>Cancel</button>}</div>
    </div></div></div></div>;
}

function Status({ value }) { const colors = { issued: ["#EAF4EC", "#2F6F4E"], draft: ["#FFF5D9", "#8A6810"], cancelled: ["#FBEAE5", "#B4472A"], active: ["#EAF4EC", "#2F6F4E"], voided: ["#EEE", "#666"] }; const pair = colors[value] || colors.draft; return <span className="text-[11px] px-2 py-0.5 rounded" style={{ background: pair[0], color: pair[1] }}>{value}</span>; }

function InvoiceRegister({ invoices, customers, balanceForInvoice, onChanged, onEdit }) {
  const [message, setMessage] = useState({});
  const action = async (fn) => { try { await fn(); await onChanged(); } catch (e) { setMessage({ error: e.message }); } };
  const issue = (invoice) => { if (window.confirm("Issue this draft? It will receive a permanent invoice number and become immutable.")) action(() => api.issueInvoice(invoice.id)); };
  const cancel = (invoice) => { const reason = window.prompt("Cancellation reason:"); if (reason) action(() => api.cancelInvoice(invoice.id, reason)); };
  const remove = (invoice) => { if (window.confirm("Delete this draft permanently?")) action(() => api.deleteInvoice(invoice.id)); };
  return <div><SectionHeader title="Invoice Register" subtitle="Draft, issued, and cancelled invoices. Issued financial data is immutable." /><div className="p-8"><Message {...message} /><table className="text-sm"><thead><tr className="text-left border-b"><th className="py-2">Invoice</th><th>Date</th><th>Customer</th><th>Status</th><th>Total</th><th>Paid</th><th>Credit</th><th>Balance</th><th></th></tr></thead><tbody>{invoices.map((invoice) => { const customer = customers.find((c) => c.id === invoice.customer_id); const amounts = balanceForInvoice(invoice); return <tr key={invoice.id} className="border-b"><td className="py-2">{invoice.invoice_no || "Draft"}</td><td>{invoice.invoice_date}</td><td>{invoice.customer_name_snapshot || customer?.name || "—"}</td><td><Status value={invoice.status} /></td><td>₹{money(invoice.total)}</td><td>₹{money(amounts.paid)}</td><td>₹{money(amounts.credited)}</td><td>₹{money(amounts.balance)}</td><td><div className="flex flex-wrap gap-2 text-xs">{invoice.status === "draft" && <><button className="underline" onClick={() => onEdit(invoice)}>Edit</button><button className="underline" onClick={() => issue(invoice)}>Issue</button><button className="underline text-red-600" onClick={() => remove(invoice)}>Delete</button></>}{invoice.status !== "draft" && <><button className="underline" onClick={() => api.invoicePdf(invoice.id, false)}>View PDF</button><button className="underline" onClick={() => api.invoicePdf(invoice.id, true)}>Download</button></>}{invoice.status === "issued" && <button className="underline text-red-600" onClick={() => cancel(invoice)}>Cancel</button>}</div></td></tr>; })}</tbody></table></div></div>;
}

function Receipts({ invoices, customers, receipts, balanceForInvoice, onChanged }) {
  const [editing, setEditing] = useState(null); const [form, setForm] = useState({ invoice_id: "", amount: "", date: todayISO(), mode: "Bank Transfer", reference: "" }); const [message, setMessage] = useState({});
  const issued = invoices.filter((i) => i.status === "issued"); const selected = issued.find((i) => i.id === form.invoice_id);
  const save = async () => { try { if (editing) await api.updateReceipt(editing, { amount: Number(form.amount), date: form.date, mode: form.mode, reference: form.reference }); else await api.createReceipt({ ...form, amount: Number(form.amount) }); setForm({ invoice_id: "", amount: "", date: todayISO(), mode: "Bank Transfer", reference: "" }); setEditing(null); await onChanged(); setMessage({ success: editing ? "Receipt updated." : "Receipt recorded." }); } catch (e) { setMessage({ error: e.message }); } };
  const edit = (receipt) => { setEditing(receipt.id); setForm({ invoice_id: receipt.invoice_id, amount: receipt.amount, date: receipt.date, mode: receipt.mode, reference: receipt.reference }); };
  const voidReceipt = async (receipt) => { const reason = window.prompt("Reason for voiding this receipt:"); if (!reason) return; try { await api.voidReceipt(receipt.id, reason); await onChanged(); } catch (e) { setMessage({ error: e.message }); } };
  const restore = async (receipt) => { try { await api.restoreReceipt(receipt.id); await onChanged(); } catch (e) { setMessage({ error: e.message }); } };
  return <div><SectionHeader title="Receipts" subtitle="Correct active receipts or void them while preserving history." /><div className="p-8 grid grid-cols-3 gap-6"><div className="card p-5 h-fit"><Message {...message} /><div className="font-semibold mb-3">{editing ? "Edit receipt" : "Record receipt"}</div><div className="flex flex-col gap-3"><Field label="Invoice"><select disabled={!!editing} className={inputCls} style={inputStyle} value={form.invoice_id} onChange={(e) => setForm({ ...form, invoice_id: e.target.value })}><option value="">Select invoice…</option>{issued.map((i) => <option key={i.id} value={i.id}>{i.invoice_no}</option>)}</select></Field>{selected && <div className="text-xs">Outstanding: ₹{money(balanceForInvoice(selected).balance)}</div>}<Field label="Amount"><input type="number" min="0.01" className={inputCls} style={inputStyle} value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} /></Field><Field label="Date"><input type="date" className={inputCls} style={inputStyle} value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} /></Field><Field label="Mode"><input className={inputCls} style={inputStyle} value={form.mode} onChange={(e) => setForm({ ...form, mode: e.target.value })} /></Field><Field label="Reference"><input className={inputCls} style={inputStyle} value={form.reference} onChange={(e) => setForm({ ...form, reference: e.target.value })} /></Field><button className="btn btn-primary px-3 py-2 text-sm" onClick={save}>{editing ? "Update receipt" : "Record receipt"}</button>{editing && <button className="underline text-sm" onClick={() => { setEditing(null); setForm({ invoice_id: "", amount: "", date: todayISO(), mode: "Bank Transfer", reference: "" }); }}>Cancel</button>}</div></div>
    <div className="col-span-2"><table className="text-sm"><thead><tr className="text-left border-b"><th>Date</th><th>Invoice</th><th>Customer</th><th>Amount</th><th>Status</th><th></th></tr></thead><tbody>{receipts.map((r) => { const invoice = invoices.find((i) => i.id === r.invoice_id); const customer = customers.find((c) => c.id === invoice?.customer_id); return <tr className="border-b" key={r.id}><td className="py-2">{r.date}</td><td>{invoice?.invoice_no}</td><td>{invoice?.customer_name_snapshot || customer?.name}</td><td>₹{money(r.amount)}</td><td><Status value={r.status} /></td><td className="flex gap-2 py-2 text-xs">{r.status === "active" ? <><button className="underline" onClick={() => edit(r)}>Edit</button><button className="underline text-red-600" onClick={() => voidReceipt(r)}>Void</button></> : <button className="underline" onClick={() => restore(r)}>Restore</button>}</td></tr>; })}</tbody></table></div></div></div>;
}

function CreditNotes({ invoices, customers, creditNotes, balanceForInvoice, onChanged }) {
  const [invoiceId, setInvoiceId] = useState(""); const [date, setDate] = useState(todayISO()); const [reason, setReason] = useState(""); const [items, setItems] = useState([blankItem()]); const [message, setMessage] = useState({});
  const selected = invoices.find((i) => i.id === invoiceId); const issued = invoices.filter((i) => i.status === "issued" && balanceForInvoice(i).balance > 0);
  const update = (id, key, value) => setItems(items.map((i) => i.id === id ? { ...i, [key]: value } : i));
  const save = async () => { try { await api.createCreditNote(invoiceId, { date, reason, items: items.map(({ description, category, qty, rate }) => ({ description, category, qty: Number(qty), rate: Number(rate) })) }); setInvoiceId(""); setReason(""); setItems([blankItem()]); await onChanged(); setMessage({ success: "Credit note created." }); } catch (e) { setMessage({ error: e.message }); } };
  const cancel = async (note) => { const why = window.prompt("Reason for cancelling this credit note:"); if (!why) return; try { await api.cancelCreditNote(note.id, why); await onChanged(); } catch (e) { setMessage({ error: e.message }); } };
  return <div><SectionHeader title="Credit Notes" subtitle="Reduce issued invoices without rewriting their history." /><div className="p-8"><Message {...message} /><div className="card p-5 mb-6"><div className="grid grid-cols-3 gap-4"><Field label="Invoice"><select className={inputCls} style={inputStyle} value={invoiceId} onChange={(e) => setInvoiceId(e.target.value)}><option value="">Select issued invoice…</option>{issued.map((i) => <option key={i.id} value={i.id}>{i.invoice_no}</option>)}</select></Field><Field label="Date"><input type="date" className={inputCls} style={inputStyle} value={date} onChange={(e) => setDate(e.target.value)} /></Field><Field label="Reason"><input className={inputCls} style={inputStyle} value={reason} onChange={(e) => setReason(e.target.value)} /></Field></div>{selected && <div className="text-xs mt-2">Maximum current credit: ₹{money(balanceForInvoice(selected).balance)}</div>}
    <div className="mt-4 flex flex-col gap-2">{items.map((item) => <div className="grid grid-cols-12 gap-2" key={item.id}><input placeholder="Description" className={`${inputCls} col-span-4`} value={item.description} onChange={(e) => update(item.id, "description", e.target.value)} /><input placeholder="Category" className={`${inputCls} col-span-3`} value={item.category} onChange={(e) => update(item.id, "category", e.target.value)} /><input type="number" placeholder="Qty" className={`${inputCls} col-span-2`} value={item.qty} onChange={(e) => update(item.id, "qty", e.target.value)} /><input type="number" placeholder="Rate" className={`${inputCls} col-span-2`} value={item.rate} onChange={(e) => update(item.id, "rate", e.target.value)} /><button onClick={() => setItems(items.filter((i) => i.id !== item.id))}>×</button></div>)}</div><div className="flex gap-3 mt-3"><button className="btn btn-outline px-3 py-2 text-sm" onClick={() => setItems([...items, blankItem()])}>Add line</button><button disabled={!invoiceId} className="btn btn-primary px-3 py-2 text-sm" onClick={save}>Create credit note</button></div></div>
    <table className="text-sm"><thead><tr className="text-left border-b"><th>Date</th><th>Credit note</th><th>Invoice</th><th>Customer</th><th>Total</th><th>Status</th><th></th></tr></thead><tbody>{creditNotes.map((note) => { const invoice = invoices.find((i) => i.id === note.invoice_id); const customer = customers.find((c) => c.id === invoice?.customer_id); return <tr className="border-b" key={note.id}><td className="py-2">{note.date}</td><td>{note.credit_note_no}</td><td>{invoice?.invoice_no}</td><td>{invoice?.customer_name_snapshot || customer?.name}</td><td>₹{money(note.total)}</td><td><Status value={note.status} /></td><td><div className="flex gap-2 text-xs"><button className="underline" onClick={() => api.creditNotePdf(note.id, false)}>PDF</button>{note.status === "active" && <button className="underline text-red-600" onClick={() => cancel(note)}>Cancel</button>}</div></td></tr>; })}</tbody></table></div></div>;
}

function Receivables() {
  const [rows, setRows] = useState(null); const [error, setError] = useState("");
  useEffect(() => { api.receivablesReport().then(setRows).catch((e) => setError(e.message)); }, []);
  if (error) return <div className="p-8"><Message error={error} /></div>; if (!rows) return <div className="p-8">Loading…</div>;
  return <div><SectionHeader title="Receivable & Overdue" subtitle="Issued invoices less active receipts and credit notes." /><div className="p-8"><div className="mb-4">Total outstanding: <b>₹{money(rows.reduce((s, r) => s + Number(r.balance), 0))}</b></div><table className="text-sm"><thead><tr className="text-left border-b"><th>Invoice</th><th>Customer</th><th>Due date</th><th>Total</th><th>Paid</th><th>Credit</th><th>Balance</th><th>Ageing</th></tr></thead><tbody>{rows.map((r) => <tr className="border-b" key={r.invoice_id}><td className="py-2">{r.invoice_no}</td><td>{r.customer_name}</td><td>{r.due_date}</td><td>₹{money(r.invoice_total)}</td><td>₹{money(r.paid)}</td><td>₹{money(r.credited)}</td><td>₹{money(r.balance)}</td><td>{r.bucket}</td></tr>)}</tbody></table></div></div>;
}

function SalesReports() {
  const [area, setArea] = useState(null); const [product, setProduct] = useState(null); const [error, setError] = useState("");
  useEffect(() => { Promise.all([api.salesByArea(), api.salesByProduct()]).then(([a, p]) => { setArea(a); setProduct(p); }).catch((e) => setError(e.message)); }, []);
  const Chart = ({ title, rows }) => <div className="card p-5"><div className="text-[11px] uppercase text-slate-500 mb-4">{title} — pre-tax, net of credits</div>{rows?.map((r) => <div className="mb-3" key={r.key}><div className="flex justify-between text-sm"><span>{r.key}</span><span>₹{money(r.total)}</span></div><div className="h-2 rounded mt-1" style={{ background: "#EEE9DD" }}><div className="h-2 rounded" style={{ background: "#C9A227", width: `${rows[0]?.total ? Math.max(0, Number(r.total) / Number(rows[0].total) * 100) : 0}%` }} /></div></div>)}</div>;
  return <div><SectionHeader title="Sales Reports" subtitle="Current reports use a consistent pre-tax sales basis." /><div className="p-8"><Message error={error} />{!area ? "Loading…" : <div className="grid grid-cols-2 gap-6"><Chart title="Area-wise" rows={area} /><Chart title="Product / service-wise" rows={product} /></div>}</div></div>;
}
