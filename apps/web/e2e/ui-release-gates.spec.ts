import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'

import { expect, test, type Page } from '@playwright/test'

import {
  installVisualFixture,
  visualDocumentId,
  visualMatterId,
  visualRevisionId,
} from './support/visual-fixture'

async function pageDoesNotOverflow(page: Page) {
  const sizes = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }))
  expect(sizes.scrollWidth, JSON.stringify(sizes)).toBeLessThanOrEqual(sizes.clientWidth + 1)
}

test.beforeEach(async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'light', reducedMotion: 'reduce' })
  await installVisualFixture(page, 'light')
})

test('keyboard command menu and create dialog trap focus and close with Escape', async ({ page }) => {
  const runtimeErrors: string[] = []
  page.on('pageerror', (error) => runtimeErrors.push(error.message))
  await page.goto('/tr/dashboard')
  const commandTrigger = page.getByRole('button', { name: 'Komut menüsünü aç' })
  await expect(commandTrigger).toBeVisible()
  await commandTrigger.focus()
  await page.keyboard.press('Enter')
  await page.waitForTimeout(250)
  expect(runtimeErrors, 'Opening the command menu must not crash the React tree').toEqual([])
  const commandDialog = page.locator('[data-slot="dialog-content"]')
  await expect(commandDialog).toBeVisible()
  await expect(commandDialog.locator('[data-slot="command-input"]')).toBeFocused()
  await page.keyboard.press('Shift+Tab')
  await expect(commandDialog).toContainText('Firma ayarları')
  expect(await commandDialog.evaluate((dialog) => dialog.contains(document.activeElement))).toBe(true)
  await page.keyboard.press('Escape')
  await expect(commandDialog).toBeHidden()

  await page.goto('/tr/matters')
  await page.getByRole('button', { name: 'Yeni dosya' }).focus()
  await page.keyboard.press('Enter')
  const createDialog = page.getByRole('dialog', { name: 'Yeni dosya oluştur' })
  await expect(createDialog).toBeVisible()
  expect(await createDialog.evaluate((dialog) => dialog.contains(document.activeElement))).toBe(true)
  await page.keyboard.press('Escape')
  await expect(createDialog).toBeHidden()
})

test('390px drawer traps focus, restores trigger and prevents page overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/tr/dashboard')
  const trigger = page.getByTestId('mobile-menu-button')
  await trigger.focus()
  await page.keyboard.press('Enter')
  const drawer = page.getByTestId('mobile-navigation')
  await expect(drawer).toBeVisible()
  expect(await drawer.evaluate((dialog) => dialog.contains(document.activeElement))).toBe(true)
  await page.keyboard.press('Shift+Tab')
  expect(await drawer.evaluate((dialog) => dialog.contains(document.activeElement))).toBe(true)
  await page.keyboard.press('Escape')
  await expect(drawer).toBeHidden()
  await expect(trigger).toBeFocused()
  await pageDoesNotOverflow(page)

  for (const route of [
    `/tr/matters/${visualMatterId}`,
    '/tr/documents',
    '/tr/reviews',
    '/tr/operations',
  ]) {
    await page.goto(route)
    await expect(page.locator('#main-content')).toBeVisible()
    await pageDoesNotOverflow(page)
  }
  await expect(page.getByTestId('mobile-menu-button')).toBeVisible()
})

test('DataTable and source workspaces expose keyboard-operable controls', async ({ page }) => {
  await page.goto('/tr/matters')
  const sortButton = page.getByRole('button', { name: 'Dosya adı' })
  await sortButton.focus()
  await page.keyboard.press('Enter')
  await expect(sortButton).toBeFocused()
  await expect(page.getByTestId('data-table-scroll')).toBeVisible()

  await page.goto('/tr/reviews')
  await expect(page.getByRole('button', { name: 'Onayla', exact: true })).toBeEnabled()
  const sourceLink = page.getByRole('link', { name: 'Kaynakta aç' })
  await sourceLink.focus()
  await expect(sourceLink).toBeFocused()
  const sourceHref = await sourceLink.getAttribute('href')
  expect(sourceHref).toContain(`documents/${visualDocumentId}`)
  expect(sourceHref).toContain(`revision=${visualRevisionId}`)

  await page.goto(`/tr/documents/${visualDocumentId}?revision=${visualRevisionId}&page=1&chunk=chunk-visual-1&start=0&end=66`)
  await expect(page.getByTestId('viewer-document').locator('canvas')).toBeVisible({ timeout: 30_000 })
  await expect(page.getByRole('button', { name: 'Önceki sayfa' })).toBeDisabled()
  await expect(page.getByRole('button', { name: 'Sonraki sayfa' })).toBeDisabled()
  await page.getByRole('button', { name: 'Sayfa 1' }).focus()
  await expect(page.getByRole('button', { name: 'Sayfa 1' })).toBeFocused()
})

test('reduced motion leaves no running ambient animation', async ({ page }) => {
  await page.goto('/tr/dashboard')
  await expect(page.getByRole('heading', { name: 'Gösterge Paneli' })).toBeVisible()
  const runningAnimations = await page.evaluate(() =>
    document.getAnimations().filter((animation) => animation.playState === 'running').length,
  )
  expect(runningAnimations).toBe(0)
})

test('PDF.js remains route-lazy and key views keep CLS within budget', async ({ page }, testInfo) => {
  const manifestPath = resolve(process.cwd(), '.next/react-loadable-manifest.json')
  const manifest = JSON.parse(await readFile(manifestPath, 'utf8')) as Record<string, { files: string[] }>
  const pdfEntry = Object.entries(manifest).find(([key]) => key.includes('PdfDocumentSurface'))
  expect(pdfEntry, 'PdfDocumentSurface must remain a route-level dynamic import').toBeTruthy()
  const pdfChunks = pdfEntry?.[1].files ?? []
  expect(pdfChunks.length).toBeGreaterThan(0)

  const requested = new Set<string>()
  page.on('request', (request) => requested.add(request.url()))
  const dashboardStart = Date.now()
  await page.goto('/tr/dashboard')
  await expect(page.getByRole('heading', { name: 'Gösterge Paneli' })).toBeVisible()
  const dashboardMs = Date.now() - dashboardStart
  expect(pdfChunks.some((chunk) => [...requested].some((url) => url.includes(chunk)))).toBe(false)
  const dashboardCls = await page.evaluate(() => window.__mesaCls)
  expect(dashboardCls).toBeLessThanOrEqual(0.1)

  const viewerStart = Date.now()
  await page.goto(`/tr/documents/${visualDocumentId}?revision=${visualRevisionId}&page=1&chunk=chunk-visual-1&start=0&end=66`)
  await expect(page.getByTestId('viewer-document').locator('canvas')).toBeVisible({ timeout: 30_000 })
  const viewerMs = Date.now() - viewerStart
  expect(pdfChunks.some((chunk) => [...requested].some((url) => url.includes(chunk)))).toBe(true)
  const viewerLayout = await page.evaluate(() => ({ cls: window.__mesaCls, entries: window.__mesaClsEntries }))
  const viewerCls = viewerLayout.cls
  expect(viewerCls, JSON.stringify(viewerLayout.entries, null, 2)).toBeLessThanOrEqual(0.1)

  const performanceSummary = { dashboard_ms: dashboardMs, viewer_ms: viewerMs, dashboard_cls: dashboardCls, viewer_cls: viewerCls }
  console.info(`[ui-performance] ${JSON.stringify(performanceSummary)}`)

  await testInfo.attach('ui-performance.json', {
    body: JSON.stringify(performanceSummary, null, 2),
    contentType: 'application/json',
  })
})
