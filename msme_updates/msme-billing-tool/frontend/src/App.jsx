import React from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import CompanySetup from './pages/CompanySetup.jsx';
import LUTSetup from './pages/LUTSetup.jsx';
import Customers from './pages/Customers.jsx';
import CreateInvoice from './pages/CreateInvoice.jsx';
import InvoiceList from './pages/InvoiceList.jsx';
import ReceiptEntry from './pages/ReceiptEntry.jsx';
import AgeingReport from './pages/AgeingReport.jsx';

const navItems = [
  { to: '/', label: 'Invoices', end: true },
  { to: '/invoices/new', label: 'New Invoice' },
  { to: '/customers', label: 'Customers' },
  { to: '/receipts', label: 'Receipts' },
  { to: '/reports/ageing', label: 'Ageing Report' },
  { to: '/company', label: 'Company Setup' },
  { to: '/lut', label: 'LUT Master' },
];

function Layout({ children }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-brand-dark text-white">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between flex-wrap gap-2">
          <div className="font-bold text-lg">MSME Billing Utility</div>
          <nav className="flex gap-1 flex-wrap">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `px-3 py-1.5 rounded text-sm font-medium transition ${
                    isActive ? 'bg-white text-brand-dark' : 'text-white hover:bg-white/10'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-4 py-8">{children}</main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<InvoiceList />} />
          <Route path="/invoices/new" element={<CreateInvoice />} />
          <Route path="/customers" element={<Customers />} />
          <Route path="/receipts" element={<ReceiptEntry />} />
          <Route path="/reports/ageing" element={<AgeingReport />} />
          <Route path="/company" element={<CompanySetup />} />
          <Route path="/lut" element={<LUTSetup />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
