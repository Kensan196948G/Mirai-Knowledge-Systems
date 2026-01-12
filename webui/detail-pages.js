// ============================================================
// 詳細ページ共通機能
// ============================================================

// 依存関係チェック
(function() {
  const requiredFunctions = ['setSecureChildren', 'createSecureElement', 'escapeHtml', 'createElement'];
  const missing = requiredFunctions.filter(fn => typeof window[fn] === 'undefined');
  if (missing.length > 0) {
    // loggerが利用可能ならlogger.errorを、そうでなければlogger.errorを使用
    const log = typeof logger !== 'undefined' ? logger.error : logger.error;
    log('[DETAIL-PAGES] Missing required functions from dom-helpers.js:', missing);
    log('[DETAIL-PAGES] Please ensure dom-helpers.js is loaded before detail-pages.js');
  }
})();

// API_BASEはapp.jsで定義されているため、ここでは定義しない
// const API_BASE = app.jsで定義済み

// 本番環境判定（app.jsのIS_PRODUCTIONを使用、なければ独自判定）
function isProductionMode() {
  // app.jsで定義されたIS_PRODUCTIONがあればそれを使用
  if (typeof IS_PRODUCTION !== 'undefined') {
    return IS_PRODUCTION;
  }
  // フォールバック: 独自判定
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('env') === 'production') return true;
  if (urlParams.get('env') === 'development') return false;
  const envSetting = localStorage.getItem('MKS_ENV');
  if (envSetting === 'production') return true;
  if (envSetting === 'development') return false;
  // ローカルホスト以外は本番と見なす
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return false;
  }
  return false;
}

// ============================================================
// ユーティリティ関数
// ============================================================

function showLoading() {
  const loading = document.getElementById('loadingIndicator');
  if (loading) loading.style.display = 'flex';
}

function hideLoading() {
  const loading = document.getElementById('loadingIndicator');
  if (loading) loading.style.display = 'none';
}

function showError(message) {
  hideLoading();
  const errorEl = document.getElementById('errorMessage');
  const errorText = document.getElementById('errorText');
  if (errorEl && errorText) {
    errorText.textContent = message;
    errorEl.style.display = 'block';
  }
}

function hideError() {
  const errorEl = document.getElementById('errorMessage');
  if (errorEl) errorEl.style.display = 'none';
}

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

function formatDateShort(dateString) {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ============================================================
// API呼び出し関数
// ============================================================

async function apiCall(endpoint, options = {}) {
  const token = localStorage.getItem('access_token');
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers
    });

    // 認証エラー
    if (response.status === 401) {
      logger.error('[API] Unauthorized. Redirecting to login...');
      showError('セッションの有効期限が切れました。再度ログインしてください。');
      setTimeout(() => {
        window.location.href = '/login.html';
      }, 2000);
      return null;
    }

    // エラーレスポンスの処理
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}`;
      let errorCode = 'UNKNOWN_ERROR';

      try {
        const errorData = await response.json();
        if (errorData.error) {
          errorMessage = errorData.error.message || errorMessage;
          errorCode = errorData.error.code || errorCode;
        }
      } catch (e) {
        logger.error('[API] Failed to parse error response:', e);
      }

      // ステータスコード別のエラー表示
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

      const error = new Error(errorMessage);
      error.code = errorCode;
      error.status = response.status;
      throw error;
    }

    return await response.json();
  } catch (error) {
    logger.error('[API] Error:', error);

    // ネットワークエラーの場合
    if (error.message === 'Failed to fetch' || error.name === 'TypeError') {
      showError('ネットワークエラー: サーバーに接続できません。');
    }

    throw error;
  }
}

// ============================================================
// search-detail.html 専用機能
// ============================================================

async function loadKnowledgeDetail() {
  logger.log('[KNOWLEDGE DETAIL] Starting to load...');
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');
  const inProduction = isProductionMode();

  logger.log('[KNOWLEDGE DETAIL] ID from URL:', id, 'Production mode:', inProduction);

  if (!id) {
    showError('ナレッジIDが指定されていません。一覧ページに戻ります...');
    setTimeout(() => {
      window.location.href = 'index.html';
    }, 2000);
    return;
  }

  showLoading();
  hideError();

  try {
    let data = null;

    // 修正: 開発環境でもAPI優先に変更（データ不整合回避）
    logger.log('[DETAIL] Loading from API (data consistency fix)...');
    try {
      const response = await apiCall(`/knowledge/${id}`);
      logger.log('[DETAIL] API Response:', response);  // 🔍 デバッグログ追加

      // 🔧 修正: APIレスポンスから data プロパティを抽出
      data = response?.data || response;  // {success: true, data: {...}} から data を取り出す

      logger.log('[DETAIL] Extracted data:', data);  // 🔍 抽出後のデータ
      logger.log('[DETAIL] Title:', data?.title);
      logger.log('[DETAIL] Summary:', data?.summary);
      logger.log('[DETAIL] Successfully loaded from API');
    } catch (apiError) {
      logger.error('[DETAIL] API call failed:', apiError);  // warn → error に変更

      // APIが失敗した場合のみlocalStorageにフォールバック
      const knowledgeDataStr = localStorage.getItem('knowledge_details');
      if (knowledgeDataStr) {
        logger.log('[DETAIL] Fallback to localStorage...');
        const knowledgeData = JSON.parse(knowledgeDataStr);
        data = knowledgeData.find(k => k.id === parseInt(id));
        if (data) {
          logger.warn('[DETAIL] Using localStorage data (may be outdated)');
        }
      }
    }

    if (!data) {
      logger.error('[DETAIL] No data found for ID:', id);  // 🔍 デバッグログ追加
      showError(`ナレッジID ${id} が見つかりません`);
      return;
    }

    logger.log('[KNOWLEDGE DETAIL] Data before display:', JSON.stringify(data, null, 2));  // 🔍 完全なデータをログ
    logger.log('[KNOWLEDGE DETAIL] Displaying data...');
    displayKnowledgeDetail(data);
    await loadRelatedKnowledge(data.tags || [], id);
    loadKnowledgeCommentsFromData(data);
    loadKnowledgeHistoryFromData(data);
    // incrementViewCount(id); // 一旦コメントアウト
  } catch (error) {
    logger.error('[KNOWLEDGE DETAIL] Error:', error);
    showError(`データの読み込みに失敗しました: ${error.message}`);
  } finally {
    hideLoading();
  }
}

function displayKnowledgeDetail(data) {
  logger.log('[DISPLAY] displayKnowledgeDetail called with data:', data);  // 🔍 デバッグログ追加
  logger.log('[DISPLAY] Title:', data?.title);
  logger.log('[DISPLAY] Summary:', data?.summary);
  logger.log('[DISPLAY] Content length:', data?.content?.length);

  // タイトル
  const titleEl = document.getElementById('knowledgeTitle');
  logger.log('[DISPLAY] titleEl found:', !!titleEl);  // 🔍 要素存在確認
  if (titleEl) {
    const titleText = data.title || 'タイトルなし';
    titleEl.textContent = titleText;
    logger.log('[DISPLAY] Title set to:', titleText);  // 🔍 設定確認
  }

  // メタ情報
  const metaEl = document.getElementById('knowledgeMeta');
  if (metaEl) {
    setSecureChildren(metaEl, createMetaInfoElement({
      category: data.category || 'N/A',
      updated_at: data.updated_at,
      created_by: data.created_by || data.created_by_name || data.owner || 'N/A',  // 🔧 owner追加
      project: data.project || 'N/A'
    }, 'knowledge'));
  }

  // タグ
  const tagsEl = document.getElementById('knowledgeTags');
  if (tagsEl && data.tags) {
    // 既存の内容をクリア
    while (tagsEl.firstChild) {
      tagsEl.removeChild(tagsEl.firstChild);
    }
    data.tags.forEach(tag => {
      const tagSpan = document.createElement('span');
      tagSpan.className = 'tag';
      tagSpan.textContent = tag;
      tagsEl.appendChild(tagSpan);
    });
  }

  // 概要
  const summaryEl = document.getElementById('knowledgeSummary');
  if (summaryEl) {
    // 既存の内容をクリア
    while (summaryEl.firstChild) {
      summaryEl.removeChild(summaryEl.firstChild);
    }
    const p = document.createElement('p');
    p.textContent = data.summary || '概要がありません';
    summaryEl.appendChild(p);
  }

  // 本文
  const contentEl = document.getElementById('knowledgeContent');
  if (contentEl) {
    // 既存の内容をクリア
    while (contentEl.firstChild) {
      contentEl.removeChild(contentEl.firstChild);
    }
    const div = document.createElement('div');
    div.style.whiteSpace = 'pre-wrap';
    div.textContent = data.content || '内容がありません';
    contentEl.appendChild(div);
  }

  // メタデータテーブル
  const metadataTable = document.getElementById('metadataTable');
  if (metadataTable) {
    const rows = [
      { label: '作成日', value: formatDate(data.created_at) },
      { label: '最終更新', value: formatDate(data.updated_at) },
      { label: '作成者', value: data.created_by || data.created_by_name || data.owner || 'N/A' },  // 🔧 owner追加
      { label: 'カテゴリ', value: data.category || 'N/A' },
      { label: 'プロジェクト', value: data.project || 'N/A' },
      { label: 'ステータス', value: data.status || '公開' }
    ];
    // 🔧 修正: createTableRowに配列として渡す
    setSecureChildren(metadataTable, rows.map(row => createTableRow([row.label, row.value])));
  }

  // 統計情報
  updateElement('totalLikes', data.likes || data.likes_count || 0);
  updateElement('totalBookmarks', data.bookmarks_count || 0);
  updateElement('totalViews', data.views || data.views_count || 0);
  updateElement('viewCount', `閲覧数 ${data.views || data.views_count || 0}`);

  // 承認フロー
  displayApprovalFlow(data.approval_status);

  // パンくずリスト更新
  updateBreadcrumb(data.category, data.title);

  // 🆕 パンくずエリアのメタ情報を更新
  updateBreadcrumbMeta(data);

  // 🆕 左側ナビゲーションの情報を更新
  updateNavigationInfo(data);
}

/**
 * パンくずエリアのメタ情報を更新
 * @param {Object} data - ナレッジデータ
 */
function updateBreadcrumbMeta(data) {
  // ステータスバッジ（ラベル付き）
  const statusText = {
    'approved': '承認状態: ✓ 承認済み',
    'pending': '承認状態: ⏳ 承認待ち',
    'draft': '承認状態: 📝 下書き',
    'archived': '承認状態: 📦 アーカイブ'
  }[data.status] || `承認状態: ${data.status}` || '承認状態: 承認済み';
  updateElement('breadcrumbStatus', statusText);

  // 優先度バッジ（ラベル付き）
  const priorityText = {
    'high': '優先度: 🔴 高',
    'medium': '優先度: 🟡 中',
    'low': '優先度: 🟢 低'
  }[data.priority] || `優先度: ${data.priority}` || '優先度: 中';
  const priorityEl = document.getElementById('breadcrumbPriority');
  if (priorityEl) {
    priorityEl.textContent = priorityText;
    priorityEl.setAttribute('data-priority', data.priority || 'medium');
  }

  // カテゴリ（ラベル付き）
  updateElement('breadcrumbCategory', data.category ? `📋 ${data.category}` : '📋 カテゴリなし');

  // 最終更新日時（ラベル付き）
  updateElement('breadcrumbUpdated', data.updated_at ? `📅 最終更新: ${formatDateShort(data.updated_at)}` : '');

  // 閲覧数（新規追加）
  const viewCount = data.views || data.views_count || 0;
  updateElement('breadcrumbViews', `👁️ 閲覧: ${viewCount}回`);
}

/**
 * 左側ナビゲーションの詳細情報を更新
 * @param {Object} data - ナレッジデータ
 */
function updateNavigationInfo(data) {
  // 概要の文字数
  const summaryLength = (data.summary || '').length;
  updateElement('navSummaryInfo', summaryLength > 0 ? `${summaryLength}文字` : '未記載');

  // 本文の文字数と推定読了時間（日本語：600文字/分）
  const contentLength = (data.content || '').length;
  const readingTime = Math.ceil(contentLength / 600);
  updateElement('navContentInfo',
    contentLength > 0 ? `${contentLength}文字・約${readingTime}分` : '未記載'
  );

  // 編集履歴件数
  const historyCount = (data.history || data.versions || []).length;
  updateElement('navHistoryInfo', historyCount > 0 ? `${historyCount}件` : 'なし');

  // コメント件数
  const commentCount = data.comments_count || (data.comments || []).length || 0;
  updateElement('navCommentsInfo', `${commentCount}件`);

  // 関連ナレッジ件数（後で更新される）
  updateElement('navRelatedInfo', '読込中...');
}

async function loadRelatedKnowledge(tags, currentId) {
  const relatedListEl = document.getElementById('relatedKnowledgeList');
  if (!relatedListEl) return;

  // 🚀 本番環境対応: 専用API使用（パフォーマンス最適化）
  try {
    logger.log('[RELATED] Loading related knowledge from dedicated API...');

    // 専用API: /api/v1/knowledge/{id}/related
    const response = await apiCall(`/knowledge/${currentId}/related?limit=5`);
    logger.log('[RELATED] Full API response:', response);

    // 🔧 既存APIのレスポンス構造に対応
    const responseData = response?.data || response || {};
    const relatedItems = responseData.related_items || responseData.data || responseData || [];

    logger.log('[RELATED] API returned:', relatedItems.length, 'items');
    logger.log('[RELATED] Algorithm:', responseData.algorithm);

    if (relatedItems.length > 0) {
      setSecureChildren(relatedListEl, relatedItems.map(item =>
        createDocumentElement(item, 'search-detail.html')
      ));
      // 🆕 関連ナレッジ件数を更新
      updateElement('navRelatedInfo', `${relatedItems.length}件`);
      logger.log('[RELATED] Successfully displayed', relatedItems.length, 'related items');
    } else {
      setSecureChildren(relatedListEl, createEmptyMessage('関連ナレッジが見つかりませんでした'));
      updateElement('navRelatedInfo', '0件');
      logger.log('[RELATED] No related items found');
    }
  } catch (error) {
    logger.error('[RELATED] Failed to load related knowledge:', error);
    setSecureChildren(relatedListEl, createErrorMessage('関連ナレッジの読み込みに失敗しました'));
    updateElement('navRelatedInfo', 'エラー');
  }
}

/**
 * コメントをlocalStorageのデータから読み込む
 */
function loadKnowledgeCommentsFromData(data) {
  const commentListEl = document.getElementById('commentList');
  const commentCountEl = document.getElementById('commentCount');
  if (!commentListEl) return;

  const comments = data.comments || [];
  if (commentCountEl) commentCountEl.textContent = comments.length;

  if (comments.length > 0) {
    setSecureChildren(commentListEl, comments.map(comment => createCommentElement(comment)));
  } else {
    setSecureChildren(commentListEl, createEmptyMessage('コメントがありません'));
  }
}

/**
 * 編集履歴をlocalStorageのデータから読み込む
 */
function loadKnowledgeHistoryFromData(data) {
  const historyTableEl = document.getElementById('historyTable');
  if (!historyTableEl) return;

  const history = data.edit_history || [];

  if (history.length > 0) {
    setSecureChildren(historyTableEl, history.map((item, index) =>
      createTableRowWithHTML([
        `v${item.version || (history.length - index)}`,
        formatDate(item.edited_at || item.updated_at),
        item.edited_by || item.updated_by_name || 'N/A',
        item.changes || item.change_summary || '更新',
        '<button class="cta ghost" onclick="alert(\'バージョン表示機能は準備中です\')">表示</button>'
      ])
    ));
  } else {
    setSecureChildren(historyTableEl, createEmptyMessage('履歴がありません', 5));
  }
}

async function loadKnowledgeComments(knowledgeId) {
  const commentListEl = document.getElementById('commentList');
  const commentCountEl = document.getElementById('commentCount');
  if (!commentListEl) return;

  try {
    const comments = await apiCall(`/knowledge/${knowledgeId}/comments`);
    if (commentCountEl) commentCountEl.textContent = comments.length;

    if (comments.length > 0) {
      setSecureChildren(commentListEl, comments.map(comment => createCommentElement(comment)));
    } else {
      setSecureChildren(commentListEl, createEmptyMessage('コメントがありません'));
    }
  } catch (error) {
    logger.error('Failed to load comments:', error);
    setSecureChildren(commentListEl, createErrorMessage('コメントの読み込みに失敗しました'));
  }
}

async function loadKnowledgeHistory(knowledgeId) {
  const historyTableEl = document.getElementById('historyTable');
  if (!historyTableEl) return;

  try {
    const history = await apiCall(`/knowledge/${knowledgeId}/history`);
    if (history && history.length > 0) {
      setSecureChildren(historyTableEl, history.map((item, index) =>
        createTableRowWithHTML([
          `v${item.version || (history.length - index)}`,
          formatDate(item.updated_at),
          item.updated_by_name || 'N/A',
          item.change_summary || '更新',
          `<button class="cta ghost" onclick="viewVersion(${item.id})">表示</button>`
        ])
      ));
    } else {
      setSecureChildren(historyTableEl, createEmptyMessage('履歴がありません', 5));
    }
  } catch (error) {
    logger.error('Failed to load history:', error);
    setSecureChildren(historyTableEl, createErrorMessage('履歴の読み込みに失敗しました', 5));
  }
}

async function submitComment() {
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');
  const commentEl = document.getElementById('newComment');

  if (!commentEl || !commentEl.value.trim()) {
    showToast('コメントを入力してください', 'warning');
    return;
  }

  try {
    // localStorageにコメントを保存
    const commentsKey = `knowledge_comments_${id}`;
    const existingComments = JSON.parse(localStorage.getItem(commentsKey) || '[]');

    const newComment = {
      id: Date.now(),
      content: commentEl.value.trim(),
      created_by: localStorage.getItem('user_name') || '現場作業員A',
      created_at: new Date().toISOString(),
      user_role: localStorage.getItem('user_role') || '作業員'
    };

    existingComments.push(newComment);
    localStorage.setItem(commentsKey, JSON.stringify(existingComments));

    // API呼び出しも試みる（エラーは無視）
    try {
      await apiCall(`/knowledge/${id}/comments`, {
        method: 'POST',
        body: JSON.stringify({ content: commentEl.value })
      });
    } catch (apiError) {
      logger.log('[COMMENT] API call failed, using localStorage only');
    }

    commentEl.value = '';
    await loadKnowledgeComments(id);
    showToast('コメントを投稿しました', 'success');
  } catch (error) {
    showToast(`コメントの投稿に失敗しました: ${error.message}`, 'error');
  }
}

async function toggleBookmark() {
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  if (!id) {
    showToast('IDが取得できません', 'error');
    return;
  }

  const bookmarkKey = `knowledge_bookmark_${id}`;
  const currentState = localStorage.getItem(bookmarkKey) === 'true';
  const newState = !currentState;

  try {
    // localStorageに保存
    localStorage.setItem(bookmarkKey, newState.toString());

    // UIを更新
    const icon = document.getElementById('bookmarkIcon');
    if (icon) {
      icon.textContent = newState ? '★' : '☆';
    }

    // API呼び出しも試みる（エラーは無視）
    try {
      await apiCall(`/knowledge/${id}/bookmark`, { method: 'POST' });
    } catch (apiError) {
      logger.log('[BOOKMARK] API call failed, using localStorage only');
    }

    showToast(newState ? 'ブックマークに追加しました' : 'ブックマークを解除しました', 'success');
  } catch (error) {
    showToast(`ブックマークの切り替えに失敗しました: ${error.message}`, 'error');
  }
}

async function toggleLike() {
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  if (!id) {
    showToast('IDが取得できません', 'error');
    return;
  }

  const likeKey = `knowledge_like_${id}`;
  const likeCountKey = `knowledge_like_count_${id}`;
  const currentState = localStorage.getItem(likeKey) === 'true';
  const newState = !currentState;

  try {
    // localStorageに保存
    localStorage.setItem(likeKey, newState.toString());

    // いいね数を更新
    let currentCount = parseInt(localStorage.getItem(likeCountKey) || '0');
    currentCount = newState ? currentCount + 1 : Math.max(0, currentCount - 1);
    localStorage.setItem(likeCountKey, currentCount.toString());

    // UIを更新
    const icon = document.getElementById('likeIcon');
    const countEl = document.getElementById('likeCount');
    const totalLikesEl = document.getElementById('totalLikes');

    if (icon) {
      icon.textContent = newState ? '♥' : '♡';
    }
    if (countEl) {
      countEl.textContent = currentCount;
    }
    if (totalLikesEl) {
      totalLikesEl.textContent = currentCount;
    }

    // API呼び出しも試みる（エラーは無視）
    try {
      const result = await apiCall(`/knowledge/${id}/like`, { method: 'POST' });
      if (result && result.likes_count !== undefined) {
        localStorage.setItem(likeCountKey, result.likes_count.toString());
        if (countEl) countEl.textContent = result.likes_count;
        if (totalLikesEl) totalLikesEl.textContent = result.likes_count;
      }
    } catch (apiError) {
      logger.log('[LIKE] API call failed, using localStorage only');
    }

    showToast(newState ? 'いいねしました' : 'いいねを解除しました', 'success');
  } catch (error) {
    showToast(`いいねの切り替えに失敗しました: ${error.message}`, 'error');
  }
}

async function incrementViewCount(id) {
  try {
    await apiCall(`/knowledge/${id}/view`, { method: 'POST' });
  } catch (error) {
    // APIエラーは無視（ダミーデータ表示時は正常）
    logger.log('[VIEW COUNT] Skipped (using dummy data)');
  }
}

function shareKnowledge() {
  const modal = document.getElementById('shareModal');
  const shareUrlEl = document.getElementById('shareUrl');
  if (modal && shareUrlEl) {
    shareUrlEl.value = window.location.href;
    modal.classList.add('is-active');
  }
}

function closeShareModal() {
  const modal = document.getElementById('shareModal');
  if (modal) modal.classList.remove('is-active');
}

function copyShareUrl() {
  const shareUrlEl = document.getElementById('shareUrl');
  if (shareUrlEl) {
    shareUrlEl.select();
    document.execCommand('copy');
    showToast('URLをコピーしました', 'success');
  }
}

function printPage() {
  window.print();
}

function exportPDF() {
  showToast('PDFを生成中...', 'info');
  setTimeout(() => {
    window.print();
  }, 500);
}

function retryLoad() {
  window.location.reload();
}

// ============================================================
// sop-detail.html 専用機能
// ============================================================

async function loadSOPDetail() {
  logger.log('[SOP DETAIL] Starting to load...');
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');
  const inProduction = isProductionMode();

  logger.log('[SOP DETAIL] ID from URL:', id, 'Production mode:', inProduction);

  if (!id) {
    showError('SOP IDが指定されていません。一覧ページに戻ります...');
    setTimeout(() => {
      window.location.href = 'index.html';
    }, 2000);
    return;
  }

  showLoading();
  hideError();

  try {
    let data = null;

    // 🔧 修正: 開発環境でもAPI優先に変更（ナレッジと統一）
    logger.log('[DETAIL] Loading SOP from API (data consistency fix)...');
    try {
      const response = await apiCall(`/sop/${id}`);
      logger.log('[DETAIL] API Response:', response);

      // 🔧 修正: APIレスポンスから data プロパティを抽出
      data = response?.data || response;

      logger.log('[DETAIL] Extracted data:', data);
      logger.log('[DETAIL] Successfully loaded from API');
    } catch (apiError) {
      logger.error('[DETAIL] API call failed:', apiError);

      // APIが失敗した場合のみlocalStorageにフォールバック
      const sopDataStr = localStorage.getItem('sop_details');
      if (sopDataStr) {
        logger.log('[DETAIL] Fallback to localStorage...');
        const sopData = JSON.parse(sopDataStr);
        data = sopData.find(s => s.id === parseInt(id));
        if (data) {
          logger.warn('[DETAIL] Using localStorage data (may be outdated)');
        }
      } else {
        logger.log('[DETAIL] Loading SOP from localStorage...');
      }
    }

    if (!data) {
      showError(`SOP ID ${id} が見つかりません`);
      return;
    }

    logger.log('[SOP DETAIL] Displaying data...');
    displaySOPDetail(data);
    await loadRelatedSOP(data.category, id);

    // 実施統計を更新
    if (typeof updateExecutionStats === 'function') {
      updateExecutionStats();
    }
  } catch (error) {
    logger.error('[SOP DETAIL] Error:', error);
    showError(`データの読み込みに失敗しました: ${error.message}`);
  } finally {
    hideLoading();
  }
}

function displaySOPDetail(data) {
  // タイトル
  updateElement('sopTitle', data.title || 'SOPタイトル');

  // ヘッダー情報
  const sopNumber = data.sop_number || data.title.match(/SOP-(\d+)/)?.[1] || 'N/A';
  updateElement('sopNumber', `SOP番号 ${sopNumber}`);
  updateElement('sopVersion', `バージョン ${data.version || 'v1.0'}`);

  // メタ情報
  const metaEl = document.getElementById('sopMeta');
  if (metaEl) {
    setSecureChildren(metaEl, createMetaInfoElement({
      revision_date: data.revision_date || data.updated_at,
      category: data.category || 'N/A',
      target: data.target || data.scope || 'N/A'
    }, 'sop'));
  }

  // タグ
  const tagsEl = document.getElementById('sopTags');
  if (tagsEl && data.tags) {
    setSecureChildren(tagsEl, data.tags.map(tag => createTagElement(tag)));
  }

  // 目的
  updateElement('sopPurpose', data.purpose || '目的が記載されていません');

  // 適用範囲
  updateElement('sopScope', data.scope || '適用範囲が記載されていません');

  // バージョン情報
  const versionInfoEl = document.getElementById('versionInfo');
  if (versionInfoEl) {
    const rows = [
      { label: 'バージョン', value: data.version || 'v1.0' },
      { label: '改訂日', value: formatDateShort(data.revision_date || data.updated_at) },
      { label: '次回改訂予定', value: formatDateShort(data.next_revision_date) || 'N/A' }
    ];
    // 🔧 修正: createTableRowに配列として渡す
    setSecureChildren(versionInfoEl, rows.map(row => createTableRow([row.label, row.value])));
  }

  // 手順（localStorageデータはsteps配列を持つ）
  const procedureEl = document.getElementById('sopProcedure');
  if (procedureEl) {
    const steps = data.steps || data.procedure || [];
    if (Array.isArray(steps) && steps.length > 0) {
      setSecureChildren(procedureEl, steps.map((step, i) => createStepElement(step, i)));
    } else if (typeof steps === 'string') {
      setSecureChildren(procedureEl, createSecureElement('div', {}, [steps]));
    } else {
      setSecureChildren(procedureEl, createEmptyMessage('手順データがありません'));
    }
  }

  // チェックリスト
  const checklistEl = document.getElementById('sopChecklist');
  if (checklistEl && data.checklist) {
    if (Array.isArray(data.checklist)) {
      setSecureChildren(checklistEl, data.checklist.map(item => createChecklistElement(item)));
    } else {
      setSecureChildren(checklistEl, createSecureElement('div', {}, [data.checklist]));
    }
  }

  // 注意事項（localStorageデータはprecautions配列を持つ）
  const warningsEl = document.getElementById('sopWarnings');
  if (warningsEl) {
    const warnings = data.precautions || data.warnings || [];
    if (Array.isArray(warnings) && warnings.length > 0) {
      setSecureChildren(warningsEl, warnings.map(warning => createWarningElement(warning)));
    } else if (typeof warnings === 'string') {
      setSecureChildren(warningsEl, createWarningElement(warnings));
    } else {
      setSecureChildren(warningsEl, createEmptyMessage('注意事項がありません'));
    }
  }

  // 改訂履歴（localStorageデータはrevision_history配列を持つ）
  const revisionHistoryEl = document.getElementById('revisionHistory');
  if (revisionHistoryEl && data.revision_history) {
    if (Array.isArray(data.revision_history)) {
      setSecureChildren(revisionHistoryEl, data.revision_history.map(rev =>
        createTableRowWithHTML([
          rev.version || 'N/A',
          rev.date || formatDateShort(rev.updated_at),
          rev.changes || 'N/A',
          rev.author || 'N/A',
          '<button class="cta ghost" onclick="alert(\'バージョン表示機能は準備中です\')">表示</button>'
        ])
      ));
    }
  }

  // 必要資材・工具
  const equipmentEl = document.getElementById('sopEquipment');
  if (equipmentEl && data.equipment) {
    if (Array.isArray(data.equipment)) {
      setSecureChildren(equipmentEl, data.equipment.map(item => createPillElement(item)));
    } else {
      setSecureChildren(equipmentEl, createPillElement(data.equipment));
    }
  }

  // 所要時間
  updateElement('prepTime', data.prep_time || '--');
  updateElement('workTime', data.work_time || '--');
  updateElement('totalTime', data.duration || '--');

  // 統計
  updateElement('executionCount', data.execution_count || 0);
  updateElement('complianceRate', data.compliance_rate || 0);

  // 承認フロー
  displayApprovalFlow(data.approval_status);

  // パンくずリスト更新
  updateBreadcrumb('SOP', data.title);
}

async function loadRelatedSOP(category, currentId) {
  const relatedListEl = document.getElementById('relatedSOPList');
  if (!relatedListEl) return;

  // 新しいAPI推薦システムを試行
  if (typeof loadRelatedSOPFromAPI === 'function') {
    try {
      await loadRelatedSOPFromAPI(currentId, 'hybrid', 5);
      return; // 成功したら終了
    } catch (error) {
      logger.warn('API recommendation failed, falling back to localStorage:', error);
    }
  }

  // フォールバック: 既存のlocalStorage方式
  try {
    // まずlocalStorageから関連SOPを取得
    const sopData = JSON.parse(localStorage.getItem('sop_details') || '[]');
    const currentSOP = sopData.find(s => s.id === parseInt(currentId));

    let relatedItems = [];

    if (currentSOP && currentSOP.related_sops) {
      // related_sops を使用
      relatedItems = currentSOP.related_sops
        .map(relatedId => sopData.find(s => s.id === relatedId))
        .filter(item => item)
        .slice(0, 5);
    } else if (category) {
      // カテゴリベースで検索
      relatedItems = sopData
        .filter(s => s.id !== parseInt(currentId))
        .filter(s => s.category === category)
        .slice(0, 5);
    }

    if (relatedItems.length > 0) {
      setSecureChildren(relatedListEl, relatedItems.map(item =>
        createDocumentElement(item, 'sop-detail.html')
      ));
    } else {
      setSecureChildren(relatedListEl, createEmptyMessage('関連SOPが見つかりませんでした'));
    }
  } catch (error) {
    logger.error('Failed to load related SOP:', error);
    setSecureChildren(relatedListEl, createErrorMessage('関連SOPの読み込みに失敗しました'));
  }
}

function startInspectionRecord() {
  const formEl = document.getElementById('record-form');
  if (formEl) {
    formEl.style.display = 'block';

    // 現在の日時をセット
    const now = new Date();
    const dateInput = document.getElementById('recordDate');
    if (dateInput) {
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const day = String(now.getDate()).padStart(2, '0');
      const hours = String(now.getHours()).padStart(2, '0');
      const minutes = String(now.getMinutes()).padStart(2, '0');
      dateInput.value = `${year}-${month}-${day}T${hours}:${minutes}`;
    }

    // チェックリスト項目をフォームに追加
    const recordChecklistEl = document.getElementById('recordChecklist');
    const sopChecklistEl = document.getElementById('sopChecklist');
    if (recordChecklistEl && sopChecklistEl) {
      const checkboxes = sopChecklistEl.querySelectorAll('input[type="checkbox"]');
      const container = createSecureElement('div', { className: 'checklist' });
      const items = [];
      checkboxes.forEach((checkbox, index) => {
        const labelText = checkbox.nextSibling ? checkbox.nextSibling.textContent : `項目 ${index + 1}`;
        const label = createSecureElement('label', { className: 'checkbox-item' });
        const input = createSecureElement('input', {
          type: 'checkbox',
          name: `recordCheck${index}`,
          checked: checkbox.checked
        });
        label.appendChild(input);
        label.appendChild(document.createTextNode(' ' + labelText));
        items.push(label);
      });
      setSecureChildren(container, items);
      setSecureChildren(recordChecklistEl, container);
    }

    formEl.scrollIntoView({ behavior: 'smooth' });

    // フォーム送信イベントリスナー設定
    const formElement = document.getElementById('inspectionForm');
    if (formElement && !formElement.hasAttribute('data-listener-attached')) {
      formElement.addEventListener('submit', submitInspectionRecord);
      formElement.setAttribute('data-listener-attached', 'true');
    }
  }
}

function cancelRecord() {
  const formEl = document.getElementById('record-form');
  if (formEl) {
    formEl.style.display = 'none';

    // フォームをリセット
    const formElement = document.getElementById('inspectionForm');
    if (formElement) {
      formElement.reset();
    }
  }
}

function submitInspectionRecord(event) {
  event.preventDefault();

  const recordDate = document.getElementById('recordDate').value;
  const recordWorker = document.getElementById('recordWorker').value;
  const recordProject = document.getElementById('recordProject').value;
  const recordContent = document.getElementById('recordContent').value;
  const recordNotes = document.getElementById('recordNotes').value;

  // チェック項目を収集
  const checkItems = [];
  const checkboxes = document.querySelectorAll('#recordChecklist input[type="checkbox"]');
  checkboxes.forEach((checkbox, index) => {
    const label = checkbox.nextSibling ? checkbox.nextSibling.textContent.trim() : `項目 ${index + 1}`;
    checkItems.push({
      item: label,
      checked: checkbox.checked
    });
  });

  // SOPのIDを取得
  const urlParams = new URLSearchParams(window.location.search);
  const sopId = urlParams.get('id');

  // 記録データを作成
  const recordData = {
    id: Date.now(),
    sop_id: sopId,
    date: recordDate,
    worker: recordWorker,
    project: recordProject,
    content: recordContent,
    checklist: checkItems,
    notes: recordNotes,
    created_at: new Date().toISOString()
  };

  // localStorageに保存
  const recordsKey = 'sop_inspection_records';
  const existingRecords = JSON.parse(localStorage.getItem(recordsKey) || '[]');
  existingRecords.push(recordData);
  localStorage.setItem(recordsKey, JSON.stringify(existingRecords));

  // 成功メッセージ
  if (typeof showToast === 'function') {
    showToast('実施記録を保存しました', 'success');
  } else if (typeof showNotification === 'function') {
    showNotification('実施記録を保存しました', 'success');
  }

  // フォームをリセットして非表示
  cancelRecord();

  // 実施統計を更新
  updateExecutionStats();
}

function updateExecutionStats() {
  // 実施統計を再計算
  const urlParams = new URLSearchParams(window.location.search);
  const sopId = urlParams.get('id');
  const recordsKey = 'sop_inspection_records';
  const allRecords = JSON.parse(localStorage.getItem(recordsKey) || '[]');
  const sopRecords = allRecords.filter(r => r.sop_id === sopId);

  // 実施回数
  const executionCountEl = document.getElementById('executionCount');
  if (executionCountEl) {
    executionCountEl.textContent = sopRecords.length;
  }

  // 適合率（すべてのチェック項目がチェックされた記録の割合）
  const complianceRateEl = document.getElementById('complianceRate');
  if (complianceRateEl && sopRecords.length > 0) {
    const compliantRecords = sopRecords.filter(record => {
      if (!record.checklist || record.checklist.length === 0) return false;
      return record.checklist.every(item => item.checked);
    });
    const rate = Math.round((compliantRecords.length / sopRecords.length) * 100);
    complianceRateEl.textContent = rate;
  }
}

function downloadSOP() {
  // window.print()を使用してPDF保存
  if (typeof downloadPDF === 'function') {
    downloadPDF('sop', document.getElementById('sopTitle')?.textContent || 'SOP');
  } else {
    window.print();
  }

  if (typeof showToast === 'function') {
    showToast('印刷ダイアログを開きました。PDFとして保存できます。', 'info');
  }
}

function printChecklist() {
  const checklistEl = document.getElementById('sopChecklist');
  const titleEl = document.getElementById('sopTitle');

  if (checklistEl) {
    const printWindow = window.open('', '', 'height=600,width=800');
    const title = titleEl ? titleEl.textContent : 'チェックリスト';

    printWindow.document.write(`
      <html>
        <head>
          <title>${title} - チェックリスト</title>
          <style>
            body {
              font-family: 'Hiragino Kaku Gothic ProN', 'Meiryo', sans-serif;
              padding: 20px;
              line-height: 1.6;
            }
            h1 {
              font-size: 18px;
              margin-bottom: 20px;
              border-bottom: 2px solid #333;
              padding-bottom: 10px;
            }
            .checklist {
              display: flex;
              flex-direction: column;
              gap: 10px;
            }
            .checkbox-item {
              display: flex;
              align-items: center;
              padding: 8px;
              border: 1px solid #ddd;
            }
            input[type="checkbox"] {
              margin-right: 10px;
              width: 18px;
              height: 18px;
            }
            @media print {
              body { padding: 0; }
            }
          </style>
        </head>
        <body>
          <h1>${title} - チェックリスト</h1>
          ${checklistEl.outerHTML}
          <script>
            window.onload = function() {
              window.print();
            };
          </script>
        </body>
      </html>
    `);
    printWindow.document.close();
  }
}

function editSOP() {
  const modal = document.getElementById('editSOPModal');
  if (!modal) return;

  // 既存データを取得してフォームに設定
  const title = document.getElementById('sopTitle')?.textContent || '';
  const purpose = document.getElementById('sopPurpose')?.textContent || '';
  const scope = document.getElementById('sopScope')?.textContent || '';

  document.getElementById('editSOPTitle').value = title;
  document.getElementById('editSOPPurpose').value = purpose;
  document.getElementById('editSOPScope').value = scope;
  document.getElementById('editSOPChanges').value = '';
  document.getElementById('editSOPReason').value = '';

  // モーダルを表示
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closeEditSOPModal() {
  const modal = document.getElementById('editSOPModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

function submitEditSOP(event) {
  event.preventDefault();

  const urlParams = new URLSearchParams(window.location.search);
  const sopId = urlParams.get('id');

  const proposalData = {
    id: Date.now(),
    sop_id: sopId,
    title: document.getElementById('editSOPTitle').value,
    purpose: document.getElementById('editSOPPurpose').value,
    scope: document.getElementById('editSOPScope').value,
    changes: document.getElementById('editSOPChanges').value,
    reason: document.getElementById('editSOPReason').value,
    proposer: localStorage.getItem('user_name') || '不明',
    status: '提案中',
    created_at: new Date().toISOString()
  };

  // localStorageに保存
  const proposalsKey = 'sop_revision_proposals';
  const existingProposals = JSON.parse(localStorage.getItem(proposalsKey) || '[]');
  existingProposals.push(proposalData);
  localStorage.setItem(proposalsKey, JSON.stringify(existingProposals));

  // 成功メッセージ
  if (typeof showToast === 'function') {
    showToast('改訂提案を送信しました', 'success');
  } else if (typeof showNotification === 'function') {
    showNotification('改訂提案を送信しました', 'success');
  }

  closeEditSOPModal();
}

function retryLoadSOP() {
  window.location.reload();
}

// ============================================================
// incident-detail.html 専用機能
// ============================================================

async function loadIncidentDetail() {
  logger.log('[INCIDENT DETAIL] Starting to load...');
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');
  const inProduction = isProductionMode();

  logger.log('[INCIDENT DETAIL] ID from URL:', id, 'Production mode:', inProduction);

  if (!id) {
    showError('事故レポートIDが指定されていません。一覧ページに戻ります...');
    setTimeout(() => {
      window.location.href = 'index.html';
    }, 2000);
    return;
  }

  showLoading();
  hideError();

  try {
    let data = null;

    // 🔧 修正: 開発環境でもAPI優先に変更（ナレッジと統一）
    logger.log('[DETAIL] Loading incident from API (data consistency fix)...');
    try {
      const response = await apiCall(`/incident/${id}`);
      logger.log('[DETAIL] API Response:', response);

      // 🔧 修正: APIレスポンスから data プロパティを抽出
      data = response?.data || response;

      logger.log('[DETAIL] Extracted data:', data);
      logger.log('[DETAIL] Successfully loaded from API');
    } catch (apiError) {
      logger.error('[DETAIL] API call failed:', apiError);

      // APIが失敗した場合のみlocalStorageにフォールバック
      const incidentDataStr = localStorage.getItem('incidents_details');
      if (incidentDataStr) {
        logger.log('[DETAIL] Fallback to localStorage...');
        const incidentData = JSON.parse(incidentDataStr);
        data = incidentData.find(i => i.id === parseInt(id));
        if (data) {
          logger.warn('[DETAIL] Using localStorage data (may be outdated)');
        }
      }
    }

    if (!data) {
      showError(`事故レポートID ${id} が見つかりません`);
      return;
    }

    logger.log('[INCIDENT DETAIL] Displaying data...');
    displayIncidentDetail(data);
    loadCorrectiveActionsFromData(data);
  } catch (error) {
    logger.error('[INCIDENT DETAIL] Error:', error);
    showError(`データの読み込みに失敗しました: ${error.message}`);
  } finally {
    hideLoading();
  }
}

function displayIncidentDetail(data) {
  // タイトル
  updateElement('incidentTitle', data.title || '事故レポートタイトル');

  // ヘッダー情報
  const incidentNumber = data.incident_number || `INC-${data.id}`;
  updateElement('incidentNumber', `報告No. ${incidentNumber}`);
  updateElement('incidentSeverity', `重大度 ${data.severity || 'N/A'}`);

  // メタ情報
  const metaEl = document.getElementById('incidentMeta');
  if (metaEl) {
    setSecureChildren(metaEl, createMetaInfoElement({
      occurred_at: data.occurred_at || data.incident_date,
      location: data.location || 'N/A',
      reporter: data.reporter || data.reporter_name || 'N/A',
      type: data.type || 'N/A'
    }, 'incident'));
  }

  // タグ
  const tagsEl = document.getElementById('incidentTags');
  if (tagsEl && data.tags) {
    setSecureChildren(tagsEl, data.tags.map(tag => createTagElement(tag)));
  }

  // 概要
  updateElement('incidentSummary', data.description || data.summary || '概要がありません');

  // 発生情報
  const incidentInfoEl = document.getElementById('incidentInfo');
  if (incidentInfoEl) {
    const rows = [
      { label: '発生日時', value: formatDate(data.occurred_at || data.incident_date) },
      { label: '発生場所', value: data.location || 'N/A' },
      { label: '種類', value: data.type || 'N/A' },
      { label: '重大度', value: data.severity || 'N/A' },
      { label: 'ステータス', value: data.status || 'N/A' }
    ];
    // 🔧 修正: createTableRowに配列として渡す
    setSecureChildren(incidentInfoEl, rows.map(row => createTableRow([row.label, row.value])));
  }

  // タイムライン（localStorageデータはtimeline配列を持つ）
  const timelineEl = document.getElementById('incidentTimeline');
  if (timelineEl && data.timeline) {
    if (Array.isArray(data.timeline)) {
      setSecureChildren(timelineEl, data.timeline.map(event => createTimelineElement(event)));
    } else {
      setSecureChildren(timelineEl, createSecureElement('div', {}, [data.timeline]));
    }
  }

  // 原因分析（localStorageデータはroot_causes配列を持つ）
  if (data.root_causes && Array.isArray(data.root_causes)) {
    const causeAnalysisEl = document.getElementById('causeAnalysis');
    if (causeAnalysisEl) {
      const causesByCategory = {
        man: [],
        machine: [],
        media: [],
        management: []
      };

      // ランダムに4Mに振り分け（簡易実装）
      data.root_causes.forEach((cause, i) => {
        const categories = ['man', 'machine', 'media', 'management'];
        const category = categories[i % categories.length];
        causesByCategory[category].push(cause);
      });

      updateElement('causeMan', causesByCategory.man.length > 0 ? causesByCategory.man.join('<br>') : '分析なし');
      updateElement('causeMachine', causesByCategory.machine.length > 0 ? causesByCategory.machine.join('<br>') : '分析なし');
      updateElement('causeMedia', causesByCategory.media.length > 0 ? causesByCategory.media.join('<br>') : '分析なし');
      updateElement('causeManagement', causesByCategory.management.length > 0 ? causesByCategory.management.join('<br>') : '分析なし');
    }
  }

  // KPI
  updateElement('completionRate', data.completion_rate || 0);
  updateElement('deadlineRate', data.deadline_rate || 0);
  updateElement('remainingTasks', data.remaining_tasks || 0);

  // 承認フロー
  displayApprovalFlow(data.approval_status);

  // パンくずリスト更新
  updateBreadcrumb('事故レポート', data.title);
}

/**
 * 是正措置をlocalStorageのデータから読み込む
 */
function loadCorrectiveActionsFromData(data) {
  const tableEl = document.getElementById('correctiveActionTable');
  if (!tableEl) return;

  const actions = data.corrective_actions || [];

  if (actions.length > 0) {
    setSecureChildren(tableEl, actions.map(action => {
      const statusClass = action.status === 'completed' ? 'is-ok' : action.status === 'in_progress' ? 'is-warn' : 'is-hold';
      const statusText = action.status === 'completed' ? '完了' : action.status === 'in_progress' ? '進行中' : '未着手';
      return createTableRowWithHTML([
        `<span class="status-dot ${statusClass}"></span> ${statusText}`,
        action.action || action.content,
        action.responsible || action.assignee_name || 'N/A',
        formatDateShort(action.deadline),
        `${action.progress || (action.status === 'completed' ? 100 : action.status === 'in_progress' ? 50 : 0)}%`,
        '<button class="cta ghost" onclick="alert(\'是正措置更新機能は準備中です\')">更新</button>'
      ]);
    }));

    // KPI更新
    const completedCount = actions.filter(a => a.status === 'completed').length;
    const completionRate = Math.round((completedCount / actions.length) * 100);
    const onTimeCount = actions.filter(a => a.status === 'completed' && new Date(a.deadline) >= new Date()).length;
    const deadlineRate = actions.length > 0 ? Math.round((onTimeCount / actions.length) * 100) : 0;
    const remainingTasks = actions.filter(a => a.status !== 'completed').length;

    updateElement('completionRate', completionRate);
    updateElement('deadlineRate', deadlineRate);
    updateElement('remainingTasks', remainingTasks);
  } else {
    setSecureChildren(tableEl, createEmptyMessage('是正措置がありません', 6));
  }
}

async function loadCorrectiveActions(incidentId) {
  const tableEl = document.getElementById('correctiveActionTable');
  if (!tableEl) return;

  try {
    const actions = await apiCall(`/incident/${incidentId}/corrective-actions`);
    if (actions && actions.length > 0) {
      setSecureChildren(tableEl, actions.map(action => {
        const statusClass = action.status === 'completed' ? 'is-ok' : 'is-warn';
        return createTableRowWithHTML([
          `<span class="status-dot ${statusClass}"></span>`,
          action.content,
          action.assignee_name || 'N/A',
          formatDateShort(action.deadline),
          `${action.progress || 0}%`,
          '<button class="cta ghost" onclick="alert(\'是正措置更新機能は準備中です\')">更新</button>'
        ]);
      }));
    } else {
      setSecureChildren(tableEl, createEmptyMessage('是正措置がありません', 6));
    }
  } catch (error) {
    logger.error('Failed to load corrective actions:', error);
    setSecureChildren(tableEl, createErrorMessage('是正措置の読み込みに失敗しました', 6));
  }
}

function addCorrectiveAction() {
  const modal = document.getElementById('correctiveActionModal');
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    // フォームリセット
    document.getElementById('correctiveActionForm').reset();
  }
}

function closeCorrectiveActionModal() {
  const modal = document.getElementById('correctiveActionModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

function submitCorrectiveAction(event) {
  event.preventDefault();

  const content = document.getElementById('actionContent').value;
  const assignee = document.getElementById('actionAssignee').value;
  const deadline = document.getElementById('actionDeadline').value;
  const priority = document.getElementById('actionPriority').value;

  // URLパラメータから現在のincident IDを取得
  const urlParams = new URLSearchParams(window.location.search);
  const incidentId = parseInt(urlParams.get('id'));

  // localStorageから事故データを取得
  const incidentsStr = localStorage.getItem('incidents_details');
  if (!incidentsStr) {
    showToast('データの読み込みに失敗しました', 'error');
    return;
  }

  const incidents = JSON.parse(incidentsStr);
  const incident = incidents.find(i => i.id === incidentId);

  if (!incident) {
    showToast('事故レポートが見つかりません', 'error');
    return;
  }

  // 新しい是正措置を追加
  if (!incident.corrective_actions) {
    incident.corrective_actions = [];
  }

  const newAction = {
    id: incident.corrective_actions.length + 1,
    action: content,
    content: content,
    responsible: assignee,
    assignee_name: assignee,
    deadline: deadline,
    priority: priority,
    status: 'pending',
    progress: 0,
    created_at: new Date().toISOString()
  };

  incident.corrective_actions.push(newAction);

  // localStorageに保存
  localStorage.setItem('incidents_details', JSON.stringify(incidents));

  // モーダルを閉じる
  closeCorrectiveActionModal();

  // ページをリロードして表示を更新
  showToast('是正措置を追加しました', 'success');
  setTimeout(() => {
    window.location.reload();
  }, 1000);
}

function downloadPDF(type) {
  showToast('PDFを生成中...', 'info');

  // 印刷ダイアログを開く（ブラウザの印刷→PDF保存機能を利用）
  setTimeout(() => {
    window.print();
  }, 500);
}

function shareIncident() {
  const modal = document.getElementById('shareModal');
  const shareUrlEl = document.getElementById('shareUrl');
  if (modal && shareUrlEl) {
    shareUrlEl.value = window.location.href;
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }
}

function closeShareModal() {
  const modal = document.getElementById('shareModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

function copyShareUrl() {
  const shareUrlEl = document.getElementById('shareUrl');
  if (shareUrlEl) {
    shareUrlEl.select();
    document.execCommand('copy');

    // Clipboard APIも試行
    if (navigator.clipboard) {
      navigator.clipboard.writeText(shareUrlEl.value).then(() => {
        showToast('URLをコピーしました', 'success');
      }).catch(() => {
        showToast('URLをコピーしました', 'success');
      });
    } else {
      showToast('URLをコピーしました', 'success');
    }
  }
}

function shareViaEmail() {
  const url = document.getElementById('shareUrl').value;
  const urlParams = new URLSearchParams(window.location.search);
  const incidentId = urlParams.get('id');
  const subject = encodeURIComponent(`事故レポート共有: INC-${incidentId}`);
  const body = encodeURIComponent(`事故レポートを共有します。\n\n${url}`);
  window.location.href = `mailto:?subject=${subject}&body=${body}`;
  showToast('メールアプリを起動しました', 'info');
}

function shareViaSlack() {
  const url = document.getElementById('shareUrl').value;
  showToast('Slack連携機能は準備中です\nURL: ' + url, 'info');
  // 実際の実装では Slack API や Webhook を使用
}

function shareViaTeams() {
  const url = document.getElementById('shareUrl').value;
  showToast('Teams連携機能は準備中です\nURL: ' + url, 'info');
  // 実際の実装では Microsoft Teams API を使用
}

function updateIncidentStatus() {
  const modal = document.getElementById('statusModal');
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    document.getElementById('newStatus').value = '';
    document.getElementById('statusComment').value = '';
  }
}

function closeStatusModal() {
  const modal = document.getElementById('statusModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

function submitStatusUpdate() {
  const newStatus = document.getElementById('newStatus').value;
  const comment = document.getElementById('statusComment').value;

  if (!newStatus) {
    showToast('ステータスを選択してください', 'warning');
    return;
  }

  // URLパラメータから現在のincident IDを取得
  const urlParams = new URLSearchParams(window.location.search);
  const incidentId = parseInt(urlParams.get('id'));

  // localStorageから事故データを取得
  const incidentsStr = localStorage.getItem('incidents_details');
  if (!incidentsStr) {
    showToast('データの読み込みに失敗しました', 'error');
    return;
  }

  const incidents = JSON.parse(incidentsStr);
  const incident = incidents.find(i => i.id === incidentId);

  if (!incident) {
    showToast('事故レポートが見つかりません', 'error');
    return;
  }

  // ステータスを更新
  incident.status = newStatus;
  incident.status_updated_at = new Date().toISOString();
  if (comment) {
    if (!incident.status_history) {
      incident.status_history = [];
    }
    incident.status_history.push({
      status: newStatus,
      comment: comment,
      updated_at: new Date().toISOString(),
      updated_by: localStorage.getItem('username') || 'Unknown'
    });
  }

  // localStorageに保存
  localStorage.setItem('incidents_details', JSON.stringify(incidents));

  // モーダルを閉じる
  closeStatusModal();

  // ページをリロードして表示を更新
  showToast(`ステータスを「${newStatus}」に更新しました`, 'success');
  setTimeout(() => {
    window.location.reload();
  }, 1000);
}

function openNewIncidentModal() {
  const modal = document.getElementById('newIncidentModal');
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    document.getElementById('newIncidentForm').reset();
    // デフォルトで現在日時を設定
    const now = new Date();
    const localDateTime = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    document.getElementById('newIncidentDate').value = localDateTime;
  }
}

function closeNewIncidentModal() {
  const modal = document.getElementById('newIncidentModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

function submitNewIncident(event) {
  event.preventDefault();

  const title = document.getElementById('newIncidentTitle').value;
  const date = document.getElementById('newIncidentDate').value;
  const location = document.getElementById('newIncidentLocation').value;
  const severity = document.getElementById('newIncidentSeverity').value;
  const content = document.getElementById('newIncidentContent').value;

  // localStorageから事故データを取得
  const incidentsStr = localStorage.getItem('incidents_details');
  const incidents = incidentsStr ? JSON.parse(incidentsStr) : [];

  // 新しいIDを生成
  const maxId = incidents.length > 0 ? Math.max(...incidents.map(i => i.id)) : 0;
  const newId = maxId + 1;

  // 新しい事故レポートを作成
  const newIncident = {
    id: newId,
    incident_number: `INC-${newId.toString().padStart(4, '0')}`,
    title: title,
    occurred_at: date,
    incident_date: date,
    location: location,
    severity: severity,
    description: content,
    summary: content,
    status: '調査中',
    reporter: localStorage.getItem('username') || 'Unknown',
    reporter_name: localStorage.getItem('username') || 'Unknown',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    type: '作業事故',
    tags: ['新規'],
    timeline: [
      {
        time: date,
        event: '事故発生',
        details: content
      },
      {
        time: new Date().toISOString(),
        event: 'レポート作成',
        details: 'システムに登録されました'
      }
    ],
    root_causes: [],
    corrective_actions: [],
    completion_rate: 0,
    deadline_rate: 0,
    remaining_tasks: 0
  };

  incidents.push(newIncident);

  // localStorageに保存
  localStorage.setItem('incidents_details', JSON.stringify(incidents));

  // モーダルを閉じる
  closeNewIncidentModal();

  // 新しいレポートのページに遷移
  showToast('新規事故レポートを作成しました', 'success');
  setTimeout(() => {
    window.location.href = `incident-detail.html?id=${newId}`;
  }, 1000);
}

function editIncident() {
  const modal = document.getElementById('editIncidentModal');
  if (!modal) return;

  // URLパラメータから現在のincident IDを取得
  const urlParams = new URLSearchParams(window.location.search);
  const incidentId = parseInt(urlParams.get('id'));

  // localStorageから事故データを取得
  const incidentsStr = localStorage.getItem('incidents_details');
  if (!incidentsStr) {
    showToast('データの読み込みに失敗しました', 'error');
    return;
  }

  const incidents = JSON.parse(incidentsStr);
  const incident = incidents.find(i => i.id === incidentId);

  if (!incident) {
    showToast('事故レポートが見つかりません', 'error');
    return;
  }

  // フォームに既存データを設定
  document.getElementById('editIncidentTitle').value = incident.title || '';

  // 日時をdatetime-local形式に変換
  const incidentDate = incident.occurred_at || incident.incident_date;
  if (incidentDate) {
    const date = new Date(incidentDate);
    const localDateTime = new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    document.getElementById('editIncidentDate').value = localDateTime;
  }

  document.getElementById('editIncidentLocation').value = incident.location || '';
  document.getElementById('editIncidentSeverity').value = incident.severity || '';
  document.getElementById('editIncidentContent').value = incident.description || incident.summary || '';

  // モーダルを表示
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closeEditIncidentModal() {
  const modal = document.getElementById('editIncidentModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

function submitEditIncident(event) {
  event.preventDefault();

  const title = document.getElementById('editIncidentTitle').value;
  const date = document.getElementById('editIncidentDate').value;
  const location = document.getElementById('editIncidentLocation').value;
  const severity = document.getElementById('editIncidentSeverity').value;
  const content = document.getElementById('editIncidentContent').value;

  // URLパラメータから現在のincident IDを取得
  const urlParams = new URLSearchParams(window.location.search);
  const incidentId = parseInt(urlParams.get('id'));

  // localStorageから事故データを取得
  const incidentsStr = localStorage.getItem('incidents_details');
  if (!incidentsStr) {
    showToast('データの読み込みに失敗しました', 'error');
    return;
  }

  const incidents = JSON.parse(incidentsStr);
  const incident = incidents.find(i => i.id === incidentId);

  if (!incident) {
    showToast('事故レポートが見つかりません', 'error');
    return;
  }

  // データを更新
  incident.title = title;
  incident.occurred_at = date;
  incident.incident_date = date;
  incident.location = location;
  incident.severity = severity;
  incident.description = content;
  incident.summary = content;
  incident.updated_at = new Date().toISOString();

  // localStorageに保存
  localStorage.setItem('incidents_details', JSON.stringify(incidents));

  // モーダルを閉じる
  closeEditIncidentModal();

  // ページをリロードして表示を更新
  showToast('事故レポートを更新しました', 'success');
  setTimeout(() => {
    window.location.reload();
  }, 1000);
}

function retryLoadIncident() {
  window.location.reload();
}

// ============================================================
// expert-consult.html 専用機能
// ============================================================

async function loadConsultDetail() {
  logger.log('[CONSULT DETAIL] Starting to load...');
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');
  const inProduction = isProductionMode();

  logger.log('[CONSULT DETAIL] ID from URL:', id, 'Production mode:', inProduction);

  if (!id) {
    showError('相談IDが指定されていません。一覧ページに戻ります...');
    setTimeout(() => {
      window.location.href = 'index.html';
    }, 2000);
    return;
  }

  showLoading();
  hideError();

  try {
    let data = null;

    // 🔧 修正: 開発環境でもAPI優先に変更（ナレッジと統一）
    logger.log('[DETAIL] Loading consultation from API (data consistency fix)...');
    try {
      // 🔧 修正: 複数形のエンドポイントに修正（/consultation/ → /consultations/）
      const response = await apiCall(`/consultations/${id}`);
      logger.log('[DETAIL] API Response:', response);

      // 🔧 修正: APIレスポンスから data プロパティを抽出
      data = response?.data || response;

      logger.log('[DETAIL] Extracted data:', data);
      logger.log('[DETAIL] Successfully loaded from API');
    } catch (apiError) {
      logger.error('[DETAIL] API call failed:', apiError);

      // APIが失敗した場合のみlocalStorageにフォールバック
      const consultDataStr = localStorage.getItem('consultations_details');
      if (consultDataStr) {
        logger.log('[DETAIL] Fallback to localStorage...');
        const consultData = JSON.parse(consultDataStr);
        data = consultData.find(c => c.id === parseInt(id));
        if (data) {
          logger.warn('[DETAIL] Using localStorage data (may be outdated)');
        }
      }
    }

    if (!data) {
      showError(`相談ID ${id} が見つかりません`);
      return;
    }

    logger.log('[CONSULT DETAIL] Displaying data...');
    displayConsultDetail(data);
    loadAnswersFromData(data);
    await loadRelatedQuestions(data.tags || [], id);
  } catch (error) {
    logger.error('[CONSULT DETAIL] Error:', error);
    showError(`データの読み込みに失敗しました: ${error.message}`);
  } finally {
    hideLoading();
  }
}

function displayConsultDetail(data) {
  // タイトル
  updateElement('consultTitle', data.title || '相談タイトル');

  // ヘッダー情報
  const statusText = data.status === 'answered' ? '回答済み' : data.status === 'pending' ? '受付中' : data.status;
  updateElement('consultStatus', `ステータス ${statusText}`);

  // 回答時間計算
  const responseTime = data.answers && data.answers.length > 0
    ? calculateResponseTime(data.created_at, data.answers[0].created_at)
    : '--';
  updateElement('responseTime', `回答時間 ${responseTime}時間`);

  // メタ情報
  const metaEl = document.getElementById('consultMeta');
  if (metaEl) {
    setSecureChildren(metaEl, createMetaInfoElement({
      created_at: data.created_at,
      requester: data.requester || data.author_name || 'N/A',
      category: data.category || 'N/A',
      project: data.project || 'N/A'
    }, 'consult'));
  }

  // タグ
  const tagsEl = document.getElementById('consultTags');
  if (tagsEl && data.tags) {
    setSecureChildren(tagsEl, data.tags.map(tag => createTagElement(tag)));
  }

  // 質問内容（🔧 修正：questionとcontentの両方に対応）
  updateElement('questionContent', data.question || data.content || '質問内容がありません');

  // 相談情報
  const consultInfoEl = document.getElementById('consultInfo');
  if (consultInfoEl) {
    const rows = [
      { label: '投稿日', value: formatDate(data.created_at) },
      { label: '投稿者', value: data.requester || data.author_name || 'N/A' },
      { label: 'カテゴリ', value: data.category || 'N/A' },
      { label: 'プロジェクト', value: data.project || 'N/A' },
      { label: 'ステータス', value: statusText }
    ];
    // 🔧 修正: createTableRowに配列として渡す
    setSecureChildren(consultInfoEl, rows.map(row => createTableRow([row.label, row.value])));
  }

  // 優先度・期限
  updateElement('priority', data.priority || '通常');
  updateElement('deadline', formatDateShort(data.deadline) || 'N/A');
  updateElement('elapsedTime', calculateElapsedTime(data.created_at));

  // 統計
  const answerCount = data.answers ? data.answers.length : data.answer_count || 0;
  updateElement('totalAnswers', answerCount);
  updateElement('answerCount', answerCount);
  updateElement('viewCount', data.views || data.view_count || 0);
  updateElement('followerCount', data.follower_count || 0);

  // 回答率・平均回答時間
  updateElement('responseRate', data.response_rate || 85);
  updateElement('avgResponseTime', data.avg_response_time || 4);

  // エキスパート情報
  displayExpertInfoConsult(data);

  // ベストアンサー
  displayBestAnswerConsult(data);

  // 参考SOP
  displayReferenceSOPConsult(data);

  // 添付ファイル
  displayConsultAttachments(data);

  // ステータス履歴
  displayConsultStatusHistory(data);

  // パンくずリスト更新
  updateBreadcrumb('専門家相談', data.title);
}

/**
 * エキスパート情報を表示
 */
async function displayExpertInfoConsult(data) {
  const expertInfoEl = document.getElementById('expertInfo');
  if (!expertInfoEl) return;

  let expert = data.expert_info;

  // 🔧 修正：expert_idからexperts.jsonのデータを取得
  if (!expert && data.expert_id) {
    try {
      // APIからエキスパート情報を取得
      const response = await apiCall(`/experts/${data.expert_id}`);
      expert = response?.data || response;
    } catch (error) {
      logger.warn('[EXPERT] Failed to load expert data:', error);
    }
  }

  // フォールバック：データがない場合はプレースホルダー
  if (!expert) {
    expert = {
      name: data.expert || 'エキスパート未割当',
      title: '-',
      department: '-',
      specialties: [],
      response_count: 0,
      rating: 0
    };
  }

  setSecureChildren(expertInfoEl, createExpertInfoElement(expert));
}

/**
 * ベストアンサーを表示
 */
function displayBestAnswerConsult(data) {
  const bestAnswerEl = document.getElementById('bestAnswer');
  if (!bestAnswerEl) return;

  const bestAnswer = data.answers?.find(a => a.is_best_answer);

  if (bestAnswer) {
    setSecureChildren(bestAnswerEl, createBestAnswerElement(bestAnswer));
  } else {
    setSecureChildren(bestAnswerEl, createEmptyMessage('まだベストアンサーが選択されていません'));
  }
}

/**
 * 参考SOPを表示
 */
function displayReferenceSOPConsult(data) {
  const referenceSOPEl = document.getElementById('referenceSOP');
  if (!referenceSOPEl) return;

  const referenceDocs = data.reference_sops || [
    { id: 1, title: 'コンクリート打設管理SOP', category: '品質管理' },
    { id: 2, title: '養生作業手順書', category: '施工手順' }
  ];

  if (referenceDocs.length > 0) {
    setSecureChildren(referenceSOPEl, referenceDocs.map(doc =>
      createDocumentElement(doc, 'sop-detail.html')
    ));
  } else {
    setSecureChildren(referenceSOPEl, createEmptyMessage('参考SOPがありません'));
  }
}

/**
 * 添付ファイルを表示
 */
function displayConsultAttachments(data) {
  const attachmentListEl = document.getElementById('attachmentList');
  if (!attachmentListEl) return;

  const attachments = data.attachments || [];

  if (attachments.length > 0) {
    setSecureChildren(attachmentListEl, attachments.map(file =>
      createAttachmentElement(file)
    ));
  } else {
    setSecureChildren(attachmentListEl, createEmptyMessage('添付ファイルがありません'));
  }
}

/**
 * ステータス履歴を表示
 */
function displayConsultStatusHistory(data) {
  const statusHistoryEl = document.getElementById('statusHistory');
  if (!statusHistoryEl) return;

  const history = data.status_history || [
    { status: '受付', timestamp: data.created_at, user: data.requester || 'ユーザー' },
    { status: '専門家割当', timestamp: data.created_at, user: 'システム' }
  ];

  if (history.length > 0) {
    setSecureChildren(statusHistoryEl, history.map(item =>
      createStatusHistoryElement(item)
    ));
  } else {
    setSecureChildren(statusHistoryEl, createEmptyMessage('履歴がありません'));
  }
}

/**
 * 回答時間を計算
 */
function calculateResponseTime(createdAt, firstAnswerAt) {
  if (!createdAt || !firstAnswerAt) return '--';
  const created = new Date(createdAt);
  const answered = new Date(firstAnswerAt);
  const diffMs = answered - created;
  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  return hours;
}

/**
 * 回答をlocalStorageのデータから読み込む
 */
function loadAnswersFromData(data) {
  const answerListEl = document.getElementById('answerList');
  const answerCountEl = document.getElementById('answerCount');
  if (!answerListEl) return;

  const answers = data.answers || [];
  if (answerCountEl) answerCountEl.textContent = answers.length;

  if (answers.length > 0) {
    setSecureChildren(answerListEl, answers.map(answer => createAnswerElement(answer, answer.is_best_answer || answer.is_best)));
  } else {
    setSecureChildren(answerListEl, createEmptyMessage('まだ回答がありません'));
  }
}

async function loadAnswers(consultId) {
  const answerListEl = document.getElementById('answerList');
  const answerCountEl = document.getElementById('answerCount');
  if (!answerListEl) return;

  try {
    const answers = await apiCall(`/consultation/${consultId}/answers`);
    if (answerCountEl) answerCountEl.textContent = answers.length;

    if (answers.length > 0) {
      setSecureChildren(answerListEl, answers.map(answer => createAnswerElement(answer, answer.is_best)));
    } else {
      setSecureChildren(answerListEl, createEmptyMessage('まだ回答がありません'));
    }
  } catch (error) {
    logger.error('Failed to load answers:', error);
    setSecureChildren(answerListEl, createErrorMessage('回答の読み込みに失敗しました'));
  }
}

async function loadRelatedQuestions(tags, currentId) {
  const relatedEl = document.getElementById('relatedQuestions');
  if (!relatedEl) return;

  try {
    // まずlocalStorageから関連質問を取得
    const consultData = JSON.parse(localStorage.getItem('consultations_details') || '[]');

    let relatedItems = [];

    if (tags && tags.length > 0) {
      // タグベースで検索
      relatedItems = consultData
        .filter(c => c.id !== parseInt(currentId))
        .filter(c => c.tags && c.tags.some(tag => tags.includes(tag)))
        .slice(0, 5);
    } else {
      // タグがない場合はカテゴリベース
      const current = consultData.find(c => c.id === parseInt(currentId));
      if (current) {
        relatedItems = consultData
          .filter(c => c.id !== parseInt(currentId))
          .filter(c => c.category === current.category)
          .slice(0, 5);
      }
    }

    if (relatedItems.length > 0) {
      setSecureChildren(relatedEl, relatedItems.map(item =>
        createDocumentElement(item, 'expert-consult.html')
      ));
    } else {
      setSecureChildren(relatedEl, createEmptyMessage('関連質問が見つかりませんでした'));
    }
  } catch (error) {
    logger.error('Failed to load related questions:', error);
    setSecureChildren(relatedEl, createErrorMessage('関連質問の読み込みに失敗しました'));
  }
}

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

function retryLoadConsult() {
  window.location.reload();
}

// ============================================================
// 共通機能
// ============================================================

function updateElement(id, value) {
  const el = document.getElementById(id);
  if (el) {
    if (typeof value === 'object' && value !== null) {
      // オブジェクトの場合はDOM要素として追加
      if (value instanceof Node) {
        setSecureChildren(el, value);
      } else {
        // 配列またはその他のオブジェクトの場合は文字列化
        el.textContent = String(value);
      }
    } else {
      el.textContent = value;
    }
  }
}

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
  const statusMap = {
    'done': 'is-done',
    'wait': 'is-wait',
    'hold': 'is-hold',
    'info': 'is-info'
  };

  const flowData = Array.isArray(flow) ? flow : defaultFlow;
  setSecureChildren(flowEl, flowData.map(item => createApprovalFlowElement(item, statusMap)));
}

function updateBreadcrumb(category, title) {
  const breadcrumbEl = document.getElementById('breadcrumbList');
  if (!breadcrumbEl) return;

  const items = [
    createSecureElement('li', {}, [
      createSecureElement('a', { href: 'index.html' }, ['ホーム'])
    ]),
    createSecureElement('li', {}, [
      createSecureElement('a', { href: `index.html#${category}` }, [category])
    ]),
    createSecureElement('li', { 'aria-current': 'page' }, [title || '詳細'])
  ];
  setSecureChildren(breadcrumbEl, items);
}

// ============================================================
// PDF保存機能
// ============================================================

/**
 * PDFダウンロード機能
 * @param {string} pageType - 'incident', 'sop', 'knowledge', 'consult'
 */
function downloadPDF(pageType) {
  try {
    // PDFファイル名生成
    const now = new Date();
    const dateStr = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`;
    const filename = `${pageType}-report-${dateStr}.pdf`;

    // ブラウザの印刷機能を使用（最も簡単な方法）
    window.print();

    // 成功通知
    showNotification(`PDFの印刷ダイアログを開きました`, 'success');
  } catch (error) {
    logger.error('PDF generation error:', error);
    showNotification('PDF保存に失敗しました', 'error');
  }
}

// ============================================================
// 共有機能
// ============================================================

/**
 * ナレッジ共有モーダルを開く
 */
function shareKnowledge() {
  openShareModal();
}

/**
 * SOP共有モーダルを開く
 */
function shareSOP() {
  openShareModal();
}

/**
 * 事故レポート共有モーダルを開く
 */
function shareIncident() {
  openShareModal();
}

/**
 * 専門家相談共有モーダルを開く
 */
function shareConsult() {
  openShareModal();
}

/**
 * 共有モーダルを開く（共通処理）
 */
function openShareModal() {
  const modal = document.getElementById('shareModal');
  const shareUrlEl = document.getElementById('shareUrl');

  if (modal && shareUrlEl) {
    // 現在のURLを共有URLとして設定
    shareUrlEl.value = window.location.href;
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  } else {
    // モーダルが存在しない場合は動的に作成
    createShareModal();
  }
}

/**
 * 共有モーダルを動的に作成
 */
function createShareModal() {
  const modal = createSecureElement('div', {
    id: 'shareModal',
    className: 'modal',
    style: 'display: flex;'
  });

  const modalContent = createSecureElement('div', { className: 'modal-content' });

  // ヘッダー
  const header = createSecureElement('div', { className: 'modal-header' }, [
    createSecureElement('h2', {}, ['共有']),
    createSecureElement('button', {
      className: 'modal-close',
      onclick: 'closeShareModal()'
    }, ['×'])
  ]);

  // ボディ
  const body = createSecureElement('div', { className: 'modal-body' });

  const urlField = createSecureElement('div', { className: 'field' }, [
    createSecureElement('label', {}, ['共有URL']),
    createSecureElement('div', { style: 'display: flex; gap: 10px;' }, [
      createSecureElement('input', {
        type: 'text',
        id: 'shareUrl',
        readonly: true,
        value: window.location.href,
        style: 'flex: 1;'
      }),
      createSecureElement('button', {
        className: 'cta secondary',
        onclick: 'copyShareUrl()'
      }, ['コピー'])
    ])
  ]);

  const shareField = createSecureElement('div', { className: 'field' }, [
    createSecureElement('label', {}, ['共有方法']),
    createSecureElement('div', { style: 'display: flex; gap: 10px; margin-top: 10px;' }, [
      createSecureElement('button', { className: 'cta ghost', onclick: 'shareByEmail()' }, ['📧 メール']),
      createSecureElement('button', { className: 'cta ghost', onclick: 'shareBySlack()' }, ['💬 Slack']),
      createSecureElement('button', { className: 'cta ghost', onclick: 'shareByTeams()' }, ['👥 Teams'])
    ])
  ]);

  setSecureChildren(body, [urlField, shareField]);

  // フッター
  const actions = createSecureElement('div', { className: 'modal-actions' }, [
    createSecureElement('button', { className: 'cta ghost', onclick: 'closeShareModal()' }, ['閉じる'])
  ]);

  setSecureChildren(modalContent, [header, body, actions]);
  setSecureChildren(modal, modalContent);

  document.body.appendChild(modal);
  document.body.style.overflow = 'hidden';

  // モーダル外クリックで閉じる
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      closeShareModal();
    }
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
 * 共有URLをクリップボードにコピー
 */
function copyShareUrl() {
  const shareUrlEl = document.getElementById('shareUrl');
  if (shareUrlEl) {
    shareUrlEl.select();
    shareUrlEl.setSelectionRange(0, 99999); // モバイル対応

    // クリップボードAPIを使用
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(shareUrlEl.value)
        .then(() => {
          showNotification('URLをクリップボードにコピーしました', 'success');
        })
        .catch(() => {
          // フォールバック: execCommand
          document.execCommand('copy');
          showNotification('URLをコピーしました', 'success');
        });
    } else {
      // 古いブラウザ対応
      document.execCommand('copy');
      showNotification('URLをコピーしました', 'success');
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
  showToast('メールアプリを開きます...', 'info');
}

/**
 * Slackで共有（ダミー処理）
 */
function shareBySlack() {
  showToast('Slack連携機能は準備中です', 'info');
  // 将来実装: Slack Webhook or Slack APIを利用してナレッジを共有
  // - バックエンドに /api/v1/integrations/slack/share エンドポイントを追加
  // - ナレッジのタイトル、URL、概要をSlackチャンネルに投稿
  // Issue: Phase D機能として実装予定
}

/**
 * Microsoft Teamsで共有（ダミー処理）
 */
function shareByTeams() {
  showToast('Teams連携機能は準備中です', 'info');
  // 将来実装: Microsoft Graph APIを利用してナレッジを共有
  // - バックエンドに /api/v1/integrations/teams/share エンドポイントを追加
  // - ナレッジのタイトル、URL、概要をTeamsチャンネルに投稿
  // Issue: Phase D機能として実装予定
}

// ============================================================
// 新規作成モーダル機能
// ============================================================

/**
 * 新規事故レポート作成モーダルを開く
 */
function openNewIncidentModal() {
  const modal = document.getElementById('newIncidentModal');
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  } else {
    createNewIncidentModal();
  }
}

/**
 * 新規事故レポート作成モーダルを作成
 */
function createNewIncidentModal() {
  const modal = createSecureElement('div', {
    id: 'newIncidentModal',
    className: 'modal',
    style: 'display: flex;'
  });

  const modalContent = createSecureElement('div', { className: 'modal-content' });

  const header = createSecureElement('div', { className: 'modal-header' }, [
    createSecureElement('h2', {}, ['新規事故レポート作成']),
    createSecureElement('button', { className: 'modal-close', onclick: 'closeNewIncidentModal()' }, ['×'])
  ]);

  const form = createSecureElement('form', { id: 'newIncidentForm', onsubmit: 'submitNewIncident(event)' });

  const body = createSecureElement('div', { className: 'modal-body' }, [
    createSecureElement('div', { className: 'field' }, [
      createSecureElement('label', {}, ['タイトル ', createSecureElement('span', { className: 'required' }, ['*'])]),
      createSecureElement('input', { type: 'text', id: 'incidentNewTitle', required: true, placeholder: '例: 足場倒壊事故' })
    ]),
    createSecureElement('div', { className: 'field' }, [
      createSecureElement('label', {}, ['発生日時 ', createSecureElement('span', { className: 'required' }, ['*'])]),
      createSecureElement('input', { type: 'datetime-local', id: 'incidentNewDate', required: true })
    ]),
    createSecureElement('div', { className: 'field' }, [
      createSecureElement('label', {}, ['発生場所 ', createSecureElement('span', { className: 'required' }, ['*'])]),
      createSecureElement('input', { type: 'text', id: 'incidentNewLocation', required: true, placeholder: '例: A工区 3階' })
    ]),
    createSecureElement('div', { className: 'field' }, [
      createSecureElement('label', {}, ['重大度 ', createSecureElement('span', { className: 'required' }, ['*'])]),
      createSecureElement('select', { id: 'incidentNewSeverity', required: true }, [
        createSecureElement('option', { value: '' }, ['選択してください']),
        createSecureElement('option', { value: '低' }, ['低']),
        createSecureElement('option', { value: '中' }, ['中']),
        createSecureElement('option', { value: '高' }, ['高']),
        createSecureElement('option', { value: '重大' }, ['重大'])
      ])
    ]),
    createSecureElement('div', { className: 'field' }, [
      createSecureElement('label', {}, ['事故内容 ', createSecureElement('span', { className: 'required' }, ['*'])]),
      createSecureElement('textarea', { id: 'incidentNewContent', required: true, rows: '6', placeholder: '事故の詳細を記入してください...' })
    ]),
    createSecureElement('div', { className: 'field' }, [
      createSecureElement('label', {}, ['写真・資料']),
      createSecureElement('input', { type: 'file', id: 'incidentNewPhotos', multiple: true, accept: 'image/*,.pdf' }),
      createSecureElement('small', {}, ['画像またはPDFファイル（最大10MB）'])
    ])
  ]);

  const actions = createSecureElement('div', { className: 'modal-actions' }, [
    createSecureElement('button', { type: 'button', className: 'cta ghost', onclick: 'closeNewIncidentModal()' }, ['キャンセル']),
    createSecureElement('button', { type: 'submit', className: 'cta' }, ['作成'])
  ]);

  setSecureChildren(form, [body, actions]);
  setSecureChildren(modalContent, [header, form]);
  setSecureChildren(modal, modalContent);

  document.body.appendChild(modal);
  document.body.style.overflow = 'hidden';

  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      closeNewIncidentModal();
    }
  });

  const dateInput = document.getElementById('incidentNewDate');
  if (dateInput) {
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    dateInput.value = now.toISOString().slice(0, 16);
  }
}

/**
 * 新規事故レポート作成モーダルを閉じる
 */
function closeNewIncidentModal() {
  const modal = document.getElementById('newIncidentModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
    // フォームリセット
    const form = document.getElementById('newIncidentForm');
    if (form) form.reset();
  }
}

/**
 * 新規事故レポートを送信
 */
async function submitNewIncident(event) {
  event.preventDefault();

  const title = document.getElementById('incidentNewTitle').value;
  const date = document.getElementById('incidentNewDate').value;
  const location = document.getElementById('incidentNewLocation').value;
  const severity = document.getElementById('incidentNewSeverity').value;
  const content = document.getElementById('incidentNewContent').value;

  const data = {
    title,
    occurred_at: date,
    location,
    severity,
    description: content,
    status: 'reported'
  };

  try {
    showNotification('事故レポートを作成中...', 'info');

    // APIに送信
    await apiCall('/incidents', {
      method: 'POST',
      body: JSON.stringify(data)
    });

    showNotification('事故レポートを作成しました', 'success');
    closeNewIncidentModal();

    // ページをリロード
    setTimeout(() => {
      window.location.reload();
    }, 1000);
  } catch (error) {
    logger.error('Failed to create incident:', error);
    showNotification(`事故レポートの作成に失敗しました: ${error.message}`, 'error');
  }
}

/**
 * 新規専門家相談作成モーダルを開く
 */
function openNewConsultationModal() {
  const modal = document.getElementById('newConsultationModal');
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  } else {
    createNewConsultationModal();
  }
}

/**
 * 新規専門家相談モーダルを作成
 */
function createNewConsultationModal() {
  const modal = createSecureElement('div', {
    id: 'newConsultationModal',
    className: 'modal',
    style: 'display: flex;'
  });

  const modalContent = createSecureElement('div', { className: 'modal-content' });

  const header = createSecureElement('div', { className: 'modal-header' }, [
    createSecureElement('h2', {}, ['新規専門家相談']),
    createSecureElement('button', { className: 'modal-close', onclick: 'closeNewConsultationModal()' }, ['×'])
  ]);

  const form = createSecureElement('form', { id: 'newConsultationForm', onsubmit: 'submitNewConsultation(event)' });

  const body = createSecureElement('div', { className: 'modal-body' }, [
    createSecureElement('div', { className: 'field' }, [
      createSecureElement('label', {}, ['質問タイトル ', createSecureElement('span', { className: 'required' }, ['*'])]),
      createSecureElement('input', { type: 'text', id: 'consultNewTitle', required: true, placeholder: '例: RC橋脚の配筋方法について' })
    ]),
    createSecureElement('div', { className: 'field' }, [
      createSecureElement('label', {}, ['カテゴリ ', createSecureElement('span', { className: 'required' }, ['*'])]),
      createSecureElement('select', { id: 'consultNewCategory', required: true }, [
        createSecureElement('option', { value: '' }, ['選択してください']),
        createSecureElement('option', { value: '構造設計' }, ['構造設計']),
        createSecureElement('option', { value: '施工管理' }, ['施工管理']),
        createSecureElement('option', { value: '品質管理' }, ['品質管理']),
        createSecureElement('option', { value: '安全管理' }, ['安全管理']),
        createSecureElement('option', { value: '環境対策' }, ['環境対策']),
        createSecureElement('option', { value: '地盤技術' }, ['地盤技術'])
      ])
    ]),
    createSecureElement('div', { className: 'field' }, [
      createSecureElement('label', {}, ['優先度 ', createSecureElement('span', { className: 'required' }, ['*'])]),
      createSecureElement('select', { id: 'consultNewPriority', required: true }, [
        createSecureElement('option', { value: '通常' }, ['通常']),
        createSecureElement('option', { value: '高' }, ['高']),
        createSecureElement('option', { value: '緊急' }, ['緊急'])
      ])
    ]),
    createSecureElement('div', { className: 'field' }, [
      createSecureElement('label', {}, ['質問内容 ', createSecureElement('span', { className: 'required' }, ['*'])]),
      createSecureElement('textarea', { id: 'consultNewContent', required: true, rows: '8', placeholder: '具体的な質問内容を記入してください...' }),
      createSecureElement('small', {}, ['できるだけ詳しく記述すると適切な回答が得られます'])
    ]),
    createSecureElement('div', { className: 'field' }, [
      createSecureElement('label', {}, ['添付ファイル']),
      createSecureElement('input', { type: 'file', id: 'consultNewAttachment', multiple: true, accept: 'image/*,.pdf,.xlsx,.dwg' }),
      createSecureElement('small', {}, ['画像、PDF、Excel、CADファイル（最大10MB）'])
    ])
  ]);

  const actions = createSecureElement('div', { className: 'modal-actions' }, [
    createSecureElement('button', { type: 'button', className: 'cta ghost', onclick: 'closeNewConsultationModal()' }, ['キャンセル']),
    createSecureElement('button', { type: 'submit', className: 'cta' }, ['相談を投稿'])
  ]);

  setSecureChildren(form, [body, actions]);
  setSecureChildren(modalContent, [header, form]);
  setSecureChildren(modal, modalContent);

  document.body.appendChild(modal);
  document.body.style.overflow = 'hidden';

  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      closeNewConsultationModal();
    }
  });
}

/**
 * 新規専門家相談モーダルを閉じる
 */
function closeNewConsultationModal() {
  const modal = document.getElementById('newConsultationModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
    // フォームリセット
    const form = document.getElementById('newConsultationForm');
    if (form) form.reset();
  }
}

/**
 * 新規専門家相談を送信
 */
async function submitNewConsultation(event) {
  if (event) {
    event.preventDefault();
  }

  // モーダルが存在する場合のみフォームデータを取得
  const titleEl = document.getElementById('consultNewTitle');
  const categoryEl = document.getElementById('consultNewCategory');
  const priorityEl = document.getElementById('consultNewPriority');
  const contentEl = document.getElementById('consultNewContent');

  if (!titleEl || !categoryEl || !priorityEl || !contentEl) {
    // モーダルが存在しない場合は作成して開く
    openNewConsultationModal();
    return;
  }

  const title = titleEl.value;
  const category = categoryEl.value;
  const priority = priorityEl.value;
  const content = contentEl.value;

  const data = {
    title,
    category,
    priority,
    content,
    status: 'pending'
  };

  try {
    showNotification('専門家相談を投稿中...', 'info');

    // APIに送信
    await apiCall('/consultations', {
      method: 'POST',
      body: JSON.stringify(data)
    });

    showNotification('専門家相談を投稿しました', 'success');
    closeNewConsultationModal();

    // ページをリロード
    setTimeout(() => {
      window.location.reload();
    }, 1000);
  } catch (error) {
    logger.error('Failed to create consultation:', error);
    showNotification(`相談の投稿に失敗しました: ${error.message}`, 'error');
  }
}

// ============================================================
// 編集機能（search-detail.html用）
// ============================================================

/**
 * ナレッジ編集モーダルを開く
 */
function editKnowledge() {
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  if (!id) {
    showToast('IDが取得できません', 'error');
    return;
  }

  // 現在のデータを取得
  const knowledgeDataStr = localStorage.getItem('knowledge_details');
  if (!knowledgeDataStr) {
    showToast('データが見つかりません', 'error');
    return;
  }

  const knowledgeData = JSON.parse(knowledgeDataStr);
  const currentData = knowledgeData.find(k => k.id === parseInt(id));

  if (!currentData) {
    showToast('データが見つかりません', 'error');
    return;
  }

  // フォームにデータを設定
  document.getElementById('editTitle').value = currentData.title || '';
  document.getElementById('editCategory').value = currentData.category || '技術資料';
  document.getElementById('editSummary').value = currentData.summary || '';
  document.getElementById('editContent').value = currentData.content || '';
  document.getElementById('editTags').value = Array.isArray(currentData.tags) ? currentData.tags.join(', ') : '';
  document.getElementById('editProject').value = currentData.project || '';

  // モーダルを表示
  const modal = document.getElementById('editModal');
  if (modal) {
    modal.classList.add('is-active');
  }
}

/**
 * 編集モーダルを閉じる
 */
function closeEditModal() {
  const modal = document.getElementById('editModal');
  if (modal) {
    modal.classList.remove('is-active');
  }
}

/**
 * ナレッジ編集を保存
 */
function saveKnowledgeEdit(event) {
  event.preventDefault();

  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  if (!id) {
    showToast('IDが取得できません', 'error');
    return;
  }

  try {
    // フォームデータを取得
    const updatedData = {
      title: document.getElementById('editTitle').value.trim(),
      category: document.getElementById('editCategory').value,
      summary: document.getElementById('editSummary').value.trim(),
      content: document.getElementById('editContent').value.trim(),
      tags: document.getElementById('editTags').value.split(',').map(t => t.trim()).filter(t => t),
      project: document.getElementById('editProject').value.trim(),
      updated_at: new Date().toISOString(),
      updated_by: localStorage.getItem('user_name') || '現場作業員A'
    };

    // localStorageのデータを更新
    const knowledgeDataStr = localStorage.getItem('knowledge_details');
    if (knowledgeDataStr) {
      const knowledgeData = JSON.parse(knowledgeDataStr);
      const index = knowledgeData.findIndex(k => k.id === parseInt(id));

      if (index !== -1) {
        // 既存データとマージ
        knowledgeData[index] = {
          ...knowledgeData[index],
          ...updatedData
        };

        localStorage.setItem('knowledge_details', JSON.stringify(knowledgeData));
      }
    }

    // 編集履歴を追加
    const historyKey = `knowledge_history_${id}`;
    const history = JSON.parse(localStorage.getItem(historyKey) || '[]');
    history.unshift({
      version: `v${history.length + 1}.0`,
      updated_at: updatedData.updated_at,
      updated_by: updatedData.updated_by,
      changes: '手動編集により更新'
    });
    localStorage.setItem(historyKey, JSON.stringify(history));

    // モーダルを閉じる
    closeEditModal();

    // ページをリロード
    showToast('ナレッジを更新しました', 'success');
    setTimeout(() => {
      window.location.reload();
    }, 1000);
  } catch (error) {
    showToast(`保存に失敗しました: ${error.message}`, 'error');
  }
}

/**
 * 新規ナレッジ作成
 */
function createNewKnowledge() {
  // フォームをクリア
  document.getElementById('editTitle').value = '';
  document.getElementById('editCategory').value = '技術資料';
  document.getElementById('editSummary').value = '';
  document.getElementById('editContent').value = '';
  document.getElementById('editTags').value = '';
  document.getElementById('editProject').value = '';

  // モーダルを表示
  const modal = document.getElementById('editModal');
  if (modal) {
    modal.classList.add('is-active');
  }

  // フォーム送信時の処理を変更
  const form = document.getElementById('editForm');
  if (form) {
    form.onsubmit = function(event) {
      event.preventDefault();

      try {
        // 新しいIDを生成
        const newId = Date.now();

        // フォームデータを取得
        const newData = {
          id: newId,
          title: document.getElementById('editTitle').value.trim(),
          category: document.getElementById('editCategory').value,
          summary: document.getElementById('editSummary').value.trim(),
          content: document.getElementById('editContent').value.trim(),
          tags: document.getElementById('editTags').value.split(',').map(t => t.trim()).filter(t => t),
          project: document.getElementById('editProject').value.trim(),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          created_by: localStorage.getItem('user_name') || '現場作業員A',
          created_by_name: localStorage.getItem('user_name') || '現場作業員A',
          status: 'draft'
        };

        // localStorageに追加
        const knowledgeDataStr = localStorage.getItem('knowledge_details');
        const knowledgeData = knowledgeDataStr ? JSON.parse(knowledgeDataStr) : [];
        knowledgeData.unshift(newData);
        localStorage.setItem('knowledge_details', JSON.stringify(knowledgeData));

        // モーダルを閉じる
        closeEditModal();

        // 新しいページに移動
        showToast('ナレッジを作成しました', 'success');
        setTimeout(() => {
          window.location.href = `search-detail.html?id=${newId}`;
        }, 1000);
      } catch (error) {
        showToast(`作成に失敗しました: ${error.message}`, 'error');
      }

      // フォーム送信時の処理を元に戻す
      form.onsubmit = saveKnowledgeEdit;
    };
  }
}

// ============================================================
// ページロード時の初期化
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;

  if (path.includes('search-detail.html')) {
    loadKnowledgeDetail();

    // ブックマーク・いいねの初期状態を設定
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('id');

    if (id) {
      const bookmarkKey = `knowledge_bookmark_${id}`;
      const likeKey = `knowledge_like_${id}`;
      const likeCountKey = `knowledge_like_count_${id}`;

      // ブックマークアイコンの初期化
      const bookmarkIcon = document.getElementById('bookmarkIcon');
      if (bookmarkIcon) {
        const isBookmarked = localStorage.getItem(bookmarkKey) === 'true';
        bookmarkIcon.textContent = isBookmarked ? '★' : '☆';
      }

      // いいねアイコンの初期化
      const likeIcon = document.getElementById('likeIcon');
      const likeCount = document.getElementById('likeCount');
      const totalLikes = document.getElementById('totalLikes');

      if (likeIcon) {
        const isLiked = localStorage.getItem(likeKey) === 'true';
        likeIcon.textContent = isLiked ? '♥' : '♡';
      }

      const count = parseInt(localStorage.getItem(likeCountKey) || '0');
      if (likeCount) likeCount.textContent = count;
      if (totalLikes) totalLikes.textContent = count;
    }
  } else if (path.includes('sop-detail.html')) {
    loadSOPDetail();
  } else if (path.includes('incident-detail.html')) {
    loadIncidentDetail();
  } else if (path.includes('expert-consult.html')) {
    loadConsultDetail();
  }

  // 最終同期時刻更新
  const syncTimeEl = document.getElementById('lastSyncTime');
  if (syncTimeEl) {
    const now = new Date();
    syncTimeEl.textContent = `最終同期 ${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`;
  }
});
