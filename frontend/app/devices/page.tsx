import { Suspense } from 'react';
import DeviceCard from '../components/DeviceCard';
import { fetchDevices } from '../lib/api';
import Link from 'next/link';

export const revalidate = 300;

const BRANDS = [
  'All','Samsung','Apple','Xiaomi','Oppo','Realme',
  'Huawei','Honor','Vivo','OnePlus','Tecno',
];

interface Props {
  searchParams?: { brand?: string; search?: string; page?: string };
}

export default async function DevicesPage({ searchParams }: Props) {
  const params = await searchParams;
  const brand  = params?.brand ?? '';
  const search = params?.search ?? '';
  const page   = Number(params?.page ?? 1);

  const data = await fetchDevices({ brand: brand || undefined, search: search || undefined, page, per_page: 24 })
    .catch(() => null);

  const totalPages = data ? Math.ceil(data.total / 24) : 1;

  return (
    <div className="max-w-7xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold mb-6">Smartphones in Egypt</h1>

      {/* Brand filter */}
      <div className="flex flex-wrap gap-2 mb-6">
        {BRANDS.map((b) => {
          const slug = b === 'All' ? '' : b.toLowerCase();
          const active = brand === slug;
          return (
            <Link
              key={b}
              href={`/devices${slug ? `?brand=${slug}` : ''}`}
              className={`px-4 py-1.5 rounded-full text-sm font-medium border transition-colors
                ${ active
                  ? 'bg-[#01696f] text-white border-[#01696f]'
                  : 'bg-white text-gray-700 border-gray-200 hover:border-[#01696f]'
                }`}
            >
              {b}
            </Link>
          );
        })}
      </div>

      {/* Results */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
        {data?.items.map((d) => <DeviceCard key={d.id} device={d} />) ?? (
          <p className="col-span-full text-gray-500">No devices found.</p>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2 mt-8">
          {page > 1 && (
            <Link href={`/devices?page=${page - 1}${brand ? `&brand=${brand}` : ''}`}
              className="px-4 py-2 bg-white border rounded-lg hover:border-[#01696f] text-sm">
              &larr; Prev
            </Link>
          )}
          <span className="px-4 py-2 text-sm text-gray-600">
            {page} / {totalPages}
          </span>
          {page < totalPages && (
            <Link href={`/devices?page=${page + 1}${brand ? `&brand=${brand}` : ''}`}
              className="px-4 py-2 bg-white border rounded-lg hover:border-[#01696f] text-sm">
              Next &rarr;
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
