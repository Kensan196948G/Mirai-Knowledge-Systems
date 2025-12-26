// ============================================================
// 共通アクション関数
// 未実装機能のプレースホルダー実装
// ============================================================

/**
 * 配信申請処理
 */
function submitDistribution(type, data) {
  alert(`【配信申請】\n\nタイプ: ${type}\n\nこの機能は今後実装予定です。\n配信申請が送信されました。`);
  console.log('[ACTION] Distribution submitted:', type, data);
}

/**
 * 改訂提案処理
 */
function proposeRevision(type) {
  const reason = prompt(`【改訂提案】\n\n改訂理由を入力してください:`);
  if (reason) {
    alert(`改訂提案を受け付けました。\n理由: ${reason}\n\n品質保証部門に通知されます。`);
    console.log('[ACTION] Revision proposed:', type, reason);
  }
}

/**
 * ダッシュボード共有処理
 */
function shareDashboard() {
  const recipients = prompt('共有先のメールアドレスを入力してください（カンマ区切り）:');
  if (recipients) {
    alert(`ダッシュボードを共有しました。\n送信先: ${recipients}`);
    console.log('[ACTION] Dashboard shared to:', recipients);
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
  console.log('[ACTION] Morning summary generated');
}

/**
 * PDFダウンロード
 */
function downloadPDF(type, title) {
  alert(`【PDFダウンロード】\n\nタイプ: ${type}\nファイル名: ${title}.pdf\n\nダウンロード機能は今後実装予定です。`);
  console.log('[ACTION] PDF download:', type, title);
}

/**
 * 点検表開始
 */
function startInspection(sopId) {
  const confirmed = confirm('点検表を開始しますか？\n\nチェックリストが表示されます。');
  if (confirmed) {
    alert('点検表機能は今後実装予定です。');
    console.log('[ACTION] Inspection started for SOP:', sopId);
  }
}

/**
 * 影響評価記録
 */
function recordImpactAssessment() {
  const notes = prompt('影響評価メモを入力してください:');
  if (notes) {
    alert(`影響評価を記録しました。\n内容: ${notes}`);
    console.log('[ACTION] Impact assessment recorded:', notes);
  }
}

/**
 * 現場周知作成
 */
function createNotice() {
  alert('現場周知文書の作成画面を表示します。\n（今後実装予定）');
  console.log('[ACTION] Notice creation initiated');
}

/**
 * 是正措置登録
 */
function registerCorrectiveAction() {
  const action = prompt('是正措置を入力してください:');
  if (action) {
    alert(`是正措置を登録しました。\n内容: ${action}\n\n関係者に通知されます。`);
    console.log('[ACTION] Corrective action registered:', action);
  }
}

/**
 * 再発防止策作成
 */
function createPreventionPlan() {
  alert('再発防止策作成フォームを表示します。\n（今後実装予定）');
  console.log('[ACTION] Prevention plan creation initiated');
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
  console.log('[ACTION] Consultation submitted:', { title, content });
}

/**
 * 資料添付
 */
function attachDocument() {
  alert('ファイル選択ダイアログを表示します。\n（今後実装予定）');
  console.log('[ACTION] Document attachment initiated');
}

/**
 * 差分確認
 */
function viewDiff() {
  alert('改訂差分の比較画面を表示します。\n（今後実装予定）');
  console.log('[ACTION] Diff view initiated');
}

/**
 * バージョン比較
 */
function compareVersions() {
  alert('バージョン比較画面を表示します。\n（今後実装予定）');
  console.log('[ACTION] Version comparison initiated');
}

/**
 * 既存相談参照
 */
function viewPastConsultations() {
  alert('過去の相談履歴を表示します。\n（今後実装予定）');
  console.log('[ACTION] Past consultations view initiated');
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
