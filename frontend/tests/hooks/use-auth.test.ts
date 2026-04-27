/**
 * TDD Test: hooks/use-auth.ts
 * ============================
 * React hooks wrapping lib/auth.ts for reactive auth state.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook } from "@testing-library/react";

// Mock lib/auth functions that the hook depends on
vi.mock("@/lib/auth", () => ({
  getSession: vi.fn(() => null),
  setSession: vi.fn(),
  clearSession: vi.fn(),
  isAuthenticated: vi.fn(() => false),
  getRole: vi.fn(() => null),
  getCsrfToken: vi.fn(() => null),
  canAccessRoute: vi.fn(() => false),
  hasRole: vi.fn(() => false),
  isAdmin: vi.fn(() => false),
  checkTokenLeakage: vi.fn(() => ({ hasLeakage: false, keys: [] })),
  logout: vi.fn(async () => {}),
}));

describe("hooks/use-auth", () => {
  let useAuth: typeof import("@/hooks/use-auth");

  beforeEach(async () => {
    vi.clearAllMocks();
    useAuth = await import("@/hooks/use-auth");
  });

  it("useCurrentUser returns null when unauthenticated", () => {
    const { result } = renderHook(() => useAuth.useCurrentUser());
    expect(result.current).toBeNull();
  });

  it("useIsAuthenticated returns false when unauthenticated", () => {
    const { result } = renderHook(() => useAuth.useIsAuthenticated());
    expect(result.current).toBe(false);
  });

  it("useUserRole returns null when unauthenticated", () => {
    const { result } = renderHook(() => useAuth.useUserRole());
    expect(result.current).toBeNull();
  });

  it("useLogout returns a function that does not throw", async () => {
    const { result } = renderHook(() => useAuth.useLogout());
    expect(typeof result.current).toBe("function");
    await expect(result.current()).resolves.not.toThrow();
  });
});