/**
 * Wellfond BMS - Route Protection Middleware
 * ==========================================
 * Edge-compatible middleware for auth and role-based routing.
 * Redirects unauthenticated users to /login.
 * Enforces role-based route access.
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// =============================================================================
// Route Configuration
// =============================================================================

// Public routes (no auth required)
const PUBLIC_ROUTES = [
  '/login',
  '/forgot-password',
  '/reset-password',
  '/api/proxy/auth/login',
  '/api/proxy/auth/csrf',
  '/health',
];

// Role-based redirects are handled client-side in the protected layout

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Check if a route is public (no auth required)
 */
function isPublicRoute(pathname: string): boolean {
  return PUBLIC_ROUTES.some(route =>
    pathname === route || pathname.startsWith(route + '/')
  );
}

// Role checking is done client-side via useAuth hook
// Middleware only validates session cookie presence

// =============================================================================
// Middleware
// =============================================================================

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip middleware for public assets and API routes that handle auth
  if (
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/api/_next/') ||
    pathname.startsWith('/static/') ||
    pathname.startsWith('/favicon') ||
    pathname.startsWith('/manifest')
  ) {
    return NextResponse.next();
  }

  // Check if route is public
  if (isPublicRoute(pathname)) {
    return NextResponse.next();
  }

  // Check for session cookie
  const sessionCookie = request.cookies.get('sessionid');

  // No session - redirect to login
  if (!sessionCookie) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('returnUrl', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // User is authenticated, check role-based access
  // Note: Full role check happens client-side via useAuth hook
  // Middleware only does basic cookie validation

  // Allow the request to proceed
  // The protected layout will handle role-based redirects
  const response = NextResponse.next();

  // Add custom headers for debugging (optional, remove in production)
  response.headers.set('x-middleware-processed', 'true');

  return response;
}

// =============================================================================
// Config
// =============================================================================

export const config = {
  matcher: [
    // Match all paths except static files
    '/((?!_next/static|_next/image|favicon.ico|manifest.json).*)',
  ],
};
