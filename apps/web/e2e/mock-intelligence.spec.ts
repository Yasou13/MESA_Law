import { test, expect } from '@playwright/test';

test('mock intelligence UX interactions', async ({ page }) => {
  // Setup local storage directly to simulate logged-in state and bypass login page delay
  await page.goto('http://localhost:3000');
  await page.evaluate(() => {
    localStorage.setItem('tenant_id', 'e2e-tenant-123');
    localStorage.setItem('user_id', 'test-user-id');
  });

  // Navigate to matters page and click on a matter ID (or just go to matter 1)
  await page.goto('http://localhost:3000/matters/1');

  // Verify Overview tab is active by default
  await expect(page.locator('h1')).toContainText('Matter 1');
  await expect(page.locator('h2').filter({ hasText: 'Matter Q&A Assistant' })).toBeVisible();

  // Test Q&A Shell Mock
  const qInput = page.getByPlaceholder('Ask a question...');
  await qInput.fill('tazminat');
  await page.getByRole('button', { name: 'Send' }).click();

  // Verify AI response after mock delay
  await expect(page.getByText('kıdem tazminatı şartları oluşmuştur')).toBeVisible({ timeout: 5000 });
  await expect(page.getByText('Citations:')).toBeVisible();

  // Test Timeline Tab
  await page.getByRole('button', { name: 'Timeline' }).click();
  // Wait for loading to finish (1.5s delay)
  await expect(page.getByText('Chronological Timeline')).toBeVisible({ timeout: 5000 });
  await expect(page.getByText('İş sözleşmesi feshedildi')).toBeVisible();

  // Test Claims & Evidence Tab
  await page.getByRole('button', { name: 'Claims' }).click();
  await expect(page.getByText('Claims & Evidence')).toBeVisible({ timeout: 5000 });
  // Verify No-evidence wording
  await expect(page.getByText('No supporting evidence found in uploaded documents')).toBeVisible();
  // Verify Confidence Badges
  await expect(page.getByText('Confidence: high').first()).toBeVisible();

  // Test Research Tab
  await page.getByRole('button', { name: 'Research' }).click();
  await expect(page.getByText('Legal Research Workspace')).toBeVisible();
  
  const searchInput = page.getByPlaceholder('Search legislation');
  await searchInput.fill('iş kanunu');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  
  // Verify research results
  await expect(page.getByText('Türk Borçlar Kanunu')).toBeVisible({ timeout: 5000 });
  await expect(page.getByText('Match:').first()).toBeVisible();
});
