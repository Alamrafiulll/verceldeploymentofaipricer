import { useEffect, useState, useCallback, useMemo } from 'react';
import { Boxes, FileSpreadsheet, Lock } from 'lucide-react';

import BulkImportPanel from '../components/BulkImportPanel';
import ProductTable from '../components/ProductTable';
import { AlertBanner, SectionHeader, SummaryCard } from '../components/ui';
import { getSession } from '../lib/auth';
import { getProducts, type SandboxProduct } from '../services/api';

const money = new Intl.NumberFormat('en-MY', {
  style: 'currency',
  currency: 'MYR',
  maximumFractionDigits: 2,
});

export default function Products() {
  const [products, setProducts] = useState<SandboxProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const role = getSession()?.user.role;
  const canRecommend = role === 'sales' || role === 'admin' || role === 'approver';
  const canImport = role === 'sales' || role === 'admin';

  const loadProducts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getProducts();
      setProducts(res.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load products');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadProducts();
  }, [loadProducts]);

  const averagePrice = useMemo(() => {
    if (products.length === 0) return 0;
    return products.reduce((sum, product) => sum + product.current_price, 0) / products.length;
  }, [products]);

  const categories = useMemo(() => new Set(products.map((product) => product.category)).size, [products]);

  const averageSpread = useMemo(() => {
    if (products.length === 0) return 0;
    return products.reduce((sum, product) => sum + (product.current_price - product.base_cost), 0) / products.length;
  }, [products]);

  return (
    <div className="space-y-6">
      <SectionHeader
        kicker="Catalog"
        icon={<Boxes className="h-5 w-5" aria-hidden="true" />}
        title="Product Pricing Master"
        subtitle="Maintain a clean product list, import catalog updates, and run quick AI checks from the same operational screen."
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <SummaryCard title="Products" value={loading ? '-' : products.length} subtitle="SKUs available to pricing" />
        <SummaryCard title="Categories" value={loading ? '-' : categories} subtitle="Distinct product groups" variant="info" />
        <SummaryCard
          title="Average Spread"
          value={loading ? '-' : money.format(averageSpread)}
          subtitle={`Average price: ${money.format(averagePrice)}`}
          variant="success"
        />
      </div>

      {canImport ? (
        <BulkImportPanel onSuccess={loadProducts} />
      ) : (
        <AlertBanner variant="info" title="Read-only catalog">
          Your role can review product and price context, but catalog imports are limited to sales and admin users.
        </AlertBanner>
      )}

      {!canRecommend && (
        <AlertBanner variant="warning" title="Recommendation access restricted">
          <span className="inline-flex items-center gap-2">
            <Lock className="h-4 w-4" aria-hidden="true" />
            Executive role has read-only access on this screen.
          </span>
        </AlertBanner>
      )}

      {loading && (
        <div className="flex h-64 items-center justify-center rounded-lg border border-slate-200 bg-white">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-300 border-t-slate-800" />
        </div>
      )}
      {error && <AlertBanner variant="danger">{error}</AlertBanner>}
      {!loading && !error && <ProductTable products={products} canRecommend={canRecommend} />}

      <AlertBanner variant="tip" title="Import Tip">
        <span className="inline-flex items-center gap-2">
          <FileSpreadsheet className="h-4 w-4" aria-hidden="true" />
          Use the template before importing so SKU, cost, and list price columns match the backend validator.
        </span>
      </AlertBanner>
    </div>
  );
}
