import type { ReactNode } from 'react';

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  badge?: string;
  action?: ReactNode;
  kicker?: string;
}

export default function SectionHeader({ title, subtitle, icon, badge, action, kicker }: SectionHeaderProps) {
  return (
    <div className="mb-6 flex flex-col gap-4 border-b border-slate-200/60 pb-5 dark:border-slate-800/50 md:flex-row md:items-center md:justify-between transition-all duration-300">
      <div className="flex min-w-0 items-start gap-4">
        {icon && (
          <span className="mt-1 inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-slate-200/60 bg-white/85 text-indigo-600 shadow-sm dark:border-slate-800/60 dark:bg-slate-900/65 dark:text-indigo-400">
            {icon}
          </span>
        )}
        <div className="min-w-0">
          {kicker && (
            <p className="text-[10px] font-extrabold uppercase tracking-[0.2em] text-indigo-500 dark:text-indigo-400">
              {kicker}
            </p>
          )}
          <div className="flex flex-wrap items-center gap-2 mt-0.5">
            <h1 className="font-display text-2xl font-extrabold tracking-tight text-slate-900 dark:text-white">
              {title}
            </h1>
            {badge && (
              <span className="rounded-lg border border-slate-200 bg-white/70 px-2.5 py-0.5 text-[11px] font-bold text-slate-500 uppercase tracking-wide dark:border-slate-800 dark:bg-slate-900/70 dark:text-slate-400">
                {badge}
              </span>
            )}
          </div>
          {subtitle && (
            <p className="mt-1.5 max-w-4xl text-xs sm:text-sm font-semibold text-slate-500 dark:text-slate-400 leading-relaxed">
              {subtitle}
            </p>
          )}
        </div>
      </div>
      {action && <div className="shrink-0 flex items-center">{action}</div>}
    </div>
  );
}
