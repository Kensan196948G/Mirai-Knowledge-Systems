const { defineConfig, devices } = require('@playwright/test');

/**
 * Playwright Configuration for Mirai Knowledge Systems E2E Tests
 * @see https://playwright.dev/docs/test-configuration
 */
module.exports = defineConfig({
  testDir: './tests/e2e',

  // Maximum time one test can run for
  timeout: 120 * 1000,

  // Test configuration
  expect: {
    timeout: 10000,
  },

  // Run tests in files in parallel
  fullyParallel: false,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Reporter to use
  reporter: [
    ['html', { outputFolder: 'tests/reports/e2e-html' }],
    ['json', { outputFile: 'tests/reports/e2e-results.json' }],
    ['junit', { outputFile: 'tests/reports/e2e-junit.xml' }],
    ['list']
  ],

  // Shared settings for all projects
  use: {
    // Base URL for navigation
    baseURL: process.env.BASE_URL || 'http://localhost:8000',

    // Collect trace when retrying the failed test
    trace: 'retain-on-failure',

    // Take screenshot on failure
    screenshot: 'only-on-failure',

    // Video on failure
    video: 'retain-on-failure',

    // Browser context options
    viewport: { width: 1280, height: 720 },

    // Ignore HTTPS errors
    ignoreHTTPSErrors: true,

    // Default timeout for actions
    actionTimeout: 10000,
  },

  // Configure projects for major browsers
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // Add more browsers as needed
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],

  // Run local dev server before starting the tests
  webServer: process.env.SKIP_WEBSERVER ? undefined : {
    command: 'cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend && source venv/bin/activate && python -m uvicorn app_v2:app --host 0.0.0.0 --port 8000',
    port: 8000,
    timeout: 120 * 1000,
    reuseExistingServer: !process.env.CI,
    stdout: 'pipe',
    stderr: 'pipe',
  },

  // Global setup/teardown
  globalSetup: process.env.SKIP_SETUP ? undefined : './tests/e2e/global-setup.js',
});
