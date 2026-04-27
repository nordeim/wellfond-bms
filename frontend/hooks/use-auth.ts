"use client";

/**
 * use-auth — React hooks for authentication state
 * ================================================
 * Wraps lib/auth.ts with reactive React hooks
 * for cross-component auth state management.
 */

import { useCallback, useSyncExternalStore } from "react";
import type { User } from "@/lib/types";
import {
  getSession,
  isAuthenticated as checkIsAuthenticated,
  getRole,
  getCsrfToken,
  canAccessRoute,
  hasRole,
  isAdmin,
  checkTokenLeakage,
  logout as performLogout,
} from "@/lib/auth";

// ── Subscriber pattern for cross-component reactivity ──

type Listener = () => void;
const listeners = new Set<Listener>();

function subscribe(listener: Listener): () => void {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}

function notifyListeners(): void {
  listeners.forEach((l) => l());
}

// ── Public API to trigger re-renders from outside hooks ──

export function notifyAuthChanged(): void {
  notifyListeners();
}

// ── Hooks ──

export function useCurrentUser(): User | null {
  const subscribeToAuth = useCallback(
    (callback: () => void) => subscribe(callback),
    []
  );
  return useSyncExternalStore(subscribeToAuth, getSession);
}

export function useIsAuthenticated(): boolean {
  const subscribeToAuth = useCallback(
    (callback: () => void) => subscribe(callback),
    []
  );
  return useSyncExternalStore(subscribeToAuth, checkIsAuthenticated);
}

export function useUserRole(): string | null {
  const subscribeToAuth = useCallback(
    (callback: () => void) => subscribe(callback),
    []
  );
  return useSyncExternalStore(subscribeToAuth, getRole);
}

export function useCsrfToken(): string | null {
  const subscribeToAuth = useCallback(
    (callback: () => void) => subscribe(callback),
    []
  );
  return useSyncExternalStore(subscribeToAuth, getCsrfToken);
}

export function useCanAccessRoute(path: string): boolean {
  const subscribeToAuth = useCallback(
    (callback: () => void) => subscribe(callback),
    []
  );
  const getSnapshot = useCallback(() => canAccessRoute(path), [path]);
  return useSyncExternalStore(subscribeToAuth, getSnapshot);
}

export function useHasRole(...roles: string[]): boolean {
  const subscribeToAuth = useCallback(
    (callback: () => void) => subscribe(callback),
    []
  );
  const getSnapshot = useCallback(() => hasRole(...roles), [roles]);
  return useSyncExternalStore(subscribeToAuth, getSnapshot);
}

export function useIsAdmin(): boolean {
  const subscribeToAuth = useCallback(
    (callback: () => void) => subscribe(callback),
    []
  );
  return useSyncExternalStore(subscribeToAuth, isAdmin);
}

export function useLogout(): () => Promise<void> {
  const wrappedLogout = useCallback(async () => {
    await performLogout();
    notifyListeners();
  }, []);

  return wrappedLogout;
}

export function useTokenLeakageCheck(): {
  hasLeakage: boolean;
  keys: string[];
} {
  return checkTokenLeakage();
}