'use client';

/**
 * AuthInitializer component
 * =========================
 * Restores user session from HttpOnly cookie on application startup.
 * Prevents flash of unauthenticated content.
 */

import { useEffect, useState } from 'react';
import { getCurrentUser, fetchCsrfToken } from '@/lib/api';
import { notifyAuthChanged } from '@/hooks/use-auth';

export function AuthInitializer({ children }: { children: React.ReactNode }) {
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    async function initAuth() {
      try {
        // 1. Fetch CSRF token for subsequent requests
        await fetchCsrfToken();
        
        // 2. Restore session from HttpOnly cookie
        await getCurrentUser();
        
        // 3. Notify listeners (hooks) to re-render
        notifyAuthChanged();
      } catch (error) {
        // Not authenticated or network error - fail gracefully
        console.debug('Auth initialization: No active session');
      } finally {
        setIsInitialized(true);
      }
    }

    initAuth();
  }, []);

  if (!isInitialized) {
    // Show nothing (or a splash screen) while verifying session
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-brand-bg">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-primary border-t-transparent" />
      </div>
    );
  }

  return <>{children}</>;
}
