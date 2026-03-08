import { useMemo } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import type { CandidatePoint } from '../types/api';

interface Props {
  candidates: CandidatePoint[];
  value: number;
  onChange: (value: number) => void;
}

export default function MarginSimulator({ candidates, value, onChange }: Props) {
  const sorted = useMemo(() => [...candidates].sort((a, b) => a.price - b.price), [candidates]);

  const min = sorted[0]?.price ?? 0;
  const max = sorted[sorted.length - 1]?.price ?? 0;

  const selected = useMemo(() => {
    if (!sorted.length) return null;
    return sorted.reduce((prev, curr) =>
      Math.abs(curr.price - value) < Math.abs(prev.price - value) ? curr : prev,
    );
  }, [sorted, value]);

  if (!sorted.length || !selected) {
    return null;
  }

  return (
    <section className="space-y-4 rounded-2xl border border-white/70 bg-white p-5 shadow-card">
      <div className="flex items-center justify-between">
        <h3 className="font-display text-lg font-semibold">What-If Margin View</h3>
        <p className="text-sm text-slate-600">Selected price: RM {value.toFixed(2)}</p>
      </div>

      <input
        type="range"
        min={min}
        max={max}
        step={0.1}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="w-full"
      />

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
        <Card label="Discount" value={`${selected.discount_percent.toFixed(2)}%`} />
        <Card label="True Margin" value={`${selected.margin_percent.toFixed(2)}%`} />
        <Card label="Win Probability" value={`${(selected.win_probability * 100).toFixed(1)}%`} />
        <Card label="Business Impact" value={`RM ${selected.expected_profit.toFixed(2)}`} />
        <Card label="Revenue" value={`RM ${(selected.price * 1).toFixed(2)}`} />
        <Card label="Pricing Compliance" value={selected.allowed ? 'Within guardrails' : 'Approval likely required'} />
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Price vs Business Impact
          </p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={sorted}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="price" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="expected_profit" stroke="#0f172a" strokeWidth={2.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Price vs Win Probability
          </p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={sorted}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="price" />
                <YAxis domain={[0, 1]} />
                <Tooltip />
                <Line type="monotone" dataKey="win_probability" stroke="#1A8F5B" strokeWidth={2.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </section>
  );
}

function Card({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
      <p className="text-[11px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-semibold text-slate-900">{value}</p>
    </article>
  );
}
