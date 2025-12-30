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
  console.log('[FOLLOW] Toggled:', { consultId, isFollowing: newState });
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
 */
function createShareConsultModal() {
  const modalHTML = `
    <div id="shareConsultModal" class="modal" style="display: none;">
      <div class="modal-content">
        <div class="modal-header">
          <h2>相談を共有</h2>
          <button class="modal-close" onclick="closeShareConsultModal()">&times;</button>
        </div>
        <div class="modal-body">
          <div class="field">
            <label>URL</label>
            <input type="text" id="shareConsultUrl" readonly style="background: #f5f5f5;">
            <button class="cta ghost" onclick="copyShareConsultUrl()" style="margin-top: 8px;">📋 URLをコピー</button>
          </div>
          <div class="field" style="margin-top: 20px;">
            <label>共有方法を選択</label>
            <div style="display: grid; gap: 10px; margin-top: 10px;">
              <button class="cta ghost" onclick="shareConsultViaEmail()">📧 メールで共有</button>
              <button class="cta ghost" onclick="shareConsultViaSlack()">💬 Slackで共有</button>
              <button class="cta ghost" onclick="shareConsultViaTeams()">👥 Teamsで共有</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  document.body.insertAdjacentHTML('beforeend', modalHTML);
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
  console.log('[SHARE] Slack share initiated');
}

/**
 * Teamsで共有
 */
function shareConsultViaTeams() {
  showToastNotification('Teams連携機能は準備中です', 'info');
  console.log('[SHARE] Teams share initiated');
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
 */
function createEditConsultModal(consult) {
  const existingModal = document.getElementById('editConsultModal');
  if (existingModal) existingModal.remove();

  const modalHTML = `
    <div id="editConsultModal" class="modal" style="display: flex;">
      <div class="modal-content">
        <div class="modal-header">
          <h2>相談を編集</h2>
          <button class="modal-close" onclick="closeEditConsultModal()">&times;</button>
        </div>
        <div class="modal-body">
          <form id="editConsultForm">
            <div class="field">
              <label>タイトル <span class="required">*</span></label>
              <input type="text" id="editConsultTitle" value="${escapeHtml(consult.title)}" required>
            </div>
            <div class="field">
              <label>カテゴリ <span class="required">*</span></label>
              <select id="editConsultCategory" required>
                <option value="技術相談" ${consult.category === '技術相談' ? 'selected' : ''}>技術相談</option>
                <option value="安全対策" ${consult.category === '安全対策' ? 'selected' : ''}>安全対策</option>
                <option value="品質管理" ${consult.category === '品質管理' ? 'selected' : ''}>品質管理</option>
                <option value="工程計画" ${consult.category === '工程計画' ? 'selected' : ''}>工程計画</option>
                <option value="その他" ${consult.category === 'その他' ? 'selected' : ''}>その他</option>
              </select>
            </div>
            <div class="field">
              <label>優先度 <span class="required">*</span></label>
              <select id="editConsultPriority" required>
                <option value="緊急" ${consult.priority === '緊急' ? 'selected' : ''}>緊急</option>
                <option value="高" ${consult.priority === '高' ? 'selected' : ''}>高</option>
                <option value="通常" ${consult.priority === '通常' ? 'selected' : ''}>通常</option>
                <option value="低" ${consult.priority === '低' ? 'selected' : ''}>低</option>
              </select>
            </div>
            <div class="field">
              <label>相談内容 <span class="required">*</span></label>
              <textarea id="editConsultContent" rows="6" required>${escapeHtml(consult.content)}</textarea>
            </div>
            <div class="modal-actions">
              <button type="button" class="cta ghost" onclick="closeEditConsultModal()">キャンセル</button>
              <button type="submit" class="cta">保存</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `;

  document.body.insertAdjacentHTML('beforeend', modalHTML);

  // フォーム送信イベント
  document.getElementById('editConsultForm').addEventListener('submit', function(e) {
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
 */
function createNewConsultModal() {
  const existingModal = document.getElementById('newConsultModal');
  if (existingModal) existingModal.remove();

  const modalHTML = `
    <div id="newConsultModal" class="modal" style="display: flex;">
      <div class="modal-content">
        <div class="modal-header">
          <h2>新規相談を作成</h2>
          <button class="modal-close" onclick="closeNewConsultModal()">&times;</button>
        </div>
        <div class="modal-body">
          <form id="newConsultForm">
            <div class="field">
              <label>タイトル <span class="required">*</span></label>
              <input type="text" id="newConsultTitle" required placeholder="相談のタイトルを入力してください">
            </div>
            <div class="field">
              <label>カテゴリ <span class="required">*</span></label>
              <select id="newConsultCategory" required>
                <option value="">選択してください</option>
                <option value="技術相談">技術相談</option>
                <option value="安全対策">安全対策</option>
                <option value="品質管理">品質管理</option>
                <option value="工程計画">工程計画</option>
                <option value="その他">その他</option>
              </select>
            </div>
            <div class="field">
              <label>優先度 <span class="required">*</span></label>
              <select id="newConsultPriority" required>
                <option value="通常" selected>通常</option>
                <option value="高">高</option>
                <option value="緊急">緊急</option>
                <option value="低">低</option>
              </select>
            </div>
            <div class="field">
              <label>相談内容 <span class="required">*</span></label>
              <textarea id="newConsultContent" rows="6" required placeholder="詳細な相談内容を入力してください"></textarea>
            </div>
            <div class="field">
              <label>タグ（カンマ区切り）</label>
              <input type="text" id="newConsultTags" placeholder="例: コンクリート, 品質, 養生">
            </div>
            <div class="modal-actions">
              <button type="button" class="cta ghost" onclick="closeNewConsultModal()">キャンセル</button>
              <button type="submit" class="cta">作成</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `;

  document.body.insertAdjacentHTML('beforeend', modalHTML);

  // フォーム送信イベント
  document.getElementById('newConsultForm').addEventListener('submit', function(e) {
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
  console.log('[ANSWER] Best answer selection initiated');
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
