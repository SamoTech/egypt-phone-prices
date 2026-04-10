import type { Device, PaginatedDevices, Price, PriceTrendPoint } from '../types';

// In production on Vercel: /api/* is rewritten to the FastAPI backend.
// In local dev: next.config.ts rewrites /api/* → localhost:8000.
// No NEXT_PUBLIC_API_URL env var needed.
const API = typeof window === 'undefined'
  ? (process.env.INTERNAL_API_URL ?? '')
  : '';

async function apiFetch<T>(path: string): Promise<T> {
  const url = `${API}/api${path}`;
  const res = await fetch(url, { next: { revalidate: 300 } });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
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
