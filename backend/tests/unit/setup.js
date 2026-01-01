/**
 * Jest Setup File
 * テスト実行前の共通設定
 */

// フェッチモックの設定
require('jest-fetch-mock').enableMocks();

// LocalStorageのモック
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  key: jest.fn(),
  length: 0
};
global.localStorage = localStorageMock;

// SessionStorageのモック
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  key: jest.fn(),
  length: 0
};
global.sessionStorage = sessionStorageMock;

// Window.locationのモック
delete window.location;
window.location = {
  href: '',
  pathname: '',
  search: '',
  hash: '',
  reload: jest.fn()
};

// Console警告を抑制（必要に応じて）
global.console = {
  ...console,
  // warn: jest.fn(),
  // error: jest.fn(),
};

// グローバルなカスタムマッチャー
expect.extend({
  toBeWithinRange(received, floor, ceiling) {
    const pass = received >= floor && received <= ceiling;
    if (pass) {
      return {
        message: () => `expected ${received} not to be within range ${floor} - ${ceiling}`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to be within range ${floor} - ${ceiling}`,
        pass: false,
      };
    }
  },
});

// 各テスト前のリセット
beforeEach(() => {
  // LocalStorageをクリア
  localStorageMock.getItem.mockClear();
  localStorageMock.setItem.mockClear();
  localStorageMock.removeItem.mockClear();
  localStorageMock.clear.mockClear();

  // SessionStorageをクリア
  sessionStorageMock.getItem.mockClear();
  sessionStorageMock.setItem.mockClear();
  sessionStorageMock.removeItem.mockClear();
  sessionStorageMock.clear.mockClear();

  // Fetchモックをリセット
  fetch.resetMocks();

  // DOMをクリア
  document.body.innerHTML = '';
  document.head.innerHTML = '';
});

// 各テスト後のクリーンアップ
afterEach(() => {
  jest.clearAllTimers();
});
