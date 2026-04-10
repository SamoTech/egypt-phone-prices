import type { NextRequest } from 'next/server';

// Vercel automatically sends CRON_SECRET as Bearer token.
// This prevents anyone else from triggering the scrape.
export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const auth = request.headers.get('authorization');
  if (auth !== `Bearer ${process.env.CRON_SECRET}`) {
    return new Response('Unauthorized', { status: 401 });
  }

  const backendUrl =
    process.env.NEXT_PUBLIC_API_URL ??
    process.env.BACKEND_INTERNAL_URL ??
    'http://localhost:8000';

  try {
    const res = await fetch(`${backendUrl}/admin/trigger-scrape`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${process.env.ADMIN_TOKEN}`,
        'Content-Type': 'application/json',
      },
    });

    if (!res.ok) {
      const body = await res.text();
      console.error('[cron/scrape] Backend error:', res.status, body);
      return Response.json({ error: body }, { status: 502 });
    }

    const data = await res.json();
    return Response.json({ ok: true, ...data });
  } catch (err) {
    console.error('[cron/scrape] Fetch failed:', err);
    return Response.json({ error: String(err) }, { status: 500 });
  }
}
