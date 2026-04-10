import Link from 'next/link';
import Image from 'next/image';
import type { Device } from '../types';

interface Props { device: Device }

export default function DeviceCard({ device }: Props) {
  return (
    <Link
      href={`/devices/${device.slug}`}
      className="group bg-white rounded-xl border border-gray-200 p-4 flex flex-col
                 hover:shadow-md hover:border-[#01696f] transition-all duration-200"
    >
      <div className="relative w-full aspect-square mb-3 rounded-lg overflow-hidden bg-gray-50">
        {device.image_url ? (
          <Image
            src={device.image_url}
            alt={device.name}
            fill
            sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
            className="object-contain p-2"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-300 text-4xl">
            📱
          </div>
        )}
      </div>

      <div className="mt-auto">
        <p className="text-xs text-[#01696f] font-semibold uppercase tracking-wide mb-1">
          {device.brand.name}
        </p>
        <h3 className="text-sm font-semibold text-gray-900 line-clamp-2 group-hover:text-[#01696f]
                       transition-colors leading-snug">
          {device.name}
        </h3>
        {device.release_year && (
          <p className="text-xs text-gray-400 mt-1">{device.release_year}</p>
        )}
      </div>
    </Link>
  );
}
