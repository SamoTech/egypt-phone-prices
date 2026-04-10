/**
 * GET /api/admin/fix-urls
 * One-time fix: update all price rows whose product_url is missing,
 * relative, or points back to our own domain. Replaces them with
 * the retailer search URL for the device name.
 */
import { NextRequest, NextResponse } from 'next/server';

const SUPABASE_URL = (process.env.NEXT_PUBLIC_SUPABASE_URL ?? '').replace(/\/$/, '');
const SUPABASE_KEY =
  process.env.SUPABASE_SERVICE_ROLE_KEY ??
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? '';

const SEARCH_TEMPLATES: Record<string, string> = {
  jumia:   'https://www.jumia.com.eg/catalog/?q=',
  noon:    'https://www.noon.com/egypt-en/search/?q=',
  amazon:  'https://www.amazon.eg/s?k=',
  btech:   'https://btech.com/en/catalogsearch/result/?q=',
  raneen:  'https://www.raneen.com/en/search?q=',
  elaraby: 'https://www.elarabygroup.com/search?q=',
};

function searchUrl(retailerSlug: string, deviceName: string): string {
  for (const [key, base] of Object.entries(SEARCH_TEMPLATES)) {
    if (retailerSlug.includes(key)) return base + encodeURIComponent(deviceName);
  }
  return '';
}

async function sbGet(table: string, qs: string) {
  const r = await fetch(`${SUPABASE_URL}/rest/v1/${table}?${qs}`, {
    headers: { apikey: SUPABASE_KEY, Authorization: `Bearer ${SUPABASE_KEY}`, Accept: 'application/json' },
  });
  return r.json();
}

async function sbPatch(table: string, qs: string, body: object) {
  const r = await fetch(`${SUPABASE_URL}/rest/v1/${table}?${qs}`, {
    method: 'PATCH',
    headers: {
      apikey: SUPABASE_KEY,
      Authorization: `Bearer ${SUPABASE_KEY}`,
      'Content-Type': 'application/json',
      Prefer: 'return=minimal',
    },
    body: JSON.stringify(body),
  });
  return r.ok;
}

export async function GET(_req: NextRequest) {
  // Fetch all prices with their retailer slug and device name
  const prices: any[] = await sbGet('prices',
    'select=id,product_url,device_id,retailer:retailers(slug),device:devices(name)'
  );

  let fixed = 0;
  const errors: string[] = [];

  for (const p of prices ?? []) {
    const url = p.product_url ?? '';
    const isBad =
      !url ||
      url.startsWith('/') ||
      url.includes('vercel.app') ||
      url.includes('egypt-phone-prices');

    if (!isBad) continue;

    const slug       = p.retailer?.slug ?? '';
    const deviceName = p.device?.name   ?? '';
    const newUrl     = searchUrl(slug, deviceName);
    if (!newUrl) continue;

    const ok = await sbPatch('prices', `id=eq.${p.id}`, { product_url: newUrl });
    if (ok) fixed++;
    else errors.push(p.id);
  }

  return NextResponse.json({ total: prices?.length ?? 0, fixed, errors });
}
