/**
 * Modal Manager - Modal Dialog Management
 * Mirai Knowledge Systems v1.5.0
 *
 * モーダルダイアログ管理
 * - innerHTML完全排除（XSS対策）
 * - DOM API（createElement + textContent）のみ使用
 * - アニメーション対応（fade-in/fade-out）
 */

import { DOMHelper, Button } from './components.js';

/**
 * モーダルマネージャー
 */
class ModalManager {
  constructor() {
    this.activeModals = new Map();
    this.modalIdCounter = 0;
  }

  /**
   * モーダルを表示
   * @param {Object} options - オプション
   * @param {string} options.id - モーダルID（既存モーダルの場合）
   * @param {string} options.title - タイトル
   * @param {string|HTMLElement|HTMLElement[]} options.content - コンテンツ
   * @param {Array} options.actions - アクションボタン配列
   * @param {boolean} options.closeButton - 閉じるボタン表示
   * @param {boolean} options.closeOnBackdrop - 背景クリックで閉じる
   * @param {Function} options.onClose - 閉じる時のコールバック
   * @param {string} options.size - サイズ（small/medium/large）
   * @returns {string} - モーダルID
   */
  show({
    id = null,
    title = '',
    content = '',
    actions = [],
    closeButton = true,
    closeOnBackdrop = true,
    onClose = null,
    size = 'medium'
  }) {
    // 既存モーダルのチェック
    if (id) {
      const existingModal = document.getElementById(id);
      if (existingModal) {
        existingModal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        setTimeout(() => existingModal.classList.add('show'), 10);
        return id;
      }
    }

    // 新規モーダルID生成
    const modalId = id || `modal-${++this.modalIdCounter}`;

    // モーダル要素作成
    const modal = this._createModalElement({
      id: modalId,
      title,
      content,
      actions,
      closeButton,
      size
    });

    // 背景クリックで閉じる
    if (closeOnBackdrop) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          this.close(modalId);
        }
      });
    }

    // DOMに追加
    document.body.appendChild(modal);
    document.body.style.overflow = 'hidden';

    // アニメーション
    setTimeout(() => modal.classList.add('show'), 10);

    // 管理対象に追加
    this.activeModals.set(modalId, {
      element: modal,
      onClose: onClose
    });

    return modalId;
  }

  /**
   * モーダル要素を作成
   * @private
   */
  _createModalElement({ id, title, content, actions, closeButton, size }) {
    const modal = DOMHelper.createElement('div', {
      id: id,
      class: 'modal',
      style: { display: 'flex' }
    });

    const modalContent = DOMHelper.createElement('div', {
      class: `modal-content modal-${size}`
    });

    // ヘッダー
    if (title || closeButton) {
      const modalHeader = DOMHelper.createElement('div', { class: 'modal-header' });

      if (title) {
        const titleEl = DOMHelper.createElement('h2', {}, title);
        modalHeader.appendChild(titleEl);
      }

      if (closeButton) {
        const closeBtn = DOMHelper.createElement('button', {
          class: 'modal-close',
          'aria-label': '閉じる'
        }, '×');
        closeBtn.addEventListener('click', () => this.close(id));
        modalHeader.appendChild(closeBtn);
      }

      modalContent.appendChild(modalHeader);
    }

    // ボディ
    const modalBody = DOMHelper.createElement('div', { class: 'modal-body' });

    if (typeof content === 'string') {
      modalBody.textContent = content;
    } else if (Array.isArray(content)) {
      content.forEach(child => {
        if (child instanceof HTMLElement) {
          modalBody.appendChild(child);
        }
      });
    } else if (content instanceof HTMLElement) {
      modalBody.appendChild(content);
    }

    modalContent.appendChild(modalBody);

    // アクション
    if (actions && actions.length > 0) {
      const modalActions = DOMHelper.createElement('div', { class: 'modal-actions' });

      actions.forEach(action => {
        const btn = Button.create({
          text: action.text,
          className: action.className || 'cta',
          onClick: action.onClick,
          disabled: action.disabled || false
        });
        modalActions.appendChild(btn);
      });

      modalContent.appendChild(modalActions);
    }

    modal.appendChild(modalContent);
    return modal;
  }

  /**
   * モーダルを閉じる
   * @param {string} modalId - モーダルID
   */
  close(modalId) {
    const modalData = this.activeModals.get(modalId);
    if (!modalData) return;

    const { element, onClose } = modalData;

    // アニメーション
    element.classList.remove('show');

    setTimeout(() => {
      element.remove();
      document.body.style.overflow = '';

      // コールバック実行
      if (onClose && typeof onClose === 'function') {
        onClose();
      }

      // 管理対象から削除
      this.activeModals.delete(modalId);
    }, 300);
  }

  /**
   * すべてのモーダルを閉じる
   */
  closeAll() {
    const modalIds = Array.from(this.activeModals.keys());
    modalIds.forEach(id => this.close(id));
  }

  /**
   * 確認ダイアログを表示
   * @param {Object} options - オプション
   * @param {string} options.title - タイトル
   * @param {string} options.message - メッセージ
   * @param {Function} options.onConfirm - 確認時のコールバック
   * @param {Function} options.onCancel - キャンセル時のコールバック
   * @param {string} options.confirmText - 確認ボタンテキスト
   * @param {string} options.cancelText - キャンセルボタンテキスト
   * @returns {string} - モーダルID
   */
  confirm({
    title = '確認',
    message = '',
    onConfirm = null,
    onCancel = null,
    confirmText = 'OK',
    cancelText = 'キャンセル'
  }) {
    const content = DOMHelper.createElement('p', {}, message);

    const actions = [
      {
        text: cancelText,
        className: 'cta ghost',
        onClick: () => {
          this.close(modalId);
          if (onCancel) onCancel();
        }
      },
      {
        text: confirmText,
        className: 'cta',
        onClick: () => {
          this.close(modalId);
          if (onConfirm) onConfirm();
        }
      }
    ];

    const modalId = this.show({
      title,
      content,
      actions,
      size: 'small',
      closeOnBackdrop: false
    });

    return modalId;
  }

  /**
   * アラートダイアログを表示
   * @param {Object} options - オプション
   * @param {string} options.title - タイトル
   * @param {string} options.message - メッセージ
   * @param {Function} options.onClose - 閉じる時のコールバック
   * @param {string} options.buttonText - ボタンテキスト
   * @returns {string} - モーダルID
   */
  alert({
    title = '通知',
    message = '',
    onClose = null,
    buttonText = 'OK'
  }) {
    const content = DOMHelper.createElement('p', {}, message);

    const actions = [
      {
        text: buttonText,
        className: 'cta',
        onClick: () => {
          this.close(modalId);
          if (onClose) onClose();
        }
      }
    ];

    const modalId = this.show({
      title,
      content,
      actions,
      size: 'small'
    });

    return modalId;
  }

  /**
   * プロンプトダイアログを表示
   * @param {Object} options - オプション
   * @param {string} options.title - タイトル
   * @param {string} options.message - メッセージ
   * @param {string} options.defaultValue - デフォルト値
   * @param {Function} options.onConfirm - 確認時のコールバック
   * @param {Function} options.onCancel - キャンセル時のコールバック
   * @returns {string} - モーダルID
   */
  prompt({
    title = '入力',
    message = '',
    defaultValue = '',
    onConfirm = null,
    onCancel = null
  }) {
    const content = DOMHelper.createElement('div', {});

    const messageEl = DOMHelper.createElement('p', {}, message);
    content.appendChild(messageEl);

    const input = DOMHelper.createElement('input', {
      type: 'text',
      value: defaultValue,
      class: 'prompt-input'
    });
    content.appendChild(input);

    const actions = [
      {
        text: 'キャンセル',
        className: 'cta ghost',
        onClick: () => {
          this.close(modalId);
          if (onCancel) onCancel();
        }
      },
      {
        text: 'OK',
        className: 'cta',
        onClick: () => {
          const value = input.value;
          this.close(modalId);
          if (onConfirm) onConfirm(value);
        }
      }
    ];

    const modalId = this.show({
      title,
      content,
      actions,
      size: 'small'
    });

    // フォーカス
    setTimeout(() => input.focus(), 100);

    return modalId;
  }

  /**
   * 既存のモーダルを開く（互換性関数）
   * @param {string} modalId - モーダルID
   */
  open(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.style.display = 'flex';
      document.body.style.overflow = 'hidden';
      setTimeout(() => modal.classList.add('show'), 10);
    }
  }

  /**
   * 既存のモーダルを閉じる（互換性関数）
   * @param {string} modalId - モーダルID
   */
  closeExisting(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('show');
      setTimeout(() => {
        modal.style.display = 'none';
        document.body.style.overflow = '';
      }, 300);
    }
  }
}

// シングルトンインスタンス
const modalManager = new ModalManager();

// グローバル公開（既存コード互換性）
if (typeof window !== 'undefined') {
  window.modalManager = modalManager;
  window.ModalManager = ModalManager;
}

export { modalManager, ModalManager };
export default modalManager;
