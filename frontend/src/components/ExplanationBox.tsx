interface Props {
  explanation: {
    short_reason: string;
    top_drivers: string[];
    negotiation_tips: string[];
    approval_justification_suggestion?: string;
  };
  explanationLevels?: {
    quick_summary?: string;
    business_explanation?: string;
    detailed_trace?: string;
  } | null;
}

export default function ExplanationBox({ explanation, explanationLevels }: Props) {
  return (
    <section className="rounded-2xl border border-white/70 bg-white p-5 shadow-card">
      <h3 className="font-display text-lg font-semibold">Explainable Recommendation</h3>
      <p className="mt-2 text-sm text-slate-700">{explanation.short_reason}</p>

      {explanationLevels?.quick_summary || explanationLevels?.business_explanation ? (
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          {explanationLevels?.quick_summary ? (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Quick Summary
              </p>
              <p className="mt-2 text-sm text-slate-700">{explanationLevels.quick_summary}</p>
            </div>
          ) : null}

          {explanationLevels?.business_explanation ? (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Business Explanation
              </p>
              <p className="mt-2 text-sm text-slate-700">
                {explanationLevels.business_explanation}
              </p>
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Top Drivers</p>
          <ul className="mt-2 space-y-1 text-sm text-slate-700">
            {explanation.top_drivers.slice(0, 4).map((item) => (
              <li key={item}>- {item}</li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Negotiation Tips
          </p>
          <ul className="mt-2 space-y-1 text-sm text-slate-700">
            {explanation.negotiation_tips.slice(0, 4).map((item) => (
              <li key={item}>- {item}</li>
            ))}
          </ul>
        </div>
      </div>

      {explanation.approval_justification_suggestion ? (
        <div className="mt-4 rounded-lg bg-slate-100 p-3 text-sm text-slate-700">
          <span className="font-semibold">Approval Guidance:</span>{' '}
          {explanation.approval_justification_suggestion}
        </div>
      ) : null}

      {explanationLevels?.detailed_trace ? (
        <details className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3">
          <summary className="cursor-pointer text-sm font-semibold text-slate-800">
            Detailed Trace
          </summary>
          <pre className="mt-3 whitespace-pre-wrap text-xs leading-relaxed text-slate-700">
            {explanationLevels.detailed_trace}
          </pre>
        </details>
      ) : null}
    </section>
  );
}
