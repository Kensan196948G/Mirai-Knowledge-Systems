/**
 * @fileoverview date-formatter.js ユニットテスト
 *
 * webui/src/utils/date-formatter.js の全関数をテスト。
 * ESMモジュールをfs.readFileSync + evalで読み込み、
 * window.DateFormatter グローバルを経由して関数を検証する。
 *
 * @version 1.0.0
 */

const fs = require('fs');
const path = require('path');

// ----------------------------------------------------------------
// グローバルモック設定（eval前に設定必須）
// ----------------------------------------------------------------

// loggerモック（ESMモジュール内の import { logger } を置き換え）
global.logger = {
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
  debug: jest.fn()
};

// date-formatter.js を読み込み、import文を除去してeval
const dateFormatterPath = path.join(
  __dirname,
  '../../../webui/src/utils/date-formatter.js'
);
let dateFormatterCode = fs.readFileSync(dateFormatterPath, 'utf8');

// ESM import文を除去（loggerはglobal.loggerでモック済み）
dateFormatterCode = dateFormatterCode.replace(
  /^import\s+.*?;?\s*$/gm,
  '// [import removed for test]'
);
// export function/const/let/var/async を export なしに変換
dateFormatterCode = dateFormatterCode.replace(
  /^export\s+(?=function|async\s+function|class|const|let|var)/gm,
  ''
);
// export default を削除
dateFormatterCode = dateFormatterCode.replace(/^export\s+default\s+/gm, '');
// export { ... } ブロックを削除
dateFormatterCode = dateFormatterCode.replace(
  /^export\s*\{[^}]*\}\s*;?\s*$/gm,
  '// [export block removed]'
);

// logger参照を global.logger に変換
dateFormatterCode = dateFormatterCode.replace(
  /\blogger\.info\b/g,
  'global.logger.info'
);

eval(dateFormatterCode);

// ----------------------------------------------------------------
// テスト: formatDate
// ----------------------------------------------------------------

describe('DateFormatter.formatDate', () => {
  test('有効なISO日付文字列をYYYY/MM/DD形式でフォーマットする', () => {
    const result = window.DateFormatter.formatDate('2026-01-31T12:00:00Z');
    // ロケール依存のため含有チェック
    expect(result).toMatch(/2026/);
    expect(result).toMatch(/01/);
    expect(result).toMatch(/31/);
  });

  test('Dateオブジェクトを正しくフォーマットする', () => {
    const date = new Date(2026, 0, 15); // 2026-01-15 ローカル時刻
    const result = window.DateFormatter.formatDate(date);
    expect(result).toMatch(/2026/);
    expect(result).toMatch(/01/);
    expect(result).toMatch(/15/);
  });

  test('nullを渡すとInvalid Dateを返す', () => {
    expect(window.DateFormatter.formatDate(null)).toBe('Invalid Date');
  });

  test('undefinedを渡すとInvalid Dateを返す', () => {
    expect(window.DateFormatter.formatDate(undefined)).toBe('Invalid Date');
  });

  test('空文字列を渡すとInvalid Dateを返す', () => {
    expect(window.DateFormatter.formatDate('')).toBe('Invalid Date');
  });

  test('無効な日付文字列を渡すとInvalid Dateを返す', () => {
    expect(window.DateFormatter.formatDate('not-a-date')).toBe('Invalid Date');
  });

  test('window.formatDate エイリアスが利用可能', () => {
    const result = window.formatDate('2026-03-03T00:00:00Z');
    expect(result).toMatch(/2026/);
  });
});

// ----------------------------------------------------------------
// テスト: formatDateTime
// ----------------------------------------------------------------

describe('DateFormatter.formatDateTime', () => {
  test('有効なISO日付時刻を日本語形式でフォーマットする', () => {
    const result = window.DateFormatter.formatDateTime('2026-01-31T09:30:00');
    expect(result).toMatch(/2026/);
    expect(result).toMatch(/01/);
    expect(result).toMatch(/31/);
    // 時刻部分の存在確認
    expect(result.length).toBeGreaterThan(10);
  });

  test('nullを渡すとInvalid Dateを返す', () => {
    expect(window.DateFormatter.formatDateTime(null)).toBe('Invalid Date');
  });

  test('undefinedを渡すとInvalid Dateを返す', () => {
    expect(window.DateFormatter.formatDateTime(undefined)).toBe('Invalid Date');
  });

  test('無効な日付文字列を渡すとInvalid Dateを返す', () => {
    expect(window.DateFormatter.formatDateTime('bad-date')).toBe('Invalid Date');
  });
});

// ----------------------------------------------------------------
// テスト: formatRelativeTime
// ----------------------------------------------------------------

describe('DateFormatter.formatRelativeTime', () => {
  test('30秒前は「たった今」を返す', () => {
    const date = new Date(Date.now() - 30 * 1000);
    expect(window.DateFormatter.formatRelativeTime(date)).toBe('たった今');
  });

  test('1分前を「1分前」でフォーマットする', () => {
    const date = new Date(Date.now() - 61 * 1000);
    const result = window.DateFormatter.formatRelativeTime(date);
    expect(result).toMatch(/\d+分前/);
  });

  test('1時間前を「1時間前」でフォーマットする', () => {
    const date = new Date(Date.now() - 61 * 60 * 1000);
    const result = window.DateFormatter.formatRelativeTime(date);
    expect(result).toMatch(/1時間前/);
  });

  test('1日前を「1日前」でフォーマットする', () => {
    const date = new Date(Date.now() - 25 * 60 * 60 * 1000);
    const result = window.DateFormatter.formatRelativeTime(date);
    expect(result).toMatch(/1日前/);
  });

  test('7日以内の6日前を「6日前」でフォーマットする', () => {
    const date = new Date(Date.now() - 6 * 24 * 60 * 60 * 1000);
    const result = window.DateFormatter.formatRelativeTime(date);
    expect(result).toMatch(/6日前/);
  });

  test('7日を超えた場合は絶対日付を返す', () => {
    const date = new Date('2025-01-01T00:00:00Z');
    const result = window.DateFormatter.formatRelativeTime(date);
    // 7日超なので日付形式（例: 2025/01/01）を返す
    expect(result).toMatch(/2025/);
    expect(result).not.toMatch(/前/);
  });

  test('nullを渡すとInvalid Dateを返す', () => {
    expect(window.DateFormatter.formatRelativeTime(null)).toBe('Invalid Date');
  });

  test('無効な日付文字列を渡すとInvalid Dateを返す', () => {
    expect(window.DateFormatter.formatRelativeTime('invalid')).toBe('Invalid Date');
  });
});

// ----------------------------------------------------------------
// テスト: formatFileSize
// ----------------------------------------------------------------

describe('DateFormatter.formatFileSize', () => {
  test('0バイトを「0 Bytes」で返す', () => {
    expect(window.DateFormatter.formatFileSize(0)).toBe('0 Bytes');
  });

  test('1023バイトを「1023 Bytes」で返す', () => {
    expect(window.DateFormatter.formatFileSize(1023)).toBe('1023 Bytes');
  });

  test('1024バイトを「1 KB」で返す', () => {
    expect(window.DateFormatter.formatFileSize(1024)).toBe('1 KB');
  });

  test('1536バイトを「1.5 KB」で返す', () => {
    expect(window.DateFormatter.formatFileSize(1536)).toBe('1.5 KB');
  });

  test('1048576バイト（1MB）を「1 MB」で返す', () => {
    expect(window.DateFormatter.formatFileSize(1048576)).toBe('1 MB');
  });

  test('1073741824バイト（1GB）を「1 GB」で返す', () => {
    expect(window.DateFormatter.formatFileSize(1073741824)).toBe('1 GB');
  });

  test('nullを渡すと「0 Bytes」を返す', () => {
    expect(window.DateFormatter.formatFileSize(null)).toBe('0 Bytes');
  });

  test('NaNを渡すと「0 Bytes」を返す', () => {
    expect(window.DateFormatter.formatFileSize(NaN)).toBe('0 Bytes');
  });
});

// ----------------------------------------------------------------
// テスト: formatDuration
// ----------------------------------------------------------------

describe('DateFormatter.formatDuration', () => {
  test('0秒を「0秒」で返す', () => {
    expect(window.DateFormatter.formatDuration(0)).toBe('0秒');
  });

  test('45秒を「45秒」で返す', () => {
    expect(window.DateFormatter.formatDuration(45)).toBe('45秒');
  });

  test('90秒を「1分30秒」で返す', () => {
    expect(window.DateFormatter.formatDuration(90)).toBe('1分30秒');
  });

  test('3600秒を「1時間」で返す', () => {
    expect(window.DateFormatter.formatDuration(3600)).toBe('1時間');
  });

  test('3661秒を「1時間1分1秒」で返す', () => {
    expect(window.DateFormatter.formatDuration(3661)).toBe('1時間1分1秒');
  });

  test('7200秒を「2時間」で返す', () => {
    expect(window.DateFormatter.formatDuration(7200)).toBe('2時間');
  });

  test('nullを渡すと「0秒」を返す', () => {
    expect(window.DateFormatter.formatDuration(null)).toBe('0秒');
  });

  test('負の値を渡すと「0秒」を返す', () => {
    expect(window.DateFormatter.formatDuration(-10)).toBe('0秒');
  });

  test('NaNを渡すと「0秒」を返す', () => {
    expect(window.DateFormatter.formatDuration(NaN)).toBe('0秒');
  });
});

// ----------------------------------------------------------------
// テスト: isToday
// ----------------------------------------------------------------

describe('DateFormatter.isToday', () => {
  test('今日の日付でtrueを返す', () => {
    expect(window.DateFormatter.isToday(new Date())).toBe(true);
  });

  test('今日の深夜0時でtrueを返す', () => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    expect(window.DateFormatter.isToday(today)).toBe(true);
  });

  test('昨日の日付でfalseを返す', () => {
    const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000);
    expect(window.DateFormatter.isToday(yesterday)).toBe(false);
  });

  test('過去の日付文字列でfalseを返す', () => {
    expect(window.DateFormatter.isToday('2020-01-01T00:00:00')).toBe(false);
  });

  test('nullを渡すとfalseを返す', () => {
    expect(window.DateFormatter.isToday(null)).toBe(false);
  });

  test('undefinedを渡すとfalseを返す', () => {
    expect(window.DateFormatter.isToday(undefined)).toBe(false);
  });

  test('無効な日付文字列でfalseを返す', () => {
    expect(window.DateFormatter.isToday('not-a-date')).toBe(false);
  });
});

// ----------------------------------------------------------------
// テスト: isPast
// ----------------------------------------------------------------

describe('DateFormatter.isPast', () => {
  test('過去の日付でtrueを返す', () => {
    expect(window.DateFormatter.isPast('2020-01-01T00:00:00')).toBe(true);
  });

  test('未来の日付でfalseを返す', () => {
    const future = new Date(Date.now() + 3600 * 1000);
    expect(window.DateFormatter.isPast(future)).toBe(false);
  });

  test('nullを渡すとfalseを返す', () => {
    expect(window.DateFormatter.isPast(null)).toBe(false);
  });

  test('undefinedを渡すとfalseを返す', () => {
    expect(window.DateFormatter.isPast(undefined)).toBe(false);
  });

  test('無効な日付文字列でfalseを返す', () => {
    expect(window.DateFormatter.isPast('invalid-date')).toBe(false);
  });
});

// ----------------------------------------------------------------
// テスト: toISOStringLocal
// ----------------------------------------------------------------

describe('DateFormatter.toISOStringLocal', () => {
  test('ISO 8601形式の文字列を返す', () => {
    const result = window.DateFormatter.toISOStringLocal(new Date(2026, 0, 31, 12, 0, 0));
    // +HH:MM または -HH:MM のタイムゾーンオフセットを含む
    expect(result).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{2}:\d{2}$/);
  });

  test('引数なしでも現在時刻のISO文字列を返す', () => {
    const result = window.DateFormatter.toISOStringLocal();
    expect(result).toMatch(/^\d{4}-\d{2}-\d{2}T/);
  });
});

// ----------------------------------------------------------------
// テスト: window.DateFormatter グローバル公開確認
// ----------------------------------------------------------------

describe('DateFormatter グローバル公開', () => {
  test('window.DateFormatter が定義されている', () => {
    expect(window.DateFormatter).toBeDefined();
  });

  test('window.DateFormatter.formatDate が関数である', () => {
    expect(typeof window.DateFormatter.formatDate).toBe('function');
  });

  test('window.DateFormatter.formatDateTime が関数である', () => {
    expect(typeof window.DateFormatter.formatDateTime).toBe('function');
  });

  test('window.DateFormatter.formatRelativeTime が関数である', () => {
    expect(typeof window.DateFormatter.formatRelativeTime).toBe('function');
  });

  test('window.DateFormatter.formatFileSize が関数である', () => {
    expect(typeof window.DateFormatter.formatFileSize).toBe('function');
  });

  test('window.DateFormatter.formatDuration が関数である', () => {
    expect(typeof window.DateFormatter.formatDuration).toBe('function');
  });

  test('window.DateFormatter.isToday が関数である', () => {
    expect(typeof window.DateFormatter.isToday).toBe('function');
  });

  test('window.DateFormatter.isPast が関数である', () => {
    expect(typeof window.DateFormatter.isPast).toBe('function');
  });

  test('window.DateFormatter.toISOStringLocal が関数である', () => {
    expect(typeof window.DateFormatter.toISOStringLocal).toBe('function');
  });

  test('window.formatDate エイリアスが関数である', () => {
    expect(typeof window.formatDate).toBe('function');
  });
});
