import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: `${process.env.MESA_LAW_BACKEND_URL || 'http://legal-api:8001'}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
