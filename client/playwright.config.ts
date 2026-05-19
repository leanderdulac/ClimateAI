import { defineConfig, devices } from '@playwright/test';

const appUrl = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:5173';
const useSystemChrome = process.env.PLAYWRIGHT_USE_SYSTEM_CHROME === '1';
const localChromeOnly = process.env.PLAYWRIGHT_LOCAL_CHROME_ONLY === '1';

const desktopChromeUse = {
  ...devices['Desktop Chrome'],
  ...(useSystemChrome
    ? {
        channel: 'chrome',
        launchOptions: {
          args: ['--no-sandbox'],
        },
      }
    : {}),
};

const accessibilityProject = {
  name: 'accessibility',
  testMatch: '**/a11y/**/*.test.ts',
  use: desktopChromeUse,
};

const chromiumProject = {
  name: 'chromium',
  use: desktopChromeUse,
  testMatch: '**/e2e/**/*.spec.ts',
};

const projects = localChromeOnly
  ? [accessibilityProject, chromiumProject]
  : [
      accessibilityProject,
      chromiumProject,
      {
        name: 'firefox',
        use: { ...devices['Desktop Firefox'] },
        testMatch: '**/e2e/**/*.spec.ts',
      },
      {
        name: 'webkit',
        use: { ...devices['Desktop Safari'] },
        testMatch: '**/e2e/**/*.spec.ts',
      },
      {
        name: 'Mobile Chrome',
        use: { ...devices['Pixel 5'] },
        testMatch: '**/e2e/**/*.spec.ts',
      },
      {
        name: 'Mobile Safari',
        use: { ...devices['iPhone 12'] },
        testMatch: '**/e2e/**/*.spec.ts',
      },
    ];

/**
 * Read environment variables from file.
 * https://github.com/motdotla/dotenv
 */
// require('dotenv').config();

/**
 * See https://playwright.dev/docs/test-configuration.
 */
export default defineConfig({
  testDir: './tests',
  /* Run tests in files in parallel */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 1 : undefined,
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: 'html',
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: appUrl,
    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  /* Configure projects for major browsers */
  projects,

  /* Run your local dev server before starting the tests */
  webServer: {
    command: 'npm run dev -- --host 0.0.0.0 --port 5173',
    url: appUrl,
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
