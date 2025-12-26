// ============================================================
// 詳細画面共通スクリプト
// LocalStorageから詳細データを読み込んで表示
// ============================================================

/**
 * ナレッジ詳細データを表示
 */
function loadKnowledgeDetail() {
  const data = localStorage.getItem('knowledge_detail');
  if (!data) {
    alert('表示するデータがありません');
    window.location.href = 'index.html';
    return;
  }

  const knowledge = JSON.parse(data);

  // タイトル更新
  const titleElement = document.querySelector('.detail-hero h2');
  if (titleElement) {
    titleElement.textContent = knowledge.title;
  }

  // カテゴリバッジ
  const categoryElement = document.querySelector('.badge.is-info');
  if (categoryElement) {
    categoryElement.textContent = knowledge.category;
  }

  // メタ情報
  const metaElement = document.querySelector('.detail-meta');
  if (metaElement) {
    metaElement.innerHTML = `
      <span>工区: ${knowledge.project || 'N/A'}</span> ·
      <span>担当: ${knowledge.owner}</span> ·
      <span>最終更新: ${new Date(knowledge.updated_at).toLocaleDateString('ja-JP')}</span>
    `;
  }

  // タグ
  const tagsElement = document.querySelector('.detail-tags');
  if (tagsElement && knowledge.tags) {
    tagsElement.innerHTML = knowledge.tags.map(tag =>
      `<span class="tag">${tag}</span>`
    ).join('');
  }

  // コンテンツ
  const contentElement = document.querySelector('.detail-card');
  if (contentElement && knowledge.content) {
    const contentDiv = document.createElement('div');
    contentDiv.style.padding = '20px';
    contentDiv.style.lineHeight = '1.8';
    contentDiv.textContent = knowledge.content;
    contentElement.appendChild(contentDiv);
  }
}

/**
 * SOP詳細データを表示
 */
function loadSOPDetail() {
  const data = localStorage.getItem('sop_detail');
  if (!data) {
    alert('表示するデータがありません');
    window.location.href = 'index.html';
    return;
  }

  const sop = JSON.parse(data);

  // タイトル更新
  const titleElement = document.querySelector('.detail-hero h2');
  if (titleElement) {
    titleElement.textContent = sop.title;
  }

  // カテゴリバッジ
  const categoryElement = document.querySelector('.badge.is-info');
  if (categoryElement) {
    categoryElement.textContent = sop.category;
  }

  // メタ情報
  const metaElement = document.querySelector('.detail-meta');
  if (metaElement) {
    metaElement.innerHTML = `
      <span>対象: ${sop.target}</span> ·
      <span>バージョン: ${sop.version || 'v1.0'}</span> ·
      <span>改訂日: ${new Date(sop.revision_date).toLocaleDateString('ja-JP')}</span>
    `;
  }

  // タグ
  const tagsElement = document.querySelector('.detail-tags');
  if (tagsElement && sop.tags) {
    tagsElement.innerHTML = sop.tags.map(tag =>
      `<span class="tag">${tag}</span>`
    ).join('');
  }

  // コンテンツ
  const contentElement = document.querySelector('.detail-card');
  if (contentElement && sop.content) {
    const contentDiv = document.createElement('div');
    contentDiv.style.padding = '20px';
    contentDiv.style.lineHeight = '1.8';
    contentDiv.textContent = sop.content;
    contentElement.appendChild(contentDiv);
  }
}

/**
 * 事故レポート詳細データを表示
 */
function loadIncidentDetail() {
  const data = localStorage.getItem('incident_detail');
  if (!data) {
    alert('表示するデータがありません');
    window.location.href = 'index.html';
    return;
  }

  const incident = JSON.parse(data);

  // タイトル更新
  const titleElement = document.querySelector('.detail-hero h2');
  if (titleElement) {
    titleElement.textContent = incident.title;
  }

  // 重要度バッジ
  const severityBadge = document.querySelector('.badge');
  if (severityBadge) {
    const severityMap = {
      'critical': 'is-alert',
      'high': 'is-alert',
      'medium': 'is-wait',
      'low': 'is-info'
    };
    severityBadge.className = `badge ${severityMap[incident.severity] || 'is-info'}`;
    severityBadge.textContent = incident.severity.toUpperCase();
  }

  // メタ情報
  const metaElement = document.querySelector('.detail-meta');
  if (metaElement) {
    metaElement.innerHTML = `
      <span>現場: ${incident.project}</span> ·
      <span>報告者: ${incident.reporter}</span> ·
      <span>報告日: ${new Date(incident.date).toLocaleDateString('ja-JP')}</span>
    `;
  }

  // タグ
  const tagsElement = document.querySelector('.detail-tags');
  if (tagsElement && incident.tags) {
    tagsElement.innerHTML = incident.tags.map(tag =>
      `<span class="tag">${tag}</span>`
    ).join('');
  }

  // 説明
  const contentElement = document.querySelector('.detail-card');
  if (contentElement && incident.description) {
    const descDiv = document.createElement('div');
    descDiv.style.padding = '20px';
    descDiv.style.lineHeight = '1.8';
    descDiv.textContent = incident.description;
    contentElement.appendChild(descDiv);

    // 是正措置
    if (incident.corrective_actions && incident.corrective_actions.length > 0) {
      const actionsTitle = document.createElement('h3');
      actionsTitle.textContent = '是正措置';
      actionsTitle.style.marginTop = '30px';
      actionsTitle.style.padding = '0 20px';
      contentElement.appendChild(actionsTitle);

      const actionsList = document.createElement('ul');
      actionsList.style.padding = '0 20px 20px 40px';
      incident.corrective_actions.forEach(action => {
        const li = document.createElement('li');
        li.textContent = action;
        li.style.marginBottom = '10px';
        actionsList.appendChild(li);
      });
      contentElement.appendChild(actionsList);
    }
  }
}

// DOMContentLoaded時に適切なローダー関数を呼び出し
document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;

  if (path.includes('search-detail.html')) {
    loadKnowledgeDetail();
  } else if (path.includes('sop-detail.html')) {
    loadSOPDetail();
  } else if (path.includes('incident-detail.html')) {
    loadIncidentDetail();
  }
});
