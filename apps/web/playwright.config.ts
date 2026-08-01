import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'MESA_LAW_ENVIRONMENT=test MESA_LAW_E2E_STUB=1 NEXTAUTH_SECRET=law-side-e2e-only-secret NEXT_TELEMETRY_DISABLED=1 pnpm run build && MESA_LAW_ENVIRONMENT=test MESA_LAW_E2E_STUB=1 NEXTAUTH_SECRET=law-side-e2e-only-secret NEXT_TELEMETRY_DISABLED=1 pnpm run start',
    url: 'http://localhost:3000',
    reuseExistingServer: false,
    timeout: 180000,
  },
});
