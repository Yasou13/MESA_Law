import { test, expect } from '@playwright/test';

test.describe('MESA Law Lifecycle', () => {
  test('should login and view matters', async ({ page }) => {
    await page.goto('/login');
    
    // Check if redirect happens (we use dummy creds)
    await page.fill('input[type="email"]', 'yasin@mesa.law');
    await page.fill('input[type="password"]', 'password');
    
    await page.click('button[type="submit"]');

    // Wait for URL to be dashboard or matters
    await page.waitForURL('**/dashboard');
    await expect(page.locator('text=Dashboard')).toBeVisible();

    // Navigate to matters
    await page.click('a[href="/matters"]');
    await expect(page).toHaveURL(/.*\/matters/);

    // Verify matter list loads (we can just check page title or table)
    await expect(page.locator('h1')).toHaveText(/Matters/i);
  });
});
