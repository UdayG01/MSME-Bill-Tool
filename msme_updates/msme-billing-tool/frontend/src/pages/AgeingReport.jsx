import React, { useEffect, useState } from 'react';
import { api } from '../api/client.js';

export default function AgeingReport() {
  const [report, setReport] = useState(null);
  const [asOf, setAsOf] = useState(new Date().toISOString().slice(0, 10));

  const load = (date) => api.getAgeingReport(date).then(setReport).catch(() => {});
  useEffect(() => { load(asOf); }, []);

  const handleDateChange = (e) => {
    setAsOf(e.target.value);
    load(e.target.value);
  };

  const bucketColor = (label) => {
    if (label === 'Not due') return 'bg-green-50 text-green-800';
    if (label === '1-30 days') return 'bg-yellow-50 text-yellow-800';
    if (label === '31-60 days') return 'bg-orange-50 text-orange-800';
    return 'bg-red-50 text-red-800';
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold text-gray-800">Receivables Ageing Report</h1>
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">As of</label>
          <input type="date" value={asOf} onChange={handleDateChange} className="input-field w-auto" />
        </div>
      </div>

      <p className="text-sm text-gray-500">
        All figures shown in INR, including receivables from export invoices — internal reporting always uses the frozen INR equivalent recorded at invoice creation, regardless of the invoice's original currency.
      </p>

      {report && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {report.buckets.map((b) => (
              <div key={b.label} className={`rounded-lg p-4 ${bucketColor(b.label)}`}>
                <p className="text-xs font-medium uppercase tracking-wide">{b.label}</p>
                <p className="text-lg font-bold mt-1">INR {b.total_inr.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</p>
                <p className="text-xs mt-1">{b.count} invoice{b.count !== 1 ? 's' : ''}</p>
              </div>
            ))}
          </div>

          <div className="card">
            <p className="text-sm text-gray-600">Total Outstanding</p>
            <p className="text-2xl font-bold text-brand-dark mt-1">
              INR {report.total_outstanding_inr.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </p>
          </div>
        </>
      )}
    </div>
  );
}
