/**
 * @fileoverview 日付フォーマットユーティリティ
 *
 * 日付・時刻・相対時刻・ファイルサイズ・期間の
 * フォーマット関数を提供するESMモジュール。
 *
 * @module utils/date-formatter
 * @version 2.0.0
 * @author Mirai Knowledge Systems
 */

import { logger } from '../core/logger.js';

// ============================================================
// 日付フォーマット関数
// ============================================================

/**
 * 日付を日本語形式でフォーマット（YYYY/MM/DD）
 *
 * @param {string|Date|null} dateStr - 日付文字列またはDateオブジェクト
 * @returns {string} フォーマットされた日付文字列（無効な場合は 'Invalid Date'）
 *
 * @example
 * formatDate('2026-01-31T12:00:00Z'); // '2026/01/31'
 * formatDate(new Date());             // '2026/03/03'
 * formatDate(null);                   // 'Invalid Date'
 */
export function formatDate(dateStr) {
  if (!dateStr) return 'Invalid Date';
  const date = dateStr instanceof Date ? dateStr : new Date(dateStr);
  if (isNaN(date.getTime())) return 'Invalid Date';
  return date.toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
}

/**
 * 日付時刻を日本語形式でフォーマット（YYYY/MM/DD HH:MM）
 *
 * @param {string|Date|null} dateStr - 日付文字列またはDateオブジェクト
 * @returns {string} フォーマットされた日付時刻文字列（無効な場合は 'Invalid Date'）
 *
 * @example
 * formatDateTime('2026-01-31T12:30:00Z'); // '2026/01/31 12:30'
 * formatDateTime(new Date());             // '2026/03/03 15:45'
 */
export function formatDateTime(dateStr) {
  if (!dateStr) return 'Invalid Date';
  const date = dateStr instanceof Date ? dateStr : new Date(dateStr);
  if (isNaN(date.getTime())) return 'Invalid Date';
  return date.toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

/**
 * 相対時刻を返す（「3分前」「2時間前」「1日前」等）
 *
 * 経過時間に応じて適切な相対表現を選択する。
 * 7日を超えた場合は絶対日付を返す。
 *
 * @param {string|Date|null} dateStr - 日付文字列またはDateオブジェクト
 * @returns {string} 相対時刻文字列（無効な場合は 'Invalid Date'）
 *
 * @example
 * formatRelativeTime(new Date(Date.now() - 60000));     // '1分前'
 * formatRelativeTime(new Date(Date.now() - 3600000));   // '1時間前'
 * formatRelativeTime(new Date(Date.now() - 86400000));  // '1日前'
 * formatRelativeTime('2025-01-01T00:00:00Z');           // '2025/01/01' (7日超)
 */
export function formatRelativeTime(dateStr) {
  if (!dateStr) return 'Invalid Date';
  const date = dateStr instanceof Date ? dateStr : new Date(dateStr);
  if (isNaN(date.getTime())) return 'Invalid Date';

  const now = Date.now();
  const diffMs = now - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) {
    return 'たった今';
  } else if (diffMinutes < 60) {
    return `${diffMinutes}分前`;
  } else if (diffHours < 24) {
    return `${diffHours}時間前`;
  } else if (diffDays < 7) {
    return `${diffDays}日前`;
  } else {
    // 7日を超えた場合は絶対日付
    return formatDate(date);
  }
}

// ============================================================
// ファイルサイズフォーマット関数
// ============================================================

/**
 * ファイルサイズを人間が読めるフォーマットに変換
 *
 * バイト数を適切な単位（Bytes/KB/MB/GB/TB）に変換する。
 * 小数点以下2桁まで表示する。
 *
 * @param {number} bytes - バイト数（0以上の整数）
 * @returns {string} フォーマットされたサイズ文字列
 *
 * @example
 * formatFileSize(0);            // '0 Bytes'
 * formatFileSize(1023);         // '1023 Bytes'
 * formatFileSize(1024);         // '1 KB'
 * formatFileSize(1536);         // '1.5 KB'
 * formatFileSize(1048576);      // '1 MB'
 * formatFileSize(1073741824);   // '1 GB'
 */
export function formatFileSize(bytes) {
  if (bytes == null || isNaN(bytes)) return '0 Bytes';
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.min(
    Math.floor(Math.log(bytes) / Math.log(k)),
    sizes.length - 1
  );

  const value = bytes / Math.pow(k, i);
  // 整数の場合は小数点を省略
  const formatted = Number.isInteger(value)
    ? value.toString()
    : value.toFixed(2).replace(/\.?0+$/, '');

  return `${formatted} ${sizes[i]}`;
}

// ============================================================
// 期間フォーマット関数
// ============================================================

/**
 * 期間を秒数から人間が読めるフォーマットに変換
 *
 * 秒数を「X時間Y分Z秒」形式に変換する。
 * 上位の単位が0の場合は省略する。
 *
 * @param {number} seconds - 秒数（0以上の整数）
 * @returns {string} フォーマットされた期間文字列
 *
 * @example
 * formatDuration(0);     // '0秒'
 * formatDuration(45);    // '45秒'
 * formatDuration(90);    // '1分30秒'
 * formatDuration(3600);  // '1時間'
 * formatDuration(3661);  // '1時間1分1秒'
 * formatDuration(7200);  // '2時間'
 */
export function formatDuration(seconds) {
  if (seconds == null || isNaN(seconds) || seconds < 0) return '0秒';

  const totalSeconds = Math.floor(seconds);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const secs = totalSeconds % 60;

  const parts = [];

  if (hours > 0) {
    parts.push(`${hours}時間`);
  }
  if (minutes > 0) {
    parts.push(`${minutes}分`);
  }
  if (secs > 0 || parts.length === 0) {
    parts.push(`${secs}秒`);
  }

  return parts.join('');
}

// ============================================================
// 日付比較・操作ユーティリティ
// ============================================================

/**
 * 指定された日付が今日かどうか判定
 *
 * @param {string|Date} dateStr - 日付文字列またはDateオブジェクト
 * @returns {boolean} 今日であれば true
 *
 * @example
 * isToday(new Date());           // true
 * isToday('2020-01-01T00:00:00'); // false
 */
export function isToday(dateStr) {
  if (!dateStr) return false;
  const date = dateStr instanceof Date ? dateStr : new Date(dateStr);
  if (isNaN(date.getTime())) return false;

  const today = new Date();
  return (
    date.getFullYear() === today.getFullYear() &&
    date.getMonth() === today.getMonth() &&
    date.getDate() === today.getDate()
  );
}

/**
 * 指定された日付が過去かどうか判定
 *
 * @param {string|Date} dateStr - 日付文字列またはDateオブジェクト
 * @returns {boolean} 過去であれば true
 *
 * @example
 * isPast('2020-01-01T00:00:00');  // true
 * isPast(new Date(Date.now() + 3600000)); // false
 */
export function isPast(dateStr) {
  if (!dateStr) return false;
  const date = dateStr instanceof Date ? dateStr : new Date(dateStr);
  if (isNaN(date.getTime())) return false;
  return date.getTime() < Date.now();
}

/**
 * ISO 8601形式の日付文字列を生成（ローカルタイム）
 *
 * @param {Date} [date=new Date()] - Dateオブジェクト
 * @returns {string} ISO 8601形式の日付文字列
 *
 * @example
 * toISOStringLocal(); // '2026-03-03T15:30:00.000+09:00'
 */
export function toISOStringLocal(date = new Date()) {
  const offset = -date.getTimezoneOffset();
  const sign = offset >= 0 ? '+' : '-';
  const absOffset = Math.abs(offset);
  const hours = String(Math.floor(absOffset / 60)).padStart(2, '0');
  const minutes = String(absOffset % 60).padStart(2, '0');

  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return `${localDate.toISOString().slice(0, -1)}${sign}${hours}:${minutes}`;
}

// ============================================================
// 後方互換性レイヤー - window.DateFormatter グローバル公開
// ============================================================
if (typeof window !== 'undefined') {
  window.DateFormatter = {
    formatDate,
    formatDateTime,
    formatRelativeTime,
    formatFileSize,
    formatDuration,
    isToday,
    isPast,
    toISOStringLocal
  };

  // 既存コードが window.formatDate を参照している場合に対応
  window.formatDate = formatDate;

  logger.info('[DateFormatter] ESM module loaded.');
}
