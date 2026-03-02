/**
 * @fileoverview ナレッジ管理機能モジュール v2.0.0
 * @module features/knowledge
 * @description Phase F-2 ESモジュール化版
 *   app.js からナレッジ管理関連の関数を抽出してESM化。
 *   - ナレッジ一覧取得・詳細取得
 *   - ナレッジ作成・更新・削除
 *   - ナレッジ表示（DOM API 使用、innerHTML 禁止）
 *   - 空データ状態表示
 *   - モーダル管理
 */

import { fetchAPI } from '../core/api-client.js';
import { logger } from '../core/logger.js';

// ============================================================
// ナレッジ API 関数
// ============================================================

/**
 * ナレッジ一覧を取得
 * @param {Object} [params={}] - フィルターパラメータ
 * @param {string} [params.search] - 検索キーワード
 * @param {string} [params.category] - カテゴリフィルター
 * @param {number} [params.page] - ページ番号
 * @param {number} [params.per_page] - 1ページあたりの件数
 * @returns {Promise<Object>} ナレッジ一覧レスポンス
 */
export async function getKnowledgeList(params = {}) {
  const queryParams = new URLSearchParams(params).toString();
  const endpoint = `/knowledge${queryParams ? '?' + queryParams : ''}`;

  try {
    const result = await fetchAPI(endpoint);
    logger.debug('[Knowledge] List loaded:', result.data?.length || 0, 'items');
    return result;
  } catch (error) {
    logger.error('[Knowledge] Failed to get knowledge list:', error);
    throw error;
  }
}

/**
 * ナレッジ詳細を取得
 * @param {string|number} id - ナレッジID
 * @returns {Promise<Object>} ナレッジ詳細レスポンス
 */
export async function getKnowledgeDetail(id) {
  try {
    const result = await fetchAPI(`/knowledge/${id}`);
    logger.debug('[Knowledge] Detail loaded:', id);
    return result;
  } catch (error) {
    logger.error('[Knowledge] Failed to get knowledge detail:', id, error);
    throw error;
  }
}

/**
 * ナレッジを作成
 * @param {Object} data - ナレッジデータ
 * @param {string} data.title - タイトル（必須）
 * @param {string} data.category - カテゴリ（必須）
 * @param {string} data.content - 本文（必須）
 * @param {string} [data.summary] - サマリー
 * @param {string} [data.priority] - 優先度
 * @param {string} [data.project] - プロジェクト
 * @param {string[]} [data.tags] - タグの配列
 * @returns {Promise<Object>} 作成結果レスポンス
 */
export async function createKnowledge(data) {
  try {
    const result = await fetchAPI('/knowledge', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    logger.debug('[Knowledge] Created:', result.data?.id);
    return result;
  } catch (error) {
    logger.error('[Knowledge] Failed to create knowledge:', error);
    throw error;
  }
}

/**
 * ナレッジを更新
 * @param {string|number} id - ナレッジID
 * @param {Object} data - 更新データ
 * @returns {Promise<Object>} 更新結果レスポンス
 */
export async function updateKnowledge(id, data) {
  try {
    const result = await fetchAPI(`/knowledge/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
    logger.debug('[Knowledge] Updated:', id);
    return result;
  } catch (error) {
    logger.error('[Knowledge] Failed to update knowledge:', id, error);
    throw error;
  }
}

/**
 * ナレッジを削除
 * @param {string|number} id - ナレッジID
 * @returns {Promise<Object>} 削除結果レスポンス
 */
export async function deleteKnowledge(id) {
  try {
    const result = await fetchAPI(`/knowledge/${id}`, {
      method: 'DELETE'
    });
    logger.debug('[Knowledge] Deleted:', id);
    return result;
  } catch (error) {
    logger.error('[Knowledge] Failed to delete knowledge:', id, error);
    throw error;
  }
}

/**
 * ナレッジを読み込んで表示
 * @param {Object} [params={}] - フィルターパラメータ
 * @returns {Promise<void>}
 */
export async function loadKnowledge(params = {}) {
  try {
    const result = await getKnowledgeList(params);
    if (result.success) {
      displayKnowledge(result.data);
    }
  } catch (error) {
    logger.debug('[Knowledge] Using static data (API unavailable)');
  }
}

// ============================================================
// モーダル管理
// ============================================================

/**
 * 新規ナレッジ作成モーダルを開く
 */
export function openNewKnowledgeModal() {
  const modal = document.getElementById('newKnowledgeModal');
  if (!modal) {
    logger.warn('[Knowledge] openNewKnowledgeModal: Modal not found');
    return;
  }
  modal.style.display = 'flex';
  modal.setAttribute('aria-hidden', 'false');
}

/**
 * 新規ナレッジ作成モーダルを閉じる
 */
export function closeNewKnowledgeModal() {
  const modal = document.getElementById('newKnowledgeModal');
  if (!modal) return;

  modal.style.display = 'none';
  modal.setAttribute('aria-hidden', 'true');

  const form = document.getElementById('newKnowledgeForm');
  if (form) form.reset();
}

/**
 * 新規ナレッジ作成フォームの送信処理
 * @param {Event} event - フォームのsubmitイベント
 * @returns {Promise<void>}
 */
export async function submitNewKnowledge(event) {
  event.preventDefault();

  const form = event.target;
  const formData = new FormData(form);

  const data = {
    title: formData.get('title'),
    category: formData.get('category'),
    priority: formData.get('priority'),
    project: formData.get('project') || null,
    summary: formData.get('summary'),
    content: formData.get('content'),
    tags: formData.get('tags')
      ? formData.get('tags').split(',').map(t => t.trim()).filter(t => t)
      : []
  };

  try {
    const result = await createKnowledge(data);
    if (result.success) {
      logger.debug('[Knowledge] New knowledge created successfully');
      closeNewKnowledgeModal();
      await loadKnowledge();
    }
    return result;
  } catch (error) {
    logger.error('[Knowledge] Failed to create knowledge:', error);
    throw error;
  }
}

/**
 * ナレッジ編集（詳細ページへ遷移）
 * @param {string|number} knowledgeId - ナレッジID
 * @param {string|number} [creatorId] - 作成者ID（権限チェック用）
 */
export function editKnowledge(knowledgeId, creatorId) {
  logger.debug('[Knowledge] Navigating to edit:', knowledgeId);
  window.location.href = `search-detail.html?id=${knowledgeId}&mode=edit`;
}

// ============================================================
// UI 表示関数（DOM API 使用、innerHTML 禁止）
// ============================================================

/**
 * ナレッジ一覧を表示
 * @param {Array} knowledgeList - ナレッジの配列
 * @param {string} [panelSelector='[data-panel="search"]'] - 表示先パネルのセレクター
 */
export function displayKnowledge(knowledgeList, panelSelector = '[data-panel="search"]') {
  const panel = document.querySelector(panelSelector);
  if (!panel) {
    logger.warn('[Knowledge] displayKnowledge: Panel not found:', panelSelector);
    return;
  }

  panel.textContent = '';

  if (!knowledgeList || knowledgeList.length === 0) {
    showEmptyState(panel, 'ナレッジ');
    return;
  }

  knowledgeList.forEach(k => {
    const card = _createKnowledgeCard(k);
    panel.appendChild(card);
  });
}

/**
 * 空データ状態を表示
 * @param {HTMLElement} container - 表示先のコンテナ要素
 * @param {string} dataType - データの種類（ナレッジ、SOP、事故レポート等）
 * @param {string} [icon='empty'] - 表示アイコンテキスト
 */
export function showEmptyState(container, dataType, icon = 'empty') {
  if (!container) return;

  container.textContent = '';

  const emptyState = document.createElement('div');
  emptyState.className = 'empty-state';
  emptyState.style.cssText = [
    'display: flex',
    'flex-direction: column',
    'align-items: center',
    'justify-content: center',
    'padding: 40px 20px',
    'text-align: center',
    'color: #64748b',
    'background: #f8fafc',
    'border-radius: 8px',
    'border: 1px dashed #cbd5e1',
  ].join(';');

  const iconEl = document.createElement('div');
  iconEl.className = 'empty-state-icon';
  iconEl.textContent = icon;
  iconEl.style.cssText = 'font-size: 48px; margin-bottom: 16px; opacity: 0.6;';
  emptyState.appendChild(iconEl);

  const messageEl = document.createElement('div');
  messageEl.className = 'empty-state-message';
  messageEl.textContent = `${dataType}データなし`;
  messageEl.style.cssText = 'font-size: 16px; font-weight: 500; margin-bottom: 8px;';
  emptyState.appendChild(messageEl);

  const hintEl = document.createElement('div');
  hintEl.className = 'empty-state-hint';
  hintEl.textContent = 'データが登録されていません。';
  hintEl.style.cssText = 'font-size: 14px; color: #94a3b8;';
  emptyState.appendChild(hintEl);

  container.appendChild(emptyState);
}

/**
 * データがあるかチェックし、なければ空状態を表示
 * @param {Array} data - チェックするデータ配列
 * @param {HTMLElement} container - 表示先のコンテナ
 * @param {string} dataType - データの種類
 * @returns {boolean} データがある場合はtrue
 */
export function checkAndShowEmptyState(data, container, dataType) {
  if (!data || data.length === 0) {
    showEmptyState(container, dataType);
    return false;
  }
  return true;
}

// ============================================================
// 内部ヘルパー関数
// ============================================================

/**
 * ナレッジカードのDOM要素を作成
 * @param {Object} k - ナレッジオブジェクト
 * @returns {HTMLElement} カード要素
 * @private
 */
function _createKnowledgeCard(k) {
  const card = document.createElement('div');
  card.className = 'knowledge-card';

  if (k.title && k.title.includes('[サンプル]')) {
    card.style.borderLeft = '3px solid #f59e0b';
  }

  const cardHeader = document.createElement('div');
  cardHeader.className = 'knowledge-card-header';

  const titleEl = document.createElement('h4');
  titleEl.className = 'knowledge-title';
  titleEl.textContent = k.title || '';
  titleEl.style.cursor = 'pointer';
  titleEl.addEventListener('click', () => {
    window.location.href = `search-detail.html?id=${k.id}`;
  });

  cardHeader.appendChild(titleEl);

  const actionButtons = document.createElement('div');
  actionButtons.className = 'knowledge-actions';

  const viewBtn = document.createElement('button');
  viewBtn.className = 'btn-secondary btn-sm';
  viewBtn.textContent = '詳細';
  viewBtn.addEventListener('click', () => {
    window.location.href = `search-detail.html?id=${k.id}`;
  });
  actionButtons.appendChild(viewBtn);

  const editBtn = document.createElement('button');
  editBtn.className = 'btn-primary btn-sm';
  editBtn.textContent = '編集';
  editBtn.addEventListener('click', () => {
    editKnowledge(k.id, k.creator_id);
  });
  actionButtons.appendChild(editBtn);

  cardHeader.appendChild(actionButtons);
  card.appendChild(cardHeader);

  const meta = document.createElement('div');
  meta.className = 'knowledge-meta';
  meta.textContent = `${k.category || ''} · ${_formatDate(k.updated_at)}`;
  card.appendChild(meta);

  if (k.summary) {
    const summary = document.createElement('div');
    summary.className = 'knowledge-summary';
    summary.textContent = k.summary;
    card.appendChild(summary);
  }

  if (k.tags && k.tags.length > 0) {
    const tagsContainer = document.createElement('div');
    tagsContainer.className = 'knowledge-tags';

    k.tags.forEach(tag => {
      const tagEl = document.createElement('span');
      tagEl.className = 'tag';
      tagEl.textContent = tag;
      tagsContainer.appendChild(tagEl);
    });

    card.appendChild(tagsContainer);
  }

  return card;
}

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
  window.KnowledgeModule = {
    getKnowledgeList,
    getKnowledgeDetail,
    createKnowledge,
    updateKnowledge,
    deleteKnowledge,
    loadKnowledge,
    openNewKnowledgeModal,
    closeNewKnowledgeModal,
    submitNewKnowledge,
    editKnowledge,
    displayKnowledge,
    showEmptyState,
    checkAndShowEmptyState,
  };
}
