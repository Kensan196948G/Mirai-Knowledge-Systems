/**
 * @fileoverview MFA（多要素認証）機能モジュール v2.0.0
 * @module features/mfa
 * @description Phase F-2 ESモジュール化版
 *   webui/mfa.js をESM形式に変換。
 *   - TOTP セットアップ / 有効化 / 無効化
 *   - バックアップコード管理
 *   - ログイン MFA 検証
 *   - QRコード表示 / バリデーションユーティリティ
 */

import { fetchAPI } from '../core/api-client.js';
import { logger } from '../core/logger.js';

// ============================================================
// MFA API 関数
// ============================================================

/**
 * MFAセットアップ - TOTPシークレット・QRコード・バックアップコードを生成
 * @returns {Promise<Object>} セットアップデータ（secret, qr_code_base64, backup_codes）
 */
export async function setupMFA() {
  const token = localStorage.getItem('access_token');
  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(`${_getApiBase()}/api/v1/auth/mfa/setup`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error?.message || 'MFA setup failed');
  }

  logger.debug('[MFA] Setup completed successfully');
  return data;
}

/**
 * MFAセットアップを検証してMFAを有効化
 * @param {string} totpCode - 6桁TOTPコード
 * @returns {Promise<Object>} 成功レスポンス
 */
export async function verifyMFASetup(totpCode) {
  const token = localStorage.getItem('access_token');
  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(`${_getApiBase()}/api/v1/auth/mfa/enable`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ code: totpCode })
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error?.message || 'MFA verification failed');
  }

  logger.debug('[MFA] MFA enabled successfully');
  return data;
}

/**
 * MFAを無効化（パスワードとTOTPコードが必要）
 * @param {string} password - ユーザーパスワード
 * @param {string} code - TOTPコードまたはバックアップコード
 * @returns {Promise<Object>} 成功レスポンス
 */
export async function disableMFA(password, code) {
  const token = localStorage.getItem('access_token');
  if (!token) {
    throw new Error('Not authenticated');
  }

  const payload = { password, code };

  const response = await fetch(`${_getApiBase()}/api/v1/auth/mfa/disable`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error?.message || 'MFA disable failed');
  }

  logger.debug('[MFA] MFA disabled successfully');
  return data;
}

/**
 * MFAトークンとTOTP/バックアップコードでログイン
 * @param {string} mfaToken - 初回ログイン時の一時MFAトークン
 * @param {string} code - TOTPコード（6桁）またはバックアップコード
 * @param {boolean} [isBackupCode=false] - バックアップコード使用時はtrue
 * @returns {Promise<Object>} ログインレスポンス（access_token含む）
 */
export async function loginWithMFA(mfaToken, code, isBackupCode = false) {
  const payload = { mfa_token: mfaToken };

  if (isBackupCode) {
    payload.backup_code = code;
  } else {
    payload.code = code;
  }

  const response = await fetch(`${_getApiBase()}/api/v1/auth/login/mfa`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error?.message || 'MFA login failed');
  }

  // トークンを保存
  if (data.success && data.data.access_token) {
    localStorage.setItem('access_token', data.data.access_token);
    localStorage.setItem('refresh_token', data.data.refresh_token);
    localStorage.setItem('user', JSON.stringify(data.data.user));

    if (data.data.used_backup_code) {
      localStorage.setItem('mfa_backup_warning', 'true');
      localStorage.setItem('remaining_backup_codes', data.data.remaining_backup_codes);
    }
  }

  logger.debug('[MFA] MFA login completed');
  return data;
}

/**
 * バックアップコードを再生成
 * @param {string} totpCode - 検証用の6桁TOTPコード
 * @returns {Promise<Object>} 新しいbackup_codesを含むレスポンス
 */
export async function regenerateBackupCodes(totpCode) {
  const token = localStorage.getItem('access_token');
  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(`${_getApiBase()}/api/v1/auth/mfa/backup-codes/regenerate`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ code: totpCode })
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error?.message || 'Backup code regeneration failed');
  }

  logger.debug('[MFA] Backup codes regenerated');
  return data;
}

/**
 * 現在のユーザーのMFAステータスを取得
 * @returns {Promise<Object>} mfa_enabled, remaining_backup_codes 等を含むMFAステータス
 */
export async function getMFAStatus() {
  const token = localStorage.getItem('access_token');
  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(`${_getApiBase()}/api/v1/auth/mfa/status`, {
    method: 'GET',
    headers: { 'Authorization': `Bearer ${token}` }
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error?.message || 'Failed to get MFA status');
  }

  return data;
}

/**
 * MFA回復をリクエスト（メールで回復リンクを送信）
 * @param {string} email - ユーザーメールアドレス
 * @param {string} username - ユーザー名
 * @returns {Promise<Object>} レスポンス
 */
export async function requestMFARecovery(email, username) {
  const response = await fetch(`${_getApiBase()}/api/v1/auth/mfa/recovery`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, username })
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error?.message || 'MFA recovery request failed');
  }

  logger.debug('[MFA] Recovery request sent');
  return data;
}

// ============================================================
// UI ユーティリティ関数
// ============================================================

/**
 * QRコードを要素に表示する
 * @param {string} qrCodeBase64 - Base64エンコードされたPNG QRコード
 * @param {HTMLElement} element - QRコードを表示するターゲット要素
 */
export function displayQRCode(qrCodeBase64, element) {
  if (!element) {
    logger.error('[MFA] displayQRCode: Target element not found');
    return;
  }

  const img = document.createElement('img');
  img.src = `data:image/png;base64,${qrCodeBase64}`;
  img.alt = 'QR Code for MFA Setup';
  img.style.maxWidth = '300px';

  element.textContent = '';
  element.appendChild(img);
}

/**
 * バックアップコードをテキストファイルとしてダウンロード
 * @param {Array<string>} codes - バックアップコードの配列
 */
export function downloadBackupCodesText(codes) {
  const content = [
    'Mirai Knowledge Systems',
    '2要素認証バックアップコード',
    '='.repeat(50),
    '',
    '各コードは1回のみ使用可能です。',
    '安全な場所に保管してください。',
    '',
    ...codes,
    '',
    `生成日時: ${new Date().toLocaleString('ja-JP')}`,
  ].join('\n');

  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `mks-backup-codes-${Date.now()}.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * MFAカウントダウンタイマーを表示（mfa_tokenの有効期限用）
 * @param {number} expiresInSeconds - 有効期限までの秒数
 * @param {HTMLElement} element - カウントダウンを表示する要素
 */
export function displayMFACountdown(expiresInSeconds, element) {
  if (!element) return;

  let remaining = expiresInSeconds;

  const updateDisplay = () => {
    const minutes = Math.floor(remaining / 60);
    const seconds = remaining % 60;
    element.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;

    if (remaining <= 60) {
      element.style.color = 'red';
    }

    if (remaining <= 0) {
      element.textContent = '期限切れ';
      clearInterval(interval);
    }

    remaining--;
  };

  updateDisplay();
  const interval = setInterval(updateDisplay, 1000);

  return interval;
}

// ============================================================
// バリデーション関数
// ============================================================

/**
 * バックアップコードを表示用にフォーマット（XXXX-XXXX-XXXX形式）
 * @param {string} code - バックアップコード
 * @returns {string} フォーマット済みコード
 */
export function formatBackupCode(code) {
  const clean = code.replace(/-/g, '');

  if (clean.length === 12) {
    return `${clean.slice(0, 4)}-${clean.slice(4, 8)}-${clean.slice(8, 12)}`;
  }

  return code;
}

/**
 * TOTPコードのフォーマットを検証
 * @param {string} code - 検証するTOTPコード
 * @returns {boolean} 有効な場合はtrue
 */
export function isValidTOTPCode(code) {
  return /^\d{6}$/.test(code);
}

/**
 * バックアップコードのフォーマットを検証
 * @param {string} code - 検証するバックアップコード
 * @returns {boolean} 有効な場合はtrue
 */
export function isValidBackupCode(code) {
  const clean = code.replace(/-/g, '');
  return /^[A-Z0-9]{12}$/i.test(clean);
}

/**
 * バックアップコードが少ない場合に警告を表示すべきか確認
 * @param {number} remaining - 残りバックアップコード数
 * @returns {boolean} 警告を表示すべき場合はtrue
 */
export function shouldWarnLowBackupCodes(remaining) {
  return remaining > 0 && remaining <= 3;
}

// ============================================================
// 内部ヘルパー
// ============================================================

/**
 * API ベースURLを取得（環境に応じた自動検出）
 * @returns {string} APIベースURL
 * @private
 */
function _getApiBase() {
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:5200';
  }
  return `${window.location.protocol}//${window.location.host}`;
}

// ============================================================
// 後方互換性（window経由のアクセスを維持）
// ============================================================

if (typeof window !== 'undefined') {
  window.MFAModule = {
    setupMFA,
    verifyMFASetup,
    disableMFA,
    loginWithMFA,
    regenerateBackupCodes,
    getMFAStatus,
    requestMFARecovery,
    displayQRCode,
    downloadBackupCodesText,
    displayMFACountdown,
    formatBackupCode,
    isValidTOTPCode,
    isValidBackupCode,
    shouldWarnLowBackupCodes,
  };
}
