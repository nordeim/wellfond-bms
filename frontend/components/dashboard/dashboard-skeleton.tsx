/**
 * Dashboard Skeleton Components
 * ==============================
 * Loading skeletons for dashboard widgets.
 *
 * Phase 8: Dashboard & Finance Exports
 */

import { Skeleton } from '@/components/ui/skeleton';

export const DashboardSkeleton = {
  Alerts: () => (
    <div className="flex gap-3 overflow-x-auto pb-2">
      {Array.from({ length: 6 }).map((_, i) => (
        <Skeleton key={i} className="h-[88px] min-w-[180px] rounded-lg" />
      ))}
    </div>
  ),

  Stats: () => (
    <div className="grid gap-4 sm:grid-cols-2">
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} className="h-20 rounded-lg" />
      ))}
    </div>
  ),

  NParks: () => (
    <div className="rounded-lg border border-[#C0D8EE] p-4 space-y-4">
      <Skeleton className="h-5 w-32" />
      <Skeleton className="h-12 w-20" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-10 w-full" />
    </div>
  ),

  Chart: () => (
    <div className="rounded-lg border border-[#C0D8EE] p-4 space-y-4">
      <Skeleton className="h-5 w-32" />
      <Skeleton className="h-40 w-full" />
    </div>
  ),

  Activity: () => (
    <div className="rounded-lg border border-[#C0D8EE] p-4 space-y-4">
      <Skeleton className="h-5 w-32" />
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-12 w-full" />
      ))}
    </div>
  ),
};
