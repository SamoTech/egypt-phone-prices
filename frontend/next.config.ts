import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'fdn2.gsmarena.com' },
      { protocol: 'https', hostname: '*.gsmarena.com' },
    ],
  },
  // /api/* is handled by app/api/[[...path]]/route.ts which proxies to BACKEND_URL
  // No rewrites needed — the catch-all route handles everything
};

export default nextConfig;
