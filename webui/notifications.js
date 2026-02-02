// ============================================================
// 通知UI専用スクリプト
// ============================================================

/**
 * 未読通知数を取得してバッジを更新
 */
async function loadUnreadNotificationCount() {
  try {
    const result = await fetchAPI('/notifications/unread/count');
    if (result.success) {
      updateNotificationBadge(result.data.unread_count);
    }
  } catch (error) {
    logger.error('[NOTIFICATION] Failed to load unread count:', error);
  }
}

/**
 * 通知一覧を取得して表示
 */
async function loadNotifications(status = null) {
  try {
    const endpoint = status ? `/notifications?status=${status}` : '/notifications';
    const result = await fetchAPI(endpoint);
    if (result.success) {
      displayNotifications(result.data);
      updateNotificationBadge(result.pagination.unread_count);
    }
  } catch (error) {
    logger.error('[NOTIFICATION] Failed to load notifications:', error);
  }
}

/**
 * 通知バッジ（未読数）を更新
 */
function updateNotificationBadge(count) {
  const badge = document.querySelector('.notification-badge');
  if (badge) {
    if (count > 0) {
      badge.textContent = count > 99 ? '99+' : count;
      badge.style.display = 'inline-block';
    } else {
      badge.style.display = 'none';
    }
  }
}

/**
 * 通知を既読にマーク
 */
async function markNotificationAsRead(notificationId) {
  try {
    await fetchAPI(`/notifications/${notificationId}/read`, { method: 'PUT' });
    loadNotifications(); // リロード
  } catch (error) {
    logger.error('[NOTIFICATION] Failed to mark as read:', error);
  }
}

/**
 * 通知一覧を表示
 */
function displayNotifications(notifications) {
  const panel = document.querySelector('.notifications-panel');
  if (!panel) return;

  // パネルをクリア（XSS対策）
  panel.textContent = '';

  if (notifications.length === 0) {
    const emptyDiv = document.createElement('div');
    emptyDiv.className = 'no-notifications';
    emptyDiv.textContent = '通知はありません';
    panel.appendChild(emptyDiv);
    return;
  }

  const notificationTypeIcons = {
    'approval_required': '📋',
    'approval_completed': '✅',
    'incident_reported': '⚠️',
    'consultation_answered': '💬'
  };

  // 各通知アイテムを安全に作成（XSS対策: innerHTML → DOM API使用）
  notifications.forEach(n => {
    const item = document.createElement('div');
    item.className = `notification-item ${n.is_read ? 'read' : 'unread'}`;
    item.dataset.id = n.id;
    item.onclick = () => handleNotificationClick(n.id);

    // アイコン
    const iconDiv = document.createElement('div');
    iconDiv.className = 'notification-icon';
    iconDiv.textContent = notificationTypeIcons[n.type] || '📢';
    item.appendChild(iconDiv);

    // コンテンツ
    const contentDiv = document.createElement('div');
    contentDiv.className = 'notification-content';

    const titleDiv = document.createElement('div');
    titleDiv.className = 'notification-title';
    titleDiv.textContent = n.title;
    contentDiv.appendChild(titleDiv);

    const messageDiv = document.createElement('div');
    messageDiv.className = 'notification-message';
    messageDiv.textContent = n.message;
    contentDiv.appendChild(messageDiv);

    const timeDiv = document.createElement('div');
    timeDiv.className = 'notification-time';
    timeDiv.textContent = formatRelativeTime(n.created_at);
    contentDiv.appendChild(timeDiv);

    item.appendChild(contentDiv);

    // 未読ドット
    if (!n.is_read) {
      const dotSpan = document.createElement('span');
      dotSpan.className = 'unread-dot';
      item.appendChild(dotSpan);
    }

    panel.appendChild(item);
  });
}

/**
 * 通知クリック処理
 */
function handleNotificationClick(notificationId) {
  markNotificationAsRead(notificationId);
  // 関連エンティティへのナビゲーションも可能（今後実装）
}

/**
 * 通知パネルの表示/非表示切替
 */
function toggleNotificationPanel() {
  const panel = document.querySelector('.notifications-panel');
  if (!panel) return;

  if (panel.style.display === 'none' || panel.style.display === '') {
    loadNotifications();
    panel.style.display = 'block';
  } else {
    panel.style.display = 'none';
  }
}

/**
 * 相対時間フォーマット（「3分前」「2時間前」など）
 */
function formatRelativeTime(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return 'たった今';
  if (diffMins < 60) return `${diffMins}分前`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}時間前`;

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}日前`;

  return formatDate(dateString);
}

/**
 * HTMLエスケープ（XSS対策）
 */
function escapeHtml(unsafe) {
  if (unsafe === null || unsafe === undefined) return '';
  return String(unsafe)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ============================================================
// 定期ポーリング（5分ごとに未読通知数を更新）
// ============================================================

setInterval(() => {
  loadUnreadNotificationCount();
}, 5 * 60 * 1000);

// 初期化時に未読通知数をロード
document.addEventListener('DOMContentLoaded', () => {
  loadUnreadNotificationCount();
});


// ============================================================
// MKSApp.Notifications Namespace - 通知機能
// ============================================================

if (typeof window.MKSApp === 'undefined') {
  window.MKSApp = {};
}

/**
 * 通知機能を統一Namespace配下に整理
 */
window.MKSApp.Notifications = {
  updateBadge: updateNotificationBadge,
  display: displayNotifications,
  handleClick: handleNotificationClick,
  togglePanel: toggleNotificationPanel,
  formatRelativeTime: formatRelativeTime
};

// ============================================================
// 互換性レイヤー
// ============================================================
window.updateNotificationBadge = updateNotificationBadge;
window.displayNotifications = displayNotifications;
window.handleNotificationClick = handleNotificationClick;
window.toggleNotificationPanel = toggleNotificationPanel;
window.formatRelativeTime = formatRelativeTime;

if (typeof logger !== 'undefined') {
  logger.log('[MKSApp.Notifications] Namespace initialized with', Object.keys(window.MKSApp.Notifications).length, 'functions');
}

