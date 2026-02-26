/**
 * API Client - fetch wrapper with JWT & retry
 * Mirai Knowledge Systems v1.5.0
 *
 * API通信ラッパー
 * - JWT認証ヘッダー自動付与
 * - 401エラー時の自動トークンリフレッシュ & リトライ
 * - エラーハンドリング & ユーザー通知
 * - リトライロジック（指数バックオフ）
 */

import authManager from '../core/auth.js';

class APIClient {
  constructor() {
    this.apiBaseUrl = this._getApiBaseUrl();
    this.defaultHeaders = {
      'Content-Type': 'application/json'
    };
    this.retryConfig = {
      maxRetries: 3,
      retryDelay: 1000, // 初期遅延（ミリ秒）
      retryStatusCodes: [408, 429, 500, 502, 503, 504]
    };
  }

  /**
   * APIベースURLを動的に取得
   * @private
   * @returns {string} APIベースURL
   */
  _getApiBaseUrl() {
    const hostname = window.location.hostname;
    const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1';

    if (isLocalhost) {
      return 'http://localhost:5200/api/v1';
    }

    return `${window.location.protocol}//${window.location.host}/api/v1`;
  }

  /**
   * リクエスト実行（リトライ付き）
   * @param {string} endpoint - エンドポイント（/で始まる相対パス）
   * @param {Object} options - fetchオプション
   * @returns {Promise<Response>} レスポンス
   */
  async request(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${this.apiBaseUrl}${endpoint}`;

    // デフォルトヘッダー + カスタムヘッダー
    const headers = {
      ...this.defaultHeaders,
      ...options.headers
    };

    // JWT認証ヘッダー自動付与
    const accessToken = localStorage.getItem('access_token');
    if (accessToken && !options.skipAuth) {
      headers['Authorization'] = `Bearer ${accessToken}`;
    }

    const fetchOptions = {
      ...options,
      headers
    };

    let lastError = null;

    // リトライロジック（指数バックオフ）
    for (let attempt = 0; attempt <= this.retryConfig.maxRetries; attempt++) {
      try {
        console.log(`[API] Calling: ${endpoint} (attempt ${attempt + 1}/${this.retryConfig.maxRetries + 1})`);
        const response = await fetch(url, fetchOptions);

        console.log(`[API] Response status: ${response.status}`);

        // 401 Unauthorized → トークンリフレッシュ試行
        if (response.status === 401 && !options.skipTokenRefresh && !endpoint.includes('/auth/')) {
          console.log('[API] 401 Unauthorized. Attempting token refresh...');

          const refreshed = await authManager.refreshAccessToken();

          if (refreshed) {
            // リフレッシュ成功 → リトライ（新しいトークンで）
            console.log('[API] Retrying request with new token...');
            headers['Authorization'] = `Bearer ${localStorage.getItem('access_token')}`;
            return await this.request(endpoint, { ...options, skipTokenRefresh: true });
          } else {
            // リフレッシュ失敗 → ログアウト
            console.log('[API] Token refresh failed. Logging out...');
            this._showNotification('セッションの有効期限が切れました。再度ログインしてください。', 'error');
            await authManager.logout();
            throw new Error('Authentication failed');
          }
        }

        // リトライ対象ステータスコード
        if (this.retryConfig.retryStatusCodes.includes(response.status) && attempt < this.retryConfig.maxRetries) {
          const delay = this.retryConfig.retryDelay * (attempt + 1); // 指数バックオフ
          console.log(`[API] Retrying in ${delay}ms...`);
          await this._sleep(delay);
          continue;
        }

        return response;

      } catch (error) {
        lastError = error;

        // ネットワークエラーでリトライ
        if (attempt < this.retryConfig.maxRetries) {
          const delay = this.retryConfig.retryDelay * (attempt + 1);
          console.log(`[API] Network error. Retrying in ${delay}ms...`);
          await this._sleep(delay);
          continue;
        }
      }
    }

    // 全リトライ失敗
    throw lastError || new Error('Request failed');
  }

  /**
   * GET リクエスト
   * @param {string} endpoint - エンドポイント
   * @param {Object} options - fetchオプション
   * @returns {Promise<Response>} レスポンス
   */
  async get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' });
  }

  /**
   * POST リクエスト
   * @param {string} endpoint - エンドポイント
   * @param {Object} body - リクエストボディ
   * @param {Object} options - fetchオプション
   * @returns {Promise<Response>} レスポンス
   */
  async post(endpoint, body, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'POST',
      body: JSON.stringify(body)
    });
  }

  /**
   * PUT リクエスト
   * @param {string} endpoint - エンドポイント
   * @param {Object} body - リクエストボディ
   * @param {Object} options - fetchオプション
   * @returns {Promise<Response>} レスポンス
   */
  async put(endpoint, body, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(body)
    });
  }

  /**
   * DELETE リクエスト
   * @param {string} endpoint - エンドポイント
   * @param {Object} options - fetchオプション
   * @returns {Promise<Response>} レスポンス
   */
  async delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' });
  }

  /**
   * JSON取得ヘルパー
   * レスポンスをJSONとしてパースし、エラーハンドリング
   * @param {string} endpoint - エンドポイント
   * @param {Object} options - fetchオプション
   * @returns {Promise<Object>} JSONレスポンス
   */
  async getJSON(endpoint, options = {}) {
    const response = await this.get(endpoint, options);
    return this._handleResponse(response);
  }

  /**
   * レスポンス処理（エラーハンドリング）
   * @private
   * @param {Response} response - fetchレスポンス
   * @returns {Promise<Object>} JSONレスポンス
   */
  async _handleResponse(response) {
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}`;
      let errorCode = 'UNKNOWN_ERROR';

      try {
        const errorData = await response.json();
        if (errorData.error) {
          errorMessage = errorData.error.message || errorMessage;
          errorCode = errorData.error.code || errorCode;
        }
      } catch (e) {
        console.error('[API] Failed to parse error response:', e);
      }

      // ステータスコード別の通知
      this._handleErrorStatus(response.status, errorMessage);

      const error = new Error(errorMessage);
      error.code = errorCode;
      error.status = response.status;
      throw error;
    }

    return await response.json();
  }

  /**
   * エラーステータスコード別の処理
   * @private
   * @param {number} status - HTTPステータスコード
   * @param {string} errorMessage - エラーメッセージ
   */
  _handleErrorStatus(status, errorMessage) {
    switch (status) {
      case 403:
        this._showNotification('この操作を実行する権限がありません。', 'error');
        break;
      case 404:
        this._showNotification('リソースが見つかりません。', 'error');
        break;
      case 429:
        this._showNotification('リクエストが多すぎます。しばらく待ってから再試行してください。', 'warning');
        break;
      case 500:
        this._showNotification('サーバーエラーが発生しました。管理者に連絡してください。', 'error');
        break;
      default:
        this._showNotification(`エラー: ${errorMessage}`, 'error');
        break;
    }
  }

  /**
   * 通知表示ヘルパー
   * @private
   * @param {string} message - メッセージ
   * @param {string} type - 通知タイプ（success/error/warning/info）
   */
  _showNotification(message, type) {
    // window.showNotificationが存在する場合は使用
    if (typeof window.showNotification === 'function') {
      window.showNotification(message, type);
    } else {
      // フォールバック: console出力
      console.log(`[Notification] ${type.toUpperCase()}: ${message}`);
    }
  }

  /**
   * sleep ヘルパー
   * @private
   * @param {number} ms - 遅延時間（ミリ秒）
   * @returns {Promise<void>}
   */
  _sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * fetchAPI互換メソッド（既存コード互換性）
   * @param {string} endpoint - エンドポイント
   * @param {Object} options - fetchオプション
   * @returns {Promise<Object>} JSONレスポンス
   */
  async fetchAPI(endpoint, options = {}) {
    const response = await this.request(endpoint, options);
    return this._handleResponse(response);
  }
}

// グローバルインスタンス（シングルトン）
const apiClient = new APIClient();

// window公開（既存コード互換性）
if (typeof window !== 'undefined') {
  window.apiClient = apiClient;
  window.APIClient = APIClient;

  // 既存関数エイリアス（後方互換性）
  window.fetchAPI = (endpoint, options) => apiClient.fetchAPI(endpoint, options);
}

// ES6モジュールエクスポート
export { APIClient, apiClient };
export default apiClient;
