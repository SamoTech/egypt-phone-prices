import type { Device, PaginatedDevices, Price, PriceTrendPoint } from '../types';

// All requests go to /api/* which is handled by the Next.js proxy route.
// Works on Vercel (proxies to BACKEND_URL env var) and locally
// (proxies to localhost:8000 when BACKEND_URL is not set).
const BASE = '/api';

async function apiFetch<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...opts,
    next: { revalidate: 300 },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`API ${res.status} on ${path}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export function fetchDevices(params?: {
  brand?: string;
  search?: string;
  year?: number;
  page?: number;
  per_page?: number;
}): Promise<PaginatedDevices> {
  const q = new URLSearchParams();
  if (params?.brand)    q.set('brand',    params.brand);
  if (params?.search)   q.set('search',   params.search);
  if (params?.year)     q.set('year',     String(params.year));
  if (params?.page)     q.set('page',     String(params.page));
  if (params?.per_page) q.set('per_page', String(params.per_page));
  const qs = q.toString();
  return apiFetch<PaginatedDevices>(`/devices${qs ? '?' + qs : ''}`);
}

export function fetchDevice(slug: string): Promise<Device> {
  return apiFetch<Device>(`/devices/${slug}`);
}

export function fetchPrices(deviceId: string): Promise<Price[]> {
  return apiFetch<Price[]>(`/prices?device_id=${deviceId}`);
}

export function fetchTrends(deviceId: string, days = 90): Promise<PriceTrendPoint[]> {
  return apiFetch<PriceTrendPoint[]>(`/trends?device_id=${deviceId}&days=${days}`);
}
