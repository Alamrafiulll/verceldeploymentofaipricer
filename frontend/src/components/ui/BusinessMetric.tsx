interface BusinessMetricProps {
  label: string;
  value: string | number;
  unit?: string;
  subLabel?: string;
  highlight?: 'good' | 'caution' | 'bad' | 'neutral';
}

const HIGHLIGHT_COLORS = {
  good: 'text-emerald-700',
  caution: 'text-amber-600',
  bad: 'text-red-600',
  neutral: 'text-slate-800',
};

export default function BusinessMetric({
  label,
  value,
  unit,
  subLabel,
  highlight = 'neutral',
}: BusinessMetricProps) {
  return (
    <div className="rounded-lg bg-slate-50 p-3 text-center">
      <p className="text-[11px] font-medium uppercase tracking-wider text-slate-500">{label}</p>
      <p className={`mt-1 text-xl font-bold ${HIGHLIGHT_COLORS[highlight]}`}>
        {unit && <span className="text-sm font-normal">{unit} </span>}
        {typeof value === 'number' ? value.toLocaleString() : value}
      </p>
      {subLabel && <p className="mt-0.5 text-[10px] text-slate-400">{subLabel}</p>}
    </div>
  );
}
