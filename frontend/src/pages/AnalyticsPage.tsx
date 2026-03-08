import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';

import AnalyticsCharts from '../components/AnalyticsCharts';
import KpiCards from '../components/KpiCards';
import Spinner from '../components/Spinner';
import { AlertBanner, NextActionCard, SectionHeader, SummaryCard } from '../components/ui';
import api from '../lib/api';
import { getSession } from '../lib/auth';
import type { BehaviorRow, Kpis, OverrideRow, SeriesPoint } from '../types/api';

export default function AnalyticsPage() {
  const role = getSession()?.user.role;
  const navigate = useNavigate();

  const kpis = useQuery({ queryKey: ['analytics', 'kpis'], queryFn: async () => (await api.get<Kpis>('/analytics/kpis')).data });
  const discount = useQuery({ queryKey: ['analytics', 'discount-distribution'], queryFn: async () => (await api.get<SeriesPoint[]>('/analytics/discount-distribution')).data });
  const margin = useQuery({ queryKey: ['analytics', 'margin-by-category'], queryFn: async () => (await api.get<SeriesPoint[]>('/analytics/margin-by-category')).data });
  const overrides = useQuery({ queryKey: ['analytics', 'overrides'], queryFn: async () => (await api.get<OverrideRow[]>('/analytics/overrides')).data });
  const behavior = useQuery({ queryKey: ['analytics', 'sales-manager-behavior'], queryFn: async () => (await api.get<BehaviorRow[]>('/analytics/sales-manager-behavior')).data });
  const inventoryImpact = useQuery({ queryKey: ['analytics', 'inventory-impact'], queryFn: async () => (await api.get<SeriesPoint[]>('/analytics/inventory-impact')).data });
  const leakageOverTime = useQuery({ queryKey: ['analytics', 'leakage-over-time'], queryFn: async () => (await api.get<SeriesPoint[]>('/analytics/leakage-over-time')).data });
  const topViolationCodes = useQuery({ queryKey: ['analytics', 'top-violation-codes'], queryFn: async () => (await api.get<SeriesPoint[]>('/analytics/top-violation-codes')).data });
  const marginWaterfall = useQuery({ queryKey: ['analytics', 'margin-waterfall'], queryFn: async () => (await api.get<SeriesPoint[]>('/analytics/margin-waterfall')).data });
  const campaignPerformance = useQuery({ queryKey: ['analytics', 'campaign-performance'], queryFn: async () => (await api.get<SeriesPoint[]>('/analytics/campaign-performance')).data });
  const leakageSources = useQuery({ queryKey: ['analytics', 'leakage-sources'], queryFn: async () => (await api.get<SeriesPoint[]>('/analytics/leakage-sources')).data });
  const competitorPositioning = useQuery({ queryKey: ['analytics', 'competitor-positioning'], queryFn: async () => (await api.get<SeriesPoint[]>('/analytics/competitor-positioning')).data });
  const categoryProfitability = useQuery({ queryKey: ['analytics', 'category-profitability'], queryFn: async () => (await api.get<SeriesPoint[]>('/analytics/category-profitability')).data });
  const approvalTurnaround = useQuery({ queryKey: ['analytics', 'approval-turnaround'], queryFn: async () => (await api.get<SeriesPoint[]>('/analytics/approval-turnaround')).data });
  const recommendationAcceptance = useQuery({ queryKey: ['analytics', 'recommendation-acceptance'], queryFn: async () => (await api.get<SeriesPoint[]>('/analytics/recommendation-acceptance')).data });

  const loading = [
    kpis,
    discount,
    margin,
    overrides,
    behavior,
    inventoryImpact,
    leakageOverTime,
    topViolationCodes,
    marginWaterfall,
    campaignPerformance,
    leakageSources,
    competitorPositioning,
    categoryProfitability,
    approvalTurnaround,
    recommendationAcceptance,
  ].some((query) => query.isLoading);

  return (
    <div className="space-y-5 p-1">
      <SectionHeader
        icon="📊"
        title="Executive Analytics"
        subtitle="Review pricing health, leakage control, approval governance, and market position in plain business language."
      />

      {kpis.data ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <SummaryCard title="Pricing Health Score" value={kpis.data.pricing_health_score.toFixed(1)} icon="📈" variant={kpis.data.pricing_health_score >= 70 ? 'success' : 'warning'} subtitle="Overall pricing control health" />
          <SummaryCard title="Average Leakage" value={`RM ${kpis.data.average_leakage_amount.toFixed(2)}`} icon="⚠️" variant={kpis.data.average_leakage_amount > 0 ? 'warning' : 'success'} subtitle="Average leakage per finance snapshot" />
          <SummaryCard title="Acceptance Rate" value={`${(kpis.data.recommendation_acceptance_rate * 100).toFixed(1)}%`} icon="✅" variant="info" subtitle="Recommendations kept without override" />
          <SummaryCard title="Decision Time" value={`${kpis.data.average_decision_time_hours.toFixed(1)}h`} icon="⏱️" variant={kpis.data.average_decision_time_hours <= 24 ? 'success' : 'warning'} subtitle="Average quote to decision time" />
        </div>
      ) : null}

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <NextActionCard
          icon="📁"
          label="Upload Strategic Data"
          description="Add market reports, strategic targets, and pricing policies to strengthen analytics context."
          actionText="Open Upload Center"
          onAction={() => navigate('/upload-center')}
          variant="secondary"
        />
        <NextActionCard
          icon="🛡️"
          label="Review Governance"
          description="Check approvals, leakage drivers, and recommendation acceptance before changing pricing strategy."
          actionText="Open Admin"
          onAction={() => navigate('/admin')}
          variant="secondary"
        />
      </div>

      {role === 'executive' ? (
        <AlertBanner variant="tip" title="Why This Matters">
          Start with the Pricing Health Score, Average Leakage, and Category Profitability views.
          They show whether discounting, campaign cost, and approval delays are eroding true margin.
        </AlertBanner>
      ) : null}

      {loading ? (
        <div className="flex h-32 items-center justify-center">
          <Spinner size="lg" />
        </div>
      ) : null}

      {kpis.data ? <KpiCards data={kpis.data} /> : null}

      {discount.data &&
      margin.data &&
      behavior.data &&
      inventoryImpact.data &&
      overrides.data &&
      leakageOverTime.data &&
      topViolationCodes.data &&
      marginWaterfall.data &&
      campaignPerformance.data &&
      leakageSources.data &&
      competitorPositioning.data &&
      categoryProfitability.data &&
      approvalTurnaround.data &&
      recommendationAcceptance.data ? (
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
          leakageSources={leakageSources.data}
          competitorPositioning={competitorPositioning.data}
          categoryProfitability={categoryProfitability.data}
          approvalTurnaround={approvalTurnaround.data}
          recommendationAcceptance={recommendationAcceptance.data}
        />
      ) : null}
    </div>
  );
}
