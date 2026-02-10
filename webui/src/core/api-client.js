/**
 * API Client - 統一されたAPIアクセスレイヤー
 *
 * 機能:
 * - API_BASE統一管理
 * - fetchAPI()中央化
 * - JWT認証ヘッダー自動付与
 * - エラーハンドリング統一
 * - 401エラー時の自動リダイレクト
 *
 * @module core/api-client
 * @version 1.0.0
 */

// API Base URL（環境に応じた自動検出）
const API_BASE = window.location.hostname === 'localhost'
  ? 'http://localhost:5200'
  : '';

/**
 * 統一されたAPI呼び出し関数
 *
 * @param {string} endpoint - APIエンドポイント（例: '/api/v1/auth/me'）
 * @param {Object} options - fetchオプション
 * @param {string} options.method - HTTPメソッド（GET, POST, PUT, DELETE等）
 * @param {Object} options.headers - 追加HTTPヘッダー
 * @param {Object|string} options.body - リクエストボディ
 * @returns {Promise<Object>} - APIレスポンス（JSON）
 * @throws {Error} - HTTP エラー または ネットワークエラー
 *
 * @example
 * // GET リクエスト
 * const user = await fetchAPI('/api/v1/auth/me');
 *
 * @example
 * // POST リクエスト
 * const result = await fetchAPI('/api/v1/knowledge', {
 *   method: 'POST',
 *   body: JSON.stringify({ title: 'Test', content: 'Content' })
 * });
 */
export async function fetchAPI(endpoint, options = {}) {
  // JWTトークン取得
  const token = localStorage.getItem('access_token');

  // HTTPヘッダー構築
  const headers = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
    ...options.headers
  };

  try {
    // APIリクエスト実行
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers
    });

    // 401 Unauthorized エラー処理（トークン無効・期限切れ）
    if (response.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login.html';
      throw new Error('Unauthorized - トークンが無効です');
    }

    // HTTPエラー処理
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.message ||
        errorData.error ||
        `HTTP ${response.status} - ${response.statusText}`
      );
    }

    // JSON レスポンス返却
    return await response.json();
  } catch (error) {
    // ネットワークエラー or パースエラー
    console.error('[API Client] Error:', error);
    throw error;
  }
}

/**
 * API_BASE をエクスポート（後方互換性のため）
 */
export { API_BASE };

/**
 * グローバル互換性レイヤー（段階的移行のため）
 * 既存コードが window.fetchAPI を期待している場合に対応
 */
if (typeof window !== 'undefined') {
  window.fetchAPI = fetchAPI;
  window.API_BASE = API_BASE;
}
