// ============================================================
// SOP詳細ページ専用機能
// ============================================================

/**
 * チェックリストのインタラクションを初期化
 * チェック状態をlocalStorageに保存・復元
 */
function initializeChecklistInteraction() {
  const checklistEl = document.getElementById('sopChecklist');
  if (!checklistEl) return;

  const urlParams = new URLSearchParams(window.location.search);
  const sopId = urlParams.get('id');
  const checklistStateKey = `sop_checklist_${sopId}`;
  const savedState = JSON.parse(localStorage.getItem(checklistStateKey) || '{}');

  // すべてのチェックボックスにイベントリスナーを追加
  const checkboxes = checklistEl.querySelectorAll('input[type="checkbox"]');
  checkboxes.forEach((checkbox, index) => {
    // 保存された状態を復元
    if (savedState[index]) {
      checkbox.checked = true;
    }

    // data-index属性を追加
    checkbox.setAttribute('data-index', index);

    // changeイベントリスナー
    checkbox.addEventListener('change', (e) => {
      const idx = parseInt(e.target.dataset.index);
      savedState[idx] = e.target.checked;
      localStorage.setItem(checklistStateKey, JSON.stringify(savedState));
    });
  });
}

/**
 * 共有モーダルを閉じる
 */
function closeShareModal() {
  const modal = document.getElementById('shareModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

/**
 * URLをコピー
 */
function copyShareUrl() {
  const shareUrlEl = document.getElementById('shareUrl');
  if (shareUrlEl) {
    shareUrlEl.select();
    document.execCommand('copy');

    if (typeof showToast === 'function') {
      showToast('URLをコピーしました', 'success');
    } else if (typeof showNotification === 'function') {
      showNotification('URLをコピーしました', 'success');
    } else {
      alert('URLをコピーしました');
    }
  }
}

/**
 * メールで共有
 */
function shareViaEmail() {
  const url = window.location.href;
  const title = document.getElementById('sopTitle')?.textContent || 'SOP';
  const subject = encodeURIComponent(`${title} - SOP共有`);
  const body = encodeURIComponent(`以下のSOPを共有します:\n\n${title}\n\n${url}`);
  window.location.href = `mailto:?subject=${subject}&body=${body}`;

  if (typeof showToast === 'function') {
    showToast('メールクライアントを起動しました', 'info');
  }
}

/**
 * Slackで共有
 */
function shareViaSlack() {
  const url = window.location.href;
  const title = document.getElementById('sopTitle')?.textContent || 'SOP';
  const slackUrl = `https://slack.com/share?url=${encodeURIComponent(url)}&title=${encodeURIComponent(title)}`;
  window.open(slackUrl, '_blank', 'width=600,height=400');

  if (typeof showToast === 'function') {
    showToast('Slack共有ダイアログを開きました', 'info');
  }
}

/**
 * Teamsで共有
 */
function shareViaTeams() {
  const url = window.location.href;
  const title = document.getElementById('sopTitle')?.textContent || 'SOP';
  const teamsUrl = `https://teams.microsoft.com/share?href=${encodeURIComponent(url)}&msgText=${encodeURIComponent(title)}`;
  window.open(teamsUrl, '_blank', 'width=600,height=400');

  if (typeof showToast === 'function') {
    showToast('Teams共有ダイアログを開きました', 'info');
  }
}

/**
 * 適用現場を表示
 */
function displayApplicableSites(data) {
  const applicableSitesEl = document.getElementById('applicableSites');
  if (!applicableSitesEl) return;

  // 既存の内容をクリア
  while (applicableSitesEl.firstChild) {
    applicableSitesEl.removeChild(applicableSitesEl.firstChild);
  }

  if (data && data.applicable_sites) {
    if (Array.isArray(data.applicable_sites)) {
      data.applicable_sites.forEach(site => {
        const statusItem = document.createElement('div');
        statusItem.className = 'status-item';

        const dot = document.createElement('span');
        dot.className = 'status-dot active';
        statusItem.appendChild(dot);

        const siteSpan = document.createElement('span');
        siteSpan.textContent = site;
        statusItem.appendChild(siteSpan);

        applicableSitesEl.appendChild(statusItem);
      });
    } else {
      const statusItem = document.createElement('div');
      statusItem.className = 'status-item';

      const dot = document.createElement('span');
      dot.className = 'status-dot active';
      statusItem.appendChild(dot);

      const siteSpan = document.createElement('span');
      siteSpan.textContent = data.applicable_sites;
      statusItem.appendChild(siteSpan);

      applicableSitesEl.appendChild(statusItem);
    }
  } else {
    const statusItem = document.createElement('div');
    statusItem.className = 'status-item';

    const dot = document.createElement('span');
    dot.className = 'status-dot active';
    statusItem.appendChild(dot);

    const siteSpan = document.createElement('span');
    siteSpan.textContent = '全現場';
    statusItem.appendChild(siteSpan);

    applicableSitesEl.appendChild(statusItem);
  }
}

/**
 * モーダル外クリックで閉じる機能を追加
 */
function setupModalClickOutside() {
  const shareModal = document.getElementById('shareModal');
  const editModal = document.getElementById('editSOPModal');

  if (shareModal) {
    shareModal.addEventListener('click', (e) => {
      if (e.target === shareModal) {
        closeShareModal();
      }
    });
  }

  if (editModal) {
    editModal.addEventListener('click', (e) => {
      if (e.target === editModal) {
        closeEditSOPModal();
      }
    });
  }
}

/**
 * ページロード時の初期化
 */
document.addEventListener('DOMContentLoaded', function() {
  // チェックリストのインタラクションを初期化
  // SOPデータ読み込み後に実行されるように少し遅延
  setTimeout(() => {
    initializeChecklistInteraction();
  }, 500);

  // モーダルのクリック外で閉じる機能を設定
  setupModalClickOutside();
});
