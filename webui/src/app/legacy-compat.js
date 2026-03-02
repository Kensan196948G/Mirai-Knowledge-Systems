/**
 * @fileoverview 後方互換性レイヤー v2.0.0
 * @module app/legacy-compat
 * @description Phase F-4: 既存 HTML ファイルからのグローバル関数呼び出しを維持するため
 *              全モジュールの主要関数を window オブジェクトに登録します。
 *
 * 読み込み順序: このファイルは他のすべてのモジュールの後に読み込むこと
 */

// ============================================================
// 後方互換性 window.App 名前空間
// ============================================================

/**
 * window.App として公開されるアプリケーション API
 * 既存 HTML の onclick 属性や外部スクリプトからの呼び出しに対応
 */
if (typeof window !== 'undefined') {
  window.App = {
    // 初期化
    init: function() {
      if (typeof initializeApp === 'function') return initializeApp();
    },
    checkAuth: function() {
      if (typeof checkAuthState === 'function') return checkAuthState();
    },

    // ルーティング
    navigateTo: function(id) {
      if (typeof navigateTo === 'function') return navigateTo(id);
    },
    showSection: function(tab) {
      if (typeof showSection === 'function') return showSection(tab);
    },
    viewKnowledgeDetail: function(id) {
      if (typeof viewKnowledgeDetail === 'function') return viewKnowledgeDetail(id);
    },
    viewSOPDetail: function(id) {
      if (typeof viewSOPDetail === 'function') return viewSOPDetail(id);
    },
    viewIncidentDetail: function(id) {
      if (typeof viewIncidentDetail === 'function') return viewIncidentDetail(id);
    },
    viewConsultationDetail: function(id) {
      if (typeof viewConsultationDetail === 'function') return viewConsultationDetail(id);
    },

    // UI 制御
    showModal: function(id) {
      if (typeof showModal === 'function') return showModal(id);
    },
    hideModal: function(id) {
      if (typeof hideModal === 'function') return hideModal(id);
    },
    showToast: function(msg, type) {
      if (typeof showToast === 'function') return showToast(msg, type);
    },
    showLoading: function() {
      if (typeof showLoading === 'function') return showLoading();
    },
    hideLoading: function() {
      if (typeof hideLoading === 'function') return hideLoading();
    },

    // データ読み込み
    loadKnowledgeData: function(params) {
      if (typeof loadKnowledge === 'function') return loadKnowledge(params);
    },
    loadDashboardData: function() {
      if (typeof loadDashboardStats === 'function') return loadDashboardStats();
    },

    // 検索
    handleSearch: function(q) {
      if (typeof loadKnowledge === 'function') return loadKnowledge({ search: q });
    },
    performHeroSearch: function() {
      if (typeof performHeroSearch === 'function') return performHeroSearch();
    },

    // 通知
    getNotifications: function() {
      if (typeof loadNotifications === 'function') return loadNotifications();
    },
    markAsRead: function(id) {
      if (typeof markNotificationAsRead === 'function') return markNotificationAsRead(id);
    },

    // アクション
    performAction: function(action, payload) {
      if (typeof performAction === 'function') return performAction(action, payload);
    },
    toggleFavorite: function(id) {
      if (typeof toggleFavorite === 'function') return toggleFavorite(id);
    },
    toggleLike: function() {
      if (typeof toggleLike === 'function') return toggleLike();
    },
    toggleBookmark: function() {
      if (typeof toggleBookmark === 'function') return toggleBookmark();
    },

    // 承認
    approveSelected: function() {
      if (typeof approveSelected === 'function') return approveSelected();
    },
    rejectSelected: function() {
      if (typeof rejectSelected === 'function') return rejectSelected();
    },

    // フィルター
    filterByCategory: function(cat) {
      if (typeof filterKnowledgeByCategory === 'function') return filterKnowledgeByCategory(cat);
    },
    filterByTag: function(tag) {
      if (typeof filterByTag === 'function') return filterByTag(tag);
    }
  };
}

// ============================================================
// グローバル関数の明示的な再確認（フォールバック登録）
// ============================================================

// 各モジュールが個別に window に登録しているが、
// このファイルを読み込むことで登録の順序に依存しない保証を提供する

const _legacyExports = [
  // init.js
  'initializeApp', 'checkAuthState', 'loadDummyDataToStorage', 'startPeriodicUpdates', 'initSocketIO',
  // router.js
  'viewKnowledgeDetail', 'viewSOPDetail', 'viewIncidentDetail', 'viewConsultationDetail',
  'toggleSidebar', 'toggleSection', 'toggleProjectDetail', 'navigateTo', 'showSection',
  // event-handlers.js
  'setupSearch', 'setupEventListeners', 'setupSidePanelTabs', 'setupCardClickHandlers',
  'performHeroSearch', 'resetSearchForm', 'displaySearchResults',
  'filterKnowledgeByCategory', 'filterProjectsByType', 'filterExpertsByField', 'filterByTag',
  'submitNewKnowledge', 'submitAdvancedSearch', 'submitUserSettings',
  'submitNotificationSettings', 'submitDisplaySettings',
  // ui-controller.js
  'openNewKnowledgeModal', 'closeNewKnowledgeModal',
  'openNewConsultModal', 'closeNewConsultModalFallback',
  'openSearchModal', 'closeSearchModal',
  'openNotificationPanel', 'closeNotificationPanel',
  'openSettingsPanel', 'closeSettingsPanel',
  'showModal', 'hideModal', 'showLoading', 'hideLoading', 'showToast',
  'showEmptyState', 'checkAndShowEmptyState',
  'updateDashboardStats', 'displayNotifications', 'loadUserSettings',
  'approveSelected', 'rejectSelected', 'initDashboardCharts', 'updateChartData',
  'openApprovalBox', 'generateMorningSummary',
  // data-loader.js
  'loadDashboardStats', 'loadMonitoringData',
  'loadKnowledge', 'loadSOPs', 'loadIncidents', 'loadApprovals',
  'displayKnowledge', 'displaySOPs', 'displayIncidents', 'displayApprovals',
  'updateNotificationBadge',
  'loadPopularKnowledge', 'loadRecentKnowledge', 'loadFavoriteKnowledge',
  'loadTagCloud', 'loadProjects', 'loadExperts',
  'loadProjectProgress', 'loadExpertStats', 'removeFavorite', 'consultExpert',
  // notifications-handler.js
  'loadNotifications', 'markNotificationAsRead', 'markAllNotificationsAsRead',
  'getNotifications', 'markAsRead',
  'loadMFAStatus', 'startMFASetup', 'verifyAndEnableMFA', 'disableMFA', 'closeMFASetupModal',
  // actions-handler.js
  'editKnowledge', 'toggleLike', 'toggleBookmark', 'toggleFavorite',
  'incrementViewCount', 'shareKnowledge', 'closeShareModal', 'copyShareUrl',
  'printPage', 'exportPDF', 'retryLoad', 'performAction', 'submitNewConsultationAPI',
  'updateProjectProgress', 'updateExpertStats', 'updateDutyExperts', 'calculateExpertRating'
];

// 登録状況をログ出力（開発環境のみ）
if (typeof window !== 'undefined' && !window.IS_PRODUCTION) {
  const missing = _legacyExports.filter(name => typeof window[name] === 'undefined');
  if (missing.length > 0) {
    const log = window.logger || console;
    log.warn('[LEGACY-COMPAT] Functions not yet registered on window:', missing);
  }
}

// ============================================================
// ESM export（モジュールとして使用する場合）
// ============================================================

export default window.App;
