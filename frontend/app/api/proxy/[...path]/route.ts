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

// Allowed API path prefixes (whitelist)
const ALLOWED_PREFIXES = [
  '/auth/',
  '/users/',
  '/dogs/',
  '/breeding/',
  '/sales/',
  '/compliance/',
  '/customers/',
  '/finance/',
  '/operations/',
  '/health/',
  '/ready/',
];

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
 */
function isAllowedPath(path: string): boolean {
  // Allow health checks
  if (path === '/health/' || path === '/ready/') {
    return true;
  }

  // Check against allowed prefixes
  return ALLOWED_PREFIXES.some(prefix => path.startsWith(prefix));
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

  // Validate path
  if (!isAllowedPath(path)) {
    return NextResponse.json(
      { error: 'Forbidden', message: 'Path not allowed' },
      { status: 403 }
    );
  }

  // Build backend URL
  const backendUrl = `${BACKEND_URL}/api/v1${path}${searchParams}`;

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
// CORS Preflight
// =============================================================================

export async function OPTIONS(_request: NextRequest) {
  return new NextResponse(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-CSRFToken, X-Idempotency-Key',
      'Access-Control-Allow-Credentials': 'true',
    },
  });
}

// =============================================================================
// Config
// =============================================================================

export const config = {
  runtime: 'edge',
};
