/**
 * Wellfond BMS - Protected Layout
 * =================================
 * Layout for authenticated pages with sidebar, topbar, and role bar.
 * Redirects to /login if not authenticated.
 */

import { Metadata } from 'next';
import { redirect } from 'next/navigation';

import { Sidebar } from '@/components/layout/sidebar';
import { Topbar } from '@/components/layout/topbar';
import { BottomNav } from '@/components/layout/bottom-nav';
import { RoleBar } from '@/components/layout/role-bar';
import { Toaster } from '@/components/ui/toast';
import { getCurrentUser } from '@/lib/api';

export const metadata: Metadata = {
  title: 'Wellfond BMS',
  description: 'Wellfond Breeding Management System',
};

export default async function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Get current user (server-side)
  let user = null;
  try {
    user = await getCurrentUser();
  } catch {
    // User not authenticated
  }

  // Redirect to login if not authenticated
  if (!user) {
    redirect('/login');
  }

  return (
    <div className="min-h-screen bg-[#DDEEFF]">
      {/* Desktop Sidebar */}
      <div className="hidden md:block">
        <Sidebar user={user} />
      </div>

      {/* Mobile Bottom Nav */}
      <div className="md:hidden">
        <BottomNav user={user} />
      </div>

      {/* Main content area */}
      <div className="flex min-h-screen flex-col md:pl-64">
        {/* Topbar */}
        <Topbar user={user} />

        {/* Role context bar */}
        <RoleBar user={user} />

        {/* Page content */}
        <main className="flex-1 p-6">
          {children}
        </main>
      </div>

      {/* Toast notifications */}
      <Toaster />
    </div>
  );
}
