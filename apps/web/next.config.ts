import type { NextConfig } from "next";
import createNextIntlPlugin from 'next-intl/plugin';

const withNextIntl = createNextIntlPlugin('./src/i18n.ts');

const nextConfig: NextConfig = {
  output: process.env.MESA_LAW_STANDALONE === '1' ? 'standalone' : undefined,
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: `${process.env.MESA_LAW_BACKEND_URL || 'http://legal-api:8001'}/api/v1/:path*`,
      },
    ];
  },
};

export default withNextIntl(nextConfig);
