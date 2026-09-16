import React, { useState } from "react";
import { api } from "../api";
import { formatMoney } from "../utils/format";
import { Field, Message, SectionHeader, inputCls } from "./ui";

const blank = {
  name: "",
  description: "",
  hsn_sac: "",
  amount: "",
};

export default function Products({ products, onChanged }) {
  const [form, setForm] = useState(blank);
  const [editing, setEditing] = useState(null);
  const [showArchived, setShowArchived] = useState(false);
  const [message, setMessage] = useState({});

  const save = async () => {
    try {
      const payload = { ...form, amount: Number(form.amount || 0) };
      editing
        ? await api.updateProduct(editing, payload)
        : await api.createProduct(payload);
      setForm(blank);
      setEditing(null);
      await onChanged();
      setMessage({ success: "Product saved." });
    } catch (e) {
      setMessage({ error: e.message });
    }
  };

  const edit = (product) => {
    setEditing(product.id);
    setForm({
      name: product.name,
      description: product.description,
      hsn_sac: product.hsn_sac,
      amount: product.amount,
    });
  };

  const cancel = () => {
    setEditing(null);
    setForm(blank);
    setMessage({});
  };

  const toggle = async (product) => {
    try {
      product.is_archived
        ? await api.restoreProduct(product.id)
        : await api.archiveProduct(product.id);
      await onChanged();
    } catch (e) {
      setMessage({ error: e.message });
    }
  };

  const remove = async (product) => {
    if (!window.confirm(`Delete ${product.name}?`)) return;
    try {
      await api.deleteProduct(product.id);
      await onChanged();
    } catch (e) {
      setMessage({ error: e.message });
    }
  };

  const visible = products.filter((product) => showArchived || !product.is_archived);

  return (
    <div>
      <SectionHeader
        title="Products"
        subtitle="Reusable invoice items with HSN/SAC and default amount."
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
            <Field label="Product">
              <input
                className={inputCls}
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </Field>
            <Field label="Description">
              <textarea
                className={inputCls}
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
              />
            </Field>
            <Field label="HSN/SAC">
              <input
                className={inputCls}
                value={form.hsn_sac}
                onChange={(e) => setForm({ ...form, hsn_sac: e.target.value })}
              />
            </Field>
            <Field label="Amount">
              <input
                type="number"
                min="0"
                className={inputCls}
                value={form.amount}
                onChange={(e) => setForm({ ...form, amount: e.target.value })}
              />
            </Field>
            <div className="flex gap-2">
              <button className="btn btn-primary px-3 py-2 text-sm" onClick={save}>
                {editing ? "Update" : "Add"} product
              </button>
              {editing && (
                <button className="btn btn-outline px-3 py-2 text-sm" onClick={cancel}>
                  Cancel
                </button>
              )}
            </div>
          </div>
        </div>
        <div className="col-span-2 min-w-0 overflow-x-auto">
          <table className="text-sm table-fixed min-w-[760px]">
            <colgroup>
              <col className="w-[22%]" />
              <col className="w-[32%]" />
              <col className="w-[13%]" />
              <col className="w-[13%]" />
              <col className="w-[20%]" />
            </colgroup>
            <thead>
              <tr className="border-b text-left">
                <th className="px-3 pb-2">Product</th>
                <th className="px-3 pb-2">Description</th>
                <th className="px-3 pb-2">HSN/SAC</th>
                <th className="px-3 pb-2 text-right">Amount</th>
                <th className="px-3 pb-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((product) => (
                <tr className="border-b" key={product.id}>
                  <td className="px-3 py-2 break-words">{product.name}</td>
                  <td className="px-3 py-2 break-words">{product.description}</td>
                  <td className="px-3 py-2 break-words">{product.hsn_sac}</td>
                  <td className="px-3 py-2 text-right whitespace-nowrap">
                    INR {formatMoney(product.amount)}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap">
                    <button className="underline mr-2" onClick={() => edit(product)}>
                      Edit
                    </button>
                    <button className="underline mr-2" onClick={() => toggle(product)}>
                      {product.is_archived ? "Restore" : "Archive"}
                    </button>
                    <button className="underline text-red-600" onClick={() => remove(product)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {visible.length === 0 && (
                <tr>
                  <td className="px-3 py-6 text-slate-500" colSpan="5">
                    No products saved yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
