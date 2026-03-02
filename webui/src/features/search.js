/**
 * @fileoverview 統合検索機能モジュール v2.0.0
 * @module features/search
 * @description Phase F-2 ESモジュール化版
 *   app.js から検索・検索履歴関連の関数を抽出してESM化。
 *   - 統合検索（キーワード・カテゴリ・日付・タグ・プロジェクト）
 *   - 高度な検索フォーム処理
 *   - ヒーロー検索
 *   - 検索結果表示（DOM API 使用、innerHTML 禁止）
 *   - 検索履歴管理（localStorage）
 *   - 人気検索ワード取得
 */

import { fetchAPI } from '../core/api-client.js';
import { logger } from '../core/logger.js';

// ============================================================
// 検索 API 関数
// ============================================================

/**
 * 統合検索を実行
 * @param {string} query - 検索クエリ
 * @param {Object} [options={}] - 検索オプション
 * @param {string} [options.category] - カテゴリフィルター
 * @param {string} [options.date_from] - 開始日（YYYY-MM-DD）
 * @param {string} [options.date_to] - 終了日（YYYY-MM-DD）
 * @param {string} [options.tags] - タグフィルター（カンマ区切り）
 * @param {string} [options.project] - プロジェクトフィルター
 * @returns {Promise<Array>} 検索結果の配列
 */
export async function searchUnified(query, options = {}) {
  const params = {
    keyword: query,
    ...options
  };

  // 空のパラメータを削除
  Object.keys(params).forEach(key => {
    if (!params[key]) delete params[key];
  });

  const queryParams = new URLSearchParams(params).toString();
  logger.debug('[Search] Searching:', query, options);

  try {
    const result = await fetchAPI(`/knowledge/search?${queryParams}`);
    logger.debug('[Search] Results found:', result.data?.length || 0);
    return result.data || [];
  } catch (error) {
    logger.error('[Search] Search failed:', error);
    throw error;
  }
}

/**
 * キーワード検索を実行（シンプル版）
 * @param {string} keyword - 検索キーワード
 * @returns {Promise<Array>} 検索結果の配列
 */
export async function searchKnowledge(keyword) {
  try {
    const result = await fetchAPI(`/knowledge/search?keyword=${encodeURIComponent(keyword)}`);
    return result.data || [];
  } catch (error) {
    logger.error('[Search] Knowledge search failed:', error);
    throw error;
  }
}

/**
 * ナレッジ一覧を取得（フィルター付き）
 * @param {Object} [params={}] - URLパラメータ
 * @returns {Promise<Array>} ナレッジの配列
 */
export async function getKnowledgeList(params = {}) {
  const queryParams = new URLSearchParams(params).toString();
  const endpoint = `/knowledge${queryParams ? '?' + queryParams : ''}`;

  try {
    const result = await fetchAPI(endpoint);
    return result.data || [];
  } catch (error) {
    logger.error('[Search] Failed to get knowledge list:', error);
    throw error;
  }
}

/**
 * 人気の検索ワードを取得
 * @param {number} [limit=10] - 取得件数
 * @returns {Promise<Array>} 人気検索ワードの配列
 */
export async function getPopularSearchTerms(limit = 10) {
  try {
    const result = await fetchAPI(`/knowledge/search/popular?limit=${limit}`);
    return result.data || [];
  } catch (error) {
    logger.warn('[Search] Failed to get popular search terms:', error);
    return [];
  }
}

// ============================================================
// 検索履歴管理（localStorage）
// ============================================================

/** @constant {string} localStorage のキー */
const SEARCH_HISTORY_KEY = 'mks_search_history';

/** @constant {number} 最大履歴保持件数 */
const MAX_HISTORY_SIZE = 50;

/**
 * 検索履歴を取得
 * @param {number} [limit=10] - 取得件数
 * @returns {Array<Object>} 検索履歴の配列 [{query, types, timestamp}]
 */
export function getSearchHistory(limit = 10) {
  try {
    const stored = localStorage.getItem(SEARCH_HISTORY_KEY);
    if (!stored) return [];
    const history = JSON.parse(stored);
    return Array.isArray(history) ? history.slice(0, limit) : [];
  } catch (error) {
    logger.warn('[Search] Failed to get search history:', error);
    return [];
  }
}

/**
 * 検索履歴にクエリを追加
 * @param {string} query - 検索クエリ
 * @param {string|string[]} [types='knowledge'] - 検索タイプ
 * @returns {void}
 */
export function addSearchHistory(query, types = 'knowledge') {
  if (!query || !query.trim()) return;

  try {
    const history = getSearchHistory(MAX_HISTORY_SIZE);
    const newEntry = {
      query: query.trim(),
      types: Array.isArray(types) ? types : [types],
      timestamp: new Date().toISOString()
    };

    // 重複を削除（同じクエリの古いエントリを除去）
    const filtered = history.filter(h => h.query !== newEntry.query);

    // 先頭に追加
    filtered.unshift(newEntry);

    // 最大件数に切り詰め
    const trimmed = filtered.slice(0, MAX_HISTORY_SIZE);

    localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(trimmed));
    logger.debug('[Search] Search history updated:', query);
  } catch (error) {
    logger.warn('[Search] Failed to save search history:', error);
  }
}

/**
 * 検索履歴をクリア
 * @returns {void}
 */
export function clearSearchHistory() {
  try {
    localStorage.removeItem(SEARCH_HISTORY_KEY);
    logger.debug('[Search] Search history cleared');
  } catch (error) {
    logger.warn('[Search] Failed to clear search history:', error);
  }
}

/**
 * 検索履歴から特定のエントリを削除
 * @param {string} query - 削除するクエリ
 * @returns {void}
 */
export function removeSearchHistoryEntry(query) {
  try {
    const history = getSearchHistory(MAX_HISTORY_SIZE);
    const filtered = history.filter(h => h.query !== query);
    localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(filtered));
    logger.debug('[Search] Removed history entry:', query);
  } catch (error) {
    logger.warn('[Search] Failed to remove history entry:', error);
  }
}

// ============================================================
// フォーム処理関数
// ============================================================

/**
 * 高度な検索フォームの送信処理
 * @param {Event} event - フォームのsubmitイベント
 * @param {Function} [onResults] - 結果受け取りコールバック（省略時はdisplaySearchResults使用）
 * @returns {Promise<void>}
 */
export async function submitAdvancedSearch(event, onResults) {
  event.preventDefault();

  const form = event.target;
  const formData = new FormData(form);

  const params = {
    keyword: formData.get('keyword'),
    category: formData.get('category'),
    date_from: formData.get('dateFrom'),
    date_to: formData.get('dateTo'),
    tags: formData.get('tags'),
    project: formData.get('project')
  };

  Object.keys(params).forEach(key => {
    if (!params[key]) delete params[key];
  });

  try {
    const results = await searchUnified(params.keyword || '', params);

    if (typeof onResults === 'function') {
      onResults(results);
    } else {
      displaySearchResults(results);
    }

    if (params.keyword) {
      addSearchHistory(params.keyword);
    }

    logger.debug(`[Search] Advanced search: ${results.length} results found`);
  } catch (error) {
    logger.error('[Search] Advanced search failed:', error);
    throw error;
  }
}

/**
 * ヒーローセクションの検索を実行
 * @param {string} [inputId='heroSearchInput'] - 検索入力フィールドのID
 * @param {Function} [onResults] - 結果受け取りコールバック
 * @returns {Promise<void>}
 */
export async function performHeroSearch(inputId = 'heroSearchInput', onResults) {
  const input = document.getElementById(inputId);
  if (!input) return;

  const keyword = input.value.trim();
  if (!keyword) {
    logger.warn('[Search] performHeroSearch: Empty keyword');
    return;
  }

  try {
    const results = await searchKnowledge(keyword);
    addSearchHistory(keyword);

    if (typeof onResults === 'function') {
      onResults(results, keyword);
    } else {
      displaySearchResults(results);
    }

    logger.debug(`[Search] Hero search: ${results.length} results for "${keyword}"`);
  } catch (error) {
    logger.error('[Search] Hero search failed:', error);
    throw error;
  }
}

// ============================================================
// UI 表示関数（DOM API 使用、innerHTML 禁止）
// ============================================================

/**
 * 検索結果を表示
 * @param {Array} results - 検索結果の配列
 * @param {string} [containerId='searchResults'] - 結果表示コンテナのID
 */
export function displaySearchResults(results, containerId = 'searchResults') {
  const resultsDiv = document.getElementById(containerId);
  if (!resultsDiv) {
    logger.warn('[Search] displaySearchResults: Container not found:', containerId);
    return;
  }

  resultsDiv.textContent = '';

  if (!results || results.length === 0) {
    const emptyMsg = document.createElement('div');
    emptyMsg.className = 'empty-message';
    emptyMsg.textContent = '検索結果がありません';
    resultsDiv.appendChild(emptyMsg);
    return;
  }

  results.forEach(item => {
    const card = document.createElement('div');
    card.className = 'knowledge-card';
    card.style.cursor = 'pointer';
    card.addEventListener('click', () => {
      window.location.href = `search-detail.html?id=${item.id}`;
    });

    const title = document.createElement('h4');
    title.textContent = item.title || '';

    const meta = document.createElement('div');
    meta.className = 'knowledge-meta';
    meta.textContent = `${item.category || ''} · ${_formatDate(item.updated_at)}`;

    const summary = document.createElement('div');
    summary.textContent = item.summary || '';

    card.appendChild(title);
    card.appendChild(meta);
    card.appendChild(summary);

    resultsDiv.appendChild(card);
  });
}

/**
 * 検索履歴一覧を表示
 * @param {Array<Object>} history - 検索履歴の配列
 * @param {string} [containerId='searchHistoryList'] - 表示コンテナのID
 * @param {Function} [onSelect] - 履歴選択時のコールバック
 */
export function displaySearchHistory(history, containerId = 'searchHistoryList', onSelect) {
  const container = document.getElementById(containerId);
  if (!container) return;

  container.textContent = '';

  if (!history || history.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'empty-message';
    empty.textContent = '検索履歴がありません';
    container.appendChild(empty);
    return;
  }

  history.forEach(entry => {
    const item = document.createElement('div');
    item.className = 'search-history-item';

    const querySpan = document.createElement('span');
    querySpan.className = 'search-history-query';
    querySpan.textContent = entry.query;

    const timeSpan = document.createElement('span');
    timeSpan.className = 'search-history-time';
    timeSpan.textContent = _formatDate(entry.timestamp);

    item.appendChild(querySpan);
    item.appendChild(timeSpan);

    item.addEventListener('click', () => {
      if (typeof onSelect === 'function') {
        onSelect(entry.query);
      }
    });

    container.appendChild(item);
  });
}

// ============================================================
// 内部ヘルパー
// ============================================================

/**
 * 日付をフォーマット
 * @param {string} dateString - 日時文字列
 * @returns {string} フォーマットされた日付
 * @private
 */
function _formatDate(dateString) {
  if (!dateString) return '';

  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  } catch (e) {
    return dateString;
  }
}

// ============================================================
// 後方互換性（window経由のアクセスを維持）
// ============================================================

if (typeof window !== 'undefined') {
  window.SearchModule = {
    searchUnified,
    searchKnowledge,
    getKnowledgeList,
    getPopularSearchTerms,
    getSearchHistory,
    addSearchHistory,
    clearSearchHistory,
    removeSearchHistoryEntry,
    submitAdvancedSearch,
    performHeroSearch,
    displaySearchResults,
    displaySearchHistory,
  };
}
