interface NextActionCardProps {
  label: string;
  description?: string;
  actionText: string;
  onAction: () => void;
  icon?: string;
  variant?: 'primary' | 'secondary';
}

export default function NextActionCard({
  label,
  description,
  actionText,
  onAction,
  icon = '➡️',
  variant = 'primary',
}: NextActionCardProps) {
  const btnClass =
    variant === 'primary'
      ? 'bg-emerald-600 text-white hover:bg-emerald-700'
      : 'bg-slate-100 text-slate-700 hover:bg-slate-200';

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-lg">{icon}</span>
          <div>
            <p className="text-sm font-semibold text-slate-800">{label}</p>
            {description && <p className="text-xs text-slate-500">{description}</p>}
          </div>
        </div>
        <button
          type="button"
          onClick={onAction}
          className={`rounded-lg px-4 py-2 text-sm font-medium transition ${btnClass}`}
        >
          {actionText}
        </button>
      </div>
    </div>
  );
}
