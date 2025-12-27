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
    const data = await apiCall(`/knowledge/${id}`);
    displayKnowledgeDetail(data);
    await loadRelatedKnowledge(data.tags || []);
    await loadKnowledgeComments(id);
    await loadKnowledgeHistory(id);
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
      <span>作成者: ${data.created_by_name || 'N/A'}</span>
      <span>優先度: ${data.priority || '通常'}</span>
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
      <tr><th>作成者</th><td>${data.created_by_name || 'N/A'}</td></tr>
      <tr><th>カテゴリ</th><td>${data.category || 'N/A'}</td></tr>
      <tr><th>優先度</th><td>${data.priority || '通常'}</td></tr>
      <tr><th>ステータス</th><td>${data.status || '公開'}</td></tr>
    `;
  }

  // 統計情報
  updateElement('totalLikes', data.likes_count || 0);
  updateElement('totalBookmarks', data.bookmarks_count || 0);
  updateElement('totalViews', data.views_count || 0);
  updateElement('viewCount', `閲覧数 ${data.views_count || 0}`);

  // 承認フロー
  displayApprovalFlow(data.approval_status);

  // パンくずリスト更新
  updateBreadcrumb(data.category, data.title);
}

async function loadRelatedKnowledge(tags) {
  const relatedListEl = document.getElementById('relatedKnowledgeList');
  if (!relatedListEl) return;

  try {
    const data = await apiCall(`/knowledge/search?tags=${tags.join(',')}&limit=5`);
    if (data && data.results && data.results.length > 0) {
      relatedListEl.innerHTML = data.results.map(item => `
        <div class="document">
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
    const data = await apiCall(`/sop/${id}`);
    displaySOPDetail(data);
    await loadRelatedSOP(data.category);
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
  updateElement('sopNumber', `SOP番号 ${data.sop_number || 'N/A'}`);
  updateElement('sopVersion', `バージョン ${data.version || 'v1.0'}`);

  // メタ情報
  const metaEl = document.getElementById('sopMeta');
  if (metaEl) {
    metaEl.innerHTML = `
      <span>改訂日: ${formatDateShort(data.revision_date || data.updated_at)}</span>
      <span>作成: ${data.department || 'N/A'}</span>
      <span>対象: ${data.target || 'N/A'}</span>
      <span>所要時間: ${data.duration || '--'}分</span>
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

  // 手順
  const procedureEl = document.getElementById('sopProcedure');
  if (procedureEl && data.procedure) {
    if (Array.isArray(data.procedure)) {
      procedureEl.innerHTML = data.procedure.map((step, i) => `
        <div class="step-item">
          <strong>Step ${i + 1}: ${step.title || ''}</strong>
          <div>${step.description || step}</div>
        </div>
      `).join('');
    } else {
      procedureEl.innerHTML = `<div>${data.procedure}</div>`;
    }
  }

  // チェックリスト
  const checklistEl = document.getElementById('sopChecklist');
  if (checklistEl && data.checklist) {
    if (Array.isArray(data.checklist)) {
      checklistEl.innerHTML = data.checklist.map(item =>
        `<div><input type="checkbox"> ${item}</div>`
      ).join('');
    } else {
      checklistEl.innerHTML = `<div>${data.checklist}</div>`;
    }
  }

  // 注意事項
  const warningsEl = document.getElementById('sopWarnings');
  if (warningsEl && data.warnings) {
    if (Array.isArray(data.warnings)) {
      warningsEl.innerHTML = data.warnings.map(warning =>
        `<div>⚠️ ${warning}</div>`
      ).join('');
    } else {
      warningsEl.innerHTML = `<div>⚠️ ${data.warnings}</div>`;
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

async function loadRelatedSOP(category) {
  const relatedListEl = document.getElementById('relatedSOPList');
  if (!relatedListEl) return;

  try {
    const data = await apiCall(`/sop/search?category=${category}&limit=5`);
    if (data && data.results && data.results.length > 0) {
      relatedListEl.innerHTML = data.results.map(item => `
        <div class="document">
          <strong><a href="sop-detail.html?id=${item.id}">${item.title}</a></strong>
          <small>${item.sop_number || ''}</small>
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
    const data = await apiCall(`/incident/${id}`);
    displayIncidentDetail(data);
    await loadCorrectiveActions(id);
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
  updateElement('incidentNumber', `報告No. ${data.incident_number || 'N/A'}`);
  updateElement('incidentSeverity', `重大度 ${data.severity || 'N/A'}`);

  // メタ情報
  const metaEl = document.getElementById('incidentMeta');
  if (metaEl) {
    metaEl.innerHTML = `
      <span>発生日: ${formatDate(data.incident_date)}</span>
      <span>現場: ${data.site || 'N/A'}</span>
      <span>報告者: ${data.reporter_name || 'N/A'}</span>
      <span>天候: ${data.weather || 'N/A'}</span>
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
  updateElement('incidentSummary', data.summary || '概要がありません');

  // 発生情報
  const incidentInfoEl = document.getElementById('incidentInfo');
  if (incidentInfoEl) {
    incidentInfoEl.innerHTML = `
      <tr><th>発生日時</th><td>${formatDate(data.incident_date)}</td></tr>
      <tr><th>発生場所</th><td>${data.location || 'N/A'}</td></tr>
      <tr><th>天候</th><td>${data.weather || 'N/A'}</td></tr>
      <tr><th>温度</th><td>${data.temperature || 'N/A'}℃</td></tr>
      <tr><th>作業内容</th><td>${data.work_description || 'N/A'}</td></tr>
    `;
  }

  // タイムライン
  const timelineEl = document.getElementById('incidentTimeline');
  if (timelineEl && data.timeline) {
    if (Array.isArray(data.timeline)) {
      timelineEl.innerHTML = data.timeline.map(event => `
        <div class="timeline-item">
          <strong>${event.time || 'N/A'}</strong>
          <div>${event.description || ''}</div>
          <small>${event.note || ''}</small>
        </div>
      `).join('');
    } else {
      timelineEl.innerHTML = `<div>${data.timeline}</div>`;
    }
  }

  // 4M分析
  if (data.cause_analysis) {
    updateElement('causeMan', data.cause_analysis.man || '分析なし');
    updateElement('causeMachine', data.cause_analysis.machine || '分析なし');
    updateElement('causeMedia', data.cause_analysis.media || '分析なし');
    updateElement('causeManagement', data.cause_analysis.management || '分析なし');
  }

  // 即時対応
  const immediateActionsEl = document.getElementById('immediateActions');
  if (immediateActionsEl && data.immediate_actions) {
    if (Array.isArray(data.immediate_actions)) {
      immediateActionsEl.innerHTML = data.immediate_actions.map(action =>
        `<div>✓ ${action}</div>`
      ).join('');
    } else {
      immediateActionsEl.innerHTML = `<div>${data.immediate_actions}</div>`;
    }
  }

  // 再発防止策
  const preventionEl = document.getElementById('preventionMeasures');
  if (preventionEl && data.prevention_measures) {
    if (Array.isArray(data.prevention_measures)) {
      preventionEl.innerHTML = data.prevention_measures.map(measure =>
        `<div>• ${measure}</div>`
      ).join('');
    } else {
      preventionEl.innerHTML = `<div>${data.prevention_measures}</div>`;
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
              <button class="cta ghost" onclick="updateCorrectiveAction(${action.id})">更新</button>
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
    const data = await apiCall(`/consultation/${id}`);
    displayConsultDetail(data);
    await loadAnswers(id);
    await loadRelatedQuestions(data.tags || []);
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
  updateElement('consultStatus', `ステータス ${data.status || '受付中'}`);
  updateElement('responseTime', `回答時間 ${data.response_time || '--'}時間`);

  // メタ情報
  const metaEl = document.getElementById('consultMeta');
  if (metaEl) {
    metaEl.innerHTML = `
      <span>投稿日: ${formatDate(data.created_at)}</span>
      <span>投稿者: ${data.author_name || 'N/A'}</span>
      <span>カテゴリ: ${data.category || 'N/A'}</span>
      <span>現場: ${data.site || 'N/A'}</span>
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
      <tr><th>投稿者</th><td>${data.author_name || 'N/A'}</td></tr>
      <tr><th>カテゴリ</th><td>${data.category || 'N/A'}</td></tr>
      <tr><th>現場</th><td>${data.site || 'N/A'}</td></tr>
      <tr><th>ステータス</th><td>${data.status || '受付中'}</td></tr>
    `;
  }

  // 優先度・期限
  updateElement('priority', data.priority || '通常');
  updateElement('deadline', formatDateShort(data.deadline) || 'N/A');
  updateElement('elapsedTime', calculateElapsedTime(data.created_at));

  // 統計
  updateElement('totalAnswers', data.answer_count || 0);
  updateElement('viewCount', data.view_count || 0);
  updateElement('followerCount', data.follower_count || 0);

  // パンくずリスト更新
  updateBreadcrumb('専門家相談', data.title);
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

async function loadRelatedQuestions(tags) {
  const relatedEl = document.getElementById('relatedQuestions');
  if (!relatedEl) return;

  try {
    const data = await apiCall(`/consultation/search?tags=${tags.join(',')}&limit=5`);
    if (data && data.results && data.results.length > 0) {
      relatedEl.innerHTML = data.results.map(item => `
        <div class="document">
          <strong><a href="expert-consult.html?id=${item.id}">${item.title}</a></strong>
          <small>${item.answer_count || 0}件の回答</small>
          <div>${item.summary || ''}</div>
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
