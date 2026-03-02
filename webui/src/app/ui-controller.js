/**
 * @fileoverview UI制御モジュール v2.0.0
 * @module app/ui-controller
 * @description Phase F-4: app.js 分割版 - UI制御処理
 *
 * 担当機能:
 * - モーダル表示・非表示管理（ナレッジ, 相談, 検索, 通知, 設定, MFA）
 * - トースト通知表示
 * - ローディング表示制御
 * - 空状態表示 (showEmptyState)
 * - ダッシュボード統計更新 (updateDashboardStats)
 * - 承認・却下機能 (approveSelected / rejectSelected)
 * - Chart.js グラフ初期化 (initDashboardCharts)
 * - ユーザー設定読み込み (loadUserSettings)
 */

// ============================================================
// モーダル制御
// ============================================================

/**
 * 新規ナレッジ登録モーダルを開く
 */
function openNewKnowledgeModal() {
  if (typeof checkPermission === 'function' && !checkPermission('construction_manager')) {
    if (typeof showNotification === 'function') {
      showNotification('ナレッジ登録権限がありません。', 'error');
    }
    return;
  }
  const modal = document.getElementById('newKnowledgeModal');
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }
}

/**
 * 新規ナレッジ登録モーダルを閉じる
 */
function closeNewKnowledgeModal() {
  const modal = document.getElementById('newKnowledgeModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
    const form = document.getElementById('newKnowledgeForm');
    if (form) form.reset();
  }
}

/**
 * 新規相談モーダルを開く（expert-consult-actions.js へ委譲）
 */
function openNewConsultModal() {
  if (typeof submitNewConsultation === 'function') {
    submitNewConsultation();
  } else {
    createNewConsultModalFallback();
  }
}

/**
 * 新規相談モーダルを閉じる（フォールバック）
 */
function closeNewConsultModalFallback() {
  const modal = document.getElementById('newConsultModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

/**
 * 新規相談モーダルを作成（フォールバック実装）
 * DOM API 使用（XSS 対策）
 */
function createNewConsultModalFallback() {
  const existing = document.getElementById('newConsultModal');
  if (existing) {
    existing.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    return;
  }

  const DH = window.DOMHelper;
  if (!DH) {
    const log = window.logger || console;
    log.error('[UI] DOMHelper not available for createNewConsultModalFallback');
    return;
  }

  const modal = DH.createElement('div', { id: 'newConsultModal', class: 'modal', style: { display: 'flex' } });
  const content = DH.createElement('div', { class: 'modal-content' });
  const header = DH.createElement('div', { class: 'modal-header' });
  const title = DH.createElement('h2', {}, '専門家に相談');
  const closeBtn = DH.createElement('button', { class: 'modal-close', onclick: 'closeNewConsultModalFallback()' }, '×');
  header.appendChild(title);
  header.appendChild(closeBtn);

  const body = DH.createElement('div', { class: 'modal-body' });
  const form = DH.createElement('form', { id: 'newConsultForm' });

  const fields = [
    { id: 'newConsultTitle', label: '相談タイトル', type: 'input', inputType: 'text', required: true, placeholder: '相談の概要を簡潔に入力してください' },
    { id: 'newConsultContent', label: '相談内容', type: 'textarea', required: true, placeholder: '具体的な相談内容を入力してください（最小10文字）' }
  ];

  fields.forEach(f => {
    const fieldDiv = DH.createElement('div', { class: 'field' });
    const label = DH.createElement('label', {});
    label.appendChild(document.createTextNode(f.label + ' '));
    if (f.required) {
      const req = DH.createElement('span', { class: 'required' }, '*');
      label.appendChild(req);
    }
    fieldDiv.appendChild(label);

    let input;
    if (f.type === 'textarea') {
      input = DH.createElement('textarea', { id: f.id, rows: 6, required: f.required, placeholder: f.placeholder });
    } else {
      input = DH.createElement('input', { type: f.inputType, id: f.id, required: f.required, placeholder: f.placeholder });
    }
    fieldDiv.appendChild(input);
    form.appendChild(fieldDiv);
  });

  const actions = DH.createElement('div', { class: 'modal-actions' });
  const cancelBtn = DH.createElement('button', { type: 'button', class: 'cta ghost', onclick: 'closeNewConsultModalFallback()' }, 'キャンセル');
  const submitBtn = DH.createElement('button', { type: 'submit', class: 'cta' }, '相談を投稿');
  actions.appendChild(cancelBtn);
  actions.appendChild(submitBtn);
  form.appendChild(actions);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (typeof submitNewConsultationAPI === 'function') {
      await submitNewConsultationAPI();
    }
  });

  body.appendChild(form);
  content.appendChild(header);
  content.appendChild(body);
  modal.appendChild(content);
  document.body.appendChild(modal);
  document.body.style.overflow = 'hidden';
}

/**
 * 検索モーダルを開く
 */
function openSearchModal() {
  const modal = document.getElementById('searchModal');
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }
}

/**
 * 検索モーダルを閉じる
 */
function closeSearchModal() {
  const modal = document.getElementById('searchModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

/**
 * 通知パネルを開く
 */
async function openNotificationPanel() {
  const panel = document.getElementById('notificationSidePanel');
  if (panel) {
    panel.classList.add('open');
    document.body.style.overflow = 'hidden';
    if (typeof loadNotifications === 'function') {
      const notifications = await loadNotifications();
      displayNotifications(notifications);
    }
  }
}

/**
 * 通知パネルを閉じる
 */
function closeNotificationPanel() {
  const panel = document.getElementById('notificationSidePanel');
  if (panel) {
    panel.classList.remove('open');
    document.body.style.overflow = '';
  }
}

/**
 * 設定パネルを開く
 */
function openSettingsPanel() {
  const panel = document.getElementById('settingsPanel');
  if (panel) {
    panel.classList.add('open');
    document.body.style.overflow = 'hidden';
    loadUserSettings();
  }
}

/**
 * 設定パネルを閉じる
 */
function closeSettingsPanel() {
  const panel = document.getElementById('settingsPanel');
  if (panel) {
    panel.classList.remove('open');
    document.body.style.overflow = '';
  }
}

/**
 * 汎用モーダルを表示
 * @param {string} modalId - モーダル要素の ID
 */
function showModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }
}

/**
 * 汎用モーダルを非表示
 * @param {string} modalId - モーダル要素の ID
 */
function hideModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

// ============================================================
// ローディング・トースト
// ============================================================

/**
 * ローディングインジケーターを表示
 */
function showLoading() {
  const loading = document.getElementById('loadingIndicator');
  if (loading) loading.style.display = 'flex';
}

/**
 * ローディングインジケーターを非表示
 */
function hideLoading() {
  const loading = document.getElementById('loadingIndicator');
  if (loading) loading.style.display = 'none';
}

/**
 * トースト通知を表示（notificationManager へ委譲、またはフォールバック）
 * @param {string} message - メッセージ
 * @param {string} [type='info'] - トーストタイプ
 */
function showToast(message, type = 'info') {
  if (typeof notificationManager !== 'undefined' && notificationManager.showToast) {
    notificationManager.showToast(message, type);
    return;
  }
  if (typeof showNotification === 'function') {
    showNotification(message, type);
  }
}

// ============================================================
// 空状態表示
// ============================================================

/**
 * 空データ状態を表示するヘルパー関数
 * @param {HTMLElement} container - 表示先コンテナ
 * @param {string} dataType - データ種類
 * @param {string} [icon='📭'] - アイコン
 */
function showEmptyState(container, dataType, icon = '📭') {
  if (!container) return;

  container.textContent = '';

  const emptyState = document.createElement('div');
  emptyState.className = 'empty-state';
  emptyState.style.cssText = `
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    text-align: center;
    color: #64748b;
    background: #f8fafc;
    border-radius: 8px;
    border: 1px dashed #cbd5e1;
  `;

  const iconEl = document.createElement('div');
  iconEl.className = 'empty-state-icon';
  iconEl.style.cssText = 'font-size: 48px; margin-bottom: 16px; opacity: 0.6;';
  iconEl.textContent = icon;
  emptyState.appendChild(iconEl);

  const messageEl = document.createElement('div');
  messageEl.className = 'empty-state-message';
  messageEl.style.cssText = 'font-size: 16px; font-weight: 500; margin-bottom: 8px;';
  messageEl.textContent = `${dataType}データなし`;
  emptyState.appendChild(messageEl);

  const IS_PRODUCTION = window.IS_PRODUCTION || false;
  if (IS_PRODUCTION) {
    const hintEl = document.createElement('div');
    hintEl.className = 'empty-state-hint';
    hintEl.style.cssText = 'font-size: 14px; color: #94a3b8;';
    hintEl.textContent = 'データが登録されていません。';
    emptyState.appendChild(hintEl);
  }

  container.appendChild(emptyState);
}

/**
 * データチェックし、なければ空状態を表示
 * @param {Array} data - データ配列
 * @param {HTMLElement} container - コンテナ
 * @param {string} dataType - データ種類
 * @returns {boolean} データがある場合は true
 */
function checkAndShowEmptyState(data, container, dataType) {
  if (!data || data.length === 0) {
    const IS_PRODUCTION = window.IS_PRODUCTION || false;
    if (IS_PRODUCTION) {
      showEmptyState(container, dataType);
      return false;
    }
    return true;
  }
  return true;
}

// ============================================================
// ダッシュボード統計更新
// ============================================================

/**
 * ダッシュボード統計情報を更新
 * @param {Object} stats - 統計データ
 */
function updateDashboardStats(stats) {
  const lastSyncTime = document.getElementById('lastSyncTime');
  const activeWorkers = document.getElementById('activeWorkers');
  const totalWorkers = document.getElementById('totalWorkers');
  const pendingApprovals = document.getElementById('pendingApprovals');

  const formatTime = window.formatTime || ((d) => d || '--:--');

  if (lastSyncTime && stats.last_sync_time) {
    lastSyncTime.textContent = formatTime(stats.last_sync_time);
  }
  if (activeWorkers && stats.active_workers !== undefined) {
    activeWorkers.textContent = stats.active_workers;
  }
  if (totalWorkers && stats.total_workers !== undefined) {
    totalWorkers.textContent = stats.total_workers;
  }
  if (pendingApprovals && stats.pending_approvals !== undefined) {
    pendingApprovals.textContent = stats.pending_approvals;
  }

  const metricCards = document.querySelectorAll('.metric-card');
  if (metricCards.length >= 4 && stats) {
    if (stats.knowledge_reuse_rate !== undefined) {
      metricCards[0].querySelector('strong').textContent = `${stats.knowledge_reuse_rate}%`;
    }
    if (stats.accident_free_days !== undefined) {
      metricCards[1].querySelector('strong').textContent = `${stats.accident_free_days}日`;
    }
    if (stats.active_audits !== undefined) {
      metricCards[2].querySelector('strong').textContent = `${stats.active_audits}現場`;
    }
    if (stats.delayed_corrections !== undefined) {
      metricCards[3].querySelector('strong').textContent = `${stats.delayed_corrections}件`;
    }
  }
}

// ============================================================
// 通知表示
// ============================================================

/**
 * 通知一覧を表示
 * @param {Array} notifications - 通知配列
 */
function displayNotifications(notifications) {
  const listContainer = document.getElementById('notificationList');
  if (!listContainer) return;

  listContainer.textContent = '';

  if (!notifications || notifications.length === 0) {
    const emptyMsg = document.createElement('div');
    emptyMsg.className = 'empty-message';
    emptyMsg.textContent = '通知はありません';
    listContainer.appendChild(emptyMsg);
    return;
  }

  const formatTime = window.formatTime || ((d) => d || '');

  notifications.forEach(notif => {
    const item = document.createElement('div');
    item.className = `notification-item ${notif.read ? 'read' : 'unread'}`;

    const header = document.createElement('div');
    header.className = 'notification-header';

    const title = document.createElement('strong');
    title.textContent = notif.title || '通知';

    const time = document.createElement('span');
    time.className = 'notification-time';
    time.textContent = formatTime(notif.created_at);

    header.appendChild(title);
    header.appendChild(time);

    const message = document.createElement('div');
    message.className = 'notification-message';
    message.textContent = notif.message || '';

    const actions = document.createElement('div');
    actions.className = 'notification-actions';

    if (!notif.read) {
      const markReadBtn = document.createElement('button');
      markReadBtn.className = 'notification-btn';
      markReadBtn.textContent = '既読にする';
      markReadBtn.onclick = () => {
        if (typeof markNotificationAsRead === 'function') {
          markNotificationAsRead(notif.id);
        }
      };
      actions.appendChild(markReadBtn);
    }

    item.appendChild(header);
    item.appendChild(message);
    item.appendChild(actions);

    listContainer.appendChild(item);
  });
}

// ============================================================
// ユーザー設定読み込み
// ============================================================

/**
 * ユーザー設定を読み込んでフォームに反映
 */
function loadUserSettings() {
  const user = typeof getCurrentUser === 'function' ? getCurrentUser() : null;
  if (!user) return;

  const fullNameInput = document.getElementById('userFullName');
  const departmentInput = document.getElementById('userDepartment');
  const emailInput = document.getElementById('userEmail');

  if (fullNameInput) fullNameInput.value = user.full_name || '';
  if (departmentInput) departmentInput.value = user.department || '';
  if (emailInput) emailInput.value = user.email || '';

  const notifyApproval = document.getElementById('notifyApproval');
  const notifyKnowledge = document.getElementById('notifyKnowledge');
  const notifyIncident = document.getElementById('notifyIncident');
  const notifyEmail = document.getElementById('notifyEmail');

  if (notifyApproval) notifyApproval.checked = localStorage.getItem('notify_approval') !== 'false';
  if (notifyKnowledge) notifyKnowledge.checked = localStorage.getItem('notify_knowledge') !== 'false';
  if (notifyIncident) notifyIncident.checked = localStorage.getItem('notify_incident') !== 'false';
  if (notifyEmail) notifyEmail.checked = localStorage.getItem('notify_email') === 'true';

  const itemsPerPage = document.getElementById('itemsPerPage');
  const enableAnimations = document.getElementById('enableAnimations');
  const compactMode = document.getElementById('compactMode');

  if (itemsPerPage) itemsPerPage.value = localStorage.getItem('items_per_page') || '20';
  if (enableAnimations) enableAnimations.checked = localStorage.getItem('enable_animations') !== 'false';
  if (compactMode) compactMode.checked = localStorage.getItem('compact_mode') === 'true';

  if (typeof loadMFAStatus === 'function') {
    loadMFAStatus();
  }
}

// ============================================================
// 承認・却下
// ============================================================

/**
 * 選択されたアイテムを承認（quality_assurance 以上）
 */
async function approveSelected() {
  const log = window.logger || console;

  if (typeof checkPermission === 'function' && !checkPermission('quality_assurance')) {
    if (typeof showNotification === 'function') {
      showNotification('承認権限がありません。', 'error');
    }
    return;
  }

  try {
    const approvalsData = await fetchAPI('/approvals');
    const pendingApproval = approvalsData.data?.find(a => a.status === 'pending');

    if (!pendingApproval) {
      if (typeof showNotification === 'function') {
        showNotification('承認待ちのアイテムがありません。', 'info');
      }
      return;
    }

    const result = await fetchAPI(`/approvals/${pendingApproval.id}/approve`, { method: 'POST' });

    if (result.success) {
      if (typeof showNotification === 'function') {
        showNotification('承認処理を実行しました。', 'success');
      }
      log.log('[APPROVAL] Approved item:', pendingApproval.id);
      if (typeof loadApprovals === 'function') loadApprovals();
    }
  } catch (error) {
    log.error('[APPROVAL] Failed to approve:', error);
    if (typeof showNotification === 'function') {
      showNotification('承認処理に失敗しました。', 'error');
    }
  }
}

/**
 * 選択されたアイテムを却下（quality_assurance 以上）
 */
async function rejectSelected() {
  const log = window.logger || console;

  if (typeof checkPermission === 'function' && !checkPermission('quality_assurance')) {
    if (typeof showNotification === 'function') {
      showNotification('却下権限がありません。', 'error');
    }
    return;
  }

  const reason = prompt('却下理由を入力してください:');
  if (!reason) return;

  try {
    const approvalsData = await fetchAPI('/approvals');
    const pendingApproval = approvalsData.data?.find(a => a.status === 'pending');

    if (!pendingApproval) {
      if (typeof showNotification === 'function') {
        showNotification('承認待ちのアイテムがありません。', 'info');
      }
      return;
    }

    const result = await fetchAPI(`/approvals/${pendingApproval.id}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason })
    });

    if (result.success) {
      if (typeof showNotification === 'function') {
        showNotification('却下処理を実行しました。', 'success');
      }
      log.log('[APPROVAL] Rejected item:', pendingApproval.id, 'Reason:', reason);
      if (typeof loadApprovals === 'function') loadApprovals();
    }
  } catch (error) {
    log.error('[APPROVAL] Failed to reject:', error);
    if (typeof showNotification === 'function') {
      showNotification('却下処理に失敗しました。', 'error');
    }
  }
}

// ============================================================
// Chart.js グラフ初期化
// ============================================================

let _dashboardCharts = {};

/**
 * ダッシュボードグラフを初期化
 */
function initDashboardCharts() {
  const log = window.logger || console;

  if (typeof Chart === 'undefined') {
    log.warn('Chart.js is not loaded');
    return;
  }

  Chart.defaults.font.family = '"Zen Kaku Gothic New", sans-serif';

  // 日別出来高チャート
  const dailyProgressCanvas = document.getElementById('dailyProgressChart');
  if (dailyProgressCanvas) {
    _dashboardCharts.dailyProgress = new Chart(dailyProgressCanvas, {
      type: 'line',
      data: {
        labels: ['月', '火', '水', '木', '金', '土', '日'],
        datasets: [{
          label: '日別出来高',
          data: [40, 52, 33, 78, 46, 62, 85],
          borderColor: '#d4662f',
          backgroundColor: 'rgba(212, 102, 47, 0.2)',
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointHoverRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(27, 38, 37, 0.9)',
            padding: 12,
            titleColor: '#fff',
            bodyColor: '#fff',
            borderColor: '#d4662f',
            borderWidth: 1,
            callbacks: {
              label: function(context) { return context.parsed.y + '%'; }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: { callback: (v) => v + '%', color: '#4b5b58' },
            grid: { color: 'rgba(216, 210, 200, 0.5)' }
          },
          x: { ticks: { color: '#4b5b58' }, grid: { display: false } }
        }
      }
    });
  }

  // リスクトレンドチャート
  const riskTrendCanvas = document.getElementById('riskTrendChart');
  if (riskTrendCanvas) {
    _dashboardCharts.riskTrend = new Chart(riskTrendCanvas, {
      type: 'bar',
      data: {
        labels: ['1週前', '6日前', '5日前', '4日前', '3日前', '2日前', '昨日', '今日'],
        datasets: [
          { label: '品質リスク', data: [3, 2, 4, 3, 2, 3, 4, 3], backgroundColor: 'rgba(224, 139, 62, 0.7)', borderColor: '#e08b3e', borderWidth: 1 },
          { label: '原価リスク', data: [2, 3, 2, 2, 3, 2, 3, 4], backgroundColor: 'rgba(197, 83, 58, 0.7)', borderColor: '#c5533a', borderWidth: 1 },
          { label: '安全リスク', data: [1, 1, 0, 1, 1, 2, 1, 2], backgroundColor: 'rgba(47, 75, 82, 0.7)', borderColor: '#2f4b52', borderWidth: 1 }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: true, position: 'top', labels: { boxWidth: 12, boxHeight: 12, padding: 10, font: { size: 11 }, color: '#4b5b58' } },
          tooltip: { backgroundColor: 'rgba(27, 38, 37, 0.9)', padding: 12, titleColor: '#fff', bodyColor: '#fff', borderColor: '#d4662f', borderWidth: 1 }
        },
        scales: {
          x: { stacked: true, ticks: { font: { size: 10 }, color: '#4b5b58' }, grid: { display: false } },
          y: { stacked: true, beginAtZero: true, ticks: { stepSize: 1, color: '#4b5b58' }, grid: { color: 'rgba(216, 210, 200, 0.5)' } }
        }
      }
    });
  }
}

/**
 * グラフデータを更新
 * @param {string} chartName - グラフ名
 * @param {Object} newData - 新規データ
 */
function updateChartData(chartName, newData) {
  const chart = _dashboardCharts[chartName];
  if (!chart) return;

  if (newData.labels) chart.data.labels = newData.labels;
  if (newData.datasets) {
    chart.data.datasets.forEach((dataset, i) => {
      if (newData.datasets[i]) dataset.data = newData.datasets[i].data;
    });
  }
  chart.update();
}

// ============================================================
// その他アクション
// ============================================================

/**
 * 承認箱へ移動
 */
function openApprovalBox() {
  window.location.href = '#approvals';
  if (typeof showNotification === 'function') {
    showNotification('承認箱へスクロールしました', 'info');
  }
}

/**
 * 朝礼用サマリ生成（将来実装）
 */
function generateMorningSummary() {
  if (typeof showNotification === 'function') {
    showNotification('朝礼用サマリを生成しています...', 'info');
  }
}

// ============================================================
// グローバル公開
// ============================================================

window.openNewKnowledgeModal = openNewKnowledgeModal;
window.closeNewKnowledgeModal = closeNewKnowledgeModal;
window.openNewConsultModal = openNewConsultModal;
window.closeNewConsultModalFallback = closeNewConsultModalFallback;
window.openSearchModal = openSearchModal;
window.closeSearchModal = closeSearchModal;
window.openNotificationPanel = openNotificationPanel;
window.closeNotificationPanel = closeNotificationPanel;
window.openSettingsPanel = openSettingsPanel;
window.closeSettingsPanel = closeSettingsPanel;
window.showModal = showModal;
window.hideModal = hideModal;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.showToast = showToast;
window.showEmptyState = showEmptyState;
window.checkAndShowEmptyState = checkAndShowEmptyState;
window.updateDashboardStats = updateDashboardStats;
window.displayNotifications = displayNotifications;
window.loadUserSettings = loadUserSettings;
window.approveSelected = approveSelected;
window.rejectSelected = rejectSelected;
window.initDashboardCharts = initDashboardCharts;
window.updateChartData = updateChartData;
window.openApprovalBox = openApprovalBox;
window.generateMorningSummary = generateMorningSummary;

export {
  openNewKnowledgeModal,
  closeNewKnowledgeModal,
  openNewConsultModal,
  closeNewConsultModalFallback,
  openSearchModal,
  closeSearchModal,
  openNotificationPanel,
  closeNotificationPanel,
  openSettingsPanel,
  closeSettingsPanel,
  showModal,
  hideModal,
  showLoading,
  hideLoading,
  showToast,
  showEmptyState,
  checkAndShowEmptyState,
  updateDashboardStats,
  displayNotifications,
  loadUserSettings,
  approveSelected,
  rejectSelected,
  initDashboardCharts,
  updateChartData,
  openApprovalBox,
  generateMorningSummary
};
