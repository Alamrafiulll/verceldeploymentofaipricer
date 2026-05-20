import { useEffect, useMemo, useState } from 'react';
import { Calculator, Sparkles, SlidersHorizontal } from 'lucide-react';

import RecommendationCard from '../components/RecommendationCard';
import { AlertBanner, SectionHeader, SummaryCard } from '../components/ui';
import {
  getProducts,
  recommendPrice,
  type SandboxProduct,
  type SandboxRecommendation,
} from '../services/api';

const money = new Intl.NumberFormat('en-MY', {
  style: 'currency',
  currency: 'MYR',
  maximumFractionDigits: 2,
});

export default function Pricing() {
  const [products, setProducts] = useState<SandboxProduct[]>([]);
  const [productId, setProductId] = useState(() => localStorage.getItem('pricing_lab_product_id') ?? '');
  const [discount, setDiscount] = useState(() => {
    const saved = localStorage.getItem('pricing_lab_discount');
    return saved ? Number(saved) : 5;
  });
  const [channel, setChannel] = useState(() => localStorage.getItem('pricing_lab_channel') ?? 'direct');
  const [result, setResult] = useState<SandboxRecommendation | null>(() => {
    const saved = localStorage.getItem('pricing_lab_result');
    if (saved) {
      try {
        return JSON.parse(saved) as SandboxRecommendation;
      } catch {
        return null;
      }
    }
    return null;
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadProducts = async () => {
      try {
        const res = await getProducts();
        setProducts(res.data);
        if (res.data.length > 0) {
          const savedProductId = localStorage.getItem('pricing_lab_product_id');
          if (savedProductId && res.data.some((p) => p.id === savedProductId)) {
            setProductId(savedProductId);
          } else {
            setProductId(res.data[0].id);
          }
        }
      } catch {
        setProducts([]);
      }
    };
    void loadProducts();
  }, []);

  useEffect(() => {
    if (productId) {
      localStorage.setItem('pricing_lab_product_id', productId);
    }
  }, [productId]);

  useEffect(() => {
    localStorage.setItem('pricing_lab_discount', String(discount));
  }, [discount]);

  useEffect(() => {
    localStorage.setItem('pricing_lab_channel', channel);
  }, [channel]);

  useEffect(() => {
    if (result) {
      localStorage.setItem('pricing_lab_result', JSON.stringify(result));
    } else {
      localStorage.removeItem('pricing_lab_result');
    }
  }, [result]);

  const resetLab = () => {
    localStorage.removeItem('pricing_lab_product_id');
    localStorage.removeItem('pricing_lab_discount');
    localStorage.removeItem('pricing_lab_channel');
    localStorage.removeItem('pricing_lab_result');
    setDiscount(5);
    setChannel('direct');
    setResult(null);
    if (products.length > 0) {
      setProductId(products[0].id);
    }
  };

  const selectedProduct = useMemo(
    () => products.find((product) => product.id === productId),
    [productId, products],
  );

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

  return (
    <div className="space-y-6">
      <SectionHeader
        kicker="Pricing lab"
        icon={<Sparkles className="h-5 w-5" aria-hidden="true" />}
        title="AI Price Recommendation"
        subtitle="Run a quick product-level recommendation before creating a full customer quote."
        action={
          <button
            type="button"
            onClick={resetLab}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
          >
            Reset Lab
          </button>
        }
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <SummaryCard title="Products Loaded" value={products.length} subtitle="Available sandbox products" />
        <SummaryCard
          title="Selected List Price"
          value={selectedProduct ? money.format(selectedProduct.current_price) : '-'}
          subtitle={selectedProduct?.sku ?? 'Select a product'}
          variant="info"
        />
        <SummaryCard
          title="Test Discount"
          value={`${discount}%`}
          subtitle={`${channel.replace(/_/g, ' ')} channel`}
          variant={discount >= 20 ? 'warning' : 'success'}
        />
      </div>

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4 flex items-center gap-2">
          <SlidersHorizontal className="h-4 w-4 text-slate-500" aria-hidden="true" />
          <h2 className="text-base font-semibold text-slate-950">Recommendation Inputs</h2>
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1.4fr)_180px_180px_150px]">
          <label className="space-y-2 text-sm">
            <span className="font-semibold text-slate-700">Product</span>
            <select
              className="input"
              value={productId}
              onChange={(e) => setProductId(e.target.value)}
              disabled={products.length === 0}
            >
              {products.length === 0 ? (
                <option value="">No products found</option>
              ) : (
                products.map((product) => (
                  <option key={product.id} value={product.id}>
                    {product.sku} - {product.name}
                  </option>
                ))
              )}
            </select>
          </label>

          <label className="space-y-2 text-sm">
            <span className="font-semibold text-slate-700">Discount %</span>
            <input
              type="number"
              className="input"
              min={0}
              max={100}
              value={discount}
              onChange={(e) => setDiscount(Number(e.target.value))}
            />
          </label>

          <label className="space-y-2 text-sm">
            <span className="font-semibold text-slate-700">Channel</span>
            <select className="input capitalize" value={channel} onChange={(e) => setChannel(e.target.value)}>
              <option value="direct">Direct</option>
              <option value="distributor">Distributor</option>
              <option value="project">Project</option>
            </select>
          </label>

          <button
            type="button"
            className="mt-auto inline-flex items-center justify-center gap-2 rounded-lg bg-slate-950 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:opacity-60"
            onClick={runAI}
            disabled={loading || products.length === 0 || !productId}
          >
            <Calculator className="h-4 w-4" aria-hidden="true" />
            {loading ? 'Running' : 'Run AI'}
          </button>
        </div>

        <p className="mt-3 text-sm leading-6 text-slate-600">
          This lab is for quick product scenarios. Use New Quote when customer tier, inventory, policy, and approval
          governance must be included.
        </p>
        {error && (
          <div className="mt-4">
            <AlertBanner variant="danger">{error}</AlertBanner>
          </div>
        )}
      </section>

      <RecommendationCard result={result} />
    </div>
  );
}
