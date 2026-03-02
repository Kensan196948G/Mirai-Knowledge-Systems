/**
 * @fileoverview ルーティングモジュール v2.0.0
 * @module app/router
 * @description Phase F-4: app.js 分割版 - ルーティング・ナビゲーション処理
 *
 * 担当機能:
 * - 詳細ページへの遷移 (viewKnowledgeDetail / viewSOPDetail / viewIncidentDetail / viewConsultationDetail)
 * - サイドバー・セクション折りたたみ制御 (toggleSidebar / toggleSection)
 * - プロジェクト詳細表示トグル (toggleProjectDetail)
 */

// ============================================================
// ページ遷移（ナビゲーション）
// ============================================================

/**
 * ナレッジ詳細ページへ遷移
 * @param {number|string} knowledgeId - ナレッジ ID
 */
function viewKnowledgeDetail(knowledgeId) {
  const log = window.logger || console;
  log.log('[NAVIGATION] Viewing knowledge detail:', knowledgeId);
  window.location.href = `search-detail.html?id=${knowledgeId}`;
}

/**
 * SOP 詳細ページへ遷移
 * @param {number|string} sopId - SOP ID
 */
function viewSOPDetail(sopId) {
  const log = window.logger || console;
  log.log('[NAVIGATION] Viewing SOP detail:', sopId);
  window.location.href = `sop-detail.html?id=${sopId}`;
}

/**
 * 事故レポート詳細ページへ遷移
 * @param {number|string} incidentId - 事故レポート ID
 */
function viewIncidentDetail(incidentId) {
  const log = window.logger || console;
  log.log('[NAVIGATION] Viewing incident detail:', incidentId);
  window.location.href = `incident-detail.html?id=${incidentId}`;
}

/**
 * 専門家相談詳細ページへ遷移
 * @param {number|string} consultId - 相談 ID
 */
function viewConsultationDetail(consultId) {
  const log = window.logger || console;
  log.log('[NAVIGATION] Viewing consultation detail:', consultId);
  window.location.href = `expert-consult.html?id=${consultId}`;
}

// ============================================================
// セクション・サイドバー制御
// ============================================================

/**
 * サイドバーの折りたたみ切替（モバイル用）
 */
function toggleSidebar() {
  const sidebar = document.querySelector('.sidebar');
  if (sidebar) {
    sidebar.classList.toggle('collapsed');
  }
}

/**
 * ナビゲーションセクションの折りたたみ切替
 * @param {HTMLElement} titleElement - クリックされたタイトル要素
 */
function toggleSection(titleElement) {
  const section = titleElement.closest('.nav-section');
  if (section) {
    section.classList.toggle('collapsed');
    const chevron = titleElement.querySelector('.chevron');
    if (chevron) {
      chevron.textContent = section.classList.contains('collapsed') ? '▶' : '▼';
    }
  }
}

/**
 * プロジェクト詳細の表示切替
 * @param {string} projectId - プロジェクト ID
 */
function toggleProjectDetail(projectId) {
  const details = document.getElementById(`details-${projectId}`);
  const chevron = document.getElementById(`chevron-${projectId}`);

  if (details && chevron) {
    const isVisible = details.style.display === 'block';
    details.style.display = isVisible ? 'none' : 'block';
    chevron.textContent = isVisible ? '▼' : '▲';
  }
}

// ============================================================
// URLパラメータ処理
// ============================================================

/**
 * 現在の URL から指定パラメータを取得
 * @param {string} name - パラメータ名
 * @returns {string|null}
 */
function getUrlParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}

/**
 * 指定セクションへスクロール
 * @param {string} sectionId - セクション ID
 */
function navigateTo(sectionId) {
  const el = document.getElementById(sectionId);
  if (el) {
    el.scrollIntoView({ behavior: 'smooth' });
  }
}

/**
 * タブパネル切替
 * @param {string} tabName - タブ名
 */
function showSection(tabName) {
  const tabs = document.querySelectorAll('.tab-btn');
  const panels = document.querySelectorAll('.tab-panel');

  tabs.forEach((btn) => {
    const isActive = btn.dataset.tab === tabName;
    btn.classList.toggle('is-active', isActive);
    btn.setAttribute('aria-selected', String(isActive));
  });

  panels.forEach((panel) => {
    const isActive = panel.dataset.panel === tabName;
    panel.classList.toggle('is-active', isActive);
  });
}

// ============================================================
// SocketIO プロジェクトルーム参加/退出
// ============================================================

/**
 * プロジェクトルームへ参加
 * @param {string} projectId - プロジェクト ID
 */
function joinProjectRoom(projectId) {
  const sock = window._appSocket;
  if (sock && sock.connected) {
    sock.emit('join_project', { project_id: projectId });
  }
}

/**
 * プロジェクトルームから退出
 * @param {string} projectId - プロジェクト ID
 */
function leaveProjectRoom(projectId) {
  const sock = window._appSocket;
  if (sock && sock.connected) {
    sock.emit('leave_project', { project_id: projectId });
  }
}

// ============================================================
// グローバル公開
// ============================================================

window.viewKnowledgeDetail = viewKnowledgeDetail;
window.viewSOPDetail = viewSOPDetail;
window.viewIncidentDetail = viewIncidentDetail;
window.viewConsultationDetail = viewConsultationDetail;
window.toggleSidebar = toggleSidebar;
window.toggleSection = toggleSection;
window.toggleProjectDetail = toggleProjectDetail;
window.getUrlParam = getUrlParam;
window.navigateTo = navigateTo;
window.showSection = showSection;
window.joinProjectRoom = joinProjectRoom;
window.leaveProjectRoom = leaveProjectRoom;

export {
  viewKnowledgeDetail,
  viewSOPDetail,
  viewIncidentDetail,
  viewConsultationDetail,
  toggleSidebar,
  toggleSection,
  toggleProjectDetail,
  getUrlParam,
  navigateTo,
  showSection,
  joinProjectRoom,
  leaveProjectRoom
};
