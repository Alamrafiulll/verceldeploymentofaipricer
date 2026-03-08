import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AlertBanner, EmptyState, NextActionCard, SectionHeader, SummaryCard } from '../components/ui';
import API from '../lib/api';

interface DashboardData {
  total_products: number;
  average_price: number | null;
  predictions_made: number;
}

interface QuoteSummary {
  id: string;
  customer_name: string;
  status: string;
  channel: string;
  created_at: string;
}

export default function SalesDashboardPage() {
  const navigate = useNavigate();
  const [data, setData] = useState<DashboardData | null>(null);
  const [quotes, setQuotes] = useState<QuoteSummary[]>([]);

  useEffect(() => {
    const load = async () => {
      try {
        const [dashRes, quotesRes] = await Promise.all([
          API.get<DashboardData>('/sandbox/dashboard/summary'),
          API.get<QuoteSummary[]>('/quotes').catch(() => ({ data: [] })),
        ]);
        setData(dashRes.data);
        setQuotes(Array.isArray(quotesRes.data) ? quotesRes.data.slice(0, 5) : []);
      } catch {
        /* ignore */
      }
    };
    void load();
  }, []);

  const pendingApprovals = useMemo(
    () => quotes.filter((quote) => quote.status === 'approval_pending').length,
    [quotes],
  );
  const finalizedQuotes = useMemo(
    () => quotes.filter((quote) => quote.status === 'finalized').length,
    [quotes],
  );

  return (
    <div className="space-y-6 p-1">
      <SectionHeader
        icon="🏢"
        title="Sales Pricing Workspace"
        subtitle="Start quotes quickly, understand the recommendation, and move the next deal action forward."
      />

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <NextActionCard
          icon="📝"
          label="Create a Quote"
          description="Build a new pricing request and get an explainable recommendation."
          actionText="Start Quote"
          onAction={() => navigate('/sales/quotes/new')}
        />
        <NextActionCard
          icon="📁"
          label="Open Upload Center"
          description="Add price lists, competitor files, and sales history for smarter pricing context."
          actionText="Go to Uploads"
          onAction={() => navigate('/upload-center')}
          variant="secondary"
        />
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard title="Catalog Coverage" value={data?.total_products ?? '-'} icon="📦" subtitle="Products available for pricing decisions" />
        <SummaryCard title="Average List Price" value={data?.average_price ? `RM ${data.average_price.toFixed(2)}` : '-'} icon="💰" subtitle="Average product price in the current catalog" />
        <SummaryCard title="Recommendations Run" value={data?.predictions_made ?? '-'} icon="🤖" subtitle="Explainable recommendations generated" variant="info" />
        <SummaryCard title="Approvals in Flight" value={pendingApprovals} icon="⏳" subtitle={`${finalizedQuotes} recently finalized quotes`} variant={pendingApprovals > 0 ? 'warning' : 'success'} />
      </div>

      <AlertBanner variant="tip" title="Recommended Action">
        If you are preparing a new quote, start with the customer, channel, and requested price.
        The system will show the recommended price, true margin impact, market comparison, and
        whether approval governance is likely to be needed.
      </AlertBanner>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="mb-3 text-sm font-semibold text-slate-800">Recent Quote Activity</h3>
        {quotes.length === 0 ? (
          <EmptyState
            icon="📝"
            title="No quotes yet"
            description="Create your first quote to see recommended pricing, margin context, and approval guidance."
            actionLabel="Create Quote"
            onAction={() => navigate('/sales/quotes/new')}
          />
        ) : (
          <div className="space-y-2">
            {quotes.map((quote) => (
              <div
                key={quote.id}
                className="flex cursor-pointer items-center justify-between rounded-lg border border-slate-100 p-3 hover:bg-slate-50"
                onClick={() => navigate(`/sales/quotes/${quote.id}`)}
              >
                <div>
                  <p className="text-sm font-medium text-slate-800">{quote.customer_name}</p>
                  <p className="text-xs text-slate-500">
                    {quote.channel} | {new Date(quote.created_at).toLocaleDateString()}
                  </p>
                </div>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-[11px] font-medium ${
                    quote.status === 'finalized'
                      ? 'bg-emerald-100 text-emerald-700'
                      : quote.status === 'draft'
                        ? 'bg-slate-100 text-slate-600'
                        : quote.status === 'approved'
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-amber-100 text-amber-700'
                  }`}
                >
                  {quote.status.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
