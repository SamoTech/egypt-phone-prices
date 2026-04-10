'use client';
import { ExternalLink, CheckCircle, XCircle } from 'lucide-react';
import type { Price } from '../types';

interface Props { prices: Price[] }

function formatEGP(n: number) {
  return new Intl.NumberFormat('ar-EG', {
    style: 'currency', currency: 'EGP', maximumFractionDigits: 0,
  }).format(n);
}

export default function PriceTable({ prices }: Props) {
  // Latest price per retailer
  const latest = new Map<string, Price>();
  for (const p of prices) {
    if (!latest.has(p.retailer.slug)) latest.set(p.retailer.slug, p);
  }
  const rows = [...latest.values()].sort((a, b) => a.price_egp - b.price_egp);

  if (rows.length === 0) {
    return <p className="text-gray-500 text-sm">No prices available yet.</p>;
  }

  const best = rows[0].price_egp;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b border-gray-200 text-left text-xs font-semibold
                         text-gray-500 uppercase tracking-wide">
            <th className="py-3 pr-4">Retailer</th>
            <th className="py-3 pr-4">Price</th>
            <th className="py-3 pr-4">Stock</th>
            <th className="py-3">Link</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((p) => (
            <tr key={p.id} className="border-b border-gray-100 hover:bg-gray-50">
              <td className="py-3 pr-4 font-medium text-gray-800">{p.retailer.name}</td>
              <td className="py-3 pr-4">
                <span className={`font-bold ${
                  p.price_egp === best ? 'text-green-700' : 'text-gray-800'
                }`}>
                  {formatEGP(p.price_egp)}
                </span>
                {p.original_price_egp && p.original_price_egp > p.price_egp && (
                  <span className="ml-2 line-through text-gray-400 text-xs">
                    {formatEGP(p.original_price_egp)}
                  </span>
                )}
                {p.price_egp === best && (
                  <span className="ml-2 text-xs text-green-700 font-semibold">Best</span>
                )}
              </td>
              <td className="py-3 pr-4">
                {p.in_stock
                  ? <CheckCircle size={16} className="text-green-600" />
                  : <XCircle    size={16} className="text-red-500"   />}
              </td>
              <td className="py-3">
                <a
                  href={p.product_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-[#01696f] hover:underline"
                >
                  View <ExternalLink size={12} />
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
