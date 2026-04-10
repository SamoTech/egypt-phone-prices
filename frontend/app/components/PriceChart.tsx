'use client';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import type { PriceTrendPoint } from '../types';

interface Props { trends: PriceTrendPoint[] }

const COLORS = ['#01696f', '#e27021', '#9b59b6', '#2980b9', '#27ae60'];

export default function PriceChart({ trends }: Props) {
  if (trends.length === 0) {
    return <p className="text-gray-500 text-sm">No historical data yet.</p>;
  }

  // Pivot: date -> { retailer: price }
  const retailers = [...new Set(trends.map((t) => t.retailer))];
  const byDate = new Map<string, Record<string, number>>();
  for (const t of trends) {
    if (!byDate.has(t.date)) byDate.set(t.date, {});
    byDate.get(t.date)![t.retailer] = t.price_egp;
  }
  const chartData = [...byDate.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, vals]) => ({ date, ...vals }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v/1000).toFixed(0)}K`} />
        <Tooltip formatter={(v: number) => `EGP ${v.toLocaleString()}`} />
        <Legend />
        {retailers.map((r, i) => (
          <Line
            key={r} type="monotone" dataKey={r}
            stroke={COLORS[i % COLORS.length]}
            strokeWidth={2} dot={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
