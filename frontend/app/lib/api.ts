import type { Device, PaginatedDevices, Price, PriceTrendPoint } from '../types';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, { next: { revalidate: 300 } });
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
  return apiFetch<PaginatedDevices>(`/devices?${q.toString()}`);
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
