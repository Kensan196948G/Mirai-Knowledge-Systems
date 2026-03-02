/**
 * @fileoverview ナレッジ詳細ページモジュール v2.0.0
 * @module pages/knowledge-detail
 * @description Phase F-4: detail-pages.js 分割版 - ナレッジ詳細ページ
 *
 * 担当機能:
 * - ナレッジ詳細読み込み (loadKnowledgeDetail)
 * - ナレッジ詳細表示 (displayKnowledgeDetail)
 * - パンくずメタ情報更新 (updateBreadcrumbMeta)
 * - ナビゲーション情報更新 (updateNavigationInfo)
 * - 関連ナレッジ読み込み (loadRelatedKnowledge)
 * - コメント管理 (loadKnowledgeCommentsFromData / loadKnowledgeComments / submitComment)
 * - 編集履歴管理 (loadKnowledgeHistoryFromData / loadKnowledgeHistory)
 * - いいね・ブックマーク (toggleLike / toggleBookmark)
 * - 閲覧数更新 (incrementViewCount)
 * - 編集機能 (editKnowledge / saveKnowledgeEdit / closeEditModal / createNewKnowledge)
 * - 共有機能 (shareKnowledge)
 *
 * 依存: page-renderer.js (showLoading, hideLoading, showError, hideError,
 *       formatDate, formatDateShort, updateElement, displayApprovalFlow, updateBreadcrumb, apiCall)
 * 依存: dom-helpers.js (setSecureChildren, createSecureElement, createMetaInfoElement,
 *       createTagElement, createTableRow, createTableRowWithHTML, createCommentElement,
 *       createDocumentElement, createEmptyMessage, createErrorMessage)
 */

// ============================================================
// ナレッジ詳細読み込み
// ============================================================

/**
 * ナレッジ詳細データを読み込む（URL の ?id= から ID を取得）
 */
async function loadKnowledgeDetail() {
  const log = window.logger || console;
  log.log('[KNOWLEDGE DETAIL] Starting to load...');
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');
  const inProduction = typeof isProductionMode === 'function' ? isProductionMode() : false;

  log.log('[KNOWLEDGE DETAIL] ID from URL:', id, 'Production mode:', inProduction);

  if (!id) {
    if (typeof showError === 'function') showError('ナレッジIDが指定されていません。一覧ページに戻ります...');
    setTimeout(() => {
      window.location.href = 'index.html';
    }, 2000);
    return;
  }

  if (typeof showLoading === 'function') showLoading();
  if (typeof hideError === 'function') hideError();

  try {
    let data = null;

    log.log('[DETAIL] Loading from API (data consistency fix)...');
    try {
      const response = await apiCall(`/knowledge/${id}`);
      log.log('[DETAIL] API Response:', response);

      data = response?.data || response;

      log.log('[DETAIL] Extracted data:', data);
      log.log('[DETAIL] Title:', data?.title);
      log.log('[DETAIL] Summary:', data?.summary);
      log.log('[DETAIL] Successfully loaded from API');
    } catch (apiError) {
      log.error('[DETAIL] API call failed:', apiError);

      const knowledgeDataStr = localStorage.getItem('knowledge_details');
      if (knowledgeDataStr) {
        log.log('[DETAIL] Fallback to localStorage...');
        const knowledgeData = JSON.parse(knowledgeDataStr);
        data = knowledgeData.find(k => k.id === parseInt(id));
        if (data) {
          log.warn('[DETAIL] Using localStorage data (may be outdated)');
        }
      }
    }

    if (!data) {
      log.error('[DETAIL] No data found for ID:', id);
      if (typeof showError === 'function') showError(`ナレッジID ${id} が見つかりません`);
      return;
    }

    log.log('[KNOWLEDGE DETAIL] Data before display:', JSON.stringify(data, null, 2));
    log.log('[KNOWLEDGE DETAIL] Displaying data...');
    displayKnowledgeDetail(data);
    await loadRelatedKnowledge(data.tags || [], id);
    loadKnowledgeCommentsFromData(data);
    loadKnowledgeHistoryFromData(data);
  } catch (error) {
    log.error('[KNOWLEDGE DETAIL] Error:', error);
    if (typeof showError === 'function') showError(`データの読み込みに失敗しました: ${error.message}`);
  } finally {
    if (typeof hideLoading === 'function') hideLoading();
  }
}

// ============================================================
// ナレッジ詳細表示
// ============================================================

/**
 * ナレッジデータを画面に表示する
 * @param {Object} data - ナレッジデータオブジェクト
 */
function displayKnowledgeDetail(data) {
  const log = window.logger || console;
  log.log('[DISPLAY] displayKnowledgeDetail called with data:', data);
  log.log('[DISPLAY] Title:', data?.title);
  log.log('[DISPLAY] Summary:', data?.summary);
  log.log('[DISPLAY] Content length:', data?.content?.length);

  // タイトル
  const titleEl = document.getElementById('knowledgeTitle');
  log.log('[DISPLAY] titleEl found:', !!titleEl);
  if (titleEl) {
    const titleText = data.title || 'タイトルなし';
    titleEl.textContent = titleText;
    log.log('[DISPLAY] Title set to:', titleText);
  }

  // メタ情報
  const metaEl = document.getElementById('knowledgeMeta');
  if (metaEl && typeof createMetaInfoElement === 'function') {
    if (typeof setSecureChildren === 'function') {
      setSecureChildren(metaEl, createMetaInfoElement({
        category: data.category || 'N/A',
        updated_at: data.updated_at,
        created_by: data.created_by || data.created_by_name || data.owner || 'N/A',
        project: data.project || 'N/A'
      }, 'knowledge'));
    }
  }

  // タグ
  const tagsEl = document.getElementById('knowledgeTags');
  if (tagsEl && data.tags) {
    while (tagsEl.firstChild) {
      tagsEl.removeChild(tagsEl.firstChild);
    }
    data.tags.forEach(tag => {
      const tagSpan = document.createElement('span');
      tagSpan.className = 'tag';
      tagSpan.textContent = tag;
      tagsEl.appendChild(tagSpan);
    });
  }

  // 概要
  const summaryEl = document.getElementById('knowledgeSummary');
  if (summaryEl) {
    while (summaryEl.firstChild) {
      summaryEl.removeChild(summaryEl.firstChild);
    }
    const p = document.createElement('p');
    p.textContent = data.summary || '概要がありません';
    summaryEl.appendChild(p);
  }

  // 本文
  const contentEl = document.getElementById('knowledgeContent');
  if (contentEl) {
    while (contentEl.firstChild) {
      contentEl.removeChild(contentEl.firstChild);
    }
    const div = document.createElement('div');
    div.style.whiteSpace = 'pre-wrap';
    div.textContent = data.content || '内容がありません';
    contentEl.appendChild(div);
  }

  // メタデータテーブル
  const metadataTable = document.getElementById('metadataTable');
  if (metadataTable && typeof createTableRow === 'function' && typeof setSecureChildren === 'function') {
    const rows = [
      { label: '作成日', value: formatDate(data.created_at) },
      { label: '最終更新', value: formatDate(data.updated_at) },
      { label: '作成者', value: data.created_by || data.created_by_name || data.owner || 'N/A' },
      { label: 'カテゴリ', value: data.category || 'N/A' },
      { label: 'プロジェクト', value: data.project || 'N/A' },
      { label: 'ステータス', value: data.status || '公開' }
    ];
    setSecureChildren(metadataTable, rows.map(row => createTableRow([row.label, row.value])));
  }

  // 統計情報
  if (typeof updateElement === 'function') {
    updateElement('totalLikes', data.likes || data.likes_count || 0);
    updateElement('totalBookmarks', data.bookmarks_count || 0);
    updateElement('totalViews', data.views || data.views_count || 0);
    updateElement('viewCount', `閲覧数 ${data.views || data.views_count || 0}`);
  }

  // 承認フロー
  if (typeof displayApprovalFlow === 'function') displayApprovalFlow(data.approval_status);

  // パンくずリスト更新
  if (typeof updateBreadcrumb === 'function') updateBreadcrumb(data.category, data.title);

  // パンくずエリアのメタ情報を更新
  updateBreadcrumbMeta(data);

  // 左側ナビゲーションの情報を更新
  updateNavigationInfo(data);
}

// ============================================================
// パンくず・ナビゲーション更新
// ============================================================

/**
 * パンくずエリアのメタ情報を更新
 * @param {Object} data - ナレッジデータ
 */
function updateBreadcrumbMeta(data) {
  const statusText = {
    'approved': '承認状態: ✓ 承認済み',
    'pending': '承認状態: ⏳ 承認待ち',
    'draft': '承認状態: 📝 下書き',
    'archived': '承認状態: 📦 アーカイブ'
  }[data.status] || `承認状態: ${data.status}` || '承認状態: 承認済み';
  if (typeof updateElement === 'function') updateElement('breadcrumbStatus', statusText);

  const priorityText = {
    'high': '優先度: 🔴 高',
    'medium': '優先度: 🟡 中',
    'low': '優先度: 🟢 低'
  }[data.priority] || `優先度: ${data.priority}` || '優先度: 中';
  const priorityEl = document.getElementById('breadcrumbPriority');
  if (priorityEl) {
    priorityEl.textContent = priorityText;
    priorityEl.setAttribute('data-priority', data.priority || 'medium');
  }

  if (typeof updateElement === 'function') {
    updateElement('breadcrumbCategory', data.category ? `📋 ${data.category}` : '📋 カテゴリなし');
    updateElement('breadcrumbUpdated', data.updated_at ? `📅 最終更新: ${formatDateShort(data.updated_at)}` : '');
    const viewCount = data.views || data.views_count || 0;
    updateElement('breadcrumbViews', `👁️ 閲覧: ${viewCount}回`);
  }
}

/**
 * 左側ナビゲーションの詳細情報を更新
 * @param {Object} data - ナレッジデータ
 */
function updateNavigationInfo(data) {
  if (typeof updateElement !== 'function') return;

  const summaryLength = (data.summary || '').length;
  updateElement('navSummaryInfo', summaryLength > 0 ? `${summaryLength}文字` : '未記載');

  const contentLength = (data.content || '').length;
  const readingTime = Math.ceil(contentLength / 600);
  updateElement('navContentInfo',
    contentLength > 0 ? `${contentLength}文字・約${readingTime}分` : '未記載'
  );

  const historyCount = (data.history || data.versions || []).length;
  updateElement('navHistoryInfo', historyCount > 0 ? `${historyCount}件` : 'なし');

  const commentCount = data.comments_count || (data.comments || []).length || 0;
  updateElement('navCommentsInfo', `${commentCount}件`);

  updateElement('navRelatedInfo', '読込中...');
}

// ============================================================
// 関連ナレッジ
// ============================================================

/**
 * 関連ナレッジを読み込む（専用 API 使用）
 * @param {Array} tags - タグ配列
 * @param {string|number} currentId - 現在のナレッジ ID
 */
async function loadRelatedKnowledge(tags, currentId) {
  const log = window.logger || console;
  const relatedListEl = document.getElementById('relatedKnowledgeList');
  if (!relatedListEl) return;

  try {
    log.log('[RELATED] Loading related knowledge from dedicated API...');

    const response = await apiCall(`/knowledge/${currentId}/related?limit=5`);
    log.log('[RELATED] Full API response:', response);

    const responseData = response?.data || response || {};
    const relatedItems = responseData.related_items || responseData.data || responseData || [];

    log.log('[RELATED] API returned:', relatedItems.length, 'items');
    log.log('[RELATED] Algorithm:', responseData.algorithm);

    if (Array.isArray(relatedItems) && relatedItems.length > 0) {
      if (typeof setSecureChildren === 'function' && typeof createDocumentElement === 'function') {
        setSecureChildren(relatedListEl, relatedItems.map(item =>
          createDocumentElement(item, 'search-detail.html')
        ));
      }
      if (typeof updateElement === 'function') updateElement('navRelatedInfo', `${relatedItems.length}件`);
      log.log('[RELATED] Successfully displayed', relatedItems.length, 'related items');
    } else {
      if (typeof setSecureChildren === 'function' && typeof createEmptyMessage === 'function') {
        setSecureChildren(relatedListEl, createEmptyMessage('関連ナレッジが見つかりませんでした'));
      }
      if (typeof updateElement === 'function') updateElement('navRelatedInfo', '0件');
      log.log('[RELATED] No related items found');
    }
  } catch (error) {
    log.error('[RELATED] Failed to load related knowledge:', error);
    if (typeof setSecureChildren === 'function' && typeof createErrorMessage === 'function') {
      setSecureChildren(relatedListEl, createErrorMessage('関連ナレッジの読み込みに失敗しました'));
    }
    if (typeof updateElement === 'function') updateElement('navRelatedInfo', 'エラー');
  }
}

// ============================================================
// コメント管理
// ============================================================

/**
 * コメントを localStorage データから読み込む
 * @param {Object} data - ナレッジデータ
 */
function loadKnowledgeCommentsFromData(data) {
  const commentListEl = document.getElementById('commentList');
  const commentCountEl = document.getElementById('commentCount');
  if (!commentListEl) return;

  const comments = data.comments || [];
  if (commentCountEl) commentCountEl.textContent = comments.length;

  if (typeof setSecureChildren === 'function' && typeof createCommentElement === 'function') {
    if (comments.length > 0) {
      setSecureChildren(commentListEl, comments.map(comment => createCommentElement(comment)));
    } else if (typeof createEmptyMessage === 'function') {
      setSecureChildren(commentListEl, createEmptyMessage('コメントがありません'));
    }
  }
}

/**
 * コメントを API から読み込む
 * @param {string|number} knowledgeId - ナレッジ ID
 */
async function loadKnowledgeComments(knowledgeId) {
  const log = window.logger || console;
  const commentListEl = document.getElementById('commentList');
  const commentCountEl = document.getElementById('commentCount');
  if (!commentListEl) return;

  try {
    const comments = await apiCall(`/knowledge/${knowledgeId}/comments`);
    if (commentCountEl) commentCountEl.textContent = comments ? comments.length : 0;

    if (typeof setSecureChildren === 'function' && typeof createCommentElement === 'function') {
      if (comments && comments.length > 0) {
        setSecureChildren(commentListEl, comments.map(comment => createCommentElement(comment)));
      } else if (typeof createEmptyMessage === 'function') {
        setSecureChildren(commentListEl, createEmptyMessage('コメントがありません'));
      }
    }
  } catch (error) {
    log.error('Failed to load comments:', error);
    if (typeof setSecureChildren === 'function' && typeof createErrorMessage === 'function') {
      setSecureChildren(commentListEl, createErrorMessage('コメントの読み込みに失敗しました'));
    }
  }
}

/**
 * コメントを投稿する
 */
async function submitComment() {
  const log = window.logger || console;
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');
  const commentEl = document.getElementById('newComment');

  if (!commentEl || !commentEl.value.trim()) {
    if (typeof showToast === 'function') showToast('コメントを入力してください', 'warning');
    return;
  }

  try {
    const commentsKey = `knowledge_comments_${id}`;
    const existingComments = JSON.parse(localStorage.getItem(commentsKey) || '[]');

    const newComment = {
      id: Date.now(),
      content: commentEl.value.trim(),
      created_by: localStorage.getItem('user_name') || '現場作業員A',
      created_at: new Date().toISOString(),
      user_role: localStorage.getItem('user_role') || '作業員'
    };

    existingComments.push(newComment);
    localStorage.setItem(commentsKey, JSON.stringify(existingComments));

    try {
      await apiCall(`/knowledge/${id}/comments`, {
        method: 'POST',
        body: JSON.stringify({ content: commentEl.value })
      });
    } catch (apiError) {
      log.log('[COMMENT] API call failed, using localStorage only');
    }

    commentEl.value = '';
    await loadKnowledgeComments(id);
    if (typeof showToast === 'function') showToast('コメントを投稿しました', 'success');
  } catch (error) {
    if (typeof showToast === 'function') showToast(`コメントの投稿に失敗しました: ${error.message}`, 'error');
  }
}

// ============================================================
// 編集履歴管理
// ============================================================

/**
 * 編集履歴を localStorage データから読み込む
 * @param {Object} data - ナレッジデータ
 */
function loadKnowledgeHistoryFromData(data) {
  const historyTableEl = document.getElementById('historyTable');
  if (!historyTableEl) return;

  const history = data.edit_history || [];

  if (typeof setSecureChildren === 'function' && typeof createTableRowWithHTML === 'function') {
    if (history.length > 0) {
      setSecureChildren(historyTableEl, history.map((item, index) => {
        const btn = document.createElement('button');
        btn.className = 'cta ghost';
        btn.textContent = '表示';
        btn.addEventListener('click', () => alert('バージョン表示機能は準備中です'));
        return createTableRowWithHTML([
          `v${item.version || (history.length - index)}`,
          formatDate(item.edited_at || item.updated_at),
          item.edited_by || item.updated_by_name || 'N/A',
          item.changes || item.change_summary || '更新',
          btn
        ]);
      }));
    } else if (typeof createEmptyMessage === 'function') {
      setSecureChildren(historyTableEl, createEmptyMessage('履歴がありません', 5));
    }
  }
}

/**
 * 編集履歴を API から読み込む
 * @param {string|number} knowledgeId - ナレッジ ID
 */
async function loadKnowledgeHistory(knowledgeId) {
  const log = window.logger || console;
  const historyTableEl = document.getElementById('historyTable');
  if (!historyTableEl) return;

  try {
    const history = await apiCall(`/knowledge/${knowledgeId}/history`);
    if (typeof setSecureChildren === 'function' && typeof createTableRowWithHTML === 'function') {
      if (history && history.length > 0) {
        setSecureChildren(historyTableEl, history.map((item, index) => {
          const btn = document.createElement('button');
          btn.className = 'cta ghost';
          btn.textContent = '表示';
          btn.addEventListener('click', () => typeof viewVersion === 'function' && viewVersion(item.id));
          return createTableRowWithHTML([
            `v${item.version || (history.length - index)}`,
            formatDate(item.updated_at),
            item.updated_by_name || 'N/A',
            item.change_summary || '更新',
            btn
          ]);
        }));
      } else if (typeof createEmptyMessage === 'function') {
        setSecureChildren(historyTableEl, createEmptyMessage('履歴がありません', 5));
      }
    }
  } catch (error) {
    log.error('Failed to load history:', error);
    if (typeof setSecureChildren === 'function' && typeof createErrorMessage === 'function') {
      setSecureChildren(historyTableEl, createErrorMessage('履歴の読み込みに失敗しました', 5));
    }
  }
}

// ============================================================
// いいね・ブックマーク
// ============================================================

/**
 * いいねをトグル（ナレッジ詳細ページ用）
 */
async function toggleLike() {
  const log = window.logger || console;
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  if (!id) {
    if (typeof showToast === 'function') showToast('IDが取得できません', 'error');
    return;
  }

  const likeKey = `knowledge_like_${id}`;
  const likeCountKey = `knowledge_like_count_${id}`;
  const currentState = localStorage.getItem(likeKey) === 'true';
  const newState = !currentState;

  try {
    localStorage.setItem(likeKey, newState.toString());

    let currentCount = parseInt(localStorage.getItem(likeCountKey) || '0');
    currentCount = newState ? currentCount + 1 : Math.max(0, currentCount - 1);
    localStorage.setItem(likeCountKey, currentCount.toString());

    const icon = document.getElementById('likeIcon');
    const countEl = document.getElementById('likeCount');
    const totalLikesEl = document.getElementById('totalLikes');

    if (icon) icon.textContent = newState ? '♥' : '♡';
    if (countEl) countEl.textContent = currentCount;
    if (totalLikesEl) totalLikesEl.textContent = currentCount;

    try {
      const result = await apiCall(`/knowledge/${id}/like`, { method: 'POST' });
      if (result && result.likes_count !== undefined) {
        localStorage.setItem(likeCountKey, result.likes_count.toString());
        if (countEl) countEl.textContent = result.likes_count;
        if (totalLikesEl) totalLikesEl.textContent = result.likes_count;
      }
    } catch (apiError) {
      log.log('[LIKE] API call failed, using localStorage only');
    }

    if (typeof showToast === 'function') {
      showToast(newState ? 'いいねしました' : 'いいねを解除しました', 'success');
    }
  } catch (error) {
    if (typeof showToast === 'function') {
      showToast(`いいねの切り替えに失敗しました: ${error.message}`, 'error');
    }
  }
}

/**
 * ブックマークをトグル（ナレッジ詳細ページ用）
 */
async function toggleBookmark() {
  const log = window.logger || console;
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  if (!id) {
    if (typeof showToast === 'function') showToast('IDが取得できません', 'error');
    return;
  }

  const bookmarkKey = `knowledge_bookmark_${id}`;
  const currentState = localStorage.getItem(bookmarkKey) === 'true';
  const newState = !currentState;

  try {
    localStorage.setItem(bookmarkKey, newState.toString());

    const icon = document.getElementById('bookmarkIcon');
    if (icon) icon.textContent = newState ? '★' : '☆';

    try {
      await apiCall(`/knowledge/${id}/bookmark`, { method: 'POST' });
    } catch (apiError) {
      log.log('[BOOKMARK] API call failed, using localStorage only');
    }

    if (typeof showToast === 'function') {
      showToast(newState ? 'ブックマークに追加しました' : 'ブックマークを解除しました', 'success');
    }
  } catch (error) {
    if (typeof showToast === 'function') {
      showToast(`ブックマークの切り替えに失敗しました: ${error.message}`, 'error');
    }
  }
}

/**
 * 閲覧数をインクリメント
 * @param {string|number} id - ナレッジ ID
 */
async function incrementViewCount(id) {
  const log = window.logger || console;
  try {
    await apiCall(`/knowledge/${id}/view`, { method: 'POST' });
  } catch (error) {
    log.log('[VIEW COUNT] Skipped (using dummy data)');
  }
}

// ============================================================
// 共有・印刷・エクスポート
// ============================================================

/**
 * ナレッジ共有モーダルを開く
 */
function shareKnowledge() {
  if (typeof openShareModal === 'function') {
    openShareModal();
  } else {
    const modal = document.getElementById('shareModal');
    const shareUrlEl = document.getElementById('shareUrl');
    if (modal && shareUrlEl) {
      shareUrlEl.value = window.location.href;
      modal.classList.add('is-active');
    }
  }
}

// ============================================================
// 編集機能
// ============================================================

/**
 * ナレッジ編集モーダルを開く
 */
function editKnowledge() {
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  if (!id) {
    if (typeof showToast === 'function') showToast('IDが取得できません', 'error');
    return;
  }

  const knowledgeDataStr = localStorage.getItem('knowledge_details');
  if (!knowledgeDataStr) {
    if (typeof showToast === 'function') showToast('データが見つかりません', 'error');
    return;
  }

  const knowledgeData = JSON.parse(knowledgeDataStr);
  const currentData = knowledgeData.find(k => k.id === parseInt(id));

  if (!currentData) {
    if (typeof showToast === 'function') showToast('データが見つかりません', 'error');
    return;
  }

  document.getElementById('editTitle').value = currentData.title || '';
  document.getElementById('editCategory').value = currentData.category || '技術資料';
  document.getElementById('editSummary').value = currentData.summary || '';
  document.getElementById('editContent').value = currentData.content || '';
  document.getElementById('editTags').value = Array.isArray(currentData.tags) ? currentData.tags.join(', ') : '';
  document.getElementById('editProject').value = currentData.project || '';

  const modal = document.getElementById('editModal');
  if (modal) modal.classList.add('is-active');
}

/**
 * 編集モーダルを閉じる
 */
function closeEditModal() {
  const modal = document.getElementById('editModal');
  if (modal) modal.classList.remove('is-active');
}

/**
 * ナレッジ編集内容を保存する
 * @param {Event} event - フォーム送信イベント
 */
function saveKnowledgeEdit(event) {
  event.preventDefault();

  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  if (!id) {
    if (typeof showToast === 'function') showToast('IDが取得できません', 'error');
    return;
  }

  try {
    const updatedData = {
      title: document.getElementById('editTitle').value.trim(),
      category: document.getElementById('editCategory').value,
      summary: document.getElementById('editSummary').value.trim(),
      content: document.getElementById('editContent').value.trim(),
      tags: document.getElementById('editTags').value.split(',').map(t => t.trim()).filter(t => t),
      project: document.getElementById('editProject').value.trim(),
      updated_at: new Date().toISOString(),
      updated_by: localStorage.getItem('user_name') || '現場作業員A'
    };

    const knowledgeDataStr = localStorage.getItem('knowledge_details');
    if (knowledgeDataStr) {
      const knowledgeData = JSON.parse(knowledgeDataStr);
      const index = knowledgeData.findIndex(k => k.id === parseInt(id));

      if (index !== -1) {
        knowledgeData[index] = { ...knowledgeData[index], ...updatedData };
        localStorage.setItem('knowledge_details', JSON.stringify(knowledgeData));
      }
    }

    const historyKey = `knowledge_history_${id}`;
    const history = JSON.parse(localStorage.getItem(historyKey) || '[]');
    history.unshift({
      version: `v${history.length + 1}.0`,
      updated_at: updatedData.updated_at,
      updated_by: updatedData.updated_by,
      changes: '手動編集により更新'
    });
    localStorage.setItem(historyKey, JSON.stringify(history));

    closeEditModal();

    if (typeof showToast === 'function') showToast('ナレッジを更新しました', 'success');
    setTimeout(() => {
      window.location.reload();
    }, 1000);
  } catch (error) {
    if (typeof showToast === 'function') showToast(`保存に失敗しました: ${error.message}`, 'error');
  }
}

/**
 * 新規ナレッジ作成フォームを開く
 */
function createNewKnowledge() {
  document.getElementById('editTitle').value = '';
  document.getElementById('editCategory').value = '技術資料';
  document.getElementById('editSummary').value = '';
  document.getElementById('editContent').value = '';
  document.getElementById('editTags').value = '';
  document.getElementById('editProject').value = '';

  const modal = document.getElementById('editModal');
  if (modal) modal.classList.add('is-active');

  const form = document.getElementById('editForm');
  if (form) {
    form.onsubmit = function(event) {
      event.preventDefault();

      try {
        const newId = Date.now();

        const newData = {
          id: newId,
          title: document.getElementById('editTitle').value.trim(),
          category: document.getElementById('editCategory').value,
          summary: document.getElementById('editSummary').value.trim(),
          content: document.getElementById('editContent').value.trim(),
          tags: document.getElementById('editTags').value.split(',').map(t => t.trim()).filter(t => t),
          project: document.getElementById('editProject').value.trim(),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          created_by: localStorage.getItem('user_name') || '現場作業員A',
          created_by_name: localStorage.getItem('user_name') || '現場作業員A',
          status: 'draft'
        };

        const knowledgeDataStr = localStorage.getItem('knowledge_details');
        const knowledgeData = knowledgeDataStr ? JSON.parse(knowledgeDataStr) : [];
        knowledgeData.unshift(newData);
        localStorage.setItem('knowledge_details', JSON.stringify(knowledgeData));

        closeEditModal();

        if (typeof showToast === 'function') showToast('ナレッジを作成しました', 'success');
        setTimeout(() => {
          window.location.href = `search-detail.html?id=${newId}`;
        }, 1000);
      } catch (error) {
        if (typeof showToast === 'function') showToast(`作成に失敗しました: ${error.message}`, 'error');
      }

      form.onsubmit = saveKnowledgeEdit;
    };
  }
}

// ============================================================
// ページ初期化（search-detail.html 専用）
// ============================================================

/**
 * search-detail.html のページ初期化処理
 */
function initKnowledgeDetailPage() {
  loadKnowledgeDetail();

  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  if (id) {
    const bookmarkKey = `knowledge_bookmark_${id}`;
    const likeKey = `knowledge_like_${id}`;
    const likeCountKey = `knowledge_like_count_${id}`;

    const bookmarkIcon = document.getElementById('bookmarkIcon');
    if (bookmarkIcon) {
      const isBookmarked = localStorage.getItem(bookmarkKey) === 'true';
      bookmarkIcon.textContent = isBookmarked ? '★' : '☆';
    }

    const likeIcon = document.getElementById('likeIcon');
    const likeCount = document.getElementById('likeCount');
    const totalLikes = document.getElementById('totalLikes');

    if (likeIcon) {
      const isLiked = localStorage.getItem(likeKey) === 'true';
      likeIcon.textContent = isLiked ? '♥' : '♡';
    }

    const count = parseInt(localStorage.getItem(likeCountKey) || '0');
    if (likeCount) likeCount.textContent = count;
    if (totalLikes) totalLikes.textContent = count;
  }
}

// ============================================================
// グローバル公開
// ============================================================

window.loadKnowledgeDetail = loadKnowledgeDetail;
window.displayKnowledgeDetail = displayKnowledgeDetail;
window.updateBreadcrumbMeta = updateBreadcrumbMeta;
window.updateNavigationInfo = updateNavigationInfo;
window.loadRelatedKnowledge = loadRelatedKnowledge;
window.loadKnowledgeCommentsFromData = loadKnowledgeCommentsFromData;
window.loadKnowledgeComments = loadKnowledgeComments;
window.submitComment = submitComment;
window.loadKnowledgeHistoryFromData = loadKnowledgeHistoryFromData;
window.loadKnowledgeHistory = loadKnowledgeHistory;
window.toggleLike = window.toggleLike || toggleLike;
window.toggleBookmark = window.toggleBookmark || toggleBookmark;
window.incrementViewCount = window.incrementViewCount || incrementViewCount;
window.shareKnowledge = window.shareKnowledge || shareKnowledge;
window.editKnowledge = window.editKnowledge || editKnowledge;
window.closeEditModal = closeEditModal;
window.saveKnowledgeEdit = saveKnowledgeEdit;
window.createNewKnowledge = createNewKnowledge;
window.initKnowledgeDetailPage = initKnowledgeDetailPage;

export {
  loadKnowledgeDetail,
  displayKnowledgeDetail,
  updateBreadcrumbMeta,
  updateNavigationInfo,
  loadRelatedKnowledge,
  loadKnowledgeCommentsFromData,
  loadKnowledgeComments,
  submitComment,
  loadKnowledgeHistoryFromData,
  loadKnowledgeHistory,
  toggleLike,
  toggleBookmark,
  incrementViewCount,
  shareKnowledge,
  editKnowledge,
  closeEditModal,
  saveKnowledgeEdit,
  createNewKnowledge,
  initKnowledgeDetailPage
};
