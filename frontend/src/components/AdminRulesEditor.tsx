import { useState } from 'react';

import type { Rule } from '../types/api';

interface Props {
  rules: Rule[];
  onSave: (payload: {
    channel: string;
    category: string;
    margin_floor_percent: number;
    max_discount_percent: number;
    approval_required_below_margin_buffer: number;
  }) => Promise<void>;
  loading: boolean;
}

export default function AdminRulesEditor({ rules, onSave, loading }: Props) {
  const [form, setForm] = useState({
    channel: 'direct',
    category: 'cement',
    margin_floor_percent: 12,
    max_discount_percent: 10,
    approval_required_below_margin_buffer: 2,
  });

  return (
    <div className="space-y-4 rounded-2xl border border-white/70 bg-white p-4 shadow-card">
      <h3 className="font-display text-lg font-semibold">Pricing Rules</h3>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
        <input
          className="input"
          value={form.channel}
          onChange={(event) => setForm((prev) => ({ ...prev, channel: event.target.value }))}
          placeholder="channel"
        />
        <input
          className="input"
          value={form.category}
          onChange={(event) => setForm((prev) => ({ ...prev, category: event.target.value }))}
          placeholder="category"
        />
        <input
          className="input"
          type="number"
          value={form.margin_floor_percent}
          onChange={(event) =>
            setForm((prev) => ({ ...prev, margin_floor_percent: Number(event.target.value) }))
          }
          placeholder="margin floor"
        />
        <input
          className="input"
          type="number"
          value={form.max_discount_percent}
          onChange={(event) =>
            setForm((prev) => ({ ...prev, max_discount_percent: Number(event.target.value) }))
          }
          placeholder="max discount"
        />
        <input
          className="input"
          type="number"
          value={form.approval_required_below_margin_buffer}
          onChange={(event) =>
            setForm((prev) => ({ ...prev, approval_required_below_margin_buffer: Number(event.target.value) }))
          }
          placeholder="approval buffer"
        />
      </div>

      <button
        className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
        disabled={loading}
        onClick={() => onSave(form)}
      >
        {loading ? 'Saving...' : 'Save Rule'}
      </button>

      <div className="overflow-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-slate-600">
              <th className="py-2 pr-3">Channel</th>
              <th className="py-2 pr-3">Category</th>
              <th className="py-2 pr-3">Margin Floor %</th>
              <th className="py-2 pr-3">Max Discount %</th>
              <th className="py-2 pr-3">Approval Buffer %</th>
            </tr>
          </thead>
          <tbody>
            {rules.map((rule) => (
              <tr key={rule.id} className="border-b border-slate-100">
                <td className="py-2 pr-3">{rule.channel}</td>
                <td className="py-2 pr-3">{rule.category}</td>
                <td className="py-2 pr-3">{rule.margin_floor_percent}</td>
                <td className="py-2 pr-3">{rule.max_discount_percent}</td>
                <td className="py-2 pr-3">{rule.approval_required_below_margin_buffer}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
