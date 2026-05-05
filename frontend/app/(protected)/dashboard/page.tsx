/**
 * Wellfond BMS - Dashboard Page
 * ==============================
 * Role-aware command centre with 7 alert cards, NParks countdown,
 * mate checker widget, revenue chart, and activity feed.
 *
 * Phase 8: Dashboard & Finance Exports
 * Avant-Garde Design: Tangerine Sky theme with intentional minimalism
 */

import { Suspense } from 'react';
import { Metadata } from 'next';

import { AlertCards } from '@/components/dogs/alert-cards';
import { StatCards } from '@/components/dashboard/stat-cards';
import { NParksCountdown } from '@/components/dashboard/nparks-countdown';
import { QuickActions } from '@/components/dashboard/quick-actions';
import { ActivityFeed } from '@/components/dashboard/activity-feed';
import { RevenueChart } from '@/components/dashboard/revenue-chart';
import { DashboardSkeleton } from '@/components/dashboard/dashboard-skeleton';
import { getCurrentUser } from '@/lib/api';


export const metadata: Metadata = {
  title: 'Dashboard | Wellfond BMS',
  description: 'Role-aware command centre for breeding operations',
};

interface DashboardPageProps {
  searchParams?: { entity?: string };
}

export default async function DashboardPage({ searchParams }: DashboardPageProps) {
  const user = await getCurrentUser();

  if (!user) {
    return null; // Protected layout handles redirect
  }

  const entityId = searchParams?.entity;

  return (
    <div className="min-h-screen space-y-6">
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#0D2030]">Dashboard</h1>
          <p className="text-sm text-[#4A7A94]">
            Welcome back, {user.first_name || user.username}
          </p>
        </div>
        <QuickActions role={user.role} />
      </div>

      {/* Alert Cards Strip */}
      <Suspense fallback={<DashboardSkeleton.Alerts />}>
        <section aria-label="Alert Cards">
          <AlertCards entityId={entityId} />
        </section>
      </Suspense>

      {/* Main Dashboard Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column: Stats + NParks */}
        <div className="space-y-6 lg:col-span-1">
          <Suspense fallback={<DashboardSkeleton.Stats />}>
            <StatCards entityId={entityId} />
          </Suspense>

          <Suspense fallback={<DashboardSkeleton.NParks />}>
            <NParksCountdown />
          </Suspense>
        </div>

        {/* Middle Column: Revenue Chart */}
        {(user.role === 'management' || user.role === 'admin' || user.role === 'sales') && (
          <div className="lg:col-span-1">
            <Suspense fallback={<DashboardSkeleton.Chart />}>
              <RevenueChart />
            </Suspense>
          </div>
        )}

        {/* Right Column: Activity Feed */}
        <div className="lg:col-span-1">
          <Suspense fallback={<DashboardSkeleton.Activity />}>
            <ActivityFeed />
          </Suspense>
        </div>
      </div>

      {/* Mobile-Only: Full Width Stats */}
      <div className="lg:hidden">
        <Suspense fallback={<DashboardSkeleton.Stats />}>
          <StatCards entityId={entityId} variant="compact" />
        </Suspense>
      </div>
    </div>
  );
}
