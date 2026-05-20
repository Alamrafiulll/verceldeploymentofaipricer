import { useQuery } from '@tanstack/react-query';

import AnalyticsCharts from '../components/AnalyticsCharts';
import KpiCards from '../components/KpiCards';
import RoleFileUploadPanel from '../components/RoleFileUploadPanel';
import api from '../lib/api';
import { getSession } from '../lib/auth';
import type { BehaviorRow, Kpis, OverrideRow, SeriesPoint } from '../types/api';

export default function AnalyticsPage() {
  const role = getSession()?.user.role;
  const kpis = useQuery({
    queryKey: ['analytics', 'kpis'],
    queryFn: async () => (await api.get<Kpis>('/analytics/kpis')).data,
  });

  const discount = useQuery({
    queryKey: ['analytics', 'discount-distribution'],
    queryFn: async () => (await api.get<SeriesPoint[]>('/analytics/discount-distribution')).data,
  });

  const margin = useQuery({
    queryKey: ['analytics', 'margin-by-category'],
    queryFn: async () => (await api.get<SeriesPoint[]>('/analytics/margin-by-category')).data,
  });

  const overrides = useQuery({
    queryKey: ['analytics', 'overrides'],
    queryFn: async () => (await api.get<OverrideRow[]>('/analytics/overrides')).data,
  });

  const behavior = useQuery({
    queryKey: ['analytics', 'sales-manager-behavior'],
    queryFn: async () => (await api.get<BehaviorRow[]>('/analytics/sales-manager-behavior')).data,
  });

  const inventoryImpact = useQuery({
    queryKey: ['analytics', 'inventory-impact'],
    queryFn: async () => (await api.get<SeriesPoint[]>('/analytics/inventory-impact')).data,
  });

  const leakageOverTime = useQuery({
    queryKey: ['analytics', 'leakage-over-time'],
    queryFn: async () => (await api.get<SeriesPoint[]>('/analytics/leakage-over-time')).data,
  });

  const topViolationCodes = useQuery({
    queryKey: ['analytics', 'top-violation-codes'],
    queryFn: async () => (await api.get<SeriesPoint[]>('/analytics/top-violation-codes')).data,
  });

  const marginWaterfall = useQuery({
    queryKey: ['analytics', 'margin-waterfall'],
    queryFn: async () => (await api.get<SeriesPoint[]>('/analytics/margin-waterfall')).data,
  });

  const campaignPerformance = useQuery({
    queryKey: ['analytics', 'campaign-performance'],
    queryFn: async () => (await api.get<SeriesPoint[]>('/analytics/campaign-performance')).data,
  });

  const leakageSources = useQuery({
    queryKey: ['analytics', 'leakage-sources'],
    queryFn: async () => (await api.get<SeriesPoint[]>('/analytics/leakage-sources')).data,
  });

  const competitorPositioning = useQuery({
    queryKey: ['analytics', 'competitor-positioning'],
    queryFn: async () => (await api.get<SeriesPoint[]>('/analytics/competitor-positioning')).data,
  });

  const categoryProfitability = useQuery({
    queryKey: ['analytics', 'category-profitability'],
    queryFn: async () => (await api.get<SeriesPoint[]>('/analytics/category-profitability')).data,
  });

  const approvalTurnaround = useQuery({
    queryKey: ['analytics', 'approval-turnaround'],
    queryFn: async () => (await api.get<SeriesPoint[]>('/analytics/approval-turnaround')).data,
  });

  const recommendationAcceptance = useQuery({
    queryKey: ['analytics', 'recommendation-acceptance'],
    queryFn: async () => (await api.get<SeriesPoint[]>('/analytics/recommendation-acceptance')).data,
  });

  const loading =
    kpis.isLoading ||
    discount.isLoading ||
    margin.isLoading ||
    overrides.isLoading ||
    behavior.isLoading ||
    inventoryImpact.isLoading ||
    leakageOverTime.isLoading ||
    topViolationCodes.isLoading ||
    marginWaterfall.isLoading ||
    campaignPerformance.isLoading ||
    leakageSources.isLoading ||
    competitorPositioning.isLoading ||
    categoryProfitability.isLoading ||
    approvalTurnaround.isLoading ||
    recommendationAcceptance.isLoading;

  return (
    <div className="space-y-5">
      <section className="rounded-2xl border border-white/70 bg-white p-5 shadow-card">
        <h2 className="font-display text-2xl font-semibold">Executive Analytics</h2>
        <p className="text-sm text-slate-600">
          Margin, override behavior, inventory impact, and AI adoption visibility.
        </p>
      </section>

      {loading ? <p className="text-sm text-slate-600">Loading analytics...</p> : null}

      {kpis.data ? <KpiCards data={kpis.data} /> : null}

      {discount.data &&
      margin.data &&
      behavior.data &&
      inventoryImpact.data &&
      overrides.data &&
      leakageOverTime.data &&
      topViolationCodes.data &&
      marginWaterfall.data &&
      campaignPerformance.data ? (
        <AnalyticsCharts
          discountDistribution={discount.data}
          marginByCategory={margin.data}
          salesBehavior={behavior.data}
          inventoryImpact={inventoryImpact.data}
          overrides={overrides.data}
          leakageOverTime={leakageOverTime.data}
          topViolationCodes={topViolationCodes.data}
          marginWaterfall={marginWaterfall.data}
          campaignPerformance={campaignPerformance.data}
          leakageSources={leakageSources.data ?? []}
          competitorPositioning={competitorPositioning.data ?? []}
          categoryProfitability={categoryProfitability.data ?? []}
          approvalTurnaround={approvalTurnaround.data ?? []}
          recommendationAcceptance={recommendationAcceptance.data ?? []}
        />
      ) : null}

      {role === 'executive' ? (
        <RoleFileUploadPanel
          title="Executive Strategic Upload"
          description="Allowed uploads: strategic_targets, market_reports."
          allowedTypes={['strategic_targets', 'market_reports']}
        />
      ) : null}
    </div>
  );
}
