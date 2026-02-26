/**
 * Auth Manager - JWT Authentication & RBAC
 * Mirai Knowledge Systems v1.5.0
 *
 * 認証・認可システム
 * - JWT認証処理（アクセストークン/リフレッシュトークン）
 * - 自動トークンリフレッシュ（14分ごと、有効期限15分の1分前）
 * - RBAC（ロールベースアクセス制御）
 * - UI権限制御
 */

import stateManager from './state-manager.js';

/**
 * ロール階層定義
 * 数値が大きいほど高い権限を持つ
 */
const ROLE_HIERARCHY = {
  'partner': 1,           // 閲覧のみ
  'quality_assurance': 2, // 承認可
  'construction_manager': 3, // ナレッジ作成・承認可
  'admin': 4              // 全機能アクセス可
};

class AuthManager {
  constructor() {
    this.apiBaseUrl = this._getApiBaseUrl();
    this.tokenRefreshInterval = null;
    this.roleHierarchy = ROLE_HIERARCHY;
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
   * ログイン
   * @param {string} username - ユーザー名
   * @param {string} password - パスワード
   * @param {string} totpCode - TOTP認証コード（MFA有効時）
   * @returns {Promise<Object>} ログイン結果
   */
  async login(username, password, totpCode = null) {
    const response = await fetch(`${this.apiBaseUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, totp_code: totpCode })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error?.message || 'Login failed');
    }

    const data = await response.json();

    if (!data.success) {
      throw new Error(data.error?.message || 'Login failed');
    }

    // トークン保存
    localStorage.setItem('access_token', data.data.access_token);
    localStorage.setItem('refresh_token', data.data.refresh_token);

    // ユーザー情報を状態管理に保存
    stateManager.setCurrentUser(data.data.user);

    // トークンリフレッシュ開始
    this.startTokenRefresh();

    return data.data;
  }

  /**
   * ログアウト
   * @returns {Promise<void>}
   */
  async logout() {
    try {
      const token = localStorage.getItem('access_token');
      if (token) {
        await fetch(`${this.apiBaseUrl}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
      }
    } catch (error) {
      console.warn('[Auth] Logout API failed:', error);
    }

    // トークン削除
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');

    // 状態リセット
    stateManager.clearState();

    // トークンリフレッシュ停止
    this.stopTokenRefresh();

    // ログインページへリダイレクト
    window.location.href = '/login.html';
  }

  /**
   * トークンリフレッシュ
   * @returns {Promise<boolean>} 成功: true, 失敗: false
   */
  async refreshAccessToken() {
    const refreshToken = localStorage.getItem('refresh_token');

    if (!refreshToken) {
      console.log('[Auth] No refresh token available');
      return false;
    }

    try {
      console.log('[Auth] Refreshing access token...');
      const response = await fetch(`${this.apiBaseUrl}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${refreshToken}`
        }
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          // 新しいアクセストークンを保存
          localStorage.setItem('access_token', result.data.access_token);
          console.log('[Auth] Access token refreshed successfully');
          return true;
        }
      }

      console.log('[Auth] Token refresh failed');
      return false;
    } catch (error) {
      console.error('[Auth] Token refresh error:', error);
      return false;
    }
  }

  /**
   * 自動トークンリフレッシュ開始
   * 14分ごとにトークンをリフレッシュ（トークン有効期限15分の1分前）
   */
  startTokenRefresh() {
    this.stopTokenRefresh();

    this.tokenRefreshInterval = setInterval(async () => {
      try {
        await this.refreshAccessToken();
      } catch (error) {
        console.error('[Auth] Token refresh failed:', error);
        await this.logout();
      }
    }, 14 * 60 * 1000); // 14分
  }

  /**
   * 自動トークンリフレッシュ停止
   */
  stopTokenRefresh() {
    if (this.tokenRefreshInterval) {
      clearInterval(this.tokenRefreshInterval);
      this.tokenRefreshInterval = null;
    }
  }

  /**
   * 認証チェック
   * @returns {boolean} 認証済み: true, 未認証: false
   */
  checkAuth() {
    const token = localStorage.getItem('access_token');
    console.log('[Auth] Checking authentication. Token exists:', token ? 'YES' : 'NO');

    if (!token) {
      console.log('[Auth] No token found. Redirecting to login...');
      window.location.href = '/login.html';
      return false;
    }

    console.log('[Auth] Token found. Length:', token.length);
    return true;
  }

  /**
   * 認証状態取得
   * @returns {boolean} 認証済み: true, 未認証: false
   */
  isAuthenticated() {
    return !!localStorage.getItem('access_token') && !!stateManager.getCurrentUser();
  }

  /**
   * ロールベースの権限チェック（階層ベース）
   * @param {string} requiredRole - 必要なロール
   * @returns {boolean} 権限あり: true, なし: false
   */
  checkPermission(requiredRole) {
    const user = stateManager.getCurrentUser();
    if (!user) return false;

    const userRoles = user.roles || [];
    const requiredLevel = this.roleHierarchy[requiredRole] || 0;

    // ユーザーの最高権限レベルを取得
    let userMaxLevel = 0;
    userRoles.forEach(role => {
      const level = this.roleHierarchy[role] || 0;
      if (level > userMaxLevel) {
        userMaxLevel = level;
      }
    });

    console.log(`[RBAC] checkPermission: required=${requiredRole}(${requiredLevel}), userMax=${userMaxLevel}`);
    return userMaxLevel >= requiredLevel;
  }

  /**
   * 権限チェック（完全一致）
   * @param {string} permission - 権限名
   * @returns {boolean} 権限あり: true, なし: false
   */
  hasPermission(permission) {
    return stateManager.hasPermission(permission);
  }

  /**
   * 作成者または管理者かどうかチェック
   * @param {string} creatorId - 作成者のID
   * @returns {boolean} 編集権限あり: true, なし: false
   */
  canEdit(creatorId) {
    const user = stateManager.getCurrentUser();
    if (!user) return false;

    // 管理者は常に編集可
    if (this.checkPermission('admin')) return true;

    // 作成者本人も編集可（data-creator属性はstring、user.idはnumberの場合を考慮）
    return String(user.id) === String(creatorId) || user.username === creatorId;
  }

  /**
   * RBAC UI制御を適用
   * data-permission, data-role, data-required-role, data-creator属性を持つ要素の表示/非表示を制御
   */
  applyRBACUI() {
    const user = stateManager.getCurrentUser();
    if (!user) return;

    console.log('[RBAC] Applying UI controls for user:', user.username);
    console.log('[RBAC] User roles:', user.roles);

    // data-permission属性を持つ要素を制御（完全一致）
    document.querySelectorAll('[data-permission]').forEach(element => {
      const requiredPermission = element.dataset.permission;
      const hasAccess = this.hasPermission(requiredPermission);

      if (!hasAccess) {
        element.classList.add('permission-hidden');
        console.log('[RBAC] Permission denied to element:', requiredPermission);
      }
    });

    // data-role属性を持つ要素を制御（完全一致）
    document.querySelectorAll('[data-role]').forEach(element => {
      const allowedRoles = element.dataset.role.split(',');
      const userRoles = user.roles || [];
      const hasRole = allowedRoles.some(role => userRoles.includes(role.trim()));

      if (!hasRole) {
        element.classList.add('permission-hidden');
        console.log('[RBAC] Role access denied:', allowedRoles);
      }
    });

    // data-required-role属性を持つ要素を制御（階層ベース）
    document.querySelectorAll('[data-required-role]').forEach(element => {
      const requiredRole = element.dataset.requiredRole;
      const hasAccess = this.checkPermission(requiredRole);

      if (!hasAccess) {
        element.classList.add('permission-hidden');
        console.log('[RBAC] Required role denied:', requiredRole);
      }
    });

    // data-creator属性を持つ要素を制御（作成者または管理者のみ編集可）
    document.querySelectorAll('[data-creator]').forEach(element => {
      const creatorId = element.dataset.creator;
      const canEditItem = this.canEdit(creatorId);

      if (!canEditItem) {
        element.classList.add('permission-hidden');
        console.log('[RBAC] Edit permission denied for creator:', creatorId);
      }
    });
  }

  /**
   * ユーザー情報表示
   * ヘッダーにユーザー情報を表示（XSS対策: DOM APIを使用）
   */
  displayUserInfo() {
    const user = stateManager.getCurrentUser();
    console.log('[Auth] Displaying user info:', user);

    if (!user) return;

    const userInfoElement = document.querySelector('.user-info');
    if (userInfoElement) {
      // 既存の内容をクリア
      userInfoElement.textContent = '';

      // 安全にDOM要素を作成
      const userName = document.createElement('span');
      userName.className = 'user-name';
      userName.textContent = user.full_name || user.username;

      const userDept = document.createElement('span');
      userDept.className = 'user-dept';
      userDept.textContent = user.department || '';

      const logoutBtn = document.createElement('button');
      logoutBtn.className = 'logout-btn';
      logoutBtn.textContent = 'ログアウト';
      logoutBtn.onclick = () => this.logout();

      userInfoElement.appendChild(userName);
      userInfoElement.appendChild(userDept);
      userInfoElement.appendChild(logoutBtn);
    }
  }
}

// グローバルインスタンス（シングルトン）
const authManager = new AuthManager();

// window公開（既存コード互換性）
if (typeof window !== 'undefined') {
  window.authManager = authManager;
  window.AuthManager = AuthManager;

  // 既存関数エイリアス（後方互換性）
  window.logout = () => authManager.logout();
  window.checkAuth = () => authManager.checkAuth();
  window.checkPermission = (role) => authManager.checkPermission(role);
  window.hasPermission = (perm) => authManager.hasPermission(perm);
  window.canEdit = (creatorId) => authManager.canEdit(creatorId);
  window.applyRBACUI = () => authManager.applyRBACUI();
  window.displayUserInfo = () => authManager.displayUserInfo();
  window.refreshAccessToken = () => authManager.refreshAccessToken();
  window.ROLE_HIERARCHY = ROLE_HIERARCHY;
}

// ES6モジュールエクスポート
export { AuthManager, authManager, ROLE_HIERARCHY };
export default authManager;
