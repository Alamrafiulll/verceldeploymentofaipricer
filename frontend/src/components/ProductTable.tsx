import { useState } from 'react';

import { recommendPrice, type SandboxProduct, type SandboxRecommendation } from '../services/api';
import Spinner from './Spinner';

interface ProductTableProps {
  products: SandboxProduct[];
  canRecommend: boolean;
}

export default function ProductTable({ products, canRecommend }: ProductTableProps) {
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [latest, setLatest] = useState<SandboxRecommendation | null>(null);
  const [error, setError] = useState<string | null>(null);

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
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-card">
      {error && <p className="mb-3 text-sm text-rose-600">{error}</p>}
      {latest && (
        <p className="mb-3 text-sm text-slate-700">
          Last recommendation: {latest.product_id} {'->'} RM {latest.predicted_price.toFixed(2)} (
          {(latest.confidence * 100).toFixed(1)}%)
        </p>
      )}

      <div className="overflow-x-auto">
        <table className="w-full min-w-[700px] text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-slate-600">
              <th className="py-2">SKU</th>
              <th className="py-2">Name</th>
              <th className="py-2">Category</th>
              <th className="py-2">Price</th>
              <th className="py-2">Action</th>
            </tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.id} className="border-b border-slate-100">
                <td className="py-2">{p.sku}</td>
                <td className="py-2">{p.name}</td>
                <td className="py-2">{p.category}</td>
                <td className="py-2">RM {p.current_price.toFixed(2)}</td>
                <td className="py-2">
                  {canRecommend ? (
                    <button
                      type="button"
                      disabled={loadingId === p.id}
                      onClick={() => handleRecommend(p.id)}
                      className="flex items-center gap-2 rounded-md bg-blue-600 px-3 py-1.5 text-white disabled:opacity-60"
                    >
                      {loadingId === p.id ? <Spinner size="sm" color="light" /> : null}
                      {loadingId === p.id ? 'Running...' : 'AI Recommend'}
                    </button>
                  ) : (
                    <span className="rounded-md bg-slate-100 px-3 py-1.5 text-xs text-slate-500">
                      View only
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
