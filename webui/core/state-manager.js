/**
 * State Manager - Observer Pattern
 * Mirai Knowledge Systems v1.5.0
 *
 * グローバル状態管理システム
 * - Observer Patternによる状態変更通知
 * - localStorage統合による永続化
 * - currentUser, appConfig等の一元管理
 */

class StateManager {
  constructor() {
    this.state = {
      currentUser: null,
      isAuthenticated: false,
      userPermissions: [],
      userRoles: [],
      appConfig: {
        apiBase: `${window.location.origin}/api/v1`,
        isProduction: false,
        envName: '開発'
      }
    };
    this.observers = [];
  }

  /**
   * Observer Pattern: 状態変更通知購読
   * @param {Function} observer - コールバック関数
   */
  subscribe(observer) {
    if (typeof observer !== 'function') {
      throw new TypeError('Observer must be a function');
    }
    this.observers.push(observer);
  }

  /**
   * Observer Pattern: 購読解除
   * @param {Function} observer - コールバック関数
   */
  unsubscribe(observer) {
    this.observers = this.observers.filter(obs => obs !== observer);
  }

  /**
   * 状態変更を全購読者に通知
   * @param {Object} stateChange - 変更内容
   */
  notify(stateChange) {
    this.observers.forEach(observer => {
      try {
        observer(stateChange);
      } catch (error) {
        console.error('[StateManager] Observer error:', error);
      }
    });
  }

  /**
   * 状態取得
   * @param {string} key - 状態キー（省略時は全状態）
   * @returns {*} 状態値
   */
  getState(key) {
    return key ? this.state[key] : { ...this.state };
  }

  /**
   * 状態更新
   * @param {string} key - 状態キー
   * @param {*} value - 新しい値
   */
  setState(key, value) {
    const oldValue = this.state[key];
    this.state[key] = value;
    this.notify({ key, oldValue, newValue: value });
    this._persistState(key, value);
  }

  /**
   * currentUser管理: 取得
   * @returns {Object|null} 現在のユーザー情報
   */
  getCurrentUser() {
    return this.state.currentUser;
  }

  /**
   * currentUser管理: 設定
   * @param {Object|null} user - ユーザー情報
   */
  setCurrentUser(user) {
    this.setState('currentUser', user);
    this.setState('isAuthenticated', !!user);

    if (user) {
      this.setState('userPermissions', user.permissions || []);
      this.setState('userRoles', user.roles || []);
    } else {
      this.setState('userPermissions', []);
      this.setState('userRoles', []);
    }
  }

  /**
   * 権限チェック
   * @param {string} permission - 権限名
   * @returns {boolean} 権限の有無
   */
  hasPermission(permission) {
    const permissions = this.state.userPermissions;

    // 管理者は全権限
    if (permissions.includes('*')) return true;

    // 指定された権限を持っているか
    return permissions.includes(permission);
  }

  /**
   * ロールチェック
   * @param {string} role - ロール名
   * @returns {boolean} ロールの有無
   */
  hasRole(role) {
    return this.state.userRoles.includes(role);
  }

  /**
   * localStorage統合: 状態永続化
   * @private
   * @param {string} key - 状態キー
   * @param {*} value - 値
   */
  _persistState(key, value) {
    // セキュリティ: 本番環境では永続化しない項目
    const nonPersistKeys = ['currentUser', 'userPermissions', 'userRoles'];
    const isProduction = this.state.appConfig?.isProduction;

    if (isProduction && nonPersistKeys.includes(key)) {
      return; // 本番環境では機密情報を永続化しない
    }

    try {
      const storageKey = `mks_state_${key}`;
      localStorage.setItem(storageKey, JSON.stringify(value));
    } catch (error) {
      console.warn('[StateManager] Failed to persist state:', key, error);
    }
  }

  /**
   * 状態復元
   * localStorageから状態を復元
   */
  restoreState() {
    Object.keys(this.state).forEach(key => {
      try {
        const storageKey = `mks_state_${key}`;
        const stored = localStorage.getItem(storageKey);

        if (stored) {
          this.state[key] = JSON.parse(stored);
        }
      } catch (error) {
        console.warn(`[StateManager] Failed to restore state: ${key}`, error);
      }
    });
  }

  /**
   * 状態リセット
   * すべての状態をクリア（ログアウト時に使用）
   */
  clearState() {
    this.state = {
      currentUser: null,
      isAuthenticated: false,
      userPermissions: [],
      userRoles: [],
      appConfig: this.state.appConfig // appConfigは保持
    };

    // localStorage内のmks_state_*をすべて削除
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith('mks_state_')) {
        localStorage.removeItem(key);
      }
    });

    this.notify({ type: 'clear' });
  }

  /**
   * アプリ設定取得
   * @param {string} key - 設定キー
   * @returns {*} 設定値
   */
  getConfig(key) {
    return key ? this.state.appConfig[key] : { ...this.state.appConfig };
  }

  /**
   * アプリ設定更新
   * @param {string} key - 設定キー
   * @param {*} value - 新しい値
   */
  setConfig(key, value) {
    this.state.appConfig[key] = value;
    this.notify({ type: 'config', key, value });
    this._persistState('appConfig', this.state.appConfig);
  }
}

// グローバルインスタンス（シングルトン）
const stateManager = new StateManager();

// window公開（既存コード互換性）
if (typeof window !== 'undefined') {
  window.stateManager = stateManager;
  window.StateManager = StateManager;

  // 既存関数エイリアス（後方互換性）
  window.getCurrentUser = () => stateManager.getCurrentUser();
}

// ES6モジュールエクスポート
export { StateManager, stateManager };
export default stateManager;
