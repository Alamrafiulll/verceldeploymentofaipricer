import type { Kpis } from '../types/api';

interface Props {
  data: Kpis;
}

export default function KpiCards({ data }: Props) {
  const items = [
    { label: 'Pricing Health Score', value: data.pricing_health_score.toFixed(1) },
    { label: 'Avg True Margin', value: `${data.average_margin_percent.toFixed(2)}%` },
    { label: 'Avg Decision Time', value: `${data.average_decision_time_hours.toFixed(2)}h` },
    { label: 'Avg Leakage', value: `RM ${data.average_leakage_amount.toFixed(2)}` },
    {
      label: 'Recommendation Acceptance',
      value: `${(data.recommendation_acceptance_rate * 100).toFixed(1)}%`,
    },
    { label: 'Override Rate', value: `${(data.override_rate * 100).toFixed(1)}%` },
    { label: 'Approval Rate', value: `${(data.approval_rate * 100).toFixed(1)}%` },
    { label: 'Win Rate Proxy', value: `${(data.win_rate_proxy * 100).toFixed(1)}%` },
    {
      label: 'Inventory Value Addressed',
      value: `RM ${data.aging_inventory_addressed_value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`,
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {items.map((item) => (
        <article key={item.label} className="rounded-xl border border-white/80 bg-white/90 p-4 shadow-card">
          <p className="text-xs uppercase tracking-wide text-slate-500">{item.label}</p>
          <p className="mt-2 font-display text-2xl font-semibold">{item.value}</p>
        </article>
      ))}
    </div>
  );
}
