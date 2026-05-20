import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  AlertTriangle,
  BadgeCheck,
  CheckCircle2,
  Clock3,
  FileCheck2,
  FileSearch,
  Scale,
  ShieldCheck,
  Sparkles,
  TrendingDown,
  UserRoundCheck,
} from 'lucide-react';

import ApprovalsTable from '../components/ApprovalsTable';
import Spinner from '../components/Spinner';
import { AlertBanner, EmptyState, SectionHeader, StatusChip, SummaryCard } from '../components/ui';
import api from '../lib/api';
import { getSession } from '../lib/auth';
import type { Approval, ApprovalContext } from '../types/api';

const money = (value?: number | null) =>
  value === null || value === undefined
    ? '-'
    : new Intl.NumberFormat('en-MY', {
        style: 'currency',
        currency: 'MYR',
        maximumFractionDigits: 2,
      }).format(value);

const pct = (value?: number | null) => (value === null || value === undefined ? '-' : `${value.toFixed(2)}%`);

const label = (value?: string | null) =>
  value ? value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase()) : '-';

const readString = (value: Record<string, unknown> | null | undefined, key: string) =>
  typeof value?.[key] === 'string' ? (value[key] as string) : null;

const readNumber = (value: Record<string, unknown> | null | undefined, key: string) =>
  typeof value?.[key] === 'number' ? (value[key] as number) : null;

function ageInHours(value?: string | null) {
  if (!value) return 0;
  return Math.max(0, Math.round((Date.now() - new Date(value).getTime()) / 360_000) / 10);
}

export default function ApprovalsPage() {
  const queryClient = useQueryClient();
  const session = getSession();
  const [loadingId, setLoadingId] = useState<string>();
  const [selectedApprovalId, setSelectedApprovalId] = useState<string>();
  const [message, setMessage] = useState('');

  const approvals = useQuery({
    queryKey: ['approvals', 'pending', session?.user.id ?? 'anonymous'],
    queryFn: async () => (await api.get<Approval[]>('/approvals?status=pending')).data,
    staleTime: 0,
    refetchOnMount: 'always',
  });

  useEffect(() => {
    const rows = approvals.data ?? [];
    if (rows.length === 0) {
      setSelectedApprovalId(undefined);
      return;
    }
    if (!selectedApprovalId || !rows.some((approval) => approval.id === selectedApprovalId)) {
      setSelectedApprovalId(rows[0].id);
    }
  }, [approvals.data, selectedApprovalId]);

  const approvalContext = useQuery({
    queryKey: ['approval-context', selectedApprovalId],
    enabled: Boolean(selectedApprovalId),
    queryFn: async () => (await api.get<ApprovalContext>(`/approvals/${selectedApprovalId}/context`)).data,
  });

  const decide = useMutation({
    mutationFn: async ({ id, approve, reason }: { id: string; approve: boolean; reason: string }) => {
      const endpoint = approve ? 'approve' : 'reject';
      return api.post(`/approvals/${id}/${endpoint}`, {
        decision_reason: reason || 'Reviewed decision',
      });
    },
    onSuccess: async (_, variables) => {
      await queryClient.invalidateQueries({ queryKey: ['approvals', 'pending'] });
      await queryClient.invalidateQueries({ queryKey: ['approval-context', variables.id] });
      setLoadingId(undefined);
      setMessage('Approval decision saved successfully.');
      if (selectedApprovalId === variables.id) {
        setSelectedApprovalId(undefined);
      }
    },
    onError: (error: any) => {
      setLoadingId(undefined);
      const detail = error?.response?.data?.detail;
      setMessage(typeof detail === 'string' ? detail : 'Failed to save approval decision.');
    },
  });

  const pendingRows = approvals.data ?? [];
  const pendingCount = pendingRows.length;
  const totalRequestedValue = useMemo(
    () => pendingRows.reduce((sum, approval) => sum + (approval.requested_price ?? 0), 0),
    [pendingRows],
  );
  const averageDiscount = useMemo(() => {
    const discounts = pendingRows
      .map((approval) => approval.requested_discount)
      .filter((value): value is number => typeof value === 'number');
    if (discounts.length === 0) return null;
    return discounts.reduce((sum, value) => sum + value, 0) / discounts.length;
  }, [pendingRows]);
  const oldestHours = useMemo(
    () => pendingRows.reduce((max, approval) => Math.max(max, ageInHours(approval.created_at)), 0),
    [pendingRows],
  );

  const currentContext = approvalContext.data;
  const aiSummary = currentContext?.ai_recommendation_summary ?? null;
  const currentFinance = currentContext?.current_finance ?? null;
  const requestedFinance = currentContext?.requested_finance ?? null;
  const requestedMargin = readNumber(requestedFinance, 'net_margin_percent');
  const currentMargin = readNumber(currentFinance, 'net_margin_percent');
  const marginDelta =
    requestedMargin !== null && currentMargin !== null && requestedMargin !== undefined && currentMargin !== undefined
      ? requestedMargin - currentMargin
      : null;
  const leakageAmount = readNumber(requestedFinance, 'leakage_amount');

  return (
    <div className="space-y-6">
      <SectionHeader
        kicker="Approver cockpit"
        icon={<ShieldCheck className="h-5 w-5 text-indigo-500" aria-hidden="true" />}
        title="Approval Governance Center"
        subtitle="Review pricing exceptions with true margin impact, policy source references, similar decisions, and a documented audit trail."
        badge={pendingCount > 0 ? `${pendingCount} pending` : 'Queue clear'}
        action={
          <div className="rounded-xl border border-slate-200/50 dark:border-slate-800/40 bg-white/50 dark:bg-slate-900/50 px-4 py-2.5 text-xs font-semibold text-slate-600 dark:text-slate-300 shadow-sm backdrop-blur-md">
            Signed in as <span className="font-bold text-slate-900 dark:text-white">{session?.user.name ?? 'Approver'}</span>
          </div>
        }
      />

      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <SummaryCard
          title="Open Exceptions"
          value={pendingCount}
          subtitle={pendingCount > 0 ? 'Needs decision' : 'No open approvals'}
          icon={<Clock3 className="h-4 w-4 text-amber-500" aria-hidden="true" />}
          variant={pendingCount > 0 ? 'warning' : 'success'}
        />
        <SummaryCard
          title="Requested Value"
          value={money(totalRequestedValue)}
          subtitle="Combined requested prices"
          icon={<Scale className="h-4 w-4 text-indigo-500" aria-hidden="true" />}
        />
        <SummaryCard
          title="Average Discount"
          value={pct(averageDiscount)}
          subtitle="Across pending requests"
          icon={<TrendingDown className="h-4 w-4 text-rose-500" aria-hidden="true" />}
          variant={(averageDiscount ?? 0) >= 20 ? 'warning' : 'info'}
        />
        <SummaryCard
          title="Oldest Request"
          value={pendingCount > 0 ? `${oldestHours.toFixed(1)}h` : '-'}
          subtitle="Time waiting for review"
          icon={<AlertTriangle className="h-4 w-4 text-rose-500" aria-hidden="true" />}
          variant={oldestHours >= 24 ? 'danger' : pendingCount > 0 ? 'warning' : 'success'}
        />
      </div>

      {message ? (
        <AlertBanner
          variant={message.toLowerCase().includes('failed') ? 'danger' : 'success'}
          dismissable
          onDismiss={() => setMessage('')}
        >
          {message}
        </AlertBanner>
      ) : null}

      {approvals.isLoading ? (
        <div className="flex h-48 items-center justify-center glass-card rounded-2xl">
          <Spinner size="lg" />
        </div>
      ) : null}

      {approvals.isError ? (
        <AlertBanner variant="danger">Unable to load pending approvals. Please refresh the page.</AlertBanner>
      ) : null}

      {!approvals.isLoading && pendingRows.length === 0 ? (
        <section className="grid gap-6 xl:grid-cols-[1fr_360px]">
          <EmptyState
            icon={<BadgeCheck className="h-8 w-8 text-emerald-500" aria-hidden="true" />}
            title="No pending approvals"
            description="All pricing exceptions have been reviewed. New requests will appear here when Sales submits a quote outside policy guardrails."
          />
          
          <div className="glass-card rounded-2xl p-6 shadow-xl relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-emerald-500 to-indigo-500 opacity-60" />
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-emerald-500" aria-hidden="true" />
              <h2 className="text-sm font-bold text-slate-900 dark:text-white">Queue Health</h2>
            </div>
            <div className="mt-4 space-y-4 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
              <p>The approver queue is clear. Keep Upload Center and pricing policy files current so future exceptions have source references.</p>
              <div className="rounded-xl border border-slate-200/50 dark:border-slate-800/40 bg-slate-500/5 p-4">
                <p className="font-bold text-slate-800 dark:text-slate-200 mb-2">Next request will show:</p>
                <ul className="space-y-1.5 font-medium list-disc list-inside">
                  <li>Requested price and discount</li>
                  <li>True margin and leakage comparison</li>
                  <li>Policy violations and source documents</li>
                  <li>Similar historical approval cases</li>
                </ul>
              </div>
            </div>
          </div>
        </section>
      ) : null}

      {pendingRows.length > 0 ? (
        <div className="grid gap-6 2xl:grid-cols-[minmax(0,0.95fr)_minmax(520px,1.05fr)]">
          <ApprovalsTable
            approvals={pendingRows}
            loadingId={loadingId}
            selectedApprovalId={selectedApprovalId}
            onApprove={async (id, reason) => {
              setLoadingId(id);
              await decide.mutateAsync({ id, approve: true, reason });
            }}
            onReject={async (id, reason) => {
              setLoadingId(id);
              await decide.mutateAsync({ id, approve: false, reason });
            }}
            onViewReport={(approvalId) => setSelectedApprovalId(approvalId)}
          />

          <section className="glass-card rounded-2xl shadow-xl overflow-hidden relative flex flex-col">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-indigo-500 to-purple-500 opacity-60" />
            
            <div className="border-b border-slate-200/50 dark:border-slate-800/40 p-6 bg-slate-500/5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <FileSearch className="h-4 w-4 text-indigo-500" aria-hidden="true" />
                    <h2 className="text-sm font-bold text-slate-900 dark:text-white">Business Impact Review</h2>
                  </div>
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    {selectedApprovalId ? `Approval ${selectedApprovalId.slice(0, 8)}` : 'Select an approval to review.'}
                  </p>
                </div>
                {currentContext?.approval.status ? <StatusChip status={currentContext.approval.status} size="md" /> : null}
              </div>
            </div>

            <div className="p-6 flex-1 space-y-6">
              {approvalContext.isLoading ? (
                <div className="flex justify-center py-12">
                  <Spinner size="md" />
                </div>
              ) : null}

              {approvalContext.isError ? (
                <AlertBanner variant="danger">Unable to load business impact context for this approval.</AlertBanner>
              ) : null}

              {!approvalContext.isLoading && !currentContext ? (
                <div className="py-8">
                  <EmptyState
                    icon={<FileCheck2 className="h-8 w-8 text-slate-400" aria-hidden="true" />}
                    title="Select a decision"
                    description="Choose a pending approval to inspect finance, policy, and market context."
                  />
                </div>
              ) : null}

              {currentContext ? (
                <div className="space-y-6">
                  {/* Impact metrics grid */}
                  <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                    <ImpactMetric label="Requested Price" value={money(currentContext.approval.requested_price)} />
                    <ImpactMetric
                      label="AI Recommended"
                      value={money(readNumber(aiSummary, 'recommended_price'))}
                      subvalue={label(readString(currentContext.market_comparison_summary, 'value_positioning_label'))}
                    />
                    <ImpactMetric
                      label="Requested Margin"
                      value={pct(requestedMargin)}
                      subvalue={marginDelta === null ? 'No delta' : `${marginDelta >= 0 ? '+' : ''}${marginDelta.toFixed(2)} pts vs current`}
                      tone={(requestedMargin ?? 0) >= 12 ? 'success' : 'warning'}
                    />
                    <ImpactMetric
                      label="Leakage Impact"
                      value={money(leakageAmount)}
                      subvalue="Estimated at requested price"
                      tone={(leakageAmount ?? 0) > 0 ? 'warning' : 'success'}
                    />
                  </div>

                  <AlertBanner variant="tip" title="Decision Guidance">
                    {currentContext.recommended_action}
                  </AlertBanner>

                  <div className="grid gap-4 xl:grid-cols-2">
                    <ContextPanel
                      title="Quote Summary"
                      icon={<UserRoundCheck className="h-4 w-4 text-indigo-500" aria-hidden="true" />}
                      rows={[
                        ['Customer', readString(currentContext.quote_summary, 'customer_name') ?? '-'],
                        ['Channel', label(readString(currentContext.quote_summary, 'channel'))],
                        ['Product', readString(currentContext.quote_summary, 'product_name') ?? '-'],
                        ['Quantity', String(readNumber(currentContext.quote_summary, 'quantity') ?? '-')],
                        ['Quote Status', label(readString(currentContext.quote_summary, 'status'))],
                      ]}
                    />

                    {/* Market comparison & similar cases */}
                    <div className="rounded-xl border border-slate-200/40 dark:border-slate-800/30 bg-slate-500/5 p-5">
                      <div className="flex items-center gap-2 mb-3">
                        <Sparkles className="h-4 w-4 text-indigo-500" aria-hidden="true" />
                        <p className="text-xs font-bold uppercase tracking-wide text-slate-800 dark:text-slate-200">
                          Market and Similar Cases
                        </p>
                      </div>
                      <p className="text-xs leading-relaxed text-slate-600 dark:text-slate-300 font-medium">
                        {readString(currentContext.market_comparison_summary, 'market_comparison_summary') ??
                          'No competitor context is available for this request.'}
                      </p>
                      
                      <div className="mt-4 space-y-2">
                        {currentContext.similar_cases.length === 0 ? (
                          <p className="rounded-xl border border-slate-200/50 dark:border-slate-800/40 bg-white/40 dark:bg-slate-900/40 p-4 text-xs font-medium text-slate-500 text-center">
                            No similar approval cases found.
                          </p>
                        ) : (
                          currentContext.similar_cases.slice(0, 3).map((item) => (
                            <div key={item.recommendation_id} className="rounded-xl border border-slate-200/40 dark:border-slate-800/40 bg-white/50 dark:bg-slate-900/50 p-3.5 text-xs transition-all duration-300 hover:border-indigo-500/30">
                              <div className="flex flex-wrap items-center justify-between gap-2">
                                <span className="font-bold text-slate-800 dark:text-white">{money(item.recommended_price)}</span>
                                <StatusChip status={item.approval_status} />
                              </div>
                              <p className="mt-1.5 text-slate-500 dark:text-slate-400 font-semibold">
                                Confidence {(item.confidence * 100).toFixed(1)}% |{' '}
                                <span className="text-slate-700 dark:text-slate-300 font-bold">
                                  {item.value_positioning_label ? label(item.value_positioning_label) : 'No value label'}
                                </span>
                              </p>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="grid gap-4 xl:grid-cols-2">
                    <ContextPanel
                      title="Current vs Requested Finance"
                      icon={<Scale className="h-4 w-4 text-indigo-500" aria-hidden="true" />}
                      rows={[
                        ['Current Price', money(readNumber(currentFinance, 'proposed_price'))],
                        ['Current True Margin', pct(currentMargin)],
                        ['Requested Price', money(readNumber(requestedFinance, 'proposed_price'))],
                        ['Requested True Margin', pct(requestedMargin)],
                        ['Current Leakage', money(readNumber(currentFinance, 'leakage_amount'))],
                        ['Requested Leakage', money(readNumber(requestedFinance, 'leakage_amount'))],
                      ]}
                    />

                    {/* Policy violatons block */}
                    <div className="rounded-xl border border-slate-200/40 dark:border-slate-800/30 bg-slate-500/5 p-5">
                      <div className="flex items-center gap-2 mb-3">
                        <ShieldCheck className="h-4 w-4 text-indigo-500" aria-hidden="true" />
                        <p className="text-xs font-bold uppercase tracking-wide text-slate-800 dark:text-slate-200">
                          Policy Source References
                        </p>
                      </div>
                      
                      {currentContext.policy_check?.violations?.length ? (
                        <div className="space-y-2">
                          {currentContext.policy_check.violations.map((violation) => (
                            <div
                              key={`${violation.code}-${violation.message}`}
                              className="rounded-xl border border-slate-200/40 dark:border-slate-800/40 bg-white/50 dark:bg-slate-900/50 p-3.5 text-xs transition-all duration-300 hover:border-rose-500/20"
                            >
                              <div className="mb-1.5 flex flex-wrap items-center justify-between gap-2">
                                <span className="font-bold text-slate-800 dark:text-white">{violation.code}</span>
                                <StatusChip status={violation.severity} />
                              </div>
                              <p className="leading-relaxed text-slate-600 dark:text-slate-300 font-medium">{violation.message}</p>
                              {violation.source_document_id ? (
                                <p className="mt-2 text-[10px] font-bold text-slate-400 dark:text-slate-500">
                                  Source reference: {violation.source_document_id.slice(0, 8)}
                                </p>
                              ) : null}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 text-xs font-semibold text-emerald-600 dark:text-emerald-400 text-center">
                          No policy violations are currently blocking approval.
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ) : null}
            </div>
          </section>
        </div>
      ) : null}
    </div>
  );
}

function ImpactMetric({
  label,
  value,
  subvalue,
  tone = 'default',
}: {
  label: string;
  value: string;
  subvalue?: string;
  tone?: 'default' | 'success' | 'warning';
}) {
  const toneClass = {
    default: 'text-slate-800 dark:text-white',
    success: 'text-emerald-600 dark:text-emerald-400',
    warning: 'text-amber-500 dark:text-amber-400',
  }[tone];

  return (
    <article className="rounded-xl border border-slate-200/50 dark:border-slate-800/40 bg-white/40 dark:bg-slate-900/40 p-4">
      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">{label}</p>
      <p className={`mt-1.5 text-lg font-bold ${toneClass}`}>{value}</p>
      {subvalue && <p className="mt-1 text-[10px] leading-relaxed text-slate-400 dark:text-slate-500 font-medium">{subvalue}</p>}
    </article>
  );
}

function ContextPanel({
  title,
  icon,
  rows,
}: {
  title: string;
  icon: ReactNode;
  rows: Array<[string, string]>;
}) {
  return (
    <div className="rounded-xl border border-slate-200/40 dark:border-slate-800/30 bg-slate-500/5 p-5">
      <div className="flex items-center gap-2">
        <span className="text-indigo-500">{icon}</span>
        <p className="text-xs font-bold uppercase tracking-wide text-slate-800 dark:text-slate-200">{title}</p>
      </div>
      <dl className="mt-3.5 space-y-2">
        {rows.map(([key, value]) => (
          <div key={key} className="flex justify-between gap-4 rounded-xl border border-slate-200/40 dark:border-slate-800/40 bg-white/50 dark:bg-slate-900/50 px-3.5 py-2.5 text-xs font-semibold">
            <dt className="text-slate-500 dark:text-slate-400 font-semibold">{key}</dt>
            <dd className="text-right font-bold text-slate-800 dark:text-slate-200">{value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
