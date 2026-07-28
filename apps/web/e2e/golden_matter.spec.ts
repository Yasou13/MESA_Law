import { test, expect } from '@playwright/test';

test('Golden Matter E2E: Full Lifecycle User Journey', async ({ page }) => {
  page.on('console', msg => console.log('BROWSER LOG:', msg.text()));

  // 1. Login
  await page.goto('/login');
  await page.fill('input[type="text"]', 'e2e-tenant-123');
  await page.click('button:has-text("Sign In")');
  await expect(page).toHaveURL(/\/matters/);

  // 2. Matter List & Create
  const matterTitle = `Golden Matter ${Date.now()}`;
  await page.fill('input[placeholder="New matter title..."]', matterTitle);
  await page.click('button:has-text("Create")');
  
  // Wait for the new matter to appear and click it
  await expect(page.locator(`text=${matterTitle}`)).toBeVisible();
  await page.click(`text=${matterTitle}`);
  
  // 3. Matter Detail & Upload Document
  await expect(page).toHaveURL(/\/matters\/[0-9a-fA-F-]+/);
  await expect(page.locator('h1')).toContainText('Matter');
  
  const buffer = Buffer.from('%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Resources <<>>\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n199\n%%EOF');
  await page.setInputFiles('input[type="file"]', {
    name: 'golden-contract.pdf',
    mimeType: 'application/pdf',
    buffer: buffer
  });
  
  await expect(page.locator('text=golden-contract.pdf')).toBeVisible({ timeout: 15000 });

  // 4. Navigate to Matter Review Center
  await page.goto(page.url() + '/reviews');
  await expect(page.locator('h1').filter({ hasText: 'Review Center' })).toBeVisible();

  // 5. Navigate to Global Reviews
  await page.goto('/reviews');
  await expect(page.locator('h1').filter({ hasText: 'Global Review Center' })).toBeVisible();
});
