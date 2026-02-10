/**
 * Microsoft 365 Sync Settings Management
 * Mirai Knowledge Systems
 */

// API Base URL
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:5200'
    : (window.location.protocol + '//' + window.location.host);

// Logger
const logger = window.logger || console;

// State
let editingConfigId = null;
let allConfigs = [];

// ========================================
// 認証チェック
// ========================================

async function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        alert('ログインが必要です');
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

// ========================================
// API呼び出し
// ========================================

/**
 * 同期設定一覧を取得
 */
async function loadSyncConfigs() {
    const token = localStorage.getItem('access_token');
    if (!token) throw new Error('Not authenticated');

    const response = await fetch(`${API_BASE}/api/v1/integrations/microsoft365/sync/configs`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error?.message || 'Failed to load sync configs');
    }

    return data;
}

/**
 * 同期設定を作成
 */
async function createSyncConfig(configData) {
    const token = localStorage.getItem('access_token');
    if (!token) throw new Error('Not authenticated');

    const response = await fetch(`${API_BASE}/api/v1/integrations/microsoft365/sync/configs`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(configData)
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error?.message || 'Failed to create sync config');
    }

    return data;
}

/**
 * 同期設定を更新
 */
async function updateSyncConfig(configId, configData) {
    const token = localStorage.getItem('access_token');
    if (!token) throw new Error('Not authenticated');

    const response = await fetch(`${API_BASE}/api/v1/integrations/microsoft365/sync/configs/${configId}`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(configData)
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error?.message || 'Failed to update sync config');
    }

    return data;
}

/**
 * 同期設定を削除
 */
async function deleteSyncConfig(configId) {
    const token = localStorage.getItem('access_token');
    if (!token) throw new Error('Not authenticated');

    const response = await fetch(`${API_BASE}/api/v1/integrations/microsoft365/sync/configs/${configId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error?.message || 'Failed to delete sync config');
    }

    return data;
}

/**
 * 同期を即時実行
 */
async function executeSyncNow(configId) {
    const token = localStorage.getItem('access_token');
    if (!token) throw new Error('Not authenticated');

    const response = await fetch(`${API_BASE}/api/v1/integrations/microsoft365/sync/configs/${configId}/execute`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error?.message || 'Failed to execute sync');
    }

    return data;
}

/**
 * 接続テストを実行
 */
async function testSyncConfig(configId) {
    const token = localStorage.getItem('access_token');
    if (!token) throw new Error('Not authenticated');

    const response = await fetch(`${API_BASE}/api/v1/integrations/microsoft365/sync/configs/${configId}/test`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error?.message || 'Failed to test sync config');
    }

    return data;
}

/**
 * 同期履歴を取得
 */
async function loadSyncHistory(configId = null, page = 1) {
    const token = localStorage.getItem('access_token');
    if (!token) throw new Error('Not authenticated');

    let url = `${API_BASE}/api/v1/integrations/microsoft365/sync/history?page=${page}&per_page=20`;
    if (configId) {
        url += `&config_id=${configId}`;
    }

    const response = await fetch(url, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error?.message || 'Failed to load sync history');
    }

    return data;
}

/**
 * 同期統計を取得
 */
async function loadSyncStats() {
    const token = localStorage.getItem('access_token');
    if (!token) throw new Error('Not authenticated');

    const response = await fetch(`${API_BASE}/api/v1/integrations/microsoft365/sync/stats`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error?.message || 'Failed to load sync stats');
    }

    return data;
}

/**
 * スケジューラーステータスを取得
 */
async function loadSyncStatus() {
    const token = localStorage.getItem('access_token');
    if (!token) throw new Error('Not authenticated');

    const response = await fetch(`${API_BASE}/api/v1/integrations/microsoft365/sync/status`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error?.message || 'Failed to load sync status');
    }

    return data;
}

// ========================================
// UI更新
// ========================================

/**
 * 設定一覧をレンダリング
 */
function renderConfigList(configs) {
    allConfigs = configs || [];
    const tbody = document.getElementById('configListBody');
    tbody.textContent = ''; // XSS対策: 既存内容をクリア

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

        // 設定名
        const tdName = document.createElement('td');
        tdName.textContent = config.name || 'Unnamed';
        tr.appendChild(tdName);

        // サイト/ドライブ
        const tdSite = document.createElement('td');
        const siteText = document.createElement('div');
        siteText.style.fontSize = '12px';
        siteText.textContent = config.site_id ? config.site_id.substring(0, 30) + '...' : 'N/A';
        tdSite.appendChild(siteText);
        tr.appendChild(tdSite);

        // スケジュール
        const tdSchedule = document.createElement('td');
        tdSchedule.textContent = formatCronSchedule(config.sync_schedule || 'N/A');
        tdSchedule.style.fontSize = '13px';
        tr.appendChild(tdSchedule);

        // ステータス
        const tdStatus = document.createElement('td');
        const statusBadge = document.createElement('span');
        statusBadge.className = config.is_enabled ? 'status-badge status-enabled' : 'status-badge status-disabled';
        statusBadge.textContent = config.is_enabled ? '有効' : '無効';
        tdStatus.appendChild(statusBadge);
        tr.appendChild(tdStatus);

        // 最終同期
        const tdLastSync = document.createElement('td');
        tdLastSync.textContent = config.last_sync_at ? formatDateTime(config.last_sync_at) : '未実行';
        tdLastSync.style.fontSize = '12px';
        tr.appendChild(tdLastSync);

        // アクション
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

    // フィルターセレクトを更新
    updateHistoryConfigFilter(configs);
}

/**
 * 同期履歴をレンダリング
 */
function renderSyncHistory(history) {
    const tbody = document.getElementById('historyTableBody');
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

        // 開始時刻
        const tdStarted = document.createElement('td');
        tdStarted.textContent = formatDateTime(record.started_at || 'N/A');
        tdStarted.style.fontSize = '12px';
        tr.appendChild(tdStarted);

        // 設定名
        const tdConfig = document.createElement('td');
        tdConfig.textContent = record.config_name || `設定ID: ${record.config_id}`;
        tr.appendChild(tdConfig);

        // ステータス
        const tdStatus = document.createElement('td');
        const statusBadge = document.createElement('span');
        statusBadge.className = `status-badge status-${record.status || 'unknown'}`;
        statusBadge.textContent = getStatusLabel(record.status);
        tdStatus.appendChild(statusBadge);
        tr.appendChild(tdStatus);

        // 処理ファイル数
        const tdFiles = document.createElement('td');
        tdFiles.textContent = record.files_processed || '0';
        tr.appendChild(tdFiles);

        // 実行時間
        const tdDuration = document.createElement('td');
        tdDuration.textContent = formatDuration(record.duration_seconds || 0);
        tdDuration.style.fontSize = '12px';
        tr.appendChild(tdDuration);

        // 詳細
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
 */
function renderStatusOverview(stats, status) {
    // スケジューラーステータス
    const schedulerEl = document.getElementById('schedulerStatus');
    if (schedulerEl) {
        schedulerEl.textContent = status?.scheduler_running ? '稼働中' : '停止中';
        schedulerEl.style.color = status?.scheduler_running ? 'var(--moss)' : 'var(--danger)';
    }

    // アクティブ設定数
    const activeCountEl = document.getElementById('activeConfigsCount');
    if (activeCountEl) {
        activeCountEl.textContent = stats?.active_configs || 0;
    }

    // 直近24時間の同期
    const recentSyncsEl = document.getElementById('recentSyncsCount');
    if (recentSyncsEl) {
        recentSyncsEl.textContent = stats?.recent_syncs_24h || 0;
    }
}

/**
 * 履歴フィルター用の設定リストを更新
 */
function updateHistoryConfigFilter(configs) {
    const select = document.getElementById('historyConfigFilter');

    // 既存オプションを保持（「全設定」オプション）
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

// ========================================
// モーダル管理
// ========================================

/**
 * 新規作成モーダルを表示
 */
function showCreateConfigModal() {
    editingConfigId = null;
    document.getElementById('modalTitle').textContent = '新規同期設定';
    document.getElementById('configForm').reset();
    document.getElementById('isEnabled').checked = true;
    document.getElementById('configModal').classList.add('show');
}

/**
 * 編集モーダルを表示
 */
function showEditConfigModal(config) {
    editingConfigId = config.id;
    document.getElementById('modalTitle').textContent = '同期設定編集';

    // フォームに値を設定
    document.getElementById('configName').value = config.name || '';
    document.getElementById('configDescription').value = config.description || '';
    document.getElementById('siteId').value = config.site_id || '';
    document.getElementById('driveId').value = config.drive_id || '';
    document.getElementById('folderPath').value = config.folder_path || '/';
    document.getElementById('syncSchedule').value = config.sync_schedule || '0 2 * * *';
    document.getElementById('syncStrategy').value = config.sync_strategy || 'incremental';
    document.getElementById('isEnabled').checked = config.is_enabled !== false;

    document.getElementById('configModal').classList.add('show');
}

/**
 * 設定モーダルを閉じる
 */
function closeConfigModal() {
    document.getElementById('configModal').classList.remove('show');
    editingConfigId = null;
}

/**
 * テスト結果モーダルを表示
 */
function showTestResultModal(result) {
    const content = document.getElementById('testResultContent');
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

    document.getElementById('testResultModal').classList.add('show');
}

/**
 * テスト結果モーダルを閉じる
 */
function closeTestResultModal() {
    document.getElementById('testResultModal').classList.remove('show');
}

// ========================================
// フォーム処理
// ========================================

/**
 * 設定フォーム送信処理
 */
async function handleConfigFormSubmit(event) {
    event.preventDefault();

    const formData = {
        name: document.getElementById('configName').value,
        description: document.getElementById('configDescription').value,
        site_id: document.getElementById('siteId').value,
        drive_id: document.getElementById('driveId').value,
        folder_path: document.getElementById('folderPath').value || '/',
        sync_schedule: document.getElementById('syncSchedule').value,
        sync_strategy: document.getElementById('syncStrategy').value,
        is_enabled: document.getElementById('isEnabled').checked,
    };

    // バリデーション
    if (!formData.name || !formData.site_id || !formData.drive_id) {
        showMessage('必須フィールドを入力してください', 'error');
        return;
    }

    try {
        if (editingConfigId) {
            await updateSyncConfig(editingConfigId, formData);
            showMessage('同期設定を更新しました', 'success');
        } else {
            await createSyncConfig(formData);
            showMessage('同期設定を作成しました', 'success');
        }
        closeConfigModal();
        await loadAllData();
    } catch (error) {
        logger.error('Config save error:', error);
        showMessage('エラー: ' + error.message, 'error');
    }
}

// ========================================
// アクションハンドラー
// ========================================

/**
 * 接続テスト実行
 */
async function handleTestConfig(configId) {
    const btn = event.target;
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'テスト中...';

    try {
        const result = await testSyncConfig(configId);
        showTestResultModal(result);
    } catch (error) {
        logger.error('Test config error:', error);
        showMessage('接続テストに失敗しました: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

/**
 * 同期即時実行
 */
async function handleExecuteSync(configId) {
    if (!confirm('この設定で同期を即時実行しますか？')) {
        return;
    }

    const btn = event.target;
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = '実行中...';

    try {
        await executeSyncNow(configId);
        showMessage('同期を開始しました。履歴タブで進行状況を確認できます。', 'success');
        setTimeout(() => loadAllData(), 2000);
    } catch (error) {
        logger.error('Execute sync error:', error);
        showMessage('同期実行に失敗しました: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

/**
 * 設定削除
 */
async function handleDeleteConfig(configId, configName) {
    if (!confirm(`同期設定「${configName}」を削除しますか？\nこの操作は取り消せません。`)) {
        return;
    }

    try {
        await deleteSyncConfig(configId);
        showMessage('同期設定を削除しました', 'success');
        await loadAllData();
    } catch (error) {
        logger.error('Delete config error:', error);
        showMessage('削除に失敗しました: ' + error.message, 'error');
    }
}

/**
 * エラー詳細を表示
 */
function showErrorDetails(record) {
    alert(`エラー詳細:\n\n${record.error_message || '詳細情報なし'}`);
}

// ========================================
// ユーティリティ
// ========================================

/**
 * cron形式を人間が読める形式に変換
 */
function formatCronSchedule(cron) {
    if (!cron || cron === 'N/A') return 'N/A';

    // 簡易的な変換（よくあるパターンのみ）
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
 */
function formatDuration(seconds) {
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
 */
function formatDateTime(dateString) {
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
 */
function getStatusLabel(status) {
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
 * メッセージ表示
 */
function showMessage(text, type = 'success') {
    // 簡易的なアラート表示（後でトースト通知に置き換え可能）
    if (type === 'error') {
        alert('エラー: ' + text);
    } else {
        alert(text);
    }
}

// ========================================
// データロード
// ========================================

/**
 * すべてのデータをロード
 */
async function loadAllData() {
    try {
        // 並列でデータ取得
        const [configsResult, statsResult, statusResult] = await Promise.all([
            loadSyncConfigs().catch(err => {
                logger.error('Failed to load configs:', err);
                return { success: false, data: [] };
            }),
            loadSyncStats().catch(err => {
                logger.error('Failed to load stats:', err);
                return { success: false, data: {} };
            }),
            loadSyncStatus().catch(err => {
                logger.error('Failed to load status:', err);
                return { success: false, data: {} };
            })
        ]);

        // UI更新
        if (configsResult.success) {
            renderConfigList(configsResult.data);
        }

        renderStatusOverview(
            statsResult.success ? statsResult.data : {},
            statusResult.success ? statusResult.data : {}
        );

        // 履歴は個別にロード（フィルター適用のため）
        await loadSyncHistoryWithFilter();

    } catch (error) {
        logger.error('Failed to load data:', error);
        showMessage('データの読み込みに失敗しました: ' + error.message, 'error');
    }
}

/**
 * フィルター適用して履歴をロード
 */
async function loadSyncHistoryWithFilter() {
    const configFilter = document.getElementById('historyConfigFilter').value;
    const statusFilter = document.getElementById('historyStatusFilter').value;

    try {
        const result = await loadSyncHistory(configFilter || null);

        let history = result.success ? result.data : [];

        // ステータスフィルター適用
        if (statusFilter) {
            history = history.filter(h => h.status === statusFilter);
        }

        renderSyncHistory(history);
    } catch (error) {
        logger.error('Failed to load history:', error);
        renderSyncHistory([]);
    }
}

// ========================================
// グローバルエクスポート（互換性レイヤー）
// ========================================
// HTMLファイル内のインラインスクリプトから呼び出せるようにする
window.checkAuth = checkAuth;
window.loadAllData = loadAllData;
window.showCreateConfigModal = showCreateConfigModal;
window.closeConfigModal = closeConfigModal;
window.handleConfigFormSubmit = handleConfigFormSubmit;
window.closeTestResultModal = closeTestResultModal;
window.loadSyncHistory = loadSyncHistory;
