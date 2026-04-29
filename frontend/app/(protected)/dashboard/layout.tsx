/**
 * Wellfond BMS - Dashboard Layout
 * ================================
 * Layout for dashboard page with mobile optimizations.
 *
 * Phase 8: Dashboard & Finance Exports
 */

import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Dashboard | Wellfond BMS',
  description: 'Role-aware command centre for breeding operations',
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-full">
      {children}
    </div>
  );
}
