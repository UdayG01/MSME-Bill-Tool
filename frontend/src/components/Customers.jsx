import React, { useState } from "react";
import { api } from "../api";
import { Field, Message, SectionHeader, inputCls, inputStyle } from "./ui";
const blank = {
  name: "",
  address: "",
  gstin: "",
  country: "India",
  is_foreign: false,
  area: "",
  state_code: "",
  credit_days: "",
};
export default function Customers({ customers, onChanged }) {
  const [form, setForm] = useState(blank);
  const [editing, setEditing] = useState(null);
  const [showArchived, setShowArchived] = useState(false);
  const [message, setMessage] = useState({});
  const save = async () => {
    try {
      editing
        ? await api.updateCustomer(editing, form)
        : await api.createCustomer(form);
      setForm(blank);
      setEditing(null);
      await onChanged();
      setMessage({ success: "Customer saved." });
    } catch (e) {
      setMessage({ error: e.message });
    }
  };
  const edit = (c) => {
    setEditing(c.id);
    setForm({
      name: c.name,
      address: c.address,
      gstin: c.gstin,
      country: c.country,
      is_foreign: c.is_foreign,
      area: c.area,
      state_code: c.state_code,
      credit_days: c.credit_days,
    });
  };
  const toggle = async (c) => {
    try {
      c.is_archived
        ? await api.restoreCustomer(c.id)
        : await api.archiveCustomer(c.id);
      await onChanged();
    } catch (e) {
      setMessage({ error: e.message });
    }
  };
  const visible = customers.filter((c) => showArchived || !c.is_archived);
  return (
    <div>
      <SectionHeader
        title="Customers"
        subtitle="Edit active customers or archive them without breaking history."
        right={
          <label>
            <input
              type="checkbox"
              checked={showArchived}
              onChange={(e) => setShowArchived(e.target.checked)}
            />{" "}
            Show archived
          </label>
        }
      />
      <div className="p-8 grid grid-cols-3 gap-6">
        <div className="card p-5 h-fit">
          <Message {...message} />
          <div className="flex flex-col gap-3">
            <Field label="Name">
              <input
                className={inputCls}
                style={inputStyle}
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </Field>
            <Field label="Address">
              <textarea
                className={inputCls}
                value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
              />
            </Field>
            <label>
              <input
                type="checkbox"
                checked={form.is_foreign}
                onChange={(e) =>
                  setForm({
                    ...form,
                    is_foreign: e.target.checked,
                    gstin: e.target.checked ? "" : form.gstin,
                    state_code: e.target.checked ? "" : form.state_code,
                    country: e.target.checked ? "" : form.country,
                  })
                }
              />{" "}
              Foreign customer
            </label>
            <Field label={form.is_foreign ? "Country" : "GSTIN"}>
              <input
                className={inputCls}
                value={form.is_foreign ? form.country : form.gstin}
                onChange={(e) =>
                  setForm(
                    form.is_foreign
                      ? { ...form, country: e.target.value }
                      : { ...form, gstin: e.target.value },
                  )
                }
              />
            </Field>
            <Field label="Area">
              <input
                className={inputCls}
                value={form.area}
                onChange={(e) => setForm({ ...form, area: e.target.value })}
              />
            </Field>
            <Field label="Payment Terms (days)">
              <input
                type="number"
                min="0"
                className={inputCls}
                value={form.credit_days}
                onChange={(e) =>
                  setForm({ ...form, credit_days: Number(e.target.value) })
                }
              />
            </Field>
            <button
              className="btn btn-primary px-3 py-2 text-sm"
              onClick={save}
            >
              {editing ? "Update" : "Add"} customer
            </button>
          </div>
        </div>
        <div className="col-span-2 min-w-0 overflow-x-auto">
          <table className="text-sm table-fixed min-w-[640px]">
            <colgroup>
              <col className="w-[30%]" />
              <col className="w-[18%]" />
              <col className="w-[18%]" />
              <col className="w-[16%]" />
              <col className="w-[18%]" />
            </colgroup>
            <thead>
              <tr className="border-b text-left">
                <th className="px-3 pb-2">Name</th>
                <th className="px-3 pb-2">Country</th>
                <th className="px-3 pb-2">Area</th>
                <th className="px-3 pb-2">Terms</th>
                <th className="px-3 pb-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((c) => (
                <tr className="border-b" key={c.id}>
                  <td className="px-3 py-2 break-words">{c.name}</td>
                  <td className="px-3 py-2 break-words">{c.country}</td>
                  <td className="px-3 py-2 break-words">{c.area}</td>
                  <td className="px-3 py-2 whitespace-nowrap">
                    {c.credit_days} days
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap">
                    <button className="underline mr-2" onClick={() => edit(c)}>
                      Edit
                    </button>
                    <button className="underline" onClick={() => toggle(c)}>
                      {c.is_archived ? "Restore" : "Archive"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
