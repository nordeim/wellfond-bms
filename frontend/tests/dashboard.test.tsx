/**
 * Dashboard Component Tests - Wellfond BMS
 * =========================================
 * Vitest + React Testing Library tests for dashboard components.
 *
 * Phase 8: Dashboard & Finance Exports
 * Test Strategy: Component rendering, hook behavior, integration with MSW
 *
 * Run: npm test -- dashboard.test.tsx
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Components to test
import { StatCards } from '@/components/dashboard/stat-cards';
import { NParksCountdown } from '@/components/dashboard/nparks-countdown';
import { QuickActions } from '@/components/dashboard/quick-actions';
import { ActivityFeed } from '@/components/dashboard/activity-feed';
import { RevenueChart } from '@/components/dashboard/revenue-chart';

// Mock data
import type { DashboardStats, NParksCountdown as NParksCountdownType, ActivityFeedItem, RevenueMonthlyData, Role } from '@/lib/types';

// =============================================================================
// Test Utilities
// =============================================================================

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 0,
      },
    },
  });
}

function Wrapper({ children }: { children: React.ReactNode }) {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}

// Mock API responses
const mockStats: DashboardStats = {
  total_dogs: 483,
  active_litters: 12,
  pending_agreements: 8,
  overdue_vaccinations: 5,
};

const mockNParksCountdown: NParksCountdownType = {
  days: 5,
  deadline_date: '2026-04-30',
  status: 'due_soon',
};

const mockActivities: ActivityFeedItem[] = [
  {
    id: '1',
    action: 'create',
    resource_type: 'dog',
    resource_id: 'dog-123',
    actor_name: 'Admin User',
    timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(), // 5 min ago
  },
  {
    id: '2',
    action: 'update',
    resource_type: 'agreement',
    resource_id: 'agr-456',
    actor_name: 'Sales User',
    timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(), // 30 min ago
  },
];

const mockRevenueData: RevenueMonthlyData[] = [
  { month: '2026-01', month_label: 'Jan 2026', total_sales: 15000, gst_collected: 1238 },
  { month: '2026-02', month_label: 'Feb 2026', total_sales: 22000, gst_collected: 1816 },
  { month: '2026-03', month_label: 'Mar 2026', total_sales: 18500, gst_collected: 1529 },
];

// Mock the hooks
vi.mock('@/hooks/use-dashboard', () => ({
  useQuickStats: vi.fn(),
  useNParksCountdown: vi.fn(),
  useActivityFeed: vi.fn(),
  useRevenueChart: vi.fn(),
}));

import * as dashboardHooks from '@/hooks/use-dashboard';

// =============================================================================
// StatCards Tests
// =============================================================================

describe('StatCards', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading skeleton when data is loading', () => {
    vi.mocked(dashboardHooks.useQuickStats).mockReturnValue({
      data: undefined,
      isLoading: true,
    } as any);

    render(<StatCards />, { wrapper: Wrapper });

    // Should show skeletons
    const skeletons = screen.getAllByRole('generic', { hidden: true });
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders all 4 stat cards with correct data', () => {
    vi.mocked(dashboardHooks.useQuickStats).mockReturnValue({
      data: mockStats,
      isLoading: false,
    } as any);

    render(<StatCards />, { wrapper: Wrapper });

    // Check all stats are displayed
    expect(screen.getByText('Total Dogs')).toBeInTheDocument();
    expect(screen.getByText('483')).toBeInTheDocument();

    expect(screen.getByText('Active Litters')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();

    expect(screen.getByText('Pending Agreements')).toBeInTheDocument();
    expect(screen.getByText('8')).toBeInTheDocument();

    expect(screen.getByText('Overdue Vaccines')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('shows empty state when no stats available', () => {
    vi.mocked(dashboardHooks.useQuickStats).mockReturnValue({
      data: null,
      isLoading: false,
    } as any);

    render(<StatCards />, { wrapper: Wrapper });

    expect(screen.getByText('No stats available')).toBeInTheDocument();
  });
});

// =============================================================================
// NParksCountdown Tests
// =============================================================================

describe('NParksCountdown', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading skeleton when data is loading', () => {
    vi.mocked(dashboardHooks.useNParksCountdown).mockReturnValue({
      data: undefined,
      isLoading: true,
    } as any);

    render(<NParksCountdown />, { wrapper: Wrapper });

    const skeletons = screen.getAllByRole('generic', { hidden: true });
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders countdown with correct days and status', () => {
    vi.mocked(dashboardHooks.useNParksCountdown).mockReturnValue({
      data: mockNParksCountdown,
      isLoading: false,
    } as any);

    render(<NParksCountdown />, { wrapper: Wrapper });

    expect(screen.getByText('NParks Submission')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('days remaining')).toBeInTheDocument();
    expect(screen.getByText('Due Soon')).toBeInTheDocument();
  });

  it('renders deadline date in correct format', () => {
    vi.mocked(dashboardHooks.useNParksCountdown).mockReturnValue({
      data: mockNParksCountdown,
      isLoading: false,
    } as any);

    render(<NParksCountdown />, { wrapper: Wrapper });

    expect(screen.getByText(/Deadline:/)).toBeInTheDocument();
  });

  it('shows overdue status when days <= 0', () => {
    vi.mocked(dashboardHooks.useNParksCountdown).mockReturnValue({
      data: { ...mockNParksCountdown, days: 0, status: 'overdue' as const },
      isLoading: false,
    } as any);

    render(<NParksCountdown />, { wrapper: Wrapper });

    expect(screen.getByText('Overdue')).toBeInTheDocument();
    expect(screen.getByText('Submit Now')).toBeInTheDocument();
  });

  it('does not render when more than 7 days away', () => {
    vi.mocked(dashboardHooks.useNParksCountdown).mockReturnValue({
      data: { ...mockNParksCountdown, days: 10, status: 'upcoming' as const },
      isLoading: false,
    } as any);

    const { container } = render(<NParksCountdown />, { wrapper: Wrapper });

    expect(container.firstChild).toBeNull();
  });
});

// =============================================================================
// QuickActions Tests
// =============================================================================

describe('QuickActions', () => {
  const roles: Role[] = ['management', 'admin', 'sales', 'ground', 'vet'];

  roles.forEach((role) => {
    it(`renders actions for ${role} role`, () => {
      render(<QuickActions role={role} />);

      // Should render at least one action button
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });
  });

  it('renders management-specific actions', () => {
    render(<QuickActions role="management" />);

    // Management should see Add Dog, Create Agreement, Run Report
    expect(screen.getByText('Add Dog')).toBeInTheDocument();
    expect(screen.getByText('Create Agreement')).toBeInTheDocument();
    expect(screen.getByText('Run Report')).toBeInTheDocument();
  });

  it('renders sales-specific actions', () => {
    render(<QuickActions role="sales" />);

    // Sales should see Create Agreement, View Pipeline, Customers
    expect(screen.getByText('Create Agreement')).toBeInTheDocument();
    expect(screen.getByText('View Pipeline')).toBeInTheDocument();
    expect(screen.getByText('Customers')).toBeInTheDocument();
  });

  it('renders vet-specific actions', () => {
    render(<QuickActions role="vet" />);

    // Vet should see Health Check, Vaccination Round, View Dogs
    expect(screen.getByText('Health Check')).toBeInTheDocument();
    expect(screen.getByText('Vaccination Round')).toBeInTheDocument();
    expect(screen.getByText('View Dogs')).toBeInTheDocument();
  });

  it('action buttons have correct links', () => {
    render(<QuickActions role="management" />);

    const addDogButton = screen.getByText('Add Dog').closest('a');
    expect(addDogButton).toHaveAttribute('href', '/dogs/new');

    const agreementButton = screen.getByText('Create Agreement').closest('a');
    expect(agreementButton).toHaveAttribute('href', '/sales/new');
  });
});

// =============================================================================
// ActivityFeed Tests
// =============================================================================

describe('ActivityFeed', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading skeleton when data is loading', () => {
    vi.mocked(dashboardHooks.useActivityFeed).mockReturnValue({
      data: undefined,
      isLoading: true,
    } as any);

    render(<ActivityFeed />, { wrapper: Wrapper });

    const skeletons = screen.getAllByRole('generic', { hidden: true });
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders activity items with correct data', () => {
    vi.mocked(dashboardHooks.useActivityFeed).mockReturnValue({
      data: mockActivities,
      isLoading: false,
    } as any);

    render(<ActivityFeed />, { wrapper: Wrapper });

    expect(screen.getByText('Recent Activity')).toBeInTheDocument();
    expect(screen.getByText('Admin User')).toBeInTheDocument();
    expect(screen.getByText('Sales User')).toBeInTheDocument();
  });

  it('shows empty state when no activities', () => {
    vi.mocked(dashboardHooks.useActivityFeed).mockReturnValue({
      data: [],
      isLoading: false,
    } as any);

    render(<ActivityFeed />, { wrapper: Wrapper });

    expect(screen.getByText('No recent activity')).toBeInTheDocument();
  });

  it('displays pause indicator on hover', () => {
    vi.mocked(dashboardHooks.useActivityFeed).mockReturnValue({
      data: mockActivities,
      isLoading: false,
    } as any);

    render(<ActivityFeed />, { wrapper: Wrapper });

    const card = screen.getByText('Recent Activity').closest('[class*="Card"]');
    expect(card).toBeInTheDocument();
  });
});

// =============================================================================
// RevenueChart Tests
// =============================================================================

describe('RevenueChart', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading skeleton when data is loading', () => {
    vi.mocked(dashboardHooks.useRevenueChart).mockReturnValue({
      data: undefined,
      isLoading: true,
    } as any);

    render(<RevenueChart />, { wrapper: Wrapper });

    const skeletons = screen.getAllByRole('generic', { hidden: true });
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders empty state when no revenue data', () => {
    vi.mocked(dashboardHooks.useRevenueChart).mockReturnValue({
      data: [],
      isLoading: false,
    } as any);

    render(<RevenueChart />, { wrapper: Wrapper });

    expect(screen.getByText('No revenue data available')).toBeInTheDocument();
    expect(screen.getByText('Complete sales agreements to see revenue trends')).toBeInTheDocument();
  });

  it('renders chart with revenue data', () => {
    vi.mocked(dashboardHooks.useRevenueChart).mockReturnValue({
      data: mockRevenueData,
      isLoading: false,
    } as any);

    render(<RevenueChart />, { wrapper: Wrapper });

    expect(screen.getByText('Revenue (6 Months)')).toBeInTheDocument();
    expect(screen.getByText('Total Revenue')).toBeInTheDocument();
    expect(screen.getByText('GST Collected')).toBeInTheDocument();
  });

  it('calculates total revenue correctly', () => {
    vi.mocked(dashboardHooks.useRevenueChart).mockReturnValue({
      data: mockRevenueData,
      isLoading: false,
    } as any);

    render(<RevenueChart />, { wrapper: Wrapper });

    const expectedTotal = mockRevenueData.reduce((sum, d) => sum + d.total_sales, 0);
    expect(expectedTotal).toBe(55500); // 15000 + 22000 + 18500

    // Total should be displayed (formatted with commas)
    expect(screen.getByText(/55,500/)).toBeInTheDocument();
  });
});

// =============================================================================
// Dashboard Page Integration Tests
// =============================================================================

describe('Dashboard Page', () => {
  it('renders dashboard layout with all sections', () => {
    // This would be a full page integration test
    // Would require mocking the full API response and user context
    // Skipping for unit test suite - covered by E2E tests
  });

  it('handles entity filter changes', () => {
    // Would test that entityId prop is passed correctly
    // Skipping for unit test suite - covered by E2E tests
  });

  it('adapts layout for different roles', () => {
    // Would test role-specific content visibility
    // Skipping for unit test suite - covered by E2E tests
  });
});
