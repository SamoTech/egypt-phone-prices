import type { Device, PaginatedDevices, Price, PriceTrendPoint } from '../types';

// Server-side: use absolute backend URL (same deployment).
// Client-side: relative /api works fine.
function getBase(): string {
  // VERCEL_URL is set automatically by Vercel for every deployment.
  // NEXT_PUBLIC_API_URL can override (e.g. point to Railway backend).
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, '');
  }
  if (typeof window === 'undefined') {
    // Server-side rendering — need absolute URL
    const host = process.env.VERCEL_URL
      ? `https://${process.env.VERCEL_URL}`
      : 'http://localhost:3000';
    return `${host}/api`;
  }
  // Client-side — relative URL works
  return '/api';
}

const BYPASS = process.env.VERCEL_AUTOMATION_BYPASS_SECRET ?? '';

async function apiFetch<T>(path: string, opts?: RequestInit): Promise<T> {
  const base = getBase();
  const url = `${base}${path}`;

  const headers: HeadersInit = {
    ...(opts?.headers ?? {}),
    // Bypass Vercel deployment protection for internal server-side calls
    ...(BYPASS ? { 'x-vercel-protection-bypass': BYPASS } : {}),
  };

  const res = await fetch(url, {
    ...opts,
    headers,
    next: { revalidate: 300 },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`API ${res.status} on ${path}: ${text.slice(0, 200)}`);
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
