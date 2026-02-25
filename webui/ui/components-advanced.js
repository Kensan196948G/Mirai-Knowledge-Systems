/**
 * Advanced UI Components - List, Table
 * Mirai Knowledge Systems v1.5.0
 *
 * セキュアDOM操作とUIコンポーネント
 * - innerHTML完全排除（XSS対策）
 * - DOM API（createElement + textContent）のみ使用
 * - 再利用可能なリスト、テーブルコンポーネント
 */

import DOMHelper from './dom-utils.js';

/**
 * リストコンポーネント
 */
class List {
  /**
   * リスト作成
   * @param {Object} options - オプション
   * @param {Array} options.items - アイテム配列
   * @param {Function} options.renderItem - アイテムレンダリング関数
   * @param {boolean} options.ordered - 順序付きリスト（ol/ul）
   * @param {string} options.className - 追加CSSクラス
   * @returns {HTMLUListElement|HTMLOListElement}
   */
  static create({ items = [], renderItem = null, ordered = false, className = '' }) {
    const listTag = ordered ? 'ol' : 'ul';
    const list = DOMHelper.createElement(listTag, { class: className });

    items.forEach(item => {
      const li = DOMHelper.createElement('li');
      if (renderItem && typeof renderItem === 'function') {
        const rendered = renderItem(item);
        if (rendered instanceof HTMLElement) {
          li.appendChild(rendered);
        } else if (typeof rendered === 'string') {
          li.textContent = rendered;
        }
      } else if (typeof item === 'string') {
        li.textContent = item;
      }
      list.appendChild(li);
    });

    return list;
  }
}

/**
 * テーブルコンポーネント
 */
class Table {
  /**
   * テーブル作成
   * @param {Object} options - オプション
   * @param {Array} options.headers - ヘッダー配列
   * @param {Array} options.rows - 行データ配列
   * @param {string} options.className - 追加CSSクラス
   * @returns {HTMLTableElement}
   */
  static create({ headers = [], rows = [], className = '' }) {
    const table = DOMHelper.createElement('table', { class: className });

    // ヘッダー
    if (headers.length > 0) {
      const thead = DOMHelper.createElement('thead');
      const headerRow = DOMHelper.createElement('tr');
      headers.forEach(header => {
        const th = DOMHelper.createElement('th', {}, header);
        headerRow.appendChild(th);
      });
      thead.appendChild(headerRow);
      table.appendChild(thead);
    }

    // ボディ
    if (rows.length > 0) {
      const tbody = DOMHelper.createElement('tbody');
      rows.forEach(row => {
        const tr = DOMHelper.createElement('tr');
        row.forEach(cell => {
          const td = DOMHelper.createElement('td');
          if (cell instanceof HTMLElement) {
            td.appendChild(cell);
          } else {
            td.textContent = cell;
          }
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });
      table.appendChild(tbody);
    }

    return table;
  }
}

// グローバル公開（既存コード互換性）
if (typeof window !== 'undefined') {
  window.List = List;
  window.Table = Table;
}

export { List, Table };
export default { List, Table };
