import type { ReactNode } from 'react';

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  icon?: string;
  badge?: string;
  action?: ReactNode;
}

export default function SectionHeader({ title, subtitle, icon, badge, action }: SectionHeaderProps) {
  return (
    <div className="mb-4 flex items-center justify-between">
      <div className="flex items-center gap-2">
        {icon && <span className="text-xl">{icon}</span>}
        <div>
          <h2 className="text-lg font-bold text-slate-900">{title}</h2>
          {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
        </div>
        {badge && (
          <span className="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600">
            {badge}
          </span>
        )}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}
