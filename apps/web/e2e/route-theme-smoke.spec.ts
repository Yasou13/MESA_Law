import { expect, test } from '@playwright/test'

import {
  installVisualFixture,
  visualDocumentId,
  visualMatterId,
  visualRevisionId,
} from './support/visual-fixture'

const routes = [
  '/tr/dashboard',
  '/tr/matters',
  `/tr/matters/${visualMatterId}`,
  `/tr/matters/${visualMatterId}/timeline`,
  `/tr/matters/${visualMatterId}/parties`,
  `/tr/matters/${visualMatterId}/documents`,
  `/tr/matters/${visualMatterId}/evidence`,
  `/tr/matters/${visualMatterId}/research`,
  `/tr/matters/${visualMatterId}/qa`,
  `/tr/matters/${visualMatterId}/reviews`,
  `/tr/matters/${visualMatterId}/operations`,
  '/tr/documents',
  `/tr/documents/${visualDocumentId}?revision=${visualRevisionId}&page=1&chunk=chunk-visual-1&start=0&end=66`,
  '/tr/reviews',
  '/tr/ask-mesa',
  '/tr/operations',
  '/tr/deadlines',
  '/tr/notifications',
  '/tr/settings/profile',
  '/tr/admin/members',
  '/tr/admin/audit',
  '/tr/admin/settings',
  '/tr/drafts',
  '/tr/drafts/draft-disabled',
] as const

for (const theme of ['light', 'dark'] as const) {
  test(`all 24 product routes render in ${theme} theme`, async ({ page }) => {
    await page.emulateMedia({ colorScheme: theme, reducedMotion: 'reduce' })
    await installVisualFixture(page, theme)

    for (const route of routes) {
      const response = await page.goto(route)
      expect(response?.status(), `${route} returned a document error`).toBeLessThan(400)
      expect(await page.locator('html').evaluate((element, expected) => element.classList.contains(expected), theme)).toBe(true)
      await expect(page.locator('#main-content')).toBeVisible()
      await expect(page.locator('nextjs-portal')).toHaveCount(0)
      const width = await page.evaluate(() => ({
        client: document.documentElement.clientWidth,
        scroll: document.documentElement.scrollWidth,
      }))
      expect(width.scroll, `${route} overflows in ${theme}`).toBeLessThanOrEqual(width.client + 1)
    }
  })
}
