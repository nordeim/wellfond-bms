/**
 * Wellfond BMS - Auth Layout
 * ============================
 * Minimal layout for auth pages (login, forgot password, etc.)
 * Centered card, full-screen Tangerine Sky background, no sidebar.
 */

import type { Metadata } from 'next';
import { Toaster } from '@/components/ui/toast';

export const metadata: Metadata = {
  title: 'Login - Wellfond BMS',
  description: 'Sign in to Wellfond Breeding Management System',
};

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[#DDEEFF]">
      {/* Centered content */}
      <div className="flex min-h-screen items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
        <div className="w-full max-w-md">
          {/* Logo */}
          <div className="mb-8 flex justify-center">
            <div className="flex flex-col items-center gap-2">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[#F97316] shadow-lg">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  className="h-8 w-8 text-white"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z" />
                  <circle cx="9" cy="10" r="1.5" fill="currentColor" />
                  <circle cx="15" cy="10" r="1.5" fill="currentColor" />
                  <path d="M12 16c-2.33 0-4.31-1.46-5.11-3.5h10.22c-.8 2.04-2.78 3.5-5.11 3.5z" />
                </svg>
              </div>
              <div className="text-center">
                <h1 className="text-xl font-bold text-[#0D2030]">Wellfond</h1>
                <p className="text-sm text-[#4A7A94]">Breeding Management System</p>
              </div>
            </div>
          </div>

          {/* Auth content */}
          {children}
        </div>
      </div>

      {/* Toast notifications */}
      <Toaster />
    </div>
  );
}
