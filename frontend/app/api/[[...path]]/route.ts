import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL?.replace(/\/$/, '');
const SUPABASE_URL = (process.env.NEXT_PUBLIC_SUPABASE_URL ?? '').replace(/\/$/, '');
const SUPABASE_KEY =
  process.env.SUPABASE_SERVICE_ROLE_KEY ??
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ??
  '';

// ---------------------------------------------------------------------------
// Supabase REST helper
// ---------------------------------------------------------------------------
async function sb<T = any>(table: string, qs = ''): Promise<T[]> {
  const url = `${SUPABASE_URL}/rest/v1/${table}${qs ? '?' + qs : ''}`;
  const res = await fetch(url, {
    headers: {
      apikey: SUPABASE_KEY,
      Authorization: `Bearer ${SUPABASE_KEY}`,
      Accept: 'application/json',
    },
    // @ts-ignore
    next: { revalidate: 60 },
  });
  if (!res.ok) {
    const msg = await res.text().catch(() => '');
    throw new Error(`Supabase ${res.status} on ${table}: ${msg.slice(0, 200)}`);
  }
  const json = await res.json();
  return Array.isArray(json) ? json : [];
}

// ---------------------------------------------------------------------------
// Main handler
// ---------------------------------------------------------------------------
async function handler(req: NextRequest): Promise<NextResponse> {
  const { pathname, search } = new URL(req.url);
  const apiPath = pathname.replace(/^\/api/, '') || '/';
  const qs = new URLSearchParams(search);

  // Proxy mode — forward to external FastAPI when BACKEND_URL is set
  if (BACKEND_URL) {
    const target = `${BACKEND_URL}${apiPath}${search}`;
    try {
      const up = await fetch(target, {
        method: req.method,
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: req.method !== 'GET' && req.method !== 'HEAD' ? await req.text() : undefined,
      });
      return NextResponse.json(await up.json(), { status: up.status });
    } catch (err: any) {
      return NextResponse.json({ error: 'Backend unavailable', detail: err.message }, { status: 502 });
    }
  }

  // Embedded Supabase mode
  try {
    return await route(apiPath, qs, req);
  } catch (err: any) {
    console.error('[api]', apiPath, err.message);
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

// ---------------------------------------------------------------------------
// Route handlers (Supabase direct)
// ---------------------------------------------------------------------------
async function route(path: string, qs: URLSearchParams, req: NextRequest): Promise<NextResponse> {

  // GET /devices
  if (path === '/devices') {
    const brand   = qs.get('brand')  ?? '';
    const search  = qs.get('search') ?? '';
    const year    = qs.get('year')   ?? '';
    const page    = Math.max(1, parseInt(qs.get('page')     ?? '1'));
    const perPage = Math.min(100, parseInt(qs.get('per_page') ?? '24'));
    const offset  = (page - 1) * perPage;

    // Build PostgREST query params
    const p = new URLSearchParams();
    p.set('select', 'id,name,slug,image_url,display,chipset,ram,storage,camera,battery,os,release_year,brand:brands(id,name,slug,logo_url)');
    p.set('order',  'name.asc');
    p.set('offset', String(offset));
    p.set('limit',  String(perPage));
    if (search) p.set('name', `ilike.*${search}*`);
    if (year)   p.set('release_year', `eq.${year}`);

    // For brand filter we need a join filter — fetch brand id first
    let brandId: string | null = null;
    if (brand) {
      const brands = await sb('brands', new URLSearchParams({ 'slug': `eq.${brand}`, select: 'id' }).toString());
      brandId = brands[0]?.id ?? null;
      if (brandId) p.set('brand_id', `eq.${brandId}`);
    }

    const [items, all] = await Promise.all([
      sb('devices', p.toString()),
      // count total (cheap: id only, same filters except offset/limit)
      (() => {
        const cp = new URLSearchParams(p);
        cp.set('select', 'id');
        cp.delete('offset');
        cp.delete('limit');
        return sb('devices', cp.toString());
      })(),
    ]);

    return NextResponse.json({ total: all.length, page, per_page: perPage, items });
  }

  // GET /devices/:slug
  const deviceSlug = path.match(/^\/devices\/([-\w]+)$/);
  if (deviceSlug) {
    const rows = await sb('devices',
      new URLSearchParams({
        'slug': `eq.${deviceSlug[1]}`,
        select: 'id,name,slug,image_url,display,chipset,ram,storage,camera,battery,os,release_year,brand:brands(id,name,slug,logo_url)',
        limit: '1',
      }).toString()
    );
    if (!rows.length) return NextResponse.json({ error: 'Not found' }, { status: 404 });
    return NextResponse.json(rows[0]);
  }

  // GET /prices?device_id=
  if (path === '/prices') {
    const deviceId = qs.get('device_id');
    if (!deviceId) return NextResponse.json({ error: 'device_id required' }, { status: 400 });
    const rows = await sb('prices', new URLSearchParams({
      'device_id': `eq.${deviceId}`,
      select: 'id,device_id,price_egp,original_price_egp,product_url,in_stock,scraped_at,retailer:retailers(id,name,slug,base_url,logo_url)',
      order: 'scraped_at.desc',
      limit: '100',
    }).toString());
    // One row per retailer — latest scrape only
    const seen = new Set<string>();
    const deduped = rows.filter((r) => {
      const key = String(r.retailer?.id ?? r.retailer_id);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
    return NextResponse.json(deduped);
  }

  // GET /trends?device_id=&days=90
  if (path === '/trends') {
    const deviceId = qs.get('device_id');
    if (!deviceId) return NextResponse.json({ error: 'device_id required' }, { status: 400 });
    const days  = Math.min(365, parseInt(qs.get('days') ?? '90'));
    const since = new Date(Date.now() - days * 86_400_000).toISOString();
    const rows  = await sb('prices', new URLSearchParams({
      'device_id':   `eq.${deviceId}`,
      'scraped_at':  `gte.${since}`,
      select: 'price_egp,scraped_at',
      order:  'scraped_at.asc',
    }).toString());
    const byDate: Record<string, number[]> = {};
    for (const r of rows) {
      const d = (r.scraped_at as string)?.slice(0, 10);
      if (!d) continue;
      (byDate[d] ??= []).push(Number(r.price_egp));
    }
    return NextResponse.json(
      Object.entries(byDate).map(([date, prices]) => ({
        date,
        min_price: Math.min(...prices),
        avg_price: prices.reduce((a, b) => a + b, 0) / prices.length,
      }))
    );
  }

  // GET /admin/stats
  if (path === '/admin/stats') {
    const [brands, devices, retailers, prices] = await Promise.all([
      sb('brands',    'select=id'),
      sb('devices',   'select=id'),
      sb('retailers', 'select=id'),
      sb('prices',    'select=id'),
    ]);
    return NextResponse.json({ brands: brands.length, devices: devices.length, retailers: retailers.length, prices: prices.length });
  }

  return NextResponse.json({ error: 'Not found' }, { status: 404 });
}

export const GET  = handler;
export const POST = handler;
