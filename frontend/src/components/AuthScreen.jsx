import React, { useState } from "react";
import { api } from "../api";
import { Field, Message, inputCls, inputStyle } from "./ui";
export default function AuthScreen({ onAuthed }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({
    company_name: "",
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async (event) => {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      mode === "signup" ? await api.signup(form) : await api.login(form);
      onAuthed();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div
      className="min-h-screen flex items-center justify-center"
      style={{ background: "#F5F3EE" }}
    >
      <div className="card p-8 w-full max-w-sm">
        <div className="serif text-xl mb-1">
          Bill<span style={{ color: "#C9A227" }}>Ops</span>
        </div>
        <div className="text-[13px] text-slate-500 mb-6">
          Billing &amp; Receivable Control
        </div>
        <form className="flex flex-col gap-3" onSubmit={submit}>
          {mode === "signup" && (
            <Field label="Company name">
              <input
                required
                autoComplete="organization"
                className={inputCls}
                style={inputStyle}
                value={form.company_name}
                onChange={(e) =>
                  setForm({ ...form, company_name: e.target.value })
                }
              />
            </Field>
          )}
          <Field label="Email">
            <input
              required
              type="email"
              autoComplete="email"
              className={inputCls}
              style={inputStyle}
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
          </Field>
          <Field label="Password">
            <input
              required
              type="password"
              autoComplete={mode === "signup" ? "new-password" : "current-password"}
              className={inputCls}
              style={inputStyle}
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
          </Field>
          <Message error={error} />
          <button
            type="submit"
            className="btn btn-primary text-sm px-3 py-2"
            disabled={busy}
          >
            {busy
              ? "Please wait…"
              : mode === "signup"
                ? "Create account"
                : "Log in"}
          </button>
          <button
            type="button"
            className="text-[12px] text-slate-500 underline"
            onClick={() => setMode(mode === "signup" ? "login" : "signup")}
          >
            {mode === "signup"
              ? "Already have an account? Log in"
              : "New company? Sign up"}
          </button>
        </form>
      </div>
    </div>
  );
}
