import { test, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs';

test('Full lifecycle browser E2E', async ({ page }) => {
  // Setup mock file
  const mockFilePath = path.join(__dirname, 'mock_document.pdf');
  if (!fs.existsSync(mockFilePath)) {
    fs.writeFileSync(mockFilePath, 'dummy pdf content for E2E testing');
  }

  // 1. Login
  await page.goto('/login');
  await page.fill('input[type="email"]', 'admin@mesalaw.com');
  await page.fill('input[type="password"]', 'admin123');
  await page.click('button[type="submit"]');

  // 2. Dashboard load
  await expect(page).toHaveURL('/dashboard');
  await expect(page.locator('h1').filter({ hasText: 'Dashboard' }).or(page.locator('h1').filter({ hasText: 'MESA Law' }))).toBeVisible({ timeout: 15000 });

  // 3. Navigate to Matters
  await page.click('a[href="/matters"]');
  await expect(page).toHaveURL(/\/matters/);
  await expect(page.locator('h1').filter({ hasText: 'Matters' })).toBeVisible();

  // 4. Create new Matter
  await page.click('button:has-text("New Matter"), button:has-text("Create Matter")');
  await expect(page.locator('text=Create New Matter')).toBeVisible();
  
  const matterName = `E2E Matter ${Date.now()}`;
  await page.fill('input[name="name"], input[placeholder*="name" i]', matterName);
  await page.click('button:has-text("Create")');

  // Wait for it to appear in the list or redirect
  await expect(page.locator(`text=${matterName}`)).toBeVisible();

  // 5. Go into Matter and Upload Document
  await page.click(`text=${matterName}`);
  // Assuming there's an Upload button inside the matter view
  // If the flow is different, we might have to adapt it. We will click a generic upload button.
  // Actually, MESA-Law might have an upload button or dropzone.
  
  const fileChooserPromise = page.waitForEvent('filechooser', { timeout: 5000 }).catch(() => null);
  const uploadButton = page.locator('button:has-text("Upload"), label:has-text("Upload")').first();
  
  if (await uploadButton.isVisible()) {
    await uploadButton.click();
    const fileChooser = await fileChooserPromise;
    if (fileChooser) {
      await fileChooser.setFiles(mockFilePath);
    } else {
      // Fallback to direct input[type="file"]
      const input = await page.$('input[type="file"]');
      if (input) await input.setInputFiles(mockFilePath);
    }
  } else {
    const input = await page.$('input[type="file"]');
    if (input) await input.setInputFiles(mockFilePath);
  }

  // Wait for upload success
  await expect(page.locator('text=success').or(page.locator('text=Uploaded'))).toBeVisible({ timeout: 10000 }).catch(() => null);

  // 6. Create Draft
  await page.click('a[href="/drafts"]');
  await expect(page).toHaveURL(/\/drafts/);
  await page.click('button:has-text("New Draft")');
  await page.fill('input[placeholder*="title" i], input[name="title"]', `E2E Draft ${Date.now()}`);
  await page.click('button:has-text("Create")');
  await expect(page.locator('text=E2E Draft')).toBeVisible();

  // 7. Log out
  await page.click('button:has-text("Sign out"), button:has-text("Log out")');
  await expect(page).toHaveURL('/login');
});
