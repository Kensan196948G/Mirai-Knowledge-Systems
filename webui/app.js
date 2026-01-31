// ============================================================
// 環境設定
// ============================================================

/**
 * 環境ポート番号定義（固定 - 変更不可）
 * 開発環境: HTTP 5100, HTTPS 5443
 * 本番環境: HTTP 8100, HTTPS 8443
 */
const ENV_PORTS = {
  development: { http: 5100, https: 5443 },
  production: { http: 8100, https: 8443 }
};

/**
 * 本番環境フラグ
 * true: 本番環境（ダミーデータを表示しない、APIからデータ取得）
 * false: 開発環境（ダミーデータを表示、開発用データ使用）
 *
 * 本番環境では以下の方法で切り替え（優先順位順）:
 * 1. URLパラメータ: ?env=production
 * 2. localStorage: localStorage.setItem('MKS_ENV', 'production')
 * 3. ポート番号: 8100/8443 = 本番、5100/5443 = 開発
 * 4. ホスト名: localhost/127.0.0.1 以外は本番モード
 */
const IS_PRODUCTION = (() => {
  // URLパラメータをチェック
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('env') === 'production') return true;
  if (urlParams.get('env') === 'development') return false;

  // localStorageをチェック
  const envSetting = localStorage.getItem('MKS_ENV');
  if (envSetting === 'production') return true;
  if (envSetting === 'development') return false;

  // ポート番号で判定（最も信頼性が高い）
  const port = parseInt(window.location.port || (window.location.protocol === 'https:' ? '443' : '80'));
  if (port === ENV_PORTS.production.http || port === ENV_PORTS.production.https) {
    return true;
  }
  if (port === ENV_PORTS.development.http || port === ENV_PORTS.development.https) {
    return false;
  }

  // ホスト名で判定（localhost以外は本番）
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return false;
  }

  // デフォルトは開発環境
  return false;
})();

/**
 * 現在の環境名を取得
 */
const ENV_NAME = IS_PRODUCTION ? '本番' : '開発';

/**
 * ブックマークタイトルの設定
 * 環境名をタイトルに含めて識別しやすくする
 */
const BASE_TITLE = 'Mirai Knowledge Systems';
document.title = `[${ENV_NAME}] ${BASE_TITLE}`;

// グローバルに環境情報を公開
window.MKS_ENV = {
  isProduction: IS_PRODUCTION,
  envName: ENV_NAME,
  ports: ENV_PORTS
};

// ============================================================
// セキュアロガー（本番環境ではログ出力を抑制）
// ============================================================

/**
 * 開発環境でのみログを出力するロガー
 * 本番環境では機密情報漏洩を防ぐためログを抑制
 */
const logger = {
  log: (...args) => { if (!IS_PRODUCTION) console.log(...args); },
  warn: (...args) => { if (!IS_PRODUCTION) console.warn(...args); },
  error: (...args) => { console.error(...args); }, // エラーは常に出力
  debug: (...args) => { if (!IS_PRODUCTION) console.debug(...args); },
  info: (...args) => { if (!IS_PRODUCTION) console.info(...args); }
};

// グローバルに公開（他のファイルからも使用可能）
window.logger = logger;

logger.log(`[ENV] 環境モード: ${ENV_NAME}`);
logger.log(`[ENV] ポート: ${window.location.port || 'default'}`);
logger.log(`[ENV] タイトル: ${document.title}`);

// ============================================================
// 認証管理
// ============================================================

// 認証チェック
function checkAuth() {
  const token = localStorage.getItem('access_token');
  logger.log('[AUTH] Checking authentication. Token exists:', token ? 'YES' : 'NO');
  if (!token) {
    logger.log('[AUTH] No token found. Redirecting to login...');
    window.location.href = '/login.html';
    return false;
  }
  logger.log('[AUTH] Token found. Length:', token.length);
  return true;
}

// ログアウト
function logout() {
  logger.log('[AUTH] Logging out...');
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  window.location.href = '/login.html';
}

// ユーザー情報取得
function getCurrentUser() {
  const userStr = localStorage.getItem('user');
  if (userStr) {
    try {
      return JSON.parse(userStr);
    } catch (e) {
      logger.error('[AUTH] Failed to parse user data:', e);
      return null;
    }
  }
  return null;
}

// ============================================================
// RBAC（ロールベースアクセス制御）
// ============================================================

/**
 * ロール階層定義
 * 数値が大きいほど高い権限を持つ
 */
const ROLE_HIERARCHY = {
  'partner': 1,           // 閲覧のみ
  'quality_assurance': 2, // 承認可
  'construction_manager': 3, // ナレッジ作成・承認可
  'admin': 4              // 全機能アクセス可
};

/**
 * ロールベースの権限チェック関数
 * ユーザーが指定されたロール以上の権限を持っているか確認
 * @param {string} requiredRole - 必要なロール
 * @returns {boolean} - 権限があるかどうか
 */
function checkPermission(requiredRole) {
  const user = getCurrentUser();
  if (!user) return false;

  const userRoles = user.roles || [];
  const requiredLevel = ROLE_HIERARCHY[requiredRole] || 0;

  // ユーザーの最高権限レベルを取得
  let userMaxLevel = 0;
  userRoles.forEach(role => {
    const level = ROLE_HIERARCHY[role] || 0;
    if (level > userMaxLevel) {
      userMaxLevel = level;
    }
  });

  logger.log(`[RBAC] checkPermission: required=${requiredRole}(${requiredLevel}), userMax=${userMaxLevel}`);
  return userMaxLevel >= requiredLevel;
}

/**
 * 権限チェック関数
 * ユーザーが指定された権限を持っているか確認
 */
function hasPermission(permission) {
  const user = getCurrentUser();
  if (!user) return false;

  const permissions = user.permissions || [];

  // 管理者は全権限
  if (permissions.includes('*')) return true;

  // 指定された権限を持っているか
  return permissions.includes(permission);
}

/**
 * 作成者または管理者かどうかチェック
 * @param {string} creatorId - 作成者のID
 * @returns {boolean} - 編集権限があるかどうか
 */
function canEdit(creatorId) {
  const user = getCurrentUser();
  if (!user) return false;

  // 管理者は常に編集可
  if (checkPermission('admin')) return true;

  // 作成者本人も編集可
  return user.id === creatorId || user.username === creatorId;
}

/**
 * RBAC UI制御を適用
 * data-permission属性、data-role属性、data-required-role属性を持つ要素の表示/非表示を制御
 */
function applyRBACUI() {
  const user = getCurrentUser();
  if (!user) return;

  logger.log('[RBAC] Applying UI controls for user:', user.username);
  logger.log('[RBAC] User roles:', user.roles);

  // data-permission属性を持つ要素を制御
  document.querySelectorAll('[data-permission]').forEach(element => {
    const requiredPermission = element.dataset.permission;
    const hasAccess = hasPermission(requiredPermission);

    if (!hasAccess) {
      // 権限がない場合は非表示
      element.classList.add('permission-hidden');
      logger.log('[RBAC] Permission denied to element:', requiredPermission);
    }
  });

  // data-role属性を持つ要素を制御（完全一致）
  document.querySelectorAll('[data-role]').forEach(element => {
    const allowedRoles = element.dataset.role.split(',');
    const userRoles = user.roles || [];
    const hasRole = allowedRoles.some(role => userRoles.includes(role.trim()));

    if (!hasRole) {
      element.classList.add('permission-hidden');
      logger.log('[RBAC] Role access denied:', allowedRoles);
    }
  });

  // data-required-role属性を持つ要素を制御（階層ベース）
  document.querySelectorAll('[data-required-role]').forEach(element => {
    const requiredRole = element.dataset.requiredRole;
    const hasAccess = checkPermission(requiredRole);

    if (!hasAccess) {
      element.classList.add('permission-hidden');
      logger.log('[RBAC] Required role denied:', requiredRole);
    }
  });

  // data-creator属性を持つ要素を制御（作成者または管理者のみ編集可）
  document.querySelectorAll('[data-creator]').forEach(element => {
    const creatorId = element.dataset.creator;
    const canEditItem = canEdit(creatorId);

    if (!canEditItem) {
      element.classList.add('permission-hidden');
      logger.log('[RBAC] Edit permission denied for creator:', creatorId);
    }
  });
}

// ============================================================
// XSS対策ヘルパー関数
// ============================================================

/**
 * DOM要素を安全に作成
 */
function createElement(tag, attrs = {}, children = []) {
  const element = document.createElement(tag);

  Object.entries(attrs).forEach(([key, value]) => {
    if (key === 'className') {
      element.className = value;
    } else if (key === 'onclick') {
      element.onclick = value;
    } else {
      element.setAttribute(key, value);
    }
  });

  children.forEach(child => {
    if (typeof child === 'string') {
      element.appendChild(document.createTextNode(child));
    } else if (child instanceof Node) {
      element.appendChild(child);
    }
  });

  return element;
}

// ユーザー情報表示
function displayUserInfo() {
  const user = getCurrentUser();
  logger.log('[AUTH] Displaying user info:', user);
  if (!user) return;

  // ヘッダーにユーザー情報を表示（XSS対策: DOM APIを使用）
  const userInfoElement = document.querySelector('.user-info');
  if (userInfoElement) {
    // 既存の内容をクリア
    userInfoElement.textContent = '';

    // 安全にDOM要素を作成
    const userName = createElement('span', {className: 'user-name'}, [
      user.full_name || user.username
    ]);
    const userDept = createElement('span', {className: 'user-dept'}, [
      user.department || ''
    ]);
    const logoutBtn = createElement('button', {className: 'logout-btn', onclick: logout}, [
      'ログアウト'
    ]);

    userInfoElement.appendChild(userName);
    userInfoElement.appendChild(userDept);
    userInfoElement.appendChild(logoutBtn);
  }
}

// ============================================================
// API クライアント
// ============================================================

// 動的にAPIベースURLを設定（localhost、IPアドレス、ホスト名に対応）
const API_BASE = `${window.location.origin}/api/v1`;

/**
 * トークンリフレッシュ関数
 * リフレッシュトークンを使用して新しいアクセストークンを取得
 */
async function refreshAccessToken() {
  const refreshToken = localStorage.getItem('refresh_token');

  if (!refreshToken) {
    logger.log('[AUTH] No refresh token available');
    return false;
  }

  try {
    logger.log('[AUTH] Refreshing access token...');
    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${refreshToken}`
      }
    });

    if (response.ok) {
      const result = await response.json();
      if (result.success) {
        // 新しいアクセストークンを保存
        localStorage.setItem('access_token', result.data.access_token);
        logger.log('[AUTH] Access token refreshed successfully');
        return true;
      }
    }

    logger.log('[AUTH] Token refresh failed');
    return false;
  } catch (error) {
    logger.error('[AUTH] Token refresh error:', error);
    return false;
  }
}

async function fetchAPI(endpoint, options = {}) {
  const token = localStorage.getItem('access_token');

  logger.log('[API] Calling:', endpoint);
  logger.log('[API] Token exists:', token ? 'YES' : 'NO');

  if (!token && !endpoint.includes('/auth/')) {
    logger.log('[API] No token for non-auth endpoint. Redirecting...');
    window.location.href = '/login.html';
    throw new Error('No authentication token');
  }

  try {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
      logger.log('[API] Authorization header added');
    }

    let response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers
    });

    logger.log('[API] Response status:', response.status);

    // 認証エラー（401）の場合、トークンリフレッシュを試行
    if (response.status === 401 && !endpoint.includes('/auth/')) {
      logger.log('[API] 401 Unauthorized. Attempting token refresh...');

      const refreshed = await refreshAccessToken();

      if (refreshed) {
        // リフレッシュ成功 → リクエストをリトライ
        logger.log('[API] Retrying request with new token...');
        const newToken = localStorage.getItem('access_token');
        headers['Authorization'] = `Bearer ${newToken}`;

        response = await fetch(`${API_BASE}${endpoint}`, {
          ...options,
          headers
        });

        logger.log('[API] Retry response status:', response.status);
      } else {
        // リフレッシュ失敗 → ログアウト
        logger.log('[API] Token refresh failed. Logging out...');
        showNotification('セッションの有効期限が切れました。再度ログインしてください。', 'error');
        logout();
        throw new Error('Authentication failed');
      }
    }

    // エラーレスポンスの処理
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}`;
      let errorCode = 'UNKNOWN_ERROR';

      try {
        const errorData = await response.json();
        if (errorData.error) {
          errorMessage = errorData.error.message || errorMessage;
          errorCode = errorData.error.code || errorCode;
        }
      } catch (e) {
        logger.error('[API] Failed to parse error response:', e);
      }

      // ステータスコード別の処理
      if (response.status === 403) {
        showNotification('この操作を実行する権限がありません。', 'error');
      } else if (response.status === 404) {
        showNotification('リソースが見つかりません。', 'error');
      } else if (response.status === 429) {
        showNotification('リクエストが多すぎます。しばらく待ってから再試行してください。', 'warning');
      } else if (response.status === 500) {
        showNotification('サーバーエラーが発生しました。管理者に連絡してください。', 'error');
      } else {
        showNotification(`エラー: ${errorMessage}`, 'error');
      }

      const error = new Error(errorMessage);
      error.code = errorCode;
      error.status = response.status;
      throw error;
    }

    return await response.json();
  } catch (error) {
    logger.error('[API] Error:', error);

    // ネットワークエラーの場合
    if (error.message === 'Failed to fetch' || error.name === 'TypeError') {
      showNotification('ネットワークエラー: サーバーに接続できません。', 'error');
    }

    throw error;
  }
}

// ============================================================
// 通知システム
// ============================================================

/**
 * トースト通知を表示
 */
function showNotification(message, type = 'info') {
  const container = document.getElementById('toastContainer') || createToastContainer();

  const toast = createElement('div', {className: `toast toast-${type}`}, []);
  const icon = {
    'success': '✓',
    'error': '✕',
    'warning': '⚠',
    'info': 'ℹ'
  }[type] || 'ℹ';

  const iconSpan = createElement('span', {className: 'toast-icon'}, [icon]);
  const messageSpan = createElement('span', {className: 'toast-message'}, [message]);

  toast.appendChild(iconSpan);
  toast.appendChild(messageSpan);
  container.appendChild(toast);

  // アニメーション
  setTimeout(() => toast.classList.add('show'), 10);

  // 自動削除
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function createToastContainer() {
  const container = createElement('div', {id: 'toastContainer', className: 'toast-container'}, []);
  document.body.appendChild(container);
  return container;
}

// ============================================================
// データ取得関数
// ============================================================

async function loadDashboardStats() {
  try {
    const result = await fetchAPI('/dashboard/stats');
    if (result.success) {
      updateDashboardStats(result.data);
    }
  } catch (error) {
    logger.log('[DASHBOARD] Using static data (API unavailable)');
    // APIエラーは無視してダミーデータで動作
  }
}

async function loadMonitoringData() {
  try {
    // プロジェクト一覧を取得
    const projectsResult = await fetchAPI('/projects');
    if (projectsResult.success && projectsResult.data.length > 0) {
      // 最初の3つのプロジェクトの進捗を取得
      const monitoringSection = document.querySelector('.progress-list');
      if (monitoringSection) {
        monitoringSection.innerHTML = '';

        for (let i = 0; i < Math.min(3, projectsResult.data.length); i++) {
          const project = projectsResult.data[i];
          const progressResult = await fetchAPI(`/projects/${project.id}/progress`);
          if (progressResult.success) {
            const progressData = progressResult.data;
            const progressItem = createElement('div', {
              className: 'progress-item',
              'data-progress': progressData.progress_percentage
            }, []);

            // 🔧 修正: project.codeフィールドは存在しない（nameに既に含まれている）
            const title = createElement('div', { className: 'progress-title' }, [
              `${project.name}`
            ]);
            const track = createElement('div', { className: 'progress-track' }, []);
            const fill = createElement('span', {
              className: 'progress-fill',
              style: `width: ${progressData.progress_percentage}%`
            }, []);
            track.appendChild(fill);

            const meta = createElement('div', { className: 'progress-meta' }, [
              createElement('span', {}, [`工程 ${progressData.progress_percentage}%`]),
              createElement('span', {}, [`予定 ${Math.max(0, progressData.progress_percentage - 3)}%`])
            ]);

            progressItem.appendChild(title);
            progressItem.appendChild(track);
            progressItem.appendChild(meta);
            monitoringSection.appendChild(progressItem);
          }
        }
      }
    }
  } catch (error) {
    logger.log('[MONITORING] Using static data (API unavailable)');
    // APIエラー時はダミーデータのまま
  }
}

async function loadKnowledge(params = {}) {
  const queryParams = new URLSearchParams(params).toString();
  const endpoint = `/knowledge${queryParams ? '?' + queryParams : ''}`;

  try {
    const result = await fetchAPI(endpoint);
    if (result.success) {
      displayKnowledge(result.data);
    }
  } catch (error) {
    logger.log('[KNOWLEDGE] Using static data (API unavailable)');
    // APIエラーは無視してダミーデータで動作
  }
}

async function loadSOPs() {
  try {
    const result = await fetchAPI('/sop');
    if (result.success) {
      displaySOPs(result.data);
    }
  } catch (error) {
    logger.error('Failed to load SOPs:', error);
  }
}

async function loadIncidents() {
  try {
    const result = await fetchAPI('/incidents');
    if (result.success) {
      displayIncidents(result.data);
    }
  } catch (error) {
    logger.error('Failed to load incidents:', error);
  }
}

async function loadApprovals() {
  try {
    const result = await fetchAPI('/approvals');
    if (result.success) {
      displayApprovals(result.data);
    }
  } catch (error) {
    logger.log('[APPROVALS] Using static data (API unavailable)');
    // APIエラーは無視してダミーデータで動作
  }
}

async function loadNotifications() {
  try {
    const result = await fetchAPI('/notifications');
    if (result.success) {
      updateNotificationBadge(result.data);
      return result.data;
    }
  } catch (error) {
    logger.error('Failed to load notifications:', error);
    return [];
  }
}

// ============================================================
// 空データ表示（本番環境用）
// ============================================================

/**
 * 空データ状態を表示するヘルパー関数
 * 本番環境でデータがない場合に「○○データなし」メッセージを表示
 *
 * @param {HTMLElement} container - 表示先のコンテナ要素
 * @param {string} dataType - データの種類（ナレッジ、SOP、事故レポート等）
 * @param {string} [icon='📭'] - 表示するアイコン
 */
function showEmptyState(container, dataType, icon = '📭') {
  if (!container) return;

  // コンテナをクリア
  container.textContent = '';

  // 空状態メッセージを作成
  const emptyState = createElement('div', { className: 'empty-state' }, []);
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

  // アイコン
  const iconEl = createElement('div', { className: 'empty-state-icon' }, [icon]);
  iconEl.style.cssText = 'font-size: 48px; margin-bottom: 16px; opacity: 0.6;';
  emptyState.appendChild(iconEl);

  // メッセージ
  const messageEl = createElement('div', { className: 'empty-state-message' }, [
    `${dataType}データなし`
  ]);
  messageEl.style.cssText = 'font-size: 16px; font-weight: 500; margin-bottom: 8px;';
  emptyState.appendChild(messageEl);

  // 補足説明（本番環境のみ）
  if (IS_PRODUCTION) {
    const hintEl = createElement('div', { className: 'empty-state-hint' }, [
      'データが登録されていません。'
    ]);
    hintEl.style.cssText = 'font-size: 14px; color: #94a3b8;';
    emptyState.appendChild(hintEl);
  }

  container.appendChild(emptyState);
}

/**
 * データがあるかどうかをチェックし、なければ空状態を表示
 * @param {Array} data - チェックするデータ配列
 * @param {HTMLElement} container - 表示先のコンテナ
 * @param {string} dataType - データの種類
 * @returns {boolean} - データがある場合はtrue
 */
function checkAndShowEmptyState(data, container, dataType) {
  if (!data || data.length === 0) {
    // 本番環境では空状態を表示
    if (IS_PRODUCTION) {
      showEmptyState(container, dataType);
      return false;
    }
    // 開発環境ではサンプルデータ表示のためtrueを返す（既存のダミーデータを維持）
    return true;
  }
  return true;
}

// ============================================================
// データ表示関数
// ============================================================

function updateDashboardStats(stats) {
  // ヘッダー統計情報の更新
  const lastSyncTime = document.getElementById('lastSyncTime');
  const activeWorkers = document.getElementById('activeWorkers');
  const totalWorkers = document.getElementById('totalWorkers');
  const pendingApprovals = document.getElementById('pendingApprovals');

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

  // メトリクスカードの更新
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

function displayKnowledge(knowledgeList) {
  const panel = document.querySelector('[data-panel="search"]');
  if (!panel) return;

  // パネルをクリア（XSS対策）
  panel.textContent = '';

  // 空データチェック（本番環境で空の場合は「ナレッジデータなし」を表示）
  if (!checkAndShowEmptyState(knowledgeList, panel, 'ナレッジ')) {
    return;
  }

  // 各ナレッジカードを安全に作成
  knowledgeList.forEach(k => {
    const card = createElement('div', {className: 'knowledge-card'}, []);
    // サンプルデータの場合はオレンジボーダーを追加
    if (k.title && k.title.includes('[サンプル]')) {
      card.style.borderLeft = '3px solid #f59e0b';
    }

    // ヘッダー部分（タイトルとアクションボタン）
    const cardHeader = createElement('div', {className: 'knowledge-card-header'}, []);
    cardHeader.style.display = 'flex';
    cardHeader.style.justifyContent = 'space-between';
    cardHeader.style.alignItems = 'flex-start';

    // タイトル（クリックで詳細画面へ遷移）
    const title = createElement('h4', {}, [k.title || '']);
    title.style.cursor = 'pointer';
    title.style.flex = '1';
    title.onclick = (e) => {
      e.stopPropagation();
      // IDベースで詳細ページに遷移
      window.location.href = `search-detail.html?id=${k.id}`;
    };
    cardHeader.appendChild(title);

    // アクションボタンコンテナ
    const actionButtons = createElement('div', {className: 'knowledge-actions'}, []);
    actionButtons.style.display = 'flex';
    actionButtons.style.gap = '8px';

    // 編集ボタン（作成者または管理者のみ表示）
    const creatorId = k.owner_id || k.owner || k.created_by;
    if (canEdit(creatorId)) {
      const editBtn = createElement('button', {className: 'cta ghost small'}, ['編集']);
      editBtn.style.fontSize = '12px';
      editBtn.style.padding = '4px 8px';
      editBtn.onclick = (e) => {
        e.stopPropagation();
        editKnowledge(k.id, creatorId);
      };
      actionButtons.appendChild(editBtn);
    }

    cardHeader.appendChild(actionButtons);
    card.appendChild(cardHeader);

    // メタ情報
    const meta = createElement('div', {className: 'knowledge-meta'}, [
      `最終更新: ${formatDate(k.updated_at)} · ${k.category} · 工区: ${k.project || 'N/A'} · 担当: ${k.owner}`
    ]);
    card.appendChild(meta);

    // タグ
    if (k.tags && k.tags.length > 0) {
      const tagsContainer = createElement('div', {className: 'knowledge-tags'}, []);
      k.tags.forEach(tag => {
        const tagSpan = createElement('span', {className: 'tag'}, [tag]);
        tagsContainer.appendChild(tagSpan);
      });
      card.appendChild(tagsContainer);
    }

    // サマリー
    const summary = createElement('div', {}, [k.summary || '']);
    card.appendChild(summary);

    panel.appendChild(card);
  });
}

function displaySOPs(sopList) {
  const panel = document.querySelector('[data-panel="sop"]');
  if (!panel) return;

  // パネルをクリア（XSS対策）
  panel.textContent = '';

  // 空データチェック（本番環境で空の場合は「標準作業手順書データなし」を表示）
  if (!checkAndShowEmptyState(sopList, panel, '標準作業手順書')) {
    return;
  }

  // 各SOPカードを安全に作成
  sopList.forEach(sop => {
    const card = createElement('div', {className: 'knowledge-card'}, []);
    // サンプルデータの場合はオレンジボーダーを追加
    if (sop.title && sop.title.includes('[サンプル]')) {
      card.style.borderLeft = '3px solid #f59e0b';
    }

    // カードクリックでSOP詳細画面へ遷移
    card.style.cursor = 'pointer';
    card.onclick = () => {
      // IDベースで詳細ページに遷移
      window.location.href = `sop-detail.html?id=${sop.id}`;
    };

    const title = createElement('h4', {}, [sop.title || '']);
    card.appendChild(title);

    const meta = createElement('div', {className: 'knowledge-meta'}, [
      `改訂: ${formatDate(sop.revision_date)} · ${sop.category} · ${sop.target}`
    ]);
    card.appendChild(meta);

    if (sop.tags && sop.tags.length > 0) {
      const tagsContainer = createElement('div', {className: 'knowledge-tags'}, []);
      sop.tags.forEach(tag => {
        const tagSpan = createElement('span', {className: 'tag'}, [tag]);
        tagsContainer.appendChild(tagSpan);
      });
      card.appendChild(tagsContainer);
    }

    const content = createElement('div', {}, [sop.content || '']);
    card.appendChild(content);

    panel.appendChild(card);
  });
}

function displayIncidents(incidentList) {
  const panel = document.querySelector('[data-panel="incident"]');
  if (!panel) return;

  // パネルをクリア（XSS対策）
  panel.textContent = '';

  // 空データチェック（本番環境で空の場合は「事故・ヒヤリハットデータなし」を表示）
  if (!checkAndShowEmptyState(incidentList, panel, '事故・ヒヤリハット')) {
    return;
  }

  // 各事故レポートカードを安全に作成
  incidentList.forEach(incident => {
    const card = createElement('div', {className: 'knowledge-card'}, []);
    // サンプルデータの場合はオレンジボーダーを追加
    if (incident.title && incident.title.includes('[サンプル]')) {
      card.style.borderLeft = '3px solid #f59e0b';
    }

    // カードクリックで事故レポート詳細画面へ遷移
    card.style.cursor = 'pointer';
    card.onclick = () => {
      // IDベースで詳細ページに遷移
      window.location.href = `incident-detail.html?id=${incident.id}`;
    };

    const title = createElement('h4', {}, [incident.title || '']);
    card.appendChild(title);

    const meta = createElement('div', {className: 'knowledge-meta'}, [
      `報告日: ${formatDate(incident.date)} · 現場: ${incident.project}`
    ]);
    card.appendChild(meta);

    if (incident.tags && incident.tags.length > 0) {
      const tagsContainer = createElement('div', {className: 'knowledge-tags'}, []);
      incident.tags.forEach(tag => {
        const tagSpan = createElement('span', {className: 'tag'}, [tag]);
        tagsContainer.appendChild(tagSpan);
      });
      card.appendChild(tagsContainer);
    }

    const description = createElement('div', {}, [incident.description || '']);
    card.appendChild(description);

    panel.appendChild(card);
  });
}

function displayApprovals(approvalList) {
  const flowContainer = document.querySelector('.flow');
  if (!flowContainer) return;

  // 空データチェック（本番環境で空の場合は「承認待ちデータなし」を表示）
  if (!checkAndShowEmptyState(approvalList, flowContainer, '承認待ち')) {
    return;
  }

  const statusBadgeClass = {
    'pending': 'is-wait',
    'reviewing': 'is-info',
    'approved': 'is-done',
    'rejected': 'is-hold'
  };

  const statusText = {
    'pending': '承認待ち',
    'reviewing': '確認中',
    'approved': '承認済み',
    'rejected': '差戻し'
  };

  // コンテナをクリア（XSS対策）
  flowContainer.textContent = '';

  // 最初の3件を安全に表示
  approvalList.slice(0, 3).forEach(approval => {
    const flowStep = createElement('div', {className: 'flow-step'}, []);

    const titleDiv = createElement('div', {}, [approval.title || '']);
    flowStep.appendChild(titleDiv);

    const badgeClass = statusBadgeClass[approval.status] || 'is-info';
    const badge = createElement('span', {className: `badge ${badgeClass}`}, [
      statusText[approval.status] || approval.status
    ]);
    flowStep.appendChild(badge);

    flowContainer.appendChild(flowStep);
  });
}

function updateNotificationBadge(notifications) {
  const badge = document.getElementById('notificationBadge');
  if (!badge) return;

  const unreadCount = notifications.filter(n => !n.read).length;

  if (unreadCount > 0) {
    badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
    badge.style.display = 'inline-block';
  } else {
    badge.style.display = 'none';
  }
}

// ============================================================
// ユーティリティ関数
// ============================================================

function formatDate(dateString) {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return `${date.getFullYear()}/${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')}`;
}

function formatTime(dateString) {
  if (!dateString) return '--:--';
  const date = new Date(dateString);
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
}

// ============================================================
// 検索機能
// ============================================================

function setupSearch() {
  const searchInput = document.querySelector('.search input');
  const searchButton = document.querySelector('.search button');

  if (searchButton) {
    searchButton.addEventListener('click', () => {
      const query = searchInput?.value || '';
      if (query) {
        loadKnowledge({ search: query });
      }
    });
  }

  if (searchInput) {
    searchInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        const query = searchInput.value || '';
        if (query) {
          loadKnowledge({ search: query });
        }
      }
    });
  }
}

// ============================================================
// モーダル管理
// ============================================================

/**
 * 新規ナレッジ登録モーダルを開く
 */
function openNewKnowledgeModal() {
  if (!checkPermission('construction_manager')) {
    showNotification('ナレッジ登録権限がありません。', 'error');
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
    // フォームをリセット
    const form = document.getElementById('newKnowledgeForm');
    if (form) form.reset();
  }
}

/**
 * 新規相談モーダルを開く
 */
function openNewConsultModal() {
  // expert-consult-actions.js の submitNewConsultation 関数を呼び出す
  if (typeof submitNewConsultation === 'function') {
    submitNewConsultation();
  } else {
    logger.warn('[MODAL] submitNewConsultation function not found, creating modal directly');
    // フォールバック: 直接モーダルを作成
    createNewConsultModalFallback();
  }
}

/**
 * 新規相談モーダルを作成（フォールバック）
 */
function createNewConsultModalFallback() {
  const existingModal = document.getElementById('newConsultModal');
  if (existingModal) {
    existingModal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    return;
  }

  const modalHTML = `
    <div id="newConsultModal" class="modal" style="display: flex;">
      <div class="modal-content">
        <div class="modal-header">
          <h2>専門家に相談</h2>
          <button class="modal-close" onclick="closeNewConsultModalFallback()">&times;</button>
        </div>
        <div class="modal-body">
          <form id="newConsultForm">
            <div class="field">
              <label>相談タイトル <span class="required">*</span></label>
              <input type="text" id="newConsultTitle" required placeholder="相談の概要を簡潔に入力してください">
            </div>
            <div class="field">
              <label>カテゴリ <span class="required">*</span></label>
              <select id="newConsultCategory" required>
                <option value="">選択してください</option>
                <option value="技術相談">技術相談</option>
                <option value="安全対策">安全対策</option>
                <option value="品質管理">品質管理</option>
                <option value="工程計画">工程計画</option>
                <option value="法令規格">法令規格</option>
                <option value="資材調達">資材調達</option>
                <option value="その他">その他</option>
              </select>
            </div>
            <div class="field">
              <label>優先度 <span class="required">*</span></label>
              <select id="newConsultPriority" required>
                <option value="通常" selected>通常</option>
                <option value="高">高</option>
                <option value="緊急">緊急</option>
                <option value="低">低</option>
              </select>
            </div>
            <div class="field">
              <label>相談内容 <span class="required">*</span></label>
              <textarea id="newConsultContent" rows="6" required placeholder="具体的な相談内容を入力してください（最小10文字）"></textarea>
            </div>
            <div class="field">
              <label>タグ（カンマ区切り）</label>
              <input type="text" id="newConsultTags" placeholder="例: コンクリート, 品質管理, 養生">
            </div>
            <div class="modal-actions">
              <button type="button" class="cta ghost" onclick="closeNewConsultModalFallback()">キャンセル</button>
              <button type="submit" class="cta">相談を投稿</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `;

  document.body.insertAdjacentHTML('beforeend', modalHTML);
  document.body.style.overflow = 'hidden';

  // フォーム送信イベント
  const form = document.getElementById('newConsultForm');
  if (form) {
    form.addEventListener('submit', async function(e) {
      e.preventDefault();
      await submitNewConsultationAPI();
    });
  }
}

/**
 * 新規相談をAPI経由で投稿
 */
async function submitNewConsultationAPI() {
  const title = document.getElementById('newConsultTitle').value;
  const category = document.getElementById('newConsultCategory').value;
  const priority = document.getElementById('newConsultPriority').value;
  const content = document.getElementById('newConsultContent').value;
  const tagsInput = document.getElementById('newConsultTags').value;
  const tags = tagsInput ? tagsInput.split(',').map(t => t.trim()) : [];

  if (content.length < 10) {
    showNotification('相談内容は10文字以上で入力してください', 'error');
    return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/consultations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({
        title: title,
        question: content,
        category: category,
        priority: priority,
        tags: tags
      })
    });

    const result = await response.json();

    if (result.success) {
      showNotification('相談を投稿しました', 'success');
      closeNewConsultModalFallback();
      // 詳細ページにリダイレクト
      setTimeout(() => {
        window.location.href = `expert-consult.html?id=${result.data.id}`;
      }, 1000);
    } else {
      showNotification(result.error?.message || '相談の投稿に失敗しました', 'error');
    }
  } catch (error) {
    logger.error('[API] Error submitting consultation:', error);
    showNotification('相談の投稿に失敗しました', 'error');
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
 * 検索フォームをリセット
 */
function resetSearchForm() {
  const form = document.getElementById('advancedSearchForm');
  if (form) {
    form.reset();
    const resultsDiv = document.getElementById('searchResults');
    if (resultsDiv) resultsDiv.textContent = '';
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

    // 通知データを読み込み
    const notifications = await loadNotifications();
    displayNotifications(notifications);
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
 * 通知を表示
 */
function displayNotifications(notifications) {
  const listContainer = document.getElementById('notificationList');
  if (!listContainer) return;

  listContainer.textContent = '';

  if (!notifications || notifications.length === 0) {
    const emptyMsg = createElement('div', {className: 'empty-message'}, ['通知はありません']);
    listContainer.appendChild(emptyMsg);
    return;
  }

  notifications.forEach(notif => {
    const item = createElement('div', {className: `notification-item ${notif.read ? 'read' : 'unread'}`}, []);

    const header = createElement('div', {className: 'notification-header'}, []);
    const title = createElement('strong', {}, [notif.title || '通知']);
    const time = createElement('span', {className: 'notification-time'}, [formatTime(notif.created_at)]);
    header.appendChild(title);
    header.appendChild(time);

    const message = createElement('div', {className: 'notification-message'}, [notif.message || '']);

    const actions = createElement('div', {className: 'notification-actions'}, []);
    if (!notif.read) {
      const markReadBtn = createElement('button', {className: 'notification-btn'}, ['既読にする']);
      markReadBtn.onclick = () => markNotificationAsRead(notif.id);
      actions.appendChild(markReadBtn);
    }

    item.appendChild(header);
    item.appendChild(message);
    item.appendChild(actions);

    listContainer.appendChild(item);
  });
}

/**
 * 通知を既読にする
 */
async function markNotificationAsRead(notificationId) {
  try {
    const result = await fetchAPI(`/notifications/${notificationId}/read`, {
      method: 'PUT'
    });

    if (result.success) {
      showNotification('通知を既読にしました', 'success');
      const notifications = await loadNotifications();
      displayNotifications(notifications);
    }
  } catch (error) {
    logger.error('Failed to mark notification as read:', error);
    showNotification('通知の更新に失敗しました', 'error');
  }
}

/**
 * ユーザー設定を読み込み
 */
function loadUserSettings() {
  const user = getCurrentUser();
  if (!user) return;

  // ユーザー設定
  const fullNameInput = document.getElementById('userFullName');
  const departmentInput = document.getElementById('userDepartment');
  const emailInput = document.getElementById('userEmail');

  if (fullNameInput) fullNameInput.value = user.full_name || '';
  if (departmentInput) departmentInput.value = user.department || '';
  if (emailInput) emailInput.value = user.email || '';

  // 通知設定（localStorageから読み込み）
  const notifyApproval = document.getElementById('notifyApproval');
  const notifyKnowledge = document.getElementById('notifyKnowledge');
  const notifyIncident = document.getElementById('notifyIncident');
  const notifyEmail = document.getElementById('notifyEmail');

  if (notifyApproval) notifyApproval.checked = localStorage.getItem('notify_approval') !== 'false';
  if (notifyKnowledge) notifyKnowledge.checked = localStorage.getItem('notify_knowledge') !== 'false';
  if (notifyIncident) notifyIncident.checked = localStorage.getItem('notify_incident') !== 'false';
  if (notifyEmail) notifyEmail.checked = localStorage.getItem('notify_email') === 'true';

  // 表示設定
  const itemsPerPage = document.getElementById('itemsPerPage');
  const enableAnimations = document.getElementById('enableAnimations');
  const compactMode = document.getElementById('compactMode');

  if (itemsPerPage) itemsPerPage.value = localStorage.getItem('items_per_page') || '20';
  if (enableAnimations) enableAnimations.checked = localStorage.getItem('enable_animations') !== 'false';
  if (compactMode) compactMode.checked = localStorage.getItem('compact_mode') === 'true';

  // MFA設定状態を読み込み
  loadMFAStatus();
}

// ============================================================
// フォーム送信処理
// ============================================================

/**
 * 新規ナレッジ登録フォームの送信
 */
async function submitNewKnowledge(event) {
  event.preventDefault();

  const form = event.target;
  const formData = new FormData(form);

  const data = {
    title: formData.get('title'),
    category: formData.get('category'),
    priority: formData.get('priority'),
    project: formData.get('project') || null,
    summary: formData.get('summary'),
    content: formData.get('content'),
    tags: formData.get('tags') ? formData.get('tags').split(',').map(t => t.trim()).filter(t => t) : []
  };

  try {
    const result = await fetchAPI('/knowledge', {
      method: 'POST',
      body: JSON.stringify(data)
    });

    if (result.success) {
      showNotification('ナレッジを登録しました！', 'success');
      closeNewKnowledgeModal();
      loadKnowledge(); // リロード
    }
  } catch (error) {
    logger.error('Failed to create knowledge:', error);
    showNotification('登録に失敗しました: ' + error.message, 'error');
  }
}

/**
 * 高度な検索フォームの送信
 */
async function submitAdvancedSearch(event) {
  event.preventDefault();

  const form = event.target;
  const formData = new FormData(form);

  const params = {
    keyword: formData.get('keyword'),
    category: formData.get('category'),
    date_from: formData.get('dateFrom'),
    date_to: formData.get('dateTo'),
    tags: formData.get('tags'),
    project: formData.get('project')
  };

  // 空のパラメータを削除
  Object.keys(params).forEach(key => {
    if (!params[key]) delete params[key];
  });

  try {
    const queryParams = new URLSearchParams(params).toString();
    const result = await fetchAPI(`/knowledge/search?${queryParams}`);

    if (result.success) {
      displaySearchResults(result.data);
      showNotification(`${result.data.length}件の結果が見つかりました`, 'success');
    }
  } catch (error) {
    logger.error('Search failed:', error);
    showNotification('検索に失敗しました', 'error');
  }
}

/**
 * ヒーローセクションの検索を実行
 */
async function performHeroSearch() {
  const input = document.getElementById('heroSearchInput');
  if (!input) return;

  const keyword = input.value.trim();
  if (!keyword) {
    showNotification('検索キーワードを入力してください', 'warning');
    return;
  }

  try {
    const result = await fetchAPI(`/knowledge/search?keyword=${encodeURIComponent(keyword)}`);

    if (result.success) {
      // 検索結果タブに切り替え
      const searchTab = document.querySelector('.tab-btn[data-tab="search"]');
      if (searchTab) {
        searchTab.click();
      }

      // 検索結果を表示
      displayKnowledge(result.data);
      showNotification(`${result.data.length}件の結果が見つかりました`, 'success');
    }
  } catch (error) {
    logger.error('Hero search failed:', error);
    showNotification('検索に失敗しました', 'error');
  }
}

/**
 * 検索結果を表示
 */
function displaySearchResults(results) {
  const resultsDiv = document.getElementById('searchResults');
  if (!resultsDiv) return;

  resultsDiv.textContent = '';

  if (results.length === 0) {
    const emptyMsg = createElement('div', {className: 'empty-message'}, ['検索結果がありません']);
    resultsDiv.appendChild(emptyMsg);
    return;
  }

  results.forEach(item => {
    const card = createElement('div', {className: 'knowledge-card'}, []);
    card.style.cursor = 'pointer';
    card.onclick = () => {
      // IDベースで詳細ページに遷移
      window.location.href = `search-detail.html?id=${item.id}`;
    };

    const title = createElement('h4', {}, [item.title || '']);
    const meta = createElement('div', {className: 'knowledge-meta'}, [
      `${item.category} · ${formatDate(item.updated_at)}`
    ]);
    const summary = createElement('div', {}, [item.summary || '']);

    card.appendChild(title);
    card.appendChild(meta);
    card.appendChild(summary);

    resultsDiv.appendChild(card);
  });
}

/**
 * ユーザー設定フォームの送信
 */
async function submitUserSettings(event) {
  event.preventDefault();

  const form = event.target;
  const formData = new FormData(form);

  const data = {
    full_name: formData.get('fullName'),
    department: formData.get('department'),
    email: formData.get('email')
  };

  try {
    const result = await fetchAPI('/users/profile', {
      method: 'PUT',
      body: JSON.stringify(data)
    });

    if (result.success) {
      // ローカルストレージのユーザー情報を更新
      const user = getCurrentUser();
      Object.assign(user, data);
      localStorage.setItem('user', JSON.stringify(user));

      showNotification('設定を保存しました', 'success');
      displayUserInfo(); // ヘッダーの表示を更新
    }
  } catch (error) {
    logger.error('Failed to update settings:', error);
    showNotification('設定の保存に失敗しました', 'error');
  }
}

/**
 * 通知設定フォームの送信
 */
function submitNotificationSettings(event) {
  event.preventDefault();

  const form = event.target;
  const formData = new FormData(form);

  localStorage.setItem('notify_approval', formData.get('notifyApproval') === 'on');
  localStorage.setItem('notify_knowledge', formData.get('notifyKnowledge') === 'on');
  localStorage.setItem('notify_incident', formData.get('notifyIncident') === 'on');
  localStorage.setItem('notify_email', formData.get('notifyEmail') === 'on');

  showNotification('通知設定を保存しました', 'success');
}

/**
 * 表示設定フォームの送信
 */
function submitDisplaySettings(event) {
  event.preventDefault();

  const form = event.target;
  const formData = new FormData(form);

  localStorage.setItem('items_per_page', formData.get('itemsPerPage'));
  localStorage.setItem('enable_animations', formData.get('enableAnimations') === 'on');
  localStorage.setItem('compact_mode', formData.get('compactMode') === 'on');

  showNotification('表示設定を保存しました', 'success');
}

// ============================================================
// MFA（2要素認証）設定
// ============================================================

/**
 * MFA設定状態を読み込み
 */
async function loadMFAStatus() {
  const mfaStatus = document.getElementById('mfaStatus');
  const mfaSetupBtn = document.getElementById('mfaSetupBtn');
  const mfaDisableBtn = document.getElementById('mfaDisableBtn');

  if (!mfaStatus) return;

  const user = getCurrentUser();
  if (!user) return;

  const isEnabled = user.mfa_enabled || false;

  mfaStatus.textContent = isEnabled ? '有効' : '無効';
  mfaStatus.className = isEnabled ? 'mfa-status enabled' : 'mfa-status disabled';

  if (mfaSetupBtn) mfaSetupBtn.style.display = isEnabled ? 'none' : 'inline-block';
  if (mfaDisableBtn) mfaDisableBtn.style.display = isEnabled ? 'inline-block' : 'none';
}

/**
 * MFAセットアップ開始
 */
async function startMFASetup() {
  const modal = document.getElementById('mfaSetupModal');
  const qrcodeContainer = document.getElementById('mfaQRCode');
  const secretDisplay = document.getElementById('mfaSecretKey');

  if (!modal) return;

  try {
    showNotification('MFAセットアップを開始しています...', 'info');

    const result = await fetchAPI('/auth/mfa/setup', {
      method: 'POST'
    });

    if (!result.success) {
      showNotification(result.error?.message || 'MFAセットアップに失敗しました', 'error');
      return;
    }

    // QRコード生成（qrcode.jsライブラリを使用、なければテキスト表示）
    if (qrcodeContainer) {
      qrcodeContainer.textContent = '';
      if (typeof QRCode !== 'undefined') {
        new QRCode(qrcodeContainer, {
          text: result.data.provisioning_uri,
          width: 200,
          height: 200
        });
      } else {
        // QRコードライブラリがない場合はURIを表示
        const uriText = createElement('p', { className: 'mfa-uri-text' }, [
          '認証アプリで以下のURIを手動入力してください:'
        ]);
        const uriCode = createElement('code', { className: 'mfa-uri-code' }, [
          result.data.provisioning_uri
        ]);
        qrcodeContainer.appendChild(uriText);
        qrcodeContainer.appendChild(uriCode);
      }
    }

    // シークレットキー表示
    if (secretDisplay) {
      secretDisplay.textContent = result.data.secret;
    }

    // モーダル表示
    modal.style.display = 'flex';

  } catch (error) {
    logger.error('[MFA] Setup error:', error);
    showNotification('MFAセットアップに失敗しました', 'error');
  }
}

/**
 * MFA有効化（コード検証）
 */
async function verifyAndEnableMFA() {
  const codeInput = document.getElementById('mfaVerifyCode');
  const code = codeInput?.value.trim();

  if (!code || !/^\d{6}$/.test(code)) {
    showNotification('6桁の認証コードを入力してください', 'error');
    return;
  }

  try {
    const result = await fetchAPI('/auth/mfa/verify', {
      method: 'POST',
      body: JSON.stringify({ code })
    });

    if (result.success) {
      showNotification('2要素認証が有効になりました', 'success');

      // ユーザー情報を更新
      const user = getCurrentUser();
      user.mfa_enabled = true;
      localStorage.setItem('user', JSON.stringify(user));

      // モーダルを閉じる
      closeMFASetupModal();

      // 状態を更新
      loadMFAStatus();
    } else {
      showNotification(result.error?.message || '認証コードが正しくありません', 'error');
      codeInput.value = '';
      codeInput.focus();
    }
  } catch (error) {
    logger.error('[MFA] Verify error:', error);
    showNotification('認証に失敗しました', 'error');
  }
}

/**
 * MFA無効化
 */
async function disableMFA() {
  if (!confirm('2要素認証を無効にしますか？\nセキュリティが低下する可能性があります。')) {
    return;
  }

  try {
    const result = await fetchAPI('/auth/mfa/disable', {
      method: 'POST'
    });

    if (result.success) {
      showNotification('2要素認証を無効にしました', 'success');

      // ユーザー情報を更新
      const user = getCurrentUser();
      user.mfa_enabled = false;
      localStorage.setItem('user', JSON.stringify(user));

      // 状態を更新
      loadMFAStatus();
    } else {
      showNotification(result.error?.message || 'MFA無効化に失敗しました', 'error');
    }
  } catch (error) {
    logger.error('[MFA] Disable error:', error);
    showNotification('MFA無効化に失敗しました', 'error');
  }
}

/**
 * MFAセットアップモーダルを閉じる
 */
function closeMFASetupModal() {
  const modal = document.getElementById('mfaSetupModal');
  if (modal) {
    modal.style.display = 'none';
  }
  // 入力をクリア
  const codeInput = document.getElementById('mfaVerifyCode');
  if (codeInput) codeInput.value = '';
}

// ============================================================
// タブ切替機能
// ============================================================

const tabs = document.querySelectorAll(".tab-btn");
const panels = document.querySelectorAll(".tab-panel");

if (tabs.length && panels.length) {
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const target = tab.dataset.tab;
      tabs.forEach((btn) => {
        const isActive = btn === tab;
        btn.classList.toggle("is-active", isActive);
        btn.setAttribute("aria-selected", String(isActive));
      });
      panels.forEach((panel) => {
        const isActive = panel.dataset.panel === target;
        panel.classList.toggle("is-active", isActive);
      });

      // タブ切替時にデータをロード
      if (target === 'search') {
        loadKnowledge();
      } else if (target === 'sop') {
        loadSOPs();
      } else if (target === 'incident') {
        loadIncidents();
      }
    });
  });
}

// ============================================================
// サイドパネルタブ切替
// ============================================================

function setupSidePanelTabs() {
  document.querySelectorAll('.side-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const panel = btn.closest('.side-panel');
      if (!panel) return;

      const tabName = btn.dataset.tab;

      // タブボタンの状態を更新
      panel.querySelectorAll('.side-tab-btn').forEach(b => {
        b.classList.toggle('is-active', b === btn);
      });

      // 設定パネルの場合、セクションを切り替え
      if (panel.id === 'settingsPanel') {
        panel.querySelectorAll('.settings-section').forEach(section => {
          section.classList.remove('is-active');
        });

        const sectionMap = {
          'user': 'userSettings',
          'notification': 'notificationSettings',
          'display': 'displaySettings'
        };

        const targetSection = document.getElementById(sectionMap[tabName]);
        if (targetSection) {
          targetSection.classList.add('is-active');
        }
      }

      // 通知パネルの場合、フィルタリング
      if (panel.id === 'notificationSidePanel') {
        // 将来実装: 通知タイプ別フィルタ（info/warning/error）、日付範囲フィルタ
        // Issue: Phase D機能として実装予定
      }
    });
  });
}

// ============================================================
// トグルボタン機能
// ============================================================

const toggleGroups = document.querySelectorAll("[data-toggle-group]");

toggleGroups.forEach((group) => {
  const options = group.querySelectorAll("[data-toggle]");
  if (!options.length) {
    return;
  }
  options.forEach((option) => {
    if (!option.hasAttribute("aria-pressed")) {
      option.setAttribute(
        "aria-pressed",
        String(option.classList.contains("is-active"))
      );
    }
    option.addEventListener("click", () => {
      const mode = group.dataset.toggleGroup || "single";
      if (mode === "multi") {
        const isActive = option.classList.toggle("is-active");
        option.setAttribute("aria-pressed", String(isActive));
        return;
      }
      options.forEach((btn) => {
        const isActive = btn === option;
        btn.classList.toggle("is-active", isActive);
        btn.setAttribute("aria-pressed", String(isActive));
      });
    });
  });
});

// ============================================================
// プログレスバーアニメーション
// ============================================================

const progressItems = document.querySelectorAll("[data-progress]");

progressItems.forEach((item) => {
  const fill = item.querySelector(".progress-fill");
  const value = Number(item.dataset.progress);
  if (!fill || Number.isNaN(value)) {
    return;
  }
  const safeValue = Math.min(100, Math.max(0, value));
  requestAnimationFrame(() => {
    fill.style.width = `${safeValue}%`;
  });
});

// ============================================================
// 承認・却下機能
// ============================================================

/**
 * 選択されたアイテムを承認
 * quality_assurance以上の権限が必要
 */
async function approveSelected() {
  if (!checkPermission('quality_assurance')) {
    showNotification('承認権限がありません。', 'error');
    return;
  }

  try {
    // 最初の承認待ちアイテムを取得（簡易実装）
    const approvalsData = await fetchAPI('/approvals');
    const pendingApproval = approvalsData.data?.find(a => a.status === 'pending');

    if (!pendingApproval) {
      showNotification('承認待ちのアイテムがありません。', 'info');
      return;
    }

    const result = await fetchAPI(`/approvals/${pendingApproval.id}/approve`, {
      method: 'POST'
    });

    if (result.success) {
      showNotification('承認処理を実行しました。', 'success');
      logger.log('[APPROVAL] Approved item:', pendingApproval.id);
      loadApprovals();
    }
  } catch (error) {
    logger.error('[APPROVAL] Failed to approve:', error);
    showNotification('承認処理に失敗しました。', 'error');
  }
}

/**
 * 選択されたアイテムを却下
 * quality_assurance以上の権限が必要
 */
async function rejectSelected() {
  if (!checkPermission('quality_assurance')) {
    showNotification('却下権限がありません。', 'error');
    return;
  }

  const reason = prompt('却下理由を入力してください:');
  if (!reason) return;

  try {
    // 最初の承認待ちアイテムを取得（簡易実装）
    const approvalsData = await fetchAPI('/approvals');
    const pendingApproval = approvalsData.data?.find(a => a.status === 'pending');

    if (!pendingApproval) {
      showNotification('承認待ちのアイテムがありません。', 'info');
      return;
    }

    const result = await fetchAPI(`/approvals/${pendingApproval.id}/reject`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ reason })
    });

    if (result.success) {
      showNotification('却下処理を実行しました。', 'success');
      logger.log('[APPROVAL] Rejected item:', pendingApproval.id, 'Reason:', reason);
      loadApprovals();
    }
  } catch (error) {
    logger.error('[APPROVAL] Failed to reject:', error);
    showNotification('却下処理に失敗しました。', 'error');
  }
}

/**
 * ナレッジを編集
 * 作成者または管理者のみ編集可
 */
async function editKnowledge(knowledgeId, creatorId) {
  if (!canEdit(creatorId)) {
    showNotification('編集権限がありません。作成者または管理者のみ編集できます。', 'error');
    return;
  }

  // 将来実装: 新規作成モーダルを流用した編集専用モーダルを表示
  // - GET /api/v1/knowledge/<id> でデータ取得
  // - フォームにデータをプリセット
  // - PUT /api/v1/knowledge/<id> で更新
  // Issue: Phase D機能として実装予定
  showNotification('編集画面へ遷移します: ' + knowledgeId, 'info');
  logger.log('[KNOWLEDGE] Editing knowledge:', knowledgeId);
}

// ============================================================
// その他のアクション（プレースホルダー削除済み）
// ============================================================

// shareDashboard() と submitDistribution() は actions.js に実装済み

function openApprovalBox() {
  window.location.href = '#approvals';
  showNotification('承認箱へスクロールしました', 'info');
}

function generateMorningSummary() {
  showNotification('朝礼用サマリを生成しています...', 'info');
  // 将来実装: 前日の更新、未読通知、承認待ちをPDF/Excel出力
  // Issue #TODO: Phase D機能として実装予定
}

// ============================================================
// Chart.js ダッシュボードグラフ
// ============================================================

let dashboardCharts = {};

/**
 * ダッシュボードグラフを初期化
 */
function initDashboardCharts() {
  if (typeof Chart === 'undefined') {
    logger.warn('Chart.js is not loaded');
    return;
  }

  // デフォルトフォント設定
  Chart.defaults.font.family = '"Zen Kaku Gothic New", sans-serif';

  // 日別出来高チャート
  const dailyProgressCanvas = document.getElementById('dailyProgressChart');
  if (dailyProgressCanvas) {
    dashboardCharts.dailyProgress = new Chart(dailyProgressCanvas, {
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
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: 'rgba(27, 38, 37, 0.9)',
            padding: 12,
            titleColor: '#fff',
            bodyColor: '#fff',
            borderColor: '#d4662f',
            borderWidth: 1,
            callbacks: {
              label: function(context) {
                return context.parsed.y + '%';
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: {
              callback: function(value) {
                return value + '%';
              },
              color: '#4b5b58'
            },
            grid: {
              color: 'rgba(216, 210, 200, 0.5)'
            }
          },
          x: {
            ticks: {
              color: '#4b5b58'
            },
            grid: {
              display: false
            }
          }
        }
      }
    });
  }

  // リスクトレンドチャート
  const riskTrendCanvas = document.getElementById('riskTrendChart');
  if (riskTrendCanvas) {
    dashboardCharts.riskTrend = new Chart(riskTrendCanvas, {
      type: 'bar',
      data: {
        labels: ['1週前', '6日前', '5日前', '4日前', '3日前', '2日前', '昨日', '今日'],
        datasets: [
          {
            label: '品質リスク',
            data: [3, 2, 4, 3, 2, 3, 4, 3],
            backgroundColor: 'rgba(224, 139, 62, 0.7)',
            borderColor: '#e08b3e',
            borderWidth: 1
          },
          {
            label: '原価リスク',
            data: [2, 3, 2, 2, 3, 2, 3, 4],
            backgroundColor: 'rgba(197, 83, 58, 0.7)',
            borderColor: '#c5533a',
            borderWidth: 1
          },
          {
            label: '安全リスク',
            data: [1, 1, 0, 1, 1, 2, 1, 2],
            backgroundColor: 'rgba(47, 75, 82, 0.7)',
            borderColor: '#2f4b52',
            borderWidth: 1
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'top',
            labels: {
              boxWidth: 12,
              boxHeight: 12,
              padding: 10,
              font: {
                size: 11
              },
              color: '#4b5b58'
            }
          },
          tooltip: {
            backgroundColor: 'rgba(27, 38, 37, 0.9)',
            padding: 12,
            titleColor: '#fff',
            bodyColor: '#fff',
            borderColor: '#d4662f',
            borderWidth: 1
          }
        },
        scales: {
          x: {
            stacked: true,
            ticks: {
              font: {
                size: 10
              },
              color: '#4b5b58'
            },
            grid: {
              display: false
            }
          },
          y: {
            stacked: true,
            beginAtZero: true,
            ticks: {
              stepSize: 1,
              color: '#4b5b58'
            },
            grid: {
              color: 'rgba(216, 210, 200, 0.5)'
            }
          }
        }
      }
    });
  }
}

/**
 * グラフデータを更新
 */
function updateChartData(chartName, newData) {
  const chart = dashboardCharts[chartName];
  if (!chart) return;

  if (newData.labels) {
    chart.data.labels = newData.labels;
  }

  if (newData.datasets) {
    chart.data.datasets.forEach((dataset, i) => {
      if (newData.datasets[i]) {
        dataset.data = newData.datasets[i].data;
      }
    });
  }

  chart.update();
}

// ============================================================
// イベントリスナーの設定
// ============================================================

function setupEventListeners() {
  // 新規ナレッジ登録フォーム
  const newKnowledgeForm = document.getElementById('newKnowledgeForm');
  if (newKnowledgeForm) {
    newKnowledgeForm.addEventListener('submit', submitNewKnowledge);
  }

  // 高度な検索フォーム
  const advancedSearchForm = document.getElementById('advancedSearchForm');
  if (advancedSearchForm) {
    advancedSearchForm.addEventListener('submit', submitAdvancedSearch);
  }

  // ユーザー設定フォーム
  const userSettingsForm = document.getElementById('userSettingsForm');
  if (userSettingsForm) {
    userSettingsForm.addEventListener('submit', submitUserSettings);
  }

  // 通知設定フォーム
  const notificationSettingsForm = document.getElementById('notificationSettingsForm');
  if (notificationSettingsForm) {
    notificationSettingsForm.addEventListener('submit', submitNotificationSettings);
  }

  // 表示設定フォーム
  const displaySettingsForm = document.getElementById('displaySettingsForm');
  if (displaySettingsForm) {
    displaySettingsForm.addEventListener('submit', submitDisplaySettings);
  }

  // モーダルの外側クリックで閉じる
  document.querySelectorAll('.modal, .side-panel').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.style.display = 'none';
        modal.classList.remove('open');
        document.body.style.overflow = '';
      }
    });
  });
}

// ============================================================
// 定期更新
// ============================================================

function startPeriodicUpdates() {
  // 5分ごとにダッシュボード統計を更新
  setInterval(() => {
    loadDashboardStats();
    loadNotifications();
  }, 5 * 60 * 1000);
}

// ============================================================
// ダミーデータのロードとlocalStorage保存
// ============================================================

/**
 * バックエンドの生成済みダミーデータをlocalStorageに保存
 */
async function loadDummyDataToStorage() {
  logger.log('[DATA] Loading dummy data to localStorage...');

  const dataFiles = [
    { key: 'knowledge_details', file: '/data/knowledge_details.json' },
    { key: 'sop_details', file: '/data/sop_details.json' },
    { key: 'incidents_details', file: '/data/incidents_details.json' },
    { key: 'consultations_details', file: '/data/consultations_details.json' },
    { key: 'projects', file: '/data/projects.json' },
    { key: 'experts', file: '/data/experts.json' }
  ];

  for (const {key, file} of dataFiles) {
    try {
      const response = await fetch(file);
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem(key, JSON.stringify(data));
        logger.log(`[DATA] ✓ Loaded ${key}: ${data.length} items (${(JSON.stringify(data).length / 1024).toFixed(1)} KB)`);
      } else {
        logger.error(`[DATA] ✗ Failed to load ${file}: ${response.status}`);
      }
    } catch (error) {
      logger.error(`[DATA] ✗ Error loading ${file}:`, error);
    }
  }

  logger.log('[DATA] All dummy data loaded to localStorage!');
}

/**
 * 詳細ページへ遷移（ナレッジ）
 * 修正: localStorageを使わず、APIに完全依存
 */
function viewKnowledgeDetail(knowledgeId) {
  logger.log('[NAVIGATION] Viewing knowledge detail:', knowledgeId);

  // URLパラメータ付きで詳細ページに遷移
  // 詳細データはloadKnowledgeDetail()がAPIから取得
  window.location.href = `search-detail.html?id=${knowledgeId}`;
}

/**
 * 詳細ページへ遷移（SOP）
 * 修正: localStorageを使わず、APIに完全依存
 */
function viewSOPDetail(sopId) {
  logger.log('[NAVIGATION] Viewing SOP detail:', sopId);
  window.location.href = `sop-detail.html?id=${sopId}`;
}

/**
 * 詳細ページへ遷移（事故レポート）
 * 修正: localStorageを使わず、APIに完全依存
 */
function viewIncidentDetail(incidentId) {
  logger.log('[NAVIGATION] Viewing incident detail:', incidentId);
  window.location.href = `incident-detail.html?id=${incidentId}`;
}

/**
 * 詳細ページへ遷移（専門家相談）
 * 修正: localStorageを使わず、APIに完全依存
 */
function viewConsultationDetail(consultId) {
  logger.log('[NAVIGATION] Viewing consultation detail:', consultId);
  window.location.href = `expert-consult.html?id=${consultId}`;
}

// ============================================================
// サイドバー機能
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
 * セクションの折りたたみ切替
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
 * ダミーデータ: 人気ナレッジ
 */
const DUMMY_POPULAR_KNOWLEDGE = [
  { id: 1, title: '砂防堰堤 温度管理フロー', views: 342, category: '施工計画' },
  { id: 2, title: '橋梁補修 塗膜剥離基準', views: 298, category: '品質管理' },
  { id: 3, title: '高所作業車 点検SOP', views: 276, category: '安全衛生' },
  { id: 4, title: '路面下空洞検知手順', views: 254, category: '施工管理' },
  { id: 5, title: '降雨時施工制限手順', views: 231, category: '施工計画' },
  { id: 6, title: 'ICT出来形測定基準', views: 218, category: '品質管理' },
  { id: 7, title: '夜間舗装の安全管理', views: 205, category: '安全衛生' },
  { id: 8, title: '地盤改良品質確認', views: 192, category: '品質管理' },
  { id: 9, title: 'トンネル換気計画', views: 178, category: '環境対策' },
  { id: 10, title: '鋼橋塗装規格改定', views: 165, category: '技術基準' }
];

/**
 * ダミーデータ: 最近追加されたナレッジ
 */
const DUMMY_RECENT_KNOWLEDGE = [
  { id: 11, title: 'RC橋脚の耐震補強工法', daysAgo: 1, category: '構造設計' },
  { id: 12, title: '土石流対策工の配置基準', daysAgo: 2, category: '砂防' },
  { id: 13, title: '鋼材溶接部の検査手順', daysAgo: 3, category: '品質管理' },
  { id: 14, title: '法面緑化の施工時期', daysAgo: 4, category: '環境対策' },
  { id: 15, title: '建設機械の燃費管理', daysAgo: 5, category: '原価管理' }
];

/**
 * ダミーデータ: お気に入りナレッジ
 */
const DUMMY_FAVORITE_KNOWLEDGE = [
  { id: 16, title: 'コンクリート配合設計', category: '品質管理' },
  { id: 17, title: '足場組立安全基準', category: '安全衛生' },
  { id: 18, title: '道路標識設置基準', category: '施工計画' }
];

/**
 * ダミーデータ: 人気タグ
 */
const DUMMY_TAGS = [
  { name: '品質確保', count: 45, size: 'large' },
  { name: '安全管理', count: 38, size: 'large' },
  { name: '寒冷地施工', count: 32, size: 'medium' },
  { name: '温度センサー', count: 28, size: 'medium' },
  { name: '鋼橋', count: 25, size: 'medium' },
  { name: '塗装規格', count: 22, size: 'small' },
  { name: '地中レーダー', count: 19, size: 'small' },
  { name: '点検', count: 17, size: 'small' },
  { name: '交通規制', count: 15, size: 'small' },
  { name: '夜間', count: 12, size: 'small' }
];

/**
 * ダミーデータ: プロジェクト一覧
 */
const DUMMY_PROJECTS = [
  { id: 'B-03', name: '東北橋梁補修', type: '橋梁', progress: 64, phase: '3-2', manager: '田中', milestone: '主桁塗装完了' },
  { id: 'K-12', name: '首都高速更新', type: '道路', progress: 38, phase: '2-1', manager: '佐藤', milestone: '夜間舗装開始' },
  { id: 'R-07', name: '河川護岸整備', type: '河川', progress: 81, phase: '4-3', manager: '鈴木', milestone: '護岸工完了' },
  { id: 'S-05', name: '砂防堰堤新設', type: '砂防', progress: 52, phase: '2-3', manager: '高橋', milestone: 'コンクリート打設中' },
  { id: 'T-09', name: '山岳トンネル掘削', type: 'トンネル', progress: 28, phase: '1-2', manager: '渡辺', milestone: '掘削進捗120m' },
  { id: 'D-14', name: '国道拡幅工事', type: '道路', progress: 75, phase: '3-4', manager: '伊藤', milestone: '路盤工完了' },
  { id: 'H-21', name: '橋梁架替工事', type: '橋梁', progress: 43, phase: '2-2', manager: '山本', milestone: '下部工施工中' },
  { id: 'R-18', name: '河川浚渫工事', type: '河川', progress: 67, phase: '3-1', manager: '中村', milestone: '浚渫進捗65%' },
  { id: 'S-22', name: '地すべり対策', type: '砂防', progress: 35, phase: '1-3', manager: '小林', milestone: '集水井設置中' },
  { id: 'T-16', name: 'シールド工事', type: 'トンネル', progress: 58, phase: '2-4', manager: '加藤', milestone: '推進延長340m' },
  { id: 'B-11', name: '鋼橋耐震補強', type: '橋梁', progress: 91, phase: '4-2', manager: '吉田', milestone: '最終検査待ち' },
  { id: 'D-08', name: '橋梁床版取替', type: '橋梁', progress: 22, phase: '1-1', manager: '山田', milestone: '交通規制準備中' }
];

/**
 * ダミーデータ: 専門家一覧
 */
const DUMMY_EXPERTS = [
  { id: 1, name: '斎藤 健一', field: '安全管理', status: 'online', answers: 47, rating: 4.8, available: '10:00-17:00' },
  { id: 2, name: '吉岡 美咲', field: '地盤技術', status: 'online', answers: 38, rating: 4.9, available: '13:00-19:00' },
  { id: 3, name: '藤田 隆', field: '構造設計', status: 'offline', answers: 52, rating: 4.7, available: '09:00-18:00' },
  { id: 4, name: '森本 由紀', field: '品質管理', status: 'online', answers: 41, rating: 4.6, available: '08:00-16:00' },
  { id: 5, name: '松井 剛', field: '施工管理', status: 'online', answers: 35, rating: 4.5, available: '10:00-18:00' },
  { id: 6, name: '岡田 春子', field: '環境対策', status: 'offline', answers: 29, rating: 4.7, available: '09:00-17:00' },
  { id: 7, name: '清水 大輔', field: '構造設計', status: 'online', answers: 44, rating: 4.8, available: '08:30-17:30' },
  { id: 8, name: '野口 真理', field: '安全管理', status: 'offline', answers: 33, rating: 4.6, available: '10:00-16:00' },
  { id: 9, name: '前田 啓介', field: '地盤技術', status: 'online', answers: 39, rating: 4.9, available: '09:00-18:00' },
  { id: 10, name: '西村 由美', field: '品質管理', status: 'online', answers: 37, rating: 4.7, available: '08:00-17:00' },
  { id: 11, name: '石井 雅彦', field: '施工管理', status: 'offline', answers: 31, rating: 4.5, available: '10:00-19:00' },
  { id: 12, name: '村田 千尋', field: '環境対策', status: 'online', answers: 26, rating: 4.8, available: '09:00-16:00' },
  { id: 13, name: '橋本 誠', field: '構造設計', status: 'offline', answers: 48, rating: 4.9, available: '08:00-18:00' },
  { id: 14, name: '内田 佳奈', field: '安全管理', status: 'online', answers: 34, rating: 4.6, available: '09:00-17:00' },
  { id: 15, name: '木村 拓也', field: '地盤技術', status: 'online', answers: 42, rating: 4.8, available: '10:00-18:00' },
  { id: 16, name: '長谷川 美紀', field: '品質管理', status: 'offline', answers: 28, rating: 4.5, available: '08:30-16:30' },
  { id: 17, name: '井上 健太', field: '施工管理', status: 'online', answers: 36, rating: 4.7, available: '09:00-18:00' },
  { id: 18, name: '坂本 彩', field: '環境対策', status: 'online', answers: 25, rating: 4.6, available: '10:00-17:00' },
  { id: 19, name: '中島 信也', field: '構造設計', status: 'offline', answers: 45, rating: 4.8, available: '08:00-17:00' },
  { id: 20, name: '福田 恵子', field: '地盤技術', status: 'online', answers: 40, rating: 4.9, available: '09:30-18:30' }
];

/**
 * 人気ナレッジを表示
 */
async function loadPopularKnowledge(category = '') {
  const container = document.getElementById('popularKnowledgeList');
  if (!container) return;

  container.textContent = '';

  try {
    // APIから人気ナレッジを取得
    const result = await fetchAPI('/knowledge/popular?limit=10');

    if (!result.success || !result.data || result.data.length === 0) {
      const emptyMsg = createElement('div', { className: 'empty-message' }, ['人気ナレッジデータなし']);
      container.appendChild(emptyMsg);
      return;
    }

    let filteredData = result.data;
    if (category) {
      filteredData = filteredData.filter(k => k.category === category);
    }

    filteredData.forEach((item, index) => {
      const navItem = createElement('div', { className: 'nav-item clickable' }, []);
      navItem.onclick = () => viewKnowledgeDetail(item.id);

      const rank = createElement('span', { className: 'rank' }, [`${index + 1}`]);
      const title = createElement('strong', {}, [item.title]);
      const views = createElement('span', { className: 'meta' }, [`${item.views || 0} views`]);

      navItem.appendChild(rank);
      navItem.appendChild(title);
      navItem.appendChild(views);

      container.appendChild(navItem);
    });
  } catch (error) {
    logger.error('[KNOWLEDGE] Failed to load popular knowledge:', error);
    const errorMsg = createElement('div', { className: 'empty-message' }, ['読み込みエラー']);
    container.appendChild(errorMsg);
  }
}

/**
 * 最近追加されたナレッジを表示
 */
async function loadRecentKnowledge(category = '') {
  const container = document.getElementById('recentKnowledgeList');
  if (!container) return;

  container.textContent = '';

  try {
    // APIから最近追加されたナレッジを取得
    const result = await fetchAPI('/knowledge/recent?limit=10&days=7');

    if (!result.success || !result.data || result.data.length === 0) {
      const emptyMsg = createElement('div', { className: 'empty-message' }, ['最近のナレッジデータなし']);
      container.appendChild(emptyMsg);
      return;
    }

    let filteredData = result.data;
    if (category) {
      filteredData = filteredData.filter(k => k.category === category);
    }

    filteredData.forEach(item => {
      const navItem = createElement('div', { className: 'nav-item clickable' }, []);
      navItem.onclick = () => viewKnowledgeDetail(item.id);

      const title = createElement('strong', {}, [item.title]);

      // 作成日時から経過日数を計算
      let daysAgo = '?';
      if (item.created_at) {
        try {
          const created = new Date(item.created_at);
          const now = new Date();
          const diffTime = Math.abs(now - created);
          daysAgo = Math.floor(diffTime / (1000 * 60 * 60 * 24));
        } catch (e) {}
      }

      const meta = createElement('span', { className: 'meta' }, [`${daysAgo}日前`]);

      navItem.appendChild(title);
      navItem.appendChild(meta);

      container.appendChild(navItem);
    });
  } catch (error) {
    logger.error('[KNOWLEDGE] Failed to load recent knowledge:', error);
    const errorMsg = createElement('div', { className: 'empty-message' }, ['読み込みエラー']);
    container.appendChild(errorMsg);
  }
}

/**
 * お気に入りナレッジを表示
 */
async function loadFavoriteKnowledge() {
  const container = document.getElementById('favoriteKnowledgeList');
  if (!container) return;

  container.textContent = '';

  try {
    // APIからお気に入りナレッジを取得
    const result = await fetchAPI('/knowledge/favorites');

    if (!result.success || !result.data || result.data.length === 0) {
      const emptyMsg = createElement('div', { className: 'empty-message' }, ['お気に入りはありません']);
      container.appendChild(emptyMsg);
      return;
    }

    result.data.forEach(item => {
      const navItem = createElement('div', { className: 'nav-item clickable' }, []);
      navItem.onclick = () => viewKnowledgeDetail(item.id);

      const title = createElement('strong', {}, [item.title]);
      const removeFav = createElement('button', { className: 'icon-btn-small' }, ['★']);
      removeFav.onclick = (e) => {
        e.stopPropagation();
        removeFavorite(item.id);
      };

      navItem.appendChild(title);
      navItem.appendChild(removeFav);

      container.appendChild(navItem);
    });
  } catch (error) {
    logger.error('[KNOWLEDGE] Failed to load favorites:', error);
    const emptyMsg = createElement('div', { className: 'empty-message' }, ['お気に入りはありません']);
    container.appendChild(emptyMsg);
  }
}

/**
 * タグクラウドを表示
 */
async function loadTagCloud() {
  const container = document.getElementById('tagCloud');
  if (!container) return;

  container.textContent = '';

  try {
    // APIからタグクラウドデータを取得
    const result = await fetchAPI('/knowledge/tags');

    if (!result.success || !result.data || result.data.length === 0) {
      const emptyMsg = createElement('div', { className: 'empty-message' }, ['タグデータなし']);
      container.appendChild(emptyMsg);
      return;
    }

    // 上位20タグのみ表示
    const topTags = result.data.slice(0, 20);

    topTags.forEach(tag => {
      const tagBtn = createElement('button', {
        className: `tag-btn tag-${tag.size || 1}`,
        onclick: () => filterByTag(tag.name)
      }, [`${tag.name} (${tag.count})`]);

      container.appendChild(tagBtn);
    });
  } catch (error) {
    logger.error('[KNOWLEDGE] Failed to load tags:', error);
    const errorMsg = createElement('div', { className: 'empty-message' }, ['タグデータなし']);
    container.appendChild(errorMsg);
  }
}

/**
 * プロジェクト一覧を表示
 */
async function loadProjects(type = '') {
  const container = document.getElementById('projectsList');
  if (!container) return;

  container.textContent = '';

  try {
    // APIからプロジェクトデータを取得
    const params = {};
    if (type) params.type = type;

    const result = await fetchAPI('/projects', { method: 'GET' });
    if (!result.success) {
      throw new Error('Failed to load projects');
    }

    let filteredData = Array.isArray(result.data) ? result.data : [];
    if (type) {
      filteredData = filteredData.filter(p => p.type === type);
    }

    if (!filteredData.length && !IS_PRODUCTION) {
      filteredData = DUMMY_PROJECTS;
    }

    if (!filteredData.length) {
      const emptyMsg = createElement('div', { className: 'empty-message' }, ['プロジェクトデータなし']);
      container.appendChild(emptyMsg);
      return;
    }

    filteredData.forEach(async (project) => {
    const projectItem = createElement('div', { className: 'project-item' }, []);

    // プロジェクトヘッダー
    const header = createElement('div', { className: 'project-header clickable' }, []);
    header.onclick = () => toggleProjectDetail(project.id);

    const projectCode = project.code || project.project_code || project.id || '';
    const projectName = project.name || project.title || 'プロジェクト';
    const nameLabel = projectCode ? `${projectName} (${projectCode})` : projectName;
    const name = createElement('strong', {}, [nameLabel]);
    const chevron = createElement('span', { className: 'chevron-small', id: `chevron-${project.id}` }, ['▼']);

    header.appendChild(name);
    header.appendChild(chevron);
    projectItem.appendChild(header);

    // プログレスバー（初期値はプロジェクトの保存された進捗率）
    const progressPercentage = project.progress_percentage ?? project.progress ?? 0;
    const progressBar = createElement('div', { className: 'mini-progress' }, []);
    const progressFill = createElement('div', {
      className: 'mini-progress-fill',
      style: `width: ${progressPercentage}%`
    }, []);
    progressBar.appendChild(progressFill);
    projectItem.appendChild(progressBar);

    const progressText = createElement('div', { className: 'progress-text' }, [`進捗 ${progressPercentage}%`]);
    projectItem.appendChild(progressText);

    // リアルタイム進捗を取得して更新
    try {
      const progressResult = await fetchAPI(`/projects/${project.id}/progress`);
      if (progressResult.success) {
        const progressData = progressResult.data;
        progressFill.style.width = `${progressData.progress_percentage}%`;
        progressText.textContent = `進捗 ${progressData.progress_percentage}%`;
      }
    } catch (error) {
      logger.log(`[PROJECTS] Failed to load progress for ${project.id}:`, error);
    }

    // プロジェクト詳細（初期状態は非表示）
    const details = createElement('div', {
      className: 'project-details',
      id: `details-${project.id}`,
      style: 'display: none;'
    }, []);

    const phaseValue = project.phase || project.work_section || project.work_type || '未設定';
    const managerValue = project.manager || project.owner || project.members?.[0]?.name || '未設定';
    const milestoneValue = project.milestone || project.milestones?.[0]?.title || '未設定';

    const phase = createElement('div', { className: 'detail-row' }, [
      createElement('span', { className: 'detail-label' }, ['工区:']),
      createElement('span', {}, [phaseValue])
    ]);
    const manager = createElement('div', { className: 'detail-row' }, [
      createElement('span', { className: 'detail-label' }, ['担当:']),
      createElement('span', {}, [managerValue])
    ]);
    const milestone = createElement('div', { className: 'detail-row' }, [
      createElement('span', { className: 'detail-label' }, ['マイルストーン:']),
      createElement('span', {}, [milestoneValue])
    ]);

    details.appendChild(phase);
    details.appendChild(manager);
    details.appendChild(milestone);
    projectItem.appendChild(details);

    container.appendChild(projectItem);
  });
  } catch (error) {
    logger.error('[PROJECTS] Failed to load projects:', error);
    const emptyMsg = createElement('div', { className: 'empty-message' }, ['プロジェクトデータなし']);
    container.appendChild(emptyMsg);
  }
}

/**
 * プロジェクト詳細の表示切替
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

/**
 * 専門家一覧を表示
 */
async function loadExperts(field = '') {
  const container = document.getElementById('expertsList');
  if (!container) return;

  container.textContent = '';

  try {
    // APIから専門家データを取得
    const params = {};
    if (field) params.specialization = field;

    const result = await fetchAPI('/experts', { method: 'GET' });
    if (!result.success) {
      throw new Error('Failed to load experts');
    }

    let filteredData = Array.isArray(result.data) ? result.data : [];
    if (field) {
      filteredData = filteredData.filter(e => (e.specialization || e.field || e.specialties?.[0]) === field);
    }

    if (!filteredData.length && !IS_PRODUCTION) {
      filteredData = DUMMY_EXPERTS;
    }

    if (!filteredData.length) {
      const emptyMsg = createElement('div', { className: 'empty-message' }, ['専門家データなし']);
      container.appendChild(emptyMsg);
      return;
    }

    filteredData.forEach(async (expert) => {
    const expertItem = createElement('div', { className: 'expert-item' }, []);

    // 専門家ヘッダー
    const header = createElement('div', { className: 'expert-header' }, []);

    const isAvailable = expert.is_available ?? expert.online ?? false;
    const consultationCount = expert.consultation_count ?? expert.answer_count ?? 0;
    const rating = expert.rating ?? expert.average_rating ?? 0;
    const specializationValue = expert.specialization || expert.field || expert.specialties?.[0] || '未設定';

    const statusDot = createElement('span', {
      className: `status-dot ${isAvailable ? 'is-ok' : 'is-muted'}`
    }, []);

    // ユーザー名を取得
    const expertName = expert.name || `Expert ${expert.id}`;
    const name = createElement('strong', {}, [expertName]);
    const specialization = createElement('span', { className: 'meta' }, [specializationValue]);

    header.appendChild(statusDot);
    header.appendChild(name);
    header.appendChild(specialization);
    expertItem.appendChild(header);

    // 専門家情報（統計を取得）
    const info = createElement('div', { className: 'expert-info' }, []);

    try {
      const statsResult = await fetchAPI(`/experts/${expert.id}`);
      if (statsResult.success) {
        const answers = createElement('div', { className: 'info-row' }, [
          `回答数: ${consultationCount}件 · 評価: ⭐${rating}`
        ]);
        const available = createElement('div', { className: 'info-row small' }, [
          `対応可能: ${isAvailable ? 'はい' : 'いいえ'}`
        ]);

        info.appendChild(answers);
        info.appendChild(available);
      }
    } catch (error) {
      logger.log(`[EXPERTS] Failed to load details for ${expert.id}:`, error);
      // デフォルト表示
      const answers = createElement('div', { className: 'info-row' }, [
        `回答数: ${consultationCount}件 · 評価: ⭐${rating}`
      ]);
      const available = createElement('div', { className: 'info-row small' }, [
        `対応可能: ${isAvailable ? 'はい' : 'いいえ'}`
      ]);

      info.appendChild(answers);
      info.appendChild(available);
    }

    expertItem.appendChild(info);

    // 相談ボタン
    const consultBtn = createElement('button', {
      className: 'cta ghost small',
      onclick: () => consultExpert(expert.id)
    }, ['相談する']);
    consultBtn.style.marginTop = '8px';
    consultBtn.style.width = '100%';

    expertItem.appendChild(consultBtn);
    container.appendChild(expertItem);
  });
  } catch (error) {
    logger.error('[EXPERTS] Failed to load experts:', error);
    const emptyMsg = createElement('div', { className: 'empty-message' }, ['専門家データなし']);
    container.appendChild(emptyMsg);
  }
}

/**
 * カテゴリフィルター
 */
function filterKnowledgeByCategory(category) {
  loadPopularKnowledge(category);
  loadRecentKnowledge(category);
}

/**
 * プロジェクトタイプフィルター
 */
function filterProjectsByType(type) {
  loadProjects(type);
}

/**
 * 専門分野フィルター
 */
function filterExpertsByField(field) {
  loadExperts(field);
}

// viewKnowledgeDetail関数は1852-1866行目で定義済み（重複削除）

/**
 * お気に入りから削除
 */
async function removeFavorite(knowledgeId) {
  logger.log('[SIDEBAR] Removing favorite:', knowledgeId);

  try {
    const result = await fetchAPI(`/favorites/${knowledgeId}`, {
      method: 'DELETE'
    });

    if (result.success) {
      showNotification('お気に入りから削除しました', 'success');
      loadFavoriteKnowledge();
    }
  } catch (error) {
    logger.error('[FAVORITES] Failed to remove:', error);
    showNotification('お気に入りの削除に失敗しました', 'error');
  }
}

/**
 * タグでフィルター
 */
function filterByTag(tagName) {
  logger.log('[SIDEBAR] Filtering by tag:', tagName);
  showNotification(`タグ「${tagName}」で検索します`, 'info');
  loadKnowledge({ tags: tagName });
}

/**
 * 専門家に相談
 */
function consultExpert(expertId) {
  const expert = DUMMY_EXPERTS.find(e => e.id === expertId);
  if (expert) {
    logger.log('[SIDEBAR] Consulting expert:', expert.name);
    showNotification(`${expert.name}さんへ相談画面を開きます`, 'info');

    // 専門家相談の最初のアイテムを表示（デモ用）
    const consultData = JSON.parse(localStorage.getItem('consultations_details') || '[]');
    if (consultData.length > 0) {
      viewConsultationDetail(1); // 最初の相談を表示
    } else {
      window.location.href = 'expert-consult.html';
    }
  }
}

/**
 * メインコンテンツのカードにクリックイベントを追加
 */
function setupCardClickHandlers() {
  logger.log('[SETUP] Setting up card click handlers...');

  // 各タブパネル内のknowledge-cardを取得
  const panels = {
    'panel-search': 'knowledge',
    'panel-sop': 'sop',
    'panel-incident': 'incident'
  };

  Object.entries(panels).forEach(([panelId, type]) => {
    const panel = document.getElementById(panelId);
    if (!panel) return;

    const cards = panel.querySelectorAll('.knowledge-card');
    cards.forEach((card, index) => {
      // カードをクリック可能にする
      card.style.cursor = 'pointer';
      card.style.transition = 'all 0.2s';

      // ホバーエフェクト
      card.addEventListener('mouseenter', () => {
        card.style.transform = 'translateY(-2px)';
        card.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
      });

      card.addEventListener('mouseleave', () => {
        card.style.transform = 'translateY(0)';
        card.style.boxShadow = '';
      });

      // クリックイベント
      card.addEventListener('click', () => {
        // ダミーデータから該当するIDを計算（サンプルとして1-3を使用）
        const itemId = index + 1;

        if (type === 'knowledge') {
          viewKnowledgeDetail(itemId);
        } else if (type === 'sop') {
          viewSOPDetail(itemId);
        } else if (type === 'incident') {
          viewIncidentDetail(itemId);
        }
      });
    });

    logger.log(`[SETUP] Added click handlers to ${cards.length} cards in ${panelId}`);
  });

  // 当番エキスパート（右サイドバー）にクリックイベントを追加
  setupExpertClickHandlers();
}

/**
 * 当番エキスパートクリック機能
 */
function setupExpertClickHandlers() {
  const expertDocuments = document.querySelectorAll('aside.rail .document');

  expertDocuments.forEach((doc, index) => {
    const strongEl = doc.querySelector('strong');
    if (strongEl && strongEl.textContent.includes('エキスパート')) {
      doc.style.cursor = 'pointer';
      doc.style.transition = 'all 0.2s';

      doc.addEventListener('mouseenter', () => {
        doc.style.background = 'rgba(212, 102, 47, 0.08)';
      });

      doc.addEventListener('mouseleave', () => {
        doc.style.background = '';
      });

      doc.addEventListener('click', () => {
        // 専門家相談の最初の数件を表示（サンプル）
        const consultId = index + 1;
        viewConsultationDetail(consultId);
      });
    }
  });
}

// ============================================================
// 初期化
// ============================================================

document.addEventListener('DOMContentLoaded', async () => {
  logger.log('建設土木ナレッジシステム - 初期化中...');

  // 認証チェック
  if (!checkAuth()) {
    return; // 認証失敗時は処理を中断
  }

  // ダミーデータをlocalStorageに保存
  await loadDummyDataToStorage();

  // ユーザー情報表示
  displayUserInfo();

  // RBAC UI制御を適用
  applyRBACUI();

  // 検索機能のセットアップ
  setupSearch();

  // イベントリスナーの設定
  setupEventListeners();

  // サイドパネルタブの設定
  setupSidePanelTabs();

  // 初期データのロード
  loadDashboardStats();
  loadMonitoringData();
  loadExpertStats();

  // KNOWLEDGE HUBとサイドバーのデータロード
  loadPopularKnowledge();
  loadRecentKnowledge();
  loadFavoriteKnowledge();
  loadTagCloud();
  loadProjects();
  loadExperts();

  // メインコンテンツのロード
  loadKnowledge();
  loadSOPs();
  loadIncidents();
  loadApprovals();
  loadNotifications();

  // Chart.js グラフの初期化
  if (typeof Chart !== 'undefined') {
    initDashboardCharts();
  }

  // メインコンテンツのカードにクリックイベントを追加
  setupCardClickHandlers();

  // 定期更新を開始
  startPeriodicUpdates();

  logger.log('初期化完了！');

  // SocketIOの初期化
  initSocketIO();
});

// ============================================================
// SocketIO リアルタイム更新
// ============================================================

let socket;

/**
 * SocketIOの初期化
 */
function initSocketIO() {
  if (typeof io === 'undefined') {
    logger.warn('[SOCKET] Socket.IO library not loaded');
    return;
  }

  // SocketIO接続
  socket = io(window.location.origin, {
    transports: ['websocket', 'polling'],
    auth: {
      token: localStorage.getItem('access_token')
    }
  });

  // 接続イベント
  socket.on('connect', () => {
    logger.log('[SOCKET] Connected to server');
    showNotification('リアルタイム接続が確立されました', 'success');

    // ダッシュボードルーム参加
    socket.emit('join_dashboard');
  });

  // 切断イベント
  socket.on('disconnect', () => {
    logger.log('[SOCKET] Disconnected from server');
    showNotification('リアルタイム接続が切断されました', 'warning');
  });

  // 接続確認
  socket.on('connected', (data) => {
    logger.log('[SOCKET] Server confirmed connection:', data);
  });

  // ダッシュボード統計更新
  socket.on('dashboard_stats_update', (data) => {
    logger.log('[SOCKET] Dashboard stats update:', data);
    updateDashboardStats(data.stats);
    showNotification('ダッシュボードが更新されました', 'info');
  });

  // プロジェクト進捗更新
  socket.on('project_progress_update', (data) => {
    logger.log('[SOCKET] Project progress update:', data);
    updateProjectProgress(data.project_id, data.progress);
    showNotification(`プロジェクト ${data.project_id} の進捗が更新されました`, 'info');
  });

  // 専門家統計更新
  socket.on('expert_stats_update', (data) => {
    logger.log('[SOCKET] Expert stats update:', data);
    updateExpertStats(data.expert_stats);
    showNotification('専門家統計が更新されました', 'info');
  });

  // エラーハンドリング
  socket.on('connect_error', (error) => {
    logger.error('[SOCKET] Connection error:', error);
    showNotification('リアルタイム接続に失敗しました', 'error');
  });
}

/**
 * プロジェクト進捗のリアルタイム更新
 */
function updateProjectProgress(projectId, progressData) {
  // サイドバーのプロジェクト一覧を更新
  const projectItems = document.querySelectorAll('.project-item');
  projectItems.forEach(item => {
    const header = item.querySelector('.project-header strong');
    if (header && header.textContent.includes(`(${projectId})`)) {
      // 進捗バーを更新
      const progressFill = item.querySelector('.mini-progress-fill');
      const progressText = item.querySelector('.progress-text');

      if (progressFill && progressText) {
        const progressPercent = progressData.progress_percentage || 0;
        progressFill.style.width = `${progressPercent}%`;
        progressText.textContent = `進捗 ${progressPercent}%`;
      }
    }
  });

  // メインコンテンツの稼働モニタリングも更新
  const progressItems = document.querySelectorAll('.progress-item');
  progressItems.forEach(item => {
    const title = item.querySelector('.progress-title');
    if (title && title.textContent.includes(projectId)) {
      const progressFill = item.querySelector('.progress-fill');
      const progressMeta = item.querySelector('.progress-meta');

      if (progressFill && progressMeta) {
        const progressPercent = progressData.progress_percentage || 0;
        progressFill.style.width = `${progressPercent}%`;
        progressMeta.innerHTML = `
          <span>工程 ${progressPercent}%</span>
          <span>予定 ${Math.max(0, progressPercent - 3)}%</span>
        `;
      }
    }
  });
}

/**
 * 専門家統計のリアルタイム更新
 */
function updateExpertStats(expertStats) {
  // 専門家一覧を更新
  const expertItems = document.querySelectorAll('.expert-item');
  expertItems.forEach(item => {
    const header = item.querySelector('.expert-header strong');
    if (header) {
      const expertName = header.textContent;
      const expertData = expertStats.experts?.find(e => e.name === expertName);

      if (expertData) {
        const infoRow = item.querySelector('.info-row');
        if (infoRow) {
          infoRow.textContent = `回答数: ${expertData.consultation_count}件 · 評価: ⭐${expertData.average_rating}`;
        }
      }
    }
  });
}

/**
 * プロジェクトルーム参加/退出
 */
function joinProjectRoom(projectId) {
  if (socket && socket.connected) {
    socket.emit('join_project', { project_id: projectId });
  }
}

function leaveProjectRoom(projectId) {
  if (socket && socket.connected) {
    socket.emit('leave_project', { project_id: projectId });
  }
}

/**
 * プロジェクト進捗APIを呼び出してリアルタイム更新
 */
async function loadProjectProgress(projectId) {
  try {
    const result = await fetchAPI(`/projects/${projectId}/progress`);
    if (result.success) {
      updateProjectProgress(projectId, result.data);
      return result.data;
    }
  } catch (error) {
    logger.error('[PROJECT] Failed to load progress:', error);
  }
  return null;
}

/**
 * 専門家統計APIを呼び出してリアルタイム更新
 */
async function loadExpertStats() {
  try {
    const result = await fetchAPI('/experts/stats');
    if (result.success) {
      updateExpertStats(result.data);
      updateDutyExperts(result.data);
    }
  } catch (error) {
    logger.error('[EXPERTS] Failed to load expert stats:', error);
  }
}

function updateDutyExperts(expertStats) {
  // 当番エキスパートを更新
  const expertDocuments = document.querySelectorAll('aside.rail .document');
  if (expertDocuments.length > 0 && expertStats.experts) {
    // 最初の2人の専門家を表示
    const experts = expertStats.experts.slice(0, 2);
    experts.forEach((expert, index) => {
      if (expertDocuments[index]) {
        const doc = expertDocuments[index];
        doc.innerHTML = '';

        const title = createElement('strong', {}, [`${expert.specialization}: ${expert.name || 'Unknown'}`]);
        const small = createElement('small', {}, [
          `対応可能: 10:00-17:00 / 東北エリア`
        ]);
        const div = createElement('div', {}, [
          `相談件数: ${expert.consultation_count}件 · 評価: ⭐${expert.average_rating}`
        ]);

        doc.appendChild(title);
        doc.appendChild(small);
        doc.appendChild(div);
      }
    });
  }
}

/**
 * 専門家評価アルゴリズムAPIを呼び出して評価を取得
 */
async function calculateExpertRating(expertId) {
  try {
    const result = await fetchAPI(`/experts/${expertId}/rating`);
    if (result.success) {
      return result.data.calculated_rating;
    }
  } catch (error) {
    logger.error('[EXPERT] Failed to calculate rating:', error);
  }
  return null;
}

// ============================================================
// グローバル関数の明示的な公開（onclick属性から呼び出し可能）
// ============================================================

window.performHeroSearch = performHeroSearch;
window.openSearchModal = openSearchModal;
window.closeSearchModal = closeSearchModal;
window.resetSearchForm = resetSearchForm;
window.openNewKnowledgeModal = openNewKnowledgeModal;
window.closeNewKnowledgeModal = closeNewKnowledgeModal;
window.openNewConsultModal = openNewConsultModal;
window.closeNewConsultModalFallback = closeNewConsultModalFallback;
window.openNotificationPanel = openNotificationPanel;
window.closeNotificationPanel = closeNotificationPanel;
window.openSettingsPanel = openSettingsPanel;
window.closeSettingsPanel = closeSettingsPanel;
window.approveSelected = approveSelected;
window.rejectSelected = rejectSelected;
window.filterKnowledgeByCategory = filterKnowledgeByCategory;
window.filterProjectsByType = filterProjectsByType;
window.filterExpertsByField = filterExpertsByField;
window.toggleSection = toggleSection;
window.toggleSidebar = toggleSidebar;

// ============================================================
// PWA (Progressive Web App) Support
// ============================================================

/**
 * PWA Feature Detection
 * Check browser support for PWA features
 */
const PWA_FEATURES = {
  serviceWorker: 'serviceWorker' in navigator,
  backgroundSync: 'serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype,
  pushNotifications: 'serviceWorker' in navigator && 'PushManager' in window,
  installPrompt: 'BeforeInstallPromptEvent' in window,
  cacheAPI: 'caches' in window,
  indexedDB: 'indexedDB' in window
};

// Export globally for testing
window.PWA_FEATURES = PWA_FEATURES;

logger.log('[PWA] Feature detection:', PWA_FEATURES);

/**
 * Service Worker Registration
 * Register after DOM is fully loaded
 */
if (PWA_FEATURES.serviceWorker) {
  // Wait for page load to ensure all resources are ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', registerServiceWorker);
  } else {
    registerServiceWorker();
  }
}

function registerServiceWorker() {
  logger.log('[PWA] Registering Service Worker...');

  navigator.serviceWorker.register('/sw.js', { scope: '/' })
    .then((registration) => {
      logger.log('[PWA] Service Worker registered successfully', registration);

      // Check for updates every 24 hours
      setInterval(() => {
        registration.update();
      }, 24 * 60 * 60 * 1000);

      // Listen for updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;

        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            // New version available
            showUpdatePrompt(newWorker);
          }
        });
      });
    })
    .catch((error) => {
      logger.error('[PWA] Service Worker registration failed:', error);
      logger.error('[PWA] Error details:', error.stack);
    });
}

/**
 * Show Update Prompt
 * Display notification when new version is available
 */
function showUpdatePrompt(newWorker) {
  const banner = document.createElement('div');
  banner.className = 'update-banner';
  banner.innerHTML = `
    <div class="update-content">
      <strong>新しいバージョンが利用可能です</strong>
      <button onclick="applyUpdate()">今すぐ更新</button>
      <button onclick="dismissUpdate()">後で</button>
    </div>
  `;
  document.body.appendChild(banner);

  window.applyUpdate = () => {
    newWorker.postMessage({ action: 'SKIP_WAITING' });
    banner.remove();

    // Reload page after activation
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      window.location.reload();
    });
  };

  window.dismissUpdate = () => {
    banner.remove();
  };
}

/**
 * Online/Offline Status Detection
 */
let isOnline = navigator.onLine;

window.addEventListener('online', () => {
  isOnline = true;
  logger.log('[PWA] Online');
  hideOfflineIndicator();
});

window.addEventListener('offline', () => {
  isOnline = false;
  logger.log('[PWA] Offline');
  showOfflineIndicator();
});

function showOfflineIndicator() {
  let indicator = document.getElementById('offline-indicator');
  if (!indicator) {
    indicator = document.createElement('div');
    indicator.id = 'offline-indicator';
    indicator.className = 'offline-indicator visible';
    indicator.innerHTML = '📡 オフラインモード - キャッシュされたコンテンツのみ利用可能';
    document.body.insertBefore(indicator, document.body.firstChild);
  }
  indicator.classList.add('visible');
}

function hideOfflineIndicator() {
  const indicator = document.getElementById('offline-indicator');
  if (indicator) {
    indicator.classList.remove('visible');
    setTimeout(() => {
      indicator.remove();
    }, 300);
  }
}

// Show offline indicator if already offline
if (!isOnline) {
  showOfflineIndicator();
}

/**
 * Cache Access Tracking (for LRU management)
 */
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.addEventListener('message', async (event) => {
    if (event.data.type === 'CACHE_ACCESS') {
      // Track cache access for LRU eviction
      // This will be handled by cache-manager.js when loaded
      if (window.CacheManager) {
        const cacheManager = new CacheManager();
        await cacheManager.trackAccess(event.data.url);
        await cacheManager.evictIfNeeded();
      }
    }
  });
}

logger.log('[PWA] Initialization complete');
