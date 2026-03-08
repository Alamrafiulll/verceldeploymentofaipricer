import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import ApprovalsTable from '../components/ApprovalsTable';
import Spinner from '../components/Spinner';
import { AlertBanner, EmptyState, SectionHeader, SummaryCard } from '../components/ui';
import api from '../lib/api';
import { getSession } from '../lib/auth';
import type { Approval, ApprovalContext } from '../types/api';

const money = (value?: number | null) => (value === null || value === undefined ? '-' : `RM ${value.toFixed(2)}`);
const pct = (value?: number | null) => (value === null || value === undefined ? '-' : `${value.toFixed(2)}%`);
const label = (value?: string | null) =>
  value ? value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase()) : '-';
const readString = (value: Record<string, unknown> | null | undefined, key: string) =>
  typeof value?.[key] === 'string' ? (value[key] as string) : null;
const readNumber = (value: Record<string, unknown> | null | undefined, key: string) =>
  typeof value?.[key] === 'number' ? (value[key] as number) : null;

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
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['approvals', 'pending'] });
      if (selectedApprovalId) {
        await queryClient.invalidateQueries({ queryKey: ['approval-context', selectedApprovalId] });
      }
      setLoadingId(undefined);
      setMessage('Approval decision saved successfully.');
    },
    onError: (error: any) => {
      setLoadingId(undefined);
      const detail = error?.response?.data?.detail;
      setMessage(typeof detail === 'string' ? detail : 'Failed to save approval decision.');
    },
  });

  const pendingCount = approvals.data?.length ?? 0;
  const currentContext = approvalContext.data;
  const aiSummary = currentContext?.ai_recommendation_summary ?? null;
  const currentFinance = currentContext?.current_finance ?? null;
  const requestedFinance = currentContext?.requested_finance ?? null;

  return (
    <div className="space-y-5 p-1">
      <SectionHeader
        icon="✅"
        title="Approval Governance Center"
        subtitle="Review pending pricing exceptions with clear business impact, policy source reference, and market context."
        badge={pendingCount > 0 ? `${pendingCount} pending` : undefined}
      />

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <SummaryCard
          title="Pending Decisions"
          value={pendingCount}
          icon="⏳"
          variant={pendingCount > 0 ? 'warning' : 'success'}
          subtitle={pendingCount > 0 ? 'Needs your review' : 'No open approvals'}
        />
        <SummaryCard
          title="Approval Role"
          value="Sales Director"
          icon="👤"
          subtitle="Decision authority for pricing exceptions"
        />
        <SummaryCard
          title="Review Focus"
          value="Margin and Risk"
          icon="📋"
          subtitle="Check true margin, leakage, and policy source reference"
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
        <div className="flex h-32 items-center justify-center">
          <Spinner size="lg" />
        </div>
      ) : null}

      {approvals.isError ? (
        <AlertBanner variant="danger">
          Unable to load pending approvals. Please refresh the page.
        </AlertBanner>
      ) : null}

      {approvals.data && approvals.data.length === 0 ? (
        <EmptyState
          icon="🎯"
          title="No pending approvals"
          description="All pricing exceptions have been reviewed. New requests will appear here when Sales submits a quote outside policy guardrails."
        />
      ) : null}

      {approvals.data && approvals.data.length > 0 ? (
        <ApprovalsTable
          approvals={approvals.data}
          loadingId={loadingId}
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
      ) : null}

      {selectedApprovalId ? (
        <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <SectionHeader
            icon="📊"
            title="Business Impact Review"
            subtitle={`Approval: ${selectedApprovalId.slice(0, 8)}`}
          />

          {approvalContext.isLoading ? (
            <div className="flex justify-center py-4">
              <Spinner size="md" />
            </div>
          ) : null}

          {currentContext ? (
            <>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
                <SummaryCard
                  title="Requested Price"
                  value={money(currentContext.approval.requested_price)}
                  subtitle="Sales request"
                />
                <SummaryCard
                  title="AI Recommended Price"
                  value={money(readNumber(aiSummary, 'recommended_price'))}
                  subtitle={label(readString(currentContext.market_comparison_summary, 'value_positioning_label'))}
                />
                <SummaryCard
                  title="Requested True Margin"
                  value={pct(readNumber(requestedFinance, 'net_margin_percent'))}
                  subtitle={money(readNumber(requestedFinance, 'net_margin_amount'))}
                  variant={(readNumber(requestedFinance, 'net_margin_percent') ?? 0) >= 12 ? 'success' : 'warning'}
                />
                <SummaryCard
                  title="Leakage Impact"
                  value={money(readNumber(requestedFinance, 'leakage_amount'))}
                  subtitle="Estimated value leakage at requested price"
                  variant={(readNumber(requestedFinance, 'leakage_amount') ?? 0) > 0 ? 'warning' : 'success'}
                />
              </div>

              <AlertBanner variant="tip" title="Recommended Action">
                {currentContext.recommended_action}
              </AlertBanner>

              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                  <p className="text-sm font-semibold text-slate-700">Quote Summary</p>
                  <div className="mt-3 space-y-2 text-sm text-slate-700">
                    <div>Customer: {readString(currentContext.quote_summary, 'customer_name') ?? '-'}</div>
                    <div>Channel: {readString(currentContext.quote_summary, 'channel') ?? '-'}</div>
                    <div>Product: {readString(currentContext.quote_summary, 'product_name') ?? '-'}</div>
                    <div>Quantity: {readNumber(currentContext.quote_summary, 'quantity') ?? '-'}</div>
                    <div>Status: {label(readString(currentContext.quote_summary, 'status'))}</div>
                  </div>
                </div>

                <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                  <p className="text-sm font-semibold text-slate-700">Market and Similar Cases</p>
                  <p className="mt-3 text-sm text-slate-700">
                    {readString(currentContext.market_comparison_summary, 'market_comparison_summary') ??
                      'No competitor context is available for this request.'}
                  </p>
                  <div className="mt-3 space-y-2">
                    {currentContext.similar_cases.slice(0, 3).map((item) => (
                      <div key={item.recommendation_id} className="rounded-md border border-slate-200 bg-white p-3 text-sm">
                        <div className="font-semibold">
                          {money(item.recommended_price)} | {label(item.approval_status)}
                        </div>
                        <div>
                          Confidence {(item.confidence * 100).toFixed(1)}% |{' '}
                          {item.value_positioning_label ? label(item.value_positioning_label) : 'No value label'}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                  <p className="text-sm font-semibold text-slate-700">Current vs Requested Finance</p>
                  <div className="mt-3 space-y-2 text-sm text-slate-700">
                    <div>Current Price: {money(readNumber(currentFinance, 'proposed_price'))}</div>
                    <div>Current True Margin: {pct(readNumber(currentFinance, 'net_margin_percent'))}</div>
                    <div>Requested Price: {money(readNumber(requestedFinance, 'proposed_price'))}</div>
                    <div>Requested True Margin: {pct(readNumber(requestedFinance, 'net_margin_percent'))}</div>
                    <div>Current Leakage: {money(readNumber(currentFinance, 'leakage_amount'))}</div>
                    <div>Requested Leakage: {money(readNumber(requestedFinance, 'leakage_amount'))}</div>
                  </div>
                </div>

                <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                  <p className="text-sm font-semibold text-slate-700">Policy Source References</p>
                  {currentContext.policy_check?.violations?.length ? (
                    <div className="mt-3 space-y-2">
                      {currentContext.policy_check.violations.map((violation) => (
                        <div key={`${violation.code}-${violation.message}`} className="rounded-md border border-slate-200 bg-white p-3 text-sm">
                          <div className="font-semibold">
                            {violation.code} | {violation.severity.toUpperCase()}
                          </div>
                          <div>{violation.message}</div>
                          {violation.source_document_id ? (
                            <div className="text-xs text-slate-500">
                              Policy source reference: {violation.source_document_id.slice(0, 8)}
                            </div>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="mt-3 text-sm text-emerald-700">
                      No policy violations are currently blocking approval.
                    </p>
                  )}
                </div>
              </div>
            </>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}
