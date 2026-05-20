import type { ReactNode } from 'react';
import { ArrowRight } from 'lucide-react';

interface NextActionCardProps {
  label: string;
  description?: string;
  actionText: string;
  onAction: () => void;
  icon?: ReactNode;
  variant?: 'primary' | 'secondary';
  eyebrow?: string;
}

export default function NextActionCard({
  label,
  description,
  actionText,
  onAction,
  icon,
  variant = 'primary',
  eyebrow,
}: NextActionCardProps) {
  const btnClass =
    variant === 'primary'
      ? 'border-slate-900 bg-slate-900 text-white hover:bg-slate-800'
      : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50';

  return (
    <div className="flex h-full flex-col rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex min-w-0 flex-1 items-start gap-3">
        {icon && (
          <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-slate-50 text-slate-700">
            {icon}
          </span>
        )}
        <div className="min-w-0">
          {eyebrow && (
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{eyebrow}</p>
          )}
          <p className="text-base font-semibold text-slate-950">{label}</p>
          {description && <p className="mt-1 max-w-xl text-sm leading-5 text-slate-600">{description}</p>}
        </div>
      </div>
      <button
        type="button"
        onClick={onAction}
        className={`mt-4 inline-flex w-fit items-center justify-center gap-2 whitespace-nowrap rounded-lg border px-4 py-2.5 text-sm font-semibold transition ${btnClass}`}
      >
        {actionText}
        <ArrowRight className="h-4 w-4" aria-hidden="true" />
      </button>
    </div>
  );
}
