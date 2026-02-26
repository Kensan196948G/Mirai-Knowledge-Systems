/**
 * Notification Manager - Toast Notification Management
 * Mirai Knowledge Systems v1.5.0
 *
 * トースト通知管理
 * - innerHTML完全排除（XSS対策）
 * - DOM API（createElement + textContent）のみ使用
 * - 通知キュー管理（最大5件表示）
 * - 自動消去タイマー
 */

import { DOMHelper } from './components.js';

/**
 * 通知マネージャー
 */
class NotificationManager {
  constructor() {
    this.container = null;
    this.notifications = new Map();
    this.notificationIdCounter = 0;
    this.maxNotifications = 5;
    this.defaultDuration = 4000;
  }

  /**
   * 通知を表示
   * @param {string} message - メッセージ
   * @param {string} type - タイプ（success, error, warning, info）
   * @param {number} duration - 表示時間（ミリ秒、0で自動消去なし）
   * @returns {string} - 通知ID
   */
  show(message, type = 'info', duration = null) {
    // コンテナ初期化
    if (!this.container) {
      this.container = this._createContainer();
    }

    // 最大件数チェック
    if (this.notifications.size >= this.maxNotifications) {
      const oldestId = Array.from(this.notifications.keys())[0];
      this.dismiss(oldestId);
    }

    // 通知ID生成
    const notificationId = `notification-${++this.notificationIdCounter}`;

    // 通知要素作成
    const toast = this._createNotificationElement(message, type, notificationId);

    // DOMに追加
    this.container.appendChild(toast);

    // アニメーション
    setTimeout(() => toast.classList.add('show'), 10);

    // 自動削除タイマー
    const displayDuration = duration !== null ? duration : this.defaultDuration;
    let timerId = null;

    if (displayDuration > 0) {
      timerId = setTimeout(() => {
        this.dismiss(notificationId);
      }, displayDuration);
    }

    // 管理対象に追加
    this.notifications.set(notificationId, {
      element: toast,
      timerId: timerId,
      type: type
    });

    return notificationId;
  }

  /**
   * 通知要素を作成
   * @private
   */
  _createNotificationElement(message, type, id) {
    const toast = DOMHelper.createElement('div', {
      id: id,
      class: `toast toast-${type}`
    });

    // アイコン
    const iconMap = {
      'success': '✓',
      'error': '✕',
      'warning': '⚠',
      'info': 'ℹ'
    };
    const icon = iconMap[type] || 'ℹ';

    const iconSpan = DOMHelper.createElement('span', { class: 'toast-icon' }, icon);
    const messageSpan = DOMHelper.createElement('span', { class: 'toast-message' }, message);

    toast.appendChild(iconSpan);
    toast.appendChild(messageSpan);

    // 閉じるボタン
    const closeBtn = DOMHelper.createElement('button', {
      class: 'toast-close',
      'aria-label': '閉じる'
    }, '×');

    closeBtn.addEventListener('click', () => this.dismiss(id));
    toast.appendChild(closeBtn);

    return toast;
  }

  /**
   * コンテナを作成
   * @private
   */
  _createContainer() {
    const container = DOMHelper.createElement('div', {
      id: 'toastContainer',
      class: 'toast-container'
    });
    document.body.appendChild(container);
    return container;
  }

  /**
   * 通知を消去
   * @param {string} notificationId - 通知ID
   */
  dismiss(notificationId) {
    const notification = this.notifications.get(notificationId);
    if (!notification) return;

    const { element, timerId } = notification;

    // タイマークリア
    if (timerId) {
      clearTimeout(timerId);
    }

    // アニメーション
    element.classList.remove('show');

    setTimeout(() => {
      element.remove();
      this.notifications.delete(notificationId);

      // コンテナが空なら削除
      if (this.notifications.size === 0 && this.container) {
        this.container.remove();
        this.container = null;
      }
    }, 300);
  }

  /**
   * すべての通知を消去
   */
  dismissAll() {
    const notificationIds = Array.from(this.notifications.keys());
    notificationIds.forEach(id => this.dismiss(id));
  }

  /**
   * 成功通知
   * @param {string} message - メッセージ
   * @param {number} duration - 表示時間
   * @returns {string} - 通知ID
   */
  success(message, duration = null) {
    return this.show(message, 'success', duration);
  }

  /**
   * エラー通知
   * @param {string} message - メッセージ
   * @param {number} duration - 表示時間
   * @returns {string} - 通知ID
   */
  error(message, duration = null) {
    return this.show(message, 'error', duration);
  }

  /**
   * 警告通知
   * @param {string} message - メッセージ
   * @param {number} duration - 表示時間
   * @returns {string} - 通知ID
   */
  warning(message, duration = null) {
    return this.show(message, 'warning', duration);
  }

  /**
   * 情報通知
   * @param {string} message - メッセージ
   * @param {number} duration - 表示時間
   * @returns {string} - 通知ID
   */
  info(message, duration = null) {
    return this.show(message, 'info', duration);
  }

  /**
   * 永続通知（手動で閉じるまで表示）
   * @param {string} message - メッセージ
   * @param {string} type - タイプ
   * @returns {string} - 通知ID
   */
  persistent(message, type = 'info') {
    return this.show(message, type, 0);
  }
}

// シングルトンインスタンス
const notificationManager = new NotificationManager();

// グローバル公開（既存コード互換性）
if (typeof window !== 'undefined') {
  window.notificationManager = notificationManager;
  window.NotificationManager = NotificationManager;

  // 既存のshowNotification関数をオーバーライド
  window.showNotification = function(message, type = 'info') {
    return notificationManager.show(message, type);
  };
}

export { notificationManager, NotificationManager };
export default notificationManager;
