/**
 * Mirai Knowledge System API - JavaScript使用例
 *
 * このスクリプトは、Node.js環境でのMKS APIの基本的な使用方法を示します。
 *
 * 必要なパッケージ:
 *   npm install axios
 */

const axios = require('axios');

class MKSAPIClient {
  /**
   * @param {string} baseURL - APIのベースURL
   */
  constructor(baseURL = 'http://localhost:5100') {
    this.baseURL = baseURL;
    this.accessToken = null;
    this.refreshToken = null;

    // Axiosインスタンスを作成
    this.client = axios.create({
      baseURL: this.baseURL,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // リクエストインターセプター（トークン自動付与）
    this.client.interceptors.request.use(
      config => {
        if (this.accessToken) {
          config.headers.Authorization = `Bearer ${this.accessToken}`;
        }
        return config;
      },
      error => Promise.reject(error)
    );

    // レスポンスインターセプター（トークンリフレッシュ）
    this.client.interceptors.response.use(
      response => response,
      async error => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            await this.refreshAccessToken();
            originalRequest.headers.Authorization = `Bearer ${this.accessToken}`;
            return this.client(originalRequest);
          } catch (refreshError) {
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  /**
   * ログイン
   * @param {string} username - ユーザー名
   * @param {string} password - パスワード
   * @returns {Promise<Object>} ユーザー情報
   */
  async login(username, password) {
    const response = await this.client.post('/api/v1/auth/login', {
      username,
      password
    });

    const { data } = response.data;
    this.accessToken = data.access_token;
    this.refreshToken = data.refresh_token;

    return data.user;
  }

  /**
   * トークンリフレッシュ
   */
  async refreshAccessToken() {
    const response = await axios.post(
      `${this.baseURL}/api/v1/auth/refresh`,
      {},
      {
        headers: {
          Authorization: `Bearer ${this.refreshToken}`
        }
      }
    );

    const { data } = response.data;
    this.accessToken = data.access_token;
  }

  /**
   * 現在のユーザー情報を取得
   * @returns {Promise<Object>} ユーザー情報
   */
  async getCurrentUser() {
    const response = await this.client.get('/api/v1/auth/me');
    return response.data.data;
  }

  // ============================================================
  // ナレッジ管理
  // ============================================================

  /**
   * ナレッジ一覧を取得
   * @param {Object} filters - フィルタ条件
   * @returns {Promise<Array>} ナレッジのリスト
   */
  async listKnowledge(filters = {}) {
    const response = await this.client.get('/api/v1/knowledge', {
      params: filters
    });
    return response.data.data;
  }

  /**
   * ナレッジ詳細を取得
   * @param {number} id - ナレッジID
   * @returns {Promise<Object>} ナレッジ詳細
   */
  async getKnowledge(id) {
    const response = await this.client.get(`/api/v1/knowledge/${id}`);
    return response.data.data;
  }

  /**
   * 新規ナレッジを作成
   * @param {Object} knowledgeData - ナレッジデータ
   * @returns {Promise<Object>} 作成されたナレッジ
   */
  async createKnowledge(knowledgeData) {
    const response = await this.client.post('/api/v1/knowledge', knowledgeData);
    return response.data.data;
  }

  // ============================================================
  // 横断検索
  // ============================================================

  /**
   * 横断検索を実行
   * @param {string} query - 検索クエリ
   * @param {Object} options - オプション
   * @returns {Promise<Object>} 検索結果
   */
  async unifiedSearch(query, options = {}) {
    const params = {
      q: query,
      types: options.types || 'knowledge,sop,incidents',
      highlight: options.highlight !== false ? 'true' : 'false'
    };

    const response = await this.client.get('/api/v1/search/unified', { params });
    return response.data;
  }

  // ============================================================
  // 通知管理
  // ============================================================

  /**
   * 通知一覧を取得
   * @returns {Promise<Array>} 通知のリスト
   */
  async listNotifications() {
    const response = await this.client.get('/api/v1/notifications');
    return response.data.data;
  }

  /**
   * 通知を既読にする
   * @param {number} notificationId - 通知ID
   */
  async markNotificationRead(notificationId) {
    await this.client.put(`/api/v1/notifications/${notificationId}/read`);
  }

  /**
   * 未読通知数を取得
   * @returns {Promise<number>} 未読通知数
   */
  async getUnreadCount() {
    const response = await this.client.get('/api/v1/notifications/unread/count');
    return response.data.data.unread_count;
  }

  // ============================================================
  // ダッシュボード
  // ============================================================

  /**
   * ダッシュボード統計を取得
   * @returns {Promise<Object>} 統計データ
   */
  async getDashboardStats() {
    const response = await this.client.get('/api/v1/dashboard/stats');
    return response.data.data;
  }
}

// ============================================================
// 使用例
// ============================================================

async function main() {
  const client = new MKSAPIClient('http://localhost:5100');

  try {
    // 1. ログイン
    console.log('=== ログイン ===');
    const user = await client.login('admin', 'admin123');
    console.log(`ログインユーザー: ${user.full_name} (${user.username})`);
    console.log(`ロール: ${user.roles.join(', ')}`);
    console.log();

    // 2. ナレッジ一覧取得
    console.log('=== ナレッジ一覧取得 ===');
    const allKnowledge = await client.listKnowledge();
    console.log(`総ナレッジ数: ${allKnowledge.length}`);
    console.log();

    // 3. カテゴリでフィルタ
    console.log('=== 品質管理カテゴリのナレッジ ===');
    const qualityKnowledge = await client.listKnowledge({ category: '品質管理' });
    console.log(`品質管理ナレッジ数: ${qualityKnowledge.length}`);
    qualityKnowledge.slice(0, 3).forEach(k => {
      console.log(`  - ${k.title}`);
    });
    console.log();

    // 4. 検索
    console.log('=== キーワード検索 ===');
    const searchResults = await client.listKnowledge({ search: 'コンクリート' });
    console.log(`「コンクリート」の検索結果: ${searchResults.length}件`);
    searchResults.slice(0, 3).forEach(k => {
      console.log(`  - ${k.title}`);
    });
    console.log();

    // 5. 新規ナレッジ作成
    console.log('=== 新規ナレッジ作成 ===');
    const newKnowledge = await client.createKnowledge({
      title: '鉄筋配筋検査のチェックポイント',
      summary: '配筋検査における重要確認項目',
      content: `
## 配筋検査の目的
- 設計図書との整合性確認
- 施工精度の確認
- 構造安全性の確保

## 主要チェック項目
1. 鉄筋径・鉄筋種別の確認
2. 配筋間隔の確認
3. かぶり厚さの確認
4. 定着長・継手長の確認
5. スペーサーの配置確認
      `,
      category: '品質管理',
      tags: ['鉄筋工事', '配筋検査', '品質管理'],
      priority: 'high',
      owner: '山田太郎',
      project: '東京タワー建設プロジェクト'
    });
    console.log(`作成されたナレッジID: ${newKnowledge.id}`);
    console.log(`タイトル: ${newKnowledge.title}`);
    console.log();

    // 6. 横断検索
    console.log('=== 横断検索 ===');
    const unifiedResults = await client.unifiedSearch('基礎工事', {
      types: 'knowledge,sop'
    });
    console.log(`検索クエリ: ${unifiedResults.query}`);
    console.log(`総検索結果数: ${unifiedResults.total_results}`);
    console.log();

    if (unifiedResults.data.knowledge) {
      const knowledgeResults = unifiedResults.data.knowledge;
      console.log(`ナレッジ検索結果: ${knowledgeResults.count}件`);
      knowledgeResults.items.slice(0, 3).forEach(item => {
        const score = item.relevance_score || 0;
        console.log(`  - ${item.title} (スコア: ${score.toFixed(2)})`);
      });
    }
    console.log();

    // 7. 通知一覧取得
    console.log('=== 通知一覧 ===');
    const notifications = await client.listNotifications();
    const unreadCount = await client.getUnreadCount();
    console.log(`総通知数: ${notifications.length}`);
    console.log(`未読通知数: ${unreadCount}`);

    if (notifications.length > 0) {
      console.log('最新の通知:');
      notifications.slice(0, 3).forEach(notif => {
        const status = notif.is_read ? '既読' : '未読';
        console.log(`  [${status}] ${notif.title}`);
      });
    }
    console.log();

    // 8. ダッシュボード統計
    console.log('=== ダッシュボード統計 ===');
    const stats = await client.getDashboardStats();

    console.log('KPI:');
    Object.entries(stats.kpis || {}).forEach(([key, value]) => {
      console.log(`  ${key}: ${value}`);
    });

    console.log('\nカウント:');
    Object.entries(stats.counts || {}).forEach(([key, value]) => {
      console.log(`  ${key}: ${value}`);
    });

  } catch (error) {
    if (error.response) {
      // APIエラーレスポンス
      console.error('APIエラー:', error.response.data);
      console.error('ステータスコード:', error.response.status);
    } else if (error.request) {
      // リクエストは送信されたがレスポンスなし
      console.error('リクエストエラー:', error.message);
    } else {
      // その他のエラー
      console.error('エラー:', error.message);
    }
  }
}

// スクリプト実行
if (require.main === module) {
  main();
}

module.exports = MKSAPIClient;
