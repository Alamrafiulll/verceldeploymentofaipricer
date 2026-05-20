import { useMemo, useState } from 'react';
import { CheckCircle2, Plus, ShieldCheck, SlidersHorizontal } from 'lucide-react';

import { EmptyState, StatusChip } from './ui';
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

const FIELD_CLASS =
  'w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm outline-none ring-slate-900/20 transition focus:border-slate-900 focus:ring-2';

export default function AdminRulesEditor({ rules, onSave, loading }: Props) {
  const [form, setForm] = useState({
    channel: 'direct',
    category: 'cement',
    margin_floor_percent: 12,
    max_discount_percent: 10,
    approval_required_below_margin_buffer: 2,
  });

  const categories = useMemo(() => new Set(rules.map((rule) => rule.category)).size, [rules]);
  const strictRules = useMemo(
    () => rules.filter((rule) => rule.margin_floor_percent >= 15 || rule.max_discount_percent <= 5).length,
    [rules],
  );

  return (
    <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-slate-50 text-slate-700">
              <SlidersHorizontal className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <h2 className="text-lg font-semibold text-slate-950">Pricing Guardrails</h2>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                Govern margin floors, discount ceilings, and approval thresholds by channel and category.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <StatusChip status={`${rules.length} rules`} variant="info" size="md" />
            <StatusChip status={`${categories} categories`} variant="success" size="md" />
          </div>
        </div>
      </div>

      <div className="grid gap-5 p-5 xl:grid-cols-[360px_minmax(0,1fr)]">
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
          <div className="mb-4 flex items-center gap-2">
            <Plus className="h-4 w-4 text-slate-500" aria-hidden="true" />
            <h3 className="text-sm font-semibold text-slate-900">Add or Update Rule</h3>
          </div>

          <div className="space-y-4">
            <label className="block text-sm">
              <span className="font-medium text-slate-700">Channel</span>
              <input
                className={`${FIELD_CLASS} mt-1`}
                value={form.channel}
                onChange={(event) => setForm((prev) => ({ ...prev, channel: event.target.value }))}
                placeholder="direct"
              />
            </label>
            <label className="block text-sm">
              <span className="font-medium text-slate-700">Category</span>
              <input
                className={`${FIELD_CLASS} mt-1`}
                value={form.category}
                onChange={(event) => setForm((prev) => ({ ...prev, category: event.target.value }))}
                placeholder="cement"
              />
            </label>
            <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
              <RuleNumberField
                label="Margin floor"
                suffix="%"
                value={form.margin_floor_percent}
                onChange={(value) => setForm((prev) => ({ ...prev, margin_floor_percent: value }))}
              />
              <RuleNumberField
                label="Max discount"
                suffix="%"
                value={form.max_discount_percent}
                onChange={(value) => setForm((prev) => ({ ...prev, max_discount_percent: value }))}
              />
              <RuleNumberField
                label="Approval buffer"
                suffix="%"
                value={form.approval_required_below_margin_buffer}
                onChange={(value) =>
                  setForm((prev) => ({ ...prev, approval_required_below_margin_buffer: value }))
                }
              />
            </div>
          </div>

          <button
            type="button"
            className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:opacity-60"
            disabled={loading}
            onClick={() => onSave(form)}
          >
            <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
            {loading ? 'Saving rule...' : 'Save guardrail'}
          </button>
        </div>

        <div className="min-w-0">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Active Rule Matrix</h3>
              <p className="mt-1 text-sm text-slate-600">{strictRules} strict controls currently active.</p>
            </div>
            <ShieldCheck className="h-5 w-5 text-slate-400" aria-hidden="true" />
          </div>

          {rules.length === 0 ? (
            <EmptyState
              icon={<SlidersHorizontal className="h-6 w-6" aria-hidden="true" />}
              title="No pricing guardrails"
              description="Create a rule to start controlling margins, discounts, and approval thresholds."
            />
          ) : (
            <div className="overflow-x-auto rounded-lg border border-slate-200">
              <table className="w-full min-w-[760px] text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                    <th className="px-4 py-3">Channel</th>
                    <th className="px-4 py-3">Category</th>
                    <th className="px-4 py-3">Margin Floor</th>
                    <th className="px-4 py-3">Max Discount</th>
                    <th className="px-4 py-3">Approval Buffer</th>
                    <th className="px-4 py-3">Control</th>
                  </tr>
                </thead>
                <tbody>
                  {rules.map((rule) => {
                    const strict = rule.margin_floor_percent >= 15 || rule.max_discount_percent <= 5;
                    return (
                      <tr key={rule.id} className="border-b border-slate-100 last:border-0">
                        <td className="px-4 py-3 font-semibold text-slate-900">{rule.channel}</td>
                        <td className="px-4 py-3 text-slate-700">{rule.category}</td>
                        <td className="px-4 py-3 text-slate-700">{rule.margin_floor_percent.toFixed(1)}%</td>
                        <td className="px-4 py-3 text-slate-700">{rule.max_discount_percent.toFixed(1)}%</td>
                        <td className="px-4 py-3 text-slate-700">
                          {rule.approval_required_below_margin_buffer.toFixed(1)}%
                        </td>
                        <td className="px-4 py-3">
                          <StatusChip status={strict ? 'strict' : 'standard'} variant={strict ? 'warning' : 'info'} />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function RuleNumberField({
  label,
  value,
  suffix,
  onChange,
}: {
  label: string;
  value: number;
  suffix: string;
  onChange: (value: number) => void;
}) {
  return (
    <label className="block text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <div className="mt-1 flex overflow-hidden rounded-lg border border-slate-300 bg-white focus-within:border-slate-900 focus-within:ring-2 focus-within:ring-slate-900/20">
        <input
          className="min-w-0 flex-1 px-3.5 py-2.5 text-sm outline-none"
          type="number"
          value={value}
          onChange={(event) => onChange(Number(event.target.value))}
        />
        <span className="inline-flex items-center border-l border-slate-200 px-3 text-sm font-semibold text-slate-500">
          {suffix}
        </span>
      </div>
    </label>
  );
}
