import type { ReactNode } from 'react';

interface SummaryCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  trendLabel?: string;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info';
  onClick?: () => void;
  children?: ReactNode;
}

const VARIANT_STYLES = {
  default: 'border-slate-200/60 bg-white/70 dark:border-slate-800/60 dark:bg-slate-900/50',
  success: 'border-emerald-200 bg-emerald-50/50 text-emerald-900 dark:border-emerald-900/30 dark:bg-emerald-950/15 dark:text-emerald-100',
  warning: 'border-amber-200 bg-amber-50/50 text-amber-900 dark:border-amber-900/30 dark:bg-amber-950/15 dark:text-amber-100',
  danger: 'border-red-200 bg-red-50/50 text-red-900 dark:border-red-900/30 dark:bg-red-950/15 dark:text-red-100',
  info: 'border-sky-200 bg-sky-50/50 text-sky-900 dark:border-sky-900/30 dark:bg-sky-950/15 dark:text-sky-100',
};

const VARIANT_VALUE_COLORS = {
  default: 'text-slate-900 dark:text-slate-50',
  success: 'text-emerald-700 dark:text-emerald-400',
  warning: 'text-amber-700 dark:text-amber-400',
  danger: 'text-red-700 dark:text-red-400',
  info: 'text-sky-700 dark:text-sky-400',
};

const TREND_ICONS = {
  up: '↑',
  down: '↓',
  neutral: '•',
};

const TREND_COLORS = {
  up: 'text-emerald-600 dark:text-emerald-400 bg-emerald-100/50 dark:bg-emerald-950/40',
  down: 'text-red-600 dark:text-red-400 bg-red-100/50 dark:bg-red-950/40',
  neutral: 'text-slate-500 dark:text-slate-400 bg-slate-100/50 dark:bg-slate-800/40',
};

export default function SummaryCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendLabel,
  variant = 'default',
  onClick,
  children,
}: SummaryCardProps) {
  const Tag = onClick ? 'button' : 'div';
  return (
    <Tag
      className={`glass-card rounded-2xl border p-5 text-left transition-all duration-300 ${VARIANT_STYLES[variant]} ${
        onClick
          ? 'cursor-pointer hover:-translate-y-1 hover:border-indigo-500/40 hover:shadow-lg hover:shadow-indigo-500/5 dark:hover:shadow-indigo-500/10 active:scale-[0.98]'
          : ''
      }`}
      onClick={onClick}
      type={onClick ? 'button' : undefined}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-400 dark:text-slate-500">{title}</p>
          {subtitle && <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400 leading-relaxed truncate">{subtitle}</p>}
        </div>
        {icon && (
          <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-slate-100 bg-white/90 text-slate-600 shadow-sm dark:border-slate-800 dark:bg-slate-900/90 dark:text-slate-400">
            {icon}
          </span>
        )}
      </div>
      
      <div className="mt-4 flex items-baseline justify-between gap-2 flex-wrap">
        <p className={`font-display text-3xl font-bold tracking-tight ${VARIANT_VALUE_COLORS[variant]}`}>
          {value}
        </p>
        
        {trend && trendLabel && (
          <span className={`inline-flex items-center gap-1 rounded-lg px-2 py-0.5 text-xs font-semibold ${TREND_COLORS[trend]}`}>
            <span>{TREND_ICONS[trend]}</span>
            <span>{trendLabel}</span>
          </span>
        )}
      </div>
      
      {children && <div className="mt-3">{children}</div>}
    </Tag>
  );
}
