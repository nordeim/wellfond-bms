import type { NextConfig } from "next";

/**
 * Wellfond BMS - Next.js Configuration
 * =====================================
 * BFF Security Pattern: Backend-for-Frontend proxy to Django API
 * Cookie-based sessions (HttpOnly, Secure in production)
 */
const nextConfig: NextConfig = {
  // Standalone output for Docker deployment
  output: "standalone",

  // React strict mode for development safety
  reactStrictMode: true,

  // Turbopack for faster development (Next.js 15+)
  // turbo config handled automatically in dev mode

  // Image optimization configuration
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "*.r2.cloudflarestorage.com",
        pathname: "/wellfond/**",
      },
      {
        protocol: "https",
        hostname: "wellfond-public.s3.ap-southeast-1.amazonaws.com",
      },
    ],
    formats: ["image/webp", "image/avif"],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },

  // Security headers
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "X-Frame-Options",
            value: "DENY",
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=(self)",
          },
        ],
      },
    ];
  },

  // BFF Proxy: Routes /api/proxy/* to Django backend
  async rewrites() {
    return {
      beforeFiles: [
        // Proxy API requests to Django backend
        {
          source: "/api/proxy/:path*",
          destination: `${process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000"}/api/v1/:path*`,
        },
      ],
    };
  },

  // Redirects for clean URLs
  async redirects() {
    return [
      {
        source: "/",
        destination: "/dashboard",
        permanent: false,
      },
    ];
  },

  // Environment variables exposed to browser (prefix with NEXT_PUBLIC_)
  env: {
    BACKEND_INTERNAL_URL: process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000",
  },

  // TypeScript configuration
  typescript: {
    // Dangerously allow production builds to successfully complete even if
    // your project has type errors (we'll catch these in CI)
    ignoreBuildErrors: false,
  },

};

export default nextConfig;
