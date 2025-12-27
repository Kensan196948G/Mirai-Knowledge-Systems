// ============================================================
// 詳細ページ共通機能
// ============================================================

const API_BASE = `${window.location.protocol}//${window.location.hostname}:${window.location.port || '5000'}/api/v1`;

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
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  if (!id) {
    showError('ナレッジIDが指定されていません');
    return;
  }

  showLoading();
  hideError();

  try {
    let data = null;

    // まずlocalStorageから取得を試みる
    const knowledgeData = JSON.parse(localStorage.getItem('knowledge_details') || '[]');
    data = knowledgeData.find(k => k.id === parseInt(id));

    // localStorageにない場合はAPIから取得
    if (!data) {
      console.log('[DETAIL] Loading from API...');
      data = await apiCall(`/knowledge/${id}`);
    } else {
      console.log('[DETAIL] Loading from localStorage...');
    }

    displayKnowledgeDetail(data);
    await loadRelatedKnowledge(data.tags || [], id);
    loadKnowledgeCommentsFromData(data);
    loadKnowledgeHistoryFromData(data);
    incrementViewCount(id);
  } catch (error) {
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
    alert('コメントを入力してください');
    return;
  }

  try {
    await apiCall(`/knowledge/${id}/comments`, {
      method: 'POST',
      body: JSON.stringify({ content: commentEl.value })
    });

    commentEl.value = '';
    await loadKnowledgeComments(id);
    alert('コメントを投稿しました');
  } catch (error) {
    alert(`コメントの投稿に失敗しました: ${error.message}`);
  }
}

async function toggleBookmark() {
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  try {
    await apiCall(`/knowledge/${id}/bookmark`, { method: 'POST' });
    const icon = document.getElementById('bookmarkIcon');
    if (icon) {
      icon.textContent = icon.textContent === '☆' ? '★' : '☆';
    }
  } catch (error) {
    alert(`ブックマークの切り替えに失敗しました: ${error.message}`);
  }
}

async function toggleLike() {
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  try {
    const result = await apiCall(`/knowledge/${id}/like`, { method: 'POST' });
    const icon = document.getElementById('likeIcon');
    const count = document.getElementById('likeCount');
    if (icon) {
      icon.textContent = result.liked ? '♥' : '♡';
    }
    if (count) {
      count.textContent = result.likes_count || 0;
    }
  } catch (error) {
    alert(`いいねの切り替えに失敗しました: ${error.message}`);
  }
}

async function incrementViewCount(id) {
  try {
    await apiCall(`/knowledge/${id}/view`, { method: 'POST' });
  } catch (error) {
    console.error('Failed to increment view count:', error);
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
    alert('URLをコピーしました');
  }
}

function printPage() {
  window.print();
}

function exportPDF() {
  alert('PDF出力機能は準備中です');
}

function retryLoad() {
  window.location.reload();
}

// ============================================================
// sop-detail.html 専用機能
// ============================================================

async function loadSOPDetail() {
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  if (!id) {
    showError('SOP IDが指定されていません');
    return;
  }

  showLoading();
  hideError();

  try {
    let data = null;

    // まずlocalStorageから取得を試みる
    const sopData = JSON.parse(localStorage.getItem('sop_details') || '[]');
    data = sopData.find(s => s.id === parseInt(id));

    // localStorageにない場合はAPIから取得
    if (!data) {
      console.log('[DETAIL] Loading SOP from API...');
      data = await apiCall(`/sop/${id}`);
    } else {
      console.log('[DETAIL] Loading SOP from localStorage...');
    }

    displaySOPDetail(data);
    await loadRelatedSOP(data.category, id);
  } catch (error) {
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
    formEl.scrollIntoView({ behavior: 'smooth' });
  }
}

function cancelRecord() {
  const formEl = document.getElementById('record-form');
  if (formEl) {
    formEl.style.display = 'none';
  }
}

function downloadSOP() {
  alert('SOP ダウンロード機能は準備中です');
}

function printChecklist() {
  const checklistEl = document.getElementById('sopChecklist');
  if (checklistEl) {
    const printWindow = window.open('', '', 'height=600,width=800');
    printWindow.document.write('<html><head><title>チェックリスト</title></head><body>');
    printWindow.document.write(checklistEl.innerHTML);
    printWindow.document.write('</body></html>');
    printWindow.document.close();
    printWindow.print();
  }
}

function retryLoadSOP() {
  window.location.reload();
}

// ============================================================
// incident-detail.html 専用機能
// ============================================================

async function loadIncidentDetail() {
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  if (!id) {
    showError('事故レポートIDが指定されていません');
    return;
  }

  showLoading();
  hideError();

  try {
    let data = null;

    // まずlocalStorageから取得を試みる
    const incidentData = JSON.parse(localStorage.getItem('incidents_details') || '[]');
    data = incidentData.find(i => i.id === parseInt(id));

    // localStorageにない場合はAPIから取得
    if (!data) {
      console.log('[DETAIL] Loading incident from API...');
      data = await apiCall(`/incident/${id}`);
    } else {
      console.log('[DETAIL] Loading incident from localStorage...');
    }

    displayIncidentDetail(data);
    loadCorrectiveActionsFromData(data);
  } catch (error) {
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
  if (modal) modal.classList.add('is-active');
}

function closeCorrectiveActionModal() {
  const modal = document.getElementById('correctiveActionModal');
  if (modal) modal.classList.remove('is-active');
}

function retryLoadIncident() {
  window.location.reload();
}

// ============================================================
// expert-consult.html 専用機能
// ============================================================

async function loadConsultDetail() {
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  if (!id) {
    showError('相談IDが指定されていません');
    return;
  }

  showLoading();
  hideError();

  try {
    let data = null;

    // まずlocalStorageから取得を試みる
    const consultData = JSON.parse(localStorage.getItem('consultations_details') || '[]');
    data = consultData.find(c => c.id === parseInt(id));

    // localStorageにない場合はAPIから取得
    if (!data) {
      console.log('[DETAIL] Loading consultation from API...');
      data = await apiCall(`/consultation/${id}`);
    } else {
      console.log('[DETAIL] Loading consultation from localStorage...');
    }

    displayConsultDetail(data);
    loadAnswersFromData(data);
    await loadRelatedQuestions(data.tags || [], id);
  } catch (error) {
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

  // パンくずリスト更新
  updateBreadcrumb('専門家相談', data.title);
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
// ページロード時の初期化
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;

  if (path.includes('search-detail.html')) {
    loadKnowledgeDetail();
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
