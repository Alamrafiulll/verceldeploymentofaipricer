import { useMemo, useState } from 'react';
import { Search, Sparkles } from 'lucide-react';

import { recommendPrice, type SandboxProduct, type SandboxRecommendation } from '../services/api';
import { EmptyState } from './ui';

interface ProductTableProps {
  products: SandboxProduct[];
  canRecommend: boolean;
}

const money = new Intl.NumberFormat('en-MY', {
  style: 'currency',
  currency: 'MYR',
  maximumFractionDigits: 2,
});

export default function ProductTable({ products, canRecommend }: ProductTableProps) {
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [latest, setLatest] = useState<SandboxRecommendation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('all');

  const categories = useMemo(
    () => Array.from(new Set(products.map((product) => product.category))).sort(),
    [products],
  );

  const filteredProducts = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return products.filter((product) => {
      const matchesCategory = category === 'all' || product.category === category;
      const matchesQuery =
        !normalized ||
        product.sku.toLowerCase().includes(normalized) ||
        product.name.toLowerCase().includes(normalized) ||
        product.category.toLowerCase().includes(normalized);
      return matchesCategory && matchesQuery;
    });
  }, [category, products, query]);

  const handleRecommend = async (id: string) => {
    setLoadingId(id);
    setError(null);
    try {
      const res = await recommendPrice(id, 5);
      setLatest(res.data);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Failed to get recommendation');
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 p-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-950">Catalog Table</h2>
            <p className="text-sm text-slate-600">Search products, review cost/price spread, and run quick AI checks.</p>
          </div>
          <div className="grid gap-2 sm:grid-cols-[minmax(220px,1fr)_180px]">
            <label className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                className="input pl-9"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search SKU, name, category"
              />
            </label>
            <select className="input" value={category} onChange={(event) => setCategory(event.target.value)}>
              <option value="all">All categories</option>
              {categories.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {error && <p className="mx-5 mt-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>}

      {latest && (
        <div className="mx-5 mt-4 rounded-lg border border-sky-200 bg-sky-50 p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-sky-950">Latest recommendation</p>
              <p className="text-sm text-sky-800">
                Product {latest.product_id.slice(0, 8)} recommended at {money.format(latest.predicted_price)} with{' '}
                {(latest.confidence * 100).toFixed(1)}% confidence.
              </p>
            </div>
            <Sparkles className="h-5 w-5 text-sky-700" aria-hidden="true" />
          </div>
        </div>
      )}

      {filteredProducts.length === 0 ? (
        <div className="p-5">
          <EmptyState title="No products match this view" description="Clear the search or import product data." />
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[820px] text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                <th className="px-5 py-3">SKU</th>
                <th className="px-5 py-3">Product</th>
                <th className="px-5 py-3">Category</th>
                <th className="px-5 py-3 text-right">Cost</th>
                <th className="px-5 py-3 text-right">Current Price</th>
                <th className="px-5 py-3 text-right">Spread</th>
                <th className="px-5 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredProducts.map((product) => {
                const spread = product.current_price - product.base_cost;
                const spreadPercent = product.current_price > 0 ? (spread / product.current_price) * 100 : 0;
                return (
                  <tr key={product.id} className="border-b border-slate-100 last:border-0">
                    <td className="px-5 py-3 font-semibold text-slate-900">{product.sku}</td>
                    <td className="px-5 py-3 text-slate-700">{product.name}</td>
                    <td className="px-5 py-3 text-slate-600">{product.category}</td>
                    <td className="px-5 py-3 text-right text-slate-600">{money.format(product.base_cost)}</td>
                    <td className="px-5 py-3 text-right font-semibold text-slate-900">{money.format(product.current_price)}</td>
                    <td className="px-5 py-3 text-right text-slate-600">
                      {money.format(spread)} ({spreadPercent.toFixed(1)}%)
                    </td>
                    <td className="px-5 py-3 text-right">
                      {canRecommend ? (
                        <button
                          type="button"
                          onClick={() => handleRecommend(product.id)}
                          disabled={loadingId === product.id}
                          className="inline-flex items-center justify-center gap-2 rounded-lg bg-slate-950 px-3 py-2 text-xs font-semibold text-white transition hover:bg-slate-800 disabled:opacity-60"
                        >
                          <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
                          {loadingId === product.id ? 'Running' : 'Recommend'}
                        </button>
                      ) : (
                        <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-500">
                          View only
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
