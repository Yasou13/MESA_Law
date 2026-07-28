import { test, expect } from '@playwright/test';

test.describe('Dashboard (Authenticated)', () => {
  test.beforeEach(async ({ page }) => {
    // Mock NextAuth session
    await page.route('**/api/auth/session', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user: { name: 'E2E User', email: 'e2e@mesalaw.test' },
          accessToken: 'mock-e2e-token',
          expires: new Date(Date.now() + 1000 * 60 * 60 * 24).toISOString()
        })
      });
    });

    // Also inject localStorage before page load using addInitScript
    await page.addInitScript(() => {
      window.localStorage.setItem('mesa_tenant_id', 'dev-tenant-default');
    });

    await page.goto('/dashboard');
  });

  test('should render dashboard layout and components', async ({ page }) => {
    // Verify Sidebar navigation items
    await expect(page.getByRole('link', { name: 'Dashboard' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Matters' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Documents' })).toBeVisible();

    // Verify main dashboard components (KPI Cards, Recent Activity)
    // Even if the backend returns empty arrays, the headers should be visible.
    await expect(page.locator('text=Active Matters').first()).toBeVisible();
    await expect(page.locator('text=Recent Activity').first()).toBeVisible();
  });

  test('should handle responsive mobile sidebar toggle', async ({ page }) => {
    // Set viewport to mobile
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/dashboard');

    // The hamburger menu button should be visible
    const menuButton = page.getByRole('button', { name: 'Open menu' });
    await expect(menuButton).toBeVisible();

    // Click it to open the sidebar
    await menuButton.click();

    // Now the sidebar links should be visible and clickable
    await expect(page.getByRole('link', { name: 'Dashboard' })).toBeVisible();

    // The close button should be visible
    const closeButton = page.getByRole('button', { name: 'Close menu' });
    await expect(closeButton).toBeVisible();
    await closeButton.click();
  });
});
