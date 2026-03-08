import type { ReactNode } from 'react';

type AlertVariant = 'info' | 'success' | 'warning' | 'danger' | 'tip';

interface AlertBannerProps {
  variant?: AlertVariant;
  title?: string;
  children: ReactNode;
  dismissable?: boolean;
  onDismiss?: () => void;
}

const STYLES: Record<AlertVariant, string> = {
  info: 'border-blue-200 bg-blue-50 text-blue-800',
  success: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  warning: 'border-amber-200 bg-amber-50 text-amber-800',
  danger: 'border-red-200 bg-red-50 text-red-800',
  tip: 'border-violet-200 bg-violet-50 text-violet-800',
};

const ICONS: Record<AlertVariant, string> = {
  info: 'ℹ️',
  success: '✅',
  warning: '⚠️',
  danger: '⛔',
  tip: '💡',
};

const TITLES: Record<AlertVariant, string> = {
  info: 'Information',
  success: 'Update Saved',
  warning: 'Policy Warning',
  danger: 'Margin Risk',
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
    <div className={`relative rounded-xl border p-4 ${STYLES[variant]}`}>
      <div className="flex items-start gap-2">
        <span className="mt-0.5 text-base">{ICONS[variant]}</span>
        <div className="flex-1">
          <p className="text-sm font-semibold">{title || TITLES[variant]}</p>
          <div className="mt-0.5 text-sm leading-relaxed">{children}</div>
        </div>
        {dismissable && onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            className="text-lg leading-none opacity-50 transition hover:opacity-100"
            aria-label="Dismiss"
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
}
