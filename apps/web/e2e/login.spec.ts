import { test, expect } from '@playwright/test';

test.describe('Login Page', () => {
  test('should render the login page correctly', async ({ page }) => {
    await page.goto('/login');
    
    // Check if the logo and title are visible
    await expect(page.locator('text=Welcome to MESA Law')).toBeVisible();
    await expect(page.locator('text=Enterprise Legal Operating System')).toBeVisible();
    
    // Check for the sign-in button
    const signInBtn = page.locator('button:has-text("Sign in with MESA")');
    await expect(signInBtn).toBeVisible();
    await expect(signInBtn).toBeEnabled();
  });
});
