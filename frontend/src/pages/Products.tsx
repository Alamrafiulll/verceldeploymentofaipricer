import { useEffect, useState, useCallback } from 'react';

import BulkImportPanel from '../components/BulkImportPanel';
import ProductTable from '../components/ProductTable';
import { getSession } from '../lib/auth';
import { getProducts, type SandboxProduct } from '../services/api';

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

  return (
    <div className="p-1">

      <h2 className="mb-4 text-2xl font-bold text-slate-900">Product List</h2>

      {canImport && (
        <BulkImportPanel onSuccess={loadProducts} />
      )}

      {!canRecommend && (
        <p className="mb-3 text-sm text-slate-600">
          Executive role has read-only access on this screen.
        </p>
      )}
      {loading && (
        <div className="flex h-64 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-300 border-t-slate-700" />
        </div>
      )}
      {error && <p className="text-sm text-rose-600">{error}</p>}
      {!loading && !error && <ProductTable products={products} canRecommend={canRecommend} />}
    </div>
  );
}

