/**
 * Jest Configuration for Mirai Knowledge Systems Frontend Tests
 * @see https://jestjs.io/docs/configuration
 */

module.exports = {
  // テスト環境：JSDOM（ブラウザ環境のシミュレート）
  testEnvironment: 'jsdom',

  // テストファイルのパターン
  testMatch: [
    '**/tests/unit/**/*.test.js',
    '**/tests/unit/**/*.spec.js'
  ],

  // テスト対象外のパス
  testPathIgnorePatterns: [
    '/node_modules/',
    '/venv/',
    '/cache/',
    '/.pytest_cache/'
  ],

  // カバレッジ収集対象
  collectCoverageFrom: [
    '../webui/**/*.js',
    '!../webui/data/**',
    '!../webui/**/*.test.js',
    '!../webui/**/*.spec.js',
    '!**/node_modules/**',
    '!**/vendor/**'
  ],

  // カバレッジ出力ディレクトリ
  coverageDirectory: 'tests/coverage',

  // カバレッジレポートの形式
  coverageReporters: [
    'text',
    'text-summary',
    'html',
    'lcov',
    'json'
  ],

  // カバレッジ閾値（70%以上を目標）
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70
    }
  },

  // モジュール名のマッピング
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/../webui/$1'
  },

  // セットアップファイル
  setupFilesAfterEnv: ['<rootDir>/tests/unit/setup.js'],

  // テスト実行前のグローバル設定
  globals: {
    'NODE_ENV': 'test'
  },

  // 詳細なエラー出力
  verbose: true,

  // 並列実行の最大ワーカー数
  maxWorkers: '50%',

  // タイムアウト（ミリ秒）
  testTimeout: 10000,

  // 変換対象（トランスパイル不要なのでスキップ）
  transform: {},

  // モジュール解決オプション
  moduleFileExtensions: ['js', 'json'],

  // テストの前にクリア
  clearMocks: true,
  resetMocks: true,
  restoreMocks: true
};
