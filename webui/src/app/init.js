/**
 * @fileoverview アプリケーション初期化モジュール v2.0.0
 * @module app/init
 * @description Phase F-4: app.js 分割版 - 初期化処理
 *
 * 担当機能:
 * - DOMContentLoaded 後のアプリ初期化シーケンス
 * - モジュール初期化（stateManager, authManager）
 * - ダミーデータ読み込み (loadDummyDataToStorage)
 * - 定期更新 (startPeriodicUpdates)
 * - SocketIO 初期化 (initSocketIO)
 */

// ============================================================
// 依存モジュール参照（グローバルインスタンスを使用）
// ============================================================

// stateManager, authManager, fetchAPI は既存モジュールで window に公開済み
// IS_PRODUCTION, ENV_NAME は app.js のグローバルを使用

// ============================================================
// ダミーデータ読み込み
// ============================================================

/**
 * バックエンドの生成済みダミーデータを localStorage に保存
 */
async function loadDummyDataToStorage() {
  const log = window.logger || console;
  log.log('[DATA] Loading dummy data to localStorage...');

  const dataFiles = [
    { key: 'knowledge_details', file: '/data/knowledge_details.json' },
    { key: 'sop_details', file: '/data/sop_details.json' },
    { key: 'incidents_details', file: '/data/incidents_details.json' },
    { key: 'consultations_details', file: '/data/consultations_details.json' },
    { key: 'projects', file: '/data/projects.json' },
    { key: 'experts', file: '/data/experts.json' }
  ];

  for (const { key, file } of dataFiles) {
    try {
      const response = await fetch(file);
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem(key, JSON.stringify(data));
        log.log(`[DATA] Loaded ${key}: ${data.length} items`);
      } else {
        log.error(`[DATA] Failed to load ${file}: ${response.status}`);
      }
    } catch (error) {
      log.error(`[DATA] Error loading ${file}:`, error);
    }
  }

  log.log('[DATA] All dummy data loaded to localStorage!');
}

// ============================================================
// 定期更新
// ============================================================

/**
 * ダッシュボードと通知の定期更新を開始（5分間隔）
 */
function startPeriodicUpdates() {
  const log = window.logger || console;

  setInterval(() => {
    if (!document.hidden) {
      if (typeof loadDashboardStats === 'function') loadDashboardStats();
      if (typeof loadNotifications === 'function') loadNotifications();
    }
  }, 5 * 60 * 1000);

  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
      if (typeof loadDashboardStats === 'function') loadDashboardStats();
      if (typeof loadNotifications === 'function') loadNotifications();
    }
  });

  log.log('[INIT] Periodic updates started (5min interval)');
}

// ============================================================
// SocketIO リアルタイム更新
// ============================================================

let _socket;

/**
 * SocketIO の初期化と各種イベントリスナー設定
 */
function initSocketIO() {
  const log = window.logger || console;

  if (typeof io === 'undefined') {
    log.warn('[SOCKET] Socket.IO library not loaded');
    return;
  }

  _socket = io(window.location.origin, {
    transports: ['websocket', 'polling'],
    auth: {
      token: localStorage.getItem('access_token')
    }
  });

  _socket.on('connect', () => {
    log.log('[SOCKET] Connected to server');
    if (typeof showNotification === 'function') {
      showNotification('リアルタイム接続が確立されました', 'success');
    }
    _socket.emit('join_dashboard');
  });

  _socket.on('disconnect', () => {
    log.log('[SOCKET] Disconnected from server');
    if (typeof showNotification === 'function') {
      showNotification('リアルタイム接続が切断されました', 'warning');
    }
  });

  _socket.on('connected', (data) => {
    log.log('[SOCKET] Server confirmed connection:', data);
  });

  _socket.on('dashboard_stats_update', (data) => {
    log.log('[SOCKET] Dashboard stats update:', data);
    if (typeof updateDashboardStats === 'function') {
      updateDashboardStats(data.stats);
    }
    if (typeof showNotification === 'function') {
      showNotification('ダッシュボードが更新されました', 'info');
    }
  });

  _socket.on('project_progress_update', (data) => {
    log.log('[SOCKET] Project progress update:', data);
    if (typeof updateProjectProgress === 'function') {
      updateProjectProgress(data.project_id, data.progress);
    }
    if (typeof showNotification === 'function') {
      showNotification(`プロジェクト ${data.project_id} の進捗が更新されました`, 'info');
    }
  });

  _socket.on('expert_stats_update', (data) => {
    log.log('[SOCKET] Expert stats update:', data);
    if (typeof updateExpertStats === 'function') {
      updateExpertStats(data.expert_stats);
    }
    if (typeof showNotification === 'function') {
      showNotification('専門家統計が更新されました', 'info');
    }
  });

  _socket.on('connect_error', (error) => {
    log.error('[SOCKET] Connection error:', error);
    if (typeof showNotification === 'function') {
      showNotification('リアルタイム接続に失敗しました', 'error');
    }
  });
}

// ============================================================
// アプリケーション初期化メイン処理
// ============================================================

/**
 * アプリケーション初期化
 * DOMContentLoaded 後に呼び出す
 */
async function initializeApp() {
  const log = window.logger || console;
  log.log('建設土木ナレッジシステム - 初期化中...');

  // --------------------------------------------------------
  // Phase E-1: モジュール初期化
  // --------------------------------------------------------

  // 状態管理初期化
  if (typeof stateManager !== 'undefined') {
    stateManager.restoreState();
    log.log('[E-1] State Manager initialized');

    const IS_PRODUCTION = window.IS_PRODUCTION || false;
    const ENV_NAME = IS_PRODUCTION ? '本番' : '開発';
    stateManager.setConfig('isProduction', IS_PRODUCTION);
    stateManager.setConfig('envName', ENV_NAME);
  }

  // 認証チェック
  if (typeof authManager !== 'undefined') {
    if (!authManager.checkAuth()) {
      return; // 認証失敗時は処理を中断
    }

    // ユーザー情報を localStorage から復元
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        if (typeof stateManager !== 'undefined') {
          stateManager.setCurrentUser(user);
        }
        log.log('[E-1] User state restored from localStorage');
      } catch (e) {
        log.error('[E-1] Failed to parse user data:', e);
      }
    }

    // トークンリフレッシュ開始
    if (authManager.isAuthenticated()) {
      authManager.startTokenRefresh();
      log.log('[E-1] Token refresh started');
    }
  }

  // --------------------------------------------------------
  // 既存初期化処理
  // --------------------------------------------------------

  // ダミーデータを localStorage に保存
  await loadDummyDataToStorage();

  // ユーザー情報表示
  if (typeof authManager !== 'undefined') {
    authManager.displayUserInfo();
    authManager.applyRBACUI();
  }

  // 検索機能のセットアップ
  if (typeof setupSearch === 'function') setupSearch();

  // イベントリスナーの設定
  if (typeof setupEventListeners === 'function') setupEventListeners();

  // サイドパネルタブの設定
  if (typeof setupSidePanelTabs === 'function') setupSidePanelTabs();

  // 初期データのロード
  if (typeof loadDashboardStats === 'function') loadDashboardStats();
  if (typeof loadMonitoringData === 'function') loadMonitoringData();
  if (typeof loadExpertStats === 'function') loadExpertStats();

  // KNOWLEDGE HUB とサイドバーのデータロード
  if (typeof loadPopularKnowledge === 'function') loadPopularKnowledge();
  if (typeof loadRecentKnowledge === 'function') loadRecentKnowledge();
  if (typeof loadFavoriteKnowledge === 'function') loadFavoriteKnowledge();
  if (typeof loadTagCloud === 'function') loadTagCloud();
  if (typeof loadProjects === 'function') loadProjects();
  if (typeof loadExperts === 'function') loadExperts();

  // メインコンテンツのロード
  if (typeof loadKnowledge === 'function') loadKnowledge();
  if (typeof loadSOPs === 'function') loadSOPs();
  if (typeof loadIncidents === 'function') loadIncidents();
  if (typeof loadApprovals === 'function') loadApprovals();
  if (typeof loadNotifications === 'function') loadNotifications();

  // Chart.js グラフの初期化
  if (typeof Chart !== 'undefined' && typeof initDashboardCharts === 'function') {
    initDashboardCharts();
  }

  // メインコンテンツのカードにクリックイベントを追加
  if (typeof setupCardClickHandlers === 'function') setupCardClickHandlers();

  // 定期更新を開始
  startPeriodicUpdates();

  log.log('初期化完了!');

  // SocketIO の初期化
  initSocketIO();
}

/**
 * 認証状態チェック（後方互換性）
 */
function checkAuthState() {
  if (typeof authManager !== 'undefined') {
    return authManager.checkAuth();
  }
  const token = localStorage.getItem('access_token');
  if (!token) {
    window.location.href = '/login.html';
    return false;
  }
  return true;
}

// ============================================================
// グローバル公開
// ============================================================

window.initializeApp = initializeApp;
window.checkAuthState = checkAuthState;
window.loadDummyDataToStorage = loadDummyDataToStorage;
window.startPeriodicUpdates = startPeriodicUpdates;
window.initSocketIO = initSocketIO;

export { initializeApp, checkAuthState, loadDummyDataToStorage, startPeriodicUpdates, initSocketIO };
