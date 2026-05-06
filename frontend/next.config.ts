import type { NextConfig } from "next";

// Build-time validation: Ensure BACKEND_INTERNAL_URL is set
if (!process.env.BACKEND_INTERNAL_URL) {
  throw new Error(
    "BACKEND_INTERNAL_URL is required but not set. " +
    "Please set this environment variable before building."
  );
}

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
          destination: `${process.env.BACKEND_INTERNAL_URL}/api/v1/:path*`,
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

  // CRITICAL FIX C2: Removed env block with BACKEND_INTERNAL_URL
  // The env block exposes variables to the browser bundle.
  // BACKEND_INTERNAL_URL must remain server-only.
  // It is safely accessed via process.env.BACKEND_INTERNAL_URL in:
  // - rewrites() function above (server-side)
  // - API route handlers (server-side)
  // Never expose internal URLs to browser.

  // TypeScript configuration
  typescript: {
    // Dangerously allow production builds to successfully complete even if
    // your project has type errors (we'll catch these in CI)
    ignoreBuildErrors: false,
  },

};

export default nextConfig;
