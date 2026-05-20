import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  Boxes,
  BriefcaseBusiness,
  CheckCircle2,
  Clock3,
  FileText,
  FileUp,
  ListChecks,
  Sparkles,
} from 'lucide-react';

import { AlertBanner, EmptyState, NextActionCard, SectionHeader, StatusChip, SummaryCard } from '../components/ui';
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

interface FileRecord {
  id: string;
  file_name: string;
  upload_type: string;
  status: string;
  review_status: string | null;
  created_at: string | null;
  next_step: string;
}

const money = new Intl.NumberFormat('en-MY', {
  style: 'currency',
  currency: 'MYR',
  maximumFractionDigits: 2,
});

function formatDate(value: string | null) {
  if (!value) return '-';
  return new Date(value).toLocaleDateString();
}

function titleCase(value: string) {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

export default function SalesDashboardPage() {
  const navigate = useNavigate();
  const [data, setData] = useState<DashboardData | null>(null);
  const [quotes, setQuotes] = useState<QuoteSummary[]>([]);
  const [files, setFiles] = useState<FileRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [dashRes, quotesRes, filesRes] = await Promise.all([
          API.get<DashboardData>('/sandbox/dashboard/summary'),
          API.get<QuoteSummary[]>('/quotes').catch(() => ({ data: [] as QuoteSummary[] })),
          API.get<FileRecord[]>('/upload-center/files').catch(() => ({ data: [] as FileRecord[] })),
        ]);
        setData(dashRes.data);
        setQuotes(Array.isArray(quotesRes.data) ? quotesRes.data.slice(0, 6) : []);
        setFiles(Array.isArray(filesRes.data) ? filesRes.data.slice(0, 5) : []);
      } catch {
        /* Keep the workspace usable even if one card cannot load. */
      } finally {
        setLoading(false);
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
  const activeFiles = useMemo(() => files.filter((file) => file.status === 'active').length, [files]);
  const reviewFiles = useMemo(
    () => files.filter((file) => file.status === 'draft' || file.status === 'needs_review').length,
    [files],
  );
  const averagePrice = data?.average_price ? money.format(data.average_price) : '-';

  return (
    <div className="space-y-6">
      <SectionHeader
        kicker="Sales workspace"
        icon={<BriefcaseBusiness className="h-5 w-5" aria-hidden="true" />}
        title="Commercial Pricing Command Center"
        subtitle="Create quote recommendations, check data readiness, and keep every deal tied to governance evidence."
        action={
          <button
            type="button"
            onClick={() => navigate('/sales/quotes/new')}
            className="inline-flex items-center gap-2 rounded-lg bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800"
          >
            New Quote
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </button>
        }
      />

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <NextActionCard
          eyebrow="Primary workflow"
          icon={<ListChecks className="h-5 w-5" aria-hidden="true" />}
          label="Create an explainable quote"
          description="Select customer, channel, product, and target price. The workspace returns the best price, margin impact, safe band, and approval route."
          actionText="Start quote"
          onAction={() => navigate('/sales/quotes/new')}
        />
        <NextActionCard
          eyebrow="Data readiness"
          icon={<FileUp className="h-5 w-5" aria-hidden="true" />}
          label="Upload price and market files"
          description="Add price lists, competitor sheets, sales history, or promotion calendars before running sensitive recommendations."
          actionText="Open uploads"
          onAction={() => navigate('/upload-center')}
          variant="secondary"
        />
        <NextActionCard
          eyebrow="Scenario test"
          icon={<Sparkles className="h-5 w-5" aria-hidden="true" />}
          label="Run a quick pricing lab"
          description="Validate a product discount with the sandbox model before building a full customer quote."
          actionText="Go to lab"
          onAction={() => navigate('/pricing')}
          variant="secondary"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard
          title="Catalog Coverage"
          value={loading ? '-' : data?.total_products ?? 0}
          icon={<Boxes className="h-4 w-4" aria-hidden="true" />}
          subtitle="Products available for quote decisions"
        />
        <SummaryCard
          title="Average List Price"
          value={loading ? '-' : averagePrice}
          icon={<Sparkles className="h-4 w-4" aria-hidden="true" />}
          subtitle="Current catalog pricing baseline"
        />
        <SummaryCard
          title="Recommendations Run"
          value={loading ? '-' : data?.predictions_made ?? 0}
          icon={<CheckCircle2 className="h-4 w-4" aria-hidden="true" />}
          subtitle="Generated recommendations in the model log"
          variant="info"
        />
        <SummaryCard
          title="Approvals In Flight"
          value={loading ? '-' : pendingApprovals}
          icon={<Clock3 className="h-4 w-4" aria-hidden="true" />}
          subtitle={`${finalizedQuotes} finalized quotes in recent activity`}
          variant={pendingApprovals > 0 ? 'warning' : 'success'}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.35fr_0.9fr]">
        <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-slate-950">Recent Quote Activity</h2>
              <p className="text-sm text-slate-600">Open any quote to regenerate, simulate true margin, or request approval.</p>
            </div>
            <button
              type="button"
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              onClick={() => navigate('/sales/quotes/new')}
            >
              Create quote
            </button>
          </div>

          {quotes.length === 0 ? (
            <EmptyState
              icon={<ListChecks className="h-6 w-6" aria-hidden="true" />}
              title="No quotes yet"
              description="Create your first quote to see recommended pricing, margin context, and approval guidance."
              actionLabel="Create Quote"
              onAction={() => navigate('/sales/quotes/new')}
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[680px] text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                    <th className="py-3">Customer</th>
                    <th className="py-3">Channel</th>
                    <th className="py-3">Status</th>
                    <th className="py-3">Created</th>
                    <th className="py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {quotes.map((quote) => (
                    <tr key={quote.id} className="border-b border-slate-100 last:border-0">
                      <td className="py-3">
                        <p className="font-semibold text-slate-900">{quote.customer_name}</p>
                        <p className="text-xs text-slate-500">Quote {quote.id.slice(0, 8)}</p>
                      </td>
                      <td className="py-3 capitalize text-slate-600">{quote.channel}</td>
                      <td className="py-3">
                        <StatusChip status={quote.status} />
                      </td>
                      <td className="py-3 text-slate-600">{formatDate(quote.created_at)}</td>
                      <td className="py-3 text-right">
                        <button
                          type="button"
                          onClick={() => navigate(`/sales/quotes/${quote.id}`)}
                          className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                        >
                          Open
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4">
            <h2 className="text-base font-semibold text-slate-950">Data Readiness</h2>
            <p className="text-sm text-slate-600">Recent uploads that feed pricing context and policy checks.</p>
          </div>

          <div className="mb-4 grid grid-cols-2 gap-3">
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Active</p>
              <p className="mt-2 text-2xl font-semibold text-emerald-700">{activeFiles}</p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Needs review</p>
              <p className="mt-2 text-2xl font-semibold text-amber-700">{reviewFiles}</p>
            </div>
          </div>

          {files.length === 0 ? (
            <EmptyState
              icon={<FileText className="h-6 w-6" aria-hidden="true" />}
              title="No pricing files uploaded"
              description="Upload product, price, competitor, or promotion files to improve quote context."
              actionLabel="Open Upload Center"
              onAction={() => navigate('/upload-center')}
            />
          ) : (
            <div className="space-y-3">
              {files.map((file) => (
                <button
                  key={file.id}
                  type="button"
                  onClick={() => navigate('/upload-center')}
                  className="w-full rounded-lg border border-slate-200 p-3 text-left transition hover:border-slate-300 hover:bg-slate-50"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold text-slate-900">{file.file_name}</p>
                      <p className="mt-0.5 text-xs text-slate-500">{titleCase(file.upload_type)}</p>
                    </div>
                    <StatusChip status={file.status} />
                  </div>
                  <p className="mt-2 line-clamp-2 text-xs leading-5 text-slate-500">{file.next_step}</p>
                </button>
              ))}
            </div>
          )}
        </section>
      </div>

      <AlertBanner variant="tip" title="Recommended Sales Workflow">
        Upload or confirm the latest source files first, create the quote, then use the simulator to finalize inside the
        safe band or request approval with a documented business reason.
      </AlertBanner>
    </div>
  );
}
