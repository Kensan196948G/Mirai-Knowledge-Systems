// ============================================================
// 詳細ページ共通機能
// ============================================================

// API_BASEはapp.jsで定義されているため、ここでは定義しない
// const API_BASE = app.jsで定義済み

// ============================================================
// ユーティリティ関数
// ============================================================

function showLoading() {
  const loading = document.getElementById('loadingIndicator');
  if (loading) loading.style.display = 'flex';
}

function hideLoading() {
  const loading = document.getElementById('loadingIndicator');
  if (loading) loading.style.display = 'none';
}

function showError(message) {
  hideLoading();
  const errorEl = document.getElementById('errorMessage');
  const errorText = document.getElementById('errorText');
  if (errorEl && errorText) {
    errorText.textContent = message;
    errorEl.style.display = 'block';
  }
}

function hideError() {
  const errorEl = document.getElementById('errorMessage');
  if (errorEl) errorEl.style.display = 'none';
}

function formatDate(dateString) {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function formatDateShort(dateString) {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ============================================================
// API呼び出し関数
// ============================================================

async function apiCall(endpoint, options = {}) {
  const token = localStorage.getItem('access_token');
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers
    });

    if (response.status === 401) {
      console.error('Unauthorized. Redirecting to login...');
      window.location.href = '/login.html';
      return null;
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API call error:', error);
    throw error;
  }
}

// ============================================================
// search-detail.html 専用機能
// ============================================================

async function loadKnowledgeDetail() {
  console.log('[KNOWLEDGE DETAIL] Starting to load...');
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  console.log('[KNOWLEDGE DETAIL] ID from URL:', id);

  if (!id) {
    showError('ナレッジIDが指定されていません');
    return;
  }

  showLoading();
  hideError();

  try {
    let data = null;

    // まずlocalStorageから取得を試みる
    const knowledgeDataStr = localStorage.getItem('knowledge_details');
    console.log('[KNOWLEDGE DETAIL] localStorage data exists:', !!knowledgeDataStr);

    if (knowledgeDataStr) {
      const knowledgeData = JSON.parse(knowledgeDataStr);
      console.log('[KNOWLEDGE DETAIL] Total items in localStorage:', knowledgeData.length);
      data = knowledgeData.find(k => k.id === parseInt(id));
      console.log('[KNOWLEDGE DETAIL] Found in localStorage:', !!data);
    }

    // localStorageにない場合はAPIから取得
    if (!data) {
      console.log('[DETAIL] Loading from API...');
      data = await apiCall(`/knowledge/${id}`);
    } else {
      console.log('[DETAIL] Loading from localStorage...');
    }

    if (!data) {
      showError(`ナレッジID ${id} が見つかりません`);
      return;
    }

    console.log('[KNOWLEDGE DETAIL] Displaying data...');
    displayKnowledgeDetail(data);
    await loadRelatedKnowledge(data.tags || [], id);
    loadKnowledgeCommentsFromData(data);
    loadKnowledgeHistoryFromData(data);
    // incrementViewCount(id); // 一旦コメントアウト
  } catch (error) {
    console.error('[KNOWLEDGE DETAIL] Error:', error);
    showError(`データの読み込みに失敗しました: ${error.message}`);
  } finally {
    hideLoading();
  }
}

function displayKnowledgeDetail(data) {
  // タイトル
  const titleEl = document.getElementById('knowledgeTitle');
  if (titleEl) titleEl.textContent = data.title || 'タイトルなし';

  // メタ情報
  const metaEl = document.getElementById('knowledgeMeta');
  if (metaEl) {
    metaEl.innerHTML = `
      <span>カテゴリ: ${data.category || 'N/A'}</span>
      <span>最終更新: ${formatDate(data.updated_at)}</span>
      <span>作成者: ${data.created_by || data.created_by_name || 'N/A'}</span>
      <span>プロジェクト: ${data.project || 'N/A'}</span>
    `;
  }

  // タグ
  const tagsEl = document.getElementById('knowledgeTags');
  if (tagsEl && data.tags) {
    tagsEl.innerHTML = data.tags.map(tag =>
      `<span class="tag">${tag}</span>`
    ).join('');
  }

  // 概要
  const summaryEl = document.getElementById('knowledgeSummary');
  if (summaryEl) {
    summaryEl.innerHTML = `<p>${data.summary || '概要がありません'}</p>`;
  }

  // 本文
  const contentEl = document.getElementById('knowledgeContent');
  if (contentEl) {
    contentEl.innerHTML = `<div style="white-space: pre-wrap;">${data.content || '内容がありません'}</div>`;
  }

  // メタデータテーブル
  const metadataTable = document.getElementById('metadataTable');
  if (metadataTable) {
    metadataTable.innerHTML = `
      <tr><th>作成日</th><td>${formatDate(data.created_at)}</td></tr>
      <tr><th>最終更新</th><td>${formatDate(data.updated_at)}</td></tr>
      <tr><th>作成者</th><td>${data.created_by || data.created_by_name || 'N/A'}</td></tr>
      <tr><th>カテゴリ</th><td>${data.category || 'N/A'}</td></tr>
      <tr><th>プロジェクト</th><td>${data.project || 'N/A'}</td></tr>
      <tr><th>ステータス</th><td>${data.status || '公開'}</td></tr>
    `;
  }

  // 統計情報
  updateElement('totalLikes', data.likes || data.likes_count || 0);
  updateElement('totalBookmarks', data.bookmarks_count || 0);
  updateElement('totalViews', data.views || data.views_count || 0);
  updateElement('viewCount', `閲覧数 ${data.views || data.views_count || 0}`);

  // 承認フロー
  displayApprovalFlow(data.approval_status);

  // パンくずリスト更新
  updateBreadcrumb(data.category, data.title);
}

async function loadRelatedKnowledge(tags, currentId) {
  const relatedListEl = document.getElementById('relatedKnowledgeList');
  if (!relatedListEl) return;

  try {
    // まずlocalStorageから関連ナレッジを取得
    const knowledgeData = JSON.parse(localStorage.getItem('knowledge_details') || '[]');
    const currentKnowledge = knowledgeData.find(k => k.id === parseInt(currentId));

    let relatedItems = [];

    if (currentKnowledge && currentKnowledge.related_knowledge_ids) {
      // related_knowledge_idsを使用
      relatedItems = currentKnowledge.related_knowledge_ids
        .map(relatedId => knowledgeData.find(k => k.id === relatedId))
        .filter(item => item)
        .slice(0, 5);
    } else if (tags && tags.length > 0) {
      // タグベースで検索
      relatedItems = knowledgeData
        .filter(k => k.id !== parseInt(currentId))
        .filter(k => k.tags && k.tags.some(tag => tags.includes(tag)))
        .slice(0, 5);
    }

    if (relatedItems.length > 0) {
      relatedListEl.innerHTML = relatedItems.map(item => `
        <div class="document" style="cursor: pointer;" onclick="window.location.href='search-detail.html?id=${item.id}'">
          <strong><a href="search-detail.html?id=${item.id}">${item.title}</a></strong>
          <small>${formatDateShort(item.updated_at)}</small>
          <div>${item.summary || ''}</div>
        </div>
      `).join('');
    } else {
      relatedListEl.innerHTML = '<p>関連ナレッジが見つかりませんでした</p>';
    }
  } catch (error) {
    console.error('Failed to load related knowledge:', error);
    relatedListEl.innerHTML = '<p>関連ナレッジの読み込みに失敗しました</p>';
  }
}

/**
 * コメントをlocalStorageのデータから読み込む
 */
function loadKnowledgeCommentsFromData(data) {
  const commentListEl = document.getElementById('commentList');
  const commentCountEl = document.getElementById('commentCount');
  if (!commentListEl) return;

  const comments = data.comments || [];
  if (commentCountEl) commentCountEl.textContent = comments.length;

  if (comments.length > 0) {
    commentListEl.innerHTML = comments.map(comment => `
      <div class="comment-item" style="padding: 15px; border-bottom: 1px solid #eee;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
          <strong>${comment.user || comment.author_name || 'Unknown'}</strong>
          <small>${formatDate(comment.created_at)}</small>
        </div>
        <div>${comment.content}</div>
        ${comment.likes ? `<div style="margin-top: 8px; font-size: 12px; color: #888;">👍 ${comment.likes}</div>` : ''}
      </div>
    `).join('');
  } else {
    commentListEl.innerHTML = '<p>コメントがありません</p>';
  }
}

/**
 * 編集履歴をlocalStorageのデータから読み込む
 */
function loadKnowledgeHistoryFromData(data) {
  const historyTableEl = document.getElementById('historyTable');
  if (!historyTableEl) return;

  const history = data.edit_history || [];

  if (history.length > 0) {
    historyTableEl.innerHTML = history.map((item, index) => `
      <tr>
        <td>v${item.version || (history.length - index)}</td>
        <td>${formatDate(item.edited_at || item.updated_at)}</td>
        <td>${item.edited_by || item.updated_by_name || 'N/A'}</td>
        <td>${item.changes || item.change_summary || '更新'}</td>
        <td><button class="cta ghost" onclick="alert('バージョン表示機能は準備中です')">表示</button></td>
      </tr>
    `).join('');
  } else {
    historyTableEl.innerHTML = '<tr><td colspan="5">履歴がありません</td></tr>';
  }
}

async function loadKnowledgeComments(knowledgeId) {
  const commentListEl = document.getElementById('commentList');
  const commentCountEl = document.getElementById('commentCount');
  if (!commentListEl) return;

  try {
    const comments = await apiCall(`/knowledge/${knowledgeId}/comments`);
    if (commentCountEl) commentCountEl.textContent = comments.length;

    if (comments.length > 0) {
      commentListEl.innerHTML = comments.map(comment => `
        <div class="comment-item" style="padding: 15px; border-bottom: 1px solid #eee;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <strong>${comment.author_name || 'Unknown'}</strong>
            <small>${formatDate(comment.created_at)}</small>
          </div>
          <div>${comment.content}</div>
        </div>
      `).join('');
    } else {
      commentListEl.innerHTML = '<p>コメントがありません</p>';
    }
  } catch (error) {
    console.error('Failed to load comments:', error);
    commentListEl.innerHTML = '<p>コメントの読み込みに失敗しました</p>';
  }
}

async function loadKnowledgeHistory(knowledgeId) {
  const historyTableEl = document.getElementById('historyTable');
  if (!historyTableEl) return;

  try {
    const history = await apiCall(`/knowledge/${knowledgeId}/history`);
    if (history && history.length > 0) {
      historyTableEl.innerHTML = history.map((item, index) => `
        <tr>
          <td>v${item.version || (history.length - index)}</td>
          <td>${formatDate(item.updated_at)}</td>
          <td>${item.updated_by_name || 'N/A'}</td>
          <td>${item.change_summary || '更新'}</td>
          <td><button class="cta ghost" onclick="viewVersion(${item.id})">表示</button></td>
        </tr>
      `).join('');
    } else {
      historyTableEl.innerHTML = '<tr><td colspan="5">履歴がありません</td></tr>';
    }
  } catch (error) {
    console.error('Failed to load history:', error);
    historyTableEl.innerHTML = '<tr><td colspan="5">履歴の読み込みに失敗しました</td></tr>';
  }
}

async function submitComment() {
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');
  const commentEl = document.getElementById('newComment');

  if (!commentEl || !commentEl.value.trim()) {
    showToast('コメントを入力してください', 'warning');
    return;
  }

  try {
    // localStorageにコメントを保存
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

    // API呼び出しも試みる（エラーは無視）
    try {
      await apiCall(`/knowledge/${id}/comments`, {
        method: 'POST',
        body: JSON.stringify({ content: commentEl.value })
      });
    } catch (apiError) {
      console.log('[COMMENT] API call failed, using localStorage only');
    }

    commentEl.value = '';
    await loadKnowledgeComments(id);
    showToast('コメントを投稿しました', 'success');
  } catch (error) {
    showToast(`コメントの投稿に失敗しました: ${error.message}`, 'error');
  }
}

async function toggleBookmark() {
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  if (!id) {
    showToast('IDが取得できません', 'error');
    return;
  }

  const bookmarkKey = `knowledge_bookmark_${id}`;
  const currentState = localStorage.getItem(bookmarkKey) === 'true';
  const newState = !currentState;

  try {
    // localStorageに保存
    localStorage.setItem(bookmarkKey, newState.toString());

    // UIを更新
    const icon = document.getElementById('bookmarkIcon');
    if (icon) {
      icon.textContent = newState ? '★' : '☆';
    }

    // API呼び出しも試みる（エラーは無視）
    try {
      await apiCall(`/knowledge/${id}/bookmark`, { method: 'POST' });
    } catch (apiError) {
      console.log('[BOOKMARK] API call failed, using localStorage only');
    }

    showToast(newState ? 'ブックマークに追加しました' : 'ブックマークを解除しました', 'success');
  } catch (error) {
    showToast(`ブックマークの切り替えに失敗しました: ${error.message}`, 'error');
  }
}

async function toggleLike() {
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  if (!id) {
    showToast('IDが取得できません', 'error');
    return;
  }

  const likeKey = `knowledge_like_${id}`;
  const likeCountKey = `knowledge_like_count_${id}`;
  const currentState = localStorage.getItem(likeKey) === 'true';
  const newState = !currentState;

  try {
    // localStorageに保存
    localStorage.setItem(likeKey, newState.toString());

    // いいね数を更新
    let currentCount = parseInt(localStorage.getItem(likeCountKey) || '0');
    currentCount = newState ? currentCount + 1 : Math.max(0, currentCount - 1);
    localStorage.setItem(likeCountKey, currentCount.toString());

    // UIを更新
    const icon = document.getElementById('likeIcon');
    const countEl = document.getElementById('likeCount');
    const totalLikesEl = document.getElementById('totalLikes');

    if (icon) {
      icon.textContent = newState ? '♥' : '♡';
    }
    if (countEl) {
      countEl.textContent = currentCount;
    }
    if (totalLikesEl) {
      totalLikesEl.textContent = currentCount;
    }

    // API呼び出しも試みる（エラーは無視）
    try {
      const result = await apiCall(`/knowledge/${id}/like`, { method: 'POST' });
      if (result && result.likes_count !== undefined) {
        localStorage.setItem(likeCountKey, result.likes_count.toString());
        if (countEl) countEl.textContent = result.likes_count;
        if (totalLikesEl) totalLikesEl.textContent = result.likes_count;
      }
    } catch (apiError) {
      console.log('[LIKE] API call failed, using localStorage only');
    }

    showToast(newState ? 'いいねしました' : 'いいねを解除しました', 'success');
  } catch (error) {
    showToast(`いいねの切り替えに失敗しました: ${error.message}`, 'error');
  }
}

async function incrementViewCount(id) {
  try {
    await apiCall(`/knowledge/${id}/view`, { method: 'POST' });
  } catch (error) {
    // APIエラーは無視（ダミーデータ表示時は正常）
    console.log('[VIEW COUNT] Skipped (using dummy data)');
  }
}

function shareKnowledge() {
  const modal = document.getElementById('shareModal');
  const shareUrlEl = document.getElementById('shareUrl');
  if (modal && shareUrlEl) {
    shareUrlEl.value = window.location.href;
    modal.classList.add('is-active');
  }
}

function closeShareModal() {
  const modal = document.getElementById('shareModal');
  if (modal) modal.classList.remove('is-active');
}

function copyShareUrl() {
  const shareUrlEl = document.getElementById('shareUrl');
  if (shareUrlEl) {
    shareUrlEl.select();
    document.execCommand('copy');
    showToast('URLをコピーしました', 'success');
  }
}

function printPage() {
  window.print();
}

function exportPDF() {
  showToast('PDFを生成中...', 'info');
  setTimeout(() => {
    window.print();
  }, 500);
}

function retryLoad() {
  window.location.reload();
}

// ============================================================
// sop-detail.html 専用機能
// ============================================================

async function loadSOPDetail() {
  console.log('[SOP DETAIL] Starting to load...');
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  console.log('[SOP DETAIL] ID from URL:', id);

  if (!id) {
    showError('SOP IDが指定されていません');
    return;
  }

  showLoading();
  hideError();

  try {
    let data = null;

    // まずlocalStorageから取得を試みる
    const sopDataStr = localStorage.getItem('sop_details');
    console.log('[SOP DETAIL] localStorage data exists:', !!sopDataStr);

    if (sopDataStr) {
      const sopData = JSON.parse(sopDataStr);
      console.log('[SOP DETAIL] Total items in localStorage:', sopData.length);
      data = sopData.find(s => s.id === parseInt(id));
      console.log('[SOP DETAIL] Found in localStorage:', !!data);
    }

    // localStorageにない場合はAPIから取得
    if (!data) {
      console.log('[DETAIL] Loading SOP from API...');
      try {
        data = await apiCall(`/sop/${id}`);
      } catch (apiError) {
        console.warn('[DETAIL] API call failed:', apiError);
      }
    } else {
      console.log('[DETAIL] Loading SOP from localStorage...');
    }

    if (!data) {
      showError(`SOP ID ${id} が見つかりません`);
      return;
    }

    console.log('[SOP DETAIL] Displaying data...');
    displaySOPDetail(data);
    await loadRelatedSOP(data.category, id);

    // 実施統計を更新
    if (typeof updateExecutionStats === 'function') {
      updateExecutionStats();
    }
  } catch (error) {
    console.error('[SOP DETAIL] Error:', error);
    showError(`データの読み込みに失敗しました: ${error.message}`);
  } finally {
    hideLoading();
  }
}

function displaySOPDetail(data) {
  // タイトル
  updateElement('sopTitle', data.title || 'SOPタイトル');

  // ヘッダー情報
  const sopNumber = data.sop_number || data.title.match(/SOP-(\d+)/)?.[1] || 'N/A';
  updateElement('sopNumber', `SOP番号 ${sopNumber}`);
  updateElement('sopVersion', `バージョン ${data.version || 'v1.0'}`);

  // メタ情報
  const metaEl = document.getElementById('sopMeta');
  if (metaEl) {
    metaEl.innerHTML = `
      <span>改訂日: ${formatDateShort(data.revision_date || data.updated_at)}</span>
      <span>カテゴリ: ${data.category || 'N/A'}</span>
      <span>対象: ${data.target || data.scope || 'N/A'}</span>
    `;
  }

  // タグ
  const tagsEl = document.getElementById('sopTags');
  if (tagsEl && data.tags) {
    tagsEl.innerHTML = data.tags.map(tag =>
      `<span class="tag">${tag}</span>`
    ).join('');
  }

  // 目的
  updateElement('sopPurpose', data.purpose || '目的が記載されていません');

  // 適用範囲
  updateElement('sopScope', data.scope || '適用範囲が記載されていません');

  // バージョン情報
  const versionInfoEl = document.getElementById('versionInfo');
  if (versionInfoEl) {
    versionInfoEl.innerHTML = `
      <tr><th>バージョン</th><td>${data.version || 'v1.0'}</td></tr>
      <tr><th>改訂日</th><td>${formatDateShort(data.revision_date || data.updated_at)}</td></tr>
      <tr><th>次回改訂予定</th><td>${formatDateShort(data.next_revision_date) || 'N/A'}</td></tr>
    `;
  }

  // 手順（localStorageデータはsteps配列を持つ）
  const procedureEl = document.getElementById('sopProcedure');
  if (procedureEl) {
    const steps = data.steps || data.procedure || [];
    if (Array.isArray(steps) && steps.length > 0) {
      procedureEl.innerHTML = steps.map((step, i) => `
        <div class="step-item" style="padding: 15px; margin-bottom: 10px; border-left: 3px solid var(--accent); background: rgba(241, 236, 228, 0.3);">
          <strong>Step ${step.step_number || (i + 1)}: ${step.title || ''}</strong>
          <div style="margin-top: 8px;">${step.description || step}</div>
          ${step.responsible ? `<small style="color: var(--muted); margin-top: 5px; display: block;">担当: ${step.responsible} · 所要時間: ${step.estimated_time || 'N/A'}</small>` : ''}
        </div>
      `).join('');
    } else if (typeof steps === 'string') {
      procedureEl.innerHTML = `<div>${steps}</div>`;
    } else {
      procedureEl.innerHTML = '<p>手順データがありません</p>';
    }
  }

  // チェックリスト
  const checklistEl = document.getElementById('sopChecklist');
  if (checklistEl && data.checklist) {
    if (Array.isArray(data.checklist)) {
      checklistEl.innerHTML = data.checklist.map(item => {
        const itemText = typeof item === 'object' ? item.item : item;
        const isRequired = typeof item === 'object' ? item.required : false;
        return `<div style="padding: 8px;"><input type="checkbox"> ${itemText}${isRequired ? ' <span style="color: var(--danger);">*</span>' : ''}</div>`;
      }).join('');
    } else {
      checklistEl.innerHTML = `<div>${data.checklist}</div>`;
    }
  }

  // 注意事項（localStorageデータはprecautions配列を持つ）
  const warningsEl = document.getElementById('sopWarnings');
  if (warningsEl) {
    const warnings = data.precautions || data.warnings || [];
    if (Array.isArray(warnings) && warnings.length > 0) {
      warningsEl.innerHTML = warnings.map(warning =>
        `<div style="padding: 10px; margin-bottom: 8px; border-left: 3px solid var(--warning); background: rgba(255, 193, 7, 0.1);">⚠️ ${warning}</div>`
      ).join('');
    } else if (typeof warnings === 'string') {
      warningsEl.innerHTML = `<div>⚠️ ${warnings}</div>`;
    } else {
      warningsEl.innerHTML = '<p>注意事項がありません</p>';
    }
  }

  // 改訂履歴（localStorageデータはrevision_history配列を持つ）
  const revisionHistoryEl = document.getElementById('revisionHistory');
  if (revisionHistoryEl && data.revision_history) {
    if (Array.isArray(data.revision_history)) {
      revisionHistoryEl.innerHTML = data.revision_history.map(rev => `
        <tr>
          <td>${rev.version || 'N/A'}</td>
          <td>${rev.date || formatDateShort(rev.updated_at)}</td>
          <td>${rev.changes || 'N/A'}</td>
          <td>${rev.author || 'N/A'}</td>
          <td><button class="cta ghost" onclick="alert('バージョン表示機能は準備中です')">表示</button></td>
        </tr>
      `).join('');
    }
  }

  // 必要資材・工具
  const equipmentEl = document.getElementById('sopEquipment');
  if (equipmentEl && data.equipment) {
    if (Array.isArray(data.equipment)) {
      equipmentEl.innerHTML = data.equipment.map(item =>
        `<div class="pill">${item}</div>`
      ).join('');
    } else {
      equipmentEl.innerHTML = `<div class="pill">${data.equipment}</div>`;
    }
  }

  // 所要時間
  updateElement('prepTime', data.prep_time || '--');
  updateElement('workTime', data.work_time || '--');
  updateElement('totalTime', data.duration || '--');

  // 統計
  updateElement('executionCount', data.execution_count || 0);
  updateElement('complianceRate', data.compliance_rate || 0);

  // 承認フロー
  displayApprovalFlow(data.approval_status);

  // パンくずリスト更新
  updateBreadcrumb('SOP', data.title);
}

async function loadRelatedSOP(category, currentId) {
  const relatedListEl = document.getElementById('relatedSOPList');
  if (!relatedListEl) return;

  try {
    // まずlocalStorageから関連SOPを取得
    const sopData = JSON.parse(localStorage.getItem('sop_details') || '[]');
    const currentSOP = sopData.find(s => s.id === parseInt(currentId));

    let relatedItems = [];

    if (currentSOP && currentSOP.related_sops) {
      // related_sopsを使用
      relatedItems = currentSOP.related_sops
        .map(relatedId => sopData.find(s => s.id === relatedId))
        .filter(item => item)
        .slice(0, 5);
    } else if (category) {
      // カテゴリベースで検索
      relatedItems = sopData
        .filter(s => s.id !== parseInt(currentId))
        .filter(s => s.category === category)
        .slice(0, 5);
    }

    if (relatedItems.length > 0) {
      relatedListEl.innerHTML = relatedItems.map(item => `
        <div class="document" style="cursor: pointer;" onclick="window.location.href='sop-detail.html?id=${item.id}'">
          <strong><a href="sop-detail.html?id=${item.id}">${item.title}</a></strong>
          <small>${item.version || 'v1.0'}</small>
          <div>${item.purpose || ''}</div>
        </div>
      `).join('');
    } else {
      relatedListEl.innerHTML = '<p>関連SOPが見つかりませんでした</p>';
    }
  } catch (error) {
    console.error('Failed to load related SOP:', error);
    relatedListEl.innerHTML = '<p>関連SOPの読み込みに失敗しました</p>';
  }
}

function startInspectionRecord() {
  const formEl = document.getElementById('record-form');
  if (formEl) {
    formEl.style.display = 'block';

    // 現在の日時をセット
    const now = new Date();
    const dateInput = document.getElementById('recordDate');
    if (dateInput) {
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const day = String(now.getDate()).padStart(2, '0');
      const hours = String(now.getHours()).padStart(2, '0');
      const minutes = String(now.getMinutes()).padStart(2, '0');
      dateInput.value = `${year}-${month}-${day}T${hours}:${minutes}`;
    }

    // チェックリスト項目をフォームに追加
    const recordChecklistEl = document.getElementById('recordChecklist');
    const sopChecklistEl = document.getElementById('sopChecklist');
    if (recordChecklistEl && sopChecklistEl) {
      const checkboxes = sopChecklistEl.querySelectorAll('input[type="checkbox"]');
      let checklistHtml = '<div class="checklist">';
      checkboxes.forEach((checkbox, index) => {
        const label = checkbox.nextSibling ? checkbox.nextSibling.textContent : `項目 ${index + 1}`;
        checklistHtml += `
          <label class="checkbox-item">
            <input type="checkbox" name="recordCheck${index}" ${checkbox.checked ? 'checked' : ''}>
            ${label}
          </label>
        `;
      });
      checklistHtml += '</div>';
      recordChecklistEl.innerHTML = checklistHtml;
    }

    formEl.scrollIntoView({ behavior: 'smooth' });

    // フォーム送信イベントリスナー設定
    const formElement = document.getElementById('inspectionForm');
    if (formElement && !formElement.hasAttribute('data-listener-attached')) {
      formElement.addEventListener('submit', submitInspectionRecord);
      formElement.setAttribute('data-listener-attached', 'true');
    }
  }
}

function cancelRecord() {
  const formEl = document.getElementById('record-form');
  if (formEl) {
    formEl.style.display = 'none';

    // フォームをリセット
    const formElement = document.getElementById('inspectionForm');
    if (formElement) {
      formElement.reset();
    }
  }
}

function submitInspectionRecord(event) {
  event.preventDefault();

  const recordDate = document.getElementById('recordDate').value;
  const recordWorker = document.getElementById('recordWorker').value;
  const recordProject = document.getElementById('recordProject').value;
  const recordContent = document.getElementById('recordContent').value;
  const recordNotes = document.getElementById('recordNotes').value;

  // チェック項目を収集
  const checkItems = [];
  const checkboxes = document.querySelectorAll('#recordChecklist input[type="checkbox"]');
  checkboxes.forEach((checkbox, index) => {
    const label = checkbox.nextSibling ? checkbox.nextSibling.textContent.trim() : `項目 ${index + 1}`;
    checkItems.push({
      item: label,
      checked: checkbox.checked
    });
  });

  // SOPのIDを取得
  const urlParams = new URLSearchParams(window.location.search);
  const sopId = urlParams.get('id');

  // 記録データを作成
  const recordData = {
    id: Date.now(),
    sop_id: sopId,
    date: recordDate,
    worker: recordWorker,
    project: recordProject,
    content: recordContent,
    checklist: checkItems,
    notes: recordNotes,
    created_at: new Date().toISOString()
  };

  // localStorageに保存
  const recordsKey = 'sop_inspection_records';
  const existingRecords = JSON.parse(localStorage.getItem(recordsKey) || '[]');
  existingRecords.push(recordData);
  localStorage.setItem(recordsKey, JSON.stringify(existingRecords));

  // 成功メッセージ
  if (typeof showToast === 'function') {
    showToast('実施記録を保存しました', 'success');
  } else if (typeof showNotification === 'function') {
    showNotification('実施記録を保存しました', 'success');
  }

  // フォームをリセットして非表示
  cancelRecord();

  // 実施統計を更新
  updateExecutionStats();
}

function updateExecutionStats() {
  // 実施統計を再計算
  const urlParams = new URLSearchParams(window.location.search);
  const sopId = urlParams.get('id');
  const recordsKey = 'sop_inspection_records';
  const allRecords = JSON.parse(localStorage.getItem(recordsKey) || '[]');
  const sopRecords = allRecords.filter(r => r.sop_id === sopId);

  // 実施回数
  const executionCountEl = document.getElementById('executionCount');
  if (executionCountEl) {
    executionCountEl.textContent = sopRecords.length;
  }

  // 適合率（すべてのチェック項目がチェックされた記録の割合）
  const complianceRateEl = document.getElementById('complianceRate');
  if (complianceRateEl && sopRecords.length > 0) {
    const compliantRecords = sopRecords.filter(record => {
      if (!record.checklist || record.checklist.length === 0) return false;
      return record.checklist.every(item => item.checked);
    });
    const rate = Math.round((compliantRecords.length / sopRecords.length) * 100);
    complianceRateEl.textContent = rate;
  }
}

function downloadSOP() {
  // window.print()を使用してPDF保存
  if (typeof downloadPDF === 'function') {
    downloadPDF('sop', document.getElementById('sopTitle')?.textContent || 'SOP');
  } else {
    window.print();
  }

  if (typeof showToast === 'function') {
    showToast('印刷ダイアログを開きました。PDFとして保存できます。', 'info');
  }
}

function printChecklist() {
  const checklistEl = document.getElementById('sopChecklist');
  const titleEl = document.getElementById('sopTitle');

  if (checklistEl) {
    const printWindow = window.open('', '', 'height=600,width=800');
    const title = titleEl ? titleEl.textContent : 'チェックリスト';

    printWindow.document.write(`
      <html>
        <head>
          <title>${title} - チェックリスト</title>
          <style>
            body {
              font-family: 'Hiragino Kaku Gothic ProN', 'Meiryo', sans-serif;
              padding: 20px;
              line-height: 1.6;
            }
            h1 {
              font-size: 18px;
              margin-bottom: 20px;
              border-bottom: 2px solid #333;
              padding-bottom: 10px;
            }
            .checklist {
              display: flex;
              flex-direction: column;
              gap: 10px;
            }
            .checkbox-item {
              display: flex;
              align-items: center;
              padding: 8px;
              border: 1px solid #ddd;
            }
            input[type="checkbox"] {
              margin-right: 10px;
              width: 18px;
              height: 18px;
            }
            @media print {
              body { padding: 0; }
            }
          </style>
        </head>
        <body>
          <h1>${title} - チェックリスト</h1>
          ${checklistEl.outerHTML}
          <script>
            window.onload = function() {
              window.print();
            };
          </script>
        </body>
      </html>
    `);
    printWindow.document.close();
  }
}

function editSOP() {
  const modal = document.getElementById('editSOPModal');
  if (!modal) return;

  // 既存データを取得してフォームに設定
  const title = document.getElementById('sopTitle')?.textContent || '';
  const purpose = document.getElementById('sopPurpose')?.textContent || '';
  const scope = document.getElementById('sopScope')?.textContent || '';

  document.getElementById('editSOPTitle').value = title;
  document.getElementById('editSOPPurpose').value = purpose;
  document.getElementById('editSOPScope').value = scope;
  document.getElementById('editSOPChanges').value = '';
  document.getElementById('editSOPReason').value = '';

  // モーダルを表示
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closeEditSOPModal() {
  const modal = document.getElementById('editSOPModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

function submitEditSOP(event) {
  event.preventDefault();

  const urlParams = new URLSearchParams(window.location.search);
  const sopId = urlParams.get('id');

  const proposalData = {
    id: Date.now(),
    sop_id: sopId,
    title: document.getElementById('editSOPTitle').value,
    purpose: document.getElementById('editSOPPurpose').value,
    scope: document.getElementById('editSOPScope').value,
    changes: document.getElementById('editSOPChanges').value,
    reason: document.getElementById('editSOPReason').value,
    proposer: localStorage.getItem('user_name') || '不明',
    status: '提案中',
    created_at: new Date().toISOString()
  };

  // localStorageに保存
  const proposalsKey = 'sop_revision_proposals';
  const existingProposals = JSON.parse(localStorage.getItem(proposalsKey) || '[]');
  existingProposals.push(proposalData);
  localStorage.setItem(proposalsKey, JSON.stringify(existingProposals));

  // 成功メッセージ
  if (typeof showToast === 'function') {
    showToast('改訂提案を送信しました', 'success');
  } else if (typeof showNotification === 'function') {
    showNotification('改訂提案を送信しました', 'success');
  }

  closeEditSOPModal();
}

function retryLoadSOP() {
  window.location.reload();
}

// ============================================================
// incident-detail.html 専用機能
// ============================================================

async function loadIncidentDetail() {
  console.log('[INCIDENT DETAIL] Starting to load...');
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  console.log('[INCIDENT DETAIL] ID from URL:', id);

  if (!id) {
    showError('事故レポートIDが指定されていません');
    return;
  }

  showLoading();
  hideError();

  try {
    let data = null;

    // まずlocalStorageから取得を試みる
    const incidentDataStr = localStorage.getItem('incidents_details');
    console.log('[INCIDENT DETAIL] localStorage data exists:', !!incidentDataStr);

    if (incidentDataStr) {
      const incidentData = JSON.parse(incidentDataStr);
      console.log('[INCIDENT DETAIL] Total items in localStorage:', incidentData.length);
      data = incidentData.find(i => i.id === parseInt(id));
      console.log('[INCIDENT DETAIL] Found in localStorage:', !!data);
    }

    // localStorageにない場合はAPIから取得
    if (!data) {
      console.log('[DETAIL] Loading incident from API...');
      try {
        data = await apiCall(`/incident/${id}`);
      } catch (apiError) {
        console.warn('[DETAIL] API call failed:', apiError);
      }
    } else {
      console.log('[DETAIL] Loading incident from localStorage...');
    }

    if (!data) {
      showError(`事故レポートID ${id} が見つかりません`);
      return;
    }

    console.log('[INCIDENT DETAIL] Displaying data...');
    displayIncidentDetail(data);
    loadCorrectiveActionsFromData(data);
  } catch (error) {
    console.error('[INCIDENT DETAIL] Error:', error);
    showError(`データの読み込みに失敗しました: ${error.message}`);
  } finally {
    hideLoading();
  }
}

function displayIncidentDetail(data) {
  // タイトル
  updateElement('incidentTitle', data.title || '事故レポートタイトル');

  // ヘッダー情報
  const incidentNumber = data.incident_number || `INC-${data.id}`;
  updateElement('incidentNumber', `報告No. ${incidentNumber}`);
  updateElement('incidentSeverity', `重大度 ${data.severity || 'N/A'}`);

  // メタ情報
  const metaEl = document.getElementById('incidentMeta');
  if (metaEl) {
    metaEl.innerHTML = `
      <span>発生日: ${formatDate(data.occurred_at || data.incident_date)}</span>
      <span>場所: ${data.location || 'N/A'}</span>
      <span>報告者: ${data.reporter || data.reporter_name || 'N/A'}</span>
      <span>種類: ${data.type || 'N/A'}</span>
    `;
  }

  // タグ
  const tagsEl = document.getElementById('incidentTags');
  if (tagsEl && data.tags) {
    tagsEl.innerHTML = data.tags.map(tag =>
      `<span class="tag">${tag}</span>`
    ).join('');
  }

  // 概要
  updateElement('incidentSummary', data.description || data.summary || '概要がありません');

  // 発生情報
  const incidentInfoEl = document.getElementById('incidentInfo');
  if (incidentInfoEl) {
    incidentInfoEl.innerHTML = `
      <tr><th>発生日時</th><td>${formatDate(data.occurred_at || data.incident_date)}</td></tr>
      <tr><th>発生場所</th><td>${data.location || 'N/A'}</td></tr>
      <tr><th>種類</th><td>${data.type || 'N/A'}</td></tr>
      <tr><th>重大度</th><td>${data.severity || 'N/A'}</td></tr>
      <tr><th>ステータス</th><td>${data.status || 'N/A'}</td></tr>
    `;
  }

  // タイムライン（localStorageデータはtimeline配列を持つ）
  const timelineEl = document.getElementById('incidentTimeline');
  if (timelineEl && data.timeline) {
    if (Array.isArray(data.timeline)) {
      timelineEl.innerHTML = data.timeline.map(event => `
        <div class="timeline-item" style="padding: 15px; margin-bottom: 10px; border-left: 3px solid var(--steel); background: rgba(47, 75, 82, 0.05);">
          <strong>${formatDate(event.time)}</strong>
          <div style="margin-top: 5px; font-weight: 600;">${event.event || ''}</div>
          <small style="color: var(--muted);">${event.details || ''}</small>
        </div>
      `).join('');
    } else {
      timelineEl.innerHTML = `<div>${data.timeline}</div>`;
    }
  }

  // 原因分析（localStorageデータはroot_causes配列を持つ）
  if (data.root_causes && Array.isArray(data.root_causes)) {
    const causeAnalysisEl = document.getElementById('causeAnalysis');
    if (causeAnalysisEl) {
      const causesByCategory = {
        man: [],
        machine: [],
        media: [],
        management: []
      };

      // ランダムに4Mに振り分け（簡易実装）
      data.root_causes.forEach((cause, i) => {
        const categories = ['man', 'machine', 'media', 'management'];
        const category = categories[i % categories.length];
        causesByCategory[category].push(cause);
      });

      updateElement('causeMan', causesByCategory.man.length > 0 ? causesByCategory.man.join('<br>') : '分析なし');
      updateElement('causeMachine', causesByCategory.machine.length > 0 ? causesByCategory.machine.join('<br>') : '分析なし');
      updateElement('causeMedia', causesByCategory.media.length > 0 ? causesByCategory.media.join('<br>') : '分析なし');
      updateElement('causeManagement', causesByCategory.management.length > 0 ? causesByCategory.management.join('<br>') : '分析なし');
    }
  }

  // KPI
  updateElement('completionRate', data.completion_rate || 0);
  updateElement('deadlineRate', data.deadline_rate || 0);
  updateElement('remainingTasks', data.remaining_tasks || 0);

  // 承認フロー
  displayApprovalFlow(data.approval_status);

  // パンくずリスト更新
  updateBreadcrumb('事故レポート', data.title);
}

/**
 * 是正措置をlocalStorageのデータから読み込む
 */
function loadCorrectiveActionsFromData(data) {
  const tableEl = document.getElementById('correctiveActionTable');
  if (!tableEl) return;

  const actions = data.corrective_actions || [];

  if (actions.length > 0) {
    tableEl.innerHTML = actions.map(action => {
      const statusClass = action.status === 'completed' ? 'is-ok' : action.status === 'in_progress' ? 'is-warn' : 'is-hold';
      const statusText = action.status === 'completed' ? '完了' : action.status === 'in_progress' ? '進行中' : '未着手';
      return `
        <tr>
          <td><span class="status-dot ${statusClass}"></span> ${statusText}</td>
          <td>${action.action || action.content}</td>
          <td>${action.responsible || action.assignee_name || 'N/A'}</td>
          <td>${formatDateShort(action.deadline)}</td>
          <td>${action.progress || (action.status === 'completed' ? 100 : action.status === 'in_progress' ? 50 : 0)}%</td>
          <td>
            <button class="cta ghost" onclick="alert('是正措置更新機能は準備中です')">更新</button>
          </td>
        </tr>
      `;
    }).join('');

    // KPI更新
    const completedCount = actions.filter(a => a.status === 'completed').length;
    const completionRate = Math.round((completedCount / actions.length) * 100);
    const onTimeCount = actions.filter(a => a.status === 'completed' && new Date(a.deadline) >= new Date()).length;
    const deadlineRate = actions.length > 0 ? Math.round((onTimeCount / actions.length) * 100) : 0;
    const remainingTasks = actions.filter(a => a.status !== 'completed').length;

    updateElement('completionRate', completionRate);
    updateElement('deadlineRate', deadlineRate);
    updateElement('remainingTasks', remainingTasks);
  } else {
    tableEl.innerHTML = '<tr><td colspan="6">是正措置がありません</td></tr>';
  }
}

async function loadCorrectiveActions(incidentId) {
  const tableEl = document.getElementById('correctiveActionTable');
  if (!tableEl) return;

  try {
    const actions = await apiCall(`/incident/${incidentId}/corrective-actions`);
    if (actions && actions.length > 0) {
      tableEl.innerHTML = actions.map(action => {
        const statusClass = action.status === 'completed' ? 'is-ok' : 'is-warn';
        return `
          <tr>
            <td><span class="status-dot ${statusClass}"></span></td>
            <td>${action.content}</td>
            <td>${action.assignee_name || 'N/A'}</td>
            <td>${formatDateShort(action.deadline)}</td>
            <td>${action.progress || 0}%</td>
            <td>
              <button class="cta ghost" onclick="alert('是正措置更新機能は準備中です')">更新</button>
            </td>
          </tr>
        `;
      }).join('');
    } else {
      tableEl.innerHTML = '<tr><td colspan="6">是正措置がありません</td></tr>';
    }
  } catch (error) {
    console.error('Failed to load corrective actions:', error);
    tableEl.innerHTML = '<tr><td colspan="6">是正措置の読み込みに失敗しました</td></tr>';
  }
}

function addCorrectiveAction() {
  const modal = document.getElementById('correctiveActionModal');
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    // フォームリセット
    document.getElementById('correctiveActionForm').reset();
  }
}

function closeCorrectiveActionModal() {
  const modal = document.getElementById('correctiveActionModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

function submitCorrectiveAction(event) {
  event.preventDefault();

  const content = document.getElementById('actionContent').value;
  const assignee = document.getElementById('actionAssignee').value;
  const deadline = document.getElementById('actionDeadline').value;
  const priority = document.getElementById('actionPriority').value;

  // URLパラメータから現在のincident IDを取得
  const urlParams = new URLSearchParams(window.location.search);
  const incidentId = parseInt(urlParams.get('id'));

  // localStorageから事故データを取得
  const incidentsStr = localStorage.getItem('incidents_details');
  if (!incidentsStr) {
    showToast('データの読み込みに失敗しました', 'error');
    return;
  }

  const incidents = JSON.parse(incidentsStr);
  const incident = incidents.find(i => i.id === incidentId);

  if (!incident) {
    showToast('事故レポートが見つかりません', 'error');
    return;
  }

  // 新しい是正措置を追加
  if (!incident.corrective_actions) {
    incident.corrective_actions = [];
  }

  const newAction = {
    id: incident.corrective_actions.length + 1,
    action: content,
    content: content,
    responsible: assignee,
    assignee_name: assignee,
    deadline: deadline,
    priority: priority,
    status: 'pending',
    progress: 0,
    created_at: new Date().toISOString()
  };

  incident.corrective_actions.push(newAction);

  // localStorageに保存
  localStorage.setItem('incidents_details', JSON.stringify(incidents));

  // モーダルを閉じる
  closeCorrectiveActionModal();

  // ページをリロードして表示を更新
  showToast('是正措置を追加しました', 'success');
  setTimeout(() => {
    window.location.reload();
  }, 1000);
}

function downloadPDF(type) {
  showToast('PDFを生成中...', 'info');

  // 印刷ダイアログを開く（ブラウザの印刷→PDF保存機能を利用）
  setTimeout(() => {
    window.print();
  }, 500);
}

function shareIncident() {
  const modal = document.getElementById('shareModal');
  const shareUrlEl = document.getElementById('shareUrl');
  if (modal && shareUrlEl) {
    shareUrlEl.value = window.location.href;
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }
}

function closeShareModal() {
  const modal = document.getElementById('shareModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

function copyShareUrl() {
  const shareUrlEl = document.getElementById('shareUrl');
  if (shareUrlEl) {
    shareUrlEl.select();
    document.execCommand('copy');

    // Clipboard APIも試行
    if (navigator.clipboard) {
      navigator.clipboard.writeText(shareUrlEl.value).then(() => {
        showToast('URLをコピーしました', 'success');
      }).catch(() => {
        showToast('URLをコピーしました', 'success');
      });
    } else {
      showToast('URLをコピーしました', 'success');
    }
  }
}

function shareViaEmail() {
  const url = document.getElementById('shareUrl').value;
  const urlParams = new URLSearchParams(window.location.search);
  const incidentId = urlParams.get('id');
  const subject = encodeURIComponent(`事故レポート共有: INC-${incidentId}`);
  const body = encodeURIComponent(`事故レポートを共有します。\n\n${url}`);
  window.location.href = `mailto:?subject=${subject}&body=${body}`;
  showToast('メールアプリを起動しました', 'info');
}

function shareViaSlack() {
  const url = document.getElementById('shareUrl').value;
  showToast('Slack連携機能は準備中です\nURL: ' + url, 'info');
  // 実際の実装では Slack API や Webhook を使用
}

function shareViaTeams() {
  const url = document.getElementById('shareUrl').value;
  showToast('Teams連携機能は準備中です\nURL: ' + url, 'info');
  // 実際の実装では Microsoft Teams API を使用
}

function updateIncidentStatus() {
  const modal = document.getElementById('statusModal');
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    document.getElementById('newStatus').value = '';
    document.getElementById('statusComment').value = '';
  }
}

function closeStatusModal() {
  const modal = document.getElementById('statusModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

function submitStatusUpdate() {
  const newStatus = document.getElementById('newStatus').value;
  const comment = document.getElementById('statusComment').value;

  if (!newStatus) {
    showToast('ステータスを選択してください', 'warning');
    return;
  }

  // URLパラメータから現在のincident IDを取得
  const urlParams = new URLSearchParams(window.location.search);
  const incidentId = parseInt(urlParams.get('id'));

  // localStorageから事故データを取得
  const incidentsStr = localStorage.getItem('incidents_details');
  if (!incidentsStr) {
    showToast('データの読み込みに失敗しました', 'error');
    return;
  }

  const incidents = JSON.parse(incidentsStr);
  const incident = incidents.find(i => i.id === incidentId);

  if (!incident) {
    showToast('事故レポートが見つかりません', 'error');
    return;
  }

  // ステータスを更新
  incident.status = newStatus;
  incident.status_updated_at = new Date().toISOString();
  if (comment) {
    if (!incident.status_history) {
      incident.status_history = [];
    }
    incident.status_history.push({
      status: newStatus,
      comment: comment,
      updated_at: new Date().toISOString(),
      updated_by: localStorage.getItem('username') || 'Unknown'
    });
  }

  // localStorageに保存
  localStorage.setItem('incidents_details', JSON.stringify(incidents));

  // モーダルを閉じる
  closeStatusModal();

  // ページをリロードして表示を更新
  showToast(`ステータスを「${newStatus}」に更新しました`, 'success');
  setTimeout(() => {
    window.location.reload();
  }, 1000);
}

function openNewIncidentModal() {
  const modal = document.getElementById('newIncidentModal');
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    document.getElementById('newIncidentForm').reset();
    // デフォルトで現在日時を設定
    const now = new Date();
    const localDateTime = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    document.getElementById('newIncidentDate').value = localDateTime;
  }
}

function closeNewIncidentModal() {
  const modal = document.getElementById('newIncidentModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

function submitNewIncident(event) {
  event.preventDefault();

  const title = document.getElementById('newIncidentTitle').value;
  const date = document.getElementById('newIncidentDate').value;
  const location = document.getElementById('newIncidentLocation').value;
  const severity = document.getElementById('newIncidentSeverity').value;
  const content = document.getElementById('newIncidentContent').value;

  // localStorageから事故データを取得
  const incidentsStr = localStorage.getItem('incidents_details');
  const incidents = incidentsStr ? JSON.parse(incidentsStr) : [];

  // 新しいIDを生成
  const maxId = incidents.length > 0 ? Math.max(...incidents.map(i => i.id)) : 0;
  const newId = maxId + 1;

  // 新しい事故レポートを作成
  const newIncident = {
    id: newId,
    incident_number: `INC-${newId.toString().padStart(4, '0')}`,
    title: title,
    occurred_at: date,
    incident_date: date,
    location: location,
    severity: severity,
    description: content,
    summary: content,
    status: '調査中',
    reporter: localStorage.getItem('username') || 'Unknown',
    reporter_name: localStorage.getItem('username') || 'Unknown',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    type: '作業事故',
    tags: ['新規'],
    timeline: [
      {
        time: date,
        event: '事故発生',
        details: content
      },
      {
        time: new Date().toISOString(),
        event: 'レポート作成',
        details: 'システムに登録されました'
      }
    ],
    root_causes: [],
    corrective_actions: [],
    completion_rate: 0,
    deadline_rate: 0,
    remaining_tasks: 0
  };

  incidents.push(newIncident);

  // localStorageに保存
  localStorage.setItem('incidents_details', JSON.stringify(incidents));

  // モーダルを閉じる
  closeNewIncidentModal();

  // 新しいレポートのページに遷移
  showToast('新規事故レポートを作成しました', 'success');
  setTimeout(() => {
    window.location.href = `incident-detail.html?id=${newId}`;
  }, 1000);
}

function editIncident() {
  const modal = document.getElementById('editIncidentModal');
  if (!modal) return;

  // URLパラメータから現在のincident IDを取得
  const urlParams = new URLSearchParams(window.location.search);
  const incidentId = parseInt(urlParams.get('id'));

  // localStorageから事故データを取得
  const incidentsStr = localStorage.getItem('incidents_details');
  if (!incidentsStr) {
    showToast('データの読み込みに失敗しました', 'error');
    return;
  }

  const incidents = JSON.parse(incidentsStr);
  const incident = incidents.find(i => i.id === incidentId);

  if (!incident) {
    showToast('事故レポートが見つかりません', 'error');
    return;
  }

  // フォームに既存データを設定
  document.getElementById('editIncidentTitle').value = incident.title || '';

  // 日時をdatetime-local形式に変換
  const incidentDate = incident.occurred_at || incident.incident_date;
  if (incidentDate) {
    const date = new Date(incidentDate);
    const localDateTime = new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    document.getElementById('editIncidentDate').value = localDateTime;
  }

  document.getElementById('editIncidentLocation').value = incident.location || '';
  document.getElementById('editIncidentSeverity').value = incident.severity || '';
  document.getElementById('editIncidentContent').value = incident.description || incident.summary || '';

  // モーダルを表示
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closeEditIncidentModal() {
  const modal = document.getElementById('editIncidentModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

function submitEditIncident(event) {
  event.preventDefault();

  const title = document.getElementById('editIncidentTitle').value;
  const date = document.getElementById('editIncidentDate').value;
  const location = document.getElementById('editIncidentLocation').value;
  const severity = document.getElementById('editIncidentSeverity').value;
  const content = document.getElementById('editIncidentContent').value;

  // URLパラメータから現在のincident IDを取得
  const urlParams = new URLSearchParams(window.location.search);
  const incidentId = parseInt(urlParams.get('id'));

  // localStorageから事故データを取得
  const incidentsStr = localStorage.getItem('incidents_details');
  if (!incidentsStr) {
    showToast('データの読み込みに失敗しました', 'error');
    return;
  }

  const incidents = JSON.parse(incidentsStr);
  const incident = incidents.find(i => i.id === incidentId);

  if (!incident) {
    showToast('事故レポートが見つかりません', 'error');
    return;
  }

  // データを更新
  incident.title = title;
  incident.occurred_at = date;
  incident.incident_date = date;
  incident.location = location;
  incident.severity = severity;
  incident.description = content;
  incident.summary = content;
  incident.updated_at = new Date().toISOString();

  // localStorageに保存
  localStorage.setItem('incidents_details', JSON.stringify(incidents));

  // モーダルを閉じる
  closeEditIncidentModal();

  // ページをリロードして表示を更新
  showToast('事故レポートを更新しました', 'success');
  setTimeout(() => {
    window.location.reload();
  }, 1000);
}

function retryLoadIncident() {
  window.location.reload();
}

// ============================================================
// expert-consult.html 専用機能
// ============================================================

async function loadConsultDetail() {
  console.log('[CONSULT DETAIL] Starting to load...');
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  console.log('[CONSULT DETAIL] ID from URL:', id);

  if (!id) {
    showError('相談IDが指定されていません');
    return;
  }

  showLoading();
  hideError();

  try {
    let data = null;

    // まずlocalStorageから取得を試みる
    const consultDataStr = localStorage.getItem('consultations_details');
    console.log('[CONSULT DETAIL] localStorage data exists:', !!consultDataStr);

    if (consultDataStr) {
      const consultData = JSON.parse(consultDataStr);
      console.log('[CONSULT DETAIL] Total items in localStorage:', consultData.length);
      data = consultData.find(c => c.id === parseInt(id));
      console.log('[CONSULT DETAIL] Found in localStorage:', !!data);
    }

    // localStorageにない場合はAPIから取得
    if (!data) {
      console.log('[DETAIL] Loading consultation from API...');
      try {
        data = await apiCall(`/consultation/${id}`);
      } catch (apiError) {
        console.warn('[DETAIL] API call failed:', apiError);
      }
    } else {
      console.log('[DETAIL] Loading consultation from localStorage...');
    }

    if (!data) {
      showError(`相談ID ${id} が見つかりません`);
      return;
    }

    console.log('[CONSULT DETAIL] Displaying data...');
    displayConsultDetail(data);
    loadAnswersFromData(data);
    await loadRelatedQuestions(data.tags || [], id);
  } catch (error) {
    console.error('[CONSULT DETAIL] Error:', error);
    showError(`データの読み込みに失敗しました: ${error.message}`);
  } finally {
    hideLoading();
  }
}

function displayConsultDetail(data) {
  // タイトル
  updateElement('consultTitle', data.title || '相談タイトル');

  // ヘッダー情報
  const statusText = data.status === 'answered' ? '回答済み' : data.status === 'pending' ? '受付中' : data.status;
  updateElement('consultStatus', `ステータス ${statusText}`);

  // 回答時間計算
  const responseTime = data.answers && data.answers.length > 0
    ? calculateResponseTime(data.created_at, data.answers[0].created_at)
    : '--';
  updateElement('responseTime', `回答時間 ${responseTime}時間`);

  // メタ情報
  const metaEl = document.getElementById('consultMeta');
  if (metaEl) {
    metaEl.innerHTML = `
      <span>投稿日: ${formatDate(data.created_at)}</span>
      <span>投稿者: ${data.requester || data.author_name || 'N/A'}</span>
      <span>カテゴリ: ${data.category || 'N/A'}</span>
      <span>プロジェクト: ${data.project || 'N/A'}</span>
    `;
  }

  // タグ
  const tagsEl = document.getElementById('consultTags');
  if (tagsEl && data.tags) {
    tagsEl.innerHTML = data.tags.map(tag =>
      `<span class="tag">${tag}</span>`
    ).join('');
  }

  // 質問内容
  updateElement('questionContent', data.content || '質問内容がありません');

  // 相談情報
  const consultInfoEl = document.getElementById('consultInfo');
  if (consultInfoEl) {
    consultInfoEl.innerHTML = `
      <tr><th>投稿日</th><td>${formatDate(data.created_at)}</td></tr>
      <tr><th>投稿者</th><td>${data.requester || data.author_name || 'N/A'}</td></tr>
      <tr><th>カテゴリ</th><td>${data.category || 'N/A'}</td></tr>
      <tr><th>プロジェクト</th><td>${data.project || 'N/A'}</td></tr>
      <tr><th>ステータス</th><td>${statusText}</td></tr>
    `;
  }

  // 優先度・期限
  updateElement('priority', data.priority || '通常');
  updateElement('deadline', formatDateShort(data.deadline) || 'N/A');
  updateElement('elapsedTime', calculateElapsedTime(data.created_at));

  // 統計
  const answerCount = data.answers ? data.answers.length : data.answer_count || 0;
  updateElement('totalAnswers', answerCount);
  updateElement('answerCount', answerCount);
  updateElement('viewCount', data.views || data.view_count || 0);
  updateElement('followerCount', data.follower_count || 0);

  // 回答率・平均回答時間
  updateElement('responseRate', data.response_rate || 85);
  updateElement('avgResponseTime', data.avg_response_time || 4);

  // エキスパート情報
  displayExpertInfoConsult(data);

  // ベストアンサー
  displayBestAnswerConsult(data);

  // 参考SOP
  displayReferenceSOPConsult(data);

  // 添付ファイル
  displayConsultAttachments(data);

  // ステータス履歴
  displayConsultStatusHistory(data);

  // パンくずリスト更新
  updateBreadcrumb('専門家相談', data.title);
}

/**
 * エキスパート情報を表示
 */
function displayExpertInfoConsult(data) {
  const expertInfoEl = document.getElementById('expertInfo');
  if (!expertInfoEl) return;

  const expert = data.expert_info || {
    name: '佐藤 健太',
    title: '技術顧問',
    department: '技術部門',
    specialties: ['コンクリート工学', '品質管理', '構造設計'],
    response_count: 127,
    rating: 4.8
  };

  expertInfoEl.innerHTML = `
    <div style="display: grid; gap: 10px;">
      <div style="display: flex; align-items: center; gap: 10px;">
        <div style="width: 50px; height: 50px; border-radius: 50%; background: linear-gradient(135deg, var(--steel), var(--teal)); display: grid; place-items: center; color: white; font-weight: 700; font-size: 18px;">
          ${expert.name.substring(0, 1)}
        </div>
        <div>
          <strong style="font-size: 16px;">${expert.name}</strong>
          <div style="font-size: 12px; color: var(--muted);">${expert.title}</div>
          <div style="font-size: 11px; color: var(--muted);">${expert.department}</div>
        </div>
      </div>
      <div style="display: grid; gap: 6px; margin-top: 8px; padding-top: 10px; border-top: 1px dashed var(--line);">
        <div style="font-size: 12px;"><strong>専門分野:</strong></div>
        ${expert.specialties.map(s => `<span class="pill" style="font-size: 11px;">${s}</span>`).join(' ')}
      </div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px;">
        <div class="stat-card" style="padding: 8px;">
          <div style="font-size: 11px;">回答数</div>
          <strong style="font-size: 18px;">${expert.response_count}</strong>
        </div>
        <div class="stat-card" style="padding: 8px;">
          <div style="font-size: 11px;">評価</div>
          <strong style="font-size: 18px;">⭐${expert.rating}</strong>
        </div>
      </div>
    </div>
  `;
}

/**
 * ベストアンサーを表示
 */
function displayBestAnswerConsult(data) {
  const bestAnswerEl = document.getElementById('bestAnswer');
  if (!bestAnswerEl) return;

  const bestAnswer = data.answers?.find(a => a.is_best_answer);

  if (bestAnswer) {
    bestAnswerEl.innerHTML = `
      <div style="padding: 15px; border: 2px solid #ffa500; border-radius: 12px; background: #fffbf0;">
        <div style="color: #ffa500; font-weight: bold; margin-bottom: 8px;">✓ ベストアンサー</div>
        <div style="font-size: 13px; line-height: 1.6; margin-bottom: 10px;">${bestAnswer.content.substring(0, 200)}${bestAnswer.content.length > 200 ? '...' : ''}</div>
        <div style="font-size: 11px; color: var(--muted);">
          <strong>${bestAnswer.expert || bestAnswer.author_name || 'エキスパート'}</strong> · ${formatDate(bestAnswer.created_at)}
        </div>
      </div>
    `;
  } else {
    bestAnswerEl.innerHTML = '<p style="font-size: 13px; color: var(--muted);">まだベストアンサーが選択されていません</p>';
  }
}

/**
 * 参考SOPを表示
 */
function displayReferenceSOPConsult(data) {
  const referenceSOPEl = document.getElementById('referenceSOP');
  if (!referenceSOPEl) return;

  const referenceDocs = data.reference_sops || [
    { id: 1, title: 'コンクリート打設管理SOP', category: '品質管理' },
    { id: 2, title: '養生作業手順書', category: '施工手順' }
  ];

  if (referenceDocs.length > 0) {
    referenceSOPEl.innerHTML = referenceDocs.map(doc => `
      <div class="document" style="cursor: pointer;" onclick="window.location.href='sop-detail.html?id=${doc.id}'">
        <strong><a href="sop-detail.html?id=${doc.id}">${doc.title}</a></strong>
        <small>${doc.category}</small>
      </div>
    `).join('');
  } else {
    referenceSOPEl.innerHTML = '<p style="font-size: 13px; color: var(--muted);">参考SOPがありません</p>';
  }
}

/**
 * 添付ファイルを表示
 */
function displayConsultAttachments(data) {
  const attachmentListEl = document.getElementById('attachmentList');
  if (!attachmentListEl) return;

  const attachments = data.attachments || [];

  if (attachments.length > 0) {
    attachmentListEl.innerHTML = attachments.map(file => `
      <div class="attachment-item">
        <div style="font-size: 32px; margin-bottom: 8px;">📄</div>
        <div style="font-size: 12px; font-weight: 600;">${file.name}</div>
        <small style="color: var(--muted); font-size: 11px;">${file.size || '1.2MB'}</small>
      </div>
    `).join('');
  } else {
    attachmentListEl.innerHTML = '<p style="font-size: 13px; color: var(--muted);">添付ファイルがありません</p>';
  }
}

/**
 * ステータス履歴を表示
 */
function displayConsultStatusHistory(data) {
  const statusHistoryEl = document.getElementById('statusHistory');
  if (!statusHistoryEl) return;

  const history = data.status_history || [
    { status: '受付', timestamp: data.created_at, user: data.requester || 'ユーザー' },
    { status: '専門家割当', timestamp: data.created_at, user: 'システム' }
  ];

  if (history.length > 0) {
    statusHistoryEl.innerHTML = history.map(item => `
      <div class="timeline-item">
        <strong>${item.status}</strong>
        <div style="font-size: 12px; color: var(--muted); margin-top: 4px;">
          ${formatDate(item.timestamp)} · ${item.user}
        </div>
      </div>
    `).join('');
  } else {
    statusHistoryEl.innerHTML = '<p style="font-size: 13px; color: var(--muted);">履歴がありません</p>';
  }
}

/**
 * 回答時間を計算
 */
function calculateResponseTime(createdAt, firstAnswerAt) {
  if (!createdAt || !firstAnswerAt) return '--';
  const created = new Date(createdAt);
  const answered = new Date(firstAnswerAt);
  const diffMs = answered - created;
  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  return hours;
}

/**
 * 回答をlocalStorageのデータから読み込む
 */
function loadAnswersFromData(data) {
  const answerListEl = document.getElementById('answerList');
  const answerCountEl = document.getElementById('answerCount');
  if (!answerListEl) return;

  const answers = data.answers || [];
  if (answerCountEl) answerCountEl.textContent = answers.length;

  if (answers.length > 0) {
    answerListEl.innerHTML = answers.map(answer => `
      <div class="answer-item" style="padding: 20px; border: 1px solid ${answer.is_best_answer ? '#ffa500' : 'var(--line)'}; border-radius: 8px; margin-bottom: 15px; background: ${answer.is_best_answer ? '#fffbf0' : 'white'};">
        ${answer.is_best_answer ? '<div style="color: #ffa500; font-weight: bold; margin-bottom: 10px;">✓ ベストアンサー</div>' : ''}
        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
          <div>
            <strong>${answer.expert || answer.author_name || 'Unknown'}</strong>
            <small style="color: var(--muted); margin-left: 10px;">${answer.expert_title || ''}</small>
          </div>
          <small>${formatDate(answer.created_at)}</small>
        </div>
        <div style="margin-bottom: 10px; white-space: pre-wrap;">${answer.content}</div>
        ${answer.attachments && answer.attachments.length > 0 ? `
          <div style="padding: 10px; background: #f5f5f5; border-radius: 4px; margin-top: 10px;">
            <strong>添付ファイル:</strong>
            ${answer.attachments.map(att => `<div>📎 ${att.name}</div>`).join('')}
          </div>
        ` : ''}
        <div style="margin-top: 10px; font-size: 12px; color: var(--muted);">
          👍 役に立った: ${answer.helpful_count || 0}人
        </div>
      </div>
    `).join('');
  } else {
    answerListEl.innerHTML = '<p>まだ回答がありません</p>';
  }
}

async function loadAnswers(consultId) {
  const answerListEl = document.getElementById('answerList');
  const answerCountEl = document.getElementById('answerCount');
  if (!answerListEl) return;

  try {
    const answers = await apiCall(`/consultation/${consultId}/answers`);
    if (answerCountEl) answerCountEl.textContent = answers.length;

    if (answers.length > 0) {
      answerListEl.innerHTML = answers.map(answer => `
        <div class="answer-item" style="padding: 20px; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 15px; ${answer.is_best ? 'background: #fffbf0; border-color: #ffa500;' : ''}">
          ${answer.is_best ? '<div style="color: #ffa500; font-weight: bold; margin-bottom: 10px;">✓ ベストアンサー</div>' : ''}
          <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <strong>${answer.author_name || 'Unknown'}</strong>
            <small>${formatDate(answer.created_at)}</small>
          </div>
          <div style="margin-bottom: 10px;">${answer.content}</div>
          ${answer.references ? `<div style="padding: 10px; background: #f5f5f5; border-radius: 4px;"><strong>参照:</strong> ${answer.references}</div>` : ''}
        </div>
      `).join('');
    } else {
      answerListEl.innerHTML = '<p>まだ回答がありません</p>';
    }
  } catch (error) {
    console.error('Failed to load answers:', error);
    answerListEl.innerHTML = '<p>回答の読み込みに失敗しました</p>';
  }
}

async function loadRelatedQuestions(tags, currentId) {
  const relatedEl = document.getElementById('relatedQuestions');
  if (!relatedEl) return;

  try {
    // まずlocalStorageから関連質問を取得
    const consultData = JSON.parse(localStorage.getItem('consultations_details') || '[]');

    let relatedItems = [];

    if (tags && tags.length > 0) {
      // タグベースで検索
      relatedItems = consultData
        .filter(c => c.id !== parseInt(currentId))
        .filter(c => c.tags && c.tags.some(tag => tags.includes(tag)))
        .slice(0, 5);
    } else {
      // タグがない場合はカテゴリベース
      const current = consultData.find(c => c.id === parseInt(currentId));
      if (current) {
        relatedItems = consultData
          .filter(c => c.id !== parseInt(currentId))
          .filter(c => c.category === current.category)
          .slice(0, 5);
      }
    }

    if (relatedItems.length > 0) {
      relatedEl.innerHTML = relatedItems.map(item => `
        <div class="document" style="cursor: pointer;" onclick="window.location.href='expert-consult.html?id=${item.id}'">
          <strong><a href="expert-consult.html?id=${item.id}">${item.title}</a></strong>
          <small>${item.answers ? item.answers.length : 0}件の回答</small>
          <div>${item.content ? item.content.substring(0, 100) + '...' : ''}</div>
        </div>
      `).join('');
    } else {
      relatedEl.innerHTML = '<p>関連質問が見つかりませんでした</p>';
    }
  } catch (error) {
    console.error('Failed to load related questions:', error);
    relatedEl.innerHTML = '<p>関連質問の読み込みに失敗しました</p>';
  }
}

function calculateElapsedTime(createdAt) {
  if (!createdAt) return 'N/A';
  const now = new Date();
  const created = new Date(createdAt);
  const diff = now - created;
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const days = Math.floor(hours / 24);

  if (days > 0) return `${days}日`;
  return `${hours}時間`;
}

function retryLoadConsult() {
  window.location.reload();
}

// ============================================================
// 共通機能
// ============================================================

function updateElement(id, value) {
  const el = document.getElementById(id);
  if (el) {
    if (typeof value === 'object') {
      el.innerHTML = value;
    } else {
      el.textContent = value;
    }
  }
}

function displayApprovalFlow(approvalStatus) {
  const flowEl = document.getElementById('approvalFlow');
  if (!flowEl) return;

  const defaultFlow = [
    { step: '起案', status: 'done' },
    { step: '所長承認', status: 'wait' },
    { step: 'レビュー', status: 'hold' },
    { step: '承認・配信', status: 'info' }
  ];

  const flow = approvalStatus || defaultFlow;
  const statusMap = {
    'done': 'is-done',
    'wait': 'is-wait',
    'hold': 'is-hold',
    'info': 'is-info'
  };

  flowEl.innerHTML = (Array.isArray(flow) ? flow : defaultFlow).map(item => `
    <div class="flow-step">
      <div>${item.step}</div>
      <span class="badge ${statusMap[item.status] || 'is-hold'}">${item.status === 'done' ? '完了' : item.status === 'wait' ? '待機中' : '未着手'}</span>
    </div>
  `).join('');
}

function updateBreadcrumb(category, title) {
  const breadcrumbEl = document.getElementById('breadcrumbList');
  if (!breadcrumbEl) return;

  breadcrumbEl.innerHTML = `
    <li><a href="index.html">ホーム</a></li>
    <li><a href="index.html#${category}">${category}</a></li>
    <li aria-current="page">${title || '詳細'}</li>
  `;
}

// ============================================================
// PDF保存機能
// ============================================================

/**
 * PDFダウンロード機能
 * @param {string} pageType - 'incident', 'sop', 'knowledge', 'consult'
 */
function downloadPDF(pageType) {
  try {
    // PDFファイル名生成
    const now = new Date();
    const dateStr = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`;
    const filename = `${pageType}-report-${dateStr}.pdf`;

    // ブラウザの印刷機能を使用（最も簡単な方法）
    window.print();

    // 成功通知
    showNotification(`PDFの印刷ダイアログを開きました`, 'success');
  } catch (error) {
    console.error('PDF generation error:', error);
    showNotification('PDF保存に失敗しました', 'error');
  }
}

// ============================================================
// 共有機能
// ============================================================

/**
 * ナレッジ共有モーダルを開く
 */
function shareKnowledge() {
  openShareModal();
}

/**
 * SOP共有モーダルを開く
 */
function shareSOP() {
  openShareModal();
}

/**
 * 事故レポート共有モーダルを開く
 */
function shareIncident() {
  openShareModal();
}

/**
 * 専門家相談共有モーダルを開く
 */
function shareConsult() {
  openShareModal();
}

/**
 * 共有モーダルを開く（共通処理）
 */
function openShareModal() {
  const modal = document.getElementById('shareModal');
  const shareUrlEl = document.getElementById('shareUrl');

  if (modal && shareUrlEl) {
    // 現在のURLを共有URLとして設定
    shareUrlEl.value = window.location.href;
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  } else {
    // モーダルが存在しない場合は動的に作成
    createShareModal();
  }
}

/**
 * 共有モーダルを動的に作成
 */
function createShareModal() {
  const modal = document.createElement('div');
  modal.id = 'shareModal';
  modal.className = 'modal';
  modal.style.display = 'flex';

  modal.innerHTML = `
    <div class="modal-content">
      <div class="modal-header">
        <h2>共有</h2>
        <button class="modal-close" onclick="closeShareModal()">&times;</button>
      </div>
      <div class="modal-body">
        <div class="field">
          <label>共有URL</label>
          <div style="display: flex; gap: 10px;">
            <input type="text" id="shareUrl" readonly value="${window.location.href}" style="flex: 1;">
            <button class="cta secondary" onclick="copyShareUrl()">コピー</button>
          </div>
        </div>
        <div class="field">
          <label>共有方法</label>
          <div style="display: flex; gap: 10px; margin-top: 10px;">
            <button class="cta ghost" onclick="shareByEmail()">📧 メール</button>
            <button class="cta ghost" onclick="shareBySlack()">💬 Slack</button>
            <button class="cta ghost" onclick="shareByTeams()">👥 Teams</button>
          </div>
        </div>
      </div>
      <div class="modal-actions">
        <button class="cta ghost" onclick="closeShareModal()">閉じる</button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);
  document.body.style.overflow = 'hidden';

  // モーダル外クリックで閉じる
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      closeShareModal();
    }
  });
}

/**
 * 共有モーダルを閉じる
 */
function closeShareModal() {
  const modal = document.getElementById('shareModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

/**
 * 共有URLをクリップボードにコピー
 */
function copyShareUrl() {
  const shareUrlEl = document.getElementById('shareUrl');
  if (shareUrlEl) {
    shareUrlEl.select();
    shareUrlEl.setSelectionRange(0, 99999); // モバイル対応

    // クリップボードAPIを使用
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(shareUrlEl.value)
        .then(() => {
          showNotification('URLをクリップボードにコピーしました', 'success');
        })
        .catch(() => {
          // フォールバック: execCommand
          document.execCommand('copy');
          showNotification('URLをコピーしました', 'success');
        });
    } else {
      // 古いブラウザ対応
      document.execCommand('copy');
      showNotification('URLをコピーしました', 'success');
    }
  }
}

/**
 * メールで共有
 */
function shareByEmail() {
  const url = encodeURIComponent(window.location.href);
  const title = encodeURIComponent(document.title);
  const subject = `【Mirai Knowledge】${title}`;
  const body = `以下のページを共有します:%0D%0A%0D%0A${url}`;

  window.location.href = `mailto:?subject=${subject}&body=${body}`;
  showToast('メールアプリを開きます...', 'info');
}

/**
 * Slackで共有（ダミー処理）
 */
function shareBySlack() {
  showToast('Slack連携機能は準備中です', 'info');
  // TODO: 実際のSlack API連携を実装
}

/**
 * Microsoft Teamsで共有（ダミー処理）
 */
function shareByTeams() {
  showToast('Teams連携機能は準備中です', 'info');
  // TODO: 実際のTeams API連携を実装
}

// ============================================================
// 新規作成モーダル機能
// ============================================================

/**
 * 新規事故レポート作成モーダルを開く
 */
function openNewIncidentModal() {
  const modal = document.getElementById('newIncidentModal');
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  } else {
    createNewIncidentModal();
  }
}

/**
 * 新規事故レポート作成モーダルを作成
 */
function createNewIncidentModal() {
  const modal = document.createElement('div');
  modal.id = 'newIncidentModal';
  modal.className = 'modal';
  modal.style.display = 'flex';

  modal.innerHTML = `
    <div class="modal-content">
      <div class="modal-header">
        <h2>新規事故レポート作成</h2>
        <button class="modal-close" onclick="closeNewIncidentModal()">&times;</button>
      </div>
      <form id="newIncidentForm" onsubmit="submitNewIncident(event)">
        <div class="modal-body">
          <div class="field">
            <label>タイトル <span class="required">*</span></label>
            <input type="text" id="incidentNewTitle" required placeholder="例: 足場倒壊事故">
          </div>
          <div class="field">
            <label>発生日時 <span class="required">*</span></label>
            <input type="datetime-local" id="incidentNewDate" required>
          </div>
          <div class="field">
            <label>発生場所 <span class="required">*</span></label>
            <input type="text" id="incidentNewLocation" required placeholder="例: A工区 3階">
          </div>
          <div class="field">
            <label>重大度 <span class="required">*</span></label>
            <select id="incidentNewSeverity" required>
              <option value="">選択してください</option>
              <option value="低">低</option>
              <option value="中">中</option>
              <option value="高">高</option>
              <option value="重大">重大</option>
            </select>
          </div>
          <div class="field">
            <label>事故内容 <span class="required">*</span></label>
            <textarea id="incidentNewContent" required rows="6" placeholder="事故の詳細を記入してください..."></textarea>
          </div>
          <div class="field">
            <label>写真・資料</label>
            <input type="file" id="incidentNewPhotos" multiple accept="image/*,.pdf">
            <small>画像またはPDFファイル（最大10MB）</small>
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="cta ghost" onclick="closeNewIncidentModal()">キャンセル</button>
          <button type="submit" class="cta">作成</button>
        </div>
      </form>
    </div>
  `;

  document.body.appendChild(modal);
  document.body.style.overflow = 'hidden';

  // モーダル外クリックで閉じる
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      closeNewIncidentModal();
    }
  });

  // デフォルト値設定（現在日時）
  const dateInput = document.getElementById('incidentNewDate');
  if (dateInput) {
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    dateInput.value = now.toISOString().slice(0, 16);
  }
}

/**
 * 新規事故レポート作成モーダルを閉じる
 */
function closeNewIncidentModal() {
  const modal = document.getElementById('newIncidentModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
    // フォームリセット
    const form = document.getElementById('newIncidentForm');
    if (form) form.reset();
  }
}

/**
 * 新規事故レポートを送信
 */
async function submitNewIncident(event) {
  event.preventDefault();

  const title = document.getElementById('incidentNewTitle').value;
  const date = document.getElementById('incidentNewDate').value;
  const location = document.getElementById('incidentNewLocation').value;
  const severity = document.getElementById('incidentNewSeverity').value;
  const content = document.getElementById('incidentNewContent').value;

  const data = {
    title,
    occurred_at: date,
    location,
    severity,
    description: content,
    status: 'reported'
  };

  try {
    showNotification('事故レポートを作成中...', 'info');

    // APIに送信
    await apiCall('/incidents', {
      method: 'POST',
      body: JSON.stringify(data)
    });

    showNotification('事故レポートを作成しました', 'success');
    closeNewIncidentModal();

    // ページをリロード
    setTimeout(() => {
      window.location.reload();
    }, 1000);
  } catch (error) {
    console.error('Failed to create incident:', error);
    showNotification(`事故レポートの作成に失敗しました: ${error.message}`, 'error');
  }
}

/**
 * 新規専門家相談作成モーダルを開く
 */
function openNewConsultationModal() {
  const modal = document.getElementById('newConsultationModal');
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  } else {
    createNewConsultationModal();
  }
}

/**
 * 新規専門家相談モーダルを作成
 */
function createNewConsultationModal() {
  const modal = document.createElement('div');
  modal.id = 'newConsultationModal';
  modal.className = 'modal';
  modal.style.display = 'flex';

  modal.innerHTML = `
    <div class="modal-content">
      <div class="modal-header">
        <h2>新規専門家相談</h2>
        <button class="modal-close" onclick="closeNewConsultationModal()">&times;</button>
      </div>
      <form id="newConsultationForm" onsubmit="submitNewConsultation(event)">
        <div class="modal-body">
          <div class="field">
            <label>質問タイトル <span class="required">*</span></label>
            <input type="text" id="consultNewTitle" required placeholder="例: RC橋脚の配筋方法について">
          </div>
          <div class="field">
            <label>カテゴリ <span class="required">*</span></label>
            <select id="consultNewCategory" required>
              <option value="">選択してください</option>
              <option value="構造設計">構造設計</option>
              <option value="施工管理">施工管理</option>
              <option value="品質管理">品質管理</option>
              <option value="安全管理">安全管理</option>
              <option value="環境対策">環境対策</option>
              <option value="地盤技術">地盤技術</option>
            </select>
          </div>
          <div class="field">
            <label>優先度 <span class="required">*</span></label>
            <select id="consultNewPriority" required>
              <option value="通常">通常</option>
              <option value="高">高</option>
              <option value="緊急">緊急</option>
            </select>
          </div>
          <div class="field">
            <label>質問内容 <span class="required">*</span></label>
            <textarea id="consultNewContent" required rows="8" placeholder="具体的な質問内容を記入してください..."></textarea>
            <small>できるだけ詳しく記述すると適切な回答が得られます</small>
          </div>
          <div class="field">
            <label>添付ファイル</label>
            <input type="file" id="consultNewAttachment" multiple accept="image/*,.pdf,.xlsx,.dwg">
            <small>画像、PDF、Excel、CADファイル（最大10MB）</small>
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="cta ghost" onclick="closeNewConsultationModal()">キャンセル</button>
          <button type="submit" class="cta">相談を投稿</button>
        </div>
      </form>
    </div>
  `;

  document.body.appendChild(modal);
  document.body.style.overflow = 'hidden';

  // モーダル外クリックで閉じる
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      closeNewConsultationModal();
    }
  });
}

/**
 * 新規専門家相談モーダルを閉じる
 */
function closeNewConsultationModal() {
  const modal = document.getElementById('newConsultationModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
    // フォームリセット
    const form = document.getElementById('newConsultationForm');
    if (form) form.reset();
  }
}

/**
 * 新規専門家相談を送信
 */
async function submitNewConsultation(event) {
  if (event) {
    event.preventDefault();
  }

  // モーダルが存在する場合のみフォームデータを取得
  const titleEl = document.getElementById('consultNewTitle');
  const categoryEl = document.getElementById('consultNewCategory');
  const priorityEl = document.getElementById('consultNewPriority');
  const contentEl = document.getElementById('consultNewContent');

  if (!titleEl || !categoryEl || !priorityEl || !contentEl) {
    // モーダルが存在しない場合は作成して開く
    openNewConsultationModal();
    return;
  }

  const title = titleEl.value;
  const category = categoryEl.value;
  const priority = priorityEl.value;
  const content = contentEl.value;

  const data = {
    title,
    category,
    priority,
    content,
    status: 'pending'
  };

  try {
    showNotification('専門家相談を投稿中...', 'info');

    // APIに送信
    await apiCall('/consultations', {
      method: 'POST',
      body: JSON.stringify(data)
    });

    showNotification('専門家相談を投稿しました', 'success');
    closeNewConsultationModal();

    // ページをリロード
    setTimeout(() => {
      window.location.reload();
    }, 1000);
  } catch (error) {
    console.error('Failed to create consultation:', error);
    showNotification(`相談の投稿に失敗しました: ${error.message}`, 'error');
  }
}

// ============================================================
// 編集機能（search-detail.html用）
// ============================================================

/**
 * ナレッジ編集モーダルを開く
 */
function editKnowledge() {
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  if (!id) {
    showToast('IDが取得できません', 'error');
    return;
  }

  // 現在のデータを取得
  const knowledgeDataStr = localStorage.getItem('knowledge_details');
  if (!knowledgeDataStr) {
    showToast('データが見つかりません', 'error');
    return;
  }

  const knowledgeData = JSON.parse(knowledgeDataStr);
  const currentData = knowledgeData.find(k => k.id === parseInt(id));

  if (!currentData) {
    showToast('データが見つかりません', 'error');
    return;
  }

  // フォームにデータを設定
  document.getElementById('editTitle').value = currentData.title || '';
  document.getElementById('editCategory').value = currentData.category || '技術資料';
  document.getElementById('editSummary').value = currentData.summary || '';
  document.getElementById('editContent').value = currentData.content || '';
  document.getElementById('editTags').value = Array.isArray(currentData.tags) ? currentData.tags.join(', ') : '';
  document.getElementById('editProject').value = currentData.project || '';

  // モーダルを表示
  const modal = document.getElementById('editModal');
  if (modal) {
    modal.classList.add('is-active');
  }
}

/**
 * 編集モーダルを閉じる
 */
function closeEditModal() {
  const modal = document.getElementById('editModal');
  if (modal) {
    modal.classList.remove('is-active');
  }
}

/**
 * ナレッジ編集を保存
 */
function saveKnowledgeEdit(event) {
  event.preventDefault();

  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  if (!id) {
    showToast('IDが取得できません', 'error');
    return;
  }

  try {
    // フォームデータを取得
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

    // localStorageのデータを更新
    const knowledgeDataStr = localStorage.getItem('knowledge_details');
    if (knowledgeDataStr) {
      const knowledgeData = JSON.parse(knowledgeDataStr);
      const index = knowledgeData.findIndex(k => k.id === parseInt(id));

      if (index !== -1) {
        // 既存データとマージ
        knowledgeData[index] = {
          ...knowledgeData[index],
          ...updatedData
        };

        localStorage.setItem('knowledge_details', JSON.stringify(knowledgeData));
      }
    }

    // 編集履歴を追加
    const historyKey = `knowledge_history_${id}`;
    const history = JSON.parse(localStorage.getItem(historyKey) || '[]');
    history.unshift({
      version: `v${history.length + 1}.0`,
      updated_at: updatedData.updated_at,
      updated_by: updatedData.updated_by,
      changes: '手動編集により更新'
    });
    localStorage.setItem(historyKey, JSON.stringify(history));

    // モーダルを閉じる
    closeEditModal();

    // ページをリロード
    showToast('ナレッジを更新しました', 'success');
    setTimeout(() => {
      window.location.reload();
    }, 1000);
  } catch (error) {
    showToast(`保存に失敗しました: ${error.message}`, 'error');
  }
}

/**
 * 新規ナレッジ作成
 */
function createNewKnowledge() {
  // フォームをクリア
  document.getElementById('editTitle').value = '';
  document.getElementById('editCategory').value = '技術資料';
  document.getElementById('editSummary').value = '';
  document.getElementById('editContent').value = '';
  document.getElementById('editTags').value = '';
  document.getElementById('editProject').value = '';

  // モーダルを表示
  const modal = document.getElementById('editModal');
  if (modal) {
    modal.classList.add('is-active');
  }

  // フォーム送信時の処理を変更
  const form = document.getElementById('editForm');
  if (form) {
    form.onsubmit = function(event) {
      event.preventDefault();

      try {
        // 新しいIDを生成
        const newId = Date.now();

        // フォームデータを取得
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

        // localStorageに追加
        const knowledgeDataStr = localStorage.getItem('knowledge_details');
        const knowledgeData = knowledgeDataStr ? JSON.parse(knowledgeDataStr) : [];
        knowledgeData.unshift(newData);
        localStorage.setItem('knowledge_details', JSON.stringify(knowledgeData));

        // モーダルを閉じる
        closeEditModal();

        // 新しいページに移動
        showToast('ナレッジを作成しました', 'success');
        setTimeout(() => {
          window.location.href = `search-detail.html?id=${newId}`;
        }, 1000);
      } catch (error) {
        showToast(`作成に失敗しました: ${error.message}`, 'error');
      }

      // フォーム送信時の処理を元に戻す
      form.onsubmit = saveKnowledgeEdit;
    };
  }
}

// ============================================================
// ページロード時の初期化
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;

  if (path.includes('search-detail.html')) {
    loadKnowledgeDetail();

    // ブックマーク・いいねの初期状態を設定
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('id');

    if (id) {
      const bookmarkKey = `knowledge_bookmark_${id}`;
      const likeKey = `knowledge_like_${id}`;
      const likeCountKey = `knowledge_like_count_${id}`;

      // ブックマークアイコンの初期化
      const bookmarkIcon = document.getElementById('bookmarkIcon');
      if (bookmarkIcon) {
        const isBookmarked = localStorage.getItem(bookmarkKey) === 'true';
        bookmarkIcon.textContent = isBookmarked ? '★' : '☆';
      }

      // いいねアイコンの初期化
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
  } else if (path.includes('sop-detail.html')) {
    loadSOPDetail();
  } else if (path.includes('incident-detail.html')) {
    loadIncidentDetail();
  } else if (path.includes('expert-consult.html')) {
    loadConsultDetail();
  }

  // 最終同期時刻更新
  const syncTimeEl = document.getElementById('lastSyncTime');
  if (syncTimeEl) {
    const now = new Date();
    syncTimeEl.textContent = `最終同期 ${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`;
  }
});
