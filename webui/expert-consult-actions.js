// ============================================================
// 専門家相談詳細ページ専用アクション
// ============================================================

/**
 * フォロー状態をトグル
 */
function toggleFollow() {
  const urlParams = new URLSearchParams(window.location.search);
  const consultId = urlParams.get('id');
  const followIcon = document.getElementById('followIcon');

  if (!consultId || !followIcon) return;

  // localStorageから現在のフォロー状態を取得
  const followKey = `consult_follow_${consultId}`;
  const isFollowing = localStorage.getItem(followKey) === 'true';

  // トグル
  const newState = !isFollowing;
  localStorage.setItem(followKey, newState.toString());

  // アイコン更新
  followIcon.textContent = newState ? '★' : '☆';

  // ボタンテキスト更新
  const followBtn = followIcon.closest('button');
  if (followBtn) {
    // 既存の内容をクリア
    while (followBtn.firstChild) {
      followBtn.removeChild(followBtn.firstChild);
    }

    const iconSpan = document.createElement('span');
    iconSpan.id = 'followIcon';
    iconSpan.textContent = newState ? '★' : '☆';
    followBtn.appendChild(iconSpan);

    followBtn.appendChild(document.createTextNode(' '));

    const textNode = document.createTextNode(newState ? 'フォロー中' : 'フォロー');
    followBtn.appendChild(textNode);
  }

  // フォロワーカウント更新
  const followerCountEl = document.getElementById('followerCount');
  if (followerCountEl) {
    const currentCount = parseInt(followerCountEl.textContent) || 0;
    followerCountEl.textContent = newState ? currentCount + 1 : Math.max(0, currentCount - 1);
  }

  // トースト通知
  showToastNotification(newState ? 'フォローしました' : 'フォロー解除しました', 'success');
  logger.log('[FOLLOW] Toggled:', { consultId, isFollowing: newState });
}

/**
 * 相談を共有
 */
function shareConsult() {
  const modal = document.getElementById('shareConsultModal');
  if (!modal) {
    // モーダルが存在しない場合は動的に作成
    createShareConsultModal();
    return shareConsult();
  }

  const shareUrlEl = document.getElementById('shareConsultUrl');
  if (shareUrlEl) {
    shareUrlEl.value = window.location.href;
  }

  modal.style.display = 'flex';
}

/**
 * 共有モーダルを作成
 * XSS対策: DOM API使用（insertAdjacentHTML完全排除）
 */
function createShareConsultModal() {
  // DOMHelperを使用（window.DOMHelperとしてグローバルに利用可能）
  const modal = window.DOMHelper.createElement('div', {
    id: 'shareConsultModal',
    class: 'modal',
    style: { display: 'none' }
  });

  const content = window.DOMHelper.createElement('div', { class: 'modal-content' });

  // ヘッダー
  const header = window.DOMHelper.createElement('div', { class: 'modal-header' });
  const title = window.DOMHelper.createElement('h2', {}, '相談を共有');
  const closeBtn = window.DOMHelper.createElement('button', {
    class: 'modal-close',
    onclick: 'closeShareConsultModal()'
  }, '×');
  header.appendChild(title);
  header.appendChild(closeBtn);

  // ボディ
  const body = window.DOMHelper.createElement('div', { class: 'modal-body' });

  // URLフィールド
  const urlField = window.DOMHelper.createElement('div', { class: 'field' });
  const urlLabel = window.DOMHelper.createElement('label', {}, 'URL');
  const urlInput = window.DOMHelper.createElement('input', {
    type: 'text',
    id: 'shareConsultUrl',
    readonly: true,
    style: { background: '#f5f5f5' }
  });
  const copyBtn = window.DOMHelper.createElement('button', {
    class: 'cta ghost',
    onclick: 'copyShareConsultUrl()',
    style: { marginTop: '8px' }
  }, '📋 URLをコピー');
  urlField.appendChild(urlLabel);
  urlField.appendChild(urlInput);
  urlField.appendChild(copyBtn);

  // 共有方法フィールド
  const shareField = window.DOMHelper.createElement('div', {
    class: 'field',
    style: { marginTop: '20px' }
  });
  const shareLabel = window.DOMHelper.createElement('label', {}, '共有方法を選択');
  const shareButtons = window.DOMHelper.createElement('div', {
    style: { display: 'grid', gap: '10px', marginTop: '10px' }
  });
  const emailBtn = window.DOMHelper.createElement('button', {
    class: 'cta ghost',
    onclick: 'shareConsultViaEmail()'
  }, '📧 メールで共有');
  const slackBtn = window.DOMHelper.createElement('button', {
    class: 'cta ghost',
    onclick: 'shareConsultViaSlack()'
  }, '💬 Slackで共有');
  const teamsBtn = window.DOMHelper.createElement('button', {
    class: 'cta ghost',
    onclick: 'shareConsultViaTeams()'
  }, '👥 Teamsで共有');
  shareButtons.appendChild(emailBtn);
  shareButtons.appendChild(slackBtn);
  shareButtons.appendChild(teamsBtn);
  shareField.appendChild(shareLabel);
  shareField.appendChild(shareButtons);

  // ボディ組み立て
  body.appendChild(urlField);
  body.appendChild(shareField);

  // コンテンツ組み立て
  content.appendChild(header);
  content.appendChild(body);

  // モーダル組み立て
  modal.appendChild(content);

  // DOM追加（セキュア）
  document.body.appendChild(modal);
}

/**
 * 共有モーダルを閉じる
 */
function closeShareConsultModal() {
  const modal = document.getElementById('shareConsultModal');
  if (modal) modal.style.display = 'none';
}

/**
 * URLをコピー
 */
function copyShareConsultUrl() {
  const shareUrlEl = document.getElementById('shareConsultUrl');
  if (shareUrlEl) {
    shareUrlEl.select();
    document.execCommand('copy');
    showToastNotification('URLをコピーしました', 'success');
  }
}

/**
 * メールで共有
 */
function shareConsultViaEmail() {
  const url = encodeURIComponent(window.location.href);
  const title = encodeURIComponent(document.getElementById('consultTitle')?.textContent || '専門家相談');
  const subject = `相談共有: ${decodeURIComponent(title)}`;
  const body = `以下の専門家相談を共有します:\n\n${decodeURIComponent(url)}`;
  window.location.href = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  closeShareConsultModal();
}

/**
 * Slackで共有
 */
function shareConsultViaSlack() {
  showToastNotification('Slack連携機能は準備中です', 'info');
  logger.log('[SHARE] Slack share initiated');
}

/**
 * Teamsで共有
 */
function shareConsultViaTeams() {
  showToastNotification('Teams連携機能は準備中です', 'info');
  logger.log('[SHARE] Teams share initiated');
}

/**
 * 相談を編集
 */
function editConsult() {
  const urlParams = new URLSearchParams(window.location.search);
  const consultId = urlParams.get('id');

  if (!consultId) {
    showToastNotification('相談IDが取得できません', 'error');
    return;
  }

  // localStorageから相談データを取得
  const consultData = JSON.parse(localStorage.getItem('consultations_details') || '[]');
  const consult = consultData.find(c => c.id === parseInt(consultId));

  if (!consult) {
    showToastNotification('相談データが見つかりません', 'error');
    return;
  }

  // 編集モーダルを作成・表示
  createEditConsultModal(consult);
}

/**
 * 編集モーダルを作成
 * XSS対策: DOM API使用（insertAdjacentHTML完全排除）
 */
function createEditConsultModal(consult) {
  const existingModal = document.getElementById('editConsultModal');
  if (existingModal) existingModal.remove();

  // DOMHelperを使用
  const modal = window.DOMHelper.createElement('div', {
    id: 'editConsultModal',
    class: 'modal',
    style: { display: 'flex' }
  });

  const content = window.DOMHelper.createElement('div', { class: 'modal-content' });

  // ヘッダー
  const header = window.DOMHelper.createElement('div', { class: 'modal-header' });
  const title = window.DOMHelper.createElement('h2', {}, '相談を編集');
  const closeBtn = window.DOMHelper.createElement('button', {
    class: 'modal-close',
    onclick: 'closeEditConsultModal()'
  }, '×');
  header.appendChild(title);
  header.appendChild(closeBtn);

  // ボディ
  const body = window.DOMHelper.createElement('div', { class: 'modal-body' });
  const form = window.DOMHelper.createElement('form', { id: 'editConsultForm' });

  // タイトルフィールド
  const titleField = window.DOMHelper.createElement('div', { class: 'field' });
  const titleLabel = window.DOMHelper.createElement('label', {});
  titleLabel.appendChild(document.createTextNode('タイトル '));
  const titleRequired = window.DOMHelper.createElement('span', { class: 'required' }, '*');
  titleLabel.appendChild(titleRequired);
  const titleInput = window.DOMHelper.createElement('input', {
    type: 'text',
    id: 'editConsultTitle',
    value: consult.title, // textContentで設定されるため自動エスケープ
    required: true
  });
  titleField.appendChild(titleLabel);
  titleField.appendChild(titleInput);

  // カテゴリフィールド
  const categoryField = window.DOMHelper.createElement('div', { class: 'field' });
  const categoryLabel = window.DOMHelper.createElement('label', {});
  categoryLabel.appendChild(document.createTextNode('カテゴリ '));
  const categoryRequired = window.DOMHelper.createElement('span', { class: 'required' }, '*');
  categoryLabel.appendChild(categoryRequired);
  const categorySelect = window.DOMHelper.createElement('select', {
    id: 'editConsultCategory',
    required: true
  });
  ['技術相談', '安全対策', '品質管理', '工程計画', 'その他'].forEach(cat => {
    const option = window.DOMHelper.createElement('option', {
      value: cat,
      selected: consult.category === cat
    }, cat);
    categorySelect.appendChild(option);
  });
  categoryField.appendChild(categoryLabel);
  categoryField.appendChild(categorySelect);

  // 優先度フィールド
  const priorityField = window.DOMHelper.createElement('div', { class: 'field' });
  const priorityLabel = window.DOMHelper.createElement('label', {});
  priorityLabel.appendChild(document.createTextNode('優先度 '));
  const priorityRequired = window.DOMHelper.createElement('span', { class: 'required' }, '*');
  priorityLabel.appendChild(priorityRequired);
  const prioritySelect = window.DOMHelper.createElement('select', {
    id: 'editConsultPriority',
    required: true
  });
  ['緊急', '高', '通常', '低'].forEach(pri => {
    const option = window.DOMHelper.createElement('option', {
      value: pri,
      selected: consult.priority === pri
    }, pri);
    prioritySelect.appendChild(option);
  });
  priorityField.appendChild(priorityLabel);
  priorityField.appendChild(prioritySelect);

  // 相談内容フィールド
  const contentField = window.DOMHelper.createElement('div', { class: 'field' });
  const contentLabel = window.DOMHelper.createElement('label', {});
  contentLabel.appendChild(document.createTextNode('相談内容 '));
  const contentRequired = window.DOMHelper.createElement('span', { class: 'required' }, '*');
  contentLabel.appendChild(contentRequired);
  const contentTextarea = window.DOMHelper.createElement('textarea', {
    id: 'editConsultContent',
    rows: 6,
    required: true
  });
  contentTextarea.value = consult.content; // textContentで自動エスケープ
  contentField.appendChild(contentLabel);
  contentField.appendChild(contentTextarea);

  // アクションボタン
  const actions = window.DOMHelper.createElement('div', { class: 'modal-actions' });
  const cancelBtn = window.DOMHelper.createElement('button', {
    type: 'button',
    class: 'cta ghost',
    onclick: 'closeEditConsultModal()'
  }, 'キャンセル');
  const submitBtn = window.DOMHelper.createElement('button', {
    type: 'submit',
    class: 'cta'
  }, '保存');
  actions.appendChild(cancelBtn);
  actions.appendChild(submitBtn);

  // フォーム組み立て
  form.appendChild(titleField);
  form.appendChild(categoryField);
  form.appendChild(priorityField);
  form.appendChild(contentField);
  form.appendChild(actions);

  // ボディ組み立て
  body.appendChild(form);

  // コンテンツ組み立て
  content.appendChild(header);
  content.appendChild(body);

  // モーダル組み立て
  modal.appendChild(content);

  // DOM追加（セキュア）
  document.body.appendChild(modal);

  // フォーム送信イベント
  form.addEventListener('submit', function(e) {
    e.preventDefault();
    saveEditConsult(consult.id);
  });
}

/**
 * HTMLエスケープ
 */
function escapeHtml(text) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * 編集内容を保存
 */
function saveEditConsult(consultId) {
  const title = document.getElementById('editConsultTitle').value;
  const category = document.getElementById('editConsultCategory').value;
  const priority = document.getElementById('editConsultPriority').value;
  const content = document.getElementById('editConsultContent').value;

  // localStorageから相談データを取得
  const consultData = JSON.parse(localStorage.getItem('consultations_details') || '[]');
  const consultIndex = consultData.findIndex(c => c.id === parseInt(consultId));

  if (consultIndex === -1) {
    showToastNotification('相談データが見つかりません', 'error');
    return;
  }

  // 更新
  consultData[consultIndex].title = title;
  consultData[consultIndex].category = category;
  consultData[consultIndex].priority = priority;
  consultData[consultIndex].content = content;
  consultData[consultIndex].updated_at = new Date().toISOString();

  // 保存
  localStorage.setItem('consultations_details', JSON.stringify(consultData));

  // モーダルを閉じる
  closeEditConsultModal();

  // トースト通知
  showToastNotification('相談を更新しました', 'success');

  // ページをリロード
  setTimeout(() => window.location.reload(), 1000);
}

/**
 * 編集モーダルを閉じる
 */
function closeEditConsultModal() {
  const modal = document.getElementById('editConsultModal');
  if (modal) modal.remove();
}

/**
 * 相談を解決済みにする
 */
function closeConsult() {
  const urlParams = new URLSearchParams(window.location.search);
  const consultId = urlParams.get('id');

  if (!consultId) {
    showToastNotification('相談IDが取得できません', 'error');
    return;
  }

  // 確認ダイアログ
  if (!confirm('この相談を解決済みにしますか?\n\nステータスが「解決済み」に変更されます。')) {
    return;
  }

  // localStorageから相談データを取得
  const consultData = JSON.parse(localStorage.getItem('consultations_details') || '[]');
  const consultIndex = consultData.findIndex(c => c.id === parseInt(consultId));

  if (consultIndex === -1) {
    showToastNotification('相談データが見つかりません', 'error');
    return;
  }

  // ステータスを更新
  consultData[consultIndex].status = 'resolved';
  consultData[consultIndex].resolved_at = new Date().toISOString();
  consultData[consultIndex].updated_at = new Date().toISOString();

  // 保存
  localStorage.setItem('consultations_details', JSON.stringify(consultData));

  // トースト通知
  showToastNotification('相談を解決済みにしました', 'success');

  // ページをリロード
  setTimeout(() => window.location.reload(), 1000);
}

/**
 * 新規相談を作成（グローバル関数）
 */
function submitNewConsultation() {
  createNewConsultModal();
}

/**
 * 新規相談モーダルを作成
 * XSS対策: DOM API使用（insertAdjacentHTML完全排除）
 */
function createNewConsultModal() {
  const existingModal = document.getElementById('newConsultModal');
  if (existingModal) existingModal.remove();

  // DOMHelperを使用
  const modal = window.DOMHelper.createElement('div', {
    id: 'newConsultModal',
    class: 'modal',
    style: { display: 'flex' }
  });

  const content = window.DOMHelper.createElement('div', { class: 'modal-content' });

  // ヘッダー
  const header = window.DOMHelper.createElement('div', { class: 'modal-header' });
  const title = window.DOMHelper.createElement('h2', {}, '新規相談を作成');
  const closeBtn = window.DOMHelper.createElement('button', {
    class: 'modal-close',
    onclick: 'closeNewConsultModal()'
  }, '×');
  header.appendChild(title);
  header.appendChild(closeBtn);

  // ボディ
  const body = window.DOMHelper.createElement('div', { class: 'modal-body' });
  const form = window.DOMHelper.createElement('form', { id: 'newConsultForm' });

  // タイトルフィールド
  const titleField = window.DOMHelper.createElement('div', { class: 'field' });
  const titleLabel = window.DOMHelper.createElement('label', {});
  titleLabel.appendChild(document.createTextNode('タイトル '));
  const titleRequired = window.DOMHelper.createElement('span', { class: 'required' }, '*');
  titleLabel.appendChild(titleRequired);
  const titleInput = window.DOMHelper.createElement('input', {
    type: 'text',
    id: 'newConsultTitle',
    required: true,
    placeholder: '相談のタイトルを入力してください'
  });
  titleField.appendChild(titleLabel);
  titleField.appendChild(titleInput);

  // カテゴリフィールド
  const categoryField = window.DOMHelper.createElement('div', { class: 'field' });
  const categoryLabel = window.DOMHelper.createElement('label', {});
  categoryLabel.appendChild(document.createTextNode('カテゴリ '));
  const categoryRequired = window.DOMHelper.createElement('span', { class: 'required' }, '*');
  categoryLabel.appendChild(categoryRequired);
  const categorySelect = window.DOMHelper.createElement('select', {
    id: 'newConsultCategory',
    required: true
  });
  ['', '技術相談', '安全対策', '品質管理', '工程計画', 'その他'].forEach((cat, idx) => {
    const option = window.DOMHelper.createElement('option', {
      value: cat
    }, cat || '選択してください');
    categorySelect.appendChild(option);
  });
  categoryField.appendChild(categoryLabel);
  categoryField.appendChild(categorySelect);

  // 優先度フィールド
  const priorityField = window.DOMHelper.createElement('div', { class: 'field' });
  const priorityLabel = window.DOMHelper.createElement('label', {});
  priorityLabel.appendChild(document.createTextNode('優先度 '));
  const priorityRequired = window.DOMHelper.createElement('span', { class: 'required' }, '*');
  priorityLabel.appendChild(priorityRequired);
  const prioritySelect = window.DOMHelper.createElement('select', {
    id: 'newConsultPriority',
    required: true
  });
  [
    { value: '通常', selected: true },
    { value: '高', selected: false },
    { value: '緊急', selected: false },
    { value: '低', selected: false }
  ].forEach(pri => {
    const option = window.DOMHelper.createElement('option', {
      value: pri.value,
      selected: pri.selected
    }, pri.value);
    prioritySelect.appendChild(option);
  });
  priorityField.appendChild(priorityLabel);
  priorityField.appendChild(prioritySelect);

  // 相談内容フィールド
  const contentField = window.DOMHelper.createElement('div', { class: 'field' });
  const contentLabel = window.DOMHelper.createElement('label', {});
  contentLabel.appendChild(document.createTextNode('相談内容 '));
  const contentRequired = window.DOMHelper.createElement('span', { class: 'required' }, '*');
  contentLabel.appendChild(contentRequired);
  const contentTextarea = window.DOMHelper.createElement('textarea', {
    id: 'newConsultContent',
    rows: 6,
    required: true,
    placeholder: '詳細な相談内容を入力してください'
  });
  contentField.appendChild(contentLabel);
  contentField.appendChild(contentTextarea);

  // タグフィールド
  const tagsField = window.DOMHelper.createElement('div', { class: 'field' });
  const tagsLabel = window.DOMHelper.createElement('label', {}, 'タグ（カンマ区切り）');
  const tagsInput = window.DOMHelper.createElement('input', {
    type: 'text',
    id: 'newConsultTags',
    placeholder: '例: コンクリート, 品質, 養生'
  });
  tagsField.appendChild(tagsLabel);
  tagsField.appendChild(tagsInput);

  // アクションボタン
  const actions = window.DOMHelper.createElement('div', { class: 'modal-actions' });
  const cancelBtn = window.DOMHelper.createElement('button', {
    type: 'button',
    class: 'cta ghost',
    onclick: 'closeNewConsultModal()'
  }, 'キャンセル');
  const submitBtn = window.DOMHelper.createElement('button', {
    type: 'submit',
    class: 'cta'
  }, '作成');
  actions.appendChild(cancelBtn);
  actions.appendChild(submitBtn);

  // フォーム組み立て
  form.appendChild(titleField);
  form.appendChild(categoryField);
  form.appendChild(priorityField);
  form.appendChild(contentField);
  form.appendChild(tagsField);
  form.appendChild(actions);

  // ボディ組み立て
  body.appendChild(form);

  // コンテンツ組み立て
  content.appendChild(header);
  content.appendChild(body);

  // モーダル組み立て
  modal.appendChild(content);

  // DOM追加（セキュア）
  document.body.appendChild(modal);

  // フォーム送信イベント
  form.addEventListener('submit', function(e) {
    e.preventDefault();
    saveNewConsult();
  });
}

/**
 * 新規相談を保存
 */
function saveNewConsult() {
  const title = document.getElementById('newConsultTitle').value;
  const category = document.getElementById('newConsultCategory').value;
  const priority = document.getElementById('newConsultPriority').value;
  const content = document.getElementById('newConsultContent').value;
  const tagsInput = document.getElementById('newConsultTags').value;
  const tags = tagsInput ? tagsInput.split(',').map(t => t.trim()) : [];

  // localStorageから相談データを取得
  const consultData = JSON.parse(localStorage.getItem('consultations_details') || '[]');

  // 新しいIDを生成
  const newId = consultData.length > 0 ? Math.max(...consultData.map(c => c.id)) + 1 : 1;

  // 新規相談オブジェクト
  const newConsult = {
    id: newId,
    title: title,
    category: category,
    priority: priority,
    content: content,
    tags: tags,
    status: 'pending',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    requester: localStorage.getItem('user_name') || 'ユーザー',
    project: '現場12',
    answers: [],
    views: 0,
    follower_count: 0
  };

  // 追加
  consultData.push(newConsult);

  // 保存
  localStorage.setItem('consultations_details', JSON.stringify(consultData));

  // モーダルを閉じる
  closeNewConsultModal();

  // トースト通知
  showToastNotification('新規相談を作成しました', 'success');

  // 詳細ページにリダイレクト
  setTimeout(() => {
    window.location.href = `expert-consult.html?id=${newId}`;
  }, 1000);
}

/**
 * 新規相談モーダルを閉じる
 */
function closeNewConsultModal() {
  const modal = document.getElementById('newConsultModal');
  if (modal) modal.remove();
}

/**
 * 回答フォームをリセット
 */
function resetAnswerForm() {
  document.getElementById('answerContent').value = '';
  document.getElementById('answerReferences').value = '';
  document.getElementById('answerAttachment').value = '';
  document.getElementById('markAsBest').checked = false;
  showToastNotification('フォームをリセットしました', 'info');
}

/**
 * 回答詳細モーダルを閉じる
 */
function closeAnswerDetailModal() {
  const modal = document.getElementById('answerDetailModal');
  if (modal) modal.classList.remove('is-active');
}

/**
 * ベストアンサーに選択
 */
function selectBestAnswer() {
  showToastNotification('ベストアンサー機能は準備中です', 'info');
  logger.log('[ANSWER] Best answer selection initiated');
}

/**
 * トースト通知を表示
 */
function showToastNotification(message, type = 'info') {
  // トーストコンテナがなければ作成
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  // トースト要素を作成
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const iconDiv = document.createElement('div');
  iconDiv.className = 'toast-icon';
  iconDiv.textContent = type === 'success' ? '✓' : type === 'error' ? '✗' : type === 'warning' ? '⚠' : 'ℹ';

  const messageDiv = document.createElement('div');
  messageDiv.className = 'toast-message';
  messageDiv.textContent = message;

  toast.appendChild(iconDiv);
  toast.appendChild(messageDiv);

  container.appendChild(toast);

  // アニメーション
  setTimeout(() => toast.classList.add('show'), 10);

  // 3秒後に削除
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ============================================================
// ページロード時の初期化
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;

  if (path.includes('expert-consult.html')) {
    // フォロー状態を復元
    const urlParams = new URLSearchParams(window.location.search);
    const consultId = urlParams.get('id');
    if (consultId) {
      const followKey = `consult_follow_${consultId}`;
      const isFollowing = localStorage.getItem(followKey) === 'true';
      const followIcon = document.getElementById('followIcon');
      if (followIcon) {
        followIcon.textContent = isFollowing ? '★' : '☆';
        const followBtn = followIcon.closest('button');
        if (followBtn) {
          // 既存の内容をクリア
          while (followBtn.firstChild) {
            followBtn.removeChild(followBtn.firstChild);
          }

          const iconSpan = document.createElement('span');
          iconSpan.id = 'followIcon';
          iconSpan.textContent = isFollowing ? '★' : '☆';
          followBtn.appendChild(iconSpan);

          followBtn.appendChild(document.createTextNode(' '));

          const textNode = document.createTextNode(isFollowing ? 'フォロー中' : 'フォロー');
          followBtn.appendChild(textNode);
        }
      }
    }

    // 回答フォーム送信イベント
    const answerForm = document.getElementById('answerForm');
    if (answerForm) {
      answerForm.addEventListener('submit', handleAnswerSubmit);
    }
  }
});

/**
 * 回答フォーム送信処理
 */
function handleAnswerSubmit(e) {
  e.preventDefault();

  const urlParams = new URLSearchParams(window.location.search);
  const consultId = urlParams.get('id');

  if (!consultId) {
    showToastNotification('相談IDが取得できません', 'error');
    return;
  }

  const content = document.getElementById('answerContent').value;
  const references = document.getElementById('answerReferences').value;
  const isBest = document.getElementById('markAsBest').checked;

  if (!content.trim()) {
    showToastNotification('回答内容を入力してください', 'warning');
    return;
  }

  // localStorageから相談データを取得
  const consultData = JSON.parse(localStorage.getItem('consultations_details') || '[]');
  const consultIndex = consultData.findIndex(c => c.id === parseInt(consultId));

  if (consultIndex === -1) {
    showToastNotification('相談データが見つかりません', 'error');
    return;
  }

  // 新しい回答オブジェクト
  const newAnswer = {
    id: Date.now(),
    content: content,
    references: references,
    is_best_answer: isBest,
    expert: localStorage.getItem('user_name') || 'エキスパート',
    expert_title: '技術顧問',
    author_name: localStorage.getItem('user_name') || 'エキスパート',
    created_at: new Date().toISOString(),
    helpful_count: 0,
    attachments: []
  };

  // 回答を追加
  if (!consultData[consultIndex].answers) {
    consultData[consultIndex].answers = [];
  }
  consultData[consultIndex].answers.push(newAnswer);

  // ステータスを更新
  if (consultData[consultIndex].status === 'pending') {
    consultData[consultIndex].status = 'answered';
  }

  consultData[consultIndex].updated_at = new Date().toISOString();

  // 保存
  localStorage.setItem('consultations_details', JSON.stringify(consultData));

  // フォームをリセット
  resetAnswerForm();

  // トースト通知
  showToastNotification('回答を投稿しました', 'success');

  // ページをリロード
  setTimeout(() => window.location.reload(), 1000);
}
