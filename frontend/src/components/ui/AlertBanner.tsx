import type { ReactNode } from 'react';
import { AlertTriangle, CheckCircle2, Info, Lightbulb, X, XCircle } from 'lucide-react';

type AlertVariant = 'info' | 'success' | 'warning' | 'danger' | 'tip';

interface AlertBannerProps {
  variant?: AlertVariant;
  title?: string;
  children: ReactNode;
  dismissable?: boolean;
  onDismiss?: () => void;
}

const STYLES: Record<AlertVariant, string> = {
  info: 'border-slate-200/50 border-l-sky-500 bg-sky-50/50 text-sky-950 dark:border-slate-800/50 dark:border-l-sky-500 dark:bg-sky-950/10 dark:text-sky-100',
  success: 'border-slate-200/50 border-l-emerald-500 bg-emerald-50/50 text-emerald-950 dark:border-slate-800/50 dark:border-l-emerald-500 dark:bg-emerald-950/10 dark:text-emerald-100',
  warning: 'border-slate-200/50 border-l-amber-500 bg-amber-50/50 text-amber-950 dark:border-slate-800/50 dark:border-l-amber-500 dark:bg-amber-950/10 dark:text-amber-100',
  danger: 'border-slate-200/50 border-l-rose-500 bg-rose-50/50 text-rose-950 dark:border-slate-800/50 dark:border-l-rose-500 dark:bg-rose-950/10 dark:text-rose-100',
  tip: 'border-slate-200/50 border-l-indigo-500 bg-indigo-50/50 text-indigo-950 dark:border-slate-800/50 dark:border-l-indigo-500 dark:bg-indigo-950/10 dark:text-indigo-100',
};

const ICONS: Record<AlertVariant, ReactNode> = {
  info: <Info className="h-4 w-4 text-sky-600 dark:text-sky-400" aria-hidden="true" />,
  success: <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />,
  warning: <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400" aria-hidden="true" />,
  danger: <XCircle className="h-4 w-4 text-rose-600 dark:text-rose-400" aria-hidden="true" />,
  tip: <Lightbulb className="h-4 w-4 text-indigo-600 dark:text-indigo-400" aria-hidden="true" />,
};

const TITLES: Record<AlertVariant, string> = {
  info: 'Information',
  success: 'Update Saved',
  warning: 'Policy Warning',
  danger: 'Action Required',
  tip: 'Recommended Action',
};

export default function AlertBanner({
  variant = 'info',
  title,
  children,
  dismissable,
  onDismiss,
}: AlertBannerProps) {
  return (
    <div className={`relative rounded-xl border border-l-4 p-4 backdrop-blur-md shadow-sm transition-all duration-300 ${STYLES[variant]}`}>
      <div className="flex items-start gap-3">
        <span className="mt-0.5 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-white/90 border border-slate-100 dark:border-slate-800 dark:bg-slate-900/90 shadow-sm">
          {ICONS[variant]}
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-bold tracking-tight">{title || TITLES[variant]}</p>
          <div className="mt-1 text-xs sm:text-sm leading-relaxed opacity-90">{children}</div>
        </div>
        {dismissable && onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            className="rounded-lg p-1 opacity-60 transition hover:bg-black/5 dark:hover:bg-white/5 hover:opacity-100"
            aria-label="Dismiss"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        )}
      </div>
    </div>
  );
}
