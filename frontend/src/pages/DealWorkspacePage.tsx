import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Calculator,
  FileCheck2,
  MessageSquareText,
  RefreshCw,
  Send,
  ShieldCheck,
} from 'lucide-react';

import DealInputForm, { type DealFormValues } from '../components/DealInputForm';
import ExplanationBox from '../components/ExplanationBox';
import MarginSimulator from '../components/MarginSimulator';
import RecommendationPanel from '../components/RecommendationPanel';
import { AlertBanner, SectionHeader, StatusChip } from '../components/ui';
import api from '../lib/api';
import type {
  Customer,
  Inventory,
  NegotiationAssistant,
  Product,
  QuoteDetail,
  QuoteFinanceSnapshot,
  QuotePolicyCheck,
  Recommendation,
  StrategyMode,
} from '../types/api';

export default function DealWorkspacePage() {
  const params = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const quoteId = params.id;

  const [strategyMode, setStrategyMode] = useState<StrategyMode>('maximize_profit');
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [simPrice, setSimPrice] = useState<number>(0);
  const [approvalReason, setApprovalReason] = useState('');
  const [message, setMessage] = useState('');

  const customers = useQuery({
    queryKey: ['customers'],
    queryFn: async () => (await api.get<Customer[]>('/customers')).data,
  });
  const products = useQuery({
    queryKey: ['products'],
    queryFn: async () => (await api.get<Product[]>('/products')).data,
  });
  const inventory = useQuery({
    queryKey: ['inventory'],
    queryFn: async () => (await api.get<Inventory[]>('/inventory')).data,
  });

  const quote = useQuery({
    queryKey: ['quote', quoteId],
    enabled: Boolean(quoteId),
    queryFn: async () => (await api.get<QuoteDetail>(`/quotes/${quoteId}`)).data,
  });
  const policyCheck = useQuery({
    queryKey: ['quote-policy', quoteId],
    enabled: Boolean(quoteId),
    queryFn: async () => (await api.get<QuotePolicyCheck>(`/quotes/${quoteId}/policy-check`)).data,
  });
  const financeSnapshot = useQuery({
    queryKey: ['quote-finance', quoteId],
    enabled: Boolean(quoteId),
    queryFn: async () => (await api.get<QuoteFinanceSnapshot>(`/quotes/${quoteId}/finance`)).data,
  });
  const negotiationAssistant = useQuery({
    queryKey: ['quote-negotiation', quoteId],
    enabled: Boolean(quoteId && recommendation),
    queryFn: async () =>
      (await api.get<NegotiationAssistant>(`/quotes/${quoteId}/negotiation-assistant`)).data,
  });

  useEffect(() => {
    if (!quote.data) return;
    setStrategyMode(quote.data.strategy_mode);

    const optimizer = quote.data.latest_recommendation?.optimizer as
      | {
          best: {
            price: number;
            discount_percent: number;
            margin_percent: number;
            expected_profit: number;
            win_probability: number;
          };
          band_low: number;
          band_high: number;
          suggested_discount_low: number;
          suggested_discount_high: number;
          confidence: number;
          points: Recommendation['candidates'];
        }
      | undefined;
    const gpt = quote.data.latest_recommendation?.gpt as Recommendation['explanation'] | undefined;

    if (optimizer && gpt) {
      const rec: Recommendation = {
        quote_id: quote.data.id,
        band_low: optimizer.band_low,
        band_high: optimizer.band_high,
        best_price: optimizer.best.price,
        suggested_discount_low: optimizer.suggested_discount_low,
        suggested_discount_high: optimizer.suggested_discount_high,
        win_probability: optimizer.best.win_probability,
        expected_profit: optimizer.best.expected_profit,
        margin_percent: optimizer.best.margin_percent,
        confidence: optimizer.confidence,
        risk_level: (quote.data.item.risk_level ?? 'medium') as Recommendation['risk_level'],
        safe_band:
          quote.data.item.risk_level === 'high'
            ? 'red'
            : quote.data.item.risk_level === 'medium'
              ? 'yellow'
              : 'green',
        explanation: gpt,
        candidates: optimizer.points,
      };
      setRecommendation(rec);
      setSimPrice(quote.data.item.final_price ?? quote.data.item.requested_price ?? rec.best_price);
    }
  }, [quote.data]);

  const createAndRecommend = useMutation({
    mutationFn: async (payload: DealFormValues) => {
      const createRes = await api.post<{ id: string }>('/quotes', {
        customer_id: payload.customer_id,
        channel: payload.channel,
        strategy_mode: payload.strategy_mode,
        item: {
          product_id: payload.product_id,
          quantity: payload.quantity,
          requested_price: payload.requested_price,
          requested_discount: payload.requested_discount,
        },
      });
      const id = createRes.data.id;
      const recRes = await api.post<Recommendation>(`/quotes/${id}/recommend`);
      return { id, recommendation: recRes.data };
    },
    onSuccess: ({ id, recommendation: rec }) => {
      setRecommendation(rec);
      setSimPrice(rec.best_price);
      setMessage('AI recommendation generated.');
      queryClient.invalidateQueries({ queryKey: ['quotes', 'mine'] });
      queryClient.invalidateQueries({ queryKey: ['quote-policy', id] });
      navigate(`/sales/quotes/${id}`);
    },
    onError: () => setMessage('Unable to generate recommendation.'),
  });

  const regenerate = useMutation({
    mutationFn: async () => {
      if (!quoteId) throw new Error('Missing quote');
      return (await api.post<Recommendation>(`/quotes/${quoteId}/recommend`)).data;
    },
    onSuccess: (rec) => {
      setRecommendation(rec);
      setSimPrice(rec.best_price);
      setMessage('Recommendation refreshed.');
      queryClient.invalidateQueries({ queryKey: ['quote', quoteId] });
      queryClient.invalidateQueries({ queryKey: ['quote-policy', quoteId] });
      queryClient.invalidateQueries({ queryKey: ['quote-negotiation', quoteId] });
    },
    onError: () => setMessage('Failed to refresh recommendation.'),
  });

  const finalize = useMutation({
    mutationFn: async () => {
      if (!quoteId) throw new Error('Missing quote');
      return api.post(`/quotes/${quoteId}/finalize`, { final_price: simPrice });
    },
    onSuccess: async () => {
      setMessage('Quote finalized successfully.');
      await queryClient.invalidateQueries({ queryKey: ['quote', quoteId] });
      await queryClient.invalidateQueries({ queryKey: ['quotes', 'mine'] });
      await queryClient.invalidateQueries({ queryKey: ['quote-policy', quoteId] });
      await queryClient.invalidateQueries({ queryKey: ['quote-negotiation', quoteId] });
    },
    onError: (error: unknown) => {
      const fallback = 'Finalize failed. Approval may be required.';
      if (typeof error === 'object' && error && 'response' in error) {
        const messageFromApi =
          (error as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? fallback;
        setMessage(messageFromApi);
      } else {
        setMessage(fallback);
      }
    },
  });

  const requestApproval = useMutation({
    mutationFn: async () => {
      if (!quoteId || !recommendation) throw new Error('Missing quote');
      if (recommendation.candidates.length === 0) throw new Error('No recommendation candidates');
      const nearest = recommendation.candidates.reduce((prev, curr) =>
        Math.abs(curr.price - simPrice) < Math.abs(prev.price - simPrice) ? curr : prev,
      );
      return api.post(`/quotes/${quoteId}/request-approval`, {
        requested_price: simPrice,
        requested_discount: nearest.discount_percent,
        justification: approvalReason || recommendation.explanation.approval_justification_suggestion || 'Requested outside AI safe band.',
      });
    },
    onSuccess: async () => {
      setMessage('Approval requested.');
      await queryClient.invalidateQueries({ queryKey: ['quote', quoteId] });
      await queryClient.invalidateQueries({ queryKey: ['quotes', 'mine'] });
      await queryClient.invalidateQueries({ queryKey: ['quote-policy', quoteId] });
      await queryClient.invalidateQueries({ queryKey: ['approvals', 'pending'] });
    },
    onError: (error: unknown) => {
      const fallback = 'Unable to request approval.';
      if (typeof error === 'object' && error && 'response' in error) {
        const detail =
          (error as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? fallback;
        setMessage(detail);
        return;
      }
      if (error instanceof Error) {
        setMessage(error.message);
        return;
      }
      setMessage(fallback);
    },
  });

  const simulateFinance = useMutation({
    mutationFn: async () => {
      if (!quoteId) throw new Error('Missing quote');
      return (
        await api.post<QuoteFinanceSnapshot>(`/quotes/${quoteId}/simulate-finance`, {
          proposed_price: simPrice,
        })
      ).data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quote-finance', quoteId] });
    },
  });

  const saveDraft = useMutation({
    mutationFn: async () => {
      if (!quoteId) throw new Error('Missing quote');
      return api.post(`/quotes/${quoteId}/save-draft`, {
        requested_price: simPrice,
        strategy_mode: strategyMode,
      });
    },
    onSuccess: async () => {
      setMessage('Draft saved successfully.');
      await queryClient.invalidateQueries({ queryKey: ['quote', quoteId] });
      await queryClient.invalidateQueries({ queryKey: ['quotes', 'mine'] });
      await queryClient.invalidateQueries({ queryKey: ['quote-policy', quoteId] });
      await queryClient.invalidateQueries({ queryKey: ['quote-negotiation', quoteId] });
      await queryClient.invalidateQueries({ queryKey: ['quote-finance', quoteId] });
    },
    onError: (error: unknown) => {
      const fallback = 'Failed to save draft.';
      if (typeof error === 'object' && error && 'response' in error) {
        const detail =
          (error as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? fallback;
        setMessage(detail);
        return;
      }
      if (error instanceof Error) {
        setMessage(error.message);
        return;
      }
      setMessage(fallback);
    },
  });

  const pageLoading = customers.isLoading || products.isLoading || inventory.isLoading || quote.isLoading;

  const selectedPoint = useMemo(() => {
    if (!recommendation || recommendation.candidates.length === 0) return null;
    return recommendation.candidates.reduce((prev, curr) =>
      Math.abs(curr.price - simPrice) < Math.abs(prev.price - simPrice) ? curr : prev,
    );
  }, [recommendation, simPrice]);

  return (
    <div className="space-y-6">
      {pageLoading ? <AlertBanner variant="info">Loading quote workspace data...</AlertBanner> : null}

      {!quoteId ? (
        <>
          <SectionHeader
            kicker="Quote workflow"
            icon={<FileCheck2 className="h-5 w-5" aria-hidden="true" />}
            title="New Quote"
            subtitle="Build a governed pricing recommendation from customer, product, and requested price context."
            action={
              <button
                type="button"
                onClick={() => navigate('/sales')}
                className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              >
                <ArrowLeft className="h-4 w-4" aria-hidden="true" />
                Workspace
              </button>
            }
          />
          <DealInputForm
            customers={customers.data ?? []}
            products={products.data ?? []}
            inventory={inventory.data ?? []}
            strategyMode={strategyMode}
            onStrategyChange={setStrategyMode}
            loading={createAndRecommend.isPending}
            onSubmit={(payload) => createAndRecommend.mutate(payload)}
          />
        </>
      ) : (
        <SectionHeader
          kicker="Deal workspace"
          icon={<FileCheck2 className="h-5 w-5" aria-hidden="true" />}
          title={quote.data?.customer_name ?? 'Quote Detail'}
          subtitle={`Quote ${quoteId.slice(0, 8)}. Review the recommendation, simulate margin, verify policy, and finalize or route approval.`}
          badge={quote.data?.status ? quote.data.status.replace(/_/g, ' ') : undefined}
          action={
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => navigate('/sales')}
                className="btn-outline flex items-center justify-center gap-2"
              >
                <ArrowLeft className="h-4 w-4" aria-hidden="true" />
                Workspace
              </button>
              <button
                type="button"
                className="btn-primary flex items-center justify-center gap-2"
                onClick={() => regenerate.mutate()}
                disabled={regenerate.isPending}
              >
                <RefreshCw className="h-4 w-4" aria-hidden="true" />
                {regenerate.isPending ? 'Refreshing' : 'Regenerate'}
              </button>
            </div>
          }
        />
      )}

      {recommendation ? (
        <>
          <RecommendationPanel recommendation={recommendation} />
          <ExplanationBox explanation={recommendation.explanation} />
          <MarginSimulator
            candidates={recommendation.candidates}
            value={simPrice || recommendation.best_price}
            onChange={setSimPrice}
          />

          {quoteId ? (
            <section className="glass-card rounded-2xl p-6 border border-slate-200/60 dark:border-slate-800/60 shadow-sm transition-all duration-300">
              <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-600 dark:bg-indigo-500/25 dark:text-indigo-400">
                    <Calculator className="h-5 w-5" aria-hidden="true" />
                  </span>
                  <div>
                    <h2 className="text-base font-extrabold text-slate-900 dark:text-white">True Margin Panel</h2>
                    <p className="text-xs font-semibold text-slate-400 dark:text-slate-500">Live finance impact evaluation</p>
                  </div>
                </div>
                <button
                  type="button"
                  className="btn-outline flex items-center justify-center gap-2"
                  onClick={() => simulateFinance.mutate()}
                  disabled={simulateFinance.isPending}
                >
                  {simulateFinance.isPending ? 'Calculating...' : 'Recalculate Selected Price'}
                </button>
              </div>
              {financeSnapshot.data ? (
                <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                  <Metric label="Revenue" value={`RM ${financeSnapshot.data.revenue_total.toFixed(2)}`} />
                  <Metric label="Gross Margin" value={`RM ${financeSnapshot.data.gross_margin_amount.toFixed(2)}`} />
                  <Metric label="Net Margin" value={`${financeSnapshot.data.net_margin_percent.toFixed(2)}%`} />
                  <Metric label="Rebate" value={`RM ${financeSnapshot.data.rebate_amount.toFixed(2)}`} />
                  <Metric label="MDF" value={`RM ${financeSnapshot.data.mdf_amount.toFixed(2)}`} />
                  <Metric
                    label="Freight + Fees"
                    value={`RM ${(financeSnapshot.data.freight_amount + financeSnapshot.data.fees_amount).toFixed(2)}`}
                  />
                </div>
              ) : (
                <p className="text-xs font-semibold text-slate-500">No finance snapshot yet.</p>
              )}
            </section>
          ) : null}

          {quoteId && negotiationAssistant.data ? (
            <section className="glass-card rounded-2xl p-6 border border-slate-200/60 dark:border-slate-800/60 shadow-sm transition-all duration-300">
              <div className="mb-5 flex items-center gap-3">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-purple-500/10 text-purple-600 dark:bg-purple-500/25 dark:text-purple-400">
                  <MessageSquareText className="h-5 w-5" aria-hidden="true" />
                </span>
                <div>
                  <h2 className="text-base font-extrabold text-slate-900 dark:text-white">Negotiation Assistant</h2>
                  <p className="text-xs font-semibold text-slate-400 dark:text-slate-500">AI suggested tactical counters</p>
                </div>
              </div>
              <p className="text-sm font-semibold leading-relaxed text-slate-600 dark:text-slate-350">{negotiationAssistant.data.strategy_summary}</p>
              <div className="mt-4 grid gap-3 sm:grid-cols-2 md:grid-cols-3">
                {negotiationAssistant.data.concession_ladder.map((step) => (
                  <div key={step.step} className="rounded-xl border border-indigo-200/40 dark:border-indigo-900/30 bg-indigo-500/5 p-4 transition-all duration-200 hover:bg-indigo-500/10">
                    <div className="font-extrabold text-sm text-indigo-600 dark:text-indigo-400">
                      Step {step.step}: RM {step.target_price.toFixed(2)}
                    </div>
                    <div className="mt-1 text-xs font-semibold leading-relaxed text-slate-500 dark:text-slate-400">{step.message}</div>
                  </div>
                ))}
              </div>
              <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
                <GuidanceList title="Guardrails" items={negotiationAssistant.data.guardrails} />
                <GuidanceList title="Must Not Do" items={negotiationAssistant.data.must_not_do} />
              </div>
            </section>
          ) : null}

          {quoteId ? (
            <section className="glass-card rounded-2xl p-6 border border-slate-200/60 dark:border-slate-800/60 shadow-sm transition-all duration-300">
              <div className="mb-5 flex items-center gap-3">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-600 dark:bg-emerald-500/25 dark:text-emerald-400">
                  <ShieldCheck className="h-5 w-5" aria-hidden="true" />
                </span>
                <div>
                  <h2 className="text-base font-extrabold text-slate-900 dark:text-white">Policy and Campaign Check</h2>
                  <p className="text-xs font-semibold text-slate-400 dark:text-slate-500">Compliance & discount governance</p>
                </div>
              </div>
              {policyCheck.isLoading ? <p className="text-xs font-semibold text-slate-500">Checking policy compliance...</p> : null}
              {policyCheck.data ? (
                <div className="grid gap-6 lg:grid-cols-2">
                  <div>
                    <p className="mb-3 text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">Violations</p>
                    {policyCheck.data.violations.length === 0 ? (
                      <div className="rounded-xl border border-emerald-200/50 bg-emerald-500/5 dark:border-emerald-900/30 p-4 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                        No policy violations detected.
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {policyCheck.data.violations.map((violation) => (
                          <div
                            key={`${violation.code}-${violation.message}`}
                            className={`rounded-xl border p-4 text-xs ${
                              violation.severity === 'high'
                                ? 'border-rose-500/25 bg-rose-500/5 text-rose-700 dark:text-rose-400'
                                : violation.severity === 'medium'
                                  ? 'border-amber-500/25 bg-amber-500/5 text-amber-700 dark:text-amber-400'
                                  : 'border-slate-200 bg-slate-500/5 text-slate-600 dark:text-slate-400'
                            }`}
                          >
                            <div className="mb-1.5 flex items-center justify-between gap-2">
                              <div className="font-extrabold">{violation.code}</div>
                              <StatusChip status={violation.severity} />
                            </div>
                            <div className="font-semibold leading-relaxed">{violation.message}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div>
                    <p className="mb-3 text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">Entitlements</p>
                    {policyCheck.data.entitlements.length === 0 ? (
                      <div className="rounded-xl border border-slate-200/50 bg-slate-500/5 p-4 text-xs font-semibold text-slate-500 dark:text-slate-400">
                        No campaign entitlements for this quote.
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {policyCheck.data.entitlements.map((entitlement) => (
                          <div
                            key={entitlement.campaign_id}
                            className="rounded-xl border border-emerald-200/50 bg-emerald-500/5 dark:border-emerald-900/30 p-4 text-xs font-semibold text-emerald-600 dark:text-emerald-400"
                          >
                            <div className="font-extrabold text-emerald-700 dark:text-emerald-400">{entitlement.campaign_name}</div>
                            <div className="mt-1 font-semibold leading-relaxed">
                              Gifts: {entitlement.sku_codes.join(', ')} | Qty: {entitlement.quantity}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ) : null}
            </section>
          ) : null}

          <section className="glass-card rounded-2xl p-6 border border-slate-200/60 dark:border-slate-800/60 shadow-sm transition-all duration-300">
            <div className="mb-5 flex items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-600 dark:bg-indigo-500/25 dark:text-indigo-400">
                <Send className="h-5 w-5" aria-hidden="true" />
              </span>
              <div>
                <h2 className="text-base font-extrabold text-slate-900 dark:text-white">Finalize or Request Approval</h2>
                <p className="text-xs font-semibold text-slate-400 dark:text-slate-500">Lock-in price or route for executive governance</p>
              </div>
            </div>
            <div className="grid gap-3 md:grid-cols-3">
              <Metric label="Selected Price" value={`RM ${simPrice.toFixed(2)}`} />
              <Metric label="Margin" value={selectedPoint ? `${selectedPoint.margin_percent.toFixed(2)}%` : '-'} />
              <Metric
                label="Expected Profit"
                value={selectedPoint ? `RM ${selectedPoint.expected_profit.toFixed(2)}` : '-'}
              />
            </div>
            <textarea
              value={approvalReason}
              onChange={(event) => setApprovalReason(event.target.value)}
              className="input mt-4 min-h-28"
              placeholder="Justification for override or approval request"
            />
            <div className="mt-5 flex flex-wrap gap-3">
              {quoteId ? (
                <button
                  type="button"
                  className="btn-primary flex items-center justify-center gap-2"
                  disabled={finalize.isPending}
                  onClick={() => finalize.mutate()}
                >
                  {finalize.isPending ? 'Finalizing...' : 'Finalize Quote'}
                </button>
              ) : null}

              {quoteId ? (
                <button
                  type="button"
                  className="btn-outline flex items-center justify-center gap-2"
                  disabled={requestApproval.isPending}
                  onClick={() => requestApproval.mutate()}
                >
                  {requestApproval.isPending ? 'Submitting...' : 'Request Approval'}
                </button>
              ) : null}

              {quoteId && ['draft', 'recommended', 'rejected'].includes(quote.data?.status ?? '') ? (
                <button
                  type="button"
                  className="btn-outline flex items-center justify-center gap-2"
                  disabled={saveDraft.isPending}
                  onClick={() => saveDraft.mutate()}
                >
                  {saveDraft.isPending ? 'Saving...' : 'Save Draft'}
                </button>
              ) : null}
            </div>
          </section>
        </>
      ) : null}

      {message ? <AlertBanner variant={message.toLowerCase().includes('failed') ? 'danger' : 'info'}>{message}</AlertBanner> : null}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200/60 dark:border-slate-800/40 bg-slate-500/5 p-3.5 transition-all duration-300">
      <p className="text-[10px] font-extrabold uppercase tracking-[0.16em] text-slate-400 dark:text-slate-500">{label}</p>
      <p className="mt-1.5 font-display text-sm sm:text-base font-bold tracking-tight text-slate-900 dark:text-white">{value}</p>
    </div>
  );
}

function GuidanceList({ title, items }: { title: string; items: string[] }) {
  const isGuardrails = title.toLowerCase() === 'guardrails';
  return (
    <div className={`rounded-xl border p-4.5 ${isGuardrails ? 'border-emerald-200/60 bg-emerald-500/5 dark:border-emerald-900/20 dark:bg-emerald-950/10' : 'border-rose-200/60 bg-rose-500/5 dark:border-rose-900/20 dark:bg-rose-950/10'}`}>
      <p className={`text-xs font-extrabold uppercase tracking-[0.14em] ${isGuardrails ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}`}>{title}</p>
      <ul className="mt-3.5 space-y-2 text-xs font-semibold leading-relaxed text-slate-600 dark:text-slate-350">
        {items.map((item) => (
          <li key={item} className="flex items-start gap-2">
            <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${isGuardrails ? 'bg-emerald-500' : 'bg-rose-500'}`} />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
