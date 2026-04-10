import { notFound } from 'next/navigation';
import Image from 'next/image';
import { fetchDevice, fetchPrices, fetchTrends } from '../../lib/api';
import PriceTable from '../../components/PriceTable';
import PriceChart from '../../components/PriceChart';

interface Props { params: Promise<{ id: string }> }

export const revalidate = 300;

export default async function DeviceDetailPage({ params }: Props) {
  const { id } = await params;

  // Step 1: fetch device by slug — response contains the UUID
  let device;
  try {
    device = await fetchDevice(id);
  } catch {
    notFound();
  }

  // Step 2: use device.id (UUID) for prices & trends — NOT the slug
  const [prices, trends] = await Promise.all([
    fetchPrices(device.id).catch(() => []),
    fetchTrends(device.id).catch(() => []),
  ]);

  const bestPrice = prices.length
    ? Math.min(...prices.map((p: any) => p.price_egp))
    : null;

  const specs = [
    { label: 'Display',  value: device.display  },
    { label: 'Chipset',  value: device.chipset  },
    { label: 'RAM',      value: device.ram      },
    { label: 'Storage',  value: device.storage  },
    { label: 'Camera',   value: device.camera   },
    { label: 'Battery',  value: device.battery  },
    { label: 'OS',       value: device.os       },
  ].filter((s) => s.value);

  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
      {/* Header */}
      <div className="flex flex-col sm:flex-row gap-8 mb-10">
        {device.image_url && (
          <div className="relative w-44 h-56 flex-shrink-0 rounded-xl overflow-hidden bg-gray-50">
            <Image src={device.image_url} alt={device.name} fill className="object-contain p-3" />
          </div>
        )}
        <div className="flex-1">
          <p className="text-sm font-semibold text-[#01696f] uppercase tracking-wide mb-1">
            {device.brand.name}
          </p>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{device.name}</h1>
          {device.release_year && (
            <p className="text-sm text-gray-500 mb-4">Released {device.release_year}</p>
          )}
          {bestPrice !== null && (
            <div className="inline-block bg-green-50 border border-green-200 rounded-xl px-5 py-3">
              <p className="text-xs text-green-700 font-semibold uppercase tracking-wide">Best Price</p>
              <p className="text-2xl font-bold text-green-800">
                {new Intl.NumberFormat('ar-EG', {
                  style: 'currency', currency: 'EGP', maximumFractionDigits: 0,
                }).format(bestPrice)}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Specs */}
      {specs.length > 0 && (
        <section className="mb-10">
          <h2 className="text-xl font-semibold mb-4">Specifications</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {specs.map((s) => (
              <div key={s.label} className="flex justify-between bg-white rounded-lg
                                           border border-gray-100 px-4 py-3">
                <span className="text-sm text-gray-500">{s.label}</span>
                <span className="text-sm font-medium text-gray-800">{s.value}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Prices */}
      <section className="mb-10">
        <h2 className="text-xl font-semibold mb-4">Current Prices</h2>
        {prices.length === 0 ? (
          <p className="text-gray-400 text-sm">No prices available yet.</p>
        ) : (
          <PriceTable prices={prices} />
        )}
      </section>

      {/* Chart */}
      {trends.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold mb-4">Price History (90 days)</h2>
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <PriceChart trends={trends} />
          </div>
        </section>
      )}
    </div>
  );
}
