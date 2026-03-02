/**
 * @fileoverview データ読み込みモジュール v2.0.0
 * @module app/data-loader
 * @description Phase F-4: app.js 分割版 - データ読み込み処理
 *
 * 担当機能:
 * - ダッシュボード統計 (loadDashboardStats)
 * - モニタリングデータ (loadMonitoringData)
 * - ナレッジ一覧 (loadKnowledge)
 * - SOP 一覧 (loadSOPs)
 * - 事故レポート一覧 (loadIncidents)
 * - 承認一覧 (loadApprovals)
 * - 人気ナレッジ (loadPopularKnowledge)
 * - 最近のナレッジ (loadRecentKnowledge)
 * - お気に入りナレッジ (loadFavoriteKnowledge)
 * - タグクラウド (loadTagCloud)
 * - プロジェクト一覧 (loadProjects)
 * - 専門家一覧 (loadExperts)
 * - プロジェクト進捗 (loadProjectProgress)
 * - 専門家統計 (loadExpertStats)
 * - 表示関数 (displayKnowledge, displaySOPs, displayIncidents, displayApprovals, etc.)
 */

// ============================================================
// ダッシュボード統計
// ============================================================

/**
 * ダッシュボード統計データを取得して表示を更新
 */
async function loadDashboardStats() {
  const log = window.logger || console;
  try {
    const result = await fetchAPI('/dashboard/stats');
    if (result && result.success) {
      if (typeof updateDashboardStats === 'function') {
        updateDashboardStats(result.data);
      }
    }
  } catch (error) {
    log.log('[DASHBOARD] Using static data (API unavailable)');
  }
}

// ============================================================
// モニタリングデータ
// ============================================================

/**
 * プロジェクトモニタリングデータを取得して表示
 */
async function loadMonitoringData() {
  const log = window.logger || console;
  try {
    const projectsResult = await fetchAPI('/projects');
    if (projectsResult && projectsResult.success && projectsResult.data.length > 0) {
      const monitoringSection = document.querySelector('.progress-list');
      if (monitoringSection) {
        const DH = window.DOMHelper;
        if (DH) DH.clearChildren(monitoringSection);

        const targetProjects = projectsResult.data.slice(0, 3);
        const progressResults = await Promise.all(
          targetProjects.map(project => fetchAPI(`/projects/${project.id}/progress`))
        );

        targetProjects.forEach((project, index) => {
          const progressResult = progressResults[index];
          if (progressResult && progressResult.success) {
            const progressData = progressResult.data;

            const progressItem = document.createElement('div');
            progressItem.className = 'progress-item';
            progressItem.setAttribute('data-progress', progressData.progress_percentage);

            const title = document.createElement('div');
            title.className = 'progress-title';
            title.textContent = project.name;

            const track = document.createElement('div');
            track.className = 'progress-track';
            const fill = document.createElement('span');
            fill.className = 'progress-fill';
            fill.style.width = `${progressData.progress_percentage}%`;
            track.appendChild(fill);

            const meta = document.createElement('div');
            meta.className = 'progress-meta';
            const span1 = document.createElement('span');
            span1.textContent = `工程 ${progressData.progress_percentage}%`;
            const span2 = document.createElement('span');
            span2.textContent = `予定 ${Math.max(0, progressData.progress_percentage - 3)}%`;
            meta.appendChild(span1);
            meta.appendChild(span2);

            progressItem.appendChild(title);
            progressItem.appendChild(track);
            progressItem.appendChild(meta);
            monitoringSection.appendChild(progressItem);
          }
        });
      }
    }
  } catch (error) {
    log.log('[MONITORING] Using static data (API unavailable)');
  }
}

// ============================================================
// ナレッジ一覧
// ============================================================

/**
 * ナレッジ一覧を取得して表示
 * @param {Object} [params={}] - クエリパラメータ
 */
async function loadKnowledge(params = {}) {
  const log = window.logger || console;
  const queryParams = new URLSearchParams(params).toString();
  const endpoint = `/knowledge${queryParams ? '?' + queryParams : ''}`;

  try {
    const result = await fetchAPI(endpoint);
    if (result && result.success) {
      displayKnowledge(result.data);
    }
  } catch (error) {
    log.log('[KNOWLEDGE] Using static data (API unavailable)');
  }
}

/**
 * ナレッジ一覧を DOM に表示
 * @param {Array} knowledgeList - ナレッジデータ配列
 */
function displayKnowledge(knowledgeList) {
  const panel = document.querySelector('[data-panel="search"]');
  if (!panel) return;

  panel.textContent = '';

  if (!_checkAndShowEmptyState(knowledgeList, panel, 'ナレッジ')) return;

  knowledgeList.forEach(k => {
    const card = document.createElement('div');
    card.className = 'knowledge-card';
    if (k.title && k.title.includes('[サンプル]')) {
      card.style.borderLeft = '3px solid #f59e0b';
    }

    const cardHeader = document.createElement('div');
    cardHeader.className = 'knowledge-card-header';
    cardHeader.style.cssText = 'display: flex; justify-content: space-between; align-items: flex-start;';

    const title = document.createElement('h4');
    title.textContent = k.title || '';
    title.style.cursor = 'pointer';
    title.style.flex = '1';
    title.onclick = (e) => {
      e.stopPropagation();
      window.location.href = `search-detail.html?id=${k.id}`;
    };
    cardHeader.appendChild(title);

    const actionButtons = document.createElement('div');
    actionButtons.className = 'knowledge-actions';
    actionButtons.style.cssText = 'display: flex; gap: 8px;';

    const creatorId = k.owner_id || k.owner || k.created_by;
    if (typeof canEdit === 'function' && canEdit(creatorId)) {
      const editBtn = document.createElement('button');
      editBtn.className = 'cta ghost small';
      editBtn.style.cssText = 'font-size: 12px; padding: 4px 8px;';
      editBtn.textContent = '編集';
      editBtn.onclick = (e) => {
        e.stopPropagation();
        if (typeof editKnowledge === 'function') editKnowledge(k.id, creatorId);
      };
      actionButtons.appendChild(editBtn);
    }

    cardHeader.appendChild(actionButtons);
    card.appendChild(cardHeader);

    const formatDate = window.formatDate || ((d) => d || 'N/A');

    const meta = document.createElement('div');
    meta.className = 'knowledge-meta';
    meta.textContent = `最終更新: ${formatDate(k.updated_at)} · ${k.category} · 工区: ${k.project || 'N/A'} · 担当: ${k.owner}`;
    card.appendChild(meta);

    if (k.tags && k.tags.length > 0) {
      const tagsContainer = document.createElement('div');
      tagsContainer.className = 'knowledge-tags';
      k.tags.forEach(tag => {
        const tagSpan = document.createElement('span');
        tagSpan.className = 'tag';
        tagSpan.textContent = tag;
        tagsContainer.appendChild(tagSpan);
      });
      card.appendChild(tagsContainer);
    }

    const summary = document.createElement('div');
    summary.textContent = k.summary || '';
    card.appendChild(summary);

    panel.appendChild(card);
  });
}

// ============================================================
// SOP 一覧
// ============================================================

/**
 * SOP 一覧を取得して表示
 */
async function loadSOPs() {
  const log = window.logger || console;
  try {
    const result = await fetchAPI('/sop');
    if (result && result.success) {
      displaySOPs(result.data);
    }
  } catch (error) {
    log.error('Failed to load SOPs:', error);
  }
}

/**
 * SOP 一覧を DOM に表示
 * @param {Array} sopList - SOP データ配列
 */
function displaySOPs(sopList) {
  const panel = document.querySelector('[data-panel="sop"]');
  if (!panel) return;

  panel.textContent = '';
  if (!_checkAndShowEmptyState(sopList, panel, '標準作業手順書')) return;

  const formatDate = window.formatDate || ((d) => d || 'N/A');

  sopList.forEach(sop => {
    const card = document.createElement('div');
    card.className = 'knowledge-card';
    if (sop.title && sop.title.includes('[サンプル]')) {
      card.style.borderLeft = '3px solid #f59e0b';
    }
    card.style.cursor = 'pointer';
    card.onclick = () => {
      window.location.href = `sop-detail.html?id=${sop.id}`;
    };

    const title = document.createElement('h4');
    title.textContent = sop.title || '';
    card.appendChild(title);

    const meta = document.createElement('div');
    meta.className = 'knowledge-meta';
    meta.textContent = `改訂: ${formatDate(sop.revision_date)} · ${sop.category} · ${sop.target}`;
    card.appendChild(meta);

    if (sop.tags && sop.tags.length > 0) {
      const tagsContainer = document.createElement('div');
      tagsContainer.className = 'knowledge-tags';
      sop.tags.forEach(tag => {
        const tagSpan = document.createElement('span');
        tagSpan.className = 'tag';
        tagSpan.textContent = tag;
        tagsContainer.appendChild(tagSpan);
      });
      card.appendChild(tagsContainer);
    }

    const content = document.createElement('div');
    content.textContent = sop.content || '';
    card.appendChild(content);

    panel.appendChild(card);
  });
}

// ============================================================
// 事故レポート一覧
// ============================================================

/**
 * 事故レポート一覧を取得して表示
 */
async function loadIncidents() {
  const log = window.logger || console;
  try {
    const result = await fetchAPI('/incidents');
    if (result && result.success) {
      displayIncidents(result.data);
    }
  } catch (error) {
    log.error('Failed to load incidents:', error);
  }
}

/**
 * 事故レポート一覧を DOM に表示
 * @param {Array} incidentList - 事故データ配列
 */
function displayIncidents(incidentList) {
  const panel = document.querySelector('[data-panel="incident"]');
  if (!panel) return;

  panel.textContent = '';
  if (!_checkAndShowEmptyState(incidentList, panel, '事故・ヒヤリハット')) return;

  const formatDate = window.formatDate || ((d) => d || 'N/A');

  incidentList.forEach(incident => {
    const card = document.createElement('div');
    card.className = 'knowledge-card';
    if (incident.title && incident.title.includes('[サンプル]')) {
      card.style.borderLeft = '3px solid #f59e0b';
    }
    card.style.cursor = 'pointer';
    card.onclick = () => {
      window.location.href = `incident-detail.html?id=${incident.id}`;
    };

    const title = document.createElement('h4');
    title.textContent = incident.title || '';
    card.appendChild(title);

    const meta = document.createElement('div');
    meta.className = 'knowledge-meta';
    meta.textContent = `報告日: ${formatDate(incident.date)} · 現場: ${incident.project}`;
    card.appendChild(meta);

    if (incident.tags && incident.tags.length > 0) {
      const tagsContainer = document.createElement('div');
      tagsContainer.className = 'knowledge-tags';
      incident.tags.forEach(tag => {
        const tagSpan = document.createElement('span');
        tagSpan.className = 'tag';
        tagSpan.textContent = tag;
        tagsContainer.appendChild(tagSpan);
      });
      card.appendChild(tagsContainer);
    }

    const description = document.createElement('div');
    description.textContent = incident.description || '';
    card.appendChild(description);

    panel.appendChild(card);
  });
}

// ============================================================
// 承認一覧
// ============================================================

/**
 * 承認一覧を取得して表示
 */
async function loadApprovals() {
  const log = window.logger || console;
  try {
    const result = await fetchAPI('/approvals');
    if (result && result.success) {
      displayApprovals(result.data);
    }
  } catch (error) {
    log.log('[APPROVALS] Using static data (API unavailable)');
  }
}

/**
 * 承認一覧を DOM に表示
 * @param {Array} approvalList - 承認データ配列
 */
function displayApprovals(approvalList) {
  const flowContainer = document.querySelector('.flow');
  if (!flowContainer) return;

  if (!_checkAndShowEmptyState(approvalList, flowContainer, '承認待ち')) return;

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

  flowContainer.textContent = '';

  approvalList.slice(0, 3).forEach(approval => {
    const flowStep = document.createElement('div');
    flowStep.className = 'flow-step';

    const titleDiv = document.createElement('div');
    titleDiv.textContent = approval.title || '';
    flowStep.appendChild(titleDiv);

    const badgeClass = statusBadgeClass[approval.status] || 'is-info';
    const badge = document.createElement('span');
    badge.className = `badge ${badgeClass}`;
    badge.textContent = statusText[approval.status] || approval.status;
    flowStep.appendChild(badge);

    flowContainer.appendChild(flowStep);
  });
}

// ============================================================
// 通知バッジ
// ============================================================

/**
 * 通知バッジを更新
 * @param {Array} notifications - 通知データ配列
 */
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
// サイドバーデータ
// ============================================================

/**
 * 人気ナレッジを取得して表示
 * @param {string} [category=''] - カテゴリフィルター
 */
async function loadPopularKnowledge(category = '') {
  const log = window.logger || console;
  const container = document.getElementById('popularKnowledgeList');
  if (!container) return;

  container.textContent = '';

  try {
    const result = await fetchAPI('/knowledge/popular?limit=10');

    if (!result || !result.success || !result.data || result.data.length === 0) {
      const emptyMsg = document.createElement('div');
      emptyMsg.className = 'empty-message';
      emptyMsg.textContent = '人気ナレッジデータなし';
      container.appendChild(emptyMsg);
      return;
    }

    let filteredData = result.data;
    if (category) {
      filteredData = filteredData.filter(k => k.category === category);
    }

    filteredData.forEach((item, index) => {
      const navItem = document.createElement('div');
      navItem.className = 'nav-item clickable';
      navItem.onclick = () => {
        if (typeof viewKnowledgeDetail === 'function') viewKnowledgeDetail(item.id);
      };

      const rank = document.createElement('span');
      rank.className = 'rank';
      rank.textContent = `${index + 1}`;

      const title = document.createElement('strong');
      title.textContent = item.title;

      const views = document.createElement('span');
      views.className = 'meta';
      views.textContent = `${item.views || 0} views`;

      navItem.appendChild(rank);
      navItem.appendChild(title);
      navItem.appendChild(views);
      container.appendChild(navItem);
    });
  } catch (error) {
    log.error('[KNOWLEDGE] Failed to load popular knowledge:', error);
    const errorMsg = document.createElement('div');
    errorMsg.className = 'empty-message';
    errorMsg.textContent = '読み込みエラー';
    container.appendChild(errorMsg);
  }
}

/**
 * 最近追加されたナレッジを取得して表示
 * @param {string} [category=''] - カテゴリフィルター
 */
async function loadRecentKnowledge(category = '') {
  const log = window.logger || console;
  const container = document.getElementById('recentKnowledgeList');
  if (!container) return;

  container.textContent = '';

  try {
    const result = await fetchAPI('/knowledge/recent?limit=10&days=7');

    if (!result || !result.success || !result.data || result.data.length === 0) {
      const emptyMsg = document.createElement('div');
      emptyMsg.className = 'empty-message';
      emptyMsg.textContent = '最近のナレッジデータなし';
      container.appendChild(emptyMsg);
      return;
    }

    let filteredData = result.data;
    if (category) {
      filteredData = filteredData.filter(k => k.category === category);
    }

    filteredData.forEach(item => {
      const navItem = document.createElement('div');
      navItem.className = 'nav-item clickable';
      navItem.onclick = () => {
        if (typeof viewKnowledgeDetail === 'function') viewKnowledgeDetail(item.id);
      };

      const title = document.createElement('strong');
      title.textContent = item.title;

      let daysAgo = '?';
      if (item.created_at) {
        try {
          const created = new Date(item.created_at);
          const now = new Date();
          daysAgo = Math.floor(Math.abs(now - created) / (1000 * 60 * 60 * 24));
        } catch (e) { /* ignore */ }
      }

      const meta = document.createElement('span');
      meta.className = 'meta';
      meta.textContent = `${daysAgo}日前`;

      navItem.appendChild(title);
      navItem.appendChild(meta);
      container.appendChild(navItem);
    });
  } catch (error) {
    log.error('[KNOWLEDGE] Failed to load recent knowledge:', error);
    const errorMsg = document.createElement('div');
    errorMsg.className = 'empty-message';
    errorMsg.textContent = '読み込みエラー';
    container.appendChild(errorMsg);
  }
}

/**
 * お気に入りナレッジを取得して表示
 */
async function loadFavoriteKnowledge() {
  const log = window.logger || console;
  const container = document.getElementById('favoriteKnowledgeList');
  if (!container) return;

  container.textContent = '';

  try {
    const result = await fetchAPI('/knowledge/favorites');

    if (!result || !result.success || !result.data || result.data.length === 0) {
      const emptyMsg = document.createElement('div');
      emptyMsg.className = 'empty-message';
      emptyMsg.textContent = 'お気に入りはありません';
      container.appendChild(emptyMsg);
      return;
    }

    result.data.forEach(item => {
      const navItem = document.createElement('div');
      navItem.className = 'nav-item clickable';
      navItem.onclick = () => {
        if (typeof viewKnowledgeDetail === 'function') viewKnowledgeDetail(item.id);
      };

      const title = document.createElement('strong');
      title.textContent = item.title;

      const removeFav = document.createElement('button');
      removeFav.className = 'icon-btn-small';
      removeFav.textContent = '★';
      removeFav.onclick = (e) => {
        e.stopPropagation();
        if (typeof removeFavorite === 'function') removeFavorite(item.id);
      };

      navItem.appendChild(title);
      navItem.appendChild(removeFav);
      container.appendChild(navItem);
    });
  } catch (error) {
    log.error('[KNOWLEDGE] Failed to load favorites:', error);
    const emptyMsg = document.createElement('div');
    emptyMsg.className = 'empty-message';
    emptyMsg.textContent = 'お気に入りはありません';
    container.appendChild(emptyMsg);
  }
}

/**
 * タグクラウドを取得して表示
 */
async function loadTagCloud() {
  const log = window.logger || console;
  const container = document.getElementById('tagCloud');
  if (!container) return;

  container.textContent = '';

  try {
    const result = await fetchAPI('/knowledge/tags');

    if (!result || !result.success || !result.data || result.data.length === 0) {
      const emptyMsg = document.createElement('div');
      emptyMsg.className = 'empty-message';
      emptyMsg.textContent = 'タグデータなし';
      container.appendChild(emptyMsg);
      return;
    }

    result.data.slice(0, 20).forEach(tag => {
      const tagBtn = document.createElement('button');
      tagBtn.className = `tag-btn tag-${tag.size || 1}`;
      tagBtn.textContent = `${tag.name} (${tag.count})`;
      tagBtn.onclick = () => {
        if (typeof filterByTag === 'function') filterByTag(tag.name);
      };
      container.appendChild(tagBtn);
    });
  } catch (error) {
    log.error('[KNOWLEDGE] Failed to load tags:', error);
    const errorMsg = document.createElement('div');
    errorMsg.className = 'empty-message';
    errorMsg.textContent = 'タグデータなし';
    container.appendChild(errorMsg);
  }
}

/**
 * プロジェクト一覧を取得して表示
 * @param {string} [type=''] - プロジェクトタイプフィルター
 */
async function loadProjects(type = '') {
  const log = window.logger || console;
  const container = document.getElementById('projectsList');
  if (!container) return;

  container.textContent = '';

  try {
    const result = await fetchAPI('/projects', { method: 'GET' });
    if (!result || !result.success) throw new Error('Failed to load projects');

    let filteredData = Array.isArray(result.data) ? result.data : [];
    if (type) filteredData = filteredData.filter(p => p.type === type);

    const IS_PRODUCTION = window.IS_PRODUCTION || false;
    if (!filteredData.length && !IS_PRODUCTION && window.DUMMY_PROJECTS) {
      filteredData = window.DUMMY_PROJECTS;
    }

    if (!filteredData.length) {
      const emptyMsg = document.createElement('div');
      emptyMsg.className = 'empty-message';
      emptyMsg.textContent = 'プロジェクトデータなし';
      container.appendChild(emptyMsg);
      return;
    }

    filteredData.forEach(async (project) => {
      const projectItem = document.createElement('div');
      projectItem.className = 'project-item';

      const header = document.createElement('div');
      header.className = 'project-header clickable';
      header.onclick = () => {
        if (typeof toggleProjectDetail === 'function') toggleProjectDetail(project.id);
      };

      const projectCode = project.code || project.project_code || project.id || '';
      const projectName = project.name || project.title || 'プロジェクト';
      const nameLabel = projectCode ? `${projectName} (${projectCode})` : projectName;

      const name = document.createElement('strong');
      name.textContent = nameLabel;

      const chevron = document.createElement('span');
      chevron.className = 'chevron-small';
      chevron.id = `chevron-${project.id}`;
      chevron.textContent = '▼';

      header.appendChild(name);
      header.appendChild(chevron);
      projectItem.appendChild(header);

      const progressPercentage = project.progress_percentage ?? project.progress ?? 0;
      const progressBar = document.createElement('div');
      progressBar.className = 'mini-progress';
      const progressFill = document.createElement('div');
      progressFill.className = 'mini-progress-fill';
      progressFill.style.width = `${progressPercentage}%`;
      progressBar.appendChild(progressFill);
      projectItem.appendChild(progressBar);

      const progressText = document.createElement('div');
      progressText.className = 'progress-text';
      progressText.textContent = `進捗 ${progressPercentage}%`;
      projectItem.appendChild(progressText);

      // リアルタイム進捗更新
      try {
        const progressResult = await fetchAPI(`/projects/${project.id}/progress`);
        if (progressResult && progressResult.success) {
          progressFill.style.width = `${progressResult.data.progress_percentage}%`;
          progressText.textContent = `進捗 ${progressResult.data.progress_percentage}%`;
        }
      } catch (e) {
        log.log(`[PROJECTS] Failed to load progress for ${project.id}:`, e);
      }

      const details = document.createElement('div');
      details.className = 'project-details';
      details.id = `details-${project.id}`;
      details.style.display = 'none';

      const phaseValue = project.phase || project.work_section || project.work_type || '未設定';
      const managerValue = project.manager || project.owner || project.members?.[0]?.name || '未設定';
      const milestoneValue = project.milestone || project.milestones?.[0]?.title || '未設定';

      [
        { label: '工区:', value: phaseValue },
        { label: '担当:', value: managerValue },
        { label: 'マイルストーン:', value: milestoneValue }
      ].forEach(row => {
        const detailRow = document.createElement('div');
        detailRow.className = 'detail-row';
        const labelSpan = document.createElement('span');
        labelSpan.className = 'detail-label';
        labelSpan.textContent = row.label;
        const valueSpan = document.createElement('span');
        valueSpan.textContent = row.value;
        detailRow.appendChild(labelSpan);
        detailRow.appendChild(valueSpan);
        details.appendChild(detailRow);
      });

      projectItem.appendChild(details);
      container.appendChild(projectItem);
    });
  } catch (error) {
    log.error('[PROJECTS] Failed to load projects:', error);
    const emptyMsg = document.createElement('div');
    emptyMsg.className = 'empty-message';
    emptyMsg.textContent = 'プロジェクトデータなし';
    container.appendChild(emptyMsg);
  }
}

/**
 * 専門家一覧を取得して表示
 * @param {string} [field=''] - 専門分野フィルター
 */
async function loadExperts(field = '') {
  const log = window.logger || console;
  const container = document.getElementById('expertsList');
  if (!container) return;

  container.textContent = '';

  try {
    const result = await fetchAPI('/experts', { method: 'GET' });
    if (!result || !result.success) throw new Error('Failed to load experts');

    let filteredData = Array.isArray(result.data) ? result.data : [];
    if (field) {
      filteredData = filteredData.filter(e =>
        (e.specialization || e.field || e.specialties?.[0]) === field
      );
    }

    const IS_PRODUCTION = window.IS_PRODUCTION || false;
    if (!filteredData.length && !IS_PRODUCTION && window.DUMMY_EXPERTS) {
      filteredData = window.DUMMY_EXPERTS;
    }

    if (!filteredData.length) {
      const emptyMsg = document.createElement('div');
      emptyMsg.className = 'empty-message';
      emptyMsg.textContent = '専門家データなし';
      container.appendChild(emptyMsg);
      return;
    }

    filteredData.forEach(async (expert) => {
      const expertItem = document.createElement('div');
      expertItem.className = 'expert-item';

      const header = document.createElement('div');
      header.className = 'expert-header';

      const isAvailable = expert.is_available ?? expert.online ?? false;
      const consultationCount = expert.consultation_count ?? expert.answer_count ?? 0;
      const rating = expert.rating ?? expert.average_rating ?? 0;
      const specializationValue = expert.specialization || expert.field || expert.specialties?.[0] || '未設定';

      const statusDot = document.createElement('span');
      statusDot.className = `status-dot ${isAvailable ? 'is-ok' : 'is-muted'}`;

      const name = document.createElement('strong');
      name.textContent = expert.name || `Expert ${expert.id}`;

      const specialization = document.createElement('span');
      specialization.className = 'meta';
      specialization.textContent = specializationValue;

      header.appendChild(statusDot);
      header.appendChild(name);
      header.appendChild(specialization);
      expertItem.appendChild(header);

      const info = document.createElement('div');
      info.className = 'expert-info';

      const answersRow = document.createElement('div');
      answersRow.className = 'info-row';
      answersRow.textContent = `回答数: ${consultationCount}件 · 評価: ⭐${rating}`;

      const availableRow = document.createElement('div');
      availableRow.className = 'info-row small';
      availableRow.textContent = `対応可能: ${isAvailable ? 'はい' : 'いいえ'}`;

      info.appendChild(answersRow);
      info.appendChild(availableRow);
      expertItem.appendChild(info);

      const consultBtn = document.createElement('button');
      consultBtn.className = 'cta ghost small';
      consultBtn.style.cssText = 'margin-top: 8px; width: 100%;';
      consultBtn.textContent = '相談する';
      consultBtn.onclick = () => {
        if (typeof consultExpert === 'function') consultExpert(expert.id);
      };
      expertItem.appendChild(consultBtn);

      container.appendChild(expertItem);
    });
  } catch (error) {
    log.error('[EXPERTS] Failed to load experts:', error);
    const emptyMsg = document.createElement('div');
    emptyMsg.className = 'empty-message';
    emptyMsg.textContent = '専門家データなし';
    container.appendChild(emptyMsg);
  }
}

// ============================================================
// プロジェクト・専門家リアルタイム更新
// ============================================================

/**
 * プロジェクト進捗を取得してリアルタイム更新
 * @param {string} projectId - プロジェクト ID
 */
async function loadProjectProgress(projectId) {
  const log = window.logger || console;
  try {
    const result = await fetchAPI(`/projects/${projectId}/progress`);
    if (result && result.success) {
      if (typeof updateProjectProgress === 'function') {
        updateProjectProgress(projectId, result.data);
      }
      return result.data;
    }
  } catch (error) {
    log.error('[PROJECT] Failed to load progress:', error);
  }
  return null;
}

/**
 * 専門家統計を取得してリアルタイム更新
 */
async function loadExpertStats() {
  const log = window.logger || console;
  try {
    const result = await fetchAPI('/experts/stats');
    if (result && result.success) {
      if (typeof updateExpertStats === 'function') updateExpertStats(result.data);
      if (typeof updateDutyExperts === 'function') updateDutyExperts(result.data);
    }
  } catch (error) {
    log.error('[EXPERTS] Failed to load expert stats:', error);
  }
}

/**
 * お気に入りから削除
 * @param {number|string} knowledgeId - ナレッジ ID
 */
async function removeFavorite(knowledgeId) {
  const log = window.logger || console;
  log.log('[SIDEBAR] Removing favorite:', knowledgeId);

  try {
    const result = await fetchAPI(`/favorites/${knowledgeId}`, { method: 'DELETE' });
    if (result && result.success) {
      if (typeof showNotification === 'function') {
        showNotification('お気に入りから削除しました', 'success');
      }
      loadFavoriteKnowledge();
    }
  } catch (error) {
    log.error('[FAVORITES] Failed to remove:', error);
    if (typeof showNotification === 'function') {
      showNotification('お気に入りの削除に失敗しました', 'error');
    }
  }
}

/**
 * 専門家に相談
 * @param {number|string} expertId - 専門家 ID
 */
function consultExpert(expertId) {
  const log = window.logger || console;
  const DUMMY_EXPERTS = window.DUMMY_EXPERTS || [];
  const expert = DUMMY_EXPERTS.find(e => e.id === expertId);

  if (expert) {
    log.log('[SIDEBAR] Consulting expert:', expert.name);
    if (typeof showNotification === 'function') {
      showNotification(`${expert.name}さんへ相談画面を開きます`, 'info');
    }
    const consultData = JSON.parse(localStorage.getItem('consultations_details') || '[]');
    if (consultData.length > 0 && typeof viewConsultationDetail === 'function') {
      viewConsultationDetail(1);
    } else {
      window.location.href = 'expert-consult.html';
    }
  }
}

// ============================================================
// 内部ユーティリティ
// ============================================================

/**
 * データ存在チェックと空状態表示（内部用）
 * @private
 */
function _checkAndShowEmptyState(data, container, dataType) {
  if (typeof checkAndShowEmptyState === 'function') {
    return checkAndShowEmptyState(data, container, dataType);
  }
  if (!data || data.length === 0) {
    if (window.IS_PRODUCTION) {
      if (typeof showEmptyState === 'function') showEmptyState(container, dataType);
      return false;
    }
    return true;
  }
  return true;
}

// ============================================================
// グローバル公開
// ============================================================

window.loadDashboardStats = loadDashboardStats;
window.loadMonitoringData = loadMonitoringData;
window.loadKnowledge = loadKnowledge;
window.loadSOPs = loadSOPs;
window.loadIncidents = loadIncidents;
window.loadApprovals = loadApprovals;
window.displayKnowledge = displayKnowledge;
window.displaySOPs = displaySOPs;
window.displayIncidents = displayIncidents;
window.displayApprovals = displayApprovals;
window.updateNotificationBadge = updateNotificationBadge;
window.loadPopularKnowledge = loadPopularKnowledge;
window.loadRecentKnowledge = loadRecentKnowledge;
window.loadFavoriteKnowledge = loadFavoriteKnowledge;
window.loadTagCloud = loadTagCloud;
window.loadProjects = loadProjects;
window.loadExperts = loadExperts;
window.loadProjectProgress = loadProjectProgress;
window.loadExpertStats = loadExpertStats;
window.removeFavorite = removeFavorite;
window.consultExpert = consultExpert;

export {
  loadDashboardStats,
  loadMonitoringData,
  loadKnowledge,
  loadSOPs,
  loadIncidents,
  loadApprovals,
  displayKnowledge,
  displaySOPs,
  displayIncidents,
  displayApprovals,
  updateNotificationBadge,
  loadPopularKnowledge,
  loadRecentKnowledge,
  loadFavoriteKnowledge,
  loadTagCloud,
  loadProjects,
  loadExperts,
  loadProjectProgress,
  loadExpertStats,
  removeFavorite,
  consultExpert
};
