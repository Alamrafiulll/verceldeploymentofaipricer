import { useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { Calculator, PackageCheck, ShieldCheck, UserRound } from 'lucide-react';
import { z } from 'zod';

import type { Customer, Inventory, Product, StrategyMode } from '../types/api';
import StrategyToggle from './StrategyToggle';

const schema = z.object({
  customer_id: z.string().min(1, 'Select customer'),
  channel: z.string().min(1, 'Select channel'),
  product_id: z.string().min(1, 'Select product'),
  quantity: z.coerce.number().int().min(1, 'Quantity must be at least 1'),
  requested_price: z.preprocess(
    (value) => (value === '' ? undefined : value),
    z.coerce.number().positive().optional(),
  ),
  requested_discount: z.preprocess(
    (value) => (value === '' ? undefined : value),
    z.coerce.number().min(0).max(100).optional(),
  ),
});

export interface DealFormValues {
  customer_id: string;
  channel: string;
  product_id: string;
  quantity: number;
  requested_price?: number;
  requested_discount?: number;
  strategy_mode: StrategyMode;
}

interface Props {
  customers: Customer[];
  products: Product[];
  inventory: Inventory[];
  strategyMode: StrategyMode;
  onStrategyChange: (mode: StrategyMode) => void;
  onSubmit: (payload: DealFormValues) => void;
  loading: boolean;
}

interface DealFormState {
  customer_id: string;
  channel: string;
  product_id: string;
  quantity: number;
  requested_price: string;
  requested_discount: string;
}

const money = new Intl.NumberFormat('en-MY', {
  style: 'currency',
  currency: 'MYR',
  maximumFractionDigits: 2,
});

export default function DealInputForm({
  customers,
  products,
  inventory,
  strategyMode,
  onStrategyChange,
  onSubmit,
  loading,
}: Props) {
  const [values, setValues] = useState<DealFormState>({
    customer_id: '',
    channel: 'direct',
    product_id: '',
    quantity: 10,
    requested_price: '',
    requested_discount: '',
  });
  const [error, setError] = useState('');

  const selectedCustomer = useMemo(
    () => customers.find((customer) => customer.id === values.customer_id),
    [customers, values.customer_id],
  );
  const selectedProduct = useMemo(
    () => products.find((product) => product.id === values.product_id),
    [products, values.product_id],
  );
  const selectedInventory = useMemo(
    () => inventory.find((item) => item.product_id === values.product_id),
    [inventory, values.product_id],
  );

  const update = <K extends keyof DealFormState>(name: K, value: DealFormState[K]) => {
    setValues((prev) => ({ ...prev, [name]: value }));
  };

  return (
    <form
      className="glass-card rounded-2xl border border-slate-200/60 dark:border-slate-800/60 shadow-sm transition-all duration-300 overflow-hidden"
      onSubmit={(event) => {
        event.preventDefault();
        const parsed = schema.safeParse(values);
        if (!parsed.success) {
          setError(parsed.error.issues[0]?.message ?? 'Invalid input');
          return;
        }

        const payload: DealFormValues = {
          customer_id: parsed.data.customer_id,
          channel: parsed.data.channel,
          product_id: parsed.data.product_id,
          quantity: parsed.data.quantity,
          strategy_mode: strategyMode,
        };

        if (typeof parsed.data.requested_price === 'number') {
          payload.requested_price = parsed.data.requested_price;
        }
        if (typeof parsed.data.requested_discount === 'number') {
          payload.requested_discount = parsed.data.requested_discount;
        }

        setError('');
        onSubmit(payload);
      }}
    >
      <div className="border-b border-slate-200/60 dark:border-slate-800/60 p-6">
        <p className="text-[10px] font-extrabold uppercase tracking-[0.18em] text-slate-400 dark:text-slate-500">Quote builder</p>
        <h2 className="mt-1.5 font-display text-2xl font-extrabold tracking-tight text-slate-900 dark:text-white">
          Create Quote And Generate Recommendation
        </h2>
        <p className="mt-2 max-w-4xl text-xs font-semibold leading-relaxed text-slate-500 dark:text-slate-400">
          Complete the account, channel, product, quantity, and target price context. The system will generate a price
          band, explain margin impact, and identify whether governance approval is required.
        </p>
      </div>

      <div className="grid gap-0 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="space-y-6 p-6">
          <section className="space-y-4">
            <div className="flex items-center gap-3">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-600 dark:bg-indigo-500/25 dark:text-indigo-400">
                <UserRound className="h-4 w-4" aria-hidden="true" />
              </span>
              <h3 className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">Deal Setup</h3>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <Field label="Customer" required helper="Choose an approved account from master data.">
                <select
                  className="input"
                  value={values.customer_id}
                  onChange={(event) => update('customer_id', event.target.value)}
                  disabled={loading}
                >
                  <option value="">Select customer</option>
                  {customers.map((customer) => (
                    <option key={customer.id} value={customer.id}>
                      {customer.name}
                    </option>
                  ))}
                </select>
              </Field>

              <Field label="Sales Channel" required helper="Channel controls margin floors and discount guardrails.">
                <select
                  className="input"
                  value={values.channel}
                  onChange={(event) => update('channel', event.target.value)}
                  disabled={loading}
                >
                  <option value="direct">Direct</option>
                  <option value="distributor">Distributor</option>
                  <option value="project">Project</option>
                </select>
              </Field>
            </div>
          </section>

          <section className="space-y-4">
            <div className="flex items-center gap-3">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-600 dark:bg-indigo-500/25 dark:text-indigo-400">
                <PackageCheck className="h-4 w-4" aria-hidden="true" />
              </span>
              <h3 className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">Product And Volume</h3>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-[1.5fr_0.6fr]">
              <Field label="Product" required helper="Select the SKU that will receive the recommendation.">
                <select
                  className="input"
                  value={values.product_id}
                  onChange={(event) => update('product_id', event.target.value)}
                  disabled={loading}
                >
                  <option value="">Select product</option>
                  {products.map((product) => (
                    <option key={product.id} value={product.id}>
                      {product.name} ({product.sku})
                    </option>
                  ))}
                </select>
              </Field>

              <Field label="Quantity" required helper="Used for revenue and margin calculations.">
                <input
                  className="input"
                  type="number"
                  min={1}
                  value={values.quantity}
                  onChange={(event) => update('quantity', Number(event.target.value))}
                  disabled={loading}
                />
              </Field>
            </div>
          </section>

          <section className="space-y-4">
            <div className="flex items-center gap-3">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-600 dark:bg-indigo-500/25 dark:text-indigo-400">
                <Calculator className="h-4 w-4" aria-hidden="true" />
              </span>
              <h3 className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">Customer Target Request</h3>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <Field label="Requested Price" helper="Optional. Leave blank to optimize from list price.">
                <input
                  className="input"
                  type="number"
                  step="0.01"
                  value={values.requested_price}
                  onChange={(event) => update('requested_price', event.target.value)}
                  disabled={loading}
                  placeholder="Example: 593.50"
                />
              </Field>

              <Field label="Requested Discount %" helper="Optional. Use when customer negotiates by discount.">
                <input
                  className="input"
                  type="number"
                  min={0}
                  max={100}
                  step="0.1"
                  value={values.requested_discount}
                  onChange={(event) => update('requested_discount', event.target.value)}
                  disabled={loading}
                  placeholder="Example: 7.5"
                />
              </Field>
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center gap-3">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-600 dark:bg-indigo-500/25 dark:text-indigo-400">
                <ShieldCheck className="h-4 w-4" aria-hidden="true" />
              </span>
              <h3 className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">Pricing Strategy</h3>
            </div>
            <StrategyToggle value={strategyMode} onChange={onStrategyChange} />
          </section>

          {error ? (
            <div className="rounded-xl border border-rose-500/25 bg-rose-500/5 p-4 text-xs font-semibold text-rose-700 dark:text-rose-400">{error}</div>
          ) : null}
        </div>

        <aside className="border-t border-slate-200/60 dark:border-slate-800/60 bg-slate-500/5 dark:bg-slate-950/20 p-6 lg:border-l lg:border-t-0 flex flex-col justify-between">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400 dark:text-slate-500">Live Quote Context</h3>
            <div className="mt-4 space-y-3">
              <Auto label="Customer Tier" value={selectedCustomer?.tier ?? '-'} />
              <Auto
                label="List Price / Cost"
                value={
                  selectedProduct
                    ? `${money.format(selectedProduct.list_price)} / ${money.format(selectedProduct.unit_cost)}`
                    : '-'
                }
              />
              <Auto label="Inventory On Hand" value={selectedInventory ? `${selectedInventory.on_hand}` : '-'} />
              <Auto label="Average Stock Age" value={selectedInventory ? `${selectedInventory.stock_age_days_avg} days` : '-'} />
            </div>

            <div className="mt-5 rounded-xl border border-slate-200/60 dark:border-slate-800/60 bg-white/70 dark:bg-slate-900/40 p-4.5">
              <p className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">Before you run</p>
              <ul className="mt-3.5 space-y-2.5 text-xs font-semibold leading-relaxed text-slate-500 dark:text-slate-400 list-disc list-inside">
                <li>Use uploaded price lists and competitor files for better context.</li>
                <li>Enter either a requested price, requested discount, or neither.</li>
                <li>Approval will be suggested when the selected price falls outside guardrails.</li>
              </ul>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary mt-6 w-full flex items-center justify-center gap-2"
          >
            {loading ? 'Building Recommendation...' : 'Generate Recommended Price'}
          </button>
        </aside>
      </div>
    </form>
  );
}

function Field({
  label,
  children,
  helper,
  required,
}: {
  label: string;
  children: ReactNode;
  helper?: string;
  required?: boolean;
}) {
  return (
    <label className="block text-sm">
      <span className="flex items-center gap-1.5 text-xs font-bold text-slate-650 dark:text-slate-350">
        {label}
        {required && <span className="text-rose-600 font-extrabold">*</span>}
      </span>
      <span className="mt-2 block">{children}</span>
      {helper && <span className="mt-1.5 block text-xs leading-relaxed text-slate-400 dark:text-slate-500 font-semibold">{helper}</span>}
    </label>
  );
}

function Auto({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-xl border border-slate-200/60 dark:border-slate-800/40 bg-white/70 dark:bg-slate-900/40 p-3.5 transition-all duration-300">
      <p className="text-[10px] font-extrabold uppercase tracking-[0.16em] text-slate-400 dark:text-slate-500">{label}</p>
      <p className="mt-1.5 font-display text-sm font-bold tracking-tight text-slate-900 dark:text-white">{value}</p>
    </article>
  );
}
