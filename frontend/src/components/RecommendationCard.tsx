import { BarChart3, BadgeCheck, Sparkles } from 'lucide-react';

import type { SandboxRecommendation } from '../services/api';

interface RecommendationCardProps {
  result: SandboxRecommendation | null;
}

const money = new Intl.NumberFormat('en-MY', {
  style: 'currency',
  currency: 'MYR',
  maximumFractionDigits: 2,
});

export default function RecommendationCard({ result }: RecommendationCardProps) {
  if (!result) {
    return null;
  }

  const marginColor =
    (result.margin_percent ?? 0) >= 20
      ? 'text-emerald-700'
      : (result.margin_percent ?? 0) >= 10
        ? 'text-amber-700'
        : 'text-rose-700';

  const confidencePercent = (result.confidence * 100).toFixed(1);
  const confidenceColor =
    result.confidence >= 0.7 ? 'bg-emerald-500' : result.confidence >= 0.5 ? 'bg-amber-500' : 'bg-rose-500';

  return (
    <div className="mt-6 space-y-4">
      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-slate-600" aria-hidden="true" />
            <h3 className="text-lg font-semibold text-slate-950">AI Recommendation Result</h3>
          </div>
          {result.model_version && (
            <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-600">
              Model: {result.model_version}
            </span>
          )}
        </div>

        <div className="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Metric label="Recommended Price" value={money.format(result.predicted_price)} className="text-emerald-700" />
          <Metric
            label="Margin"
            value={result.margin_percent !== undefined ? `${result.margin_percent.toFixed(1)}%` : '-'}
            className={marginColor}
          />
          <Metric label="Confidence" value={`${confidencePercent}%`} className="text-slate-900" />
          <Metric label="Channel" value={result.channel || 'direct'} className="text-slate-900" />
        </div>

        <div className="mt-5">
          <div className="flex items-center justify-between text-xs font-medium text-slate-500">
            <span>Confidence</span>
            <span>{confidencePercent}%</span>
          </div>
          <div className="mt-2 h-2 w-full rounded-full bg-slate-100">
            <div
              className={`h-2 rounded-full transition-all ${confidenceColor}`}
              style={{ width: `${Math.min(100, result.confidence * 100)}%` }}
            />
          </div>
        </div>

        {result.unit_cost !== undefined && result.list_price !== undefined && (
          <div className="mt-5 grid gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700 md:grid-cols-3">
            <span>
              Unit cost: <strong>{money.format(result.unit_cost)}</strong>
            </span>
            <span>
              List price: <strong>{money.format(result.list_price)}</strong>
            </span>
            <span>
              AI price: <strong className="text-emerald-700">{money.format(result.predicted_price)}</strong>
            </span>
          </div>
        )}
      </section>

      {result.rationale && (
        <section className="rounded-lg border border-sky-200 bg-sky-50 p-5">
          <h4 className="flex items-center gap-2 text-sm font-semibold text-sky-900">
            <BadgeCheck className="h-4 w-4" aria-hidden="true" />
            Business Rationale
          </h4>
          <p className="mt-2 text-sm leading-6 text-sky-900">{result.rationale}</p>
        </section>
      )}

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h4 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
          <BarChart3 className="h-4 w-4" aria-hidden="true" />
          Explanation
        </h4>
        <p className="mt-2 text-sm leading-6 text-slate-600">{result.explanation}</p>
      </section>
    </div>
  );
}

function Metric({ label, value, className }: { label: string; value: string; className: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">{label}</p>
      <p className={`mt-2 truncate text-lg font-semibold ${className}`}>{value}</p>
    </div>
  );
}
