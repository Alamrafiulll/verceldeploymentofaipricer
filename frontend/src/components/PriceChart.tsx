import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { TrendingUp } from 'lucide-react';

interface PriceChartPoint {
  label: string;
  price: number;
}

interface PriceChartProps {
  data: PriceChartPoint[];
}

export default function PriceChart({ data }: PriceChartProps) {
  return (
    <section className="glass-card rounded-2xl p-6 border border-slate-200/60 dark:border-slate-800/60 shadow-sm">
      <div className="mb-6 flex items-center gap-3">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-600 dark:bg-indigo-500/25 dark:text-indigo-400">
          <TrendingUp className="h-4.5 w-4.5" aria-hidden="true" />
        </span>
        <div>
          <h2 className="text-base font-extrabold text-slate-900 dark:text-white">Current Price Trend</h2>
          <p className="text-xs font-semibold text-slate-400 dark:text-slate-500">Sample of loaded SKUs and their active pricing levels.</p>
        </div>
      </div>
      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 15, bottom: 10, left: 0 }}>
            <defs>
              <linearGradient id="colorPrice" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#6366f1" />
                <stop offset="100%" stopColor="#8b5cf6" />
              </linearGradient>
            </defs>
            <XAxis 
              dataKey="label" 
              tick={{ fontSize: 11, fontWeight: 'semibold', fill: '#94a3b8' }} 
              axisLine={{ stroke: 'rgba(148, 163, 184, 0.15)' }}
              tickLine={{ stroke: 'rgba(148, 163, 184, 0.15)' }}
            />
            <YAxis 
              tick={{ fontSize: 11, fontWeight: 'semibold', fill: '#94a3b8' }} 
              axisLine={{ stroke: 'rgba(148, 163, 184, 0.15)' }}
              tickLine={{ stroke: 'rgba(148, 163, 184, 0.15)' }}
            />
            <Tooltip
              formatter={(value) => [`RM ${Number(value).toFixed(2)}`, 'Price']}
              contentStyle={{ 
                borderRadius: 14, 
                backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                borderColor: 'rgba(255, 255, 255, 0.15)',
                color: '#fff',
                fontSize: 12,
                fontWeight: 'bold',
                backdropFilter: 'blur(8px)',
                boxShadow: '0 10px 25px rgba(0,0,0,0.3)'
              }}
            />
            <CartesianGrid stroke="rgba(148, 163, 184, 0.08)" strokeDasharray="5 5" />
            <Line 
              type="monotone" 
              dataKey="price" 
              stroke="url(#colorPrice)" 
              strokeWidth={3} 
              dot={{ r: 4, stroke: '#6366f1', strokeWidth: 2, fill: '#fff' }} 
              activeDot={{ r: 7, stroke: '#8b5cf6', strokeWidth: 2, fill: '#fff' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
