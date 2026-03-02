/**
 * @fileoverview SOP詳細ページモジュール v2.0.0
 * @module pages/sop-detail
 * @description Phase F-4: detail-pages.js 分割版 - SOP詳細ページ
 *
 * 担当機能:
 * - SOP詳細読み込み (loadSOPDetail)
 * - SOP詳細表示 (displaySOPDetail)
 * - 関連SOP読み込み (loadRelatedSOP)
 * - 実施記録 (startInspectionRecord / cancelRecord / submitInspectionRecord)
 * - 実施統計更新 (updateExecutionStats)
 * - ダウンロード・印刷 (downloadSOP / printChecklist)
 * - SOP編集 (editSOP / closeEditSOPModal / submitEditSOP)
 * - 共有 (shareSOP)
 *
 * 依存: page-renderer.js (showLoading, hideLoading, showError, hideError,
 *       formatDate, formatDateShort, updateElement, displayApprovalFlow, updateBreadcrumb, apiCall)
 * 依存: dom-helpers.js (setSecureChildren, createSecureElement, createMetaInfoElement,
 *       createTagElement, createTableRow, createTableRowWithHTML, createDocumentElement,
 *       createStepElement, createChecklistElement, createWarningElement, createPillElement,
 *       createEmptyMessage, createErrorMessage)
 */

// ============================================================
// SOP詳細読み込み
// ============================================================

/**
 * SOP詳細データを読み込む（URL の ?id= から ID を取得）
 */
async function loadSOPDetail() {
  const log = window.logger || console;
  log.log('[SOP DETAIL] Starting to load...');
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id');
  const inProduction = typeof isProductionMode === 'function' ? isProductionMode() : false;

  log.log('[SOP DETAIL] ID from URL:', id, 'Production mode:', inProduction);

  if (!id) {
    if (typeof showError === 'function') showError('SOP IDが指定されていません。一覧ページに戻ります...');
    setTimeout(() => {
      window.location.href = 'index.html';
    }, 2000);
    return;
  }

  if (typeof showLoading === 'function') showLoading();
  if (typeof hideError === 'function') hideError();

  try {
    let data = null;

    log.log('[DETAIL] Loading SOP from API (data consistency fix)...');
    try {
      const response = await apiCall(`/sop/${id}`);
      log.log('[DETAIL] API Response:', response);

      data = response?.data || response;

      log.log('[DETAIL] Extracted data:', data);
      log.log('[DETAIL] Successfully loaded from API');
    } catch (apiError) {
      log.error('[DETAIL] API call failed:', apiError);

      const sopDataStr = localStorage.getItem('sop_details');
      if (sopDataStr) {
        log.log('[DETAIL] Fallback to localStorage...');
        const sopData = JSON.parse(sopDataStr);
        data = sopData.find(s => s.id === parseInt(id));
        if (data) {
          log.warn('[DETAIL] Using localStorage data (may be outdated)');
        }
      } else {
        log.log('[DETAIL] Loading SOP from localStorage...');
      }
    }

    if (!data) {
      if (typeof showError === 'function') showError(`SOP ID ${id} が見つかりません`);
      return;
    }

    log.log('[SOP DETAIL] Displaying data...');
    displaySOPDetail(data);
    await loadRelatedSOP(data.category, id);

    if (typeof updateExecutionStats === 'function') {
      updateExecutionStats();
    }
  } catch (error) {
    log.error('[SOP DETAIL] Error:', error);
    if (typeof showError === 'function') showError(`データの読み込みに失敗しました: ${error.message}`);
  } finally {
    if (typeof hideLoading === 'function') hideLoading();
  }
}

// ============================================================
// SOP詳細表示
// ============================================================

/**
 * SOPデータを画面に表示する
 * @param {Object} data - SOPデータオブジェクト
 */
function displaySOPDetail(data) {
  if (typeof updateElement === 'function') {
    updateElement('sopTitle', data.title || 'SOPタイトル');

    const sopNumber = data.sop_number || data.title.match(/SOP-(\d+)/)?.[1] || 'N/A';
    updateElement('sopNumber', `SOP番号 ${sopNumber}`);
    updateElement('sopVersion', `バージョン ${data.version || 'v1.0'}`);
  }

  // メタ情報
  const metaEl = document.getElementById('sopMeta');
  if (metaEl && typeof createMetaInfoElement === 'function' && typeof setSecureChildren === 'function') {
    setSecureChildren(metaEl, createMetaInfoElement({
      revision_date: data.revision_date || data.updated_at,
      category: data.category || 'N/A',
      target: data.target || data.scope || 'N/A'
    }, 'sop'));
  }

  // タグ
  const tagsEl = document.getElementById('sopTags');
  if (tagsEl && data.tags && typeof createTagElement === 'function' && typeof setSecureChildren === 'function') {
    setSecureChildren(tagsEl, data.tags.map(tag => createTagElement(tag)));
  }

  if (typeof updateElement === 'function') {
    updateElement('sopPurpose', data.purpose || '目的が記載されていません');
    updateElement('sopScope', data.scope || '適用範囲が記載されていません');
  }

  // バージョン情報
  const versionInfoEl = document.getElementById('versionInfo');
  if (versionInfoEl && typeof createTableRow === 'function' && typeof setSecureChildren === 'function') {
    const rows = [
      { label: 'バージョン', value: data.version || 'v1.0' },
      { label: '改訂日', value: formatDateShort(data.revision_date || data.updated_at) },
      { label: '次回改訂予定', value: formatDateShort(data.next_revision_date) || 'N/A' }
    ];
    setSecureChildren(versionInfoEl, rows.map(row => createTableRow([row.label, row.value])));
  }

  // 手順
  const procedureEl = document.getElementById('sopProcedure');
  if (procedureEl && typeof setSecureChildren === 'function') {
    const steps = data.steps || data.procedure || [];
    if (Array.isArray(steps) && steps.length > 0 && typeof createStepElement === 'function') {
      setSecureChildren(procedureEl, steps.map((step, i) => createStepElement(step, i)));
    } else if (typeof steps === 'string' && typeof createSecureElement === 'function') {
      setSecureChildren(procedureEl, createSecureElement('div', {}, [steps]));
    } else if (typeof createEmptyMessage === 'function') {
      setSecureChildren(procedureEl, createEmptyMessage('手順データがありません'));
    }
  }

  // チェックリスト
  const checklistEl = document.getElementById('sopChecklist');
  if (checklistEl && data.checklist && typeof setSecureChildren === 'function') {
    if (Array.isArray(data.checklist) && typeof createChecklistElement === 'function') {
      setSecureChildren(checklistEl, data.checklist.map(item => createChecklistElement(item)));
    } else if (typeof createSecureElement === 'function') {
      setSecureChildren(checklistEl, createSecureElement('div', {}, [data.checklist]));
    }
  }

  // 注意事項
  const warningsEl = document.getElementById('sopWarnings');
  if (warningsEl && typeof setSecureChildren === 'function') {
    const warnings = data.precautions || data.warnings || [];
    if (Array.isArray(warnings) && warnings.length > 0 && typeof createWarningElement === 'function') {
      setSecureChildren(warningsEl, warnings.map(warning => createWarningElement(warning)));
    } else if (typeof warnings === 'string' && typeof createWarningElement === 'function') {
      setSecureChildren(warningsEl, createWarningElement(warnings));
    } else if (typeof createEmptyMessage === 'function') {
      setSecureChildren(warningsEl, createEmptyMessage('注意事項がありません'));
    }
  }

  // 改訂履歴
  const revisionHistoryEl = document.getElementById('revisionHistory');
  if (revisionHistoryEl && data.revision_history && typeof setSecureChildren === 'function') {
    if (Array.isArray(data.revision_history) && typeof createTableRowWithHTML === 'function') {
      setSecureChildren(revisionHistoryEl, data.revision_history.map(rev => {
        const btn = document.createElement('button');
        btn.className = 'cta ghost';
        btn.textContent = '表示';
        btn.addEventListener('click', () => alert('バージョン表示機能は準備中です'));
        return createTableRowWithHTML([
          rev.version || 'N/A',
          rev.date || formatDateShort(rev.updated_at),
          rev.changes || 'N/A',
          rev.author || 'N/A',
          btn
        ]);
      }));
    }
  }

  // 必要資材・工具
  const equipmentEl = document.getElementById('sopEquipment');
  if (equipmentEl && data.equipment && typeof setSecureChildren === 'function') {
    if (Array.isArray(data.equipment) && typeof createPillElement === 'function') {
      setSecureChildren(equipmentEl, data.equipment.map(item => createPillElement(item)));
    } else if (typeof createPillElement === 'function') {
      setSecureChildren(equipmentEl, createPillElement(data.equipment));
    }
  }

  if (typeof updateElement === 'function') {
    updateElement('prepTime', data.prep_time || '--');
    updateElement('workTime', data.work_time || '--');
    updateElement('totalTime', data.duration || '--');
    updateElement('executionCount', data.execution_count || 0);
    updateElement('complianceRate', data.compliance_rate || 0);
  }

  if (typeof displayApprovalFlow === 'function') displayApprovalFlow(data.approval_status);
  if (typeof updateBreadcrumb === 'function') updateBreadcrumb('SOP', data.title);
}

// ============================================================
// 関連SOP
// ============================================================

/**
 * 関連SOPを読み込む
 * @param {string} category - SOPカテゴリ
 * @param {string|number} currentId - 現在のSOP ID
 */
async function loadRelatedSOP(category, currentId) {
  const log = window.logger || console;
  const relatedListEl = document.getElementById('relatedSOPList');
  if (!relatedListEl) return;

  if (typeof loadRelatedSOPFromAPI === 'function') {
    try {
      await loadRelatedSOPFromAPI(currentId, 'hybrid', 5);
      return;
    } catch (error) {
      log.warn('API recommendation failed, falling back to localStorage:', error);
    }
  }

  try {
    const sopData = JSON.parse(localStorage.getItem('sop_details') || '[]');
    const currentSOP = sopData.find(s => s.id === parseInt(currentId));

    let relatedItems = [];

    if (currentSOP && currentSOP.related_sops) {
      relatedItems = currentSOP.related_sops
        .map(relatedId => sopData.find(s => s.id === relatedId))
        .filter(item => item)
        .slice(0, 5);
    } else if (category) {
      relatedItems = sopData
        .filter(s => s.id !== parseInt(currentId))
        .filter(s => s.category === category)
        .slice(0, 5);
    }

    if (typeof setSecureChildren === 'function' && typeof createDocumentElement === 'function') {
      if (relatedItems.length > 0) {
        setSecureChildren(relatedListEl, relatedItems.map(item =>
          createDocumentElement(item, 'sop-detail.html')
        ));
      } else if (typeof createEmptyMessage === 'function') {
        setSecureChildren(relatedListEl, createEmptyMessage('関連SOPが見つかりませんでした'));
      }
    }
  } catch (error) {
    log.error('Failed to load related SOP:', error);
    if (typeof setSecureChildren === 'function' && typeof createErrorMessage === 'function') {
      setSecureChildren(relatedListEl, createErrorMessage('関連SOPの読み込みに失敗しました'));
    }
  }
}

// ============================================================
// 実施記録
// ============================================================

/**
 * 実施記録フォームを表示する
 */
function startInspectionRecord() {
  const formEl = document.getElementById('record-form');
  if (!formEl) return;

  formEl.style.display = 'block';

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

  const recordChecklistEl = document.getElementById('recordChecklist');
  const sopChecklistEl = document.getElementById('sopChecklist');
  if (recordChecklistEl && sopChecklistEl && typeof createSecureElement === 'function') {
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
    if (typeof setSecureChildren === 'function') {
      setSecureChildren(container, items);
      setSecureChildren(recordChecklistEl, container);
    }
  }

  formEl.scrollIntoView({ behavior: 'smooth' });

  const formElement = document.getElementById('inspectionForm');
  if (formElement && !formElement.hasAttribute('data-listener-attached')) {
    formElement.addEventListener('submit', submitInspectionRecord);
    formElement.setAttribute('data-listener-attached', 'true');
  }
}

/**
 * 実施記録フォームをキャンセルする
 */
function cancelRecord() {
  const formEl = document.getElementById('record-form');
  if (formEl) {
    formEl.style.display = 'none';

    const formElement = document.getElementById('inspectionForm');
    if (formElement) formElement.reset();
  }
}

/**
 * 実施記録を送信・保存する
 * @param {Event} event - フォーム送信イベント
 */
function submitInspectionRecord(event) {
  event.preventDefault();

  const recordDate = document.getElementById('recordDate').value;
  const recordWorker = document.getElementById('recordWorker').value;
  const recordProject = document.getElementById('recordProject').value;
  const recordContent = document.getElementById('recordContent').value;
  const recordNotes = document.getElementById('recordNotes').value;

  const checkItems = [];
  const checkboxes = document.querySelectorAll('#recordChecklist input[type="checkbox"]');
  checkboxes.forEach((checkbox, index) => {
    const label = checkbox.nextSibling ? checkbox.nextSibling.textContent.trim() : `項目 ${index + 1}`;
    checkItems.push({
      item: label,
      checked: checkbox.checked
    });
  });

  const urlParams = new URLSearchParams(window.location.search);
  const sopId = urlParams.get('id');

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

  const recordsKey = 'sop_inspection_records';
  const existingRecords = JSON.parse(localStorage.getItem(recordsKey) || '[]');
  existingRecords.push(recordData);
  localStorage.setItem(recordsKey, JSON.stringify(existingRecords));

  if (typeof showToast === 'function') {
    showToast('実施記録を保存しました', 'success');
  } else if (typeof showNotification === 'function') {
    showNotification('実施記録を保存しました', 'success');
  }

  cancelRecord();
  updateExecutionStats();
}

/**
 * 実施統計を再計算・更新する
 */
function updateExecutionStats() {
  const urlParams = new URLSearchParams(window.location.search);
  const sopId = urlParams.get('id');
  const recordsKey = 'sop_inspection_records';
  const allRecords = JSON.parse(localStorage.getItem(recordsKey) || '[]');
  const sopRecords = allRecords.filter(r => r.sop_id === sopId);

  const executionCountEl = document.getElementById('executionCount');
  if (executionCountEl) executionCountEl.textContent = sopRecords.length;

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

// ============================================================
// ダウンロード・印刷
// ============================================================

/**
 * SOPをダウンロード（印刷ダイアログ使用）
 */
function downloadSOP() {
  if (typeof downloadPDF === 'function') {
    downloadPDF('sop', document.getElementById('sopTitle')?.textContent || 'SOP');
  } else {
    window.print();
  }

  if (typeof showToast === 'function') {
    showToast('印刷ダイアログを開きました。PDFとして保存できます。', 'info');
  }
}

/**
 * チェックリストを印刷する
 */
function printChecklist() {
  const checklistEl = document.getElementById('sopChecklist');
  const titleEl = document.getElementById('sopTitle');

  if (!checklistEl) return;

  const printWindow = window.open('', '', 'height=600,width=800');
  const title = titleEl ? titleEl.textContent : 'チェックリスト';

  const doc = printWindow.document;

  const html = doc.createElement('html');
  const head = doc.createElement('head');
  const titleTag = doc.createElement('title');
  titleTag.textContent = `${title} - チェックリスト`;

  const style = doc.createElement('style');
  style.textContent = `
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
  `;

  head.appendChild(titleTag);
  head.appendChild(style);

  const body = doc.createElement('body');
  const h1 = doc.createElement('h1');
  h1.textContent = `${title} - チェックリスト`;

  const checklistClone = checklistEl.cloneNode(true);

  body.appendChild(h1);
  body.appendChild(checklistClone);

  html.appendChild(head);
  html.appendChild(body);

  doc.appendChild(html);
  doc.close();

  printWindow.onload = function() {
    printWindow.print();
  };
}

// ============================================================
// SOP編集
// ============================================================

/**
 * SOP編集モーダルを開く
 */
function editSOP() {
  const modal = document.getElementById('editSOPModal');
  if (!modal) return;

  const title = document.getElementById('sopTitle')?.textContent || '';
  const purpose = document.getElementById('sopPurpose')?.textContent || '';
  const scope = document.getElementById('sopScope')?.textContent || '';

  document.getElementById('editSOPTitle').value = title;
  document.getElementById('editSOPPurpose').value = purpose;
  document.getElementById('editSOPScope').value = scope;
  document.getElementById('editSOPChanges').value = '';
  document.getElementById('editSOPReason').value = '';

  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

/**
 * SOP編集モーダルを閉じる
 */
function closeEditSOPModal() {
  const modal = document.getElementById('editSOPModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

/**
 * SOP改訂提案を送信する
 * @param {Event} event - フォーム送信イベント
 */
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

  const proposalsKey = 'sop_revision_proposals';
  const existingProposals = JSON.parse(localStorage.getItem(proposalsKey) || '[]');
  existingProposals.push(proposalData);
  localStorage.setItem(proposalsKey, JSON.stringify(existingProposals));

  if (typeof showToast === 'function') {
    showToast('改訂提案を送信しました', 'success');
  } else if (typeof showNotification === 'function') {
    showNotification('改訂提案を送信しました', 'success');
  }

  closeEditSOPModal();
}

// ============================================================
// 共有
// ============================================================

/**
 * SOP共有モーダルを開く
 */
function shareSOP() {
  if (typeof openShareModal === 'function') {
    openShareModal();
  }
}

/**
 * ページをリロード（リトライ）
 */
function retryLoadSOP() {
  window.location.reload();
}

// ============================================================
// グローバル公開
// ============================================================

window.loadSOPDetail = loadSOPDetail;
window.displaySOPDetail = displaySOPDetail;
window.loadRelatedSOP = loadRelatedSOP;
window.startInspectionRecord = startInspectionRecord;
window.cancelRecord = cancelRecord;
window.submitInspectionRecord = submitInspectionRecord;
window.updateExecutionStats = updateExecutionStats;
window.downloadSOP = downloadSOP;
window.printChecklist = printChecklist;
window.editSOP = editSOP;
window.closeEditSOPModal = closeEditSOPModal;
window.submitEditSOP = submitEditSOP;
window.shareSOP = shareSOP;
window.retryLoadSOP = retryLoadSOP;

export {
  loadSOPDetail,
  displaySOPDetail,
  loadRelatedSOP,
  startInspectionRecord,
  cancelRecord,
  submitInspectionRecord,
  updateExecutionStats,
  downloadSOP,
  printChecklist,
  editSOP,
  closeEditSOPModal,
  submitEditSOP,
  shareSOP,
  retryLoadSOP
};
