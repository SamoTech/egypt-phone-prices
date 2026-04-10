/**
 * Catch-all API proxy: forwards every /api/* request to the FastAPI backend.
 * Set BACKEND_URL env var on Vercel to your Railway/Render backend URL.
 * e.g. https://egypt-phone-prices-api.railway.app
 */
import { NextRequest, NextResponse } from 'next/server';

const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8000';

async function proxy(req: NextRequest, path: string): Promise<NextResponse> {
  const url = new URL(req.url);
  const target = `${BACKEND}/${path}${url.search}`;

  const headers = new Headers(req.headers);
  headers.delete('host');

  try {
    const res = await fetch(target, {
      method: req.method,
      headers,
      body: ['GET', 'HEAD'].includes(req.method) ? undefined : req.body,
      // @ts-expect-error — Node fetch duplex
      duplex: 'half',
    });

    const body = await res.arrayBuffer();
    return new NextResponse(body, {
      status: res.status,
      headers: {
        'content-type': res.headers.get('content-type') ?? 'application/json',
        'cache-control': res.headers.get('cache-control') ?? 'no-store',
        'access-control-allow-origin': '*',
      },
    });
  } catch (err) {
    console.error('[proxy] backend unreachable:', err);
    return NextResponse.json(
      { error: 'Backend unavailable', detail: String(err) },
      { status: 502 }
    );
  }
}

export async function GET(req: NextRequest, { params }: { params: Promise<{ path?: string[] }> }) {
  const { path = [] } = await params;
  return proxy(req, path.join('/'));
}
export async function POST(req: NextRequest, { params }: { params: Promise<{ path?: string[] }> }) {
  const { path = [] } = await params;
  return proxy(req, path.join('/'));
}
export async function PUT(req: NextRequest, { params }: { params: Promise<{ path?: string[] }> }) {
  const { path = [] } = await params;
  return proxy(req, path.join('/'));
}
export async function DELETE(req: NextRequest, { params }: { params: Promise<{ path?: string[] }> }) {
  const { path = [] } = await params;
  return proxy(req, path.join('/'));
}
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: {
      'access-control-allow-origin': '*',
      'access-control-allow-methods': 'GET,POST,PUT,DELETE,OPTIONS',
      'access-control-allow-headers': 'content-type,x-admin-token,authorization',
    },
  });
}
