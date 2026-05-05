/**
 * Wellfond BMS - BFF Proxy Route Handler
 * ======================================
 * Backend-for-Frontend proxy that forwards requests to Django API.
 * - Strips dangerous headers
 * - Sets X-Forwarded-Proto
 * - Validates allowed paths
 * - Streams responses
 */

import { NextRequest, NextResponse } from 'next/server';

// =============================================================================
// Configuration
// =============================================================================

// Backend URL (internal, not exposed to browser)
const BACKEND_URL = process.env.BACKEND_INTERNAL_URL || 'http://127.0.0.1:8000';

// Headers to strip (security)
const STRIP_HEADERS = [
  'host',
  'x-forwarded-for',
  'x-forwarded-host',
  'x-forwarded-proto',
  'x-forwarded-port',
  'x-forwarded-server',
];

// =============================================================================
// Helper Functions
// =============================================================================

/**
* Validate if path is allowed
*
* Security fix for Critical Issue C1: Path Traversal Vulnerability
* - Normalizes path before validation
* - Rejects paths with traversal attempts (..)
* - Uses strict regex matching anchored at start
* - Rejects null byte injection attempts
*/
export function isAllowedPath(path: string): boolean {
  // Normalize path: remove duplicate slashes, remove trailing slash
  const normalized = path.replace(/\/+/g, '/').replace(/\/$/, '') || '/';

  // Reject paths with traversal attempts
  if (normalized.includes('..')) {
    return false;
  }

  // Reject null byte injection attempts
  if (normalized.includes('\0')) {
    return false;
  }

  // Allow health checks (exact match or with trailing slash)
  if (normalized === '/health' || normalized === '/ready') {
    return true;
  }

  // Strict regex matching for API paths
  // Matches: /auth, /users, /dogs, /breeding, /sales, /compliance,
  //          /customers, /finance, /operations
  // Followed by optional path segments (sub-paths)
  const allowedPattern = /^\/(auth|users|dogs|breeding|sales|compliance|customers|finance|operations|stream|alerts)(\/.*|$)/;
  return allowedPattern.test(normalized);
}

/**
 * Strip dangerous headers
 */
function stripHeaders(headers: Headers): Headers {
  const newHeaders = new Headers(headers);
  STRIP_HEADERS.forEach(header => {
    newHeaders.delete(header);
  });
  return newHeaders;
}

/**
 * Forward request to backend
 */
async function proxyRequest(
  request: NextRequest,
  method: string
): Promise<NextResponse> {
  const path = request.nextUrl.pathname.replace('/api/proxy', '');
  const searchParams = request.nextUrl.search;

  // Defensive guard: strip /api/v1 from path if it's already there
  // to avoid double prefixing when buildUrl includes it for server-side calls
  const cleanPath = path.startsWith('/api/v1') ? path.replace('/api/v1', '') : path;

  // Validate path
  if (!isAllowedPath(cleanPath)) {
    return NextResponse.json(
      { error: 'Forbidden', message: 'Path not allowed' },
      { status: 403 }
    );
  }

  // Build backend URL
  const backendUrl = `${BACKEND_URL}/api/v1${cleanPath}${searchParams}`;

  // Strip headers and set new ones
  const headers = stripHeaders(request.headers);
  headers.set('X-Forwarded-Proto', 'https');

  // Forward cookies
  const cookie = request.headers.get('cookie');
  if (cookie) {
    headers.set('Cookie', cookie);
  }

  // Get request body
  let body: BodyInit | null = null;
  if (['POST', 'PUT', 'PATCH'].includes(method)) {
    try {
      body = await request.text();
    } catch {
      // No body
    }
  }

  try {
    // Forward to backend
    const response = await fetch(backendUrl, {
      method,
      headers,
      body,
      // Important: Don't follow redirects, pass them through
      redirect: 'manual',
    });

    // Build response
    const responseHeaders = new Headers(response.headers);

    // Copy Set-Cookie headers from backend
    response.headers.forEach((value, key) => {
      if (key.toLowerCase() === 'set-cookie') {
        responseHeaders.append('Set-Cookie', value);
      }
    });

    // Add CORS headers to actual response (not just preflight)
    const corsHeaders = getCorsHeaders(request);
    Object.entries(corsHeaders).forEach(([key, value]) => {
      responseHeaders.set(key, value);
    });

    // Create response with streaming body
    const responseBody = response.body
      ? new ReadableStream({
          start(controller) {
            const reader = response.body!.getReader();
            const pump = (): Promise<void> => {
              return reader.read().then(({ done, value }) => {
                if (done) {
                  controller.close();
                  return Promise.resolve();
                }
                controller.enqueue(value);
                return pump();
              });
            };
            void pump();
          },
        })
      : null;

    return new NextResponse(responseBody, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    console.error('Proxy error:', error);
    return NextResponse.json(
      { error: 'Service Unavailable', message: 'Backend unavailable' },
      { status: 503 }
    );
  }
}

// =============================================================================
// Route Handlers
// =============================================================================

export async function GET(request: NextRequest) {
  return proxyRequest(request, 'GET');
}

export async function POST(request: NextRequest) {
  return proxyRequest(request, 'POST');
}

export async function PUT(request: NextRequest) {
  return proxyRequest(request, 'PUT');
}

export async function PATCH(request: NextRequest) {
  return proxyRequest(request, 'PATCH');
}

export async function DELETE(request: NextRequest) {
  return proxyRequest(request, 'DELETE');
}

// =============================================================================
// CORS Configuration
// =============================================================================

const ALLOWED_ORIGINS = [
  'https://wellfond.sg',
  'https://www.wellfond.sg',
  'http://localhost:3000',
];

function getCorsHeaders(request: NextRequest): Record<string, string> {
  const origin = request.headers.get('origin') || '';
  const isAllowed =
    ALLOWED_ORIGINS.includes(origin) ||
    (process.env.NODE_ENV === 'development' &&
     origin.startsWith('http://localhost'));
  return {
    'Access-Control-Allow-Origin': isAllowed ? origin : ALLOWED_ORIGINS[0],
    'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-CSRFToken, X-Idempotency-Key',
    'Access-Control-Allow-Credentials': 'true',
    'Access-Control-Max-Age': '86400',
  };
}

// =============================================================================
// CORS Preflight
// =============================================================================

export async function OPTIONS(request: NextRequest) {
  return new NextResponse(null, {
    status: 204,
    headers: getCorsHeaders(request),
  });
}

// CRITICAL FIX C1: Removed Edge Runtime export
// Edge Runtime cannot read process.env at request time.
// Default Node.js runtime allows server-side process.env access.
// export const runtime = 'edge';  // REMOVED - causes BACKEND_INTERNAL_URL to be undefined
