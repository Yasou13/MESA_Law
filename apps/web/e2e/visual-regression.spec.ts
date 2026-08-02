import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Page, type TestInfo } from '@playwright/test'

import {
  installVisualFixture,
  visualDocumentId,
  visualMatterId,
  visualRevisionId,
} from './support/visual-fixture'

type VisualTheme = 'light' | 'dark'

function projectTheme(testInfo: TestInfo): VisualTheme {
  const theme = testInfo.project.metadata.theme
  if (theme !== 'light' && theme !== 'dark') throw new Error(`Missing visual theme metadata for ${testInfo.project.name}`)
  return theme
}

async function assertNoBodyOverflow(page: Page) {
  const dimensions = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }))
  expect(dimensions.scrollWidth, `body overflow: ${JSON.stringify(dimensions)}`).toBeLessThanOrEqual(dimensions.clientWidth + 1)
}

async function assertShellMode(page: Page) {
  const viewport = page.viewportSize()
  if (!viewport) throw new Error('Visual project must define a viewport')

  const desktopSidebar = page.getByTestId('desktop-sidebar')
  const mobileButton = page.getByTestId('mobile-menu-button')
  if (viewport.width >= 1024) {
    await expect(desktopSidebar).toBeVisible()
    await expect(mobileButton).toBeHidden()
    const width = (await desktopSidebar.boundingBox())?.width
    expect(width).toBe(viewport.width >= 1280 ? 256 : 72)
  } else {
    await expect(desktopSidebar).toBeHidden()
    await expect(mobileButton).toBeVisible()
  }
}

async function assertA11y(page: Page, testInfo: TestInfo) {
  if (!['visual-1440x900-light', 'visual-1440x900-dark'].includes(testInfo.project.name)) return
  const scan = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
    .analyze()
  const blocking = scan.violations.filter((violation) => violation.impact === 'serious' || violation.impact === 'critical')
  expect(blocking, blocking.map((violation) => `${violation.id}: ${violation.help} (${violation.nodes.length})`).join('\n')).toEqual([])
}

async function capture(page: Page, testInfo: TestInfo, name: string) {
  await page.evaluate(() => document.fonts.ready)
  await assertNoBodyOverflow(page)
  await assertA11y(page, testInfo)
  await expect(page).toHaveScreenshot(`${name}.png`, {
    animations: 'disabled',
    caret: 'hide',
    maxDiffPixelRatio: 0.001,
  })
}

test.beforeEach(async ({ page }, testInfo) => {
  await page.emulateMedia({ reducedMotion: 'reduce', colorScheme: projectTheme(testInfo) })
  await installVisualFixture(page, projectTheme(testInfo))
})

test('@visual dashboard priority workspace', async ({ page }, testInfo) => {
  await page.goto('/tr/dashboard')
  await expect(page.getByRole('heading', { name: 'Gösterge Paneli', level: 1 })).toBeVisible()
  await assertShellMode(page)
  await capture(page, testInfo, 'dashboard')
})

test('@visual matter list data table', async ({ page }, testInfo) => {
  await page.goto('/tr/matters')
  await expect(page.getByRole('heading', { name: 'Dosyalar', level: 1 })).toBeVisible()
  await expect(page.getByTestId('data-table-scroll')).toBeVisible()
  await capture(page, testInfo, 'matter-list')
})

test('@visual matter overview and url navigation', async ({ page }, testInfo) => {
  await page.goto(`/tr/matters/${visualMatterId}`)
  await expect(page.getByRole('heading', { name: 'Artemis Enerji tedarik uyuşmazlığı', level: 1 })).toBeVisible()
  const tabs = page.getByTestId('matter-tabs')
  await expect(tabs).toBeVisible()
  await expect(tabs.getByRole('link', { name: 'Genel Bakış' })).toHaveAttribute('aria-current', 'page')
  await capture(page, testInfo, 'matter-detail')
})

test('@visual canonical document center', async ({ page }, testInfo) => {
  await page.goto('/tr/documents')
  await expect(page.getByRole('heading', { name: 'Belge Merkezi', level: 1 })).toBeVisible()
  await expect(page.getByText('Ana Tedarik Sözleşmesi — imzalı.pdf')).toBeVisible()
  await expect(page.getByTestId('data-table-scroll')).toBeVisible()
  await capture(page, testInfo, 'documents')
})

test('@visual source aware document viewer', async ({ page }, testInfo) => {
  const query = new URLSearchParams({
    revision: visualRevisionId,
    page: '1',
    chunk: 'chunk-visual-1',
    start: '0',
    end: '66',
  })
  await page.goto(`/tr/documents/${visualDocumentId}?${query.toString()}`)
  await expect(page.getByRole('heading', { name: 'Ana Tedarik Sözleşmesi — imzalı.pdf', level: 1 })).toBeVisible()
  await expect(page.getByTestId('viewer-document').locator('canvas')).toBeVisible({ timeout: 30_000 })

  const viewport = page.viewportSize()
  const pagesBox = await page.getByTestId('viewer-pages').boundingBox()
  const documentBox = await page.getByTestId('viewer-document').boundingBox()
  const sourceBox = await page.getByTestId('viewer-source').boundingBox()
  if (!viewport || !pagesBox || !documentBox || !sourceBox) throw new Error('Viewer panels must be measurable')
  if (viewport.width >= 1280) {
    expect(pagesBox.x).toBeLessThan(documentBox.x)
    expect(documentBox.x).toBeLessThan(sourceBox.x)
  } else {
    expect(pagesBox.y).toBeLessThan(documentBox.y)
    expect(documentBox.y).toBeLessThan(sourceBox.y)
  }
  await capture(page, testInfo, 'document-viewer')
})

test('@visual fail closed review center', async ({ page }, testInfo) => {
  await page.goto('/tr/reviews')
  await expect(page.getByRole('heading', { name: 'İnceleme Merkezi', level: 1 })).toBeVisible()
  await expect(page.getByText('Artemis Enerji, Fatura 2026/42 bedelini 30 gün içinde ödemelidir.')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Onayla', exact: true })).toBeEnabled()
  await capture(page, testInfo, 'review-center')
})

test('@visual sourced ask mesa result', async ({ page }, testInfo) => {
  await page.goto(`/tr/matters/${visualMatterId}/qa`)
  await expect(page.getByRole('heading', { name: 'Ask MESA', level: 1 })).toBeVisible()
  await page.getByLabel('Sorunuz').fill('Sözleşmedeki doğrulanmış ödeme yükümlülüğü nedir?')
  await page.getByRole('button', { name: 'Kaynaklarda ara' }).click()
  await expect(page.getByText('Ana sözleşmeye göre Fatura 2026/42 bedeli 30 gün içinde ödenmelidir.')).toBeVisible()
  await expect(page.getByText('Kaynak eşleşme skoru 0.940')).toBeVisible()
  await capture(page, testInfo, 'ask-mesa')
})

test('@visual grouped operations workspace', async ({ page }, testInfo) => {
  await page.goto('/tr/operations')
  await expect(page.getByRole('heading', { name: 'Operasyonlar', level: 1 })).toBeVisible()
  await expect(page.getByTestId('data-table-scroll')).toBeVisible()
  await page.getByRole('row', { name: /DOCUMENT SCAN/ }).getByRole('button', { name: 'Ayrıntıları aç' }).click()
  await expect(page.getByText('ClamAV tarama servisi yanıt vermedi; iş terminal duruma alındı.')).toBeVisible()
  await capture(page, testInfo, 'operations')
})
