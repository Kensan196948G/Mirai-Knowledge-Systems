/**
 * @fileoverview 専門家相談詳細ページモジュール v2.0.0
 * @module pages/consultation-detail
 * @description Phase F-4: detail-pages.js 分割版 - expert-consult.html専用
 *
 * 担当機能:
 * - 専門家相談詳細読み込み (loadConsultDetail)
 * - 専門家相談詳細表示 (displayConsultDetail)
 * - エキスパート情報表示 (displayExpertInfoConsult)
 * - ベストアンサー表示 (displayBestAnswerConsult)
 * - 参考SOP表示 (displayReferenceSOPConsult)
 * - 添付ファイル表示 (displayConsultAttachments)
 * - ステータス履歴表示 (displayConsultStatusHistory)
 * - 回答時間計算 (calculateResponseTime)
 * - 回答管理 (loadAnswersFromData / loadAnswers)
 * - 関連質問 (loadRelatedQuestions)
 * - 経過時間計算 (calculateElapsedTime)
 * - リトライ (retryLoadConsult)
 * - 新規相談モーダル (openNewConsultationModal / createNewConsultationModal /
 *   closeNewConsultationModal / submitNewConsultation)
 *
 * 依存: page-renderer.js (showLoading, hideLoading, showError, hideError,
 *       formatDate, formatDateShort, updateElement, displayApprovalFlow, updateBreadcrumb, apiCall,
 *       calculateElapsedTime, calculateResponseTime)
 * 依存: dom-helpers.js (setSecureChildren, createSecureElement, createMetaInfoElement,
 *       createTagElement, createTableRow, createAnswerElement, createBestAnswerElement,
 *       createExpertInfoElement, createAttachmentElement, createStatusHistoryElement,
 *       createDocumentElement, createEmptyMessage, createErrorMessage)
 */

// ============================================================
// 専門家相談詳細読み込み
// ============================================================

/**
 * 専門家相談詳細データを読み込む（URL の ?id= から ID を取得）
 */
async function loadConsultDetail() {
  const log = window.logger || console;
  log.log('[CONSULT DETAIL] Starting to load...');
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');
  const inProduction = typeof isProductionMode === 'function' ? isProductionMode() : false;

  log.log('[CONSULT DETAIL] ID from URL:', id, 'Production mode:', inProduction);

  if (!id) {
    if (typeof showError === 'function') showError('相談IDが指定されていません。一覧ページに戻ります...');
    setTimeout(() => {
      window.location.href = 'index.html';
    }, 2000);
    return;
  }

  if (typeof showLoading === 'function') showLoading();
  if (typeof hideError === 'function') hideError();

  try {
    let data = null;

    log.log('[DETAIL] Loading consultation from API (data consistency fix)...');
    try {
      const response = await apiCall(`/consultations/${id}`);
      log.log('[DETAIL] API Response:', response);

      data = response?.data || response;

      log.log('[DETAIL] Extracted data:', data);
      log.log('[DETAIL] Successfully loaded from API');
    } catch (apiError) {
      log.error('[DETAIL] API call failed:', apiError);

      const consultDataStr = localStorage.getItem('consultations_details');
      if (consultDataStr) {
        log.log('[DETAIL] Fallback to localStorage...');
        const consultData = JSON.parse(consultDataStr);
        data = consultData.find(c => c.id === parseInt(id));
        if (data) {
          log.warn('[DETAIL] Using localStorage data (may be outdated)');
        }
      }
    }

    if (!data) {
      if (typeof showError === 'function') showError(`相談ID ${id} が見つかりません`);
      return;
    }

    log.log('[CONSULT DETAIL] Displaying data...');
    displayConsultDetail(data);
    loadAnswersFromData(data);
    await loadRelatedQuestions(data.tags || [], id);
  } catch (error) {
    log.error('[CONSULT DETAIL] Error:', error);
    if (typeof showError === 'function') showError(`データの読み込みに失敗しました: ${error.message}`);
  } finally {
    if (typeof hideLoading === 'function') hideLoading();
  }
}

// ============================================================
// 専門家相談詳細表示
// ============================================================

/**
 * 専門家相談データを画面に表示する
 * @param {Object} data - 専門家相談データオブジェクト
 */
function displayConsultDetail(data) {
  if (typeof updateElement === 'function') {
    updateElement('consultTitle', data.title || '相談タイトル');

    const statusText = data.status === 'answered' ? '回答済み' : data.status === 'pending' ? '受付中' : data.status;
    updateElement('consultStatus', `ステータス ${statusText}`);

    const responseTime = data.answers && data.answers.length > 0
      ? calculateResponseTimeLocal(data.created_at, data.answers[0].created_at)
      : '--';
    updateElement('responseTime', `回答時間 ${responseTime}時間`);
  }

  // メタ情報
  const metaEl = document.getElementById('consultMeta');
  if (metaEl && typeof createMetaInfoElement === 'function' && typeof setSecureChildren === 'function') {
    setSecureChildren(metaEl, createMetaInfoElement({
      created_at: data.created_at,
      requester: data.requester || data.author_name || 'N/A',
      category: data.category || 'N/A',
      project: data.project || 'N/A'
    }, 'consult'));
  }

  // タグ
  const tagsEl = document.getElementById('consultTags');
  if (tagsEl && data.tags && typeof createTagElement === 'function' && typeof setSecureChildren === 'function') {
    setSecureChildren(tagsEl, data.tags.map(tag => createTagElement(tag)));
  }

  if (typeof updateElement === 'function') {
    updateElement('questionContent', data.question || data.content || '質問内容がありません');
  }

  // 相談情報テーブル
  const consultInfoEl = document.getElementById('consultInfo');
  if (consultInfoEl && typeof createTableRow === 'function' && typeof setSecureChildren === 'function') {
    const statusText = data.status === 'answered' ? '回答済み' : data.status === 'pending' ? '受付中' : data.status;
    const rows = [
      { label: '投稿日', value: formatDate(data.created_at) },
      { label: '投稿者', value: data.requester || data.author_name || 'N/A' },
      { label: 'カテゴリ', value: data.category || 'N/A' },
      { label: 'プロジェクト', value: data.project || 'N/A' },
      { label: 'ステータス', value: statusText }
    ];
    setSecureChildren(consultInfoEl, rows.map(row => createTableRow([row.label, row.value])));
  }

  if (typeof updateElement === 'function') {
    updateElement('priority', data.priority || '通常');
    updateElement('deadline', formatDateShort(data.deadline) || 'N/A');
    updateElement('elapsedTime', calculateElapsedTimeLocal(data.created_at));

    const answerCount = data.answers ? data.answers.length : data.answer_count || 0;
    updateElement('totalAnswers', answerCount);
    updateElement('answerCount', answerCount);
    updateElement('viewCount', data.views || data.view_count || 0);
    updateElement('followerCount', data.follower_count || 0);
    updateElement('responseRate', data.response_rate || 85);
    updateElement('avgResponseTime', data.avg_response_time || 4);
  }

  displayExpertInfoConsult(data);
  displayBestAnswerConsult(data);
  displayReferenceSOPConsult(data);
  displayConsultAttachments(data);
  displayConsultStatusHistory(data);

  if (typeof updateBreadcrumb === 'function') updateBreadcrumb('専門家相談', data.title);
}

// ============================================================
// エキスパート情報表示
// ============================================================

/**
 * エキスパート情報を表示する
 * @param {Object} data - 相談データ
 */
async function displayExpertInfoConsult(data) {
  const log = window.logger || console;
  const expertInfoEl = document.getElementById('expertInfo');
  if (!expertInfoEl) return;

  let expert = data.expert_info;

  if (!expert && data.expert_id) {
    try {
      const response = await apiCall(`/experts/${data.expert_id}`);
      expert = response?.data || response;
    } catch (error) {
      log.warn('[EXPERT] Failed to load expert data:', error);
    }
  }

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

  if (typeof createExpertInfoElement === 'function' && typeof setSecureChildren === 'function') {
    setSecureChildren(expertInfoEl, createExpertInfoElement(expert));
  }
}

// ============================================================
// ベストアンサー表示
// ============================================================

/**
 * ベストアンサーを表示する
 * @param {Object} data - 相談データ
 */
function displayBestAnswerConsult(data) {
  const bestAnswerEl = document.getElementById('bestAnswer');
  if (!bestAnswerEl) return;

  const bestAnswer = data.answers?.find(a => a.is_best_answer);

  if (typeof setSecureChildren === 'function') {
    if (bestAnswer && typeof createBestAnswerElement === 'function') {
      setSecureChildren(bestAnswerEl, createBestAnswerElement(bestAnswer));
    } else if (typeof createEmptyMessage === 'function') {
      setSecureChildren(bestAnswerEl, createEmptyMessage('まだベストアンサーが選択されていません'));
    }
  }
}

// ============================================================
// 参考SOP表示
// ============================================================

/**
 * 参考SOPを表示する
 * @param {Object} data - 相談データ
 */
function displayReferenceSOPConsult(data) {
  const referenceSOPEl = document.getElementById('referenceSOP');
  if (!referenceSOPEl) return;

  const referenceDocs = data.reference_sops || [
    { id: 1, title: 'コンクリート打設管理SOP', category: '品質管理' },
    { id: 2, title: '養生作業手順書', category: '施工手順' }
  ];

  if (typeof setSecureChildren === 'function' && typeof createDocumentElement === 'function') {
    if (referenceDocs.length > 0) {
      setSecureChildren(referenceSOPEl, referenceDocs.map(doc =>
        createDocumentElement(doc, 'sop-detail.html')
      ));
    } else if (typeof createEmptyMessage === 'function') {
      setSecureChildren(referenceSOPEl, createEmptyMessage('参考SOPがありません'));
    }
  }
}

// ============================================================
// 添付ファイル表示
// ============================================================

/**
 * 添付ファイルを表示する
 * @param {Object} data - 相談データ
 */
function displayConsultAttachments(data) {
  const attachmentListEl = document.getElementById('attachmentList');
  if (!attachmentListEl) return;

  const attachments = data.attachments || [];

  if (typeof setSecureChildren === 'function') {
    if (attachments.length > 0 && typeof createAttachmentElement === 'function') {
      setSecureChildren(attachmentListEl, attachments.map(file =>
        createAttachmentElement(file)
      ));
    } else if (typeof createEmptyMessage === 'function') {
      setSecureChildren(attachmentListEl, createEmptyMessage('添付ファイルがありません'));
    }
  }
}

// ============================================================
// ステータス履歴表示
// ============================================================

/**
 * ステータス履歴を表示する
 * @param {Object} data - 相談データ
 */
function displayConsultStatusHistory(data) {
  const statusHistoryEl = document.getElementById('statusHistory');
  if (!statusHistoryEl) return;

  const history = data.status_history || [
    { status: '受付', timestamp: data.created_at, user: data.requester || 'ユーザー' },
    { status: '専門家割当', timestamp: data.created_at, user: 'システム' }
  ];

  if (typeof setSecureChildren === 'function') {
    if (history.length > 0 && typeof createStatusHistoryElement === 'function') {
      setSecureChildren(statusHistoryEl, history.map(item =>
        createStatusHistoryElement(item)
      ));
    } else if (typeof createEmptyMessage === 'function') {
      setSecureChildren(statusHistoryEl, createEmptyMessage('履歴がありません'));
    }
  }
}

// ============================================================
// 計算関数（ローカル版）
// ============================================================

/**
 * 回答時間を計算する（時間単位）
 * @param {string} createdAt - 投稿日時
 * @param {string} firstAnswerAt - 最初の回答日時
 * @returns {number|string}
 */
function calculateResponseTimeLocal(createdAt, firstAnswerAt) {
  if (typeof calculateResponseTime === 'function') {
    return calculateResponseTime(createdAt, firstAnswerAt);
  }
  if (!createdAt || !firstAnswerAt) return '--';
  const created = new Date(createdAt);
  const answered = new Date(firstAnswerAt);
  const diffMs = answered - created;
  return Math.floor(diffMs / (1000 * 60 * 60));
}

/**
 * 経過時間を計算して日本語文字列で返す
 * @param {string} createdAt - 作成日時
 * @returns {string}
 */
function calculateElapsedTimeLocal(createdAt) {
  if (typeof calculateElapsedTime === 'function') {
    return calculateElapsedTime(createdAt);
  }
  if (!createdAt) return 'N/A';
  const now = new Date();
  const created = new Date(createdAt);
  const diff = now - created;
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const days = Math.floor(hours / 24);
  if (days > 0) return `${days}日`;
  return `${hours}時間`;
}

// ============================================================
// 回答管理
// ============================================================

/**
 * 回答を localStorage データから読み込む
 * @param {Object} data - 相談データ
 */
function loadAnswersFromData(data) {
  const answerListEl = document.getElementById('answerList');
  const answerCountEl = document.getElementById('answerCount');
  if (!answerListEl) return;

  const answers = data.answers || [];
  if (answerCountEl) answerCountEl.textContent = answers.length;

  if (typeof setSecureChildren === 'function' && typeof createAnswerElement === 'function') {
    if (answers.length > 0) {
      setSecureChildren(answerListEl, answers.map(answer =>
        createAnswerElement(answer, answer.is_best_answer || answer.is_best)
      ));
    } else if (typeof createEmptyMessage === 'function') {
      setSecureChildren(answerListEl, createEmptyMessage('まだ回答がありません'));
    }
  }
}

/**
 * 回答を API から読み込む
 * @param {string|number} consultId - 相談 ID
 */
async function loadAnswers(consultId) {
  const log = window.logger || console;
  const answerListEl = document.getElementById('answerList');
  const answerCountEl = document.getElementById('answerCount');
  if (!answerListEl) return;

  try {
    const answers = await apiCall(`/consultation/${consultId}/answers`);
    if (answerCountEl) answerCountEl.textContent = answers ? answers.length : 0;

    if (typeof setSecureChildren === 'function' && typeof createAnswerElement === 'function') {
      if (answers && answers.length > 0) {
        setSecureChildren(answerListEl, answers.map(answer =>
          createAnswerElement(answer, answer.is_best)
        ));
      } else if (typeof createEmptyMessage === 'function') {
        setSecureChildren(answerListEl, createEmptyMessage('まだ回答がありません'));
      }
    }
  } catch (error) {
    log.error('Failed to load answers:', error);
    if (typeof setSecureChildren === 'function' && typeof createErrorMessage === 'function') {
      setSecureChildren(answerListEl, createErrorMessage('回答の読み込みに失敗しました'));
    }
  }
}

// ============================================================
// 関連質問
// ============================================================

/**
 * 関連質問を読み込む
 * @param {Array} tags - タグ配列
 * @param {string|number} currentId - 現在の相談 ID
 */
async function loadRelatedQuestions(tags, currentId) {
  const log = window.logger || console;
  const relatedEl = document.getElementById('relatedQuestions');
  if (!relatedEl) return;

  try {
    const consultData = JSON.parse(localStorage.getItem('consultations_details') || '[]');

    let relatedItems = [];

    if (tags && tags.length > 0) {
      relatedItems = consultData
        .filter(c => c.id !== parseInt(currentId))
        .filter(c => c.tags && c.tags.some(tag => tags.includes(tag)))
        .slice(0, 5);
    } else {
      const current = consultData.find(c => c.id === parseInt(currentId));
      if (current) {
        relatedItems = consultData
          .filter(c => c.id !== parseInt(currentId))
          .filter(c => c.category === current.category)
          .slice(0, 5);
      }
    }

    if (typeof setSecureChildren === 'function' && typeof createDocumentElement === 'function') {
      if (relatedItems.length > 0) {
        setSecureChildren(relatedEl, relatedItems.map(item =>
          createDocumentElement(item, 'expert-consult.html')
        ));
      } else if (typeof createEmptyMessage === 'function') {
        setSecureChildren(relatedEl, createEmptyMessage('関連質問が見つかりませんでした'));
      }
    }
  } catch (error) {
    log.error('Failed to load related questions:', error);
    if (typeof setSecureChildren === 'function' && typeof createErrorMessage === 'function') {
      setSecureChildren(relatedEl, createErrorMessage('関連質問の読み込みに失敗しました'));
    }
  }
}

/**
 * 専門家相談ページをリロード（リトライ）
 */
function retryLoadConsult() {
  window.location.reload();
}

// ============================================================
// 新規専門家相談作成モーダル
// ============================================================

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
 * 新規専門家相談モーダルを動的に作成する
 */
function createNewConsultationModal() {
  if (typeof createSecureElement !== 'function' || typeof setSecureChildren !== 'function') return;

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
    const form = document.getElementById('newConsultationForm');
    if (form) form.reset();
  }
}

/**
 * 新規専門家相談を送信する
 * @param {Event} [event] - フォーム送信イベント
 */
async function submitNewConsultation(event) {
  if (event) {
    event.preventDefault();
  }

  const titleEl = document.getElementById('consultNewTitle');
  const categoryEl = document.getElementById('consultNewCategory');
  const priorityEl = document.getElementById('consultNewPriority');
  const contentEl = document.getElementById('consultNewContent');

  if (!titleEl || !categoryEl || !priorityEl || !contentEl) {
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

  const log = window.logger || console;

  try {
    if (typeof showNotification === 'function') showNotification('専門家相談を投稿中...', 'info');

    await apiCall('/consultations', {
      method: 'POST',
      body: JSON.stringify(data)
    });

    if (typeof showNotification === 'function') showNotification('専門家相談を投稿しました', 'success');
    closeNewConsultationModal();

    setTimeout(() => {
      window.location.reload();
    }, 1000);
  } catch (error) {
    log.error('Failed to create consultation:', error);
    if (typeof showNotification === 'function') {
      showNotification(`相談の投稿に失敗しました: ${error.message}`, 'error');
    }
  }
}

// ============================================================
// ページ初期化（expert-consult.html 専用）
// ============================================================

/**
 * expert-consult.html のページ初期化処理
 */
export async function initPage() {
  loadConsultDetail();
}

// ============================================================
// グローバル公開（後方互換性）
// ============================================================

if (typeof window.MKSApp === 'undefined') window.MKSApp = {};
if (typeof window.MKSApp.DetailPages === 'undefined') window.MKSApp.DetailPages = {};
window.MKSApp.DetailPages.Consult = {
  load: loadConsultDetail,
  display: displayConsultDetail,
  loadAnswers: loadAnswersFromData,
  loadRelated: loadRelatedQuestions,
  retry: retryLoadConsult
};

window.loadConsultDetail = loadConsultDetail;
window.displayConsultDetail = displayConsultDetail;
window.displayExpertInfoConsult = displayExpertInfoConsult;
window.displayBestAnswerConsult = displayBestAnswerConsult;
window.displayReferenceSOPConsult = displayReferenceSOPConsult;
window.displayConsultAttachments = displayConsultAttachments;
window.displayConsultStatusHistory = displayConsultStatusHistory;
window.loadAnswersFromData = loadAnswersFromData;
window.loadAnswers = loadAnswers;
window.loadRelatedQuestions = loadRelatedQuestions;
window.retryLoadConsult = retryLoadConsult;
window.openNewConsultationModal = openNewConsultationModal;
window.createNewConsultationModal = createNewConsultationModal;
window.closeNewConsultationModal = closeNewConsultationModal;
window.submitNewConsultation = submitNewConsultation;

export {
  loadConsultDetail,
  displayConsultDetail,
  displayExpertInfoConsult,
  displayBestAnswerConsult,
  displayReferenceSOPConsult,
  displayConsultAttachments,
  displayConsultStatusHistory,
  calculateResponseTimeLocal,
  calculateElapsedTimeLocal,
  loadAnswersFromData,
  loadAnswers,
  loadRelatedQuestions,
  retryLoadConsult,
  openNewConsultationModal,
  createNewConsultationModal,
  closeNewConsultationModal,
  submitNewConsultation
};
