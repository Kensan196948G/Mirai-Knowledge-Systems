// ============================================================
// 認証管理
// ============================================================

// 認証チェック
function checkAuth() {
  const token = localStorage.getItem('access_token');
  console.log('[AUTH] Checking authentication. Token exists:', token ? 'YES' : 'NO');
  if (!token) {
    console.log('[AUTH] No token found. Redirecting to login...');
    window.location.href = '/login.html';
    return false;
  }
  console.log('[AUTH] Token found. Length:', token.length);
  return true;
}

// ログアウト
function logout() {
  console.log('[AUTH] Logging out...');
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
      console.error('[AUTH] Failed to parse user data:', e);
      return null;
    }
  }
  return null;
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
 * RBAC UI制御を適用
 * data-permission属性とdata-role属性を持つ要素の表示/非表示を制御
 */
function applyRBACUI() {
  const user = getCurrentUser();
  if (!user) return;

  console.log('[RBAC] Applying UI controls for user:', user.username);

  // data-permission属性を持つ要素を制御
  document.querySelectorAll('[data-permission]').forEach(element => {
    const requiredPermission = element.dataset.permission;
    const hasAccess = hasPermission(requiredPermission);

    if (!hasAccess) {
      // 権限がない場合は非表示または無効化
      if (element.tagName === 'BUTTON') {
        element.disabled = true;
        element.style.opacity = '0.5';
        element.title = '権限がありません';
      } else {
        element.style.display = 'none';
      }
      console.log('[RBAC] Access denied to element:', requiredPermission);
    }
  });

  // data-role属性を持つ要素を制御
  document.querySelectorAll('[data-role]').forEach(element => {
    const allowedRoles = element.dataset.role.split(',');
    const userRoles = user.roles || [];
    const hasRole = allowedRoles.some(role => userRoles.includes(role.trim()));

    if (!hasRole) {
      element.style.display = 'none';
      console.log('[RBAC] Role access denied:', allowedRoles);
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
  console.log('[AUTH] Displaying user info:', user);
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
const API_BASE = `${window.location.protocol}//${window.location.hostname}:${window.location.port || '5000'}/api/v1`;

/**
 * トークンリフレッシュ関数
 * リフレッシュトークンを使用して新しいアクセストークンを取得
 */
async function refreshAccessToken() {
  const refreshToken = localStorage.getItem('refresh_token');

  if (!refreshToken) {
    console.log('[AUTH] No refresh token available');
    return false;
  }

  try {
    console.log('[AUTH] Refreshing access token...');
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
        console.log('[AUTH] Access token refreshed successfully');
        return true;
      }
    }

    console.log('[AUTH] Token refresh failed');
    return false;
  } catch (error) {
    console.error('[AUTH] Token refresh error:', error);
    return false;
  }
}

async function fetchAPI(endpoint, options = {}) {
  const token = localStorage.getItem('access_token');

  console.log('[API] Calling:', endpoint);
  console.log('[API] Token exists:', token ? 'YES' : 'NO');

  if (!token && !endpoint.includes('/auth/')) {
    console.log('[API] No token for non-auth endpoint. Redirecting...');
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
      console.log('[API] Authorization header added');
    }

    let response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers
    });

    console.log('[API] Response status:', response.status);

    // 認証エラー（401）の場合、トークンリフレッシュを試行
    if (response.status === 401 && !endpoint.includes('/auth/')) {
      console.log('[API] 401 Unauthorized. Attempting token refresh...');

      const refreshed = await refreshAccessToken();

      if (refreshed) {
        // リフレッシュ成功 → リクエストをリトライ
        console.log('[API] Retrying request with new token...');
        const newToken = localStorage.getItem('access_token');
        headers['Authorization'] = `Bearer ${newToken}`;

        response = await fetch(`${API_BASE}${endpoint}`, {
          ...options,
          headers
        });

        console.log('[API] Retry response status:', response.status);
      } else {
        // リフレッシュ失敗 → ログアウト
        console.log('[API] Token refresh failed. Logging out...');
        logout();
        throw new Error('Authentication failed');
      }
    }

    // 権限エラー（403）
    if (response.status === 403) {
      console.error('[API] 403 Forbidden.');
      alert('この操作を実行する権限がありません。');
      throw new Error('Permission denied');
    }

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('[API] Error:', error);
    throw error;
  }
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
    console.error('Failed to load dashboard stats:', error);
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
    console.error('Failed to load knowledge:', error);
  }
}

async function loadSOPs() {
  try {
    const result = await fetchAPI('/sop');
    if (result.success) {
      displaySOPs(result.data);
    }
  } catch (error) {
    console.error('Failed to load SOPs:', error);
  }
}

async function loadIncidents() {
  try {
    const result = await fetchAPI('/incidents');
    if (result.success) {
      displayIncidents(result.data);
    }
  } catch (error) {
    console.error('Failed to load incidents:', error);
  }
}

async function loadApprovals() {
  try {
    const result = await fetchAPI('/approvals');
    if (result.success) {
      displayApprovals(result.data);
    }
  } catch (error) {
    console.error('Failed to load approvals:', error);
  }
}

// ============================================================
// データ表示関数
// ============================================================

function updateDashboardStats(stats) {
  const metricCards = document.querySelectorAll('.metric-card');
  if (metricCards.length >= 4) {
    metricCards[0].querySelector('strong').textContent = `${stats.knowledge_reuse_rate}%`;
    metricCards[1].querySelector('strong').textContent = `${stats.accident_free_days}日`;
    metricCards[2].querySelector('strong').textContent = `${stats.active_audits}現場`;
    metricCards[3].querySelector('strong').textContent = `${stats.delayed_corrections}件`;
  }
}

function displayKnowledge(knowledgeList) {
  const panel = document.querySelector('[data-panel="search"]');
  if (!panel) return;

  // パネルをクリア（XSS対策）
  panel.textContent = '';

  // 各ナレッジカードを安全に作成
  knowledgeList.forEach(k => {
    const card = createElement('div', {className: 'knowledge-card'}, []);

    // カードクリックで詳細画面へ遷移
    card.style.cursor = 'pointer';
    card.onclick = () => {
      // 詳細データをlocalStorageに保存
      localStorage.setItem('knowledge_detail', JSON.stringify(k));
      window.location.href = 'search-detail.html';
    };

    // タイトル
    const title = createElement('h4', {}, [k.title || '']);
    card.appendChild(title);

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

  // 各SOPカードを安全に作成
  sopList.forEach(sop => {
    const card = createElement('div', {className: 'knowledge-card'}, []);

    // カードクリックでSOP詳細画面へ遷移
    card.style.cursor = 'pointer';
    card.onclick = () => {
      localStorage.setItem('sop_detail', JSON.stringify(sop));
      window.location.href = 'sop-detail.html';
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

  // 各事故レポートカードを安全に作成
  incidentList.forEach(incident => {
    const card = createElement('div', {className: 'knowledge-card'}, []);

    // カードクリックで事故レポート詳細画面へ遷移
    card.style.cursor = 'pointer';
    card.onclick = () => {
      localStorage.setItem('incident_detail', JSON.stringify(incident));
      window.location.href = 'incident-detail.html';
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

// ============================================================
// ユーティリティ関数
// ============================================================

function formatDate(dateString) {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return `${date.getFullYear()}/${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')}`;
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
// タブ切替機能（既存のコードと統合）
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
// トグルボタン機能（既存のコードと統合）
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
// プログレスバーアニメーション（既存のコードと統合）
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
// 新規ナレッジ登録モーダル
// ============================================================

async function showNewKnowledgeModal() {
  const title = prompt('ナレッジタイトルを入力してください:');
  if (!title) return;

  const summary = prompt('概要を入力してください:');
  if (!summary) return;

  const category = prompt('カテゴリを入力してください（施工計画/品質/安全衛生など）:');
  if (!category) return;

  try {
    const result = await fetchAPI('/knowledge', {
      method: 'POST',
      body: JSON.stringify({
        title,
        summary,
        content: summary,
        category,
        tags: [],
        owner: 'ユーザー'
      })
    });

    if (result.success) {
      alert('ナレッジを登録しました！');
      loadKnowledge();
    }
  } catch (error) {
    alert('登録に失敗しました: ' + error.message);
  }
}

// ============================================================
// 新規登録ボタンのセットアップ
// ============================================================

function setupNewKnowledgeButton() {
  const newKnowledgeButtons = document.querySelectorAll('.cta');
  newKnowledgeButtons.forEach(btn => {
    if (btn.textContent.includes('新規ナレッジ登録')) {
      btn.addEventListener('click', showNewKnowledgeModal);
    }
  });
}

// ============================================================
// 初期化
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  console.log('建設土木ナレッジシステム - 初期化中...');

  // 認証チェック
  if (!checkAuth()) {
    return; // 認証失敗時は処理を中断
  }

  // ユーザー情報表示
  displayUserInfo();

  // RBAC UI制御を適用
  applyRBACUI();

  // 検索機能のセットアップ
  setupSearch();

  // 新規登録ボタンのセットアップ
  setupNewKnowledgeButton();

  // 初期データのロード
  loadDashboardStats();
  loadKnowledge();
  loadApprovals();

  console.log('初期化完了！');
});
