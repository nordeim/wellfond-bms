/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { isAuthenticated, setSession, clearSession } from './auth';

describe('isAuthenticated - FIX-06 regression (CR-004)', () => {
  beforeEach(() => {
    clearSession();
  });

  afterEach(() => {
    clearSession();
    // Clean up any cookie we set
    document.cookie = 'sessionid=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
  });

  it('returns true when sessionid cookie exists (even with no cached user)', () => {
    // Arrange: no cached user, but sessionid cookie exists
    document.cookie = 'sessionid=test123; path=/; SameSite=Lax';
    
    // Act
    const result = isAuthenticated();
    
    // Assert: should return true because sessionid cookie = server session exists
    expect(result).toBe(true);
  });

  it('returns false when no sessionid cookie AND no cached user', () => {
    // Arrange: no cached user, no sessionid cookie
    
    // Act
    const result = isAuthenticated();
    
    // Assert: should return false
    expect(result).toBe(false);
  });

  it('returns true when cached user exists (regardless of cookie)', () => {
    // Arrange: set cached user
    setSession({ id: '1', role: 'admin', email: 'test@test.com' } as any);
    
    // Act
    const result = isAuthenticated();
    
    // Assert: should return true via cached user
    expect(result).toBe(true);
  });
});
