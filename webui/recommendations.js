// ============================================================
// 推薦機能UI - Mirai Knowledge System
// ============================================================

/**
 * 関連ナレッジを新しいAPIエンドポイントから取得して表示
 *
 * @param {number} knowledgeId - ナレッジID
 * @param {string} algorithm - アルゴリズム（tag/category/keyword/hybrid）
 * @param {number} limit - 取得件数
 */
async function loadRelatedKnowledgeFromAPI(knowledgeId, algorithm = 'hybrid', limit = 5) {
  const relatedListEl = document.getElementById('relatedKnowledgeList');
  if (!relatedListEl) return;

  try {
    // APIから関連ナレッジを取得
    const response = await apiCall(
      `/v1/knowledge/${knowledgeId}/related?algorithm=${algorithm}&limit=${limit}`
    );

    if (!response || !response.success) {
      throw new Error('Failed to fetch related knowledge');
    }

    const relatedItems = response.data.related_items || [];

    if (relatedItems.length > 0) {
      // 関連ナレッジカードを生成
      const cards = relatedItems.map(item => createRecommendationCard(item, 'knowledge'));
      setSecureChildren(relatedListEl, cards);
    } else {
      setSecureChildren(relatedListEl, createEmptyMessage('関連ナレッジが見つかりませんでした'));
    }
  } catch (error) {
    logger.error('Failed to load related knowledge from API:', error);
    // フォールバック: 既存のlocalStorage方式を使用
    const tags = getCurrentKnowledgeTags();
    await loadRelatedKnowledge(tags, knowledgeId);
  }
}

/**
 * 関連SOPを新しいAPIエンドポイントから取得して表示
 *
 * @param {number} sopId - SOP ID
 * @param {string} algorithm - アルゴリズム（tag/category/keyword/hybrid）
 * @param {number} limit - 取得件数
 */
async function loadRelatedSOPFromAPI(sopId, algorithm = 'hybrid', limit = 5) {
  const relatedListEl = document.getElementById('relatedSOPList');
  if (!relatedListEl) return;

  try {
    // APIから関連SOPを取得
    const response = await apiCall(
      `/v1/sop/${sopId}/related?algorithm=${algorithm}&limit=${limit}`
    );

    if (!response || !response.success) {
      throw new Error('Failed to fetch related SOP');
    }

    const relatedItems = response.data.related_items || [];

    if (relatedItems.length > 0) {
      // 関連SOPカードを生成
      const cards = relatedItems.map(item => createRecommendationCard(item, 'sop'));
      setSecureChildren(relatedListEl, cards);
    } else {
      setSecureChildren(relatedListEl, createEmptyMessage('関連SOPが見つかりませんでした'));
    }
  } catch (error) {
    logger.error('Failed to load related SOP from API:', error);
    // フォールバック: 既存のlocalStorage方式を使用
    const category = getCurrentSOPCategory();
    await loadRelatedSOP(category, sopId);
  }
}

/**
 * パーソナライズ推薦を取得して表示
 *
 * @param {string} type - 推薦タイプ（knowledge/sop/all）
 * @param {number} limit - 取得件数
 * @param {number} days - 対象期間（日数）
 */
async function loadPersonalizedRecommendations(type = 'all', limit = 5, days = 30) {
  const recContainerEl = document.getElementById('personalizedRecommendations');
  if (!recContainerEl) return;

  try {
    showLoadingInContainer(recContainerEl);

    // APIからパーソナライズ推薦を取得
    const response = await apiCall(
      `/v1/recommendations/personalized?type=${type}&limit=${limit}&days=${days}`
    );

    if (!response || !response.success) {
      throw new Error('Failed to fetch personalized recommendations');
    }

    const data = response.data;
    const sections = [];

    // ナレッジ推薦
    if (data.knowledge && data.knowledge.items.length > 0) {
      const section = createRecommendationSection(
        'あなたへのおすすめナレッジ',
        data.knowledge.items,
        'knowledge'
      );
      sections.push(section);
    }

    // SOP推薦
    if (data.sop && data.sop.items.length > 0) {
      const section = createRecommendationSection(
        'あなたへのおすすめSOP',
        data.sop.items,
        'sop'
      );
      sections.push(section);
    }

    if (sections.length > 0) {
      setSecureChildren(recContainerEl, sections);
    } else {
      setSecureChildren(recContainerEl, createEmptyMessage(
        'まだ推薦がありません。ナレッジやSOPを閲覧すると、パーソナライズされた推薦が表示されます。'
      ));
    }
  } catch (error) {
    logger.error('Failed to load personalized recommendations:', error);
    setSecureChildren(recContainerEl, createErrorMessage(
      'パーソナライズ推薦の読み込みに失敗しました'
    ));
  }
}

/**
 * 推薦カードを生成（XSS対策: DOM API使用）
 *
 * @param {Object} item - アイテムデータ
 * @param {string} type - アイテムタイプ（knowledge/sop）
 * @returns {HTMLElement} - カード要素
 */
function createRecommendationCard(item, type) {
  const card = document.createElement('div');
  card.className = 'recommendation-card';

  // リンク先を決定
  const linkUrl = type === 'knowledge'
    ? `search-detail.html?id=${encodeURIComponent(item.id)}`
    : `sop-detail.html?id=${encodeURIComponent(item.id)}`;

  // リンク要素を作成
  const link = document.createElement('a');
  link.href = linkUrl;
  link.className = 'rec-card-link';

  // ヘッダー
  const header = document.createElement('div');
  header.className = 'rec-card-header';

  const title = document.createElement('h4');
  title.className = 'rec-card-title';
  title.textContent = item.title || 'タイトルなし';
  header.appendChild(title);

  // スコアバッジ
  if (item.recommendation_score) {
    const scoreBadge = document.createElement('span');
    scoreBadge.className = 'rec-score';
    scoreBadge.title = '推薦スコア';
    scoreBadge.textContent = `${(item.recommendation_score * 100).toFixed(0)}%`;
    header.appendChild(scoreBadge);
  }

  link.appendChild(header);

  // サマリー
  const summary = document.createElement('p');
  summary.className = 'rec-card-summary';
  const summaryText = (item.summary || item.content || '').substring(0, 80);
  summary.textContent = summaryText + (summaryText.length >= 80 ? '...' : '');
  link.appendChild(summary);

  // 推薦理由バッジ
  const reasons = item.recommendation_reasons || [];
  if (reasons.length > 0) {
    const reasonsDiv = document.createElement('div');
    reasonsDiv.className = 'rec-reasons';
    reasons.forEach(reason => {
      const badge = document.createElement('span');
      badge.className = 'rec-reason';
      badge.textContent = reason;
      reasonsDiv.appendChild(badge);
    });
    link.appendChild(reasonsDiv);
  }

  // タグ表示
  const tags = (item.tags || []).slice(0, 3);
  if (tags.length > 0) {
    const tagsDiv = document.createElement('div');
    tagsDiv.className = 'rec-tags';
    tags.forEach(tag => {
      const tagSpan = document.createElement('span');
      tagSpan.className = 'tag';
      tagSpan.textContent = tag;
      tagsDiv.appendChild(tagSpan);
    });
    link.appendChild(tagsDiv);
  }

  card.appendChild(link);
  return card;
}

/**
 * 推薦セクションを生成
 *
 * @param {string} title - セクションタイトル
 * @param {Array} items - アイテムリスト
 * @param {string} type - アイテムタイプ（knowledge/sop）
 * @returns {HTMLElement} - セクション要素
 */
function createRecommendationSection(title, items, type) {
  const section = document.createElement('div');
  section.className = 'recommendation-section';

  const sectionHeader = document.createElement('h3');
  sectionHeader.className = 'rec-section-title';
  sectionHeader.textContent = title;

  const cardContainer = document.createElement('div');
  cardContainer.className = 'rec-card-container';

  const cards = items.map(item => createRecommendationCard(item, type));
  setSecureChildren(cardContainer, cards);

  section.appendChild(sectionHeader);
  section.appendChild(cardContainer);

  return section;
}

/**
 * コンテナ内にローディング表示（XSS対策: DOM API使用）
 *
 * @param {HTMLElement} container - コンテナ要素
 */
function showLoadingInContainer(container) {
  const loading = document.createElement('div');
  loading.className = 'loading-container';

  const spinner = document.createElement('div');
  spinner.className = 'spinner';

  const text = document.createElement('p');
  text.textContent = '読み込み中...';

  loading.appendChild(spinner);
  loading.appendChild(text);
  setSecureChildren(container, [loading]);
}

/**
 * 現在のナレッジのタグを取得（ヘルパー関数）
 *
 * @returns {Array} - タグリスト
 */
function getCurrentKnowledgeTags() {
  const tagsEl = document.getElementById('knowledgeTags');
  if (!tagsEl) return [];

  const tagElements = tagsEl.querySelectorAll('.tag');
  return Array.from(tagElements).map(el => el.textContent);
}

/**
 * 現在のSOPのカテゴリを取得（ヘルパー関数）
 *
 * @returns {string} - カテゴリ
 */
function getCurrentSOPCategory() {
  const categoryEl = document.getElementById('sopCategory');
  if (!categoryEl) return '';

  return categoryEl.textContent;
}

/**
 * アルゴリズム選択UIを追加（XSS対策: DOM API使用）
 *
 * @param {string} containerId - コンテナID
 * @param {Function} onChangeCallback - 変更時のコールバック
 */
function addAlgorithmSelector(containerId, onChangeCallback) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const selector = document.createElement('div');
  selector.className = 'algorithm-selector';

  const label = document.createElement('label');
  label.setAttribute('for', 'recAlgorithm');
  label.textContent = '推薦アルゴリズム:';

  const select = document.createElement('select');
  select.id = 'recAlgorithm';
  select.className = 'algorithm-select';

  const options = [
    { value: 'hybrid', text: 'ハイブリッド（推奨）' },
    { value: 'tag', text: 'タグ類似度' },
    { value: 'category', text: 'カテゴリマッチ' },
    { value: 'keyword', text: 'キーワード類似度' }
  ];

  options.forEach(opt => {
    const option = document.createElement('option');
    option.value = opt.value;
    option.textContent = opt.text;
    select.appendChild(option);
  });

  select.addEventListener('change', (e) => {
    if (onChangeCallback) {
      onChangeCallback(e.target.value);
    }
  });

  selector.appendChild(label);
  selector.appendChild(select);
  container.insertBefore(selector, container.firstChild);
}

/**
 * 推薦詳細情報を表示するモーダル（XSS対策: DOM API使用）
 *
 * @param {Object} item - アイテムデータ
 */
function showRecommendationDetails(item) {
  const modal = document.createElement('div');
  modal.className = 'rec-details-modal';

  // オーバーレイ
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.addEventListener('click', () => modal.remove());

  // コンテンツ
  const content = document.createElement('div');
  content.className = 'modal-content';

  // ヘッダー
  const header = document.createElement('div');
  header.className = 'modal-header';

  const headerTitle = document.createElement('h3');
  headerTitle.textContent = '推薦の詳細情報';

  const closeBtn = document.createElement('button');
  closeBtn.className = 'close-btn';
  closeBtn.textContent = '×';
  closeBtn.addEventListener('click', () => modal.remove());

  header.appendChild(headerTitle);
  header.appendChild(closeBtn);

  // ボディ
  const body = document.createElement('div');
  body.className = 'modal-body';

  const itemTitle = document.createElement('h4');
  itemTitle.textContent = item.title || '';
  body.appendChild(itemTitle);

  const scoreP = document.createElement('p');
  const scoreLabel = document.createElement('strong');
  scoreLabel.textContent = '推薦スコア: ';
  scoreP.appendChild(scoreLabel);
  scoreP.appendChild(document.createTextNode(`${(item.recommendation_score * 100).toFixed(1)}%`));
  body.appendChild(scoreP);

  const reasonLabel = document.createElement('p');
  const reasonStrong = document.createElement('strong');
  reasonStrong.textContent = '推薦理由:';
  reasonLabel.appendChild(reasonStrong);
  body.appendChild(reasonLabel);

  const reasonList = document.createElement('ul');
  (item.recommendation_reasons || []).forEach(reason => {
    const li = document.createElement('li');
    li.textContent = reason;
    reasonList.appendChild(li);
  });
  body.appendChild(reasonList);

  // 共通キーワード
  if (item.recommendation_details && item.recommendation_details.common_keywords) {
    const keywordP = document.createElement('p');
    const keywordLabel = document.createElement('strong');
    keywordLabel.textContent = '共通キーワード: ';
    keywordP.appendChild(keywordLabel);
    keywordP.appendChild(document.createTextNode(item.recommendation_details.common_keywords.join(', ')));
    body.appendChild(keywordP);
  }

  content.appendChild(header);
  content.appendChild(body);
  modal.appendChild(overlay);
  modal.appendChild(content);

  document.body.appendChild(modal);
}

// ============================================================
// ダッシュボード用推薦ウィジェット
// ============================================================

/**
 * ダッシュボードに推薦ウィジェットを追加
 */
async function initializeDashboardRecommendations() {
  const widgetContainer = document.getElementById('recommendationsWidget');
  if (!widgetContainer) return;

  try {
    // パーソナライズ推薦を取得
    const response = await apiCall('/v1/recommendations/personalized?type=all&limit=3');

    if (!response || !response.success) {
      throw new Error('Failed to fetch recommendations');
    }

    const data = response.data;
    const allItems = [];

    // ナレッジとSOPを統合
    if (data.knowledge && data.knowledge.items) {
      allItems.push(...data.knowledge.items.map(item => ({ ...item, type: 'knowledge' })));
    }
    if (data.sop && data.sop.items) {
      allItems.push(...data.sop.items.map(item => ({ ...item, type: 'sop' })));
    }

    // スコア順にソート
    allItems.sort((a, b) => (b.recommendation_score || 0) - (a.recommendation_score || 0));

    // 上位3件を表示
    const topItems = allItems.slice(0, 3);

    if (topItems.length > 0) {
      const cards = topItems.map(item => createCompactRecommendationCard(item));
      setSecureChildren(widgetContainer, cards);
    } else {
      setSecureChildren(widgetContainer, createEmptyMessage('推薦がありません'));
    }
  } catch (error) {
    logger.error('Failed to initialize dashboard recommendations:', error);
    setSecureChildren(widgetContainer, createErrorMessage('推薦の読み込みに失敗しました'));
  }
}

/**
 * コンパクトな推薦カードを生成（ダッシュボード用）（XSS対策: DOM API使用）
 *
 * @param {Object} item - アイテムデータ
 * @returns {HTMLElement} - カード要素
 */
function createCompactRecommendationCard(item) {
  const card = document.createElement('div');
  card.className = 'compact-rec-card';

  const linkUrl = item.type === 'knowledge'
    ? `search-detail.html?id=${encodeURIComponent(item.id)}`
    : `sop-detail.html?id=${encodeURIComponent(item.id)}`;

  const link = document.createElement('a');
  link.href = linkUrl;
  link.className = 'compact-rec-link';

  // ヘッダー
  const header = document.createElement('div');
  header.className = 'compact-rec-header';

  const typeBadge = document.createElement('span');
  typeBadge.className = 'compact-type-badge';
  typeBadge.textContent = item.type === 'knowledge' ? 'ナレッジ' : 'SOP';
  header.appendChild(typeBadge);

  if (item.recommendation_score) {
    const score = document.createElement('span');
    score.className = 'compact-score';
    score.textContent = `${(item.recommendation_score * 100).toFixed(0)}%`;
    header.appendChild(score);
  }

  link.appendChild(header);

  // タイトル
  const title = document.createElement('h5');
  title.className = 'compact-rec-title';
  title.textContent = item.title || 'タイトルなし';
  link.appendChild(title);

  // 推薦理由
  const reason = document.createElement('p');
  reason.className = 'compact-rec-reason';
  reason.textContent = (item.recommendation_reasons || [])[0] || '';
  link.appendChild(reason);

  card.appendChild(link);
  return card;
}

// ============================================================
// CSS スタイル（動的追加）
// ============================================================

function injectRecommendationStyles() {
  const styleId = 'recommendation-styles';

  // 既に追加済みの場合はスキップ
  if (document.getElementById(styleId)) return;

  const style = document.createElement('style');
  style.id = styleId;
  style.textContent = `
    /* 推薦カード */
    .recommendation-card {
      background: white;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 12px;
      transition: all 0.2s ease;
    }

    .recommendation-card:hover {
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      transform: translateY(-2px);
    }

    .rec-card-link {
      text-decoration: none;
      color: inherit;
      display: block;
    }

    .rec-card-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 8px;
    }

    .rec-card-title {
      margin: 0;
      font-size: 16px;
      color: #1976d2;
      flex: 1;
    }

    .rec-score {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 4px 10px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: bold;
      margin-left: 8px;
      white-space: nowrap;
    }

    .rec-card-summary {
      color: #666;
      font-size: 14px;
      margin: 8px 0;
      line-height: 1.5;
    }

    .rec-reasons {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin: 8px 0;
    }

    .rec-reason {
      background: #e3f2fd;
      color: #1976d2;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 12px;
    }

    .rec-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 8px;
    }

    .rec-tags .tag {
      background: #f5f5f5;
      color: #666;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 12px;
    }

    /* 推薦セクション */
    .recommendation-section {
      margin-bottom: 32px;
    }

    .rec-section-title {
      font-size: 20px;
      margin-bottom: 16px;
      color: #333;
      border-left: 4px solid #1976d2;
      padding-left: 12px;
    }

    .rec-card-container {
      display: grid;
      gap: 12px;
    }

    /* アルゴリズム選択 */
    .algorithm-selector {
      margin-bottom: 16px;
      padding: 12px;
      background: #f9f9f9;
      border-radius: 6px;
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .algorithm-selector label {
      font-weight: 500;
      color: #555;
    }

    .algorithm-select {
      padding: 6px 12px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 14px;
      background: white;
      cursor: pointer;
    }

    /* コンパクトカード（ダッシュボード用） */
    .compact-rec-card {
      background: white;
      border: 1px solid #e0e0e0;
      border-radius: 6px;
      padding: 12px;
      margin-bottom: 8px;
      transition: all 0.2s ease;
    }

    .compact-rec-card:hover {
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }

    .compact-rec-link {
      text-decoration: none;
      color: inherit;
      display: block;
    }

    .compact-rec-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
    }

    .compact-type-badge {
      background: #1976d2;
      color: white;
      padding: 2px 8px;
      border-radius: 3px;
      font-size: 11px;
      font-weight: bold;
    }

    .compact-score {
      color: #667eea;
      font-size: 12px;
      font-weight: bold;
    }

    .compact-rec-title {
      margin: 0 0 4px 0;
      font-size: 14px;
      color: #333;
      font-weight: 500;
    }

    .compact-rec-reason {
      margin: 0;
      font-size: 12px;
      color: #666;
    }

    /* モーダル */
    .rec-details-modal {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      z-index: 10000;
    }

    .modal-overlay {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.5);
    }

    .modal-content {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background: white;
      border-radius: 8px;
      padding: 24px;
      max-width: 500px;
      width: 90%;
      max-height: 80vh;
      overflow-y: auto;
    }

    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid #e0e0e0;
    }

    .modal-header h3 {
      margin: 0;
      font-size: 18px;
    }

    .close-btn {
      background: none;
      border: none;
      font-size: 24px;
      cursor: pointer;
      color: #999;
      padding: 0;
      width: 30px;
      height: 30px;
      line-height: 30px;
      text-align: center;
    }

    .close-btn:hover {
      color: #333;
    }

    .modal-body ul {
      margin: 8px 0;
      padding-left: 20px;
    }

    .loading-container {
      text-align: center;
      padding: 32px;
      color: #999;
    }

    .spinner {
      border: 3px solid #f3f3f3;
      border-top: 3px solid #1976d2;
      border-radius: 50%;
      width: 40px;
      height: 40px;
      animation: spin 1s linear infinite;
      margin: 0 auto 16px;
    }

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }

    @media (max-width: 768px) {
      .rec-card-header {
        flex-direction: column;
      }

      .rec-score {
        margin-left: 0;
        margin-top: 8px;
        align-self: flex-start;
      }
    }
  `;

  document.head.appendChild(style);
}

// ページ読み込み時にスタイルを注入
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', injectRecommendationStyles);
} else {
  injectRecommendationStyles();
}
