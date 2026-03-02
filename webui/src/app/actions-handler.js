/**
 * @fileoverview アクション処理モジュール v2.0.0
 * @module app/actions-handler
 * @description Phase F-4: app.js 分割版 - アクション処理
 *
 * 担当機能:
 * - ナレッジ編集 (editKnowledge)
 * - いいね処理 (toggleLike)
 * - ブックマーク処理 (toggleBookmark)
 * - 閲覧数更新 (incrementViewCount)
 * - 共有機能 (shareKnowledge / closeShareModal / copyShareUrl / printPage / exportPDF)
 * - 承認アクション (submitNewConsultationAPI)
 * - プロジェクト・専門家リアルタイム更新 (updateProjectProgress / updateExpertStats / updateDutyExperts)
 * - SocketIO ルーム操作
 * - 専門家評価算出 (calculateExpertRating)
 */

// ============================================================
// ナレッジ編集
// ============================================================

/**
 * ナレッジを編集（作成者または管理者のみ）
 * @param {number|string} knowledgeId - ナレッジ ID
 * @param {string|number} [creatorId] - 作成者 ID
 */
async function editKnowledge(knowledgeId, creatorId) {
  const log = window.logger || console;

  if (typeof canEdit === 'function' && !canEdit(creatorId)) {
    if (typeof showNotification === 'function') {
      showNotification('編集権限がありません。作成者または管理者のみ編集できます。', 'error');
    }
    return;
  }

  if (typeof showNotification === 'function') {
    showNotification('編集画面へ遷移します: ' + knowledgeId, 'info');
  }
  log.log('[KNOWLEDGE] Editing knowledge:', knowledgeId);
}

// ============================================================
// いいね・ブックマーク
// ============================================================

/**
 * いいねをトグル
 */
async function toggleLike() {
  const log = window.logger || console;
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  if (!id) {
    if (typeof showToast === 'function') showToast('IDが取得できません', 'error');
    return;
  }

  const likeKey = `knowledge_like_${id}`;
  const likeCountKey = `knowledge_like_count_${id}`;
  const currentState = localStorage.getItem(likeKey) === 'true';
  const newState = !currentState;

  try {
    localStorage.setItem(likeKey, newState.toString());

    let currentCount = parseInt(localStorage.getItem(likeCountKey) || '0');
    currentCount = newState ? currentCount + 1 : Math.max(0, currentCount - 1);
    localStorage.setItem(likeCountKey, currentCount.toString());

    const icon = document.getElementById('likeIcon');
    const countEl = document.getElementById('likeCount');
    const totalLikesEl = document.getElementById('totalLikes');

    if (icon) icon.textContent = newState ? '♥' : '♡';
    if (countEl) countEl.textContent = currentCount;
    if (totalLikesEl) totalLikesEl.textContent = currentCount;

    try {
      const result = await apiCall(`/knowledge/${id}/like`, { method: 'POST' });
      if (result && result.likes_count !== undefined) {
        localStorage.setItem(likeCountKey, result.likes_count.toString());
        if (countEl) countEl.textContent = result.likes_count;
        if (totalLikesEl) totalLikesEl.textContent = result.likes_count;
      }
    } catch (apiError) {
      log.log('[LIKE] API call failed, using localStorage only');
    }

    if (typeof showToast === 'function') {
      showToast(newState ? 'いいねしました' : 'いいねを解除しました', 'success');
    }
  } catch (error) {
    if (typeof showToast === 'function') {
      showToast(`いいねの切り替えに失敗しました: ${error.message}`, 'error');
    }
  }
}

/**
 * ブックマークをトグル
 */
async function toggleBookmark() {
  const log = window.logger || console;
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');

  if (!id) {
    if (typeof showToast === 'function') showToast('IDが取得できません', 'error');
    return;
  }

  const bookmarkKey = `knowledge_bookmark_${id}`;
  const currentState = localStorage.getItem(bookmarkKey) === 'true';
  const newState = !currentState;

  try {
    localStorage.setItem(bookmarkKey, newState.toString());

    const icon = document.getElementById('bookmarkIcon');
    if (icon) icon.textContent = newState ? '★' : '☆';

    try {
      await apiCall(`/knowledge/${id}/bookmark`, { method: 'POST' });
    } catch (apiError) {
      log.log('[BOOKMARK] API call failed, using localStorage only');
    }

    if (typeof showToast === 'function') {
      showToast(newState ? 'ブックマークに追加しました' : 'ブックマークを解除しました', 'success');
    }
  } catch (error) {
    if (typeof showToast === 'function') {
      showToast(`ブックマークの切り替えに失敗しました: ${error.message}`, 'error');
    }
  }
}

/**
 * お気に入りのトグル（後方互換性）
 * @param {number|string} [knowledgeId] - ナレッジ ID（省略時は URL から取得）
 */
async function toggleFavorite(knowledgeId) {
  if (knowledgeId) {
    // ID 指定の場合はお気に入りトグル
    const favKey = `favorite_${knowledgeId}`;
    const current = localStorage.getItem(favKey) === 'true';
    localStorage.setItem(favKey, (!current).toString());
    return !current;
  }
  return toggleBookmark();
}

// ============================================================
// 閲覧数・共有
// ============================================================

/**
 * 閲覧数をインクリメント
 * @param {number|string} id - ナレッジ ID
 */
async function incrementViewCount(id) {
  const log = window.logger || console;
  try {
    await apiCall(`/knowledge/${id}/view`, { method: 'POST' });
  } catch (error) {
    log.log('[VIEW COUNT] Skipped (using dummy data)');
  }
}

/**
 * 共有モーダルを開く
 */
function shareKnowledge() {
  const modal = document.getElementById('shareModal');
  const shareUrlEl = document.getElementById('shareUrl');
  if (modal && shareUrlEl) {
    shareUrlEl.value = window.location.href;
    modal.classList.add('is-active');
  }
}

/**
 * 共有モーダルを閉じる
 */
function closeShareModal() {
  const modal = document.getElementById('shareModal');
  if (modal) modal.classList.remove('is-active');
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
          if (typeof showToast === 'function') showToast('URLをコピーしました', 'success');
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
 * ページを印刷
 */
function printPage() {
  window.print();
}

/**
 * PDF エクスポート（印刷ダイアログ使用）
 */
function exportPDF() {
  if (typeof showToast === 'function') showToast('PDFを生成中...', 'info');
  setTimeout(() => {
    window.print();
  }, 500);
}

/**
 * ページをリロード（リトライ）
 */
function retryLoad() {
  window.location.reload();
}

// ============================================================
// 汎用アクション実行
// ============================================================

/**
 * アクションを実行（汎用）
 * @param {string} action - アクション名
 * @param {*} [payload] - ペイロード
 */
async function performAction(action, payload) {
  const log = window.logger || console;
  switch (action) {
    case 'like':
      return toggleLike();
    case 'bookmark':
      return toggleBookmark();
    case 'share':
      return shareKnowledge();
    case 'print':
      return printPage();
    case 'export':
      return exportPDF();
    default:
      log.warn('[ACTION] Unknown action:', action);
  }
}

// ============================================================
// 新規相談 API 送信
// ============================================================

/**
 * 新規相談を API 経由で投稿（フォールバックモーダル用）
 */
async function submitNewConsultationAPI() {
  const log = window.logger || console;

  const title = document.getElementById('newConsultTitle')?.value;
  const category = document.getElementById('newConsultCategory')?.value;
  const priority = document.getElementById('newConsultPriority')?.value;
  const content = document.getElementById('newConsultContent')?.value;
  const tagsInput = document.getElementById('newConsultTags')?.value;
  const tags = tagsInput ? tagsInput.split(',').map(t => t.trim()) : [];

  if (!content || content.length < 10) {
    if (typeof showNotification === 'function') {
      showNotification('相談内容は10文字以上で入力してください', 'error');
    }
    return;
  }

  const API_BASE_URL = window.API_BASE_URL || window.location.origin;

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/consultations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({ title, question: content, category, priority, tags })
    });

    const result = await response.json();

    if (result.success) {
      if (typeof showNotification === 'function') {
        showNotification('相談を投稿しました', 'success');
      }
      if (typeof closeNewConsultModalFallback === 'function') {
        closeNewConsultModalFallback();
      }
      setTimeout(() => {
        window.location.href = `expert-consult.html?id=${result.data.id}`;
      }, 1000);
    } else {
      if (typeof showNotification === 'function') {
        showNotification(result.error?.message || '相談の投稿に失敗しました', 'error');
      }
    }
  } catch (error) {
    log.error('[API] Error submitting consultation:', error);
    if (typeof showNotification === 'function') {
      showNotification('相談の投稿に失敗しました', 'error');
    }
  }
}

// ============================================================
// リアルタイム更新（SocketIO 関連）
// ============================================================

/**
 * プロジェクト進捗のリアルタイム更新
 * @param {string} projectId - プロジェクト ID
 * @param {Object} progressData - 進捗データ
 */
function updateProjectProgress(projectId, progressData) {
  const DH = window.DOMHelper;

  // サイドバーのプロジェクト一覧を更新
  const projectItems = document.querySelectorAll('.project-item');
  projectItems.forEach(item => {
    const header = item.querySelector('.project-header strong');
    if (header && header.textContent.includes(`(${projectId})`)) {
      const progressFill = item.querySelector('.mini-progress-fill');
      const progressText = item.querySelector('.progress-text');
      if (progressFill && progressText) {
        const pct = progressData.progress_percentage || 0;
        progressFill.style.width = `${pct}%`;
        progressText.textContent = `進捗 ${pct}%`;
      }
    }
  });

  // メインコンテンツの稼働モニタリングも更新
  const monProgressItems = document.querySelectorAll('.progress-item');
  monProgressItems.forEach(item => {
    const titleEl = item.querySelector('.progress-title');
    if (titleEl && titleEl.textContent.includes(projectId)) {
      const progressFill = item.querySelector('.progress-fill');
      const progressMeta = item.querySelector('.progress-meta');
      if (progressFill && progressMeta) {
        const pct = progressData.progress_percentage || 0;
        progressFill.style.width = `${pct}%`;
        if (DH) {
          DH.clearChildren(progressMeta);
          const span1 = DH.createElement('span', {}, `工程 ${pct}%`);
          const span2 = DH.createElement('span', {}, `予定 ${Math.max(0, pct - 3)}%`);
          progressMeta.appendChild(span1);
          progressMeta.appendChild(span2);
        } else {
          progressMeta.textContent = `工程 ${pct}% / 予定 ${Math.max(0, pct - 3)}%`;
        }
      }
    }
  });
}

/**
 * 専門家統計のリアルタイム更新
 * @param {Object} expertStats - 専門家統計データ
 */
function updateExpertStats(expertStats) {
  const expertItems = document.querySelectorAll('.expert-item');
  expertItems.forEach(item => {
    const header = item.querySelector('.expert-header strong');
    if (header) {
      const expertName = header.textContent;
      const expertData = expertStats.experts?.find(e => e.name === expertName);
      if (expertData) {
        const infoRow = item.querySelector('.info-row');
        if (infoRow) {
          infoRow.textContent = `回答数: ${expertData.consultation_count}件 · 評価: ⭐${expertData.average_rating}`;
        }
      }
    }
  });
}

/**
 * 当番エキスパートを更新
 * @param {Object} expertStats - 専門家統計データ
 */
function updateDutyExperts(expertStats) {
  const expertDocuments = document.querySelectorAll('aside.rail .document');
  if (expertDocuments.length > 0 && expertStats.experts) {
    const experts = expertStats.experts.slice(0, 2);
    experts.forEach((expert, index) => {
      if (expertDocuments[index]) {
        const doc = expertDocuments[index];
        const DH = window.DOMHelper;
        if (DH) DH.clearChildren(doc);
        else doc.textContent = '';

        const title = document.createElement('strong');
        title.textContent = `${expert.specialization}: ${expert.name || 'Unknown'}`;

        const small = document.createElement('small');
        small.textContent = '対応可能: 10:00-17:00 / 東北エリア';

        const div = document.createElement('div');
        div.textContent = `相談件数: ${expert.consultation_count}件 · 評価: ⭐${expert.average_rating}`;

        doc.appendChild(title);
        doc.appendChild(small);
        doc.appendChild(div);
      }
    });
  }
}

/**
 * 専門家評価を算出
 * @param {number|string} expertId - 専門家 ID
 * @returns {Promise<number|null>}
 */
async function calculateExpertRating(expertId) {
  const log = window.logger || console;
  try {
    const result = await fetchAPI(`/experts/${expertId}/rating`);
    if (result && result.success) {
      return result.data.calculated_rating;
    }
  } catch (error) {
    log.error('[EXPERT] Failed to calculate rating:', error);
  }
  return null;
}

// ============================================================
// その他
// ============================================================

/**
 * 専門家相談ページへ遷移
 */
function openApprovalBox() {
  window.location.href = '#approvals';
}

// ============================================================
// グローバル公開
// ============================================================

window.editKnowledge = editKnowledge;
window.toggleLike = toggleLike;
window.toggleBookmark = toggleBookmark;
window.toggleFavorite = toggleFavorite;
window.incrementViewCount = incrementViewCount;
window.shareKnowledge = shareKnowledge;
window.closeShareModal = closeShareModal;
window.copyShareUrl = copyShareUrl;
window.printPage = printPage;
window.exportPDF = exportPDF;
window.retryLoad = retryLoad;
window.performAction = performAction;
window.submitNewConsultationAPI = submitNewConsultationAPI;
window.updateProjectProgress = updateProjectProgress;
window.updateExpertStats = updateExpertStats;
window.updateDutyExperts = updateDutyExperts;
window.calculateExpertRating = calculateExpertRating;

export {
  editKnowledge,
  toggleLike,
  toggleBookmark,
  toggleFavorite,
  incrementViewCount,
  shareKnowledge,
  closeShareModal,
  copyShareUrl,
  printPage,
  exportPDF,
  retryLoad,
  performAction,
  submitNewConsultationAPI,
  updateProjectProgress,
  updateExpertStats,
  updateDutyExperts,
  calculateExpertRating
};
