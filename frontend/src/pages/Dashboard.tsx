import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';


import PriceChart from '../components/PriceChart';
import Spinner from '../components/Spinner';
import { getDashboard, getProducts } from '../services/api';

export default function Dashboard() {
  const { data, isLoading: loading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const [summaryRes, productsRes] = await Promise.all([getDashboard(), getProducts()]);
      return {
        summary: summaryRes.data,
        products: productsRes.data,
      };
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  const chartData = useMemo(
    () => (data?.products ?? []).slice(0, 12).map((p) => ({ label: p.sku, price: p.current_price })),
    [data?.products],
  );

  return (
    <div className="p-1">


      <h2 className="mb-4 text-2xl font-bold text-slate-900">Pricing Overview</h2>

      {loading && (
        <div className="flex h-64 items-center justify-center">
          <Spinner size="lg" />
        </div>
      )}
      {error && <p className="text-sm text-rose-600">{(error as Error).message || 'Failed to load dashboard'}</p>}

      {!loading && data && (
        <div className="space-y-5">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-card">
              <h3 className="text-sm text-slate-600">Total Products</h3>
              <p className="text-3xl font-semibold text-slate-900">{data.summary.total_products}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-card">
              <h3 className="text-sm text-slate-600">Average Price</h3>
              <p className="text-3xl font-semibold text-slate-900">
                RM {(data.summary.average_price ?? 0).toFixed(2)}
              </p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-card">
              <h3 className="text-sm text-slate-600">Predictions Made</h3>
              <p className="text-3xl font-semibold text-slate-900">{data.summary.predictions_made}</p>
            </div>
          </div>

          <PriceChart data={chartData} />
        </div>
      )}
    </div>
  );
}
