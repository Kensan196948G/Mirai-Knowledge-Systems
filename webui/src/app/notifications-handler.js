/**
 * @fileoverview 通知処理モジュール v2.0.0
 * @module app/notifications-handler
 * @description Phase F-4: app.js 分割版 - 通知処理
 *
 * 担当機能:
 * - 通知一覧取得 (loadNotifications)
 * - 通知既読処理 (markNotificationAsRead / markAllNotificationsAsRead)
 * - 通知バッジ更新 (updateNotificationBadge)
 * - MFA 設定管理 (loadMFAStatus / startMFASetup / verifyAndEnableMFA / disableMFA / closeMFASetupModal)
 */

// ============================================================
// 通知取得・既読管理
// ============================================================

/**
 * 通知一覧を取得
 * @returns {Promise<Array>} 通知データ配列
 */
async function loadNotifications() {
  const log = window.logger || console;
  try {
    const result = await fetchAPI('/notifications');
    if (result && result.success) {
      if (typeof updateNotificationBadge === 'function') {
        updateNotificationBadge(result.data);
      }
      return result.data;
    }
  } catch (error) {
    log.error('Failed to load notifications:', error);
    return [];
  }
  return [];
}

/**
 * 通知を既読にする
 * @param {number|string} notificationId - 通知 ID
 */
async function markNotificationAsRead(notificationId) {
  const log = window.logger || console;
  try {
    const result = await fetchAPI(`/notifications/${notificationId}/read`, { method: 'PUT' });

    if (result && result.success) {
      if (typeof showNotification === 'function') {
        showNotification('通知を既読にしました', 'success');
      }
      const notifications = await loadNotifications();
      if (typeof displayNotifications === 'function') {
        displayNotifications(notifications);
      }
    }
  } catch (error) {
    log.error('Failed to mark notification as read:', error);
    if (typeof showNotification === 'function') {
      showNotification('通知の更新に失敗しました', 'error');
    }
  }
}

/**
 * 全通知を既読にする
 */
async function markAllNotificationsAsRead() {
  const log = window.logger || console;
  try {
    const result = await fetchAPI('/notifications/read-all', { method: 'PUT' });

    if (result && result.success) {
      if (typeof showNotification === 'function') {
        showNotification('全ての通知を既読にしました', 'success');
      }
      const notifications = await loadNotifications();
      if (typeof displayNotifications === 'function') {
        displayNotifications(notifications);
      }
    }
  } catch (error) {
    log.error('Failed to mark all notifications as read:', error);
    if (typeof showNotification === 'function') {
      showNotification('通知の更新に失敗しました', 'error');
    }
  }
}

/**
 * 通知バッジを更新（loadNotifications から委譲される場合もある）
 * @param {Array} notifications - 通知データ配列
 */
function getNotifications() {
  return loadNotifications();
}

/**
 * 既読にする（後方互換性エイリアス）
 * @param {number|string} id - 通知 ID
 */
function markAsRead(id) {
  return markNotificationAsRead(id);
}

// ============================================================
// MFA（2要素認証）設定
// ============================================================

/**
 * MFA 設定状態を読み込み
 */
async function loadMFAStatus() {
  const mfaStatus = document.getElementById('mfaStatus');
  const mfaSetupBtn = document.getElementById('mfaSetupBtn');
  const mfaDisableBtn = document.getElementById('mfaDisableBtn');

  if (!mfaStatus) return;

  const user = typeof getCurrentUser === 'function' ? getCurrentUser() : null;
  if (!user) return;

  const isEnabled = user.mfa_enabled || false;

  mfaStatus.textContent = isEnabled ? '有効' : '無効';
  mfaStatus.className = isEnabled ? 'mfa-status enabled' : 'mfa-status disabled';

  if (mfaSetupBtn) mfaSetupBtn.style.display = isEnabled ? 'none' : 'inline-block';
  if (mfaDisableBtn) mfaDisableBtn.style.display = isEnabled ? 'inline-block' : 'none';
}

/**
 * MFA セットアップ開始
 */
async function startMFASetup() {
  const log = window.logger || console;
  const modal = document.getElementById('mfaSetupModal');
  const qrcodeContainer = document.getElementById('mfaQRCode');
  const secretDisplay = document.getElementById('mfaSecretKey');

  if (!modal) return;

  try {
    if (typeof showNotification === 'function') {
      showNotification('MFAセットアップを開始しています...', 'info');
    }

    const result = await fetchAPI('/auth/mfa/setup', { method: 'POST' });

    if (!result || !result.success) {
      if (typeof showNotification === 'function') {
        showNotification(result?.error?.message || 'MFAセットアップに失敗しました', 'error');
      }
      return;
    }

    if (qrcodeContainer) {
      qrcodeContainer.textContent = '';
      if (typeof QRCode !== 'undefined') {
        new QRCode(qrcodeContainer, {
          text: result.data.provisioning_uri,
          width: 200,
          height: 200
        });
      } else {
        const uriText = document.createElement('p');
        uriText.className = 'mfa-uri-text';
        uriText.textContent = '認証アプリで以下のURIを手動入力してください:';

        const uriCode = document.createElement('code');
        uriCode.className = 'mfa-uri-code';
        uriCode.textContent = result.data.provisioning_uri;

        qrcodeContainer.appendChild(uriText);
        qrcodeContainer.appendChild(uriCode);
      }
    }

    if (secretDisplay) {
      secretDisplay.textContent = result.data.secret;
    }

    modal.style.display = 'flex';
  } catch (error) {
    log.error('[MFA] Setup error:', error);
    if (typeof showNotification === 'function') {
      showNotification('MFAセットアップに失敗しました', 'error');
    }
  }
}

/**
 * MFA 有効化（コード検証）
 */
async function verifyAndEnableMFA() {
  const log = window.logger || console;
  const codeInput = document.getElementById('mfaVerifyCode');
  const code = codeInput?.value.trim();

  if (!code || !/^\d{6}$/.test(code)) {
    if (typeof showNotification === 'function') {
      showNotification('6桁の認証コードを入力してください', 'error');
    }
    return;
  }

  try {
    const result = await fetchAPI('/auth/mfa/verify', {
      method: 'POST',
      body: JSON.stringify({ code })
    });

    if (result && result.success) {
      if (typeof showNotification === 'function') {
        showNotification('2要素認証が有効になりました', 'success');
      }

      const user = typeof getCurrentUser === 'function' ? getCurrentUser() : {};
      if (user) {
        user.mfa_enabled = true;
        localStorage.setItem('user', JSON.stringify(user));
      }

      closeMFASetupModal();
      loadMFAStatus();
    } else {
      if (typeof showNotification === 'function') {
        showNotification(result?.error?.message || '認証コードが正しくありません', 'error');
      }
      if (codeInput) {
        codeInput.value = '';
        codeInput.focus();
      }
    }
  } catch (error) {
    log.error('[MFA] Verify error:', error);
    if (typeof showNotification === 'function') {
      showNotification('認証に失敗しました', 'error');
    }
  }
}

/**
 * MFA 無効化
 */
async function disableMFA() {
  const log = window.logger || console;

  if (!confirm('2要素認証を無効にしますか?\nセキュリティが低下する可能性があります。')) {
    return;
  }

  try {
    const result = await fetchAPI('/auth/mfa/disable', { method: 'POST' });

    if (result && result.success) {
      if (typeof showNotification === 'function') {
        showNotification('2要素認証を無効にしました', 'success');
      }

      const user = typeof getCurrentUser === 'function' ? getCurrentUser() : {};
      if (user) {
        user.mfa_enabled = false;
        localStorage.setItem('user', JSON.stringify(user));
      }

      loadMFAStatus();
    } else {
      if (typeof showNotification === 'function') {
        showNotification(result?.error?.message || 'MFA無効化に失敗しました', 'error');
      }
    }
  } catch (error) {
    log.error('[MFA] Disable error:', error);
    if (typeof showNotification === 'function') {
      showNotification('MFA無効化に失敗しました', 'error');
    }
  }
}

/**
 * MFA セットアップモーダルを閉じる
 */
function closeMFASetupModal() {
  const modal = document.getElementById('mfaSetupModal');
  if (modal) modal.style.display = 'none';

  const codeInput = document.getElementById('mfaVerifyCode');
  if (codeInput) codeInput.value = '';
}

// ============================================================
// グローバル公開
// ============================================================

window.loadNotifications = loadNotifications;
window.markNotificationAsRead = markNotificationAsRead;
window.markAllNotificationsAsRead = markAllNotificationsAsRead;
window.getNotifications = getNotifications;
window.markAsRead = markAsRead;
window.loadMFAStatus = loadMFAStatus;
window.startMFASetup = startMFASetup;
window.verifyAndEnableMFA = verifyAndEnableMFA;
window.disableMFA = disableMFA;
window.closeMFASetupModal = closeMFASetupModal;

export {
  loadNotifications,
  markNotificationAsRead,
  markAllNotificationsAsRead,
  getNotifications,
  markAsRead,
  loadMFAStatus,
  startMFASetup,
  verifyAndEnableMFA,
  disableMFA,
  closeMFASetupModal
};
