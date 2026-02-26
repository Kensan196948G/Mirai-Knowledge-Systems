/**
 * Basic UI Components - Button, Card, Alert
 * Mirai Knowledge Systems v1.5.0
 *
 * セキュアDOM操作とUIコンポーネント
 * - innerHTML完全排除（XSS対策）
 * - DOM API（createElement + textContent）のみ使用
 * - 再利用可能なボタン、カード、アラートコンポーネント
 */

import DOMHelper from './dom-utils.js';

/**
 * ボタンコンポーネント
 */
class Button {
  /**
   * ボタン作成
   * @param {Object} options - オプション
   * @param {string} options.text - ボタンテキスト
   * @param {string} options.className - CSSクラス
   * @param {Function} options.onClick - クリックハンドラ
   * @param {boolean} options.disabled - 無効化
   * @param {string} options.type - ボタンタイプ（button/submit/reset）
   * @param {string} options.id - ID属性
   * @param {string} options.ariaLabel - ARIA label
   * @returns {HTMLButtonElement}
   */
  static create({
    text,
    className = 'btn',
    onClick = null,
    disabled = false,
    type = 'button',
    id = null,
    ariaLabel = null
  }) {
    const attributes = {
      class: className,
      type: type,
      disabled: disabled
    };

    if (id) attributes.id = id;
    if (ariaLabel) attributes['aria-label'] = ariaLabel;

    const button = DOMHelper.createElement('button', attributes, text);

    if (onClick) {
      button.addEventListener('click', onClick);
    }

    return button;
  }

  /**
   * アクションボタン作成
   * @param {string} text - ボタンテキスト
   * @param {Function} onClick - クリックハンドラ
   * @returns {HTMLButtonElement}
   */
  static createAction(text, onClick) {
    return Button.create({ text, className: 'action-btn', onClick });
  }

  /**
   * プライマリボタン作成
   * @param {string} text - ボタンテキスト
   * @param {Function} onClick - クリックハンドラ
   * @returns {HTMLButtonElement}
   */
  static createPrimary(text, onClick) {
    return Button.create({ text, className: 'cta', onClick });
  }

  /**
   * キャンセルボタン作成
   * @param {Function} onClick - クリックハンドラ
   * @returns {HTMLButtonElement}
   */
  static createCancel(onClick) {
    return Button.create({ text: 'キャンセル', className: 'cta ghost', onClick });
  }

  /**
   * アイコンボタン作成
   * @param {string} icon - アイコン（絵文字またはテキスト）
   * @param {Function} onClick - クリックハンドラ
   * @param {string} title - ツールチップ
   * @returns {HTMLButtonElement}
   */
  static createIcon(icon, onClick, title = '') {
    return Button.create({
      text: icon,
      className: 'icon-button',
      onClick,
      ariaLabel: title
    });
  }

  /**
   * 削除ボタン作成
   * @param {Function} onClick - クリックハンドラ
   * @returns {HTMLButtonElement}
   */
  static createDelete(onClick) {
    return Button.create({ text: '削除', className: 'btn-delete', onClick });
  }
}

/**
 * カードコンポーネント
 */
class Card {
  /**
   * カード作成
   * @param {Object} options - オプション
   * @param {string} options.title - タイトル
   * @param {string|HTMLElement|HTMLElement[]} options.content - コンテンツ
   * @param {string|HTMLElement|HTMLElement[]} options.footer - フッター
   * @param {string} options.className - 追加CSSクラス
   * @returns {HTMLDivElement}
   */
  static create({ title, content, footer = null, className = '' }) {
    const cardClass = className ? `card ${className}` : 'card';
    const card = DOMHelper.createElement('div', { class: cardClass });

    if (title) {
      const cardHeader = DOMHelper.createElement('div', { class: 'card-header' });
      const cardTitle = DOMHelper.createElement('h3', { class: 'card-title' }, title);
      cardHeader.appendChild(cardTitle);
      card.appendChild(cardHeader);
    }

    if (content) {
      const cardBody = DOMHelper.createElement('div', { class: 'card-body' });
      if (typeof content === 'string') {
        cardBody.textContent = content;
      } else if (Array.isArray(content)) {
        content.forEach(child => {
          if (child instanceof HTMLElement) {
            cardBody.appendChild(child);
          }
        });
      } else if (content instanceof HTMLElement) {
        cardBody.appendChild(content);
      }
      card.appendChild(cardBody);
    }

    if (footer) {
      const cardFooter = DOMHelper.createElement('div', { class: 'card-footer' });
      if (typeof footer === 'string') {
        cardFooter.textContent = footer;
      } else if (Array.isArray(footer)) {
        footer.forEach(child => {
          if (child instanceof HTMLElement) {
            cardFooter.appendChild(child);
          }
        });
      } else if (footer instanceof HTMLElement) {
        cardFooter.appendChild(footer);
      }
      card.appendChild(cardFooter);
    }

    return card;
  }

  /**
   * ナレッジカード作成
   * @param {Object} knowledge - ナレッジオブジェクト
   * @returns {HTMLDivElement}
   */
  static createKnowledge(knowledge) {
    const title = knowledge.title || '無題';
    const content = DOMHelper.createElement('div', {});

    // カテゴリバッジ
    if (knowledge.category) {
      const badge = DOMHelper.createElement('span', { class: 'badge' }, knowledge.category);
      content.appendChild(badge);
    }

    // 説明
    if (knowledge.description) {
      const description = DOMHelper.createElement('p', {}, knowledge.description);
      content.appendChild(description);
    }

    return Card.create({ title, content, className: 'knowledge-card' });
  }
}

/**
 * アラートコンポーネント
 */
class Alert {
  /**
   * アラート作成
   * @param {Object} options - オプション
   * @param {string} options.message - メッセージ
   * @param {string} options.type - タイプ（success, error, warning, info）
   * @param {boolean} options.dismissible - 閉じるボタン表示
   * @returns {HTMLDivElement}
   */
  static create({ message, type = 'info', dismissible = true }) {
    const alert = DOMHelper.createElement('div', {
      class: `alert alert-${type}`,
      role: 'alert'
    });

    const messageEl = DOMHelper.createElement('span', {}, message);
    alert.appendChild(messageEl);

    if (dismissible) {
      const closeBtn = DOMHelper.createElement('button', {
        class: 'alert-close',
        'aria-label': '閉じる'
      }, '×');

      closeBtn.addEventListener('click', () => {
        alert.remove();
      });

      alert.appendChild(closeBtn);
    }

    return alert;
  }

  /**
   * 成功アラート作成
   * @param {string} message - メッセージ
   * @returns {HTMLDivElement}
   */
  static success(message) {
    return Alert.create({ message, type: 'success' });
  }

  /**
   * エラーアラート作成
   * @param {string} message - メッセージ
   * @returns {HTMLDivElement}
   */
  static error(message) {
    return Alert.create({ message, type: 'error' });
  }

  /**
   * 警告アラート作成
   * @param {string} message - メッセージ
   * @returns {HTMLDivElement}
   */
  static warning(message) {
    return Alert.create({ message, type: 'warning' });
  }

  /**
   * 情報アラート作成
   * @param {string} message - メッセージ
   * @returns {HTMLDivElement}
   */
  static info(message) {
    return Alert.create({ message, type: 'info' });
  }
}

// グローバル公開（既存コード互換性）
if (typeof window !== 'undefined') {
  window.Button = Button;
  window.Card = Card;
  window.Alert = Alert;
}

export { Button, Card, Alert };
export default { Button, Card, Alert };
