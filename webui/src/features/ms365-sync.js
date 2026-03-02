/**
 * @fileoverview Microsoft 365 同期機能モジュール v2.0.0
 * @module features/ms365-sync
 * @description Phase F-2 ESモジュール化版
 *   webui/ms365-sync.js をESM形式に変換。
 *   - 同期設定 CRUD
 *   - 同期即時実行 / 接続テスト
 *   - 同期履歴・統計・ステータス取得
 *   - UI レンダリング関数（DOM API 使用、innerHTML 禁止）
 *   - ユーティリティ（cron フォーマット、秒数フォーマット等）
 */

import { fetchAPI } from '../core/api-client.js';
import { logger } from '../core/logger.js';

// ============================================================
// モジュール内部ステート
// ============================================================

/** @type {string|null} 編集中の設定ID */
let _editingConfigId = null;

/** @type {Array} 全設定キャッシュ */
let _allConfigs = [];

// ============================================================
// 認証チェック
// ============================================================

/**
 * 認証チェック。未認証の場合はログインページへリダイレクト
 * @returns {boolean} 認証済みの場合は true
 */
export async function checkAuth() {
  const token = localStorage.getItem('access_token');
  if (!token) {
    alert('ログインが必要です');
    window.location.href = 'login.html';
    return false;
  }
  return true;
}

// ============================================================
// API 呼び出し関数
// ============================================================

/**
 * 同期設定一覧を取得
 * @returns {Promise<Object>} 設定一覧レスポンス
 */
export async function loadSyncConfigs() {
  try {
    const data = await fetchAPI('/api/v1/integrations/microsoft365/sync/configs');
    logger.debug('[MS365] Sync configs loaded:', data);
    return data;
  } catch (error) {
    logger.error('[MS365] Failed to load sync configs:', error);
    throw error;
  }
}

/**
 * 同期設定を作成
 * @param {Object} configData - 設定データ
 * @returns {Promise<Object>} 作成結果レスポンス
 */
export async function createSyncConfig(configData) {
  try {
    const data = await fetchAPI('/api/v1/integrations/microsoft365/sync/configs', {
      method: 'POST',
      body: JSON.stringify(configData)
    });
    logger.debug('[MS365] Sync config created:', data);
    return data;
  } catch (error) {
    logger.error('[MS365] Failed to create sync config:', error);
    throw error;
  }
}

/**
 * 同期設定を更新
 * @param {string} configId - 設定ID
 * @param {Object} configData - 更新データ
 * @returns {Promise<Object>} 更新結果レスポンス
 */
export async function updateSyncConfig(configId, configData) {
  try {
    const data = await fetchAPI(`/api/v1/integrations/microsoft365/sync/configs/${configId}`, {
      method: 'PUT',
      body: JSON.stringify(configData)
    });
    logger.debug('[MS365] Sync config updated:', configId);
    return data;
  } catch (error) {
    logger.error('[MS365] Failed to update sync config:', error);
    throw error;
  }
}

/**
 * 同期設定を削除
 * @param {string} configId - 設定ID
 * @returns {Promise<Object>} 削除結果レスポンス
 */
export async function deleteSyncConfig(configId) {
  try {
    const data = await fetchAPI(`/api/v1/integrations/microsoft365/sync/configs/${configId}`, {
      method: 'DELETE'
    });
    logger.debug('[MS365] Sync config deleted:', configId);
    return data;
  } catch (error) {
    logger.error('[MS365] Failed to delete sync config:', error);
    throw error;
  }
}

/**
 * 同期を即時実行
 * @param {string} configId - 設定ID
 * @returns {Promise<Object>} 実行結果レスポンス
 */
export async function executeSyncNow(configId) {
  try {
    const data = await fetchAPI(`/api/v1/integrations/microsoft365/sync/configs/${configId}/execute`, {
      method: 'POST'
    });
    logger.debug('[MS365] Sync executed for config:', configId);
    return data;
  } catch (error) {
    logger.error('[MS365] Failed to execute sync:', error);
    throw error;
  }
}

/**
 * 接続テストを実行
 * @param {string} configId - 設定ID
 * @returns {Promise<Object>} テスト結果レスポンス
 */
export async function testSyncConfig(configId) {
  try {
    const data = await fetchAPI(`/api/v1/integrations/microsoft365/sync/configs/${configId}/test`, {
      method: 'POST'
    });
    logger.debug('[MS365] Connection test completed for config:', configId);
    return data;
  } catch (error) {
    logger.error('[MS365] Failed to test sync config:', error);
    throw error;
  }
}

/**
 * 同期履歴を取得
 * @param {string|null} [configId=null] - フィルターする設定ID（null で全件）
 * @param {number} [page=1] - ページ番号
 * @returns {Promise<Object>} 同期履歴レスポンス
 */
export async function loadSyncHistory(configId = null, page = 1) {
  let endpoint = `/api/v1/integrations/microsoft365/sync/history?page=${page}&per_page=20`;
  if (configId) {
    endpoint += `&config_id=${configId}`;
  }

  try {
    const data = await fetchAPI(endpoint);
    logger.debug('[MS365] Sync history loaded, page:', page);
    return data;
  } catch (error) {
    logger.error('[MS365] Failed to load sync history:', error);
    throw error;
  }
}

/**
 * 同期統計を取得
 * @returns {Promise<Object>} 統計レスポンス
 */
export async function loadSyncStats() {
  try {
    const data = await fetchAPI('/api/v1/integrations/microsoft365/sync/stats');
    logger.debug('[MS365] Sync stats loaded');
    return data;
  } catch (error) {
    logger.error('[MS365] Failed to load sync stats:', error);
    throw error;
  }
}

/**
 * スケジューラーステータスを取得
 * @returns {Promise<Object>} ステータスレスポンス
 */
export async function loadSyncStatus() {
  try {
    const data = await fetchAPI('/api/v1/integrations/microsoft365/sync/status');
    logger.debug('[MS365] Sync status loaded');
    return data;
  } catch (error) {
    logger.error('[MS365] Failed to load sync status:', error);
    throw error;
  }
}

/**
 * 全データを並列でロード
 * @returns {Promise<void>}
 */
export async function loadAllData() {
  try {
    const [configsResult, statsResult, statusResult] = await Promise.all([
      loadSyncConfigs().catch(err => {
        logger.error('[MS365] Failed to load configs:', err);
        return { success: false, data: [] };
      }),
      loadSyncStats().catch(err => {
        logger.error('[MS365] Failed to load stats:', err);
        return { success: false, data: {} };
      }),
      loadSyncStatus().catch(err => {
        logger.error('[MS365] Failed to load status:', err);
        return { success: false, data: {} };
      })
    ]);

    if (configsResult.success) {
      renderConfigList(configsResult.data);
    }

    renderStatusOverview(
      statsResult.success ? statsResult.data : {},
      statusResult.success ? statusResult.data : {}
    );

    await loadSyncHistoryWithFilter();
  } catch (error) {
    logger.error('[MS365] Failed to load all data:', error);
    showMessage('データの読み込みに失敗しました: ' + error.message, 'error');
  }
}

/**
 * フィルターを適用して履歴をロード
 * @returns {Promise<void>}
 */
export async function loadSyncHistoryWithFilter() {
  const configFilterEl = document.getElementById('historyConfigFilter');
  const statusFilterEl = document.getElementById('historyStatusFilter');
  const configFilter = configFilterEl ? configFilterEl.value : null;
  const statusFilter = statusFilterEl ? statusFilterEl.value : null;

  try {
    const result = await loadSyncHistory(configFilter || null);
    let history = result.success ? result.data : [];

    if (statusFilter) {
      history = history.filter(h => h.status === statusFilter);
    }

    renderSyncHistory(history);
  } catch (error) {
    logger.error('[MS365] Failed to load history with filter:', error);
    renderSyncHistory([]);
  }
}

// ============================================================
// UI レンダリング関数（DOM API 使用）
// ============================================================

/**
 * 設定一覧をレンダリング
 * @param {Array} configs - 設定の配列
 */
export function renderConfigList(configs) {
  _allConfigs = configs || [];
  const tbody = document.getElementById('configListBody');
  if (!tbody) return;

  tbody.textContent = '';

  if (!configs || configs.length === 0) {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 6;
    td.style.textAlign = 'center';
    td.style.padding = '40px';
    td.style.color = 'var(--muted)';
    td.textContent = '同期設定データがありません';
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }

  configs.forEach(config => {
    const tr = document.createElement('tr');

    const tdName = document.createElement('td');
    tdName.textContent = config.name || 'Unnamed';
    tr.appendChild(tdName);

    const tdSite = document.createElement('td');
    const siteText = document.createElement('div');
    siteText.style.fontSize = '12px';
    siteText.textContent = config.site_id ? config.site_id.substring(0, 30) + '...' : 'N/A';
    tdSite.appendChild(siteText);
    tr.appendChild(tdSite);

    const tdSchedule = document.createElement('td');
    tdSchedule.textContent = formatCronSchedule(config.sync_schedule || 'N/A');
    tdSchedule.style.fontSize = '13px';
    tr.appendChild(tdSchedule);

    const tdStatus = document.createElement('td');
    const statusBadge = document.createElement('span');
    statusBadge.className = config.is_enabled ? 'status-badge status-enabled' : 'status-badge status-disabled';
    statusBadge.textContent = config.is_enabled ? '有効' : '無効';
    tdStatus.appendChild(statusBadge);
    tr.appendChild(tdStatus);

    const tdLastSync = document.createElement('td');
    tdLastSync.textContent = config.last_sync_at ? formatDateTime(config.last_sync_at) : '未実行';
    tdLastSync.style.fontSize = '12px';
    tr.appendChild(tdLastSync);

    const tdActions = document.createElement('td');

    const testBtn = document.createElement('button');
    testBtn.className = 'action-btn';
    testBtn.textContent = 'テスト';
    testBtn.addEventListener('click', () => handleTestConfig(config.id));
    tdActions.appendChild(testBtn);

    const executeBtn = document.createElement('button');
    executeBtn.className = 'action-btn';
    executeBtn.textContent = '実行';
    executeBtn.addEventListener('click', () => handleExecuteSync(config.id));
    tdActions.appendChild(executeBtn);

    const editBtn = document.createElement('button');
    editBtn.className = 'action-btn';
    editBtn.textContent = '編集';
    editBtn.addEventListener('click', () => showEditConfigModal(config));
    tdActions.appendChild(editBtn);

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'action-btn danger';
    deleteBtn.textContent = '削除';
    deleteBtn.addEventListener('click', () => handleDeleteConfig(config.id, config.name));
    tdActions.appendChild(deleteBtn);

    tr.appendChild(tdActions);
    tbody.appendChild(tr);
  });

  updateHistoryConfigFilter(configs);
}

/**
 * 同期履歴をレンダリング
 * @param {Array} history - 履歴レコードの配列
 */
export function renderSyncHistory(history) {
  const tbody = document.getElementById('historyTableBody');
  if (!tbody) return;

  tbody.textContent = '';

  if (!history || history.length === 0) {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 6;
    td.style.textAlign = 'center';
    td.style.padding = '40px';
    td.style.color = 'var(--muted)';
    td.textContent = '同期履歴データがありません';
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }

  history.forEach(record => {
    const tr = document.createElement('tr');

    const tdStarted = document.createElement('td');
    tdStarted.textContent = formatDateTime(record.started_at || 'N/A');
    tdStarted.style.fontSize = '12px';
    tr.appendChild(tdStarted);

    const tdConfig = document.createElement('td');
    tdConfig.textContent = record.config_name || `設定ID: ${record.config_id}`;
    tr.appendChild(tdConfig);

    const tdStatus = document.createElement('td');
    const statusBadge = document.createElement('span');
    statusBadge.className = `status-badge status-${record.status || 'unknown'}`;
    statusBadge.textContent = getStatusLabel(record.status);
    tdStatus.appendChild(statusBadge);
    tr.appendChild(tdStatus);

    const tdFiles = document.createElement('td');
    tdFiles.textContent = record.files_processed || '0';
    tr.appendChild(tdFiles);

    const tdDuration = document.createElement('td');
    tdDuration.textContent = formatDuration(record.duration_seconds || 0);
    tdDuration.style.fontSize = '12px';
    tr.appendChild(tdDuration);

    const tdDetails = document.createElement('td');
    if (record.error_message) {
      const detailsBtn = document.createElement('button');
      detailsBtn.className = 'action-btn';
      detailsBtn.textContent = 'エラー詳細';
      detailsBtn.addEventListener('click', () => showErrorDetails(record));
      tdDetails.appendChild(detailsBtn);
    } else {
      tdDetails.textContent = '-';
    }
    tr.appendChild(tdDetails);

    tbody.appendChild(tr);
  });
}

/**
 * ステータス概要を更新
 * @param {Object} stats - 統計データ
 * @param {Object} status - ステータスデータ
 */
export function renderStatusOverview(stats, status) {
  const schedulerEl = document.getElementById('schedulerStatus');
  if (schedulerEl) {
    schedulerEl.textContent = status?.scheduler_running ? '稼働中' : '停止中';
    schedulerEl.style.color = status?.scheduler_running ? 'var(--moss)' : 'var(--danger)';
  }

  const activeCountEl = document.getElementById('activeConfigsCount');
  if (activeCountEl) {
    activeCountEl.textContent = stats?.active_configs || 0;
  }

  const recentSyncsEl = document.getElementById('recentSyncsCount');
  if (recentSyncsEl) {
    recentSyncsEl.textContent = stats?.recent_syncs_24h || 0;
  }
}

/**
 * 履歴フィルター用の設定セレクトを更新
 * @param {Array} configs - 設定の配列
 */
export function updateHistoryConfigFilter(configs) {
  const select = document.getElementById('historyConfigFilter');
  if (!select) return;

  while (select.options.length > 1) {
    select.remove(1);
  }

  configs.forEach(config => {
    const option = document.createElement('option');
    option.value = config.id;
    option.textContent = config.name || `設定ID: ${config.id}`;
    select.appendChild(option);
  });
}

// ============================================================
// モーダル管理
// ============================================================

/**
 * 新規作成モーダルを表示
 */
export function showCreateConfigModal() {
  _editingConfigId = null;
  const modalTitle = document.getElementById('modalTitle');
  if (modalTitle) modalTitle.textContent = '新規同期設定';
  const configForm = document.getElementById('configForm');
  if (configForm) configForm.reset();
  const isEnabled = document.getElementById('isEnabled');
  if (isEnabled) isEnabled.checked = true;
  const configModal = document.getElementById('configModal');
  if (configModal) configModal.classList.add('show');
}

/**
 * 編集モーダルを表示
 * @param {Object} config - 編集する設定オブジェクト
 */
export function showEditConfigModal(config) {
  _editingConfigId = config.id;
  const modalTitle = document.getElementById('modalTitle');
  if (modalTitle) modalTitle.textContent = '同期設定編集';

  const fields = {
    configName: config.name || '',
    configDescription: config.description || '',
    siteId: config.site_id || '',
    driveId: config.drive_id || '',
    folderPath: config.folder_path || '/',
    syncSchedule: config.sync_schedule || '0 2 * * *',
    syncStrategy: config.sync_strategy || 'incremental',
  };

  Object.entries(fields).forEach(([id, value]) => {
    const el = document.getElementById(id);
    if (el) el.value = value;
  });

  const isEnabled = document.getElementById('isEnabled');
  if (isEnabled) isEnabled.checked = config.is_enabled !== false;

  const configModal = document.getElementById('configModal');
  if (configModal) configModal.classList.add('show');
}

/**
 * 設定モーダルを閉じる
 */
export function closeConfigModal() {
  const configModal = document.getElementById('configModal');
  if (configModal) configModal.classList.remove('show');
  _editingConfigId = null;
}

/**
 * テスト結果モーダルを表示
 * @param {Object} result - テスト結果オブジェクト
 */
export function showTestResultModal(result) {
  const content = document.getElementById('testResultContent');
  if (!content) return;

  content.textContent = '';

  if (result.success) {
    const successDiv = document.createElement('div');
    successDiv.className = 'test-result-success';

    const title = document.createElement('strong');
    title.textContent = '接続テスト成功';
    successDiv.appendChild(title);

    const message = document.createElement('p');
    message.textContent = result.message || 'SharePoint/OneDriveへの接続が確認できました。';
    message.style.marginTop = '10px';
    successDiv.appendChild(message);

    if (result.data?.files) {
      const fileCount = document.createElement('p');
      fileCount.textContent = `検出ファイル数: ${result.data.files.length}`;
      successDiv.appendChild(fileCount);

      const preview = document.createElement('div');
      preview.className = 'file-preview';
      result.data.files.slice(0, 10).forEach(file => {
        const fileDiv = document.createElement('div');
        fileDiv.textContent = file.name || file;
        preview.appendChild(fileDiv);
      });
      successDiv.appendChild(preview);
    }

    content.appendChild(successDiv);
  } else {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'test-result-error';

    const title = document.createElement('strong');
    title.textContent = '接続テスト失敗';
    errorDiv.appendChild(title);

    const message = document.createElement('p');
    message.textContent = result.error?.message || '接続に失敗しました。設定を確認してください。';
    message.style.marginTop = '10px';
    errorDiv.appendChild(message);

    content.appendChild(errorDiv);
  }

  const testResultModal = document.getElementById('testResultModal');
  if (testResultModal) testResultModal.classList.add('show');
}

/**
 * テスト結果モーダルを閉じる
 */
export function closeTestResultModal() {
  const testResultModal = document.getElementById('testResultModal');
  if (testResultModal) testResultModal.classList.remove('show');
}

// ============================================================
// フォーム処理
// ============================================================

/**
 * 設定フォーム送信処理
 * @param {Event} event - フォームのsubmitイベント
 */
export async function handleConfigFormSubmit(event) {
  event.preventDefault();

  const getValue = (id) => {
    const el = document.getElementById(id);
    return el ? el.value : '';
  };

  const formData = {
    name: getValue('configName'),
    description: getValue('configDescription'),
    site_id: getValue('siteId'),
    drive_id: getValue('driveId'),
    folder_path: getValue('folderPath') || '/',
    sync_schedule: getValue('syncSchedule'),
    sync_strategy: getValue('syncStrategy'),
    is_enabled: document.getElementById('isEnabled')?.checked ?? true,
  };

  if (!formData.name || !formData.site_id || !formData.drive_id) {
    showMessage('必須フィールドを入力してください', 'error');
    return;
  }

  try {
    if (_editingConfigId) {
      await updateSyncConfig(_editingConfigId, formData);
      showMessage('同期設定を更新しました', 'success');
    } else {
      await createSyncConfig(formData);
      showMessage('同期設定を作成しました', 'success');
    }
    closeConfigModal();
    await loadAllData();
  } catch (error) {
    logger.error('[MS365] Config save error:', error);
    showMessage('エラー: ' + error.message, 'error');
  }
}

// ============================================================
// アクションハンドラー
// ============================================================

/**
 * 接続テスト実行
 * @param {string} configId - 設定ID
 */
export async function handleTestConfig(configId) {
  try {
    const result = await testSyncConfig(configId);
    showTestResultModal(result);
  } catch (error) {
    logger.error('[MS365] Test config error:', error);
    showMessage('接続テストに失敗しました: ' + error.message, 'error');
  }
}

/**
 * 同期即時実行
 * @param {string} configId - 設定ID
 */
export async function handleExecuteSync(configId) {
  if (!confirm('この設定で同期を即時実行しますか？')) {
    return;
  }

  try {
    await executeSyncNow(configId);
    showMessage('同期を開始しました。履歴タブで進行状況を確認できます。', 'success');
    setTimeout(() => loadAllData(), 2000);
  } catch (error) {
    logger.error('[MS365] Execute sync error:', error);
    showMessage('同期実行に失敗しました: ' + error.message, 'error');
  }
}

/**
 * 設定削除
 * @param {string} configId - 設定ID
 * @param {string} configName - 設定名
 */
export async function handleDeleteConfig(configId, configName) {
  if (!confirm(`同期設定「${configName}」を削除しますか？\nこの操作は取り消せません。`)) {
    return;
  }

  try {
    await deleteSyncConfig(configId);
    showMessage('同期設定を削除しました', 'success');
    await loadAllData();
  } catch (error) {
    logger.error('[MS365] Delete config error:', error);
    showMessage('削除に失敗しました: ' + error.message, 'error');
  }
}

/**
 * エラー詳細を表示
 * @param {Object} record - 履歴レコード
 */
export function showErrorDetails(record) {
  alert(`エラー詳細:\n\n${record.error_message || '詳細情報なし'}`);
}

// ============================================================
// ユーティリティ関数
// ============================================================

/**
 * cron形式を人間が読める日本語に変換
 * @param {string} cron - cron形式の文字列
 * @returns {string} 日本語表現
 */
export function formatCronSchedule(cron) {
  if (!cron || cron === 'N/A') return 'N/A';

  const patterns = {
    '0 * * * *': '毎時0分',
    '0 */2 * * *': '2時間ごと',
    '0 */6 * * *': '6時間ごと',
    '0 0 * * *': '毎日0時',
    '0 2 * * *': '毎日2時',
    '0 0 * * 0': '毎週日曜0時',
    '0 0 1 * *': '毎月1日0時',
  };

  return patterns[cron] || cron;
}

/**
 * 秒数を時間形式に変換
 * @param {number} seconds - 秒数
 * @returns {string} 人間が読める形式
 */
export function formatDuration(seconds) {
  if (!seconds || seconds < 0) return '0秒';

  if (seconds < 60) {
    return `${Math.round(seconds)}秒`;
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${minutes}分${secs}秒`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}時間${minutes}分`;
  }
}

/**
 * 日時フォーマット
 * @param {string} dateString - 日時文字列
 * @returns {string} フォーマットされた日時
 */
export function formatDateTime(dateString) {
  if (!dateString || dateString === 'N/A') return 'N/A';

  try {
    const date = new Date(dateString);
    return date.toLocaleString('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (e) {
    return dateString;
  }
}

/**
 * ステータスラベル取得
 * @param {string} status - ステータス文字列
 * @returns {string} 日本語ラベル
 */
export function getStatusLabel(status) {
  const labels = {
    'completed': '完了',
    'failed': '失敗',
    'partial': '部分完了',
    'running': '実行中',
    'pending': '待機中'
  };
  return labels[status] || status || '不明';
}

/**
 * メッセージ表示（アラート）
 * @param {string} text - 表示するテキスト
 * @param {'success'|'error'} [type='success'] - メッセージタイプ
 */
export function showMessage(text, type = 'success') {
  if (type === 'error') {
    alert('エラー: ' + text);
  } else {
    alert(text);
  }
}

// ============================================================
// 後方互換性（window経由のアクセスを維持）
// ============================================================

if (typeof window !== 'undefined') {
  window.MS365SyncModule = {
    checkAuth,
    loadSyncConfigs,
    createSyncConfig,
    updateSyncConfig,
    deleteSyncConfig,
    executeSyncNow,
    testSyncConfig,
    loadSyncHistory,
    loadSyncStats,
    loadSyncStatus,
    loadAllData,
    loadSyncHistoryWithFilter,
    renderConfigList,
    renderSyncHistory,
    renderStatusOverview,
    updateHistoryConfigFilter,
    showCreateConfigModal,
    showEditConfigModal,
    closeConfigModal,
    showTestResultModal,
    closeTestResultModal,
    handleConfigFormSubmit,
    handleTestConfig,
    handleExecuteSync,
    handleDeleteConfig,
    showErrorDetails,
    formatCronSchedule,
    formatDuration,
    formatDateTime,
    getStatusLabel,
    showMessage,
  };
}
