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
    <section className="glass-card rounded-2xl p-6 shadow-xl relative overflow-hidden">
      {/* Visual top accent line */}
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 opacity-80" />

      <h3 className="font-display text-lg font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
        <span className="inline-block w-2.5 h-2.5 rounded-full bg-indigo-500 animate-pulse shadow-[0_0_8px_rgba(99,102,241,0.6)]" />
        Explainable Recommendation
      </h3>
      <p className="mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300 font-medium">
        {explanation.short_reason}
      </p>

      {explanationLevels?.quick_summary || explanationLevels?.business_explanation ? (
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          {explanationLevels?.quick_summary ? (
            <div className="rounded-xl border border-slate-200/50 dark:border-slate-800/40 bg-slate-500/5 backdrop-blur-md p-4 transition-all hover:bg-slate-500/10">
              <p className="text-[10px] font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
                Quick Summary
              </p>
              <p className="mt-2 text-xs leading-relaxed text-slate-600 dark:text-slate-300 font-normal">
                {explanationLevels.quick_summary}
              </p>
            </div>
          ) : null}

          {explanationLevels?.business_explanation ? (
            <div className="rounded-xl border border-slate-200/50 dark:border-slate-800/40 bg-slate-500/5 backdrop-blur-md p-4 transition-all hover:bg-slate-500/10">
              <p className="text-[10px] font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
                Business Explanation
              </p>
              <p className="mt-2 text-xs leading-relaxed text-slate-600 dark:text-slate-300 font-normal">
                {explanationLevels.business_explanation}
              </p>
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="mt-5 grid gap-5 md:grid-cols-2">
        <div className="rounded-xl border border-slate-200/40 dark:border-slate-800/30 bg-slate-500/5 p-4">
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-3 block">
            Top Drivers
          </p>
          <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-300">
            {explanation.top_drivers.slice(0, 4).map((item) => (
              <li key={item} className="flex items-start gap-2.5 leading-relaxed">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.6)]" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
        
        <div className="rounded-xl border border-slate-200/40 dark:border-slate-800/30 bg-slate-500/5 p-4">
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-3 block">
            Negotiation Tips
          </p>
          <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-300">
            {explanation.negotiation_tips.slice(0, 4).map((item) => (
              <li key={item} className="flex items-start gap-2.5 leading-relaxed">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-indigo-500 shadow-[0_0_6px_rgba(99,102,241,0.6)]" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {explanation.approval_justification_suggestion ? (
        <div className="mt-5 rounded-xl bg-indigo-500/5 dark:bg-indigo-500/10 border border-indigo-500/20 dark:border-indigo-500/30 p-4 text-xs text-slate-700 dark:text-slate-300 flex items-start gap-3">
          <svg className="w-5 h-5 text-indigo-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          <div>
            <span className="font-bold text-indigo-600 dark:text-indigo-400 block mb-0.5 uppercase tracking-wide text-[10px]">
              Approval Guidance
            </span>
            <span className="leading-relaxed font-medium">{explanation.approval_justification_suggestion}</span>
          </div>
        </div>
      ) : null}

      {explanationLevels?.detailed_trace ? (
        <details className="mt-5 rounded-xl border border-slate-200/50 dark:border-slate-800/40 bg-slate-500/5 transition-all duration-200 overflow-hidden">
          <summary className="cursor-pointer text-xs font-semibold text-slate-700 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400 p-4 transition-colors select-none flex items-center justify-between">
            <span>Detailed Engine Trace</span>
            <svg className="w-4 h-4 text-slate-400 transition-transform duration-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </summary>
          <div className="p-4 border-t border-slate-200/30 dark:border-slate-800/30 bg-slate-950/40 dark:bg-slate-950/80">
            <pre className="whitespace-pre-wrap font-mono text-[10px] leading-relaxed text-indigo-200/90 dark:text-indigo-300/80 overflow-x-auto max-h-60 sidebar-scroll">
              {explanationLevels.detailed_trace}
            </pre>
          </div>
        </details>
      ) : null}
    </section>
  );
}
