/**
 * Dashboard E2E Tests - Wellfond BMS
 * ===================================
 * Playwright E2E tests for dashboard functionality.
 *
 * Phase 8: Dashboard & Finance Exports
 * Run: npx playwright test dashboard.spec.ts
 */

import { test, expect } from '@playwright/test';
import type { Page } from '@playwright/test';

// Test users for different roles
const TEST_USERS = {
  management: { username: 'admin', password: 'Wellfond@2024!', role: 'management' as const },
  admin: { username: 'admin', password: 'Wellfond@2024!', role: 'admin' as const },
  sales: { username: 'sales', password: 'Wellfond@2024!', role: 'sales' as const },
  vet: { username: 'vet', password: 'Wellfond@2024!', role: 'vet' as const },
  ground: { username: 'ground', password: 'Wellfond@2024!', role: 'ground' as const },
};

/**
 * Helper: Login as a specific user role
 */
async function loginAs(page: Page, role: keyof typeof TEST_USERS) {
  const user = TEST_USERS[role];

  await page.goto('/login');
  await page.waitForSelector('[data-testid="login-form"]', { timeout: 5000 });

  await page.fill('[data-testid="email-input"]', user.username);
  await page.fill('[data-testid="password-input"]', user.password);
  await page.click('[data-testid="login-button"]');

  // Wait for dashboard redirect
  await page.waitForURL('**/dashboard', { timeout: 10000 });
}

/**
 * Helper: Wait for dashboard to be fully loaded
 */
async function waitForDashboard(page: Page) {
  // Wait for dashboard container
  await page.waitForSelector('[data-testid="dashboard-page"]', { timeout: 10000 });

  // Wait for at least one stat card to load
  await page.waitForSelector('[data-testid="stat-card"]', { timeout: 10000 });
}

test.describe('Dashboard Page - Core Functionality', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin before each test
    await loginAs(page, 'admin');
    await waitForDashboard(page);
  });

  test('dashboard page loads without 404', async ({ page }) => {
    // Verify page loaded
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.locator('h1')).toContainText('Dashboard');
  });

  test('page title is correct', async ({ page }) => {
    await expect(page).toHaveTitle(/Dashboard | Wellfond BMS/);
  });

  test('displays welcome message with user name', async ({ page }) => {
    // Check welcome message is displayed
    await expect(page.locator('[data-testid="welcome-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="welcome-message"]')).toContainText('Welcome back');
  });

  test('quick actions are visible', async ({ page }) => {
    // Check quick actions section
    const quickActions = page.locator('[data-testid="quick-actions"]');
    await expect(quickActions).toBeVisible();
    await expect(quickActions.locator('button')).toHaveCount(3);
  });
});

test.describe('Dashboard - Alert Cards', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
    await waitForDashboard(page);
  });

  test('alert cards strip is visible', async ({ page }) => {
    const alertCards = page.locator('[data-testid="alert-cards"]');
    await expect(alertCards).toBeVisible();
  });

  test('at least one alert card is displayed', async ({ page }) => {
    const alertCardItems = page.locator('[data-testid="alert-card-item"]');
    await expect(alertCardItems.first()).toBeVisible();
  });

  test('alert cards show counts', async ({ page }) => {
    // Check that alert cards have numeric counts
    const counts = page.locator('[data-testid="alert-card-count"]');
    const count = await counts.count();
    expect(count).toBeGreaterThan(0);
  });
});

test.describe('Dashboard - Stat Cards', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
    await waitForDashboard(page);
  });

  test('all 4 stat cards are displayed', async ({ page }) => {
    const statCards = page.locator('[data-testid="stat-card"]');
    await expect(statCards).toHaveCount(4);
  });

  test('stat cards show correct labels', async ({ page }) => {
    await expect(page.locator('text=Total Dogs')).toBeVisible();
    await expect(page.locator('text=Active Litters')).toBeVisible();
    await expect(page.locator('text=Pending Agreements')).toBeVisible();
    await expect(page.locator('text=Overdue Vaccines')).toBeVisible();
  });

  test('stat cards show numeric values', async ({ page }) => {
    const statValues = page.locator('[data-testid="stat-value"]');
    const count = await statValues.count();
    expect(count).toBe(4);

    // Check each value is a number
    for (let i = 0; i < count; i++) {
      const text = await statValues.nth(i).textContent();
      expect(parseInt(text || '0')).not.toBeNaN();
    }
  });

  test('stat cards are clickable', async ({ page }) => {
    const firstStatCard = page.locator('[data-testid="stat-card"]').first();
    await expect(firstStatCard).toBeEnabled();
  });
});

test.describe('Dashboard - NParks Countdown', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
    await waitForDashboard(page);
  });

  test('NParks countdown widget is visible', async ({ page }) => {
    const nparksWidget = page.locator('[data-testid="nparks-countdown"]');
    await expect(nparksWidget).toBeVisible();
  });

  test('shows days remaining', async ({ page }) => {
    await expect(page.locator('[data-testid="nparks-days"]')).toBeVisible();
  });

  test('shows deadline date', async ({ page }) => {
    await expect(page.locator('text=/Deadline:/')).toBeVisible();
  });

  test('has action button to compliance', async ({ page }) => {
    const actionButton = page.locator('[data-testid="nparks-action"]');
    await expect(actionButton).toBeVisible();
    await expect(actionButton).toContainText('Go to Compliance');
  });

  test('action button navigates to compliance', async ({ page }) => {
    await page.click('[data-testid="nparks-action"]');
    await page.waitForURL('**/compliance', { timeout: 5000 });
    await expect(page).toHaveURL(/\/compliance/);
  });
});

test.describe('Dashboard - Activity Feed', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
    await waitForDashboard(page);
  });

  test('activity feed is visible', async ({ page }) => {
    const activityFeed = page.locator('[data-testid="activity-feed"]');
    await expect(activityFeed).toBeVisible();
  });

  test('shows recent activity header', async ({ page }) => {
    await expect(page.locator('text=Recent Activity')).toBeVisible();
  });

  test('activity items have timestamps', async ({ page }) => {
    // Check for time indicators (e.g., "5m ago", "1h ago")
    const timeIndicators = page.locator('text=/\\d+[mh] ago/');
    await expect(timeIndicators.first()).toBeVisible();
  });

  test('pauses on hover', async ({ page }) => {
    const activityFeed = page.locator('[data-testid="activity-feed"]');
    await activityFeed.hover();
    await expect(page.locator('text=(paused)')).toBeVisible();
  });
});

test.describe('Dashboard - Revenue Chart', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
    await waitForDashboard(page);
  });

  test('revenue chart is visible for authorized roles', async ({ page }) => {
    const revenueChart = page.locator('[data-testid="revenue-chart"]');
    await expect(revenueChart).toBeVisible();
  });

  test('shows revenue header', async ({ page }) => {
    await expect(page.locator('text=Revenue (6 Months)')).toBeVisible();
  });

  test('shows total revenue and GST', async ({ page }) => {
    await expect(page.locator('text=Total Revenue')).toBeVisible();
    await expect(page.locator('text=GST Collected')).toBeVisible();
  });
});

test.describe('Dashboard - Role-Based Access', () => {
  test('ground staff does not see revenue chart', async ({ page }) => {
    await loginAs(page, 'ground');
    await waitForDashboard(page);

    const revenueChart = page.locator('[data-testid="revenue-chart"]');
    await expect(revenueChart).toHaveCount(0);
  });

  test('vet sees health-focused quick actions', async ({ page }) => {
    await loginAs(page, 'vet');
    await waitForDashboard(page);

    await expect(page.locator('text=Health Check')).toBeVisible();
    await expect(page.locator('text=Vaccination Round')).toBeVisible();
  });

  test('sales sees sales-focused quick actions', async ({ page }) => {
    await loginAs(page, 'sales');
    await waitForDashboard(page);

    await expect(page.locator('text=Create Agreement')).toBeVisible();
    await expect(page.locator('text=View Pipeline')).toBeVisible();
    await expect(page.locator('text=Customers')).toBeVisible();
  });

  test('management sees all quick actions', async ({ page }) => {
    await loginAs(page, 'management');
    await waitForDashboard(page);

    await expect(page.locator('text=Add Dog')).toBeVisible();
    await expect(page.locator('text=Create Agreement')).toBeVisible();
    await expect(page.locator('text=Run Report')).toBeVisible();
  });
});

test.describe('Dashboard - Responsive Design', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
    await waitForDashboard(page);
  });

  test('displays correctly on desktop (1920x1080)', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });

    // All sections should be visible
    await expect(page.locator('[data-testid="stat-cards"]')).toBeVisible();
    await expect(page.locator('[data-testid="alert-cards"]')).toBeVisible();
    await expect(page.locator('[data-testid="revenue-chart"]')).toBeVisible();
  });

  test('displays correctly on tablet (768x1024)', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });

    await expect(page.locator('[data-testid="stat-cards"]')).toBeVisible();
    await expect(page.locator('[data-testid="alert-cards"]')).toBeVisible();
  });

  test('displays correctly on mobile (375x667)', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });

    await expect(page.locator('[data-testid="stat-cards"]')).toBeVisible();
    await expect(page.locator('[data-testid="alert-cards"]')).toBeVisible();
  });
});

test.describe('Dashboard - API Integration', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
  });

  test('dashboard API returns 200', async ({ request }) => {
    // This test verifies the API endpoint directly
    const response = await request.get('/api/proxy/dashboard/metrics');
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('stats');
    expect(data).toHaveProperty('alerts');
    expect(data).toHaveProperty('nparks_countdown');
    expect(data).toHaveProperty('recent_activity');
  });

  test('dashboard API returns correct structure', async ({ request }) => {
    const response = await request.get('/api/proxy/dashboard/metrics');
    const data = await response.json();

    // Check stats structure
    expect(data.stats).toHaveProperty('total_dogs');
    expect(data.stats).toHaveProperty('active_litters');
    expect(data.stats).toHaveProperty('pending_agreements');
    expect(data.stats).toHaveProperty('overdue_vaccinations');

    // Check alerts is an array
    expect(Array.isArray(data.alerts)).toBe(true);

    // Check nparks_countdown structure
    expect(data.nparks_countdown).toHaveProperty('days');
    expect(data.nparks_countdown).toHaveProperty('deadline_date');
    expect(data.nparks_countdown).toHaveProperty('status');

    // Check recent_activity is an array
    expect(Array.isArray(data.recent_activity)).toBe(true);
  });
});

test.describe('Dashboard - Performance', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
  });

  test('dashboard loads within 2 seconds', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/dashboard');
    await waitForDashboard(page);

    const loadTime = Date.now() - startTime;
    expect(loadTime).toBeLessThan(2000);
  });

  test('stat cards show skeleton during loading', async ({ page }) => {
    // Intercept API and delay response
    await page.route('/api/proxy/dashboard/metrics', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 500));
      await route.continue();
    });

    await page.goto('/dashboard');

    // Check for skeleton elements
    const skeletons = page.locator('.animate-pulse');
    await expect(skeletons.first()).toBeVisible();
  });
});

test.describe('Dashboard - Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
    await waitForDashboard(page);
  });

  test('page has proper heading hierarchy', async ({ page }) => {
    // Check h1 exists
    const h1 = page.locator('h1');
    await expect(h1).toHaveCount(1);
    await expect(h1).toContainText('Dashboard');
  });

  test('quick action buttons are keyboard accessible', async ({ page }) => {
    const firstButton = page.locator('[data-testid="quick-actions"] button').first();

    // Tab to button
    await page.keyboard.press('Tab');
    await expect(firstButton).toBeFocused();

    // Enter should work
    await page.keyboard.press('Enter');
    // Should navigate to the link
  });

  test('stat cards have proper ARIA labels', async ({ page }) => {
    const statCards = page.locator('[data-testid="stat-card"]');
    const count = await statCards.count();

    for (let i = 0; i < count; i++) {
      const card = statCards.nth(i);
      const label = await card.getAttribute('aria-label');
      expect(label).toBeTruthy();
    }
  });
});
