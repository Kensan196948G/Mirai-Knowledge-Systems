/**
 * @fileoverview イベントハンドラーモジュール v2.0.0
 * @module app/event-handlers
 * @description Phase F-4: app.js 分割版 - イベントハンドラー処理
 *
 * 担当機能:
 * - 検索機能セットアップ (setupSearch)
 * - イベントリスナー登録 (setupEventListeners)
 * - サイドパネルタブ (setupSidePanelTabs)
 * - タブ切替 (タブ btn クリック)
 * - トグルグループ制御
 * - プログレスバーアニメーション
 * - カードクリックハンドラー (setupCardClickHandlers)
 * - フォーム送信処理 (submitNewKnowledge, submitAdvancedSearch, performHeroSearch, etc.)
 */

// ============================================================
// 検索機能セットアップ
// ============================================================

/**
 * メイン検索バーのイベントリスナーを設定
 */
function setupSearch() {
  const searchInput = document.querySelector('.search input');
  const searchButton = document.querySelector('.search button');

  if (searchButton) {
    searchButton.addEventListener('click', () => {
      const query = searchInput ? searchInput.value : '';
      if (query && typeof loadKnowledge === 'function') {
        loadKnowledge({ search: query });
      }
    });
  }

  if (searchInput) {
    searchInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        const query = searchInput.value || '';
        if (query && typeof loadKnowledge === 'function') {
          loadKnowledge({ search: query });
        }
      }
    });
  }
}

// ============================================================
// イベントリスナー一括設定
// ============================================================

/**
 * アプリ全体のイベントリスナーを設定
 */
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

  // モーダル外側クリックで閉じる
  document.querySelectorAll('.modal, .side-panel').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.style.display = 'none';
        modal.classList.remove('open');
        document.body.style.overflow = '';
      }
    });
  });

  // タブ切替
  _setupTabSwitching();

  // トグルグループ
  _setupToggleGroups();

  // プログレスバーアニメーション
  _setupProgressBars();
}

/**
 * タブ切替イベントのセットアップ
 * @private
 */
function _setupTabSwitching() {
  const tabs = document.querySelectorAll('.tab-btn');
  const panels = document.querySelectorAll('.tab-panel');

  if (tabs.length && panels.length) {
    tabs.forEach((tab) => {
      tab.addEventListener('click', () => {
        const target = tab.dataset.tab;

        tabs.forEach((btn) => {
          const isActive = btn === tab;
          btn.classList.toggle('is-active', isActive);
          btn.setAttribute('aria-selected', String(isActive));
        });

        panels.forEach((panel) => {
          const isActive = panel.dataset.panel === target;
          panel.classList.toggle('is-active', isActive);
        });

        // タブ切替時にデータをロード
        if (target === 'search' && typeof loadKnowledge === 'function') {
          loadKnowledge();
        } else if (target === 'sop' && typeof loadSOPs === 'function') {
          loadSOPs();
        } else if (target === 'incident' && typeof loadIncidents === 'function') {
          loadIncidents();
        }
      });
    });
  }
}

/**
 * トグルグループのセットアップ
 * @private
 */
function _setupToggleGroups() {
  const toggleGroups = document.querySelectorAll('[data-toggle-group]');

  toggleGroups.forEach((group) => {
    const options = group.querySelectorAll('[data-toggle]');
    if (!options.length) return;

    options.forEach((option) => {
      if (!option.hasAttribute('aria-pressed')) {
        option.setAttribute('aria-pressed', String(option.classList.contains('is-active')));
      }

      option.addEventListener('click', () => {
        const mode = group.dataset.toggleGroup || 'single';

        if (mode === 'multi') {
          const isActive = option.classList.toggle('is-active');
          option.setAttribute('aria-pressed', String(isActive));
        } else {
          if (option.classList.contains('is-active')) return;
          options.forEach((btn) => {
            const isActive = btn === option;
            btn.classList.toggle('is-active', isActive);
            btn.setAttribute('aria-pressed', String(isActive));
          });
        }
      });
    });
  });
}

/**
 * プログレスバーのアニメーションセットアップ
 * @private
 */
function _setupProgressBars() {
  const progressItems = document.querySelectorAll('[data-progress]');

  progressItems.forEach((item) => {
    const fill = item.querySelector('.progress-fill');
    const value = Number(item.dataset.progress);
    if (!fill || Number.isNaN(value)) return;

    const safeValue = Math.min(100, Math.max(0, value));
    requestAnimationFrame(() => {
      fill.style.width = `${safeValue}%`;
    });
  });
}

// ============================================================
// サイドパネルタブ
// ============================================================

/**
 * サイドパネルのタブ切替イベントを設定
 */
function setupSidePanelTabs() {
  document.querySelectorAll('.side-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const panel = btn.closest('.side-panel');
      if (!panel) return;

      const tabName = btn.dataset.tab;

      panel.querySelectorAll('.side-tab-btn').forEach(b => {
        b.classList.toggle('is-active', b === btn);
      });

      // 設定パネルのセクション切替
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
    });
  });
}

// ============================================================
// カードクリックハンドラー
// ============================================================

/**
 * メインコンテンツのカードにクリックイベントを追加
 */
function setupCardClickHandlers() {
  const log = window.logger || console;
  log.log('[SETUP] Setting up card click handlers...');

  const panelMap = {
    'panel-search': 'knowledge',
    'panel-sop': 'sop',
    'panel-incident': 'incident'
  };

  Object.entries(panelMap).forEach(([panelId, type]) => {
    const panel = document.getElementById(panelId);
    if (!panel) return;

    const cards = panel.querySelectorAll('.knowledge-card');
    cards.forEach((card, index) => {
      card.style.cursor = 'pointer';
      card.style.transition = 'all 0.2s';

      card.addEventListener('mouseenter', () => {
        card.style.transform = 'translateY(-2px)';
        card.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
      });

      card.addEventListener('mouseleave', () => {
        card.style.transform = 'translateY(0)';
        card.style.boxShadow = '';
      });

      card.addEventListener('click', () => {
        const itemId = index + 1;
        if (type === 'knowledge' && typeof viewKnowledgeDetail === 'function') {
          viewKnowledgeDetail(itemId);
        } else if (type === 'sop' && typeof viewSOPDetail === 'function') {
          viewSOPDetail(itemId);
        } else if (type === 'incident' && typeof viewIncidentDetail === 'function') {
          viewIncidentDetail(itemId);
        }
      });
    });

    log.log(`[SETUP] Added click handlers to ${cards.length} cards in ${panelId}`);
  });

  setupExpertClickHandlers();
}

/**
 * 当番エキスパートのクリックイベントを設定
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
        const consultId = index + 1;
        if (typeof viewConsultationDetail === 'function') {
          viewConsultationDetail(consultId);
        }
      });
    }
  });
}

// ============================================================
// フォーム送信処理
// ============================================================

/**
 * 新規ナレッジ登録フォームの送信
 * @param {Event} event - フォーム送信イベント
 */
async function submitNewKnowledge(event) {
  event.preventDefault();

  const log = window.logger || console;
  const form = event.target;
  const formData = new FormData(form);

  const data = {
    title: formData.get('title'),
    category: formData.get('category'),
    priority: formData.get('priority'),
    project: formData.get('project') || null,
    summary: formData.get('summary'),
    content: formData.get('content'),
    tags: formData.get('tags')
      ? formData.get('tags').split(',').map(t => t.trim()).filter(t => t)
      : []
  };

  try {
    const result = await fetchAPI('/knowledge', {
      method: 'POST',
      body: JSON.stringify(data)
    });

    if (result.success) {
      if (typeof showNotification === 'function') {
        showNotification('ナレッジを登録しました!', 'success');
      }
      if (typeof closeNewKnowledgeModal === 'function') {
        closeNewKnowledgeModal();
      }
      if (typeof loadKnowledge === 'function') {
        loadKnowledge();
      }
    }
  } catch (error) {
    log.error('Failed to create knowledge:', error);
    if (typeof showNotification === 'function') {
      showNotification('登録に失敗しました: ' + error.message, 'error');
    }
  }
}

/**
 * 高度な検索フォームの送信
 * @param {Event} event - フォーム送信イベント
 */
async function submitAdvancedSearch(event) {
  event.preventDefault();

  const log = window.logger || console;
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

  Object.keys(params).forEach(key => {
    if (!params[key]) delete params[key];
  });

  try {
    const queryParams = new URLSearchParams(params).toString();
    const result = await fetchAPI(`/knowledge/search?${queryParams}`);

    if (result.success) {
      if (typeof displaySearchResults === 'function') {
        displaySearchResults(result.data);
      }
      if (typeof showNotification === 'function') {
        showNotification(`${result.data.length}件の結果が見つかりました`, 'success');
      }
    }
  } catch (error) {
    log.error('Search failed:', error);
    if (typeof showNotification === 'function') {
      showNotification('検索に失敗しました', 'error');
    }
  }
}

/**
 * ヒーローセクションの検索を実行
 */
async function performHeroSearch() {
  const log = window.logger || console;
  const input = document.getElementById('heroSearchInput');
  if (!input) return;

  const keyword = input.value.trim();
  if (!keyword) {
    if (typeof showNotification === 'function') {
      showNotification('検索キーワードを入力してください', 'warning');
    }
    return;
  }

  try {
    const result = await fetchAPI(`/knowledge/search?keyword=${encodeURIComponent(keyword)}`);

    if (result.success) {
      const searchTab = document.querySelector('.tab-btn[data-tab="search"]');
      if (searchTab) {
        searchTab.click();
      }
      if (typeof displayKnowledge === 'function') {
        displayKnowledge(result.data);
      }
      if (typeof showNotification === 'function') {
        showNotification(`${result.data.length}件の結果が見つかりました`, 'success');
      }
    }
  } catch (error) {
    log.error('Hero search failed:', error);
    if (typeof showNotification === 'function') {
      showNotification('検索に失敗しました', 'error');
    }
  }
}

/**
 * ユーザー設定フォームの送信
 * @param {Event} event - フォーム送信イベント
 */
async function submitUserSettings(event) {
  event.preventDefault();

  const log = window.logger || console;
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
      const user = typeof getCurrentUser === 'function' ? getCurrentUser() : {};
      Object.assign(user, data);
      localStorage.setItem('user', JSON.stringify(user));
      if (typeof showNotification === 'function') {
        showNotification('設定を保存しました', 'success');
      }
      if (typeof displayUserInfo === 'function') {
        displayUserInfo();
      }
    }
  } catch (error) {
    log.error('Failed to update settings:', error);
    if (typeof showNotification === 'function') {
      showNotification('設定の保存に失敗しました', 'error');
    }
  }
}

/**
 * 通知設定フォームの送信
 * @param {Event} event - フォーム送信イベント
 */
function submitNotificationSettings(event) {
  event.preventDefault();

  const form = event.target;
  const formData = new FormData(form);

  localStorage.setItem('notify_approval', formData.get('notifyApproval') === 'on');
  localStorage.setItem('notify_knowledge', formData.get('notifyKnowledge') === 'on');
  localStorage.setItem('notify_incident', formData.get('notifyIncident') === 'on');
  localStorage.setItem('notify_email', formData.get('notifyEmail') === 'on');

  if (typeof showNotification === 'function') {
    showNotification('通知設定を保存しました', 'success');
  }
}

/**
 * 表示設定フォームの送信
 * @param {Event} event - フォーム送信イベント
 */
function submitDisplaySettings(event) {
  event.preventDefault();

  const form = event.target;
  const formData = new FormData(form);

  localStorage.setItem('items_per_page', formData.get('itemsPerPage'));
  localStorage.setItem('enable_animations', formData.get('enableAnimations') === 'on');
  localStorage.setItem('compact_mode', formData.get('compactMode') === 'on');

  if (typeof showNotification === 'function') {
    showNotification('表示設定を保存しました', 'success');
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
 * 検索結果を表示
 * @param {Array} results - 検索結果配列
 */
function displaySearchResults(results) {
  const resultsDiv = document.getElementById('searchResults');
  if (!resultsDiv) return;

  resultsDiv.textContent = '';

  if (!results || results.length === 0) {
    const emptyMsg = document.createElement('div');
    emptyMsg.className = 'empty-message';
    emptyMsg.textContent = '検索結果がありません';
    resultsDiv.appendChild(emptyMsg);
    return;
  }

  results.forEach(item => {
    const card = document.createElement('div');
    card.className = 'knowledge-card';
    card.style.cursor = 'pointer';
    card.onclick = () => {
      window.location.href = `search-detail.html?id=${item.id}`;
    };

    const title = document.createElement('h4');
    title.textContent = item.title || '';

    const meta = document.createElement('div');
    meta.className = 'knowledge-meta';
    const formatDate = window.formatDate || ((d) => d || 'N/A');
    meta.textContent = `${item.category} · ${formatDate(item.updated_at)}`;

    const summary = document.createElement('div');
    summary.textContent = item.summary || '';

    card.appendChild(title);
    card.appendChild(meta);
    card.appendChild(summary);

    resultsDiv.appendChild(card);
  });
}

// ============================================================
// フィルター操作
// ============================================================

/**
 * カテゴリフィルター
 * @param {string} category - カテゴリ名
 */
function filterKnowledgeByCategory(category) {
  if (typeof loadPopularKnowledge === 'function') loadPopularKnowledge(category);
  if (typeof loadRecentKnowledge === 'function') loadRecentKnowledge(category);
}

/**
 * プロジェクトタイプフィルター
 * @param {string} type - プロジェクトタイプ
 */
function filterProjectsByType(type) {
  if (typeof loadProjects === 'function') loadProjects(type);
}

/**
 * 専門分野フィルター
 * @param {string} field - 専門分野
 */
function filterExpertsByField(field) {
  if (typeof loadExperts === 'function') loadExperts(field);
}

/**
 * タグでフィルター
 * @param {string} tagName - タグ名
 */
function filterByTag(tagName) {
  const log = window.logger || console;
  log.log('[SIDEBAR] Filtering by tag:', tagName);
  if (typeof showNotification === 'function') {
    showNotification(`タグ「${tagName}」で検索します`, 'info');
  }
  if (typeof loadKnowledge === 'function') {
    loadKnowledge({ tags: tagName });
  }
}

// ============================================================
// グローバル公開
// ============================================================

window.setupSearch = setupSearch;
window.setupEventListeners = setupEventListeners;
window.setupSidePanelTabs = setupSidePanelTabs;
window.setupCardClickHandlers = setupCardClickHandlers;
window.setupExpertClickHandlers = setupExpertClickHandlers;
window.submitNewKnowledge = submitNewKnowledge;
window.submitAdvancedSearch = submitAdvancedSearch;
window.performHeroSearch = performHeroSearch;
window.submitUserSettings = submitUserSettings;
window.submitNotificationSettings = submitNotificationSettings;
window.submitDisplaySettings = submitDisplaySettings;
window.resetSearchForm = resetSearchForm;
window.displaySearchResults = displaySearchResults;
window.filterKnowledgeByCategory = filterKnowledgeByCategory;
window.filterProjectsByType = filterProjectsByType;
window.filterExpertsByField = filterExpertsByField;
window.filterByTag = filterByTag;

export {
  setupSearch,
  setupEventListeners,
  setupSidePanelTabs,
  setupCardClickHandlers,
  setupExpertClickHandlers,
  submitNewKnowledge,
  submitAdvancedSearch,
  performHeroSearch,
  submitUserSettings,
  submitNotificationSettings,
  submitDisplaySettings,
  resetSearchForm,
  displaySearchResults,
  filterKnowledgeByCategory,
  filterProjectsByType,
  filterExpertsByField,
  filterByTag
};
