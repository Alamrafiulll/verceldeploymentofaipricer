import { History, SearchCheck } from 'lucide-react';

import { EmptyState, StatusChip } from './ui';
import type { AuditLog } from '../types/api';

interface Props {
  rows: AuditLog[];
}

function label(value: string) {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

export default function AuditLogTable({ rows }: Props) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-slate-50 text-slate-700">
              <History className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <h2 className="text-lg font-semibold text-slate-950">Audit Trail</h2>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                System changes, actor references, and recorded governance reasons.
              </p>
            </div>
          </div>
          <StatusChip status={`${rows.length} events`} variant="info" size="md" />
        </div>
      </div>

      {rows.length === 0 ? (
        <div className="p-5">
          <EmptyState
            icon={<SearchCheck className="h-6 w-6" aria-hidden="true" />}
            title="No audit events"
            description="Governance changes will appear here after admin activity."
          />
        </div>
      ) : (
        <div className="max-h-[460px] overflow-auto">
          <table className="w-full min-w-[920px] text-left text-sm">
            <thead className="sticky top-0 z-10 border-b border-slate-200 bg-slate-50 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              <tr>
                <th className="px-5 py-3">Timestamp</th>
                <th className="px-5 py-3">Action</th>
                <th className="px-5 py-3">Entity</th>
                <th className="px-5 py-3">Actor</th>
                <th className="px-5 py-3">Reason</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-b border-slate-100 last:border-0">
                  <td className="px-5 py-3 text-xs text-slate-600">{new Date(row.created_at).toLocaleString()}</td>
                  <td className="px-5 py-3">
                    <StatusChip status={label(row.action)} variant="info" />
                  </td>
                  <td className="px-5 py-3">
                    <p className="font-semibold text-slate-900">{label(row.entity_type)}</p>
                    <p className="mt-1 font-mono text-xs text-slate-500">{row.entity_id.slice(0, 8)}</p>
                  </td>
                  <td className="px-5 py-3 font-mono text-xs text-slate-600">
                    {row.actor_user_id?.slice(0, 8) ?? '-'}
                  </td>
                  <td className="px-5 py-3 text-slate-600">{row.reason ?? '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
