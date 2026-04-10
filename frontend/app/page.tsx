import Link from 'next/link';
import { fetchDevices } from './lib/api';
import DeviceCard from './components/DeviceCard';

export const revalidate = 300;

export default async function HomePage() {
  const data = await fetchDevices({ per_page: 12, page: 1 }).catch(() => null);

  return (
    <div className="max-w-7xl mx-auto px-4 py-12">
      {/* Hero */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          📱 Egypt Phone Prices
        </h1>
        <p className="text-lg text-gray-600 max-w-xl mx-auto">
          Real-time smartphone prices from Jumia, Noon, B.Tech, and Amazon Egypt.
          Updated daily.
        </p>
        <Link
          href="/devices"
          className="mt-6 inline-block bg-[#01696f] hover:bg-[#0c4e54] text-white
                     font-semibold px-8 py-3 rounded-lg transition-colors"
        >
          Browse All Devices
        </Link>
      </div>

      {/* Latest Devices */}
      <h2 className="text-2xl font-semibold mb-6">Latest Devices</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {data?.items.map((d) => <DeviceCard key={d.id} device={d} />) ?? (
          <p className="col-span-full text-gray-500">Could not load devices.</p>
        )}
      </div>

      {data && (
        <div className="mt-8 text-center">
          <Link href="/devices" className="text-[#01696f] hover:underline font-medium">
            View all {data.total} devices →
          </Link>
        </div>
      )}
    </div>
  );
}
