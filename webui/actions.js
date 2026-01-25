// ============================================================
// 共通アクション関数
// 未実装機能のプレースホルダー実装
// ============================================================

/**
 * トースト通知を表示
 * @param {string} message - 表示するメッセージ
 * @param {string} type - 通知タイプ ('success', 'error', 'warning', 'info')
 */
function showToast(message, type = 'info') {
  // トーストコンテナを取得または作成
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  // トースト要素を作成（XSS対策: innerHTML → DOM API使用）
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  // アイコンを設定
  const iconMap = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ'
  };

  const iconDiv = document.createElement('div');
  iconDiv.className = 'toast-icon';
  iconDiv.textContent = iconMap[type] || 'ℹ';

  const messageDiv = document.createElement('div');
  messageDiv.className = 'toast-message';
  messageDiv.textContent = message;

  toast.appendChild(iconDiv);
  toast.appendChild(messageDiv);

  container.appendChild(toast);

  // アニメーション表示
  setTimeout(() => {
    toast.classList.add('show');
  }, 10);

  // 3秒後に削除
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => {
      container.removeChild(toast);
      // コンテナが空なら削除
      if (container.children.length === 0) {
        document.body.removeChild(container);
      }
    }, 300);
  }, 3000);
}

// グローバルに公開
window.showToast = showToast;

/**
 * 配信申請処理
 */
function submitDistribution(type, data) {
  // 🔧 修正: 確認ダイアログを追加
  const confirmed = confirm(
    '現場に共有申請を送信しますか？\n\n' +
    '承認者にメール通知が送信されます。\n' +
    '※現在はサンプル実装です（Phase Dで完全実装予定）'
  );

  if (!confirmed) {
    logger.log('[ACTION] Distribution cancelled by user');
    return;
  }

  showToast('配信申請を送信しました', 'success');
  logger.log('[ACTION] Distribution submitted:', type, data);

  // 将来実装: Microsoft 365連携（SharePoint/OneDrive）と同時実装推奨
  // - バックエンドに /api/v1/distribution/submit エンドポイントを追加
  // - type: 'sharepoint' | 'onedrive' | 'email'
  // - 配信先の管理者承認フローと統合
  // Issue: Phase D機能として実装予定
}

/**
 * 改訂提案処理
 */
function proposeRevision(type) {
  const reason = prompt(`【改訂提案】\n\n改訂理由を入力してください:`);
  if (reason) {
    alert(`改訂提案を受け付けました。\n理由: ${reason}\n\n品質保証部門に通知されます。`);
    logger.log('[ACTION] Revision proposed:', type, reason);
  }
}

/**
 * ダッシュボード共有処理
 */
function shareDashboard() {
  const recipients = prompt('共有先のメールアドレスを入力してください（カンマ区切り）:');
  if (recipients) {
    alert(`ダッシュボードを共有しました。\n送信先: ${recipients}`);
    logger.log('[ACTION] Dashboard shared to:', recipients);
  }
}

/**
 * 承認箱を開く
 */
function openApprovalBox() {
  window.location.href = 'admin.html#approvals';
}

/**
 * 朝礼用サマリ生成
 */
function generateMorningSummary() {
  alert('【朝礼用サマリ】\n\n本日の重要事項:\n• 承認待ち: 7件\n• 新規事故報告: 2件\n• 期限切れ是正措置: 1件\n\nPDFをダウンロードしますか？');
  logger.log('[ACTION] Morning summary generated');
}

/**
 * PDFダウンロード
 */
function downloadPDF(type, title) {
  alert(`【PDFダウンロード】\n\nタイプ: ${type}\nファイル名: ${title}.pdf\n\nダウンロード機能は今後実装予定です。`);
  logger.log('[ACTION] PDF download:', type, title);
}

/**
 * 点検表開始
 */
function startInspection(sopId) {
  const confirmed = confirm('点検表を開始しますか？\n\nチェックリストが表示されます。');
  if (confirmed) {
    alert('点検表機能は今後実装予定です。');
    logger.log('[ACTION] Inspection started for SOP:', sopId);
  }
}

/**
 * 影響評価記録
 */
function recordImpactAssessment() {
  const notes = prompt('影響評価メモを入力してください:');
  if (notes) {
    alert(`影響評価を記録しました。\n内容: ${notes}`);
    logger.log('[ACTION] Impact assessment recorded:', notes);
  }
}

/**
 * 現場周知作成
 */
function createNotice() {
  alert('現場周知文書の作成画面を表示します。\n（今後実装予定）');
  logger.log('[ACTION] Notice creation initiated');
}

/**
 * 是正措置登録
 */
function registerCorrectiveAction() {
  const action = prompt('是正措置を入力してください:');
  if (action) {
    alert(`是正措置を登録しました。\n内容: ${action}\n\n関係者に通知されます。`);
    logger.log('[ACTION] Corrective action registered:', action);
  }
}

/**
 * 再発防止策作成
 */
function createPreventionPlan() {
  alert('再発防止策作成フォームを表示します。\n（今後実装予定）');
  logger.log('[ACTION] Prevention plan creation initiated');
}

/**
 * 専門家相談起案
 */
function submitConsultation() {
  const form = document.querySelector('form');
  if (!form) {
    alert('相談を起案しました。\n（フォーム機能は今後実装予定）');
    return;
  }

  const title = document.querySelector('input[type="text"]')?.value;
  const content = document.querySelector('textarea')?.value;

  if (!title || !content) {
    alert('タイトルと相談内容を入力してください。');
    return;
  }

  alert(`【専門家相談】\n\nタイトル: ${title}\n\n相談内容が送信されました。\n専門家から回答があり次第、通知します。`);
  logger.log('[ACTION] Consultation submitted:', { title, content });
}

/**
 * 資料添付
 */
function attachDocument() {
  alert('ファイル選択ダイアログを表示します。\n（今後実装予定）');
  logger.log('[ACTION] Document attachment initiated');
}

/**
 * 差分確認
 */
function viewDiff() {
  alert('改訂差分の比較画面を表示します。\n（今後実装予定）');
  logger.log('[ACTION] Diff view initiated');
}

/**
 * バージョン比較
 */
function compareVersions() {
  alert('バージョン比較画面を表示します。\n（今後実装予定）');
  logger.log('[ACTION] Version comparison initiated');
}

/**
 * 既存相談参照
 */
function viewPastConsultations() {
  alert('過去の相談履歴を表示します。\n（今後実装予定）');
  logger.log('[ACTION] Past consultations view initiated');
}

/**
 * 事故レポートステータス更新
 */
function updateIncidentStatus() {
  const modal = document.getElementById('statusModal');
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  } else {
    alert('ステータス更新機能は準備中です');
  }
}

/**
 * ステータスモーダルを閉じる
 */
function closeStatusModal() {
  const modal = document.getElementById('statusModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

/**
 * 事故レポート編集
 */
function editIncident() {
  alert('事故レポート編集機能は準備中です');
  logger.log('[ACTION] Edit incident initiated');
}

/**
 * 専門家相談編集
 */
function editConsult() {
  alert('専門家相談編集機能は準備中です');
  logger.log('[ACTION] Edit consultation initiated');
}

/**
 * 専門家相談クローズ
 */
function closeConsult() {
  const confirmed = confirm('この相談を解決済みにしますか？');
  if (confirmed) {
    alert('相談を解決済みにしました');
    logger.log('[ACTION] Consultation closed');
  }
}

/**
 * フォロー切り替え
 */
function toggleFollow() {
  const icon = document.getElementById('followIcon');
  if (icon) {
    if (icon.textContent === '☆') {
      icon.textContent = '★';
      alert('この相談をフォローしました');
    } else {
      icon.textContent = '☆';
      alert('フォローを解除しました');
    }
  }
}

/**
 * 回答フォームリセット
 */
function resetAnswerForm() {
  const form = document.getElementById('answerForm');
  if (form) {
    form.reset();
  }
}

/**
 * 回答詳細モーダルを閉じる
 */
function closeAnswerDetailModal() {
  const modal = document.getElementById('answerDetailModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

/**
 * ベストアンサーに選択
 */
function selectBestAnswer() {
  const confirmed = confirm('この回答をベストアンサーに選択しますか？');
  if (confirmed) {
    alert('ベストアンサーに選択しました');
    closeAnswerDetailModal();
  }
}

/**
 * SOP編集記録開始
 */
function startRecord() {
  const formEl = document.getElementById('record-form');
  if (formEl) {
    formEl.style.display = 'block';
    formEl.scrollIntoView({ behavior: 'smooth' });
  } else {
    alert('記録開始機能は準備中です');
  }
}

/**
 * 記録キャンセル
 */
function cancelRecord() {
  const formEl = document.getElementById('record-form');
  if (formEl) {
    formEl.style.display = 'none';
  }
}

// ============================================================
// グローバル関数として登録（onclick属性から呼び出し可能）
// ============================================================

window.submitDistribution = submitDistribution;
window.proposeRevision = proposeRevision;
window.shareDashboard = shareDashboard;
window.openApprovalBox = openApprovalBox;
window.generateMorningSummary = generateMorningSummary;
window.downloadPDF = downloadPDF;
window.startInspection = startInspection;
window.recordImpactAssessment = recordImpactAssessment;
window.createNotice = createNotice;
window.registerCorrectiveAction = registerCorrectiveAction;
window.createPreventionPlan = createPreventionPlan;
window.submitConsultation = submitConsultation;
window.attachDocument = attachDocument;
window.viewDiff = viewDiff;
window.compareVersions = compareVersions;
window.viewPastConsultations = viewPastConsultations;
window.updateIncidentStatus = updateIncidentStatus;
window.closeStatusModal = closeStatusModal;
window.editIncident = editIncident;
window.editConsult = editConsult;
window.closeConsult = closeConsult;
window.toggleFollow = toggleFollow;
window.resetAnswerForm = resetAnswerForm;
window.closeAnswerDetailModal = closeAnswerDetailModal;
window.selectBestAnswer = selectBestAnswer;
window.startRecord = startRecord;
window.cancelRecord = cancelRecord;
