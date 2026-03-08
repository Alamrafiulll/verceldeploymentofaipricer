import type { AuditLog } from '../types/api';

interface Props {
  rows: AuditLog[];
}

export default function AuditLogTable({ rows }: Props) {
  return (
    <div className="overflow-hidden rounded-2xl border border-white/70 bg-white shadow-card">
      <div className="border-b border-slate-200 p-4">
        <h3 className="font-display text-lg font-semibold">Audit Logs</h3>
      </div>
      <div className="max-h-[420px] overflow-auto">
        <table className="min-w-full text-sm">
          <thead className="sticky top-0 bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-3 py-2">Timestamp</th>
              <th className="px-3 py-2">Action</th>
              <th className="px-3 py-2">Entity</th>
              <th className="px-3 py-2">Actor</th>
              <th className="px-3 py-2">Reason</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-b border-slate-100">
                <td className="px-3 py-2 text-xs">{new Date(row.created_at).toLocaleString()}</td>
                <td className="px-3 py-2">{row.action}</td>
                <td className="px-3 py-2">
                  {row.entity_type}:{row.entity_id.slice(0, 8)}
                </td>
                <td className="px-3 py-2 text-xs">{row.actor_user_id?.slice(0, 8) ?? '-'}</td>
                <td className="px-3 py-2 text-slate-600">{row.reason ?? '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
