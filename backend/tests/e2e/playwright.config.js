// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * Playwright Configuration for Mirai Knowledge System
 * Browser & Device Compatibility Testing
 *
 * @see https://playwright.dev/docs/test-configuration
 */
module.exports = defineConfig({
  testDir: './compatibility',

  /* 並列実行の最大ワーカー数 */
  fullyParallel: true,

  /* CI環境でのリトライ設定 */
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,

  /* CI環境ではワーカー数を制限 */
  workers: process.env.CI ? 1 : undefined,

  /* レポーター設定 */
  reporter: [
    ['html', { outputFolder: 'reports/playwright-html' }],
    ['json', { outputFile: 'reports/playwright-results.json' }],
    ['junit', { outputFile: 'reports/playwright-junit.xml' }],
    ['list']
  ],

  /* すべてのテストで共通の設定 */
  use: {
    /* ベースURL（環境変数で上書き可能） */
    baseURL: process.env.BASE_URL || 'http://127.0.0.1:5000',

    /* スクリーンショット設定 */
    screenshot: 'only-on-failure',

    /* ビデオ録画設定 */
    video: 'retain-on-failure',

    /* トレース設定 */
    trace: 'on-first-retry',

    /* タイムアウト設定 */
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },

  /* プロジェクト設定: 複数ブラウザ・デバイスでのテスト */
  projects: [
    /* === デスクトップブラウザ === */
    {
      name: 'chromium-desktop',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 }
      },
    },
    {
      name: 'firefox-desktop',
      use: {
        ...devices['Desktop Firefox'],
        viewport: { width: 1920, height: 1080 }
      },
    },
    {
      name: 'webkit-desktop',
      use: {
        ...devices['Desktop Safari'],
        viewport: { width: 1920, height: 1080 }
      },
    },
    {
      name: 'edge-desktop',
      use: {
        ...devices['Desktop Edge'],
        viewport: { width: 1920, height: 1080 },
        channel: 'msedge'
      },
    },

    /* === ノートPCサイズ === */
    {
      name: 'chromium-laptop',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1366, height: 768 }
      },
    },

    /* === タブレットデバイス === */
    {
      name: 'ipad-portrait',
      use: {
        ...devices['iPad Pro'],
        viewport: { width: 768, height: 1024 }
      },
    },
    {
      name: 'ipad-landscape',
      use: {
        ...devices['iPad Pro landscape'],
        viewport: { width: 1024, height: 768 }
      },
    },

    /* === モバイルデバイス === */
    {
      name: 'iphone-13',
      use: {
        ...devices['iPhone 13'],
        viewport: { width: 390, height: 844 }
      },
    },
    {
      name: 'iphone-se',
      use: {
        ...devices['iPhone SE'],
        viewport: { width: 375, height: 667 }
      },
    },
    {
      name: 'pixel-5',
      use: {
        ...devices['Pixel 5'],
        viewport: { width: 393, height: 851 }
      },
    },
    {
      name: 'galaxy-s9',
      use: {
        ...devices['Galaxy S9+'],
        viewport: { width: 360, height: 740 }
      },
    },
  ],

  /* ローカル開発サーバー設定（オプション） */
  webServer: process.env.NO_WEB_SERVER ? undefined : {
    command: 'python app.py',
    url: 'http://127.0.0.1:5000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
    cwd: '../..',
    shell: true,
  },

  /* グローバルタイムアウト */
  timeout: 60000,
  expect: {
    timeout: 10000
  },
});
