/**
 * @fileoverview 共通ページレンダリングモジュール v2.0.0
 * @module pages/page-renderer
 * @description Phase F-4: detail-pages.js 分割版 - 共通レンダリング処理
 *
 * 担当機能:
 * - 本番環境判定 (isProductionMode)
 * - ローディング・エラー表示 (showLoading / hideLoading / showError / hideError)
 * - 日付フォーマット (formatDate / formatDateShort)
 * - API 呼び出し (apiCall)
 * - 承認フロー表示 (displayApprovalFlow)
 * - パンくずリスト更新 (updateBreadcrumb)
 * - DOM 更新ヘルパー (updateElement)
 * - 共有機能 (openShareModal / closeShareModal / copyShareUrl / shareByEmail / shareBySlack / shareByTeams)
 * - PDF ダウンロード (downloadPDF)
 * - スクロール (scrollToTop)
 * - 計算関数 (calculateElapsedTime / calculateResponseTime)
 */

// ============================================================
// 本番環境判定
// ============================================================

/**
 * 本番環境かどうかを判定
 * @returns {boolean}
 */
function isProductionMode() {
  if (typeof IS_PRODUCTION !== 'undefined') return IS_PRODUCTION;
  if (typeof window.IS_PRODUCTION !== 'undefined') return window.IS_PRODUCTION;

  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('env') === 'production') return true;
  if (urlParams.get('env') === 'development') return false;
  const envSetting = localStorage.getItem('MKS_ENV');
  if (envSetting === 'production') return true;
  if (envSetting === 'development') return false;
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') return false;
  return false;
}

// ============================================================
// ローディング・エラー表示
// ============================================================

/**
 * ローディングインジケーターを表示
 */
function showLoading() {
  const loading = document.getElementById('loadingIndicator');
  if (loading) loading.style.display = 'flex';
}

/**
 * ローディングインジケーターを非表示
 */
function hideLoading() {
  const loading = document.getElementById('loadingIndicator');
  if (loading) loading.style.display = 'none';
}

/**
 * エラーメッセージを表示
 * @param {string} message - エラーメッセージ
 */
function showError(message) {
  hideLoading();
  const errorEl = document.getElementById('errorMessage');
  const errorText = document.getElementById('errorText');
  if (errorEl && errorText) {
    errorText.textContent = message;
    errorEl.style.display = 'block';
  }
}

/**
 * エラーメッセージを非表示
 */
function hideError() {
  const errorEl = document.getElementById('errorMessage');
  if (errorEl) errorEl.style.display = 'none';
}

// ============================================================
// 日付フォーマット
// ============================================================

/**
 * 日時文字列を日本語フォーマットに変換（年月日時分）
 * @param {string} dateString - ISO 日付文字列
 * @returns {string}
 */
function formatDate(dateString) {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

/**
 * 日時文字列を短い日本語フォーマットに変換（年月日のみ）
 * @param {string} dateString - ISO 日付文字列
 * @returns {string}
 */
function formatDateShort(dateString) {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
}

// ============================================================
// スクロール
// ============================================================

/**
 * ページ先頭へスクロール
 */
function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ============================================================
// API 呼び出し
// ============================================================

/**
 * API を呼び出す（detail-pages.js 内部用）
 * @param {string} endpoint - API エンドポイント（/api/v1 以降）
 * @param {Object} [options={}] - fetch オプション
 * @returns {Promise<Object|null>}
 */
async function apiCall(endpoint, options = {}) {
  const log = window.logger || console;

  // API_BASE は app.js のグローバルを使用
  const API_BASE = window.API_BASE || `${window.location.origin}/api/v1`;

  const token = localStorage.getItem('access_token');
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });

    if (response.status === 401) {
      log.error('[API] Unauthorized. Redirecting to login...');
      showError('セッションの有効期限が切れました。再度ログインしてください。');
      setTimeout(() => { window.location.href = '/login.html'; }, 2000);
      return null;
    }

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData.error) errorMessage = errorData.error.message || errorMessage;
      } catch (e) { /* ignore */ }

      if (response.status === 403) {
        showError('この操作を実行する権限がありません。');
      } else if (response.status === 404) {
        showError('リソースが見つかりません。');
      } else if (response.status === 429) {
        showError('リクエストが多すぎます。しばらく待ってから再試行してください。');
      } else if (response.status === 500) {
        showError('サーバーエラーが発生しました。管理者に連絡してください。');
      } else {
        showError(`エラー: ${errorMessage}`);
      }
      return null;
    }

    return await response.json();
  } catch (error) {
    log.error('[API] Error:', error);
    if (error.message === 'Failed to fetch' || error.name === 'TypeError') {
      showError('ネットワークエラー: サーバーに接続できません。');
    }
    return null;
  }
}

// ============================================================
// DOM 更新ヘルパー
// ============================================================

/**
 * 要素のテキストを安全に更新
 * @param {string} id - 要素 ID
 * @param {string|number} value - 設定する値
 */
function updateElement(id, value) {
  const el = document.getElementById(id);
  if (el) {
    if (typeof value === 'object' && value !== null) {
      if (value instanceof Node) {
        if (typeof setSecureChildren === 'function') {
          setSecureChildren(el, value);
        }
      } else {
        el.textContent = String(value);
      }
    } else {
      el.textContent = value;
    }
  }
}

// ============================================================
// 承認フロー表示
// ============================================================

/**
 * 承認フローを表示
 * @param {Array|null} approvalStatus - 承認ステータス配列
 */
function displayApprovalFlow(approvalStatus) {
  const flowEl = document.getElementById('approvalFlow');
  if (!flowEl) return;

  const defaultFlow = [
    { step: '起案', status: 'done' },
    { step: '所長承認', status: 'wait' },
    { step: 'レビュー', status: 'hold' },
    { step: '承認・配信', status: 'info' }
  ];

  const flow = approvalStatus || defaultFlow;
  const statusMap = { 'done': 'is-done', 'wait': 'is-wait', 'hold': 'is-hold', 'info': 'is-info' };
  const flowData = Array.isArray(flow) ? flow : defaultFlow;

  if (typeof setSecureChildren === 'function' && typeof createApprovalFlowElement === 'function') {
    setSecureChildren(flowEl, flowData.map(item => createApprovalFlowElement(item, statusMap)));
  } else {
    flowEl.textContent = '';
    flowData.forEach(item => {
      const stepEl = document.createElement('div');
      stepEl.className = `flow-step ${statusMap[item.status] || ''}`;
      stepEl.textContent = item.step;
      flowEl.appendChild(stepEl);
    });
  }
}

// ============================================================
// パンくずリスト
// ============================================================

/**
 * パンくずリストを更新
 * @param {string} category - カテゴリ名
 * @param {string} title - タイトル
 */
function updateBreadcrumb(category, title) {
  const breadcrumbEl = document.getElementById('breadcrumbList');
  if (!breadcrumbEl) return;

  breadcrumbEl.textContent = '';

  const homeLink = document.createElement('a');
  homeLink.href = 'index.html';
  homeLink.textContent = 'ホーム';

  const catLink = document.createElement('a');
  catLink.href = `index.html#${category || ''}`;
  catLink.textContent = category || '';

  const currentItem = document.createElement('span');
  currentItem.setAttribute('aria-current', 'page');
  currentItem.textContent = title || '詳細';

  const li1 = document.createElement('li');
  li1.appendChild(homeLink);
  const li2 = document.createElement('li');
  li2.appendChild(catLink);
  const li3 = document.createElement('li');
  li3.appendChild(currentItem);

  breadcrumbEl.appendChild(li1);
  breadcrumbEl.appendChild(li2);
  breadcrumbEl.appendChild(li3);
}

// ============================================================
// 共有機能
// ============================================================

/**
 * 共有モーダルを開く
 */
function openShareModal() {
  const modal = document.getElementById('shareModal');
  const shareUrlEl = document.getElementById('shareUrl');

  if (modal && shareUrlEl) {
    shareUrlEl.value = window.location.href;
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  } else {
    _createShareModal();
  }
}

/**
 * 共有モーダルを動的作成
 * @private
 */
function _createShareModal() {
  const createEl = typeof createSecureElement === 'function' ? createSecureElement : _createEl;
  const setChildren = typeof setSecureChildren === 'function' ? setSecureChildren : null;

  const modal = createEl('div', { id: 'shareModal', className: 'modal', style: 'display: flex;' });
  const modalContent = createEl('div', { className: 'modal-content' });

  const header = document.createElement('div');
  header.className = 'modal-header';
  const h2 = document.createElement('h2');
  h2.textContent = '共有';
  const closeBtn = document.createElement('button');
  closeBtn.className = 'modal-close';
  closeBtn.textContent = '×';
  closeBtn.onclick = () => closeShareModal();
  header.appendChild(h2);
  header.appendChild(closeBtn);

  const body = document.createElement('div');
  body.className = 'modal-body';

  const urlInput = document.createElement('input');
  urlInput.type = 'text';
  urlInput.id = 'shareUrl';
  urlInput.readOnly = true;
  urlInput.value = window.location.href;
  urlInput.style.flex = '1';

  const copyBtn = document.createElement('button');
  copyBtn.className = 'cta secondary';
  copyBtn.textContent = 'コピー';
  copyBtn.onclick = () => copyShareUrl();

  const urlRow = document.createElement('div');
  urlRow.style.cssText = 'display: flex; gap: 10px;';
  urlRow.appendChild(urlInput);
  urlRow.appendChild(copyBtn);
  body.appendChild(urlRow);

  const actions = document.createElement('div');
  actions.className = 'modal-actions';
  const closeActionBtn = document.createElement('button');
  closeActionBtn.className = 'cta ghost';
  closeActionBtn.textContent = '閉じる';
  closeActionBtn.onclick = () => closeShareModal();
  actions.appendChild(closeActionBtn);

  modalContent.appendChild(header);
  modalContent.appendChild(body);
  modalContent.appendChild(actions);
  modal.appendChild(modalContent);

  document.body.appendChild(modal);
  document.body.style.overflow = 'hidden';

  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeShareModal();
  });
}

/**
 * 簡易要素作成（createSecureElement がない場合のフォールバック）
 * @private
 */
function _createEl(tag, attrs = {}, children) {
  const el = document.createElement(tag);
  Object.entries(attrs).forEach(([k, v]) => {
    if (k === 'className') el.className = v;
    else if (k === 'style' && typeof v === 'string') el.style.cssText = v;
    else el.setAttribute(k, v);
  });
  if (children) {
    if (typeof children === 'string') el.textContent = children;
    else if (Array.isArray(children)) {
      children.forEach(c => {
        if (typeof c === 'string') el.appendChild(document.createTextNode(c));
        else if (c instanceof Node) el.appendChild(c);
      });
    } else if (children instanceof Node) el.appendChild(children);
  }
  return el;
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
 * 共有 URL をコピー
 */
function copyShareUrl() {
  const shareUrlEl = document.getElementById('shareUrl');
  if (shareUrlEl) {
    shareUrlEl.select();
    shareUrlEl.setSelectionRange(0, 99999);

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(shareUrlEl.value)
        .then(() => {
          if (typeof showNotification === 'function') showNotification('URLをクリップボードにコピーしました', 'success');
          else if (typeof showToast === 'function') showToast('URLをコピーしました', 'success');
        })
        .catch(() => {
          document.execCommand('copy');
          if (typeof showToast === 'function') showToast('URLをコピーしました', 'success');
        });
    } else {
      document.execCommand('copy');
      if (typeof showToast === 'function') showToast('URLをコピーしました', 'success');
    }
  }
}

/**
 * メールで共有
 */
function shareByEmail() {
  const url = encodeURIComponent(window.location.href);
  const title = encodeURIComponent(document.title);
  const subject = `【Mirai Knowledge】${title}`;
  const body = `以下のページを共有します:%0D%0A%0D%0A${url}`;
  window.location.href = `mailto:?subject=${subject}&body=${body}`;
  if (typeof showToast === 'function') showToast('メールアプリを開きます...', 'info');
}

/**
 * Slack で共有（将来実装）
 */
function shareBySlack() {
  if (typeof showToast === 'function') showToast('Slack連携機能は準備中です', 'info');
}

/**
 * Teams で共有（将来実装）
 */
function shareByTeams() {
  if (typeof showToast === 'function') showToast('Teams連携機能は準備中です', 'info');
}

/**
 * ページを印刷
 */
function printPage() {
  window.print();
}

/**
 * PDF エクスポート（印刷ダイアログ）
 */
function exportPDF() {
  if (typeof showToast === 'function') showToast('PDFを生成中...', 'info');
  setTimeout(() => { window.print(); }, 500);
}

/**
 * PDF ダウンロード
 * @param {string} [pageType=''] - ページタイプ
 * @param {string} [filename=''] - ファイル名
 */
function downloadPDF(pageType = '', filename = '') {
  const log = window.logger || console;
  try {
    window.print();
    if (typeof showNotification === 'function') {
      showNotification('PDFの印刷ダイアログを開きました', 'success');
    }
  } catch (error) {
    log.error('PDF generation error:', error);
    if (typeof showNotification === 'function') {
      showNotification('PDF保存に失敗しました', 'error');
    }
  }
}

// ============================================================
// 計算関数
// ============================================================

/**
 * 経過時間を計算して日本語文字列で返す
 * @param {string} createdAt - 作成日時 ISO 文字列
 * @returns {string}
 */
function calculateElapsedTime(createdAt) {
  if (!createdAt) return 'N/A';
  const now = new Date();
  const created = new Date(createdAt);
  const diff = now - created;
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const days = Math.floor(hours / 24);
  if (days > 0) return `${days}日`;
  return `${hours}時間`;
}

/**
 * 回答時間を計算（時間単位）
 * @param {string} createdAt - 投稿日時
 * @param {string} firstAnswerAt - 最初の回答日時
 * @returns {number|string}
 */
function calculateResponseTime(createdAt, firstAnswerAt) {
  if (!createdAt || !firstAnswerAt) return '--';
  const created = new Date(createdAt);
  const answered = new Date(firstAnswerAt);
  return Math.floor((answered - created) / (1000 * 60 * 60));
}

/**
 * ページをリロード（リトライ）
 */
function retryLoad() {
  window.location.reload();
}

// ============================================================
// グローバル公開
// ============================================================

window.isProductionMode = isProductionMode;
window.showLoading = window.showLoading || showLoading;
window.hideLoading = window.hideLoading || hideLoading;
window.showError = showError;
window.hideError = hideError;
window.formatDate = window.formatDate || formatDate;
window.formatDateShort = formatDateShort;
window.scrollToTop = scrollToTop;
window.apiCall = apiCall;
window.updateElement = updateElement;
window.displayApprovalFlow = displayApprovalFlow;
window.updateBreadcrumb = updateBreadcrumb;
window.openShareModal = openShareModal;
window.closeShareModal = closeShareModal;
window.copyShareUrl = copyShareUrl;
window.shareByEmail = shareByEmail;
window.shareBySlack = shareBySlack;
window.shareByTeams = shareByTeams;
window.printPage = printPage;
window.exportPDF = exportPDF;
window.downloadPDF = downloadPDF;
window.calculateElapsedTime = calculateElapsedTime;
window.calculateResponseTime = calculateResponseTime;
window.retryLoad = retryLoad;

export {
  isProductionMode,
  showLoading,
  hideLoading,
  showError,
  hideError,
  formatDate,
  formatDateShort,
  scrollToTop,
  apiCall,
  updateElement,
  displayApprovalFlow,
  updateBreadcrumb,
  openShareModal,
  closeShareModal,
  copyShareUrl,
  shareByEmail,
  shareBySlack,
  shareByTeams,
  printPage,
  exportPDF,
  downloadPDF,
  calculateElapsedTime,
  calculateResponseTime,
  retryLoad
};
