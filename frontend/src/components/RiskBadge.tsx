interface Props {
  level: 'low' | 'medium' | 'high';
}

const styleByLevel = {
  low: 'bg-signal-green/10 text-signal-green border-signal-green/30',
  medium: 'bg-signal-yellow/10 text-signal-yellow border-signal-yellow/30',
  high: 'bg-signal-red/10 text-signal-red border-signal-red/30',
};

export default function RiskBadge({ level }: Props) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${styleByLevel[level]}`}
    >
      {level} risk
    </span>
  );
}
