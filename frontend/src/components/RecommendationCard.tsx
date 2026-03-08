import type { SandboxRecommendation } from '../services/api';

interface RecommendationCardProps {
  result: SandboxRecommendation | null;
}

export default function RecommendationCard({ result }: RecommendationCardProps) {
  if (!result) {
    return null;
  }

  const marginColor =
    (result.margin_percent ?? 0) >= 20
      ? 'text-emerald-700'
      : (result.margin_percent ?? 0) >= 10
        ? 'text-amber-600'
        : 'text-red-600';

  const confidencePercent = (result.confidence * 100).toFixed(1);
  const confidenceColor =
    result.confidence >= 0.7 ? 'bg-emerald-500' : result.confidence >= 0.5 ? 'bg-amber-500' : 'bg-red-500';

  return (
    <div className="mt-6 space-y-4">
      {/* Main Recommendation */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-900">🤖 AI Recommendation</h3>
          {result.model_version && (
            <span className="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-medium text-slate-500">
              Model: {result.model_version}
            </span>
          )}
        </div>

        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-lg bg-emerald-50 p-3 text-center">
            <p className="text-[11px] font-medium text-emerald-600">Recommended Price</p>
            <p className="mt-1 text-xl font-bold text-emerald-700">
              RM {result.predicted_price.toFixed(2)}
            </p>
          </div>
          <div className="rounded-lg bg-slate-50 p-3 text-center">
            <p className="text-[11px] font-medium text-slate-500">Margin</p>
            <p className={`mt-1 text-xl font-bold ${marginColor}`}>
              {result.margin_percent !== undefined ? `${result.margin_percent.toFixed(1)}%` : '—'}
            </p>
          </div>
          <div className="rounded-lg bg-slate-50 p-3 text-center">
            <p className="text-[11px] font-medium text-slate-500">Confidence</p>
            <p className="mt-1 text-xl font-bold text-slate-800">{confidencePercent}%</p>
          </div>
          <div className="rounded-lg bg-slate-50 p-3 text-center">
            <p className="text-[11px] font-medium text-slate-500">Channel</p>
            <p className="mt-1 text-sm font-bold capitalize text-slate-800">
              {result.channel || 'direct'}
            </p>
          </div>
        </div>

        {/* Confidence Bar */}
        <div className="mt-4">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>AI Confidence</span>
            <span>{confidencePercent}%</span>
          </div>
          <div className="mt-1 h-2 w-full rounded-full bg-slate-100">
            <div
              className={`h-2 rounded-full transition-all ${confidenceColor}`}
              style={{ width: `${Math.min(100, result.confidence * 100)}%` }}
            />
          </div>
        </div>

        {/* Cost-Price Breakdown */}
        {result.unit_cost !== undefined && result.list_price !== undefined && (
          <div className="mt-4 flex gap-4 text-xs text-slate-600">
            <span>
              Unit Cost: <strong>RM {result.unit_cost.toFixed(2)}</strong>
            </span>
            <span>
              List Price: <strong>RM {result.list_price.toFixed(2)}</strong>
            </span>
            <span>
              AI Price: <strong className="text-emerald-700">RM {result.predicted_price.toFixed(2)}</strong>
            </span>
          </div>
        )}
      </div>

      {/* Smart "Why" Rationale */}
      {result.rationale && (
        <div className="rounded-xl border border-blue-200 bg-blue-50 p-5">
          <h4 className="flex items-center gap-2 text-sm font-semibold text-blue-800">
            💡 Smart &quot;Why&quot; Rationale
          </h4>
          <p className="mt-2 text-sm leading-relaxed text-blue-900">{result.rationale}</p>
        </div>
      )}

      {/* Basic Explanation */}
      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <p className="text-sm text-slate-600">{result.explanation}</p>
      </div>
    </div>
  );
}
