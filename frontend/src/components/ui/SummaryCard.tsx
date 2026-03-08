import type { ReactNode } from 'react';

interface SummaryCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: string;
  trend?: 'up' | 'down' | 'neutral';
  trendLabel?: string;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info';
  onClick?: () => void;
  children?: ReactNode;
}

const VARIANT_STYLES = {
  default: 'border-slate-200 bg-white',
  success: 'border-emerald-200 bg-emerald-50',
  warning: 'border-amber-200 bg-amber-50',
  danger: 'border-red-200 bg-red-50',
  info: 'border-blue-200 bg-blue-50',
};

const VARIANT_VALUE_COLORS = {
  default: 'text-slate-900',
  success: 'text-emerald-700',
  warning: 'text-amber-700',
  danger: 'text-red-700',
  info: 'text-blue-700',
};

const TREND_ICONS = {
  up: '+',
  down: '-',
  neutral: '=',
};

const TREND_COLORS = {
  up: 'text-emerald-600',
  down: 'text-red-600',
  neutral: 'text-slate-500',
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
      className={`rounded-xl border p-4 text-left shadow-sm transition-all ${VARIANT_STYLES[variant]} ${
        onClick ? 'cursor-pointer hover:shadow-md hover:scale-[1.01]' : ''
      }`}
      onClick={onClick}
      type={onClick ? 'button' : undefined}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-slate-500">{title}</p>
          {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
        </div>
        {icon && (
          <span className="rounded-md bg-white/70 px-2 py-1 text-[10px] font-semibold tracking-wide text-slate-600">
            {icon}
          </span>
        )}
      </div>
      <p className={`mt-2 text-2xl font-bold ${VARIANT_VALUE_COLORS[variant]}`}>{value}</p>
      {trend && trendLabel && (
        <p className={`mt-1 text-xs font-medium ${TREND_COLORS[trend]}`}>
          {TREND_ICONS[trend]} {trendLabel}
        </p>
      )}
      {children}
    </Tag>
  );
}
