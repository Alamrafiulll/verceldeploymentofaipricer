import { useState } from 'react';
import { CheckCircle2, FileSearch, Send, XCircle } from 'lucide-react';

import type { Approval } from '../types/api';
import { StatusChip } from './ui';

interface Props {
  approvals: Approval[];
  onApprove: (id: string, reason: string) => Promise<void>;
  onReject: (id: string, reason: string) => Promise<void>;
  onViewReport: (approvalId: string) => void;
  loadingId?: string;
  selectedApprovalId?: string;
}

const money = (value?: number | null) =>
  value === null || value === undefined
    ? '-'
    : new Intl.NumberFormat('en-MY', {
        style: 'currency',
        currency: 'MYR',
        maximumFractionDigits: 2,
      }).format(value);

const pct = (value?: number | null) =>
  value === null || value === undefined ? '-' : `${value.toFixed(2)}%`;

function formatDate(value: string) {
  return new Date(value).toLocaleString();
}

export default function ApprovalsTable({
  approvals,
  onApprove,
  onReject,
  onViewReport,
  loadingId,
  selectedApprovalId,
}: Props) {
  const [reasons, setReasons] = useState<Record<string, string>>({});

  return (
    <section className="glass-card rounded-2xl shadow-xl overflow-hidden relative">
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-amber-500 via-indigo-500 to-emerald-500 opacity-60" />
      
      <div className="border-b border-slate-200/50 dark:border-slate-800/40 p-6 bg-slate-500/5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white">Decision Queue</h2>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Review the commercial exception, document the decision reason, then approve or reject.
            </p>
          </div>
          <StatusChip 
            status={`${approvals.length} pending`} 
            variant={approvals.length > 0 ? 'warning' : 'success'} 
            size="md" 
          />
        </div>
      </div>

      <div className="divide-y divide-slate-100/50 dark:divide-slate-800/40">
        {approvals.map((approval) => {
          const selected = selectedApprovalId === approval.id;
          const reason = reasons[approval.id] ?? '';
          const busy = loadingId === approval.id;

          return (
            <article
              key={approval.id}
              className={`grid gap-4 p-6 transition-all duration-300 ${
                selected 
                  ? 'bg-indigo-500/5 dark:bg-indigo-500/10 border-l-4 border-indigo-500' 
                  : 'bg-transparent hover:bg-slate-500/5 border-l-4 border-transparent'
              }`}
            >
              <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-mono text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                          Quote {approval.quote_id.slice(0, 8)}
                        </p>
                        <StatusChip status={approval.status} />
                      </div>
                      <p className="mt-2 text-lg font-bold text-slate-900 dark:text-white">
                        {money(approval.requested_price)} requested price
                      </p>
                      <p className="mt-1 text-xs font-semibold text-slate-500 dark:text-slate-400">
                        Requested discount:{' '}
                        <span className="text-slate-800 dark:text-slate-200 font-bold">
                          {pct(approval.requested_discount)}
                        </span>
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => onViewReport(approval.id)}
                      className="btn-outline py-1.5 px-3 text-xs inline-flex items-center gap-1.5"
                    >
                      <FileSearch className="h-3.5 w-3.5 text-indigo-500" aria-hidden="true" />
                      Review Context
                    </button>
                  </div>

                  <div className="mt-4 rounded-xl border border-slate-200/40 dark:border-slate-800/30 bg-slate-500/5 p-4">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5 block">
                      Sales Justification
                    </p>
                    <p className="text-xs leading-relaxed text-slate-700 dark:text-slate-300 font-medium">
                      {approval.request_justification || 'No justification was provided.'}
                    </p>
                    <p className="mt-3.5 text-[10px] font-semibold text-slate-400 dark:text-slate-500">
                      Submitted {formatDate(approval.created_at)}
                    </p>
                  </div>
                </div>

                <div className="space-y-3.5">
                  <label className="block text-xs font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                    <span>Decision reason</span>
                    <textarea
                      className="input mt-2 min-h-24 py-2 text-xs"
                      value={reason}
                      onChange={(event) =>
                        setReasons((prev) => ({
                          ...prev,
                          [approval.id]: event.target.value,
                        }))
                      }
                      placeholder="Record margin, customer strategy, policy, or market rationale"
                    />
                  </label>
                  
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 px-3 py-2.5 text-xs font-bold text-white transition duration-200 hover:from-emerald-500 hover:to-teal-500 active:scale-[0.98] shadow-md shadow-emerald-600/10 disabled:opacity-40"
                      disabled={busy}
                      onClick={() => onApprove(approval.id, reason)}
                    >
                      <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
                      {busy ? 'Saving...' : 'Approve'}
                    </button>
                    <button
                      type="button"
                      className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-gradient-to-r from-rose-600 to-red-600 px-3 py-2.5 text-xs font-bold text-white transition duration-200 hover:from-rose-500 hover:to-red-500 active:scale-[0.98] shadow-md shadow-rose-600/10 disabled:opacity-40"
                      disabled={busy}
                      onClick={() => onReject(approval.id, reason)}
                    >
                      <XCircle className="h-4 w-4" aria-hidden="true" />
                      {busy ? 'Saving...' : 'Reject'}
                    </button>
                  </div>
                  
                  <button
                    type="button"
                    onClick={() => onViewReport(approval.id)}
                    className="inline-flex w-full items-center justify-center gap-1.5 rounded-xl bg-slate-900 dark:bg-indigo-600 dark:hover:bg-indigo-500 hover:bg-slate-800 px-3 py-2.5 text-xs font-bold text-white transition-all duration-200 active:scale-[0.98] hover:shadow-lg hover:shadow-indigo-500/10"
                  >
                    <Send className="h-4 w-4" aria-hidden="true" />
                    Open business impact
                  </button>
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
