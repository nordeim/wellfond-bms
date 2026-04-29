'use client';

/**
 * Dashboard Hooks for Wellfond BMS
 * ==================================
 * TanStack Query hooks for dashboard metrics and activity feed.
 * Phase 8: Dashboard & Finance Exports
 */

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { DashboardMetrics } from '@/lib/types';

// Query keys
const DASHBOARD_KEY = 'dashboard';
const ACTIVITY_KEY = 'activity';

// =============================================================================
// Dashboard Metrics Hook
// =============================================================================

interface UseDashboardMetricsOptions {
  entityId?: string;
}

export function useDashboardMetrics(options: UseDashboardMetricsOptions = {}) {
  const { entityId } = options;

  return useQuery({
    queryKey: [DASHBOARD_KEY, entityId],
    queryFn: async () => {
      const params = entityId ? `?entity=${entityId}` : '';
      const response = await api.get<DashboardMetrics>(`/dashboard/metrics${params}`);
      return response;
    },
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Auto-refresh every 60 seconds
  });
}

// =============================================================================
// Activity Feed Hook (Initial Load)
// =============================================================================

export function useActivityFeed(limit: number = 20) {
  return useQuery({
    queryKey: [ACTIVITY_KEY, limit],
    queryFn: async () => {
      // Get activity from dashboard metrics (recent_activity)
      const response = await api.get<DashboardMetrics>('/dashboard/metrics');
      return response.recent_activity || [];
    },
    staleTime: 30000,
  });
}

// =============================================================================
// Revenue Chart Hook
// =============================================================================

interface UseRevenueChartOptions {
  months?: number;
}

export function useRevenueChart(options: UseRevenueChartOptions = {}) {
  const { months = 6 } = options;

  return useQuery({
    queryKey: [DASHBOARD_KEY, 'revenue', months],
    queryFn: async () => {
      const response = await api.get<DashboardMetrics>('/dashboard/metrics');
      return response.revenue_summary?.monthly_data || [];
    },
    staleTime: 300000, // 5 minutes - revenue data changes less frequently
  });
}

// =============================================================================
// Quick Stats Hook (for widget refresh)
// =============================================================================

export function useQuickStats() {
  return useQuery({
    queryKey: [DASHBOARD_KEY, 'stats'],
    queryFn: async () => {
      const response = await api.get<DashboardMetrics>('/dashboard/metrics');
      return response.stats;
    },
    staleTime: 30000,
    refetchInterval: 60000,
  });
}

// =============================================================================
// Alerts Hook (for alert cards)
// =============================================================================

interface UseAlertsOptions {
  entityId?: string;
}

export function useDashboardAlerts(options: UseAlertsOptions = {}) {
  const { entityId } = options;

  return useQuery({
    queryKey: [DASHBOARD_KEY, 'alerts', entityId],
    queryFn: async () => {
      const params = entityId ? `?entity=${entityId}` : '';
      const response = await api.get<DashboardMetrics>(`/dashboard/metrics${params}`);
      return response.alerts;
    },
    staleTime: 30000,
    refetchInterval: 60000,
  });
}

// =============================================================================
// NParks Countdown Hook
// =============================================================================

export function useNParksCountdown() {
  return useQuery({
    queryKey: [DASHBOARD_KEY, 'nparks'],
    queryFn: async () => {
      const response = await api.get<DashboardMetrics>('/dashboard/metrics');
      return response.nparks_countdown;
    },
    staleTime: 3600000, // 1 hour - countdown only changes daily
  });
}
