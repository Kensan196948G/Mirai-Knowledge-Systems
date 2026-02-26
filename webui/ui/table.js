/**
 * Table Component - Table rendering with pagination & sorting
 * Mirai Knowledge Systems v1.5.0
 *
 * テーブル描画・ページネーション・ソート機能
 * - セキュアDOM操作（innerHTML完全排除）
 * - ページネーション制御
 * - ソート機能
 * - 検索フィルタ対応
 */

import DOMHelper from './dom-utils.js';

/**
 * テーブルマネージャークラス
 */
class TableManager {
  /**
   * テーブル作成
   * @param {Object} options - オプション
   * @param {Array} options.columns - カラム定義 [{key, label, sortable, width}]
   * @param {Array} options.data - データ配列
   * @param {Object} options.pagination - ページネーション設定 {currentPage, totalPages, pageSize, onPageChange}
   * @param {Function} options.onRowClick - 行クリックハンドラ
   * @param {Function} options.onSort - ソートハンドラ
   * @param {string} options.className - 追加CSSクラス
   * @returns {HTMLTableElement}
   */
  static create({
    columns = [],
    data = [],
    pagination = null,
    onRowClick = null,
    onSort = null,
    className = 'data-table'
  }) {
    const container = DOMHelper.createElement('div', { class: 'table-container' });
    const table = DOMHelper.createElement('table', { class: className });

    // thead作成
    const thead = TableManager._createTableHead(columns, onSort);
    table.appendChild(thead);

    // tbody作成
    const tbody = TableManager._createTableBody(columns, data, onRowClick);
    table.appendChild(tbody);

    container.appendChild(table);

    // tfoot作成（ページネーション）
    if (pagination) {
      const paginationNav = TableManager._createPagination(pagination);
      container.appendChild(paginationNav);
    }

    return container;
  }

  /**
   * テーブルヘッダー作成
   * @private
   * @param {Array} columns - カラム定義
   * @param {Function} onSort - ソートハンドラ
   * @returns {HTMLTableSectionElement}
   */
  static _createTableHead(columns, onSort) {
    const thead = DOMHelper.createElement('thead');
    const tr = DOMHelper.createElement('tr');

    columns.forEach(col => {
      const attrs = {};
      if (col.width) {
        attrs.style = `width: ${col.width}`;
      }

      const th = DOMHelper.createElement('th', attrs, col.label);

      if (col.sortable && onSort) {
        th.style.cursor = 'pointer';
        th.classList.add('sortable');

        // ソートアイコン追加
        const sortIcon = DOMHelper.createElement('span', {
          class: 'sort-icon',
          'data-sort-key': col.key
        });
        th.appendChild(sortIcon);

        th.addEventListener('click', () => {
          onSort(col.key);
        });
      }

      tr.appendChild(th);
    });

    thead.appendChild(tr);
    return thead;
  }

  /**
   * テーブルボディ作成
   * @private
   * @param {Array} columns - カラム定義
   * @param {Array} data - データ配列
   * @param {Function} onRowClick - 行クリックハンドラ
   * @returns {HTMLTableSectionElement}
   */
  static _createTableBody(columns, data, onRowClick) {
    const tbody = DOMHelper.createElement('tbody');

    if (data.length === 0) {
      // データなし表示
      const tr = DOMHelper.createElement('tr', { class: 'no-data' });
      const td = DOMHelper.createElement('td', {
        colspan: columns.length.toString(),
        style: 'text-align: center; padding: 2rem; color: #666;'
      }, 'データがありません');
      tr.appendChild(td);
      tbody.appendChild(tr);
      return tbody;
    }

    data.forEach((row, index) => {
      const tr = DOMHelper.createElement('tr', {
        'data-row-index': index.toString()
      });

      if (onRowClick) {
        tr.style.cursor = 'pointer';
        tr.classList.add('clickable-row');
        tr.addEventListener('click', () => onRowClick(row, index));
      }

      columns.forEach(col => {
        const td = DOMHelper.createElement('td');

        // カラム定義にrenderがあればそれを使用
        if (col.render && typeof col.render === 'function') {
          const rendered = col.render(row[col.key], row, index);
          if (rendered instanceof HTMLElement) {
            td.appendChild(rendered);
          } else {
            td.textContent = String(rendered || '');
          }
        } else {
          // デフォルトはテキスト表示
          const value = row[col.key];
          td.textContent = value !== null && value !== undefined ? String(value) : '';
        }

        tr.appendChild(td);
      });

      tbody.appendChild(tr);
    });

    return tbody;
  }

  /**
   * ページネーション作成
   * @private
   * @param {Object} pagination - ページネーション設定
   * @param {number} pagination.currentPage - 現在ページ
   * @param {number} pagination.totalPages - 総ページ数
   * @param {number} pagination.pageSize - ページサイズ
   * @param {number} pagination.totalItems - 総アイテム数
   * @param {Function} pagination.onPageChange - ページ変更ハンドラ
   * @returns {HTMLElement}
   */
  static _createPagination(pagination) {
    const { currentPage, totalPages, pageSize, totalItems, onPageChange } = pagination;

    const nav = DOMHelper.createElement('nav', {
      class: 'pagination-container',
      role: 'navigation',
      'aria-label': 'ページネーション'
    });

    const paginationDiv = DOMHelper.createElement('div', { class: 'pagination' });

    // 前へボタン
    const prevBtn = DOMHelper.createElement('button', {
      class: 'pagination-btn prev-btn',
      disabled: currentPage === 1,
      'aria-label': '前のページ'
    }, '← 前へ');

    prevBtn.addEventListener('click', () => {
      if (currentPage > 1) {
        onPageChange(currentPage - 1);
      }
    });
    paginationDiv.appendChild(prevBtn);

    // ページ番号表示
    const pageInfo = DOMHelper.createElement('span', {
      class: 'pagination-info',
      'aria-live': 'polite'
    });

    const pageText = DOMHelper.createElement('span', {},
      `ページ ${currentPage} / ${totalPages}`
    );
    pageInfo.appendChild(pageText);

    if (totalItems !== undefined) {
      const itemsText = DOMHelper.createElement('span', {
        class: 'items-info',
        style: 'margin-left: 1rem; color: #666; font-size: 0.9em;'
      }, `（全 ${totalItems} 件）`);
      pageInfo.appendChild(itemsText);
    }

    paginationDiv.appendChild(pageInfo);

    // 次へボタン
    const nextBtn = DOMHelper.createElement('button', {
      class: 'pagination-btn next-btn',
      disabled: currentPage === totalPages || totalPages === 0,
      'aria-label': '次のページ'
    }, '次へ →');

    nextBtn.addEventListener('click', () => {
      if (currentPage < totalPages) {
        onPageChange(currentPage + 1);
      }
    });
    paginationDiv.appendChild(nextBtn);

    nav.appendChild(paginationDiv);

    // ページサイズ選択（オプション）
    if (pageSize !== undefined) {
      const pageSizeDiv = TableManager._createPageSizeSelector(pageSize, pagination.onPageSizeChange);
      nav.appendChild(pageSizeDiv);
    }

    return nav;
  }

  /**
   * ページサイズ選択UI作成
   * @private
   * @param {number} currentPageSize - 現在のページサイズ
   * @param {Function} onPageSizeChange - ページサイズ変更ハンドラ
   * @returns {HTMLElement}
   */
  static _createPageSizeSelector(currentPageSize, onPageSizeChange) {
    if (!onPageSizeChange) return DOMHelper.createElement('div');

    const div = DOMHelper.createElement('div', { class: 'page-size-selector' });

    const label = DOMHelper.createElement('label', {
      for: 'page-size-select',
      style: 'margin-right: 0.5rem;'
    }, '表示件数:');
    div.appendChild(label);

    const select = DOMHelper.createElement('select', {
      id: 'page-size-select',
      class: 'page-size-select'
    });

    const pageSizes = [10, 20, 50, 100];
    pageSizes.forEach(size => {
      const option = DOMHelper.createElement('option', {
        value: size.toString(),
        selected: size === currentPageSize
      }, `${size}件`);
      select.appendChild(option);
    });

    select.addEventListener('change', (e) => {
      const newSize = parseInt(e.target.value, 10);
      onPageSizeChange(newSize);
    });

    div.appendChild(select);
    return div;
  }

  /**
   * テーブル更新（既存のテーブルコンテナを更新）
   * @param {HTMLElement} container - テーブルコンテナ
   * @param {Object} options - テーブルオプション
   */
  static update(container, options) {
    if (!container) return;

    // 古いコンテンツをクリア
    container.textContent = '';

    // 新しいテーブルを作成して追加
    const newTable = TableManager.create(options);
    while (newTable.firstChild) {
      container.appendChild(newTable.firstChild);
    }
  }

  /**
   * ソート状態の更新（ヘッダーにソートアイコンを追加）
   * @param {HTMLElement} tableContainer - テーブルコンテナ
   * @param {string} sortKey - ソートキー
   * @param {string} sortOrder - ソート順序 ('asc' | 'desc')
   */
  static updateSortIndicator(tableContainer, sortKey, sortOrder) {
    if (!tableContainer) return;

    // 全てのソートアイコンをリセット
    const sortIcons = tableContainer.querySelectorAll('.sort-icon');
    sortIcons.forEach(icon => {
      icon.textContent = '';
      icon.classList.remove('asc', 'desc');
    });

    // 対象のソートアイコンを更新
    const targetIcon = tableContainer.querySelector(`[data-sort-key="${sortKey}"]`);
    if (targetIcon) {
      targetIcon.textContent = sortOrder === 'asc' ? ' ▲' : ' ▼';
      targetIcon.classList.add(sortOrder);
    }
  }
}

// グローバル公開（既存コード互換性）
if (typeof window !== 'undefined') {
  window.TableManager = TableManager;
}

// ES6モジュールエクスポート
export { TableManager };
export default TableManager;
