import { NextRequest, NextResponse } from 'next/server';

// The FastAPI backend URL — set BACKEND_URL in Vercel env vars
// pointing to your Railway/Render/etc. deployment.
// Falls back to the bundled Supabase-direct handler below if not set.
const BACKEND_URL = process.env.BACKEND_URL?.replace(/\/$/, '');

async function handler(req: NextRequest) {
  // Extract the path after /api/
  const { pathname, search } = new URL(req.url);
  const apiPath = pathname.replace(/^\/api/, '') || '/';

  if (BACKEND_URL) {
    // --- Proxy mode: forward to external FastAPI backend ---
    const target = `${BACKEND_URL}${apiPath}${search}`;
    try {
      const upstream = await fetch(target, {
        method: req.method,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: req.method !== 'GET' && req.method !== 'HEAD'
          ? await req.text()
          : undefined,
        // @ts-ignore — Next.js extended fetch option
        next: { revalidate: 60 },
      });
      const data = await upstream.json();
      return NextResponse.json(data, { status: upstream.status });
    } catch (err: any) {
      return NextResponse.json(
        { error: 'Backend unavailable', detail: err.message },
        { status: 502 }
      );
    }
  }

  // --- Embedded mode: query Supabase directly (no external backend needed) ---
  return handleSupabase(apiPath, search, req);
}

// ---------------------------------------------------------------------------
// Supabase direct handler — used when BACKEND_URL is not set
// ---------------------------------------------------------------------------
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL ?? '';
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY
  ?? process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  ?? '';

function sb(table: string, params: string = '') {
  return fetch(
    `${SUPABASE_URL}/rest/v1/${table}${params}`,
    { headers: { apikey: SUPABASE_KEY, Authorization: `Bearer ${SUPABASE_KEY}`, Accept: 'application/json' }, next: { revalidate: 60 } }
  ).then(r => r.json());
}

async function handleSupabase(path: string, search: string, req: NextRequest): Promise<NextResponse> {
  const qs = new URLSearchParams(search);

  // ── GET /devices ──────────────────────────────────────────────────────────
  if (path === '/devices' && req.method === 'GET') {
    const brand    = qs.get('brand');
    const query    = qs.get('search');
    const year     = qs.get('year');
    const page     = parseInt(qs.get('page') ?? '1');
    const perPage  = parseInt(qs.get('per_page') ?? '24');
    const from     = (page - 1) * perPage;
    const to       = from + perPage - 1;

    let filter = 'select=id,name,slug,image_url,display,chipset,ram,storage,camera,battery,os,release_year,brand:brands(id,name,slug,logo_url)';
    if (brand) filter += `&brands.slug=eq.${brand}`;
    if (query) filter += `&name=ilike.*${query}*`;
    if (year)  filter += `&release_year=eq.${year}`;
    filter += `&order=name.asc&offset=${from}&limit=${perPage}`;

    const [items, countRows] = await Promise.all([
      sb('devices', `?${filter}`),
      sb('devices', '?select=id'),
    ]);

    return NextResponse.json({ total: countRows.length, page, per_page: perPage, items: items ?? [] });
  }

  // ── GET /devices/:slug ────────────────────────────────────────────────────
  const deviceMatch = path.match(/^\/devices\/([\w-]+)$/);
  if (deviceMatch && req.method === 'GET') {
    const slug = deviceMatch[1];
    const rows = await sb('devices',
      `?slug=eq.${slug}&select=id,name,slug,image_url,display,chipset,ram,storage,camera,battery,os,release_year,brand:brands(id,name,slug,logo_url)&limit=1`
    );
    if (!rows?.length) return NextResponse.json({ error: 'Not found' }, { status: 404 });
    return NextResponse.json(rows[0]);
  }

  // ── GET /prices?device_id= ────────────────────────────────────────────────
  if (path === '/prices' && req.method === 'GET') {
    const deviceId = qs.get('device_id');
    if (!deviceId) return NextResponse.json({ error: 'device_id required' }, { status: 400 });
    const latest = qs.get('latest') !== 'false';
    let filter = `?device_id=eq.${deviceId}&select=id,device_id,price_egp,original_price_egp,product_url,in_stock,scraped_at,retailer:retailers(id,name,slug,base_url,logo_url)&order=scraped_at.desc`;
    if (latest) filter += '&limit=20';
    const rows = await sb('prices', filter);
    // Deduplicate: one row per retailer (latest scrape)
    const seen = new Set<string>();
    const deduped = (rows ?? []).filter((r: any) => {
      const key = r.retailer?.id;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
    return NextResponse.json(deduped);
  }

  // ── GET /trends?device_id= ────────────────────────────────────────────────
  if (path === '/trends' && req.method === 'GET') {
    const deviceId = qs.get('device_id');
    const days = parseInt(qs.get('days') ?? '90');
    if (!deviceId) return NextResponse.json({ error: 'device_id required' }, { status: 400 });
    const since = new Date(Date.now() - days * 86400_000).toISOString();
    const rows = await sb('prices',
      `?device_id=eq.${deviceId}&scraped_at=gte.${since}&select=price_egp,scraped_at&order=scraped_at.asc`
    );
    // Group by date, take min price
    const byDate: Record<string, number[]> = {};
    for (const r of rows ?? []) {
      const d = r.scraped_at?.slice(0, 10);
      if (!d) continue;
      byDate[d] = byDate[d] ?? [];
      byDate[d].push(r.price_egp);
    }
    const trend = Object.entries(byDate).map(([date, prices]) => ({
      date,
      min_price: Math.min(...prices),
      avg_price: prices.reduce((a: number, b: number) => a + b, 0) / prices.length,
    }));
    return NextResponse.json(trend);
  }

  // ── GET /admin/stats ──────────────────────────────────────────────────────
  if (path === '/admin/stats' && req.method === 'GET') {
    const [brands, devices, retailers, prices] = await Promise.all([
      sb('brands', '?select=id'),
      sb('devices', '?select=id'),
      sb('retailers', '?select=id'),
      sb('prices', '?select=id'),
    ]);
    return NextResponse.json({
      brands: brands?.length ?? 0,
      devices: devices?.length ?? 0,
      retailers: retailers?.length ?? 0,
      prices: prices?.length ?? 0,
      scrape_logs: 0,
    });
  }

  return NextResponse.json({ error: 'Not found' }, { status: 404 });
}

export const GET  = handler;
export const POST = handler;
