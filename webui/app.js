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

// ユーザー情報表示
function displayUserInfo() {
  const user = getCurrentUser();
  console.log('[AUTH] Displaying user info:', user);
  if (!user) return;

  // ヘッダーにユーザー情報を表示
  const userInfoElement = document.querySelector('.user-info');
  if (userInfoElement) {
    userInfoElement.innerHTML = `
      <span class="user-name">${user.full_name || user.username}</span>
      <span class="user-dept">${user.department || ''}</span>
      <button class="logout-btn" onclick="logout()">ログアウト</button>
    `;
  }
}

// ============================================================
// API クライアント
// ============================================================

// 動的にAPIベースURLを設定（localhost、IPアドレス、ホスト名に対応）
const API_BASE = `${window.location.protocol}//${window.location.hostname}:${window.location.port || '5000'}/api/v1`;

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

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers
    });

    console.log('[API] Response status:', response.status);

    // 認証エラー（401）の場合はログイン画面へ
    if (response.status === 401) {
      console.log('[API] 401 Unauthorized. Token expired or invalid, redirecting to login...');
      logout();
      throw new Error('Authentication failed');
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

  panel.innerHTML = knowledgeList.map(k => `
    <div class="knowledge-card">
      <h4>${k.title}</h4>
      <div class="knowledge-meta">
        最終更新: ${formatDate(k.updated_at)} · ${k.category} · 工区: ${k.project || 'N/A'} · 担当: ${k.owner}
      </div>
      <div class="knowledge-tags">
        ${k.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
      </div>
      <div>${k.summary}</div>
    </div>
  `).join('');
}

function displaySOPs(sopList) {
  const panel = document.querySelector('[data-panel="sop"]');
  if (!panel) return;

  panel.innerHTML = sopList.map(sop => `
    <div class="knowledge-card">
      <h4>${sop.title}</h4>
      <div class="knowledge-meta">
        改訂: ${formatDate(sop.revision_date)} · ${sop.category} · ${sop.target}
      </div>
      <div class="knowledge-tags">
        ${sop.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
      </div>
      <div>${sop.content}</div>
    </div>
  `).join('');
}

function displayIncidents(incidentList) {
  const panel = document.querySelector('[data-panel="incident"]');
  if (!panel) return;

  panel.innerHTML = incidentList.map(incident => `
    <div class="knowledge-card">
      <h4>${incident.title}</h4>
      <div class="knowledge-meta">
        報告日: ${formatDate(incident.date)} · 現場: ${incident.project}
      </div>
      <div class="knowledge-tags">
        ${incident.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
      </div>
      <div>${incident.description}</div>
    </div>
  `).join('');
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

  flowContainer.innerHTML = approvalList.slice(0, 3).map(approval => `
    <div class="flow-step">
      <div>${approval.title}</div>
      <span class="badge ${statusBadgeClass[approval.status] || 'is-info'}">
        ${statusText[approval.status] || approval.status}
      </span>
    </div>
  `).join('');
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
