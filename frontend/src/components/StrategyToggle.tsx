import type { StrategyMode } from '../types/api';

const options: { value: StrategyMode; label: string; helper: string }[] = [
  {
    value: 'maximize_profit',
    label: 'Margin Focus',
    helper: 'Protect true margin and expected profit',
  },
  {
    value: 'clear_inventory',
    label: 'Stock Pressure',
    helper: 'Move ageing inventory with controlled discounting',
  },
  {
    value: 'market_expansion',
    label: 'Market Position',
    helper: 'Prioritize win rate and value positioning',
  },
];

interface Props {
  value: StrategyMode;
  onChange: (mode: StrategyMode) => void;
}

export default function StrategyToggle({ value, onChange }: Props) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-2">
      <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={`rounded-lg border px-3 py-2 text-left transition ${
              value === option.value
                ? 'border-slate-900 bg-slate-900 text-white'
                : 'border-slate-200 bg-white text-slate-700 hover:border-slate-400'
            }`}
          >
            <p className="text-sm font-semibold">{option.label}</p>
            <p className="text-xs opacity-80">{option.helper}</p>
          </button>
        ))}
      </div>
    </div>
  );
}
