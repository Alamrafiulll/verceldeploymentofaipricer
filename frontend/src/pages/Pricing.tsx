import { useEffect, useState } from 'react';

import RecommendationCard from '../components/RecommendationCard';
import Spinner from '../components/Spinner';
import {
  getProducts,
  recommendPrice,
  type SandboxProduct,
  type SandboxRecommendation,
} from '../services/api';

const CHANNELS = [
  { value: 'direct', label: '🏪 Direct Sales', desc: 'Sell directly to end customers' },
  { value: 'distributor', label: '🚚 Distributor', desc: 'Wholesale to distributors (8% off)' },
  { value: 'project', label: '🏗️ Project / Bulk', desc: 'Project-based pricing (12% off)' },
];

export default function Pricing() {
  const [products, setProducts] = useState<SandboxProduct[]>([]);
  const [productId, setProductId] = useState('');
  const [discount, setDiscount] = useState(5);
  const [channel, setChannel] = useState('direct');
  const [result, setResult] = useState<SandboxRecommendation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadProducts = async () => {
      try {
        const res = await getProducts();
        setProducts(res.data);
        if (res.data.length > 0) {
          setProductId(res.data[0].id);
        }
      } catch {
        setProducts([]);
      }
    };
    void loadProducts();
  }, []);

  const runAI = async () => {
    const id = productId.trim();
    if (!id) {
      setError('Select a product first.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await recommendPrice(id, discount, channel);
      setResult(res.data);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Failed to run recommendation');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const selectedProduct = products.find((p) => p.id === productId);

  return (
    <div className="p-1">

      <h2 className="mb-4 text-2xl font-bold text-slate-900">AI Price Recommendation</h2>

      {/* Channel Selector */}
      <div className="mb-4 rounded-xl border border-slate-200 bg-white p-4 shadow-card">
        <p className="mb-3 text-xs font-medium uppercase tracking-wider text-slate-400">
          Select Pricing Channel
        </p>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
          {CHANNELS.map((ch) => (
            <button
              key={ch.value}
              type="button"
              className={`rounded-lg border-2 px-4 py-3 text-left transition-all ${
                channel === ch.value
                  ? 'border-emerald-500 bg-emerald-50 shadow-sm'
                  : 'border-slate-200 bg-white hover:border-slate-300'
              }`}
              onClick={() => setChannel(ch.value)}
            >
              <span className="text-sm font-semibold text-slate-800">{ch.label}</span>
              <p className="mt-0.5 text-[11px] text-slate-500">{ch.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Product & Discount Input */}
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-card">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-[1fr,180px,140px]">
          <select
            className="rounded-lg border border-slate-300 px-3 py-2"
            value={productId}
            onChange={(e) => setProductId(e.target.value)}
            disabled={products.length === 0}
          >
            {products.length === 0 ? (
              <option value="">No products found</option>
            ) : (
              products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.sku} - {p.name} (RM {p.current_price.toFixed(2)})
                </option>
              ))
            )}
          </select>
          <input
            type="number"
            placeholder="Discount %"
            className="rounded-lg border border-slate-300 px-3 py-2"
            min={0}
            max={100}
            value={discount}
            onChange={(e) => setDiscount(Number(e.target.value))}
          />
          <button
            type="button"
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 font-medium text-white disabled:opacity-60"
            onClick={runAI}
            disabled={loading || products.length === 0 || !productId}
          >
            {loading ? <Spinner size="sm" color="light" /> : null}
            {loading ? 'Running...' : '🤖 Run AI'}
          </button>
        </div>
        <div className="mt-2 flex items-center gap-4 text-xs text-slate-500">
          <span>Channel: <strong className="text-slate-700">{CHANNELS.find(c => c.value === channel)?.label}</strong></span>
          {selectedProduct && (
            <span>
              Cost: <strong className="text-slate-700">RM {selectedProduct.base_cost.toFixed(2)}</strong>
              {' | '}
              List: <strong className="text-slate-700">RM {selectedProduct.current_price.toFixed(2)}</strong>
            </span>
          )}
        </div>
        {error && <p className="mt-3 text-sm text-rose-600">{error}</p>}
      </div>

      {/* Margin Simulator (discount slider) */}
      {selectedProduct && (
        <div className="mt-4 rounded-xl border border-slate-200 bg-white p-4 shadow-card">
          <h3 className="mb-3 text-sm font-semibold text-slate-700">📊 Margin Simulator</h3>
          <input
            type="range"
            min={0}
            max={35}
            step={0.5}
            value={discount}
            onChange={(e) => setDiscount(Number(e.target.value))}
            className="w-full accent-emerald-600"
          />
          <div className="mt-2 grid grid-cols-3 gap-3 text-center text-sm">
            <div className="rounded-lg bg-slate-50 p-3">
              <p className="text-xs text-slate-500">Discount</p>
              <p className="text-lg font-bold text-slate-800">{discount.toFixed(1)}%</p>
            </div>
            <div className="rounded-lg bg-slate-50 p-3">
              <p className="text-xs text-slate-500">Estimated Price</p>
              <p className="text-lg font-bold text-emerald-700">
                RM {(selectedProduct.current_price * (1 - discount / 100)).toFixed(2)}
              </p>
            </div>
            <div className="rounded-lg bg-slate-50 p-3">
              <p className="text-xs text-slate-500">Est. Margin</p>
              <p className={`text-lg font-bold ${
                ((selectedProduct.current_price * (1 - discount / 100) - selectedProduct.base_cost) /
                  (selectedProduct.current_price * (1 - discount / 100))) *
                  100 <
                10
                  ? 'text-red-600'
                  : 'text-emerald-700'
              }`}>
                {(
                  ((selectedProduct.current_price * (1 - discount / 100) - selectedProduct.base_cost) /
                    (selectedProduct.current_price * (1 - discount / 100))) *
                  100
                ).toFixed(1)}
                %
              </p>
            </div>
          </div>
        </div>
      )}

      <RecommendationCard result={result} />
    </div>
  );
}
