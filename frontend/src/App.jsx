import React, { useEffect, useState } from "react";
import { api } from "./api";
import AuthScreen from "./components/AuthScreen";
import BillingSettingsScreen from "./components/BillingSettings";
import CompanySetupScreen from "./components/CompanySetup";
import CreditNotesScreen from "./components/CreditNotes";
import CustomersScreen from "./components/Customers";
import DashboardScreen from "./components/Dashboard";
import InvoiceEditorScreen from "./components/InvoiceEditor";
import InvoiceRegisterScreen from "./components/InvoiceRegister";
import LutCertificatesScreen from "./components/LutCertificates";
import NumberingSetupScreen from "./components/NumberingSetup";
import ProductsScreen from "./components/Products";
import ReceiptsScreen from "./components/Receipts";
import ReceivablesScreen from "./components/Receivables";
import SalesReportsScreen from "./components/SalesReports";
import { Message } from "./components/ui";

const NAV = [
  ["dashboard", "Dashboard"],
  ["company", "Company Setup"],
  ["settings", "Billing Settings"],
  ["numbering", "Invoice Numbering"],
  ["lut", "LUT Certificates"],
  ["customers", "Customers"],
  ["products", "Products"],
  ["invoice", "New Invoice"],
  ["invoices", "Invoice Register"],
  ["receipts", "Receipt Entry"],
  ["credits", "Credit Notes"],
  ["receivables", "Receivable / Overdue"],
  ["sales", "Sales Reports"],
];

export default function App() {
  const [authed, setAuthed] = useState(null);
  const [tab, setTab] = useState("dashboard");
  const [company, setCompany] = useState(null);
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [receipts, setReceipts] = useState([]);
  const [creditNotes, setCreditNotes] = useState([]);
  const [editingInvoice, setEditingInvoice] = useState(null);
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    api
      .me()
      .then(() => setAuthed(true))
      .catch(() => setAuthed(false));
  }, []);

  const loadAll = async () => {
    setLoadError("");
    try {
      const [
        companyData,
        customersData,
        productsData,
        invoicesData,
        receiptsData,
        creditNotesData,
      ] = await Promise.all([
        api.getCompany(),
        api.listCustomers(true),
        api.listProducts(true),
        api.listInvoices(),
        api.listReceipts(),
        api.listCreditNotes(),
      ]);
      setCompany(companyData);
      setCustomers(customersData);
      setProducts(productsData);
      setInvoices(invoicesData);
      setReceipts(receiptsData);
      setCreditNotes(creditNotesData);
    } catch (error) {
      setLoadError(error.message);
    }
  };

  useEffect(() => {
    if (authed) loadAll();
  }, [authed]);

  const balanceForInvoice = (invoice) => {
    if (invoice.status !== "issued")
      return { paid: 0, credited: 0, balance: 0 };

    const paid = receipts
      .filter(
        (receipt) =>
          receipt.invoice_id === invoice.id && receipt.status === "active",
      )
      .reduce(
        (sum, receipt) =>
          sum + Number(receipt.applied_amount_inr ?? receipt.amount),
        0,
      );
    const credited = creditNotes
      .filter(
        (note) => note.invoice_id === invoice.id && note.status === "active",
      )
      .reduce((sum, note) => sum + Number(note.total), 0);

    return { paid, credited, balance: Number(invoice.total) - paid - credited };
  };

  const editDraft = (invoice) => {
    setEditingInvoice(invoice);
    setTab("invoice");
  };

  const logout = async () => {
    await api.logout();
    setAuthed(false);
  };

  if (authed === null) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        Loading…
      </div>
    );
  }

  if (!authed) return <AuthScreen onAuthed={() => setAuthed(true)} />;

  if (!company) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div>
          <Message error={loadError} />
          <span>Loading your ledger…</span>
        </div>
      </div>
    );
  }

  return (
    <div
      className="w-full min-h-screen flex"
      style={{
        background: "#F5F3EE",
        color: "#1C2B39",
        fontFamily: "Inter, -apple-system, sans-serif",
      }}
    >
      <style>{`.serif{font-family:Georgia,'Times New Roman',serif}.tnum{font-variant-numeric:tabular-nums}input:focus,select:focus,textarea:focus{outline:2px solid #C9A227;outline-offset:1px}table{border-collapse:collapse;width:100%}.btn{border-radius:4px;font-weight:600}.btn:disabled{opacity:.45}.btn-primary{background:#1C2B39;color:#F5F3EE}.btn-outline{border:1px solid #1C2B39;color:#1C2B39;background:transparent}.btn-danger{background:#B4472A;color:white}.card{background:#FFF;border:1px solid #E4DFD3;border-radius:6px}`}</style>
      <aside className="w-60 shrink-0" style={{ background: "#1C2B39" }}>
        <div className="px-5 py-6 border-b" style={{ borderColor: "#2A3D4F" }}>
          <div className="serif text-lg text-white">
            Bill<span style={{ color: "#C9A227" }}>Ops</span>
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">
            {company.company_name}
          </div>
        </div>
        <nav className="py-3">
          {NAV.map(([id, label]) => (
            <button
              key={id}
              className="w-full px-5 py-2.5 text-[13px] text-left"
              style={{
                background: tab === id ? "#0F1C28" : "transparent",
                color: tab === id ? "#C9A227" : "#C7CDD3",
                borderLeft:
                  tab === id ? "3px solid #C9A227" : "3px solid transparent",
              }}
              onClick={() => {
                setTab(id);
                if (id === "invoice") setEditingInvoice(null);
              }}
            >
              {label}
            </button>
          ))}
        </nav>
        <button
          className="mx-5 mt-4 text-[12px] text-slate-400 underline"
          onClick={logout}
        >
          Log out
        </button>
      </aside>
      <main className="flex-1 min-w-0 overflow-y-auto">
        {loadError && (
          <div className="m-4">
            <Message error={loadError} />
          </div>
        )}
        {tab === "dashboard" && (
          <DashboardScreen
            invoices={invoices}
            customers={customers}
            balanceForInvoice={balanceForInvoice}
            setTab={setTab}
          />
        )}
        {tab === "company" && (
          <CompanySetupScreen company={company} onSaved={loadAll} />
        )}
        {tab === "settings" && <BillingSettingsScreen />}
        {tab === "numbering" && <NumberingSetupScreen />}
        {tab === "lut" && <LutCertificatesScreen />}
        {tab === "customers" && (
          <CustomersScreen customers={customers} onChanged={loadAll} />
        )}
        {tab === "products" && (
          <ProductsScreen products={products} onChanged={loadAll} />
        )}
        {tab === "invoice" && (
          <InvoiceEditorScreen
            customers={customers}
            products={products.filter((product) => !product.is_archived)}
            invoice={editingInvoice}
            onSaved={loadAll}
            onAddProduct={() => setTab("products")}
            onDone={() => {
              setEditingInvoice(null);
              setTab("invoices");
            }}
          />
        )}
        {tab === "invoices" && (
          <InvoiceRegisterScreen
            invoices={invoices}
            customers={customers}
            balanceForInvoice={balanceForInvoice}
            onChanged={loadAll}
            onEdit={editDraft}
          />
        )}
        {tab === "receipts" && (
          <ReceiptsScreen
            invoices={invoices}
            receipts={receipts}
            balanceForInvoice={balanceForInvoice}
            onChanged={loadAll}
          />
        )}
        {tab === "credits" && (
          <CreditNotesScreen
            invoices={invoices}
            creditNotes={creditNotes}
            balanceForInvoice={balanceForInvoice}
            onChanged={loadAll}
          />
        )}
        {tab === "receivables" && <ReceivablesScreen />}
        {tab === "sales" && <SalesReportsScreen />}
      </main>
    </div>
  );
}
