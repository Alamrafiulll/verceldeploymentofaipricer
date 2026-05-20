import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  BarChart3,
  Boxes,
  Brain,
  ClipboardCheck,
  FileUp,
  Gauge,
  LineChart as LineChartIcon,
  PackageSearch,
  Scale,
  ShieldAlert,
  Sparkles,
  Target,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import PriceChart from '../components/PriceChart';
import { AlertBanner, EmptyState, SectionHeader, StatusChip, SummaryCard } from '../components/ui';
import api from '../lib/api';
import { getSession } from '../lib/auth';
import { getDashboard, getProducts, type SandboxDashboardSummary, type SandboxProduct } from '../services/api';
import type { Kpis, SeriesPoint } from '../types/api';

const money = new Intl.NumberFormat('en-MY', {
  style: 'currency',
  currency: 'MYR',
  maximumFractionDigits: 2,
});

const compactMoney = new Intl.NumberFormat('en-MY', {
  style: 'currency',
  currency: 'MYR',
  notation: 'compact',
  maximumFractionDigits: 1,
});

interface FileRecord {
  id: string;
  file_name: string;
  upload_type: string;
  status: string;
  review_status: string | null;
  created_at: string | null;
  next_step: string;
}

async function safeData<T>(
  request: Promise<{ data: T }>,
  fallback: T,
  failures: string[],
  label: string,
): Promise<T> {
  try {
    return (await request).data;
  } catch {
    failures.push(label);
    return fallback;
  }
}

function average(values: number[]) {
  if (values.length === 0) {
    return 0;
  }
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function deriveExecutiveKpis(products: SandboxProduct[], leakageSeries: SeriesPoint[], acceptanceSeries: SeriesPoint[]): Kpis {
  const marginValues = products
    .filter((product) => product.current_price > 0)
    .map((product) => ((product.current_price - product.base_cost) / product.current_price) * 100);
  const leakageAverage = average(leakageSeries.map((point) => point.value));
  const acceptanceAverage = average(acceptanceSeries.map((point) => point.value));
  const averageMargin = average(marginValues);

  return {
    pricing_health_score: Math.max(0, Math.min(100, averageMargin * 3)),
    average_margin_percent: averageMargin,
    average_decision_time_hours: 0,
    override_rate: 0,
    approval_rate: 0,
    win_rate_proxy: 0,
    aging_inventory_addressed_value: 0,
    average_leakage_amount: leakageAverage,
    recommendation_acceptance_rate: acceptanceAverage > 1 ? acceptanceAverage / 100 : acceptanceAverage,
  };
}

export default function Dashboard() {
  const role = getSession()?.user.role;

  if (role === 'executive') {
    return <ExecutivePricingDashboard />;
  }

  return <OperationalPricingDashboard />;
}

function ExecutivePricingDashboard() {
  const navigate = useNavigate();
  const [kpis, setKpis] = useState<Kpis | null>(null);
  const [products, setProducts] = useState<SandboxProduct[]>([]);
  const [files, setFiles] = useState<FileRecord[]>([]);
  const [leakageOverTime, setLeakageOverTime] = useState<SeriesPoint[]>([]);
  const [categoryProfitability, setCategoryProfitability] = useState<SeriesPoint[]>([]);
  const [competitorPositioning, setCompetitorPositioning] = useState<SeriesPoint[]>([]);
  const [approvalTurnaround, setApprovalTurnaround] = useState<SeriesPoint[]>([]);
  const [recommendationAcceptance, setRecommendationAcceptance] = useState<SeriesPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analyticsWarning, setAnalyticsWarning] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      setAnalyticsWarning(null);
      try {
        const failures: string[] = [];
        const [
          kpisData,
          productsData,
          filesData,
          leakageData,
          profitabilityData,
          competitorData,
          approvalData,
          acceptanceData,
        ] = await Promise.all([
          safeData<Kpis | null>(api.get<Kpis>('/analytics/kpis'), null, failures, 'KPI scorecard'),
          safeData<SandboxProduct[]>(getProducts(), [], failures, 'product catalog'),
          safeData<FileRecord[]>(api.get<FileRecord[]>('/upload-center/files'), [], failures, 'upload register'),
          safeData<SeriesPoint[]>(api.get<SeriesPoint[]>('/analytics/leakage-over-time'), [], failures, 'leakage trend'),
          safeData<SeriesPoint[]>(
            api.get<SeriesPoint[]>('/analytics/category-profitability'),
            [],
            failures,
            'category profitability',
          ),
          safeData<SeriesPoint[]>(
            api.get<SeriesPoint[]>('/analytics/competitor-positioning'),
            [],
            failures,
            'competitor positioning',
          ),
          safeData<SeriesPoint[]>(
            api.get<SeriesPoint[]>('/analytics/approval-turnaround'),
            [],
            failures,
            'approval turnaround',
          ),
          safeData<SeriesPoint[]>(
            api.get<SeriesPoint[]>('/analytics/recommendation-acceptance'),
            [],
            failures,
            'recommendation acceptance',
          ),
        ]);

        setKpis(kpisData ?? deriveExecutiveKpis(productsData, leakageData, acceptanceData));
        setProducts(productsData);
        setFiles(filesData);
        setLeakageOverTime(leakageData);
        setCategoryProfitability(profitabilityData);
        setCompetitorPositioning(competitorData);
        setApprovalTurnaround(approvalData);
        setRecommendationAcceptance(acceptanceData);
        if (failures.length) {
          setAnalyticsWarning(
            `Some executive analytics are unavailable (${failures.join(', ')}). Showing available product, upload, and market signals.`,
          );
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load executive dashboard');
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, []);

  const categories = useMemo(() => new Set(products.map((product) => product.category)).size, [products]);
  const highestPrice = useMemo(
    () => products.reduce((max, product) => Math.max(max, product.current_price), 0),
    [products],
  );
  const activeMarketFiles = useMemo(
    () => files.filter((file) => file.status === 'active' || file.status === 'parsed').length,
    [files],
  );
  const pendingFiles = useMemo(
    () => files.filter((file) => file.status === 'draft' || file.status === 'needs_review').length,
    [files],
  );
  const topProfitCategories = useMemo(
    () => [...categoryProfitability].sort((a, b) => b.value - a.value).slice(0, 4),
    [categoryProfitability],
  );

  return (
    <div className="space-y-6">
      <SectionHeader
        kicker="Executive cockpit"
        icon={<Gauge className="h-5 w-5" aria-hidden="true" />}
        title="Pricing Performance Command Center"
        subtitle="Track margin health, revenue leakage, AI adoption, market position, and data readiness without operational pricing controls."
        action={
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => navigate('/analytics')}
              className="inline-flex items-center gap-2 rounded-lg bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-800"
            >
              Open Analytics
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </button>
            <button
              type="button"
              onClick={() => navigate('/upload-center')}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              Upload Market File
            </button>
          </div>
        }
      />

      {loading ? (
        <div className="flex h-64 items-center justify-center rounded-lg border border-slate-200 bg-white">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-300 border-t-slate-800" />
        </div>
      ) : null}
      {error ? <AlertBanner variant="danger">{error}</AlertBanner> : null}
      {analyticsWarning ? (
        <AlertBanner variant="warning" title="Partial analytics view">
          {analyticsWarning}
        </AlertBanner>
      ) : null}

      {!loading && kpis ? (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            <SummaryCard
              title="Pricing Health"
              value={kpis.pricing_health_score.toFixed(1)}
              subtitle="Composite score from margin, leakage, AI adoption, and speed"
              icon={<Target className="h-4 w-4" aria-hidden="true" />}
              variant={kpis.pricing_health_score >= 80 ? 'success' : kpis.pricing_health_score >= 60 ? 'info' : 'warning'}
            />
            <SummaryCard
              title="Average True Margin"
              value={`${kpis.average_margin_percent.toFixed(2)}%`}
              subtitle="Finalized quote margin"
              icon={<Scale className="h-4 w-4" aria-hidden="true" />}
              variant={kpis.average_margin_percent >= 15 ? 'success' : 'warning'}
            />
            <SummaryCard
              title="Average Leakage"
              value={money.format(kpis.average_leakage_amount)}
              subtitle="Value leakage per finance snapshot"
              icon={<ShieldAlert className="h-4 w-4" aria-hidden="true" />}
              variant={kpis.average_leakage_amount > 0 ? 'warning' : 'success'}
            />
            <SummaryCard
              title="AI Acceptance"
              value={`${(kpis.recommendation_acceptance_rate * 100).toFixed(1)}%`}
              subtitle="Finalized quotes aligned to recommendation"
              icon={<Brain className="h-4 w-4" aria-hidden="true" />}
              variant={kpis.recommendation_acceptance_rate >= 0.75 ? 'success' : 'info'}
            />
          </div>

          <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_360px]">
            <section className="glass-card rounded-2xl p-6 border border-slate-200/60 dark:border-slate-800/60 shadow-sm transition-all duration-300">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-base font-extrabold text-slate-900 dark:text-white">Executive Decision Signals</h2>
                  <p className="text-xs font-semibold text-slate-400 dark:text-slate-500">Board-level controls that indicate whether pricing governance is working.</p>
                </div>
                <StatusChip status={kpis.override_rate > 0.25 ? 'watch' : 'healthy'} variant={kpis.override_rate > 0.25 ? 'warning' : 'success'} />
              </div>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <ExecutiveSignal
                  label="Override Rate"
                  value={`${(kpis.override_rate * 100).toFixed(1)}%`}
                  detail="High values signal weak field adoption or outdated guardrails."
                  tone={kpis.override_rate > 0.25 ? 'warning' : 'success'}
                />
                <ExecutiveSignal
                  label="Approval Rate"
                  value={`${(kpis.approval_rate * 100).toFixed(1)}%`}
                  detail="Share of quotes requiring management decision."
                />
                <ExecutiveSignal
                  label="Decision Time"
                  value={`${kpis.average_decision_time_hours.toFixed(1)}h`}
                  detail="Cycle time from quote creation to final decision."
                  tone={kpis.average_decision_time_hours > 24 ? 'warning' : 'success'}
                />
                <ExecutiveSignal
                  label="Win Rate Proxy"
                  value={`${(kpis.win_rate_proxy * 100).toFixed(1)}%`}
                  detail="Finalized rate among recommended/approved quote flow."
                  tone={kpis.win_rate_proxy >= 0.5 ? 'success' : 'default'}
                />
              </div>
            </section>

            <section className="glass-card rounded-2xl p-6 border border-slate-200/60 dark:border-slate-800/60 shadow-sm transition-all duration-300 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-3">
                  <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-600 dark:bg-indigo-500/25 dark:text-indigo-400">
                    <FileUp className="h-5 w-5" aria-hidden="true" />
                  </span>
                  <div>
                    <h2 className="text-base font-extrabold text-slate-900 dark:text-white">Market Data Readiness</h2>
                    <p className="text-xs font-semibold text-slate-400 dark:text-slate-500">System upload health</p>
                  </div>
                </div>
                <div className="mt-5 grid grid-cols-2 gap-3">
                  <MiniMetric label="Active Files" value={activeMarketFiles.toString()} />
                  <MiniMetric label="Needs Review" value={pendingFiles.toString()} tone={pendingFiles > 0 ? 'warning' : 'success'} />
                </div>
                <p className="mt-4 text-xs font-semibold leading-relaxed text-slate-500 dark:text-slate-400">
                  Executives should maintain strategic targets and market reports so pricing recommendations can reference current market context.
                </p>
              </div>
              <button
                type="button"
                onClick={() => navigate('/upload-center')}
                className="btn-outline mt-5 w-full flex items-center justify-center gap-2"
              >
                Manage executive uploads
              </button>
            </section>
          </div>

          <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_420px]">
            <ChartPanel
              title="Leakage Over Time"
              subtitle="Revenue leakage trend from finance snapshots"
              icon={<TrendingDown className="h-4 w-4" aria-hidden="true" />}
            >
              {leakageOverTime.length ? (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={leakageOverTime} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
                    <CartesianGrid stroke="rgba(148, 163, 184, 0.08)" strokeDasharray="5 5" />
                    <XAxis 
                      dataKey="label" 
                      tick={{ fontSize: 11, fontWeight: 'semibold', fill: '#94a3b8' }} 
                      axisLine={{ stroke: 'rgba(148, 163, 184, 0.15)' }}
                      tickLine={{ stroke: 'rgba(148, 163, 184, 0.15)' }}
                    />
                    <YAxis 
                      tick={{ fontSize: 11, fontWeight: 'semibold', fill: '#94a3b8' }} 
                      axisLine={{ stroke: 'rgba(148, 163, 184, 0.15)' }}
                      tickLine={{ stroke: 'rgba(148, 163, 184, 0.15)' }}
                    />
                    <Tooltip 
                      formatter={(value) => [money.format(Number(value)), 'Leakage']} 
                      contentStyle={{ 
                        borderRadius: 14, 
                        backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                        borderColor: 'rgba(255, 255, 255, 0.15)',
                        color: '#fff',
                        fontSize: 12,
                        fontWeight: 'bold',
                        backdropFilter: 'blur(8px)',
                        boxShadow: '0 10px 25px rgba(0,0,0,0.3)'
                      }}
                    />
                    <Line type="monotone" dataKey="value" stroke="#ea580c" strokeWidth={3} dot={{ r: 4, stroke: '#ea580c', strokeWidth: 2, fill: '#fff' }} activeDot={{ r: 6 }} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState title="No leakage trend yet" description="Finance snapshots will appear after quote simulations." />
              )}
            </ChartPanel>

            <section className="glass-card rounded-2xl p-6 border border-slate-200/60 dark:border-slate-800/60 shadow-sm transition-all duration-300 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-3">
                  <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-600 dark:bg-indigo-500/25 dark:text-indigo-400">
                    <Boxes className="h-5 w-5" aria-hidden="true" />
                  </span>
                  <div>
                    <h2 className="text-base font-extrabold text-slate-900 dark:text-white">Portfolio Snapshot</h2>
                    <p className="text-xs font-semibold text-slate-400 dark:text-slate-500">Products and taxonomy breakdown</p>
                  </div>
                </div>
                <div className="mt-5 grid grid-cols-2 gap-3">
                  <MiniMetric label="Products" value={products.length.toString()} />
                  <MiniMetric label="Categories" value={categories.toString()} />
                  <MiniMetric label="Highest Price" value={money.format(highestPrice)} className="col-span-2" />
                </div>
                <div className="mt-4 rounded-xl border border-slate-200/40 dark:border-slate-800/40 bg-slate-500/5 p-4">
                  <p className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">Top profitable categories</p>
                  {topProfitCategories.length ? (
                    <div className="mt-3 space-y-2">
                      {topProfitCategories.map((item) => (
                        <div key={item.label} className="flex items-center justify-between gap-3 text-sm">
                          <span className="truncate text-slate-500 dark:text-slate-400 font-semibold">{item.label}</span>
                          <span className="font-extrabold text-slate-900 dark:text-white">{money.format(item.value)}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="mt-3 text-xs font-semibold text-slate-500">No category profitability data yet.</p>
                  )}
                </div>
              </div>
              <button
                type="button"
                onClick={() => navigate('/products')}
                className="btn-primary mt-5 w-full flex items-center justify-center gap-2"
              >
                Review product catalog
              </button>
            </section>
          </div>

          <div className="grid gap-4 xl:grid-cols-3">
            <ChartPanel
              title="Category Profitability"
              subtitle="Profit contribution by category"
              icon={<BarChart3 className="h-4 w-4" aria-hidden="true" />}
            >
              <BarChartBlock data={categoryProfitability} color="#047857" format="money" />
            </ChartPanel>
            <ChartPanel
              title="Competitor Positioning"
              subtitle="Market position signals from uploaded context"
              icon={<LineChartIcon className="h-4 w-4" aria-hidden="true" />}
            >
              <BarChartBlock data={competitorPositioning} color="#2563eb" />
            </ChartPanel>
            <ChartPanel
              title="Approval Turnaround"
              subtitle="Decision speed by channel or state"
              icon={<ClipboardCheck className="h-4 w-4" aria-hidden="true" />}
            >
              <BarChartBlock data={approvalTurnaround} color="#c2410c" suffix="h" />
            </ChartPanel>
          </div>

          <section className="glass-card rounded-2xl p-6 border border-slate-200/60 dark:border-slate-800/60 shadow-sm transition-all duration-300">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-500/10 text-teal-600 dark:bg-teal-500/25 dark:text-teal-400">
                  <Sparkles className="h-5 w-5" aria-hidden="true" />
                </span>
                <div>
                  <h2 className="text-base font-extrabold text-slate-900 dark:text-white">Recommendation Acceptance</h2>
                  <p className="text-xs font-semibold text-slate-400 dark:text-slate-500">Adoption trend by acceptance status.</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => navigate('/analytics')}
                className="btn-outline"
              >
                Full analytics
              </button>
            </div>
            <BarChartBlock data={recommendationAcceptance} color="#0f766e" />
          </section>
        </>
      ) : null}
    </div>
  );
}

function OperationalPricingDashboard() {
  const [data, setData] = useState<SandboxDashboardSummary | null>(null);
  const [products, setProducts] = useState<SandboxProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [summaryRes, productsRes] = await Promise.all([getDashboard(), getProducts()]);
        setData(summaryRes.data);
        setProducts(productsRes.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard');
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, []);

  const chartData = useMemo(
    () => products.slice(0, 12).map((product) => ({ label: product.sku, price: product.current_price })),
    [products],
  );

  const highestPrice = useMemo(
    () => products.reduce((max, product) => Math.max(max, product.current_price), 0),
    [products],
  );

  return (
    <div className="space-y-6">
      <SectionHeader
        kicker="Overview"
        icon={<Gauge className="h-5 w-5" aria-hidden="true" />}
        title="Pricing Overview"
        subtitle="Monitor catalog breadth, price baseline, and AI usage across the pricing workspace."
      />

      {loading && (
        <div className="flex h-64 items-center justify-center rounded-lg border border-slate-200 bg-white">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-300 border-t-slate-800" />
        </div>
      )}
      {error && <AlertBanner variant="danger">{error}</AlertBanner>}

      {!loading && data && (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <SummaryCard
              title="Total Products"
              value={data.total_products}
              subtitle="Catalog records"
              icon={<PackageSearch className="h-4 w-4" aria-hidden="true" />}
            />
            <SummaryCard
              title="Average Price"
              value={money.format(data.average_price ?? 0)}
              subtitle="Current price baseline"
              icon={<TrendingUp className="h-4 w-4" aria-hidden="true" />}
              variant="info"
            />
            <SummaryCard
              title="Highest Price"
              value={money.format(highestPrice)}
              subtitle="Highest loaded SKU"
              variant="warning"
            />
            <SummaryCard
              title="Predictions Made"
              value={data.predictions_made}
              subtitle="AI recommendations generated"
              icon={<Sparkles className="h-4 w-4" aria-hidden="true" />}
              variant="success"
            />
          </div>

          <PriceChart data={chartData} />
        </>
      )}
    </div>
  );
}

function ExecutiveSignal({
  label,
  value,
  detail,
  tone = 'default',
}: {
  label: string;
  value: string;
  detail: string;
  tone?: 'default' | 'success' | 'warning';
}) {
  const valueClass = {
    default: 'text-slate-900 dark:text-white',
    success: 'text-emerald-700 dark:text-emerald-400',
    warning: 'text-amber-700 dark:text-amber-400',
  }[tone];

  const cardStyle = {
    default: 'border-slate-200 bg-white/50 dark:border-slate-800 dark:bg-slate-900/30',
    success: 'border-emerald-200/60 bg-emerald-500/5 dark:border-emerald-900/20 dark:bg-emerald-950/10',
    warning: 'border-amber-200/60 bg-amber-500/5 dark:border-amber-900/20 dark:bg-amber-950/10',
  }[tone];

  return (
    <article className={`rounded-xl border p-4.5 transition-all duration-300 ${cardStyle}`}>
      <p className="text-[10px] font-extrabold uppercase tracking-[0.16em] text-slate-400 dark:text-slate-500">{label}</p>
      <p className={`mt-2 font-display text-2xl font-bold tracking-tight ${valueClass}`}>{value}</p>
      <p className="mt-2 text-xs font-semibold leading-relaxed text-slate-500 dark:text-slate-400">{detail}</p>
    </article>
  );
}

function MiniMetric({
  label,
  value,
  tone = 'default',
  className = '',
}: {
  label: string;
  value: string;
  tone?: 'default' | 'success' | 'warning';
  className?: string;
}) {
  const valueClass = {
    default: 'text-slate-900 dark:text-white',
    success: 'text-emerald-700 dark:text-emerald-400',
    warning: 'text-amber-700 dark:text-amber-400',
  }[tone];

  const cardStyle = {
    default: 'border-slate-200/60 bg-white/50 dark:border-slate-800/40 dark:bg-slate-900/30',
    success: 'border-emerald-200/60 bg-emerald-500/5 dark:border-emerald-900/20 dark:bg-emerald-950/10',
    warning: 'border-amber-200/60 bg-amber-500/5 dark:border-amber-900/20 dark:bg-amber-950/10',
  }[tone];

  return (
    <div className={`rounded-xl border p-3.5 transition-all duration-300 ${cardStyle} ${className}`}>
      <p className="text-[10px] font-extrabold uppercase tracking-[0.16em] text-slate-400 dark:text-slate-500">{label}</p>
      <p className={`mt-1.5 font-display text-lg font-bold tracking-tight ${valueClass}`}>{value}</p>
    </div>
  );
}

function ChartPanel({
  title,
  subtitle,
  icon,
  children,
}: {
  title: string;
  subtitle: string;
  icon: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="glass-card rounded-2xl p-6 border border-slate-200/60 dark:border-slate-800/60 shadow-sm transition-all duration-300">
      <div className="mb-5 flex items-center gap-3">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-600 dark:bg-indigo-500/25 dark:text-indigo-400">
          {icon}
        </span>
        <div>
          <h2 className="text-sm sm:text-base font-extrabold text-slate-900 dark:text-white">{title}</h2>
          <p className="text-xs font-semibold text-slate-400 dark:text-slate-500">{subtitle}</p>
        </div>
      </div>
      {children}
    </section>
  );
}

function BarChartBlock({
  data,
  color,
  suffix = '',
  format,
}: {
  data: SeriesPoint[];
  color: string;
  suffix?: string;
  format?: 'money';
}) {
  if (data.length === 0) {
    return <EmptyState title="No data yet" description="This signal will appear when more quote activity is available." />;
  }

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 15, bottom: 10, left: 0 }}>
          <CartesianGrid stroke="rgba(148, 163, 184, 0.08)" strokeDasharray="5 5" />
          <XAxis 
            dataKey="label" 
            tick={{ fontSize: 11, fontWeight: 'semibold', fill: '#94a3b8' }} 
            axisLine={{ stroke: 'rgba(148, 163, 184, 0.15)' }}
            tickLine={{ stroke: 'rgba(148, 163, 184, 0.15)' }}
          />
          <YAxis 
            tick={{ fontSize: 11, fontWeight: 'semibold', fill: '#94a3b8' }} 
            axisLine={{ stroke: 'rgba(148, 163, 184, 0.15)' }}
            tickLine={{ stroke: 'rgba(148, 163, 184, 0.15)' }}
          />
          <Tooltip
            formatter={(value) => [
              format === 'money' ? compactMoney.format(Number(value)) : `${Number(value).toFixed(2)}${suffix}`,
              'Value',
            ]}
            contentStyle={{ 
              borderRadius: 14, 
              backgroundColor: 'rgba(15, 23, 42, 0.9)', 
              borderColor: 'rgba(255, 255, 255, 0.15)',
              color: '#fff',
              fontSize: 12,
              fontWeight: 'bold',
              backdropFilter: 'blur(8px)',
              boxShadow: '0 10px 25px rgba(0,0,0,0.3)'
            }}
          />
          <Bar dataKey="value" fill={color} radius={[6, 6, 0, 0]} maxBarSize={45} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
