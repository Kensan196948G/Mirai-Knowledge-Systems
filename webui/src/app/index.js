/**
 * @fileoverview アプリケーションエントリーポイント v2.0.0
 * @module app/index
 * @description Phase F-4: app.js 分割版エントリーポイント
 *
 * 読み込み順序:
 *   1. init.js       - 初期化処理
 *   2. router.js     - ルーティング
 *   3. event-handlers.js - イベントハンドラー
 *   4. ui-controller.js  - UI制御
 *   5. data-loader.js    - データ読み込み
 *   6. notifications-handler.js - 通知処理
 *   7. actions-handler.js       - アクション処理
 *   8. legacy-compat.js  - 後方互換性
 */

import { initializeApp, checkAuthState } from './init.js';
import { navigateTo, showSection } from './router.js';
import { setupSearch, setupEventListeners } from './event-handlers.js';
import {
  showModal, hideModal, showToast, showLoading, hideLoading,
  openNewKnowledgeModal, closeNewKnowledgeModal,
  openNotificationPanel, closeNotificationPanel,
  openSettingsPanel, closeSettingsPanel,
  openSearchModal, closeSearchModal,
  updateDashboardStats, displayNotifications, loadUserSettings,
  approveSelected, rejectSelected, initDashboardCharts
} from './ui-controller.js';
import {
  loadKnowledge, loadSOPs, loadIncidents, loadApprovals,
  loadDashboardStats, loadMonitoringData,
  loadPopularKnowledge, loadRecentKnowledge, loadFavoriteKnowledge,
  loadTagCloud, loadProjects, loadExperts, loadExpertStats
} from './data-loader.js';
import {
  loadNotifications, markNotificationAsRead, getNotifications, markAsRead
} from './notifications-handler.js';
import {
  editKnowledge, toggleLike, toggleBookmark, toggleFavorite, performAction
} from './actions-handler.js';
import legacyApp from './legacy-compat.js';

// ============================================================
// 集約エクスポート
// ============================================================

export {
  // 初期化
  initializeApp,
  checkAuthState,
  // ルーティング
  navigateTo,
  showSection,
  // UI制御
  showModal,
  hideModal,
  showToast,
  showLoading,
  hideLoading,
  openNewKnowledgeModal,
  closeNewKnowledgeModal,
  openNotificationPanel,
  closeNotificationPanel,
  openSettingsPanel,
  closeSettingsPanel,
  openSearchModal,
  closeSearchModal,
  updateDashboardStats,
  displayNotifications,
  loadUserSettings,
  approveSelected,
  rejectSelected,
  initDashboardCharts,
  // データ読み込み
  loadKnowledge,
  loadSOPs,
  loadIncidents,
  loadApprovals,
  loadDashboardStats,
  loadMonitoringData,
  loadPopularKnowledge,
  loadRecentKnowledge,
  loadFavoriteKnowledge,
  loadTagCloud,
  loadProjects,
  loadExperts,
  loadExpertStats,
  // 通知
  loadNotifications,
  markNotificationAsRead,
  getNotifications,
  markAsRead,
  // アクション
  editKnowledge,
  toggleLike,
  toggleBookmark,
  toggleFavorite,
  performAction,
  // イベント設定
  setupSearch,
  setupEventListeners,
  // 後方互換性
  legacyApp
};

// ============================================================
// DOMContentLoaded 後のアプリ初期化
// ============================================================

if (typeof document !== 'undefined') {
  document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
  });
}
