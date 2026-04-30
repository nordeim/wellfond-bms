/**
 * Wellfond BMS - Authentication Utilities
 * ========================================
 * Client-side session helpers for Phase 1.
 * Note: Actual auth is HttpOnly cookie-based (server-side).
 */

import type { User } from './types';

// =============================================================================
// Session Storage (Memory only - cookies are HttpOnly)
// =============================================================================

// In-memory session cache (not localStorage for security)
let cachedUser: User | null = null;
let cachedCsrfToken: string | null = null;

// =============================================================================
// User Session
// =============================================================================

/**
 * Get current user from memory cache.
 * Note: This is set after successful login/refresh.
 * The actual session is stored in HttpOnly cookie (server-side).
 */
export function getSession(): User | null {
  if (typeof window === 'undefined') {
    return null; // Server-side
  }
  return cachedUser;
}

/**
 * Set user in session cache.
 * Called after login/refresh.
 */
export function setSession(user: User | null): void {
  cachedUser = user;
}

/**
 * Clear session cache.
 * Called after logout.
 */
export function clearSession(): void {
  cachedUser = null;
  cachedCsrfToken = null;
}

// =============================================================================
// CSRF Token
// =============================================================================

/**
 * Get CSRF token from memory cache.
 * Note: CSRF token is also available from cookie (django-csrf).
 */
export function getCsrfToken(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }
  return cachedCsrfToken;
}

/**
 * Set CSRF token in cache.
 */
export function setCsrfToken(token: string | null): void {
  cachedCsrfToken = token;
}

// =============================================================================
// Authentication State
// =============================================================================

/**
 * Check if user is authenticated.
 * Checks memory cache first, then falls back to cookie check.
 */
export function isAuthenticated(): boolean {
  if (typeof window === 'undefined') {
    return false;
  }

  // Check memory cache
  if (cachedUser) {
    return true;
  }

  // Check for session cookie
  return document.cookie.includes('sessionid=');
}

/**
 * Get current user role.
 */
export function getRole(): string | null {
  return getSession()?.role ?? null;
}

/**
 * Check if user has specific role(s).
 */
export function hasRole(...roles: string[]): boolean {
  const userRole = getRole();
  if (!userRole) return false;
  return roles.includes(userRole);
}

/**
 * Check if user is management or admin.
 */
export function isAdmin(): boolean {
  return hasRole('management', 'admin');
}

// =============================================================================
// Server-Side Detection
// =============================================================================

/**
 * Check if running on server.
 */
export function isServer(): boolean {
  return typeof window === 'undefined';
}

/**
 * Check if running on client.
 */
export function isClient(): boolean {
  return typeof window !== 'undefined';
}

// =============================================================================
// Role-Based Access
// =============================================================================

import { ROLE_HIERARCHY } from './constants';

/**
 * Check if current user has role >= required role.
 */
export function hasRoleLevel(requiredRole: string): boolean {
  const userRole = getRole();
  if (!userRole) return false;

  const userLevel = ROLE_HIERARCHY[userRole] ?? 0;
  const requiredLevel = ROLE_HIERARCHY[requiredRole] ?? 999;

  return userLevel >= requiredLevel;
}

/**
 * Check if user can access specific entity.
 * Management can access all entities.
 */
export function canAccessEntity(entityId: string): boolean {
  const user = getSession();
  if (!user) return false;

  // Management sees all
  if (user.role === 'management') {
    return true;
  }

  // Others see only their entity
  return user.entityId === entityId;
}

// =============================================================================
// Route Guards
// =============================================================================

/**
 * Role-based route access map.
 */
const ROUTE_ACCESS: Record<string, string[]> = {
  '/dashboard': ['management', 'admin', 'sales'],
  '/dogs': ['management', 'admin', 'sales', 'ground', 'vet'],
  '/ground': ['management', 'admin', 'ground'],
  '/breeding': ['management', 'admin'],
  '/sales': ['management', 'admin', 'sales'],
  '/compliance': ['management', 'admin'],
  '/customers': ['management', 'admin', 'sales'],
  '/finance': ['management', 'admin'],
  '/users': ['management', 'admin'],
};

/**
 * Check if current user can access a route.
 */
export function canAccessRoute(path: string): boolean {
  const userRole = getRole();
  if (!userRole) return false;

  // Management can access everything
  if (userRole === 'management') {
    return true;
  }

  // Find matching route pattern
  for (const [route, allowedRoles] of Object.entries(ROUTE_ACCESS)) {
    if (path.startsWith(route)) {
      return allowedRoles.includes(userRole);
    }
  }

  // Allow by default for unmatched routes
  return true;
}

/**
 * Get redirect path based on role.
 */
export function getRoleRedirect(role: string): string {
  const redirects: Record<string, string> = {
    management: '/dashboard',
    admin: '/dashboard',
    sales: '/dashboard',
    ground: '/ground',
    vet: '/dogs',
  };
  return redirects[role] ?? '/login';
}

// =============================================================================
// Auth Actions
// =============================================================================

/**
 * Redirect to login page.
 * Call this when auth is required but user is not authenticated.
 */
export function requireAuth(redirectUrl?: string): never {
  if (typeof window !== 'undefined') {
    const returnUrl = redirectUrl ?? window.location.pathname;
    window.location.href = `/login?returnUrl=${encodeURIComponent(returnUrl)}`;
  }
  throw new Error('Authentication required');
}

/**
 * Handle logout.
 * Clears session and redirects to login.
 */
export async function logout(): Promise<void> {
  clearSession();

  // Call logout endpoint
  try {
    await fetch('/api/proxy/auth/logout', {
      method: 'POST',
      credentials: 'include',
    });
  } catch {
    // Ignore errors
  }

  // Redirect to login
  if (typeof window !== 'undefined') {
    window.location.href = '/login';
  }
}

// =============================================================================
// Storage Detection (Security Check)
// =============================================================================

/**
 * Check if localStorage/sessionStorage contains tokens (should be empty).
 * This is for security auditing - tokens should be HttpOnly cookies.
 */
export function checkTokenLeakage(): { hasLeakage: boolean; keys: string[] } {
  if (typeof window === 'undefined') {
    return { hasLeakage: false, keys: [] };
  }

  const suspiciousKeys: string[] = [];
  const patterns = ['token', 'auth', 'session', 'csrf', 'jwt', 'api'];

  // Check localStorage
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && patterns.some(p => key.toLowerCase().includes(p))) {
      suspiciousKeys.push(`localStorage.${key}`);
    }
  }

  // Check sessionStorage
  for (let i = 0; i < sessionStorage.length; i++) {
    const key = sessionStorage.key(i);
    if (key && patterns.some(p => key.toLowerCase().includes(p))) {
      suspiciousKeys.push(`sessionStorage.${key}`);
    }
  }

  return {
    hasLeakage: suspiciousKeys.length > 0,
    keys: suspiciousKeys,
  };
}
