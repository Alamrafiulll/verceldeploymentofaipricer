import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';

import DealInputForm, { type DealFormValues } from '../components/DealInputForm';
import ExplanationBox from '../components/ExplanationBox';
import MarginSimulator from '../components/MarginSimulator';
import RecommendationPanel from '../components/RecommendationPanel';
import { AlertBanner, SummaryCard } from '../components/ui';
import api from '../lib/api';
import type {
  Customer,
  Inventory,
  MarketComparison,
  NegotiationAssistant,
  Product,
  QuoteDetail,
  QuoteFinanceSnapshot,
  QuotePolicyCheck,
  Recommendation,
  StrategyMode,
} from '../types/api';

const money = (value?: number | null) => (value === null || value === undefined ? '-' : `RM ${value.toFixed(2)}`);
const pct = (value?: number | null) => (value === null || value === undefined ? '-' : `${value.toFixed(2)}%`);
const label = (value?: string | null) =>
  value ? value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase()) : '-';
const readString = (value: Record<string, unknown> | null | undefined, key: string) =>
  typeof value?.[key] === 'string' ? (value[key] as string) : null;
const readNumber = (value: Record<string, unknown> | null | undefined, key: string) =>
  typeof value?.[key] === 'number' ? (value[key] as number) : null;

export default function DealWorkspacePage() {
  const params = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const quoteId = params.id;
  const [strategyMode, setStrategyMode] = useState<StrategyMode>('maximize_profit');
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [simPrice, setSimPrice] = useState(0);
  const [approvalReason, setApprovalReason] = useState('');
  const [message, setMessage] = useState('');

  const customers = useQuery({ queryKey: ['customers'], queryFn: async () => (await api.get<Customer[]>('/customers')).data });
  const products = useQuery({ queryKey: ['products'], queryFn: async () => (await api.get<Product[]>('/products')).data });
  const inventory = useQuery({ queryKey: ['inventory'], queryFn: async () => (await api.get<Inventory[]>('/inventory')).data });
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
    queryFn: async () => (await api.get<NegotiationAssistant>(`/quotes/${quoteId}/negotiation-assistant`)).data,
  });
  const marketComparison = useQuery({
    queryKey: ['quote-market', quote.data?.item.product_id],
    enabled: Boolean(quote.data?.item.product_id),
    queryFn: async () => (await api.get<MarketComparison>(`/market/compare/${quote.data?.item.product_id}`)).data,
  });

  useEffect(() => {
    if (!quote.data) return;
    setStrategyMode(quote.data.strategy_mode);
    const optimizer = quote.data.latest_recommendation?.optimizer as
      | {
          best: { price: number; margin_percent: number; expected_profit: number; win_probability: number };
          band_low: number;
          band_high: number;
          suggested_discount_low: number;
          suggested_discount_high: number;
          confidence: number;
          points: Recommendation['candidates'];
        }
      | undefined;
    const gpt = quote.data.latest_recommendation?.gpt as Recommendation['explanation'] | undefined;
    if (!optimizer || !gpt) return;
    setRecommendation({
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
      safe_band: quote.data.item.risk_level === 'high' ? 'red' : quote.data.item.risk_level === 'medium' ? 'yellow' : 'green',
      explanation: gpt,
      candidates: optimizer.points,
      pricebook_compliance_summary: quote.data.pricebook_compliance_summary,
      contract_pricing_summary: quote.data.contract_pricing_summary,
      market_comparison_summary: quote.data.market_comparison_summary,
      value_positioning_label: readString(quote.data.market_comparison_summary, 'value_positioning_label'),
      next_best_action: label(readString(quote.data.market_comparison_summary, 'recommended_strategy')),
    });
    setSimPrice(quote.data.item.final_price ?? optimizer.best.price);
  }, [quote.data]);

  const refreshQuote = async (id: string) => {
    await queryClient.invalidateQueries({ queryKey: ['quote', id] });
    await queryClient.invalidateQueries({ queryKey: ['quote-policy', id] });
    await queryClient.invalidateQueries({ queryKey: ['quote-finance', id] });
    await queryClient.invalidateQueries({ queryKey: ['quote-negotiation', id] });
  };

  const createAndRecommend = useMutation({
    mutationFn: async (payload: DealFormValues) => {
      const created = await api.post<{ id: string }>('/quotes', {
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
      const rec = await api.post<Recommendation>(`/quotes/${created.data.id}/recommend`);
      return { id: created.data.id, recommendation: rec.data };
    },
    onSuccess: ({ id, recommendation: rec }) => {
      setRecommendation(rec);
      setSimPrice(rec.best_price);
      setMessage('Explainable recommendation generated.');
      navigate(`/sales/quotes/${id}`);
    },
    onError: () => setMessage('Unable to generate recommendation.'),
  });
  const regenerate = useMutation({
    mutationFn: async () => (await api.post<Recommendation>(`/quotes/${quoteId}/recommend`)).data,
    onSuccess: async (rec) => {
      setRecommendation(rec);
      setSimPrice(rec.best_price);
      setMessage('Recommendation refreshed.');
      if (quoteId) await refreshQuote(quoteId);
    },
  });
  const finalize = useMutation({
    mutationFn: async () => api.post(`/quotes/${quoteId}/finalize`, { final_price: simPrice }),
    onSuccess: async () => {
      setMessage('Quote finalized successfully.');
      if (quoteId) await refreshQuote(quoteId);
    },
    onError: (error: unknown) => {
      const detail =
        typeof error === 'object' && error && 'response' in error
          ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null;
      setMessage(detail ?? 'Finalize failed. Approval may be required.');
    },
  });
  const requestApproval = useMutation({
    mutationFn: async () => {
      if (!recommendation) throw new Error('Missing recommendation');
      const nearest = recommendation.candidates.reduce((prev, curr) =>
        Math.abs(curr.price - simPrice) < Math.abs(prev.price - simPrice) ? curr : prev,
      );
      return api.post(`/quotes/${quoteId}/request-approval`, {
        requested_price: simPrice,
        requested_discount: nearest.discount_percent,
        justification:
          approvalReason || recommendation.explanation.approval_justification_suggestion || 'Requested outside AI safe band.',
      });
    },
    onSuccess: async () => {
      setMessage('Approval requested.');
      if (quoteId) await refreshQuote(quoteId);
      await queryClient.invalidateQueries({ queryKey: ['approvals', 'pending'] });
    },
  });
  const simulateFinance = useMutation({
    mutationFn: async () => (await api.post<QuoteFinanceSnapshot>(`/quotes/${quoteId}/simulate-finance`, { proposed_price: simPrice })).data,
    onSuccess: async () => {
      if (quoteId) await queryClient.invalidateQueries({ queryKey: ['quote-finance', quoteId] });
    },
  });

  const selectedPoint = useMemo(() => {
    if (!recommendation || recommendation.candidates.length === 0) return null;
    return recommendation.candidates.reduce((prev, curr) =>
      Math.abs(curr.price - simPrice) < Math.abs(prev.price - simPrice) ? curr : prev,
    );
  }, [recommendation, simPrice]);

  const finance = financeSnapshot.data;
  const nextBestAction =
    recommendation?.next_best_action ?? policyCheck.data?.recommended_action ?? label(marketComparison.data?.recommended_strategy);
  const valuePositioning =
    recommendation?.value_positioning_label ?? marketComparison.data?.value_positioning_label ?? readString(quote.data?.market_comparison_summary, 'value_positioning_label');
  const loading = customers.isLoading || products.isLoading || inventory.isLoading || quote.isLoading;

  return (
    <div className="space-y-5">
      {loading ? <p className="text-sm text-slate-600">Loading workspace...</p> : null}

      {!quoteId ? (
        <DealInputForm
          customers={customers.data ?? []}
          products={products.data ?? []}
          inventory={inventory.data ?? []}
          strategyMode={strategyMode}
          onStrategyChange={setStrategyMode}
          loading={createAndRecommend.isPending}
          onSubmit={(payload) => createAndRecommend.mutate(payload)}
        />
      ) : (
        <section className="rounded-2xl border border-white/70 bg-white p-5 shadow-card">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="font-display text-2xl font-semibold">Deal Workspace</h2>
              <p className="text-sm text-slate-600">Quote {quoteId?.slice(0, 8)} | Status: {quote.data?.status ?? '-'}</p>
            </div>
            <button type="button" className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold" onClick={() => regenerate.mutate()} disabled={regenerate.isPending}>
              {regenerate.isPending ? 'Refreshing...' : 'Refresh Recommendation'}
            </button>
          </div>
        </section>
      )}

      {recommendation ? (
        <>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
            <SummaryCard title="Recommended Action" value={nextBestAction || 'Review Quote'} subtitle="What to do next" variant="info" />
            <SummaryCard title="True Margin" value={pct(finance?.net_margin_percent ?? recommendation.margin_percent)} subtitle="Current net true margin" variant={(finance?.net_margin_percent ?? recommendation.margin_percent) >= 12 ? 'success' : 'warning'} />
            <SummaryCard title="Leakage Control" value={money(finance?.leakage_amount)} subtitle="Estimated value leakage" variant={(finance?.leakage_amount ?? 0) > 0 ? 'warning' : 'success'} />
            <SummaryCard title="Value Positioning" value={label(valuePositioning)} subtitle="Uploaded market view" />
          </div>

          {nextBestAction ? <AlertBanner variant="tip" title="Recommended Action">{nextBestAction}</AlertBanner> : null}
          <RecommendationPanel recommendation={recommendation} />
          <ExplanationBox explanation={recommendation.explanation} explanationLevels={recommendation.explanation_levels} />
          <MarginSimulator candidates={recommendation.candidates} value={simPrice || recommendation.best_price} onChange={setSimPrice} />

          <section className="space-y-3 rounded-2xl border border-white/70 bg-white p-5 shadow-card">
            <h3 className="font-display text-lg font-semibold">True Margin and Leakage Control</h3>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              <SummaryCard title="List Revenue" value={money(finance?.list_revenue_total)} subtitle="Before discounting" />
              <SummaryCard title="Discounted Revenue" value={money(finance?.discounted_revenue_total)} subtitle="After price change" />
              <SummaryCard title="Net Margin" value={pct(finance?.net_margin_percent)} subtitle={money(finance?.net_margin_amount)} />
              <SummaryCard title="Campaign Cost" value={money(finance?.campaign_cost_amount)} subtitle="Gift, bundle, discount support" />
              <SummaryCard title="Contract Effect" value={money(finance?.contract_effect_amount)} subtitle="Customer-specific contract impact" />
              <SummaryCard title="Leakage Amount" value={money(finance?.leakage_amount)} subtitle={`${(finance?.leakage_reasons_json ?? []).length} leakage drivers`} variant={(finance?.leakage_amount ?? 0) > 0 ? 'warning' : 'success'} />
            </div>
            <button className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold" onClick={() => simulateFinance.mutate()} disabled={simulateFinance.isPending}>
              {simulateFinance.isPending ? 'Calculating...' : 'Recalculate True Margin'}
            </button>
          </section>

          {marketComparison.data ? (
            <section className="space-y-3 rounded-2xl border border-white/70 bg-white p-5 shadow-card">
              <h3 className="font-display text-lg font-semibold">Market Comparison and Value Positioning</h3>
              <p className="text-sm text-slate-600">{marketComparison.data.market_comparison_summary}</p>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
                <SummaryCard title="Competitor Count" value={marketComparison.data.competitor_count} subtitle="Uploaded matches" />
                <SummaryCard title="Average Competitor Price" value={money(marketComparison.data.avg_competitor_price)} subtitle="Uploaded market average" />
                <SummaryCard title="Price Gap" value={pct(marketComparison.data.price_gap_percent)} subtitle="Against market average" />
                <SummaryCard title="Value Score" value={marketComparison.data.value_score.toFixed(1)} subtitle={label(marketComparison.data.recommended_strategy)} />
              </div>
            </section>
          ) : null}

          {quoteId && negotiationAssistant.data ? (
            <section className="space-y-3 rounded-2xl border border-white/70 bg-white p-5 shadow-card">
              <h3 className="font-display text-lg font-semibold">Negotiation Support</h3>
              <p className="text-sm text-slate-700">{negotiationAssistant.data.strategy_summary}</p>
              <div className="space-y-2">
                {negotiationAssistant.data.concession_ladder.map((step) => (
                  <div key={step.step} className="rounded-md border border-slate-200 p-2 text-sm">
                    <div className="font-semibold">Step {step.step}: RM {step.target_price.toFixed(2)}</div>
                    <div>{step.message}</div>
                  </div>
                ))}
              </div>
            </section>
          ) : null}

          {policyCheck.data ? (
            <section className="space-y-3 rounded-2xl border border-white/70 bg-white p-5 shadow-card">
              <h3 className="font-display text-lg font-semibold">Policy, Pricebook, and Campaign Check</h3>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                <SummaryCard title="Pricebook Enforcement" value={label(readString(policyCheck.data.pricebook_compliance_summary, 'status'))} subtitle={readString(policyCheck.data.pricebook_compliance_summary, 'reference_label') ?? 'No active reference'} />
                <SummaryCard title="Contract Pricing" value={label(readString(policyCheck.data.contract_pricing_summary, 'status'))} subtitle={readString(policyCheck.data.contract_pricing_summary, 'contract_source_reference') ?? 'No contract'} />
                <SummaryCard title="Campaign Eligibility" value={`${readNumber(policyCheck.data.campaign_summary, 'eligible_campaign_count') ?? 0}`} subtitle={money(readNumber(policyCheck.data.campaign_summary, 'estimated_campaign_cost'))} />
              </div>
              {policyCheck.data.recommended_action ? <AlertBanner variant="info" title="Why This Matters">{policyCheck.data.recommended_action}</AlertBanner> : null}
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                  <p className="text-sm font-semibold text-slate-700">Policy Warnings</p>
                  {policyCheck.data.violations.length === 0 ? <p className="mt-2 text-sm text-emerald-700">No policy violations detected for the current quote.</p> : policyCheck.data.violations.map((violation) => (
                    <div key={`${violation.code}-${violation.message}`} className="mt-2 rounded-md border border-slate-200 bg-white p-3 text-sm">
                      <div className="font-semibold">{violation.code} | {violation.severity.toUpperCase()}</div>
                      <div>{violation.message}</div>
                      {violation.source_document_id ? <div className="text-xs text-slate-500">Policy source reference: {violation.source_document_id.slice(0, 8)}</div> : null}
                    </div>
                  ))}
                </div>
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                  <p className="text-sm font-semibold text-slate-700">Campaign Eligibility</p>
                  {policyCheck.data.entitlements.length === 0 ? <p className="mt-2 text-sm text-slate-600">No active campaign benefits are available for this quote.</p> : policyCheck.data.entitlements.map((entitlement) => (
                    <div key={`${entitlement.campaign_id}-${entitlement.rule_type}`} className="mt-2 rounded-md border border-slate-200 bg-white p-3 text-sm">
                      <div className="font-semibold">{entitlement.campaign_name} | {label(entitlement.rule_type)}</div>
                      {entitlement.summary ? <div>{entitlement.summary}</div> : null}
                      {entitlement.sku_codes.length > 0 ? <div>SKUs: {entitlement.sku_codes.join(', ')}</div> : null}
                      {entitlement.bundle_skus?.length ? <div>Bundle: {entitlement.bundle_skus.join(', ')}</div> : null}
                      {typeof entitlement.estimated_campaign_cost === 'number' ? <div>Estimated Cost: {money(entitlement.estimated_campaign_cost)}</div> : null}
                    </div>
                  ))}
                </div>
              </div>
            </section>
          ) : null}

          <section className="space-y-3 rounded-2xl border border-white/70 bg-white p-5 shadow-card">
            <h3 className="font-display text-lg font-semibold">Recommended Action</h3>
            <p className="text-sm text-slate-600">Selected price: RM {simPrice.toFixed(2)} | True Margin: {selectedPoint ? `${selectedPoint.margin_percent.toFixed(2)}%` : '-'} | Business Impact: {selectedPoint ? `RM ${selectedPoint.expected_profit.toFixed(2)}` : '-'}</p>
            <textarea value={approvalReason} onChange={(event) => setApprovalReason(event.target.value)} className="input min-h-24" placeholder="Add business context if you are requesting approval or overriding the recommendation" />
            <div className="flex flex-wrap gap-3">
              {quoteId ? <button className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50" disabled={finalize.isPending} onClick={() => finalize.mutate()}>{finalize.isPending ? 'Finalizing...' : 'Finalize Quote'}</button> : null}
              {quoteId ? <button className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold" disabled={requestApproval.isPending} onClick={() => requestApproval.mutate()}>{requestApproval.isPending ? 'Submitting...' : 'Request Approval'}</button> : null}
            </div>
          </section>
        </>
      ) : null}

      {message ? <div className="rounded-lg border border-slate-200 bg-slate-100 p-3 text-sm text-slate-700">{message}</div> : null}
    </div>
  );
}
