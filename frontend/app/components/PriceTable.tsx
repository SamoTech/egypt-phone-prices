'use client';
import { ExternalLink, CheckCircle, XCircle, ShoppingCart } from 'lucide-react';
import type { Price } from '../types';

interface Props { prices: Price[]; deviceName: string }

function formatEGP(n: number) {
  return new Intl.NumberFormat('ar-EG', {
    style: 'currency', currency: 'EGP', maximumFractionDigits: 0,
  }).format(n);
}

const SEARCH_URLS: Record<string, (name: string) => string> = {
  jumia:   (n) => `https://www.jumia.com.eg/catalog/?q=${encodeURIComponent(n)}`,
  noon:    (n) => `https://www.noon.com/egypt-en/search/?q=${encodeURIComponent(n)}`,
  amazon:  (n) => `https://www.amazon.eg/s?k=${encodeURIComponent(n)}`,
  btech:   (n) => `https://btech.com/en/catalogsearch/result/?q=${encodeURIComponent(n)}`,
  raneen:  (n) => `https://www.raneen.com/en/search?q=${encodeURIComponent(n)}`,
  elaraby: (n) => `https://www.elarabygroup.com/search?q=${encodeURIComponent(n)}`,
};

function getLink(p: Price, deviceName: string): string {
  const url = p.product_url ?? '';
  const isInternal =
    !url ||
    url.startsWith('/') ||
    url.includes('egypt-phone-prices') ||
    url.includes('vercel.app');

  if (!isInternal) return url;

  const slug = p.retailer?.slug ?? '';
  const name = p.retailer?.name?.toLowerCase() ?? '';
  for (const [key, builder] of Object.entries(SEARCH_URLS)) {
    if (slug.includes(key) || name.includes(key)) return builder(deviceName);
  }
  return p.retailer?.base_url ?? '#';
}

export default function PriceTable({ prices, deviceName }: Props) {
  const latest = new Map<string, Price>();
  for (const p of prices) {
    const key = p.retailer?.slug ?? String(p.id);
    if (!latest.has(key)) latest.set(key, p);
  }
  const rows = [...latest.values()].sort((a, b) => a.price_egp - b.price_egp);

  if (rows.length === 0) {
    return (
      <div className="text-center py-10 text-gray-400">
        <ShoppingCart size={40} className="mx-auto mb-3 opacity-30" />
        <p className="text-sm">No prices available yet. Check back after the next scrape.</p>
      </div>
    );
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
            <th className="py-3">Buy</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((p) => {
            const link   = getLink(p, deviceName);
            const isBest = p.price_egp === best;
            return (
              <tr key={p.id}
                  className={`border-b border-gray-100 hover:bg-gray-50 transition-colors
                    ${isBest ? 'bg-green-50/40' : ''}`}>

                <td className="py-3 pr-4">
                  <div className="flex items-center gap-2">
                    {p.retailer?.logo_url && (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={p.retailer.logo_url} alt={p.retailer.name}
                           width={20} height={20} className="object-contain rounded" />
                    )}
                    <span className="font-medium text-gray-800">
                      {p.retailer?.name ?? 'Unknown'}
                    </span>
                  </div>
                </td>

                <td className="py-3 pr-4">
                  <div className="flex items-baseline gap-2 flex-wrap">
                    <span className={`font-bold text-base ${
                      isBest ? 'text-green-700' : 'text-gray-800'
                    }`}>
                      {formatEGP(p.price_egp)}
                    </span>
                    {p.original_price_egp && p.original_price_egp > p.price_egp && (
                      <span className="line-through text-gray-400 text-xs">
                        {formatEGP(p.original_price_egp)}
                      </span>
                    )}
                    {isBest && (
                      <span className="text-xs bg-green-100 text-green-700
                                       px-1.5 py-0.5 rounded font-semibold">Best</span>
                    )}
                  </div>
                </td>

                <td className="py-3 pr-4">
                  {p.in_stock
                    ? <span className="inline-flex items-center gap-1 text-green-600 text-xs font-medium">
                        <CheckCircle size={14} /> In Stock
                      </span>
                    : <span className="inline-flex items-center gap-1 text-red-400 text-xs">
                        <XCircle size={14} /> Out
                      </span>
                  }
                </td>

                <td className="py-3">
                  <a
                    href={link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                               bg-[#01696f] text-white text-xs font-semibold
                               hover:bg-[#0c4e54] transition-colors"
                  >
                    Buy <ExternalLink size={11} />
                  </a>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
