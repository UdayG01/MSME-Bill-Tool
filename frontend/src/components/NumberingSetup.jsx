import React, { useEffect, useState } from "react";
import { api } from "../api";

export default function NumberingSetup() {
  const [setup, setSetup] = useState(null);
  const [next, setNext] = useState("");
  const [message, setMessage] = useState("");
  const load = () =>
    api
      .getNumberingSetup()
      .then((value) => {
        setSetup(value);
        setNext(value.next_invoice_number);
      })
      .catch((e) => setMessage(e.message));
  useEffect(() => {
    load();
  }, []);
  if (!setup) return <div className="p-8">{message || "Loading…"}</div>;
  const save = async () => {
    try {
      await api.setNumberingSetup({ next_invoice_number: Number(next) });
      await load();
      setMessage("Invoice numbering confirmed.");
    } catch (e) {
      setMessage(e.message);
    }
  };
  return (
    <div>
      <div className="px-8 pt-8 pb-5 border-b">
        <h1 className="serif text-2xl">Invoice Numbering</h1>
        <p className="text-sm text-slate-500">
          Invoice numbers reset to 0001 automatically at the start of each financial year.
        </p>
      </div>
      <div className="p-8 max-w-xl">
        <div className="card p-5">
          {message && <div className="mb-3 text-sm">{message}</div>}
          <div>
            Financial year: <b>{setup.financial_year}</b>
          </div>
          {setup.manual_setup_available && (
            <>
              <p className="text-sm text-slate-600 mt-3">
                Invoices will begin at 0001. If you have already issued invoices
                outside this app during this financial year, enter the next invoice
                number to continue from.
              </p>
              <label className="block mt-3">
                Next invoice number
                <input
                  type="number"
                  min="1"
                  className="w-full border rounded px-2 py-1"
                  value={next}
                  onChange={(e) => setNext(e.target.value)}
                />
              </label>
              <div className="text-sm mt-2">
                Preview: {setup.invoice_prefix}/{setup.financial_year}/
                {String(next || 1).padStart(4, "0")}
              </div>
              <button
                className="btn btn-primary px-3 py-2 text-sm mt-4"
                onClick={save}
              >
                Confirm invoice numbering
              </button>
            </>
          )}
          {!setup.manual_setup_available && (
            <div className="mt-3">
              Invoice numbering is active. The next invoice will be: {" "}
              <b>
                {setup.invoice_prefix}/{setup.financial_year}/
                {String(setup.next_invoice_number).padStart(4, "0")}
              </b>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
