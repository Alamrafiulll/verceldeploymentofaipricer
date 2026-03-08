import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

interface PriceChartPoint {
  label: string;
  price: number;
}

interface PriceChartProps {
  data: PriceChartPoint[];
}

export default function PriceChart({ data }: PriceChartProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-card">
      <p className="mb-3 text-sm font-semibold text-slate-700">Current Price Trend (by SKU sample)</p>
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis dataKey="label" />
            <YAxis />
            <Tooltip />
            <CartesianGrid stroke="#e2e8f0" />
            <Line type="monotone" dataKey="price" stroke="#0f172a" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
