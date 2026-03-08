import { useMemo, useState } from 'react';
import type { ReactNode } from 'react';
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
  const [isNewCustomer, setIsNewCustomer] = useState(false);
  const [newCustomerName, setNewCustomerName] = useState('');

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
      className="space-y-5 rounded-2xl border border-white/80 bg-white p-5 shadow-card"
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
      <div>
        <h2 className="font-display text-2xl font-semibold">Create Quote and Get an Explainable Recommendation</h2>
        <p className="text-sm text-slate-600">
          Enter the deal details, review the recommendation, then finalize or request approval governance.
        </p>
      </div>

      <StrategyToggle value={strategyMode} onChange={onStrategyChange} />

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Field label="Customer">
          <div className="flex flex-col gap-2">
            {isNewCustomer ? (
              <input
                className="input"
                placeholder="Enter new customer name"
                value={newCustomerName}
                onChange={(e) => setNewCustomerName(e.target.value)}
                disabled={loading}
              />
            ) : (
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
            )}
            <button
              type="button"
              onClick={() => {
                setIsNewCustomer(!isNewCustomer);
                setError('');
              }}
              className="text-xs text-blue-600 hover:underline text-left w-fit"
            >
              {isNewCustomer ? 'Select existing customer' : 'Record new customer'}
            </button>
          </div>
        </Field>

        <Field label="Channel">
          <select
            className="input"
            value={values.channel}
            onChange={(event) => update('channel', event.target.value)}
          >
            <option value="direct">Direct</option>
            <option value="distributor">Distributor</option>
            <option value="project">Project</option>
          </select>
        </Field>

        <Field label="Product">
          <select
            className="input"
            value={values.product_id}
            onChange={(event) => update('product_id', event.target.value)}
          >
            <option value="">Select product</option>
            {products.map((product) => (
              <option key={product.id} value={product.id}>
                {product.name} ({product.sku})
              </option>
            ))}
          </select>
        </Field>

        <Field label="Quantity">
          <input
            className="input"
            type="number"
            min={1}
            value={values.quantity}
            onChange={(event) => update('quantity', Number(event.target.value))}
          />
        </Field>

        <Field label="Requested Price (optional)">
          <input
            className="input"
            type="number"
            step="0.01"
            value={values.requested_price}
            onChange={(event) => update('requested_price', event.target.value)}
          />
        </Field>

        <Field label="Requested Discount % (optional)">
          <input
            className="input"
            type="number"
            min={0}
            max={100}
            step="0.1"
            value={values.requested_discount}
            onChange={(event) => update('requested_discount', event.target.value)}
          />
        </Field>
      </div>

      <div className="grid gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3 md:grid-cols-4">
        <Auto label="Customer Tier" value={selectedCustomer?.tier ?? '-'} />
        <Auto
          label="List Price / Cost"
          value={selectedProduct ? `RM ${selectedProduct.list_price.toFixed(2)} / RM ${selectedProduct.unit_cost.toFixed(2)}` : '-'}
        />
        <Auto label="Inventory On Hand" value={selectedInventory ? `${selectedInventory.on_hand}` : '-'} />
        <Auto
          label="Stock Age"
          value={selectedInventory ? `${selectedInventory.stock_age_days_avg} days` : '-'}
        />
      </div>

      {error ? <p className="text-sm text-signal-red">{error}</p> : null}

      <button
        type="submit"
        disabled={loading}
        className="rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:opacity-60"
      >
        {loading ? 'Building Recommendation...' : 'Get Recommended Price'}
      </button>
    </form>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="space-y-1.5 text-sm">
      <span className="text-slate-600">{label}</span>
      {children}
    </label>
  );
}

function Auto({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-lg bg-white p-2">
      <p className="text-[11px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-semibold">{value}</p>
    </article>
  );
}
