import type { Recommendation } from '../types/api';
import RiskBadge from './RiskBadge';

interface Props {
  recommendation: Recommendation;
}

function formatLabel(value: string) {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

export default function RecommendationPanel({ recommendation }: Props) {
  const zoneStyle = {
    green: 'border-emerald-500/25 bg-emerald-500/5 shadow-emerald-500/5 shadow-xl',
    yellow: 'border-amber-500/25 bg-amber-500/5 shadow-amber-500/5 shadow-xl',
    red: 'border-rose-500/25 bg-rose-500/5 shadow-rose-500/5 shadow-xl',
  }[recommendation.safe_band];
  const marketSummary =
    typeof recommendation.market_comparison_summary?.market_comparison_summary === 'string'
      ? recommendation.market_comparison_summary.market_comparison_summary
      : null;

  return (
    <section className={`rounded-2xl border p-6 backdrop-blur-md transition-all duration-300 ${zoneStyle}`}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="font-display text-lg sm:text-xl font-extrabold tracking-tight text-slate-900 dark:text-white">
          Recommended Price and Safe Trading Range
        </h3>
        <RiskBadge level={recommendation.risk_level} />
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3.5 md:grid-cols-4">
        <Metric
          label="Recommended Range"
          value={`RM ${recommendation.band_low.toFixed(2)} - RM ${recommendation.band_high.toFixed(2)}`}
        />
        <Metric label="Recommended Price" value={`RM ${recommendation.best_price.toFixed(2)}`} />
        <Metric label="Business Impact" value={`RM ${recommendation.expected_profit.toFixed(2)}`} />
        <Metric
          label="Win Probability"
          value={`${(recommendation.win_probability * 100).toFixed(1)}%`}
        />
        <Metric
          label="Suggested Discount Band"
          value={`${recommendation.suggested_discount_low.toFixed(1)}% - ${recommendation.suggested_discount_high.toFixed(1)}%`}
        />
        <Metric label="True Margin" value={`${recommendation.margin_percent.toFixed(2)}%`} />
        <Metric
          label="Recommendation Confidence"
          value={`${(recommendation.confidence * 100).toFixed(1)}%`}
        />
        <Metric label="Policy Zone" value={recommendation.safe_band.toUpperCase()} />
      </div>

      {recommendation.value_positioning_label || recommendation.next_best_action || marketSummary ? (
        <div className="mt-4 grid gap-3.5 md:grid-cols-2">
          {recommendation.value_positioning_label ? (
            <Metric
              label="Value Positioning"
              value={formatLabel(recommendation.value_positioning_label)}
            />
          ) : null}

          {recommendation.next_best_action ? (
            <article className="rounded-xl border border-slate-200/50 dark:border-slate-800/40 bg-slate-500/5 dark:bg-slate-900/40 p-3.5 transition-all duration-300">
              <p className="text-[10px] font-extrabold uppercase tracking-[0.16em] text-slate-400 dark:text-slate-500">Next Best Action</p>
              <p className="mt-1.5 text-xs font-semibold leading-relaxed text-slate-700 dark:text-slate-300">
                {recommendation.next_best_action}
              </p>
            </article>
          ) : null}

          {marketSummary ? (
            <article className="rounded-xl border border-slate-200/50 dark:border-slate-800/40 bg-slate-500/5 dark:bg-slate-900/40 p-3.5 transition-all duration-300 md:col-span-2">
              <p className="text-[10px] font-extrabold uppercase tracking-[0.16em] text-slate-400 dark:text-slate-500">Market Comparison</p>
              <p className="mt-1.5 text-xs font-semibold leading-relaxed text-slate-700 dark:text-slate-350">{marketSummary}</p>
            </article>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-xl border border-slate-200/50 dark:border-slate-800/40 bg-slate-500/5 dark:bg-slate-900/40 p-3.5 transition-all duration-300">
      <p className="text-[10px] font-extrabold uppercase tracking-[0.16em] text-slate-400 dark:text-slate-500">{label}</p>
      <p className="mt-1.5 font-display text-sm sm:text-base font-bold tracking-tight text-slate-900 dark:text-white">{value}</p>
    </article>
  );
}
