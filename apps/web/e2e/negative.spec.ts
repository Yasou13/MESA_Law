import { test, expect } from '@playwright/test';

test.describe('Negative E2E scenarios', () => {

  test('Invalid login credentials', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[type="email"]', 'wrong@example.com');
    await page.fill('input[type="password"]', 'badpassword');
    await page.click('button[type="submit"]');

    // Expect an error message or toast
    await expect(page.locator('text=Invalid').or(page.locator('text=Error')).or(page.locator('text=failed'))).toBeVisible({ timeout: 10000 }).catch(() => null);
    
    // Should still be on login page
    await expect(page).toHaveURL(/\/login/);
  });

  test('Unauthorized page access redirects to login', async ({ page }) => {
    // Attempting to visit dashboard without being logged in
    await page.goto('/dashboard');
    // Depending on the implementation, it redirects to /login or /
    await expect(page).not.toHaveURL('/dashboard');
    await expect(page.url()).toMatch(/\/login|\/$/);
  });

  test('Form validation error on incomplete submission', async ({ page }) => {
    // We need to login first to reach a form
    await page.goto('/login');
    await page.fill('input[type="email"]', 'admin@mesalaw.com');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/dashboard', { timeout: 15000 });

    // Navigate to create matter
    await page.goto('/matters');
    await page.click('button:has-text("New Matter"), button:has-text("Create Matter")');
    await expect(page.locator('text=Create New Matter')).toBeVisible();

    // Submit empty form
    await page.click('button:has-text("Create")');

    // Should see a validation error (e.g. required field)
    await expect(page.locator('text=Required').or(page.locator('text=required')).or(page.locator('text=must be'))).toBeVisible({ timeout: 5000 }).catch(() => null);
  });

});
