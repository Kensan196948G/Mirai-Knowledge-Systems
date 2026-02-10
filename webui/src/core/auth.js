/**
 * Auth - 統一された認証ロジック
 *
 * 機能:
 * - トークン存在確認
 * - 未認証時の自動リダイレクト
 * - 現在のユーザー情報取得
 * - ログアウト処理
 *
 * @module core/auth
 * @version 1.0.0
 */

import { fetchAPI } from './api-client.js';

/**
 * 認証状態チェック（トークン存在確認）
 *
 * @returns {boolean} - 認証済みの場合true、未認証の場合false
 *
 * @example
 * if (!checkAuth()) {
 *   // 未認証 → /login.html にリダイレクト済み
 * }
 */
export function checkAuth() {
  const token = localStorage.getItem('access_token');
  if (!token) {
    window.location.href = '/login.html';
    return false;
  }
  return true;
}

/**
 * 現在のユーザー情報を取得
 *
 * @returns {Promise<Object|null>} - ユーザー情報オブジェクト または null（エラー時）
 *
 * @example
 * const user = await getCurrentUser();
 * if (user) {
 *   console.log('ユーザー名:', user.username);
 *   console.log('権限:', user.role);
 * }
 */
export async function getCurrentUser() {
  try {
    const response = await fetchAPI('/api/v1/auth/me');
    return response.user;
  } catch (error) {
    console.error('[Auth] Failed to get current user:', error);
    return null;
  }
}

/**
 * ログアウト処理
 *
 * 機能:
 * - localStorage のトークン削除
 * - ユーザー情報削除
 * - ログイン画面へリダイレクト
 *
 * @example
 * // ログアウトボタンのクリックイベント
 * document.getElementById('logout-btn').addEventListener('click', () => {
 *   logout();
 * });
 */
export function logout() {
  // トークン・ユーザー情報を削除
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');

  // IndexedDB の暗号化トークンも削除（PWA対応）
  if (window.indexedDB) {
    const dbRequest = indexedDB.open('mks-pwa-db', 1);
    dbRequest.onsuccess = (event) => {
      const db = event.target.result;
      if (db.objectStoreNames.contains('auth-tokens')) {
        const transaction = db.transaction(['auth-tokens'], 'readwrite');
        const store = transaction.objectStore('auth-tokens');
        store.clear();
      }
    };
  }

  // ログイン画面へリダイレクト
  window.location.href = '/login.html';
}

/**
 * トークンリフレッシュ
 *
 * @returns {Promise<boolean>} - 成功時true、失敗時false
 *
 * @example
 * const refreshed = await refreshToken();
 * if (!refreshed) {
 *   console.error('トークンのリフレッシュに失敗しました');
 * }
 */
export async function refreshToken() {
  try {
    const response = await fetchAPI('/api/v1/auth/refresh', {
      method: 'POST'
    });

    if (response.access_token) {
      localStorage.setItem('access_token', response.access_token);
      return true;
    }

    return false;
  } catch (error) {
    console.error('[Auth] Failed to refresh token:', error);
    return false;
  }
}

/**
 * グローバル互換性レイヤー（段階的移行のため）
 */
if (typeof window !== 'undefined') {
  window.checkAuth = checkAuth;
  window.getCurrentUser = getCurrentUser;
  window.logout = logout;
  window.refreshToken = refreshToken;
}
