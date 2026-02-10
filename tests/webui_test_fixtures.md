# WebUIテスト用Fixtureデータ定義

## 概要

WebUIテストで使用するテストデータの定義と準備方法を記載します。

---

## 1. ユーザーアカウント

### 1.1 テストユーザー一覧

```javascript
// backend/tests/fixtures/users.js
const TEST_USERS = {
  admin_no_mfa: {
    id: 1,
    email: 'admin@example.com',
    password: 'Admin1234!',
    role: 'admin',
    status: 'active',
    mfa_enabled: false,
    permissions: ['*']
  },

  admin_with_mfa: {
    id: 2,
    email: 'admin_mfa@example.com',
    password: 'AdminMFA1234!',
    role: 'admin',
    status: 'active',
    mfa_enabled: true,
    totp_secret: 'JBSWY3DPEHPK3PXP',
    backup_codes: [
      'AAAA-1111-BBBB',
      'CCCC-2222-DDDD',
      'EEEE-3333-FFFF',
      'GGGG-4444-HHHH',
      'IIII-5555-JJJJ',
      'KKKK-6666-LLLL',
      'MMMM-7777-NNNN',
      'OOOO-8888-PPPP',
      'QQQQ-9999-RRRR',
      'SSSS-0000-TTTT'
    ],
    permissions: ['*']
  },

  editor: {
    id: 3,
    email: 'editor@example.com',
    password: 'Editor1234!',
    role: 'editor',
    status: 'active',
    mfa_enabled: false,
    permissions: [
      'knowledge.read',
      'knowledge.create',
      'knowledge.update',
      'notification.read',
      'notification.update'
    ]
  },

  viewer: {
    id: 4,
    email: 'viewer@example.com',
    password: 'Viewer1234!',
    role: 'viewer',
    status: 'active',
    mfa_enabled: false,
    permissions: [
      'knowledge.read',
      'notification.read'
    ]
  },

  suspended: {
    id: 5,
    email: 'suspended@example.com',
    password: 'Suspended1234!',
    role: 'viewer',
    status: 'suspended',
    mfa_enabled: false,
    permissions: []
  },

  expired_token: {
    id: 6,
    email: 'expired@example.com',
    password: 'Expired1234!',
    role: 'viewer',
    status: 'active',
    mfa_enabled: false,
    token_expires_at: '2024-01-01T00:00:00Z',
    permissions: ['knowledge.read']
  }
};

module.exports = { TEST_USERS };
```

### 1.2 パスワード要件

- 最小長: 8文字
- 最大長: 128文字
- 必須要素:
  - 大文字（A-Z）: 1文字以上
  - 小文字（a-z）: 1文字以上
  - 数字（0-9）: 1文字以上
  - 特殊文字（!@#$%^&*）: 1文字以上

---

## 2. ナレッジデータ

### 2.1 基本ナレッジ（20件）

```javascript
// backend/tests/fixtures/knowledge.js
const KNOWLEDGE_DATA = [
  {
    id: 1,
    title: '土木工事における安全管理の基本',
    category: 'safety',
    status: 'approved',
    content: '安全管理の基本的な考え方とチェックリスト...',
    tags: ['安全', '土木', '管理'],
    author_id: 1,
    created_at: '2026-01-01T09:00:00Z',
    updated_at: '2026-01-15T14:30:00Z',
    attachments: [
      {
        id: 101,
        filename: 'safety_checklist.pdf',
        size: 1024000,
        mime_type: 'application/pdf'
      }
    ]
  },

  {
    id: 2,
    title: '建設現場でのクレーン操作手順',
    category: 'technical',
    status: 'approved',
    content: 'クレーン操作の詳細手順とトラブルシューティング...',
    tags: ['技術', 'クレーン', '操作'],
    author_id: 3,
    created_at: '2026-01-10T10:00:00Z',
    updated_at: '2026-01-20T11:00:00Z',
    attachments: []
  },

  {
    id: 3,
    title: '労働安全衛生法の最新改正内容',
    category: 'legal',
    status: 'approved',
    content: '2026年1月施行の労働安全衛生法改正のポイント...',
    tags: ['法規', '労働安全衛生法'],
    author_id: 1,
    created_at: '2026-01-05T13:00:00Z',
    updated_at: '2026-01-05T13:00:00Z',
    attachments: [
      {
        id: 102,
        filename: 'law_amendment_2026.pdf',
        size: 2048000,
        mime_type: 'application/pdf'
      }
    ]
  },

  // ... 計20件のナレッジデータ
];

// カテゴリ別内訳
// - technical（技術）: 8件
// - safety（安全）: 6件
// - legal（法規）: 6件

// ステータス別内訳
// - approved（承認済み）: 15件
// - pending（承認待ち）: 3件
// - draft（下書き）: 2件

module.exports = { KNOWLEDGE_DATA };
```

---

## 3. 通知データ

### 3.1 通知タイプ定義

```javascript
// backend/tests/fixtures/notifications.js
const NOTIFICATION_TYPES = {
  APPROVAL_REQUIRED: 'approval_required',
  APPROVAL_COMPLETED: 'approval_completed',
  INCIDENT_REPORTED: 'incident_reported',
  CONSULTATION_ANSWERED: 'consultation_answered',
  KNOWLEDGE_UPDATED: 'knowledge_updated',
  COMMENT_ADDED: 'comment_added'
};

const NOTIFICATION_DATA = [
  {
    id: 1,
    user_id: 1,
    type: NOTIFICATION_TYPES.APPROVAL_REQUIRED,
    title: '承認依頼: クレーン操作手順',
    message: '新規ナレッジ「クレーン操作手順」の承認をお願いします。',
    link: '/knowledge/2',
    is_read: false,
    created_at: '2026-02-10T09:00:00Z'
  },

  {
    id: 2,
    user_id: 1,
    type: NOTIFICATION_TYPES.INCIDENT_REPORTED,
    title: '事故報告: 現場Aで軽傷事故',
    message: '現場Aで軽傷事故が報告されました。詳細を確認してください。',
    link: '/incidents/5',
    is_read: false,
    created_at: '2026-02-10T08:30:00Z'
  },

  {
    id: 3,
    user_id: 1,
    type: NOTIFICATION_TYPES.CONSULTATION_ANSWERED,
    title: '相談回答: 安全管理について',
    message: '安全管理に関する相談に回答がありました。',
    link: '/consultations/12',
    is_read: true,
    created_at: '2026-02-09T15:00:00Z'
  },

  // ... 計30件の通知データ
];

// タイプ別内訳
// - approval_required: 10件
// - approval_completed: 8件
// - incident_reported: 7件
// - consultation_answered: 5件

// ステータス別内訳
// - is_read: false（未読）: 20件
// - is_read: true（既読）: 10件

module.exports = { NOTIFICATION_TYPES, NOTIFICATION_DATA };
```

---

## 4. MS365同期設定

### 4.1 同期設定データ

```javascript
// backend/tests/fixtures/ms365_configs.js
const MS365_SYNC_CONFIGS = [
  {
    id: 1,
    user_id: 1,
    name: 'OneDrive 定期同期',
    source_type: 'onedrive',
    source_path: '/Documents/建設現場資料',
    schedule: '0 */1 * * *', // 1時間ごと
    is_enabled: true,
    last_sync_at: '2026-02-10T09:00:00Z',
    last_sync_status: 'success',
    created_at: '2026-01-01T00:00:00Z'
  },

  {
    id: 2,
    user_id: 1,
    name: 'SharePoint 手動同期',
    source_type: 'sharepoint',
    source_path: '/sites/ConstructionDocs/Shared Documents',
    schedule: null, // 手動同期
    is_enabled: false,
    last_sync_at: '2026-02-09T18:00:00Z',
    last_sync_status: 'success',
    created_at: '2026-01-15T00:00:00Z'
  },

  {
    id: 3,
    user_id: 1,
    name: 'OneDrive エラー状態',
    source_type: 'onedrive',
    source_path: '/Documents/古いフォルダ',
    schedule: '0 0 * * *', // 毎日0時
    is_enabled: true,
    last_sync_at: '2026-02-10T00:00:00Z',
    last_sync_status: 'error',
    last_sync_error: 'フォルダが見つかりません',
    created_at: '2026-02-01T00:00:00Z'
  },

  {
    id: 4,
    user_id: 1,
    name: 'SharePoint 大量ファイル',
    source_type: 'sharepoint',
    source_path: '/sites/Archive/Documents',
    schedule: '0 0 * * 0', // 毎週日曜0時
    is_enabled: true,
    last_sync_at: '2026-02-04T00:00:00Z',
    last_sync_status: 'success',
    last_sync_files_count: 1000,
    created_at: '2026-01-20T00:00:00Z'
  },

  {
    id: 5,
    user_id: 1,
    name: 'OneDrive 空フォルダ',
    source_type: 'onedrive',
    source_path: '/Documents/空フォルダ',
    schedule: '0 12 * * *', // 毎日12時
    is_enabled: true,
    last_sync_at: '2026-02-10T12:00:00Z',
    last_sync_status: 'success',
    last_sync_files_count: 0,
    created_at: '2026-02-05T00:00:00Z'
  }
];

module.exports = { MS365_SYNC_CONFIGS };
```

### 4.2 同期履歴データ

```javascript
// backend/tests/fixtures/ms365_history.js
const MS365_SYNC_HISTORY = [
  {
    id: 1,
    config_id: 1,
    status: 'success',
    files_synced: 15,
    files_skipped: 3,
    files_failed: 0,
    started_at: '2026-02-10T09:00:00Z',
    completed_at: '2026-02-10T09:02:30Z',
    duration_seconds: 150,
    error_message: null
  },

  {
    id: 2,
    config_id: 1,
    status: 'success',
    files_synced: 8,
    files_skipped: 10,
    files_failed: 0,
    started_at: '2026-02-10T08:00:00Z',
    completed_at: '2026-02-10T08:01:45Z',
    duration_seconds: 105,
    error_message: null
  },

  {
    id: 3,
    config_id: 3,
    status: 'error',
    files_synced: 0,
    files_skipped: 0,
    files_failed: 0,
    started_at: '2026-02-10T00:00:00Z',
    completed_at: '2026-02-10T00:00:05Z',
    duration_seconds: 5,
    error_message: 'フォルダが見つかりません: /Documents/古いフォルダ'
  },

  // ... 計100件の同期履歴
];

module.exports = { MS365_SYNC_HISTORY };
```

---

## 5. PWAテストデータ

### 5.1 キャッシュデータ

```javascript
// backend/tests/fixtures/pwa_cache.js
const PWA_CACHE_DATA = {
  static: [
    '/',
    '/index.html',
    '/login.html',
    '/offline.html',
    '/app.js',
    '/styles.css',
    '/manifest.json',
    '/icons/icon-192x192.png',
    '/icons/icon-512x512.png'
  ],

  api: [
    { url: '/api/knowledge?page=1', response: { /* ... */ }, maxAge: 3600000 }, // 1時間
    { url: '/api/knowledge/1', response: { /* ... */ }, maxAge: 86400000 }, // 24時間
    { url: '/api/notifications/unread/count', response: { count: 5 }, maxAge: 300000 } // 5分
  ]
};

module.exports = { PWA_CACHE_DATA };
```

### 5.2 IndexedDBデータ

```javascript
// backend/tests/fixtures/pwa_indexeddb.js
const INDEXEDDB_STORES = {
  'sync-queue': [
    {
      id: 1,
      type: 'knowledge_create',
      data: { title: 'オフライン作成ナレッジ', content: '...' },
      timestamp: Date.now() - 60000, // 1分前
      retryCount: 0
    },
    {
      id: 2,
      type: 'notification_read',
      data: { notification_id: 10 },
      timestamp: Date.now() - 30000, // 30秒前
      retryCount: 1
    }
  ],

  'tokens': [
    {
      key: 'access_token',
      encrypted: 'encrypted_token_data',
      iv: 'initialization_vector',
      expires_at: Date.now() + 86400000 // 24時間後
    }
  ],

  'cache-metadata': [
    {
      url: '/api/knowledge/1',
      size: 5120,
      cachedAt: Date.now() - 3600000, // 1時間前
      expiresAt: Date.now() + 82800000 // 23時間後
    }
  ]
};

module.exports = { INDEXEDDB_STORES };
```

---

## 6. テストデータ準備スクリプト

### 6.1 一括準備スクリプト

```javascript
// backend/tests/fixtures/setup.js
const { TEST_USERS } = require('./users');
const { KNOWLEDGE_DATA } = require('./knowledge');
const { NOTIFICATION_DATA } = require('./notifications');
const { MS365_SYNC_CONFIGS } = require('./ms365_configs');

async function setupTestData() {
  // ユーザー作成
  for (const user of Object.values(TEST_USERS)) {
    await createUser(user);
  }

  // ナレッジ作成
  for (const knowledge of KNOWLEDGE_DATA) {
    await createKnowledge(knowledge);
  }

  // 通知作成
  for (const notification of NOTIFICATION_DATA) {
    await createNotification(notification);
  }

  // MS365同期設定作成
  for (const config of MS365_SYNC_CONFIGS) {
    await createMS365Config(config);
  }

  console.log('✅ テストデータ準備完了');
}

async function teardownTestData() {
  // 全テストデータ削除
  await deleteAllNotifications();
  await deleteAllMS365Configs();
  await deleteAllKnowledge();
  await deleteAllUsers();

  console.log('✅ テストデータクリーンアップ完了');
}

module.exports = { setupTestData, teardownTestData };
```

### 6.2 Playwright Fixtures

```javascript
// backend/tests/e2e/fixtures.js
const { test as base } = require('@playwright/test');
const { setupTestData, teardownTestData } = require('../fixtures/setup');

const test = base.extend({
  // 自動ログインFixture
  authenticatedPage: async ({ page }, use) => {
    await page.goto('/login.html');
    await page.fill('#username', 'admin@example.com');
    await page.fill('#password', 'Admin1234!');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/index.html');
    await use(page);
  },

  // MFA有効ユーザーFixture
  mfaEnabledPage: async ({ page }, use) => {
    await page.goto('/login.html');
    await page.fill('#username', 'admin_mfa@example.com');
    await page.fill('#password', 'AdminMFA1234!');
    await page.click('button[type="submit"]');

    // MFA検証
    await page.waitForSelector('#mfaForm');
    const totp = generateTOTP('JBSWY3DPEHPK3PXP');
    await page.fill('#mfaCode', totp);
    await page.waitForURL('**/index.html');

    await use(page);
  },

  // テストデータ準備Fixture
  withTestData: async ({}, use) => {
    await setupTestData();
    await use();
    await teardownTestData();
  }
});

module.exports = { test };
```

---

## 7. モックデータ

### 7.1 MS365 API モック

```javascript
// backend/tests/mocks/ms365_api.js
async function mockMS365API(page) {
  // OneDrive files API
  await page.route('**/api/ms365/onedrive/files**', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: [
          {
            id: 'file1',
            name: '安全管理マニュアル.pdf',
            size: 1024000,
            modifiedDateTime: '2026-02-10T09:00:00Z',
            webUrl: 'https://onedrive.live.com/...'
          },
          {
            id: 'file2',
            name: 'クレーン操作手順.docx',
            size: 512000,
            modifiedDateTime: '2026-02-09T14:30:00Z',
            webUrl: 'https://onedrive.live.com/...'
          }
        ]
      })
    });
  });

  // SharePoint sites API
  await page.route('**/api/ms365/sharepoint/sites**', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: [
          {
            id: 'site1',
            name: 'ConstructionDocs',
            webUrl: 'https://company.sharepoint.com/sites/ConstructionDocs'
          }
        ]
      })
    });
  });
}

module.exports = { mockMS365API };
```

### 7.2 WebSocket モック

```javascript
// backend/tests/mocks/websocket.js
class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      this.onopen && this.onopen();
    }, 100);
  }

  send(data) {
    console.log('[MockWebSocket] Send:', data);
  }

  close() {
    this.readyState = WebSocket.CLOSED;
    this.onclose && this.onclose();
  }

  // テスト用: 通知を手動送信
  simulateNotification(notification) {
    if (this.readyState === WebSocket.OPEN) {
      this.onmessage && this.onmessage({
        data: JSON.stringify(notification)
      });
    }
  }
}

async function mockWebSocket(page) {
  await page.addInitScript(() => {
    window.WebSocket = MockWebSocket;
  });
}

module.exports = { MockWebSocket, mockWebSocket };
```

---

## 8. テストデータ実行例

### 8.1 使用例

```javascript
// backend/tests/e2e/example.spec.js
const { test } = require('./fixtures');
const { TEST_USERS } = require('../fixtures/users');

test.describe('ログイン機能', () => {
  test('Admin権限でログイン成功', async ({ authenticatedPage }) => {
    // authenticatedPageはログイン済み
    await expect(authenticatedPage).toHaveURL('**/index.html');
  });

  test('MFA有効ユーザーでログイン成功', async ({ mfaEnabledPage }) => {
    // mfaEnabledPageはMFA検証済み
    await expect(mfaEnabledPage).toHaveURL('**/index.html');
  });

  test('テストデータ準備', async ({ page, withTestData }) => {
    // withTestDataでテストデータが自動準備・クリーンアップ
    await page.goto('/index.html');
    // テストロジック
  });
});
```

---

**作成日**: 2026-02-10
**作成者**: test-designer SubAgent
**バージョン**: v1.0
**ステータス**: レビュー待ち
