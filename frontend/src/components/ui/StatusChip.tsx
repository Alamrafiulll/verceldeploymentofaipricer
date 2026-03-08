type ChipVariant =
  | 'draft'
  | 'parsed'
  | 'needs_review'
  | 'active'
  | 'rejected'
  | 'archived'
  | 'pending'
  | 'approved'
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
  draft: 'bg-slate-100 text-slate-600 border-slate-200',
  parsed: 'bg-blue-100 text-blue-700 border-blue-200',
  needs_review: 'bg-amber-100 text-amber-700 border-amber-200',
  active: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  rejected: 'bg-red-100 text-red-700 border-red-200',
  archived: 'bg-slate-100 text-slate-500 border-slate-200',
  pending: 'bg-amber-100 text-amber-700 border-amber-200',
  approved: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  low: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  medium: 'bg-amber-100 text-amber-700 border-amber-200',
  high: 'bg-red-100 text-red-700 border-red-200',
  info: 'bg-blue-100 text-blue-700 border-blue-200',
  success: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  warning: 'bg-amber-100 text-amber-700 border-amber-200',
  danger: 'bg-red-100 text-red-700 border-red-200',
};

const CHIP_ICONS: Record<string, string> = {
  draft: '📝',
  parsed: '🔎',
  needs_review: '👁️',
  active: '✅',
  rejected: '❌',
  archived: '🗂️',
  pending: '⏳',
  approved: '✅',
  low: '🟢',
  medium: '🟡',
  high: '🔴',
};

export default function StatusChip({ status, variant, size = 'sm' }: StatusChipProps) {
  const key = variant || status.toLowerCase().replace(/\s+/g, '_');
  const style = CHIP_STYLES[key] || CHIP_STYLES.info;
  const icon = CHIP_ICONS[key] || '';
  const sizeClass = size === 'md' ? 'px-3 py-1.5 text-xs' : 'px-2 py-0.5 text-[11px]';

  const label = status.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());

  return (
    <span className={`inline-flex items-center gap-1 rounded-full border font-medium ${style} ${sizeClass}`}>
      {icon && <span className="text-xs">{icon}</span>}
      {label}
    </span>
  );
}
