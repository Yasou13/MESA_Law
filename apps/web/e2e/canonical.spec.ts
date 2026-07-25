import { test, expect } from '@playwright/test';

test('canonical workflow: login -> matter -> upload -> view', async ({ page }) => {
  page.on('console', msg => console.log('BROWSER LOG:', msg.text()));
  page.on('requestfailed', request => console.log('FAILED REQUEST:', request.url(), request.failure()?.errorText));
  page.on('response', response => {
    if (!response.ok()) {
      console.log('BAD RESPONSE:', response.url(), response.status());
    }
  });

  // 1. Login
  await page.goto('/login');
  await page.fill('input[type="text"]', 'e2e-tenant-123');
  await page.click('button:has-text("Sign In")');
  
  // 2. Matter List & Create
  await expect(page).toHaveURL('/matters');
  
  const matterTitle = `Test Matter ${Date.now()}`;
  await page.fill('input[placeholder="e.g. Smith vs. Johnson"]', matterTitle);
  await page.click('button:has-text("Create")');
  
  // Wait for the new matter to appear and click it
  await expect(page.locator(`text=${matterTitle}`)).toBeVisible();
  await page.click(`text=${matterTitle}`);
  
  // 3. Matter Detail & Upload
  await expect(page).toHaveURL(/\/matters\/[0-9a-fA-F-]+/);
  await expect(page.locator('h1')).toContainText('Matter');
  
  // Upload a file
  const buffer = Buffer.from('%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Resources <<>>\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n199\n%%EOF');
  
  // file input is hidden or we can just set files directly
  await page.setInputFiles('input[type="file"]', {
    name: 'test-doc.pdf',
    mimeType: 'application/pdf',
    buffer: buffer
  });
  
  await page.click('button:has-text("Upload")');
  
  // Verify upload success
  await expect(page.locator('text=Upload complete!')).toBeVisible({ timeout: 15000 });
  await expect(page.locator('text=test-doc.pdf')).toBeVisible();
});
