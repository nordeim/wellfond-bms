/**
 * Wellfond BMS - API Client
 * ==========================
 * Unified fetch wrapper with auth, idempotency, and error handling.
 */

import { toast } from 'sonner';

import { getCsrfToken, isAuthenticated } from './auth';
import { generateIdempotencyKey } from './utils';

// =============================================================================
// Configuration
// =============================================================================

// SECURITY FIX H2: Use BACKEND_INTERNAL_URL for server-side (not exposed to browser)
// NEXT_PUBLIC_API_URL removed - prevents internal URL leakage to browser bundle
const API_BASE_URL = process.env.BACKEND_INTERNAL_URL || 'http://127.0.0.1:8000';

// BFF proxy path (Next.js handles this)
const PROXY_PREFIX = '/api/proxy';

// SECURITY: Prevent BACKEND_INTERNAL_URL from leaking to browser bundle.
// NEXT_PUBLIC_* env vars are inlined by Next.js at build time and exposed to client JS.
if (typeof window !== 'undefined' && process.env.BACKEND_INTERNAL_URL) {
  console.error(
    '[SECURITY] BACKEND_INTERNAL_URL is exposed in the browser bundle. '
    + 'This environment variable must NOT be prefixed with NEXT_PUBLIC_.'
  );
}

// =============================================================================
// Error Handling
// =============================================================================

export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public details?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// =============================================================================
// Request Builder
// =============================================================================

interface RequestConfig extends RequestInit {
  idempotencyKey?: string;
  skipAuth?: boolean;
  params?: Record<string, string | number | boolean | undefined>;
}

/**
 * Build full URL for API request.
 * Server-side: direct to Django
 * Client-side: via BFF proxy
 */
function buildUrl(path: string): string {
  if (typeof window === 'undefined') {
    // Server-side: direct API call
    return `${API_BASE_URL}/api/v1${path}`;
  }
  // Client-side: via BFF proxy
  return `${PROXY_PREFIX}${path}`;
}

/**
 * Unified API request function.
 * Handles:
 * - CSRF token attachment
 * - Idempotency keys for POST/PUT/PATCH/DELETE
 * - Auth check
 * - Auto-refresh on 401
 * - Error toasting
 */
async function apiRequest<T>(
  path: string,
  options: RequestConfig = {},
  isRetry = false
): Promise<T> {
  const url = buildUrl(path);
  const { idempotencyKey, skipAuth, ...fetchOptions } = options;

  // Check auth (unless skipped)
  if (!skipAuth && !isAuthenticated()) {
    throw new ApiError('Authentication required', 401);
  }

  // Build headers
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((fetchOptions.headers as Record<string, string>) || {}),
  };

  // Attach CSRF token
  const csrfToken = getCsrfToken();
  if (csrfToken) {
    headers['X-CSRFToken'] = csrfToken;
  }

  // Attach idempotency key for state-changing methods
  const method = (fetchOptions.method || 'GET').toUpperCase();
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    headers['X-Idempotency-Key'] = idempotencyKey || generateIdempotencyKey();
  }

  const finalOptions: RequestInit = {
    ...fetchOptions,
    headers,
    credentials: 'include', // Important: sends cookies
  };

  // Make request
  let response: Response;
  try {
    response = await fetch(url, finalOptions);
  } catch (error) {
    toast.error('Network error. Please check your connection.');
    throw new ApiError('Network error', 0);
  }

  // Handle 401 Unauthorized - try refresh once
  if (response.status === 401 && !isRetry) {
    try {
      const refreshResponse = await fetch(buildUrl('/auth/refresh'), {
        method: 'POST',
        credentials: 'include',
      });

      if (refreshResponse.ok) {
        const data = await refreshResponse.json();
        const { setSession, setCsrfToken } = await import('./auth');
        setSession(data.user);
        // FIX CRIT-003: Use snake_case csrf_token from LoginResponse
        setCsrfToken(data.csrf_token);
        // Retry original request
        return apiRequest<T>(path, options, true);
      }
    } catch {
      // Refresh failed, fall through to logout
    }

    // Refresh failed or not retryable
    await logout();
    throw new ApiError('Session expired. Please login again.', 401);
  }

  // Handle errors
  if (!response.ok) {
    let errorData: { error?: string; message?: string } = {};
    try {
      errorData = await response.json();
    } catch {
      // Non-JSON error
    }

    const errorMessage = errorData.error || errorData.message || `HTTP ${response.status}`;

    // Show toast for client-side errors
    if (typeof window !== 'undefined') {
      toast.error(errorMessage);
    }

    throw new ApiError(errorMessage, response.status);
  }

  // Parse response
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// =============================================================================
// HTTP Methods
// =============================================================================

export const api = {
  get: <T>(path: string, options: RequestConfig = {}) =>
    apiRequest<T>(path, { ...options, method: 'GET' }),

  post: <T>(path: string, body: unknown, options: RequestConfig = {}) =>
    apiRequest<T>(path, {
      ...options,
      method: 'POST',
      body: JSON.stringify(body),
    }),

  patch: <T>(path: string, body: unknown, options: RequestConfig = {}) =>
    apiRequest<T>(path, {
      ...options,
      method: 'PATCH',
      body: JSON.stringify(body),
    }),

  delete: (path: string, options: RequestConfig = {}) =>
    apiRequest<void>(path, { ...options, method: 'DELETE' }),
};

// =============================================================================
// Auth Endpoints
// =============================================================================

import type { LoginRequest, LoginResponse, User } from './types';

export async function login(credentials: LoginRequest): Promise<User> {
  const data = await api.post<LoginResponse>('/auth/login', credentials, {
    skipAuth: true, // Login doesn't require auth
  });

  // Store session in memory
  const { setSession, setCsrfToken } = await import('./auth');
  setSession(data.user);
  // FIX CRIT-003: Use snake_case csrf_token
  setCsrfToken(data.csrf_token);

  toast.success('Login successful');
  return data.user;
}

export async function logout(): Promise<void> {
  try {
    await api.post('/auth/logout', {});
  } finally {
    const { clearSession } = await import('./auth');
    clearSession();
  }
}

export async function refreshSession(): Promise<User | null> {
  try {
    const data = await api.post<LoginResponse>('/auth/refresh', {});
    const { setSession, setCsrfToken } = await import('./auth');
    setSession(data.user);
    // FIX CRIT-003: Use snake_case csrf_token
    setCsrfToken(data.csrf_token);
    return data.user;
  } catch {
    const { clearSession } = await import('./auth');
    clearSession();
    return null;
  }
}

export async function getCurrentUser(): Promise<User | null> {
  try {
    const user = await api.get<User>('/auth/me');
    const { setSession } = await import('./auth');
    setSession(user);
    return user;
  } catch {
    return null;
  }
}

export async function fetchCsrfToken(): Promise<string> {
  const data = await api.get<{ csrf_token: string }>('/auth/csrf', {
    skipAuth: true,
  });
  const { setCsrfToken } = await import('./auth');
  // FIX CRIT-003: Use snake_case csrf_token
  setCsrfToken(data.csrf_token);
  return data.csrf_token;
}
