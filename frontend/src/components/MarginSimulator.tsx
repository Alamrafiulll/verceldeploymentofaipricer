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
    <section className="space-y-6 glass-card rounded-2xl p-6 border border-slate-200/60 dark:border-slate-800/60 shadow-sm transition-all duration-300">
      <div className="flex items-center justify-between gap-3">
        <h3 className="font-display text-base sm:text-lg font-extrabold tracking-tight text-slate-900 dark:text-white">What-If Margin View</h3>
        <p className="text-xs sm:text-sm font-semibold text-slate-500 dark:text-slate-400">Selected price: <span className="text-indigo-650 dark:text-indigo-400 font-extrabold">RM {value.toFixed(2)}</span></p>
      </div>

      <input
        type="range"
        min={min}
        max={max}
        step={0.1}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="w-full h-2 bg-slate-200 dark:bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/25"
      />

      <div className="grid grid-cols-2 gap-3.5 md:grid-cols-3">
        <Card label="Discount" value={`${selected.discount_percent.toFixed(2)}%`} />
        <Card label="True Margin" value={`${selected.margin_percent.toFixed(2)}%`} />
        <Card label="Win Probability" value={`${(selected.win_probability * 100).toFixed(1)}%`} />
        <Card label="Business Impact" value={`RM ${selected.expected_profit.toFixed(2)}`} />
        <Card label="Revenue" value={`RM ${(selected.price * 1).toFixed(2)}`} />
        <Card label="Pricing Compliance" value={selected.allowed ? 'Within guardrails' : 'Approval likely required'} />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div>
          <p className="mb-3 text-[10px] font-extrabold uppercase tracking-[0.16em] text-slate-400 dark:text-slate-500">
            Price vs Business Impact
          </p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={sorted} margin={{ top: 10, right: 10, bottom: 5, left: -20 }}>
                <CartesianGrid stroke="rgba(148, 163, 184, 0.08)" strokeDasharray="5 5" />
                <XAxis 
                  dataKey="price" 
                  tick={{ fontSize: 10, fontWeight: 'semibold', fill: '#94a3b8' }} 
                  axisLine={{ stroke: 'rgba(148, 163, 184, 0.15)' }}
                  tickLine={{ stroke: 'rgba(148, 163, 184, 0.15)' }}
                />
                <YAxis 
                  tick={{ fontSize: 10, fontWeight: 'semibold', fill: '#94a3b8' }} 
                  axisLine={{ stroke: 'rgba(148, 163, 184, 0.15)' }}
                  tickLine={{ stroke: 'rgba(148, 163, 184, 0.15)' }}
                />
                <Tooltip 
                  formatter={(val) => [`RM ${Number(val).toFixed(2)}`, 'Exp. Profit']}
                  contentStyle={{ 
                    borderRadius: 14, 
                    backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                    borderColor: 'rgba(255, 255, 255, 0.15)',
                    color: '#fff',
                    fontSize: 11,
                    fontWeight: 'bold',
                    backdropFilter: 'blur(8px)',
                    boxShadow: '0 10px 25px rgba(0,0,0,0.3)'
                  }}
                />
                <Line type="monotone" dataKey="expected_profit" stroke="#6366f1" strokeWidth={3} dot={false} activeDot={{ r: 5 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div>
          <p className="mb-3 text-[10px] font-extrabold uppercase tracking-[0.16em] text-slate-400 dark:text-slate-500">
            Price vs Win Probability
          </p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={sorted} margin={{ top: 10, right: 10, bottom: 5, left: -20 }}>
                <CartesianGrid stroke="rgba(148, 163, 184, 0.08)" strokeDasharray="5 5" />
                <XAxis 
                  dataKey="price" 
                  tick={{ fontSize: 10, fontWeight: 'semibold', fill: '#94a3b8' }} 
                  axisLine={{ stroke: 'rgba(148, 163, 184, 0.15)' }}
                  tickLine={{ stroke: 'rgba(148, 163, 184, 0.15)' }}
                />
                <YAxis 
                  domain={[0, 1]} 
                  tick={{ fontSize: 10, fontWeight: 'semibold', fill: '#94a3b8' }} 
                  axisLine={{ stroke: 'rgba(148, 163, 184, 0.15)' }}
                  tickLine={{ stroke: 'rgba(148, 163, 184, 0.15)' }}
                />
                <Tooltip 
                  formatter={(val) => [`${(Number(val) * 100).toFixed(1)}%`, 'Win Prob.']}
                  contentStyle={{ 
                    borderRadius: 14, 
                    backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                    borderColor: 'rgba(255, 255, 255, 0.15)',
                    color: '#fff',
                    fontSize: 11,
                    fontWeight: 'bold',
                    backdropFilter: 'blur(8px)',
                    boxShadow: '0 10px 25px rgba(0,0,0,0.3)'
                  }}
                />
                <Line type="monotone" dataKey="win_probability" stroke="#10b981" strokeWidth={3} dot={false} activeDot={{ r: 5 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </section>
  );
}

function Card({ label, value }: { label: string; value: string }) {
  const isHighAlert = value.toLowerCase().includes('required');
  return (
    <article className={`rounded-xl border p-3.5 transition-all duration-300 ${
      isHighAlert 
        ? 'border-amber-500/20 bg-amber-500/5 dark:bg-amber-950/10 text-amber-705 dark:text-amber-400' 
        : 'border-slate-200/60 dark:border-slate-800/40 bg-slate-500/5 dark:bg-slate-900/40'
    }`}>
      <p className="text-[10px] font-extrabold uppercase tracking-[0.16em] text-slate-400 dark:text-slate-500">{label}</p>
      <p className="mt-1.5 font-display text-sm font-bold tracking-tight text-slate-900 dark:text-white">{value}</p>
    </article>
  );
}
