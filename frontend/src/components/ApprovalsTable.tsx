import { useState } from 'react';

import type { Approval } from '../types/api';
import Spinner from './Spinner';

interface Props {
  approvals: Approval[];
  onApprove: (id: string, reason: string) => Promise<void>;
  onReject: (id: string, reason: string) => Promise<void>;
  onViewReport: (approvalId: string) => void;
  loadingId?: string;
}

export default function ApprovalsTable({ approvals, onApprove, onReject, onViewReport, loadingId }: Props) {
  const [reasons, setReasons] = useState<Record<string, string>>({});

  return (
    <div className="overflow-hidden rounded-2xl border border-white/70 bg-white shadow-card">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-3 py-2 text-left">Quote</th>
            <th className="px-3 py-2 text-left">Requested Price</th>
            <th className="px-3 py-2 text-left">Requested Discount</th>
            <th className="px-3 py-2 text-left">Justification</th>
            <th className="px-3 py-2 text-left">Decision Reason</th>
            <th className="px-3 py-2 text-left">Action</th>
            <th className="px-3 py-2 text-left">Compliance</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {approvals.map((approval) => (
            <tr key={approval.id}>
              <td className="px-3 py-2 font-mono text-xs">{approval.quote_id.slice(0, 8)}</td>
              <td className="px-3 py-2">{approval.requested_price ? `RM ${approval.requested_price.toFixed(2)}` : '-'}</td>
              <td className="px-3 py-2">
                {approval.requested_discount ? `${approval.requested_discount.toFixed(2)}%` : '-'}
              </td>
              <td className="px-3 py-2 text-slate-600">{approval.request_justification}</td>
              <td className="px-3 py-2">
                <input
                  className="w-full rounded-md border border-slate-300 px-2 py-1"
                  value={reasons[approval.id] ?? ''}
                  onChange={(event) =>
                    setReasons((prev) => ({
                      ...prev,
                      [approval.id]: event.target.value,
                    }))
                  }
                  placeholder="Enter reason"
                />
              </td>
              <td className="px-3 py-2">
                <div className="flex gap-2">
                  <button
                    className="flex items-center gap-1 rounded-md bg-signal-green px-2.5 py-1.5 text-white disabled:opacity-50"
                    disabled={loadingId === approval.id}
                    onClick={() => onApprove(approval.id, reasons[approval.id] ?? '')}
                  >
                    {loadingId === approval.id ? <Spinner size="sm" color="light" /> : null}
                    Approve
                  </button>
                  <button
                    className="flex items-center gap-1 rounded-md bg-signal-red px-2.5 py-1.5 text-white disabled:opacity-50"
                    disabled={loadingId === approval.id}
                    onClick={() => onReject(approval.id, reasons[approval.id] ?? '')}
                  >
                    {loadingId === approval.id ? <Spinner size="sm" color="light" /> : null}
                    Reject
                  </button>
                </div>
              </td>
              <td className="px-3 py-2">
                <button
                  className="rounded-md border border-slate-300 px-2.5 py-1.5 text-xs"
                  onClick={() => onViewReport(approval.id)}
                >
                  Review Context
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
