import type { ReactNode } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import type { BehaviorRow, OverrideRow, SeriesPoint } from '../types/api';

interface Props {
  discountDistribution: SeriesPoint[];
  marginByCategory: SeriesPoint[];
  salesBehavior: BehaviorRow[];
  inventoryImpact: SeriesPoint[];
  overrides: OverrideRow[];
  leakageOverTime: SeriesPoint[];
  topViolationCodes: SeriesPoint[];
  marginWaterfall: SeriesPoint[];
  campaignPerformance: SeriesPoint[];
  leakageSources: SeriesPoint[];
  competitorPositioning: SeriesPoint[];
  categoryProfitability: SeriesPoint[];
  approvalTurnaround: SeriesPoint[];
  recommendationAcceptance: SeriesPoint[];
}

export default function AnalyticsCharts({
  discountDistribution,
  marginByCategory,
  salesBehavior,
  inventoryImpact,
  overrides,
  leakageOverTime,
  topViolationCodes,
  marginWaterfall,
  campaignPerformance,
  leakageSources,
  competitorPositioning,
  categoryProfitability,
  approvalTurnaround,
  recommendationAcceptance,
}: Props) {
  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <ChartCard title="Discount Distribution by Channel">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={discountDistribution}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#0f172a" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Margin by Product Category">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={marginByCategory}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#1A8F5B" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <ChartCard title="Override Frequency by Sales Manager">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart
              data={salesBehavior.map((row) => ({
                ...row,
                override_pct: row.override_frequency * 100,
              }))}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="sales_manager" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="override_pct" stroke="#B43A3A" strokeWidth={2.5} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Top SKUs Inventory Impact">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={inventoryImpact}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#B38600" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <ChartCard title="Leakage Over Time">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={leakageOverTime}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#b91c1c" strokeWidth={2.5} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Top Violation Codes">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={topViolationCodes}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#B43A3A" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <ChartCard title="Margin Before vs After Leakage">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={marginWaterfall}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#0f766e" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Campaign Cost and Uptake">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={campaignPerformance}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#1d4ed8" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <ChartCard title="Top Leakage Sources">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={leakageSources}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#9333ea" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Competitor Positioning Summary">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={competitorPositioning}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#2563eb" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <ChartCard title="Category Profitability">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={categoryProfitability}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#059669" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Approval Turnaround by Channel">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={approvalTurnaround}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#ea580c" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <ChartCard title="Recommendation Acceptance">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={recommendationAcceptance}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#0f766e" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div className="rounded-2xl border border-white/70 bg-white p-4 shadow-card">
        <h3 className="font-display text-lg font-semibold">Overrides Table</h3>
        <div className="mt-3 overflow-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b text-left text-slate-600">
                <th className="py-2 pr-3">Quote</th>
                <th className="py-2 pr-3">Sales Manager</th>
                <th className="py-2 pr-3">AI Price</th>
                <th className="py-2 pr-3">Final Price</th>
                <th className="py-2 pr-3">Reason</th>
              </tr>
            </thead>
            <tbody>
              {overrides.map((row) => (
                <tr key={row.quote_id} className="border-b border-slate-100">
                  <td className="py-2 pr-3 font-mono text-xs">{row.quote_id.slice(0, 8)}</td>
                  <td className="py-2 pr-3">{row.sales_manager}</td>
                  <td className="py-2 pr-3">RM {row.ai_price.toFixed(2)}</td>
                  <td className="py-2 pr-3">RM {row.final_price.toFixed(2)}</td>
                  <td className="py-2 pr-3 text-slate-600">{row.reason ?? '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-2xl border border-white/70 bg-white p-4 shadow-card">
      <h3 className="font-display text-lg font-semibold">{title}</h3>
      <div className="mt-2">{children}</div>
    </section>
  );
}
