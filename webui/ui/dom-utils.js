/**
 * DOM Utilities - Secure DOM Manipulation
 * Mirai Knowledge Systems v1.5.0
 *
 * セキュアDOM操作ヘルパー
 * - innerHTML完全排除（XSS対策）
 * - DOM API（createElement + textContent）のみ使用
 */

/**
 * セキュアDOM操作ヘルパー
 */
class DOMHelper {
  /**
   * 要素作成（セキュア）
   * @param {string} tag - タグ名
   * @param {Object} attributes - 属性
   * @param {string|HTMLElement|HTMLElement[]} content - コンテンツ
   * @returns {HTMLElement}
   */
  static createElement(tag, attributes = {}, content = null) {
    const element = document.createElement(tag);

    // 属性設定
    Object.keys(attributes).forEach(key => {
      if (key === 'class' || key === 'className') {
        element.className = attributes[key];
      } else if (key === 'dataset') {
        Object.keys(attributes[key]).forEach(dataKey => {
          element.dataset[dataKey] = attributes[key][dataKey];
        });
      } else if (key === 'style' && typeof attributes[key] === 'object') {
        Object.assign(element.style, attributes[key]);
      } else {
        element.setAttribute(key, attributes[key]);
      }
    });

    // コンテンツ設定（セキュア）
    if (content !== null) {
      if (typeof content === 'string') {
        element.textContent = content;
      } else if (Array.isArray(content)) {
        content.forEach(child => {
          if (child instanceof HTMLElement) {
            element.appendChild(child);
          } else if (typeof child === 'string') {
            element.appendChild(document.createTextNode(child));
          }
        });
      } else if (content instanceof HTMLElement) {
        element.appendChild(content);
      }
    }

    return element;
  }

  /**
   * テキストノード作成
   * @param {string} text - テキスト
   * @returns {Text}
   */
  static createTextNode(text) {
    return document.createTextNode(text);
  }

  /**
   * 子要素をすべて削除（セキュア）
   * @param {HTMLElement} element - 要素
   */
  static clearChildren(element) {
    while (element.firstChild) {
      element.removeChild(element.firstChild);
    }
  }

  /**
   * 要素置換（セキュア）
   * @param {HTMLElement} oldElement - 古い要素
   * @param {HTMLElement} newElement - 新しい要素
   */
  static replaceElement(oldElement, newElement) {
    if (oldElement && oldElement.parentNode) {
      oldElement.parentNode.replaceChild(newElement, oldElement);
    }
  }

  /**
   * 要素にクラスを追加
   * @param {HTMLElement} element - 要素
   * @param {string|string[]} classNames - クラス名
   */
  static addClass(element, classNames) {
    if (Array.isArray(classNames)) {
      element.classList.add(...classNames);
    } else {
      element.classList.add(classNames);
    }
  }

  /**
   * 要素からクラスを削除
   * @param {HTMLElement} element - 要素
   * @param {string|string[]} classNames - クラス名
   */
  static removeClass(element, classNames) {
    if (Array.isArray(classNames)) {
      element.classList.remove(...classNames);
    } else {
      element.classList.remove(classNames);
    }
  }

  /**
   * 要素のクラスをトグル
   * @param {HTMLElement} element - 要素
   * @param {string} className - クラス名
   */
  static toggleClass(element, className) {
    element.classList.toggle(className);
  }

  /**
   * 属性を安全に設定
   * @param {HTMLElement} element - 要素
   * @param {string} attribute - 属性名
   * @param {string} value - 属性値
   */
  static setAttribute(element, attribute, value) {
    element.setAttribute(attribute, value);
  }

  /**
   * スタイルを安全に設定
   * @param {HTMLElement} element - 要素
   * @param {Object} styles - スタイルオブジェクト
   */
  static setStyle(element, styles) {
    Object.assign(element.style, styles);
  }
}

// グローバル公開（既存コード互換性）
if (typeof window !== 'undefined') {
  window.DOMHelper = DOMHelper;
}

export { DOMHelper };
export default DOMHelper;
