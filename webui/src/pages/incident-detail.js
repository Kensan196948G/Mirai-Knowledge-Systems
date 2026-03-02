/**
 * @fileoverview 事故レポート詳細ページモジュール v2.0.0
 * @module pages/incident-detail
 * @description Phase F-4: detail-pages.js 分割版 - incident-detail.html専用
 *
 * 担当機能:
 * - 事故レポート詳細読み込み (loadIncidentDetail)
 * - 事故レポート詳細表示 (displayIncidentDetail)
 * - 是正措置管理 (loadCorrectiveActionsFromData / loadCorrectiveActions / addCorrectiveAction /
 *   closeCorrectiveActionModal / submitCorrectiveAction)
 * - PDF・共有 (downloadPDF / shareIncident / closeShareModal / copyShareUrl /
 *   shareViaEmail / shareViaSlack / shareViaTeams)
 * - ステータス更新 (updateIncidentStatus / closeStatusModal / submitStatusUpdate)
 * - 新規作成モーダル (openNewIncidentModal / createNewIncidentModal /
 *   closeNewIncidentModal / submitNewIncident)
 * - 編集機能 (editIncident / closeEditIncidentModal / submitEditIncident)
 * - リトライ (retryLoadIncident)
 *
 * 依存: page-renderer.js (showLoading, hideLoading, showError, hideError,
 *       formatDate, formatDateShort, updateElement, displayApprovalFlow, updateBreadcrumb, apiCall)
 * 依存: dom-helpers.js (setSecureChildren, createSecureElement, createMetaInfoElement,
 *       createTagElement, createTableRow, createTableRowWithHTML, createTimelineElement,
 *       createDocumentElement, createEmptyMessage, createErrorMessage)
 */

// ============================================================
// 事故レポート詳細読み込み
// ============================================================

/**
 * 事故レポート詳細データを読み込む（URL の ?id= から ID を取得）
 */
async function loadIncidentDetail() {
  const log = window.logger || console;
  log.log('[INCIDENT DETAIL] Starting to load...');
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');
  const inProduction = typeof isProductionMode === 'function' ? isProductionMode() : false;

  log.log('[INCIDENT DETAIL] ID from URL:', id, 'Production mode:', inProduction);

  if (!id) {
    if (typeof showError === 'function') showError('事故レポートIDが指定されていません。一覧ページに戻ります...');
    setTimeout(() => {
      window.location.href = 'index.html';
    }, 2000);
    return;
  }

  if (typeof showLoading === 'function') showLoading();
  if (typeof hideError === 'function') hideError();

  try {
    let data = null;

    log.log('[DETAIL] Loading incident from API (data consistency fix)...');
    try {
      const response = await apiCall(`/incident/${id}`);
      log.log('[DETAIL] API Response:', response);

      data = response?.data || response;

      log.log('[DETAIL] Extracted data:', data);
      log.log('[DETAIL] Successfully loaded from API');
    } catch (apiError) {
      log.error('[DETAIL] API call failed:', apiError);

      const incidentDataStr = localStorage.getItem('incidents_details');
      if (incidentDataStr) {
        log.log('[DETAIL] Fallback to localStorage...');
        const incidentData = JSON.parse(incidentDataStr);
        data = incidentData.find(i => i.id === parseInt(id));
        if (data) {
          log.warn('[DETAIL] Using localStorage data (may be outdated)');
        }
      }
    }

    if (!data) {
      if (typeof showError === 'function') showError(`事故レポートID ${id} が見つかりません`);
      return;
    }

    log.log('[INCIDENT DETAIL] Displaying data...');
    displayIncidentDetail(data);
    loadCorrectiveActionsFromData(data);
  } catch (error) {
    log.error('[INCIDENT DETAIL] Error:', error);
    if (typeof showError === 'function') showError(`データの読み込みに失敗しました: ${error.message}`);
  } finally {
    if (typeof hideLoading === 'function') hideLoading();
  }
}

// ============================================================
// 事故レポート詳細表示
// ============================================================

/**
 * 事故レポートデータを画面に表示する
 * @param {Object} data - 事故レポートデータオブジェクト
 */
function displayIncidentDetail(data) {
  if (typeof updateElement === 'function') {
    updateElement('incidentTitle', data.title || '事故レポートタイトル');

    const incidentNumber = data.incident_number || `INC-${data.id}`;
    updateElement('incidentNumber', `報告No. ${incidentNumber}`);
    updateElement('incidentSeverity', `重大度 ${data.severity || 'N/A'}`);
  }

  // メタ情報
  const metaEl = document.getElementById('incidentMeta');
  if (metaEl && typeof createMetaInfoElement === 'function' && typeof setSecureChildren === 'function') {
    setSecureChildren(metaEl, createMetaInfoElement({
      occurred_at: data.occurred_at || data.incident_date,
      location: data.location || 'N/A',
      reporter: data.reporter || data.reporter_name || 'N/A',
      type: data.type || 'N/A'
    }, 'incident'));
  }

  // タグ
  const tagsEl = document.getElementById('incidentTags');
  if (tagsEl && data.tags && typeof createTagElement === 'function' && typeof setSecureChildren === 'function') {
    setSecureChildren(tagsEl, data.tags.map(tag => createTagElement(tag)));
  }

  if (typeof updateElement === 'function') {
    updateElement('incidentSummary', data.description || data.summary || '概要がありません');
  }

  // 発生情報テーブル
  const incidentInfoEl = document.getElementById('incidentInfo');
  if (incidentInfoEl && typeof createTableRow === 'function' && typeof setSecureChildren === 'function') {
    const rows = [
      { label: '発生日時', value: formatDate(data.occurred_at || data.incident_date) },
      { label: '発生場所', value: data.location || 'N/A' },
      { label: '種類', value: data.type || 'N/A' },
      { label: '重大度', value: data.severity || 'N/A' },
      { label: 'ステータス', value: data.status || 'N/A' }
    ];
    setSecureChildren(incidentInfoEl, rows.map(row => createTableRow([row.label, row.value])));
  }

  // タイムライン
  const timelineEl = document.getElementById('incidentTimeline');
  if (timelineEl && data.timeline) {
    if (Array.isArray(data.timeline) && typeof createTimelineElement === 'function' && typeof setSecureChildren === 'function') {
      setSecureChildren(timelineEl, data.timeline.map(event => createTimelineElement(event)));
    } else if (typeof createSecureElement === 'function' && typeof setSecureChildren === 'function') {
      setSecureChildren(timelineEl, createSecureElement('div', {}, [data.timeline]));
    }
  }

  // 原因分析（4M分析）
  if (data.root_causes && Array.isArray(data.root_causes)) {
    const causeAnalysisEl = document.getElementById('causeAnalysis');
    if (causeAnalysisEl && typeof updateElement === 'function') {
      const causesByCategory = {
        man: [],
        machine: [],
        media: [],
        management: []
      };

      data.root_causes.forEach((cause, i) => {
        const categories = ['man', 'machine', 'media', 'management'];
        const category = categories[i % categories.length];
        causesByCategory[category].push(cause);
      });

      updateElement('causeMan', causesByCategory.man.length > 0 ? causesByCategory.man.join('\n') : '分析なし');
      updateElement('causeMachine', causesByCategory.machine.length > 0 ? causesByCategory.machine.join('\n') : '分析なし');
      updateElement('causeMedia', causesByCategory.media.length > 0 ? causesByCategory.media.join('\n') : '分析なし');
      updateElement('causeManagement', causesByCategory.management.length > 0 ? causesByCategory.management.join('\n') : '分析なし');
    }
  }

  if (typeof updateElement === 'function') {
    updateElement('completionRate', data.completion_rate || 0);
    updateElement('deadlineRate', data.deadline_rate || 0);
    updateElement('remainingTasks', data.remaining_tasks || 0);
  }

  if (typeof displayApprovalFlow === 'function') displayApprovalFlow(data.approval_status);
  if (typeof updateBreadcrumb === 'function') updateBreadcrumb('事故レポート', data.title);
}

// ============================================================
// 是正措置管理
// ============================================================

/**
 * 是正措置を localStorage データから読み込む
 * @param {Object} data - 事故レポートデータ
 */
function loadCorrectiveActionsFromData(data) {
  const tableEl = document.getElementById('correctiveActionTable');
  if (!tableEl) return;

  const actions = data.corrective_actions || [];

  if (typeof setSecureChildren === 'function' && typeof createTableRowWithHTML === 'function') {
    if (actions.length > 0) {
      setSecureChildren(tableEl, actions.map(action => {
        const statusClass = action.status === 'completed' ? 'is-ok' : action.status === 'in_progress' ? 'is-warn' : 'is-hold';
        const statusText = action.status === 'completed' ? '完了' : action.status === 'in_progress' ? '進行中' : '未着手';
        const statusCell = document.createElement('span');
        const dot = document.createElement('span');
        dot.className = `status-dot ${statusClass}`;
        statusCell.appendChild(dot);
        statusCell.appendChild(document.createTextNode(` ${statusText}`));
        const updateBtn = document.createElement('button');
        updateBtn.className = 'cta ghost';
        updateBtn.textContent = '更新';
        updateBtn.addEventListener('click', () => alert('是正措置更新機能は準備中です'));
        return createTableRowWithHTML([
          statusCell,
          action.action || action.content,
          action.responsible || action.assignee_name || 'N/A',
          formatDateShort(action.deadline),
          `${action.progress || (action.status === 'completed' ? 100 : action.status === 'in_progress' ? 50 : 0)}%`,
          updateBtn
        ]);
      }));

      const completedCount = actions.filter(a => a.status === 'completed').length;
      const completionRate = Math.round((completedCount / actions.length) * 100);
      const onTimeCount = actions.filter(a => a.status === 'completed' && new Date(a.deadline) >= new Date()).length;
      const deadlineRate = actions.length > 0 ? Math.round((onTimeCount / actions.length) * 100) : 0;
      const remainingTasks = actions.filter(a => a.status !== 'completed').length;

      if (typeof updateElement === 'function') {
        updateElement('completionRate', completionRate);
        updateElement('deadlineRate', deadlineRate);
        updateElement('remainingTasks', remainingTasks);
      }
    } else if (typeof createEmptyMessage === 'function') {
      setSecureChildren(tableEl, createEmptyMessage('是正措置がありません', 6));
    }
  }
}

/**
 * 是正措置を API から読み込む
 * @param {string|number} incidentId - 事故レポート ID
 */
async function loadCorrectiveActions(incidentId) {
  const log = window.logger || console;
  const tableEl = document.getElementById('correctiveActionTable');
  if (!tableEl) return;

  try {
    const actions = await apiCall(`/incident/${incidentId}/corrective-actions`);
    if (typeof setSecureChildren === 'function' && typeof createTableRowWithHTML === 'function') {
      if (actions && actions.length > 0) {
        setSecureChildren(tableEl, actions.map(action => {
          const statusClass = action.status === 'completed' ? 'is-ok' : 'is-warn';
          const dotSpan = document.createElement('span');
          dotSpan.className = `status-dot ${statusClass}`;
          const actionBtn = document.createElement('button');
          actionBtn.className = 'cta ghost';
          actionBtn.textContent = '更新';
          actionBtn.addEventListener('click', () => alert('是正措置更新機能は準備中です'));
          return createTableRowWithHTML([
            dotSpan,
            action.content,
            action.assignee_name || 'N/A',
            formatDateShort(action.deadline),
            `${action.progress || 0}%`,
            actionBtn
          ]);
        }));
      } else if (typeof createEmptyMessage === 'function') {
        setSecureChildren(tableEl, createEmptyMessage('是正措置がありません', 6));
      }
    }
  } catch (error) {
    log.error('Failed to load corrective actions:', error);
    if (typeof setSecureChildren === 'function' && typeof createErrorMessage === 'function') {
      setSecureChildren(tableEl, createErrorMessage('是正措置の読み込みに失敗しました', 6));
    }
  }
}

/**
 * 是正措置追加モーダルを開く
 */
function addCorrectiveAction() {
  const modal = document.getElementById('correctiveActionModal');
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    const form = document.getElementById('correctiveActionForm');
    if (form) form.reset();
  }
}

/**
 * 是正措置モーダルを閉じる
 */
function closeCorrectiveActionModal() {
  const modal = document.getElementById('correctiveActionModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

/**
 * 是正措置を送信・保存する
 * @param {Event} event - フォーム送信イベント
 */
function submitCorrectiveAction(event) {
  event.preventDefault();

  const content = document.getElementById('actionContent').value;
  const assignee = document.getElementById('actionAssignee').value;
  const deadline = document.getElementById('actionDeadline').value;
  const priority = document.getElementById('actionPriority').value;

  const urlParams = new URLSearchParams(window.location.search);
  const incidentId = parseInt(urlParams.get('id'));

  const incidentsStr = localStorage.getItem('incidents_details');
  if (!incidentsStr) {
    if (typeof showToast === 'function') showToast('データの読み込みに失敗しました', 'error');
    return;
  }

  const incidents = JSON.parse(incidentsStr);
  const incident = incidents.find(i => i.id === incidentId);

  if (!incident) {
    if (typeof showToast === 'function') showToast('事故レポートが見つかりません', 'error');
    return;
  }

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
  localStorage.setItem('incidents_details', JSON.stringify(incidents));

  closeCorrectiveActionModal();

  if (typeof showToast === 'function') showToast('是正措置を追加しました', 'success');
  setTimeout(() => {
    window.location.reload();
  }, 1000);
}

// ============================================================
// PDF・共有機能
// ============================================================

/**
 * PDFを生成・ダウンロードする
 * @param {string} [type] - ページタイプ
 */
function downloadPDFIncident(type) {
  if (typeof showToast === 'function') showToast('PDFを生成中...', 'info');
  setTimeout(() => {
    window.print();
  }, 500);
}

/**
 * 事故レポート共有モーダルを開く
 */
function shareIncident() {
  if (typeof openShareModal === 'function') {
    openShareModal();
  } else {
    const modal = document.getElementById('shareModal');
    const shareUrlEl = document.getElementById('shareUrl');
    if (modal && shareUrlEl) {
      shareUrlEl.value = window.location.href;
      modal.style.display = 'flex';
      document.body.style.overflow = 'hidden';
    }
  }
}

/**
 * 共有モーダルを閉じる（インシデント専用ローカル版）
 */
function closeShareModalIncident() {
  const modal = document.getElementById('shareModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

/**
 * 共有URLをコピー（インシデント専用ローカル版）
 */
function copyShareUrlIncident() {
  const shareUrlEl = document.getElementById('shareUrl');
  if (shareUrlEl) {
    shareUrlEl.select();
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(shareUrlEl.value).then(() => {
        if (typeof showToast === 'function') showToast('URLをコピーしました', 'success');
      }).catch(() => {
        document.execCommand('copy');
        if (typeof showToast === 'function') showToast('URLをコピーしました', 'success');
      });
    } else {
      document.execCommand('copy');
      if (typeof showToast === 'function') showToast('URLをコピーしました', 'success');
    }
  }
}

/**
 * メールで共有（インシデント）
 */
function shareViaEmail() {
  const shareUrlEl = document.getElementById('shareUrl');
  const url = shareUrlEl ? shareUrlEl.value : window.location.href;
  const urlParams = new URLSearchParams(window.location.search);
  const incidentId = urlParams.get('id');
  const subject = encodeURIComponent(`事故レポート共有: INC-${incidentId}`);
  const body = encodeURIComponent(`事故レポートを共有します。\n\n${url}`);
  window.location.href = `mailto:?subject=${subject}&body=${body}`;
  if (typeof showToast === 'function') showToast('メールアプリを起動しました', 'info');
}

/**
 * Slackで共有（インシデント、将来実装）
 */
function shareViaSlack() {
  if (typeof showToast === 'function') showToast('Slack連携機能は準備中です', 'info');
}

/**
 * Teamsで共有（インシデント、将来実装）
 */
function shareViaTeams() {
  if (typeof showToast === 'function') showToast('Teams連携機能は準備中です', 'info');
}

// ============================================================
// ステータス更新
// ============================================================

/**
 * ステータス更新モーダルを開く
 */
function updateIncidentStatus() {
  const modal = document.getElementById('statusModal');
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    const newStatusEl = document.getElementById('newStatus');
    const statusCommentEl = document.getElementById('statusComment');
    if (newStatusEl) newStatusEl.value = '';
    if (statusCommentEl) statusCommentEl.value = '';
  }
}

/**
 * ステータス更新モーダルを閉じる
 */
function closeStatusModal() {
  const modal = document.getElementById('statusModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

/**
 * ステータス更新を送信・保存する
 */
function submitStatusUpdate() {
  const newStatusEl = document.getElementById('newStatus');
  const commentEl = document.getElementById('statusComment');
  const newStatus = newStatusEl ? newStatusEl.value : '';
  const comment = commentEl ? commentEl.value : '';

  if (!newStatus) {
    if (typeof showToast === 'function') showToast('ステータスを選択してください', 'warning');
    return;
  }

  const urlParams = new URLSearchParams(window.location.search);
  const incidentId = parseInt(urlParams.get('id'));

  const incidentsStr = localStorage.getItem('incidents_details');
  if (!incidentsStr) {
    if (typeof showToast === 'function') showToast('データの読み込みに失敗しました', 'error');
    return;
  }

  const incidents = JSON.parse(incidentsStr);
  const incident = incidents.find(i => i.id === incidentId);

  if (!incident) {
    if (typeof showToast === 'function') showToast('事故レポートが見つかりません', 'error');
    return;
  }

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

  localStorage.setItem('incidents_details', JSON.stringify(incidents));

  closeStatusModal();

  if (typeof showToast === 'function') showToast(`ステータスを「${newStatus}」に更新しました`, 'success');
  setTimeout(() => {
    window.location.reload();
  }, 1000);
}

// ============================================================
// 新規事故レポート作成モーダル
// ============================================================

/**
 * 新規事故レポート作成モーダルを開く
 */
function openNewIncidentModal() {
  const modal = document.getElementById('newIncidentModal');
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    const form = document.getElementById('newIncidentForm');
    if (form) form.reset();
    const now = new Date();
    const localDateTime = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    const dateEl = document.getElementById('newIncidentDate');
    if (dateEl) dateEl.value = localDateTime;
  } else {
    createNewIncidentModal();
  }
}

/**
 * 新規事故レポート作成モーダルを動的に作成する
 */
function createNewIncidentModal() {
  if (typeof createSecureElement !== 'function' || typeof setSecureChildren !== 'function') return;

  const modal = createSecureElement('div', {
    id: 'newIncidentModal',
    className: 'modal',
    style: 'display: flex;'
  });

  const modalContent = createSecureElement('div', { className: 'modal-content' });

  const header = createSecureElement('div', { className: 'modal-header' }, [
    createSecureElement('h2', {}, ['新規事故レポート作成']),
    createSecureElement('button', { className: 'modal-close', onclick: 'closeNewIncidentModal()' }, ['×'])
  ]);

  const form = createSecureElement('form', { id: 'newIncidentForm', onsubmit: 'submitNewIncident(event)' });

  const body = createSecureElement('div', { className: 'modal-body' }, [
    createSecureElement('div', { className: 'field' }, [
      createSecureElement('label', {}, ['タイトル ', createSecureElement('span', { className: 'required' }, ['*'])]),
      createSecureElement('input', { type: 'text', id: 'incidentNewTitle', required: true, placeholder: '例: 足場倒壊事故' })
    ]),
    createSecureElement('div', { className: 'field' }, [
      createSecureElement('label', {}, ['発生日時 ', createSecureElement('span', { className: 'required' }, ['*'])]),
      createSecureElement('input', { type: 'datetime-local', id: 'incidentNewDate', required: true })
    ]),
    createSecureElement('div', { className: 'field' }, [
      createSecureElement('label', {}, ['発生場所 ', createSecureElement('span', { className: 'required' }, ['*'])]),
      createSecureElement('input', { type: 'text', id: 'incidentNewLocation', required: true, placeholder: '例: A工区 3階' })
    ]),
    createSecureElement('div', { className: 'field' }, [
      createSecureElement('label', {}, ['重大度 ', createSecureElement('span', { className: 'required' }, ['*'])]),
      createSecureElement('select', { id: 'incidentNewSeverity', required: true }, [
        createSecureElement('option', { value: '' }, ['選択してください']),
        createSecureElement('option', { value: '低' }, ['低']),
        createSecureElement('option', { value: '中' }, ['中']),
        createSecureElement('option', { value: '高' }, ['高']),
        createSecureElement('option', { value: '重大' }, ['重大'])
      ])
    ]),
    createSecureElement('div', { className: 'field' }, [
      createSecureElement('label', {}, ['事故内容 ', createSecureElement('span', { className: 'required' }, ['*'])]),
      createSecureElement('textarea', { id: 'incidentNewContent', required: true, rows: '6', placeholder: '事故の詳細を記入してください...' })
    ]),
    createSecureElement('div', { className: 'field' }, [
      createSecureElement('label', {}, ['写真・資料']),
      createSecureElement('input', { type: 'file', id: 'incidentNewPhotos', multiple: true, accept: 'image/*,.pdf' }),
      createSecureElement('small', {}, ['画像またはPDFファイル（最大10MB）'])
    ])
  ]);

  const actions = createSecureElement('div', { className: 'modal-actions' }, [
    createSecureElement('button', { type: 'button', className: 'cta ghost', onclick: 'closeNewIncidentModal()' }, ['キャンセル']),
    createSecureElement('button', { type: 'submit', className: 'cta' }, ['作成'])
  ]);

  setSecureChildren(form, [body, actions]);
  setSecureChildren(modalContent, [header, form]);
  setSecureChildren(modal, modalContent);

  document.body.appendChild(modal);
  document.body.style.overflow = 'hidden';

  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      closeNewIncidentModal();
    }
  });

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
    const form = document.getElementById('newIncidentForm');
    if (form) form.reset();
  }
}

/**
 * 新規事故レポートを送信する
 * @param {Event} event - フォーム送信イベント
 */
async function submitNewIncident(event) {
  event.preventDefault();

  const titleEl = document.getElementById('incidentNewTitle') || document.getElementById('newIncidentTitle');
  const dateEl = document.getElementById('incidentNewDate') || document.getElementById('newIncidentDate');
  const locationEl = document.getElementById('incidentNewLocation') || document.getElementById('newIncidentLocation');
  const severityEl = document.getElementById('incidentNewSeverity') || document.getElementById('newIncidentSeverity');
  const contentEl = document.getElementById('incidentNewContent') || document.getElementById('newIncidentContent');

  const title = titleEl ? titleEl.value : '';
  const date = dateEl ? dateEl.value : '';
  const location = locationEl ? locationEl.value : '';
  const severity = severityEl ? severityEl.value : '';
  const content = contentEl ? contentEl.value : '';

  const data = {
    title,
    occurred_at: date,
    location,
    severity,
    description: content,
    status: 'reported'
  };

  const log = window.logger || console;

  try {
    if (typeof showNotification === 'function') showNotification('事故レポートを作成中...', 'info');

    await apiCall('/incidents', {
      method: 'POST',
      body: JSON.stringify(data)
    });

    if (typeof showNotification === 'function') showNotification('事故レポートを作成しました', 'success');
    closeNewIncidentModal();

    setTimeout(() => {
      window.location.reload();
    }, 1000);
  } catch (error) {
    log.error('Failed to create incident:', error);

    // APIが失敗した場合はlocalStorageに保存
    const incidentsStr = localStorage.getItem('incidents_details');
    const incidents = incidentsStr ? JSON.parse(incidentsStr) : [];
    const maxId = incidents.length > 0 ? Math.max(...incidents.map(i => i.id)) : 0;
    const newId = maxId + 1;

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
        { time: date, event: '事故発生', details: content },
        { time: new Date().toISOString(), event: 'レポート作成', details: 'システムに登録されました' }
      ],
      root_causes: [],
      corrective_actions: [],
      completion_rate: 0,
      deadline_rate: 0,
      remaining_tasks: 0
    };

    incidents.push(newIncident);
    localStorage.setItem('incidents_details', JSON.stringify(incidents));

    closeNewIncidentModal();
    if (typeof showToast === 'function') showToast('新規事故レポートを作成しました', 'success');
    setTimeout(() => {
      window.location.href = `incident-detail.html?id=${newId}`;
    }, 1000);
  }
}

// ============================================================
// 編集機能
// ============================================================

/**
 * 事故レポート編集モーダルを開く
 */
function editIncident() {
  const modal = document.getElementById('editIncidentModal');
  if (!modal) return;

  const urlParams = new URLSearchParams(window.location.search);
  const incidentId = parseInt(urlParams.get('id'));

  const incidentsStr = localStorage.getItem('incidents_details');
  if (!incidentsStr) {
    if (typeof showToast === 'function') showToast('データの読み込みに失敗しました', 'error');
    return;
  }

  const incidents = JSON.parse(incidentsStr);
  const incident = incidents.find(i => i.id === incidentId);

  if (!incident) {
    if (typeof showToast === 'function') showToast('事故レポートが見つかりません', 'error');
    return;
  }

  const editTitleEl = document.getElementById('editIncidentTitle');
  const editDateEl = document.getElementById('editIncidentDate');
  const editLocationEl = document.getElementById('editIncidentLocation');
  const editSeverityEl = document.getElementById('editIncidentSeverity');
  const editContentEl = document.getElementById('editIncidentContent');

  if (editTitleEl) editTitleEl.value = incident.title || '';

  const incidentDate = incident.occurred_at || incident.incident_date;
  if (incidentDate && editDateEl) {
    const date = new Date(incidentDate);
    const localDateTime = new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    editDateEl.value = localDateTime;
  }

  if (editLocationEl) editLocationEl.value = incident.location || '';
  if (editSeverityEl) editSeverityEl.value = incident.severity || '';
  if (editContentEl) editContentEl.value = incident.description || incident.summary || '';

  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

/**
 * 事故レポート編集モーダルを閉じる
 */
function closeEditIncidentModal() {
  const modal = document.getElementById('editIncidentModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

/**
 * 事故レポートの編集内容を送信・保存する
 * @param {Event} event - フォーム送信イベント
 */
function submitEditIncident(event) {
  event.preventDefault();

  const title = document.getElementById('editIncidentTitle').value;
  const date = document.getElementById('editIncidentDate').value;
  const location = document.getElementById('editIncidentLocation').value;
  const severity = document.getElementById('editIncidentSeverity').value;
  const content = document.getElementById('editIncidentContent').value;

  const urlParams = new URLSearchParams(window.location.search);
  const incidentId = parseInt(urlParams.get('id'));

  const incidentsStr = localStorage.getItem('incidents_details');
  if (!incidentsStr) {
    if (typeof showToast === 'function') showToast('データの読み込みに失敗しました', 'error');
    return;
  }

  const incidents = JSON.parse(incidentsStr);
  const incident = incidents.find(i => i.id === incidentId);

  if (!incident) {
    if (typeof showToast === 'function') showToast('事故レポートが見つかりません', 'error');
    return;
  }

  incident.title = title;
  incident.occurred_at = date;
  incident.incident_date = date;
  incident.location = location;
  incident.severity = severity;
  incident.description = content;
  incident.summary = content;
  incident.updated_at = new Date().toISOString();

  localStorage.setItem('incidents_details', JSON.stringify(incidents));

  closeEditIncidentModal();

  if (typeof showToast === 'function') showToast('事故レポートを更新しました', 'success');
  setTimeout(() => {
    window.location.reload();
  }, 1000);
}

/**
 * 事故レポートページをリロード（リトライ）
 */
function retryLoadIncident() {
  window.location.reload();
}

// ============================================================
// ページ初期化（incident-detail.html 専用）
// ============================================================

/**
 * incident-detail.html のページ初期化処理
 */
export async function initPage() {
  loadIncidentDetail();
}

// ============================================================
// グローバル公開（後方互換性）
// ============================================================

if (typeof window.MKSApp === 'undefined') window.MKSApp = {};
if (typeof window.MKSApp.DetailPages === 'undefined') window.MKSApp.DetailPages = {};
window.MKSApp.DetailPages.Incident = {
  load: loadIncidentDetail,
  display: displayIncidentDetail,
  loadCorrectiveActions: loadCorrectiveActionsFromData,
  addAction: addCorrectiveAction,
  downloadPDF: downloadPDFIncident,
  share: shareIncident,
  updateStatus: updateIncidentStatus,
  edit: editIncident
};

window.loadIncidentDetail = loadIncidentDetail;
window.displayIncidentDetail = displayIncidentDetail;
window.loadCorrectiveActionsFromData = loadCorrectiveActionsFromData;
window.loadCorrectiveActions = loadCorrectiveActions;
window.addCorrectiveAction = addCorrectiveAction;
window.closeCorrectiveActionModal = closeCorrectiveActionModal;
window.submitCorrectiveAction = submitCorrectiveAction;
window.shareIncident = shareIncident;
window.shareViaEmail = window.shareViaEmail || shareViaEmail;
window.shareViaSlack = window.shareViaSlack || shareViaSlack;
window.shareViaTeams = window.shareViaTeams || shareViaTeams;
window.updateIncidentStatus = updateIncidentStatus;
window.closeStatusModal = closeStatusModal;
window.submitStatusUpdate = submitStatusUpdate;
window.openNewIncidentModal = openNewIncidentModal;
window.createNewIncidentModal = createNewIncidentModal;
window.closeNewIncidentModal = closeNewIncidentModal;
window.submitNewIncident = submitNewIncident;
window.editIncident = editIncident;
window.closeEditIncidentModal = closeEditIncidentModal;
window.submitEditIncident = submitEditIncident;
window.retryLoadIncident = retryLoadIncident;

export {
  loadIncidentDetail,
  displayIncidentDetail,
  loadCorrectiveActionsFromData,
  loadCorrectiveActions,
  addCorrectiveAction,
  closeCorrectiveActionModal,
  submitCorrectiveAction,
  downloadPDFIncident,
  shareIncident,
  closeShareModalIncident,
  copyShareUrlIncident,
  shareViaEmail,
  shareViaSlack,
  shareViaTeams,
  updateIncidentStatus,
  closeStatusModal,
  submitStatusUpdate,
  openNewIncidentModal,
  createNewIncidentModal,
  closeNewIncidentModal,
  submitNewIncident,
  editIncident,
  closeEditIncidentModal,
  submitEditIncident,
  retryLoadIncident
};
