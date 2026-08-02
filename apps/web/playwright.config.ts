import { defineConfig, devices } from '@playwright/test';

const visualViewports = [
  { name: '1440x900', width: 1440, height: 900 },
  { name: '1280x800', width: 1280, height: 800 },
  { name: '1024x768', width: 1024, height: 768 },
  { name: '768x1024', width: 768, height: 1024 },
] as const;

const visualProjects = visualViewports.flatMap((viewport) =>
  (['light', 'dark'] as const).map((theme) => ({
    name: `visual-${viewport.name}-${theme}`,
    grep: /@visual/,
    metadata: { theme, viewport: viewport.name },
    use: {
      ...devices['Desktop Chrome'],
      colorScheme: theme,
      viewport: { width: viewport.width, height: viewport.height },
    },
  })),
);

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: 'html',
  snapshotPathTemplate: '{testDir}/__screenshots__/{testFilePath}/{projectName}/{arg}{ext}',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium-functional',
      grepInvert: /@visual/,
      use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } },
    },
    ...visualProjects,
  ],
  webServer: {
    command: 'MESA_LAW_ENVIRONMENT=test MESA_LAW_E2E_STUB=1 NEXTAUTH_SECRET=law-side-e2e-only-secret NEXT_TELEMETRY_DISABLED=1 pnpm run build && MESA_LAW_ENVIRONMENT=test MESA_LAW_E2E_STUB=1 NEXTAUTH_SECRET=law-side-e2e-only-secret NEXT_TELEMETRY_DISABLED=1 pnpm run start',
    url: 'http://localhost:3000',
    reuseExistingServer: false,
    timeout: 180000,
  },
});
