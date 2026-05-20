type ChipVariant =
  | 'draft'
  | 'parsed'
  | 'needs_review'
  | 'active'
  | 'rejected'
  | 'archived'
  | 'pending'
  | 'approval_pending'
  | 'approved'
  | 'finalized'
  | 'low'
  | 'medium'
  | 'high'
  | 'info'
  | 'success'
  | 'warning'
  | 'danger';

interface StatusChipProps {
  status: string;
  variant?: ChipVariant;
  size?: 'sm' | 'md';
}

const CHIP_STYLES: Record<string, string> = {
  draft: 'bg-slate-100/80 text-slate-700 border-slate-200/60 dark:bg-slate-800/40 dark:text-slate-300 dark:border-slate-700/60 before:bg-slate-400',
  parsed: 'bg-sky-100/80 text-sky-800 border-sky-200/60 dark:bg-sky-950/20 dark:text-sky-300 dark:border-sky-800/60 before:bg-sky-400',
  needs_review: 'bg-amber-100/80 text-amber-800 border-amber-200/60 dark:bg-amber-950/20 dark:text-amber-300 dark:border-amber-800/60 before:bg-amber-400',
  active: 'bg-emerald-100/80 text-emerald-800 border-emerald-200/60 dark:bg-emerald-950/20 dark:text-emerald-300 dark:border-emerald-800/60 before:bg-emerald-400',
  rejected: 'bg-rose-100/80 text-rose-800 border-rose-200/60 dark:bg-rose-950/20 dark:text-rose-300 dark:border-rose-800/60 before:bg-rose-400',
  archived: 'bg-slate-100/80 text-slate-600 border-slate-200/60 dark:bg-slate-800/40 dark:text-slate-400 dark:border-slate-700/60 before:bg-slate-400',
  pending: 'bg-amber-100/80 text-amber-800 border-amber-200/60 dark:bg-amber-950/20 dark:text-amber-300 dark:border-amber-800/60 before:bg-amber-400',
  approval_pending: 'bg-amber-100/80 text-amber-800 border-amber-200/60 dark:bg-amber-950/20 dark:text-amber-300 dark:border-amber-800/60 before:bg-amber-400',
  approved: 'bg-emerald-100/80 text-emerald-800 border-emerald-200/60 dark:bg-emerald-950/20 dark:text-emerald-300 dark:border-emerald-800/60 before:bg-emerald-400',
  finalized: 'bg-indigo-100/80 text-indigo-800 border-indigo-200/60 dark:bg-indigo-950/20 dark:text-indigo-300 dark:border-indigo-800/60 before:bg-indigo-400',
  low: 'bg-emerald-100/80 text-emerald-800 border-emerald-200/60 dark:bg-emerald-950/20 dark:text-emerald-300 dark:border-emerald-800/60 before:bg-emerald-400',
  medium: 'bg-amber-100/80 text-amber-800 border-amber-200/60 dark:bg-amber-950/20 dark:text-amber-300 dark:border-amber-800/60 before:bg-amber-400',
  high: 'bg-rose-100/80 text-rose-800 border-rose-200/60 dark:bg-rose-950/20 dark:text-rose-300 dark:border-rose-800/60 before:bg-rose-400',
  info: 'bg-sky-100/80 text-sky-800 border-sky-200/60 dark:bg-sky-950/20 dark:text-sky-300 dark:border-sky-800/60 before:bg-sky-400',
  success: 'bg-emerald-100/80 text-emerald-800 border-emerald-200/60 dark:bg-emerald-950/20 dark:text-emerald-300 dark:border-emerald-800/60 before:bg-emerald-400',
  warning: 'bg-amber-100/80 text-amber-800 border-amber-200/60 dark:bg-amber-950/20 dark:text-amber-300 dark:border-amber-800/60 before:bg-amber-400',
  danger: 'bg-rose-100/80 text-rose-800 border-rose-200/60 dark:bg-rose-950/20 dark:text-rose-300 dark:border-rose-800/60 before:bg-rose-400',
};

export default function StatusChip({ status, variant, size = 'sm' }: StatusChipProps) {
  const key = variant || status.toLowerCase().replace(/\s+/g, '_');
  const style = CHIP_STYLES[key] || CHIP_STYLES.info;
  const sizeClass = size === 'md' ? 'px-3.5 py-1.5 text-xs' : 'px-2.5 py-1 text-[11px]';
  const label = status.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-semibold tracking-wide backdrop-blur-sm transition-all duration-300 before:h-1.5 before:w-1.5 before:rounded-full before:breathe-dot ${style} ${sizeClass}`}
    >
      {label}
    </span>
  );
}
