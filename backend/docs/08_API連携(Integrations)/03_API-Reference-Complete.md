# API仕様書（完全版）

## 概要

建設土木ナレッジシステムのREST APIリファレンスです。このドキュメントは、すべてのエンドポイント、リクエスト/レスポンス形式、認証方法、エラーコード、レート制限について包括的に説明します。

## 基本情報

### ベースURL

```
開発環境: http://localhost:8000
本番環境: https://api.example.com
```

### バージョン

API Version: v1
ドキュメントバージョン: 1.0.0
最終更新日: 2024年12月27日

### プロトコル

- 開発環境: HTTP
- 本番環境: HTTPS必須（HTTP接続は自動的にHTTPSへリダイレクト）

### データフォーマット

- リクエスト: JSON（Content-Type: application/json）
- レスポンス: JSON（Content-Type: application/json; charset=utf-8）
- 文字エンコーディング: UTF-8

## 認証

### 認証方式

このAPIは JWT（JSON Web Token）ベースの認証を使用します。

#### 認証フロー

1. `/api/v1/auth/login` でユーザー名とパスワードを送信
2. アクセストークンとリフレッシュトークンを取得
3. 以降のリクエストで `Authorization` ヘッダーにアクセストークンを含める
4. アクセストークンの有効期限が切れたら `/api/v1/auth/refresh` で更新

#### トークンの種類

| トークン種別 | 有効期限 | 用途 |
|------------|---------|------|
| アクセストークン | 1時間（デフォルト） | API呼び出しの認証 |
| リフレッシュトークン | 7日間（デフォルト） | アクセストークンの更新 |

#### リクエストヘッダー

```http
Authorization: Bearer {access_token}
```

#### 例

```bash
curl https://api.example.com/api/v1/knowledge \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## レート制限

APIへのリクエスト数には以下の制限があります。

### ログインエンドポイント

- 5回 / 分（同一IPアドレスあたり）
- 20回 / 時間（同一IPアドレスあたり）

### その他のエンドポイント

現在、ログインエンドポイント以外にレート制限は設定されていませんが、将来的に追加される可能性があります。

### レート制限超過時のレスポンス

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later."
  }
}
```

HTTPステータスコード: `429 Too Many Requests`

## 共通レスポンス形式

### 成功レスポンス

```json
{
  "success": true,
  "data": {
    // エンドポイント固有のデータ
  }
}
```

### エラーレスポンス

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "エラーメッセージ"
  }
}
```

### ページネーション付きレスポンス

```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "total_items": 100,
    "page": 1,
    "per_page": 20,
    "total_pages": 5
  }
}
```

## エンドポイント一覧

### 認証（Authentication）

| メソッド | パス | 説明 | 認証 |
|---------|------|------|------|
| POST | /api/v1/auth/login | ログイン | 不要 |
| POST | /api/v1/auth/refresh | トークン更新 | リフレッシュトークン |
| GET | /api/v1/auth/me | 現在のユーザー情報取得 | 必要 |

### 知識管理（Knowledge）

| メソッド | パス | 説明 | 認証 | 権限 |
|---------|------|------|------|------|
| GET | /api/v1/knowledge | ナレッジ一覧取得 | 必要 | knowledge.read |
| GET | /api/v1/knowledge/{id} | ナレッジ詳細取得 | 必要 | knowledge.read |
| POST | /api/v1/knowledge | ナレッジ作成 | 必要 | knowledge.create |

### 検索（Search）

| メソッド | パス | 説明 | 認証 |
|---------|------|------|------|
| GET | /api/v1/search/unified | 横断検索 | 必要 |

### 通知（Notifications）

| メソッド | パス | 説明 | 認証 |
|---------|------|------|------|
| GET | /api/v1/notifications | 通知一覧取得 | 必要 |
| PUT | /api/v1/notifications/{id}/read | 通知を既読にする | 必要 |
| GET | /api/v1/notifications/unread/count | 未読通知数取得 | 必要 |

### SOP（Standard Operating Procedures）

| メソッド | パス | 説明 | 認証 |
|---------|------|------|------|
| GET | /api/v1/sop | SOP一覧取得 | 必要 |

### ダッシュボード（Dashboard）

| メソッド | パス | 説明 | 認証 |
|---------|------|------|------|
| GET | /api/v1/dashboard/stats | 統計情報取得 | 必要 |

### 承認（Approvals）

| メソッド | パス | 説明 | 認証 |
|---------|------|------|------|
| GET | /api/v1/approvals | 承認待ちアイテム取得 | 必要 |

### メトリクス（Metrics）

| メソッド | パス | 説明 | 認証 |
|---------|------|------|------|
| GET | /api/v1/metrics | システムメトリクス取得 | 必要 |

---

## 詳細仕様

## 1. 認証API

### 1.1 ログイン

ユーザー名とパスワードでログインし、アクセストークンとリフレッシュトークンを取得します。

**エンドポイント**

```
POST /api/v1/auth/login
```

**認証**: 不要

**レート制限**: 5回/分、20回/時間

**リクエストボディ**

```json
{
  "username": "string (3-50文字)",
  "password": "string (6-100文字)"
}
```

**リクエスト例**

```bash
curl -X POST https://api.example.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "secure_password"
  }'
```

**成功レスポンス**

HTTPステータスコード: `200 OK`

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": "1",
      "username": "admin",
      "email": "admin@example.com",
      "roles": ["admin"],
      "full_name": "管理者"
    }
  }
}
```

**エラーレスポンス**

1. バリデーションエラー

HTTPステータスコード: `400 Bad Request`

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Username and password are required",
    "details": {
      "username": ["ユーザー名は必須です"],
      "password": ["パスワードは6文字以上である必要があります"]
    }
  }
}
```

2. 認証失敗

HTTPステータスコード: `401 Unauthorized`

```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid username or password"
  }
}
```

3. レート制限超過

HTTPステータスコード: `429 Too Many Requests`

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many login attempts. Please try again later."
  }
}
```

---

### 1.2 トークン更新

リフレッシュトークンを使用してアクセストークンを更新します。

**エンドポイント**

```
POST /api/v1/auth/refresh
```

**認証**: リフレッシュトークン必須

**リクエストヘッダー**

```http
Authorization: Bearer {refresh_token}
```

**リクエスト例**

```bash
curl -X POST https://api.example.com/api/v1/auth/refresh \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功レスポンス**

HTTPステータスコード: `200 OK`

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600
  }
}
```

**エラーレスポンス**

HTTPステータスコード: `401 Unauthorized`

```json
{
  "success": false,
  "error": {
    "code": "INVALID_TOKEN",
    "message": "Invalid or expired refresh token"
  }
}
```

---

### 1.3 現在のユーザー情報取得

ログイン中のユーザー情報を取得します。

**エンドポイント**

```
GET /api/v1/auth/me
```

**認証**: アクセストークン必須

**リクエスト例**

```bash
curl https://api.example.com/api/v1/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功レスポンス**

HTTPステータスコード: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "1",
    "username": "admin",
    "email": "admin@example.com",
    "roles": ["admin"],
    "full_name": "管理者",
    "permissions": {
      "knowledge": ["read", "create", "update", "delete"],
      "incident": ["read", "create"],
      "sop": ["read"]
    }
  }
}
```

**エラーレスポンス**

HTTPステータスコード: `404 Not Found`

```json
{
  "success": false,
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User not found"
  }
}
```

---

## 2. 知識管理API

### 2.1 ナレッジ一覧取得

ナレッジ記事の一覧を取得します。フィルタリング、検索、ソートが可能です。

**エンドポイント**

```
GET /api/v1/knowledge
```

**認証**: アクセストークン必須

**権限**: `knowledge.read`

**クエリパラメータ**

| パラメータ | 型 | 必須 | 説明 |
|-----------|---|------|------|
| category | string | × | カテゴリでフィルタ（施工計画、品質管理、安全衛生、環境対策、原価管理、出来形管理、その他） |
| search | string | × | 全文検索（title、summary、contentから検索） |
| tags | string | × | タグでフィルタ（カンマ区切りで複数指定可） |
| highlight | boolean | × | 検索結果をハイライト表示（デフォルト: false） |

**リクエスト例**

```bash
# 基本的な取得
curl https://api.example.com/api/v1/knowledge \
  -H "Authorization: Bearer {token}"

# カテゴリでフィルタ
curl "https://api.example.com/api/v1/knowledge?category=品質管理" \
  -H "Authorization: Bearer {token}"

# 全文検索
curl "https://api.example.com/api/v1/knowledge?search=コンクリート&highlight=true" \
  -H "Authorization: Bearer {token}"

# タグでフィルタ
curl "https://api.example.com/api/v1/knowledge?tags=橋梁,鋼構造" \
  -H "Authorization: Bearer {token}"
```

**成功レスポンス**

HTTPステータスコード: `200 OK`

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "コンクリート打設の品質管理手順",
      "summary": "コンクリート打設時の品質管理について詳細な手順を説明",
      "content": "...",
      "category": "品質管理",
      "tags": ["コンクリート", "品質管理"],
      "status": "approved",
      "created_at": "2024-01-15T09:00:00",
      "updated_at": "2024-01-20T14:30:00",
      "owner": "山田太郎",
      "project": "新橋梁建設プロジェクト",
      "priority": "high",
      "created_by_id": "1",
      "matched_fields": ["title", "content"],
      "relevance_score": 0.95
    }
  ],
  "pagination": {
    "total_items": 42
  }
}
```

**レスポンスフィールド説明**

| フィールド | 型 | 説明 |
|-----------|---|------|
| id | integer | ナレッジID |
| title | string | タイトル |
| summary | string | 概要 |
| content | string | 本文 |
| category | string | カテゴリ |
| tags | array[string] | タグリスト |
| status | string | ステータス（draft, pending, approved, archived） |
| created_at | datetime | 作成日時（ISO 8601形式） |
| updated_at | datetime | 更新日時（ISO 8601形式） |
| owner | string | 所有者名 |
| project | string | 関連プロジェクト |
| priority | string | 優先度（low, medium, high） |
| created_by_id | string | 作成者ID |
| matched_fields | array[string] | 検索マッチフィールド（検索時のみ） |
| relevance_score | float | 関連度スコア（検索時のみ、0-1の範囲） |

**エラーレスポンス**

HTTPステータスコード: `403 Forbidden`

```json
{
  "success": false,
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "You don't have permission to read knowledge"
  }
}
```

---

### 2.2 ナレッジ詳細取得

指定したIDのナレッジ記事の詳細を取得します。

**エンドポイント**

```
GET /api/v1/knowledge/{knowledge_id}
```

**認証**: アクセストークン必須

**権限**: `knowledge.read`

**パスパラメータ**

| パラメータ | 型 | 説明 |
|-----------|---|------|
| knowledge_id | integer | ナレッジID |

**リクエスト例**

```bash
curl https://api.example.com/api/v1/knowledge/1 \
  -H "Authorization: Bearer {token}"
```

**成功レスポンス**

HTTPステータスコード: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "コンクリート打設の品質管理手順",
    "summary": "コンクリート打設時の品質管理について詳細な手順を説明",
    "content": "## 概要\n\nコンクリート打設は...",
    "category": "品質管理",
    "tags": ["コンクリート", "品質管理"],
    "status": "approved",
    "created_at": "2024-01-15T09:00:00",
    "updated_at": "2024-01-20T14:30:00",
    "owner": "山田太郎",
    "project": "新橋梁建設プロジェクト",
    "priority": "high",
    "created_by_id": "1"
  }
}
```

**エラーレスポンス**

HTTPステータスコード: `404 Not Found`

```json
{
  "success": false,
  "error": {
    "code": "KNOWLEDGE_NOT_FOUND",
    "message": "Knowledge not found"
  }
}
```

---

### 2.3 ナレッジ作成

新しいナレッジ記事を作成します。

**エンドポイント**

```
POST /api/v1/knowledge
```

**認証**: アクセストークン必須

**権限**: `knowledge.create`

**リクエストボディ**

```json
{
  "title": "string (1-200文字、必須)",
  "summary": "string (1-500文字、必須)",
  "content": "string (1-50000文字、必須)",
  "category": "string (必須)",
  "tags": ["string"],
  "owner": "string (最大100文字)",
  "project": "string (最大100文字)",
  "priority": "string (low|medium|high)"
}
```

**有効なカテゴリ値**

- 施工計画
- 品質管理
- 安全衛生
- 環境対策
- 原価管理
- 出来形管理
- その他

**リクエスト例**

```bash
curl -X POST https://api.example.com/api/v1/knowledge \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "橋梁点検の新手法",
    "summary": "ドローンを活用した効率的な橋梁点検手法について",
    "content": "## 概要\n\n従来の橋梁点検では...",
    "category": "品質管理",
    "tags": ["橋梁", "ドローン", "点検"],
    "owner": "佐藤次郎",
    "project": "橋梁維持管理プロジェクト",
    "priority": "high"
  }'
```

**成功レスポンス**

HTTPステータスコード: `201 Created`

```json
{
  "success": true,
  "data": {
    "id": 43,
    "title": "橋梁点検の新手法",
    "summary": "ドローンを活用した効率的な橋梁点検手法について",
    "content": "## 概要\n\n従来の橋梁点検では...",
    "category": "品質管理",
    "tags": ["橋梁", "ドローン", "点検"],
    "status": "draft",
    "created_at": "2024-12-27T10:30:00",
    "updated_at": "2024-12-27T10:30:00",
    "owner": "佐藤次郎",
    "project": "橋梁維持管理プロジェクト",
    "priority": "high",
    "created_by_id": "2"
  }
}
```

**エラーレスポンス**

1. バリデーションエラー

HTTPステータスコード: `400 Bad Request`

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "title": ["タイトルは必須です"],
      "category": ["無効なカテゴリです"]
    }
  }
}
```

2. 権限エラー

HTTPステータスコード: `403 Forbidden`

```json
{
  "success": false,
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "You don't have permission to create knowledge"
  }
}
```

---

## 3. 検索API

### 3.1 横断検索

複数のエンティティ（知識、SOP、事故レポート）を横断的に検索します。

**エンドポイント**

```
GET /api/v1/search/unified
```

**認証**: アクセストークン必須

**クエリパラメータ**

| パラメータ | 型 | 必須 | 説明 |
|-----------|---|------|------|
| q | string | ○ | 検索クエリ |
| entities | string | × | 検索対象（カンマ区切り: knowledge,sop,incidents。デフォルト: すべて） |
| highlight | boolean | × | 検索結果をハイライト表示（デフォルト: false） |

**リクエスト例**

```bash
# すべてのエンティティを検索
curl "https://api.example.com/api/v1/search/unified?q=コンクリート" \
  -H "Authorization: Bearer {token}"

# 特定のエンティティのみ検索
curl "https://api.example.com/api/v1/search/unified?q=安全&entities=knowledge,sop" \
  -H "Authorization: Bearer {token}"

# ハイライト付き
curl "https://api.example.com/api/v1/search/unified?q=品質管理&highlight=true" \
  -H "Authorization: Bearer {token}"
```

**成功レスポンス**

HTTPステータスコード: `200 OK`

```json
{
  "success": true,
  "data": {
    "query": "コンクリート",
    "total_results": 15,
    "results": {
      "knowledge": {
        "count": 8,
        "items": [
          {
            "id": 1,
            "entity_type": "knowledge",
            "title": "コンクリート打設の品質管理手順",
            "summary": "コンクリート打設時の品質管理について...",
            "matched_fields": ["title", "content"],
            "relevance_score": 0.95,
            "url": "/knowledge/1"
          }
        ]
      },
      "sop": {
        "count": 5,
        "items": [...]
      },
      "incidents": {
        "count": 2,
        "items": [...]
      }
    }
  }
}
```

**エラーレスポンス**

HTTPステータスコード: `400 Bad Request`

```json
{
  "success": false,
  "error": {
    "code": "MISSING_QUERY",
    "message": "Search query is required"
  }
}
```

---

## 4. 通知API

### 4.1 通知一覧取得

ログイン中のユーザーの通知一覧を取得します。

**エンドポイント**

```
GET /api/v1/notifications
```

**認証**: アクセストークン必須

**クエリパラメータ**

| パラメータ | 型 | 必須 | 説明 |
|-----------|---|------|------|
| unread_only | boolean | × | 未読のみ取得（デフォルト: false） |
| type | string | × | 通知タイプでフィルタ |
| limit | integer | × | 取得件数制限（デフォルト: 50） |

**リクエスト例**

```bash
# 全通知を取得
curl https://api.example.com/api/v1/notifications \
  -H "Authorization: Bearer {token}"

# 未読のみ取得
curl "https://api.example.com/api/v1/notifications?unread_only=true" \
  -H "Authorization: Bearer {token}"
```

**成功レスポンス**

HTTPステータスコード: `200 OK`

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "新規ナレッジが承認待ちです",
      "message": "山田太郎さんが「コンクリート打設手順」を登録しました。承認をお願いします。",
      "type": "approval_required",
      "priority": "high",
      "is_read": false,
      "created_at": "2024-12-27T09:00:00",
      "related_entity_type": "knowledge",
      "related_entity_id": 42
    }
  ],
  "pagination": {
    "total_items": 15,
    "unread_count": 3
  }
}
```

**通知タイプ**

- `approval_required`: 承認が必要
- `approval_approved`: 承認された
- `approval_rejected`: 却下された
- `comment_added`: コメントが追加された
- `mention`: メンションされた
- `system`: システム通知

---

### 4.2 通知を既読にする

指定した通知を既読にします。

**エンドポイント**

```
PUT /api/v1/notifications/{notification_id}/read
```

**認証**: アクセストークン必須

**パスパラメータ**

| パラメータ | 型 | 説明 |
|-----------|---|------|
| notification_id | integer | 通知ID |

**リクエスト例**

```bash
curl -X PUT https://api.example.com/api/v1/notifications/1/read \
  -H "Authorization: Bearer {token}"
```

**成功レスポンス**

HTTPステータスコード: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": 1,
    "is_read": true,
    "read_at": "2024-12-27T10:30:00"
  }
}
```

---

### 4.3 未読通知数取得

未読の通知数を取得します。

**エンドポイント**

```
GET /api/v1/notifications/unread/count
```

**認証**: アクセストークン必須

**リクエスト例**

```bash
curl https://api.example.com/api/v1/notifications/unread/count \
  -H "Authorization: Bearer {token}"
```

**成功レスポンス**

HTTPステータスコード: `200 OK`

```json
{
  "success": true,
  "data": {
    "unread_count": 3,
    "by_type": {
      "approval_required": 2,
      "comment_added": 1
    }
  }
}
```

---

## 5. その他のAPI

### 5.1 SOP一覧取得

**エンドポイント**: `GET /api/v1/sop`

**認証**: アクセストークン必須

**成功レスポンス**: `200 OK`

```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "total_items": 25
  }
}
```

---

### 5.2 ダッシュボード統計情報

**エンドポイント**: `GET /api/v1/dashboard/stats`

**認証**: アクセストークン必須

**成功レスポンス**: `200 OK`

```json
{
  "success": true,
  "data": {
    "knowledge_count": 42,
    "sop_count": 25,
    "incident_count": 8,
    "pending_approvals": 3,
    "recent_activities": [...]
  }
}
```

---

### 5.3 承認待ちアイテム取得

**エンドポイント**: `GET /api/v1/approvals`

**認証**: アクセストークン必須

**成功レスポンス**: `200 OK`

```json
{
  "success": true,
  "data": [
    {
      "entity_type": "knowledge",
      "entity_id": 42,
      "title": "新規ナレッジ",
      "status": "pending",
      "submitted_at": "2024-12-27T09:00:00",
      "submitted_by": "山田太郎"
    }
  ]
}
```

---

### 5.4 システムメトリクス

**エンドポイント**: `GET /api/v1/metrics`

**認証**: アクセストークン必須

**権限**: 管理者のみ

**成功レスポンス**: `200 OK`

```json
{
  "success": true,
  "data": {
    "system": {
      "cpu_percent": 45.2,
      "memory_percent": 62.8,
      "disk_usage_percent": 38.5
    },
    "application": {
      "total_requests": 12345,
      "active_users": 25,
      "uptime_seconds": 86400
    }
  }
}
```

---

## エラーコード一覧

### 認証・認可エラー

| コード | HTTPステータス | 説明 |
|-------|---------------|------|
| UNAUTHORIZED | 401 | 認証が必要、またはトークンが無効 |
| INVALID_TOKEN | 401 | トークンの形式が不正、または期限切れ |
| PERMISSION_DENIED | 403 | 権限不足 |
| RATE_LIMIT_EXCEEDED | 429 | レート制限超過 |

### バリデーションエラー

| コード | HTTPステータス | 説明 |
|-------|---------------|------|
| VALIDATION_ERROR | 400 | リクエストのバリデーション失敗 |
| MISSING_FIELD | 400 | 必須フィールドが欠落 |
| INVALID_FORMAT | 400 | フィールドの形式が不正 |

### リソースエラー

| コード | HTTPステータス | 説明 |
|-------|---------------|------|
| NOT_FOUND | 404 | リソースが見つからない |
| KNOWLEDGE_NOT_FOUND | 404 | 指定したナレッジが存在しない |
| USER_NOT_FOUND | 404 | ユーザーが存在しない |

### サーバーエラー

| コード | HTTPステータス | 説明 |
|-------|---------------|------|
| INTERNAL_SERVER_ERROR | 500 | サーバー内部エラー |
| DATABASE_ERROR | 500 | データベースエラー |
| SERVICE_UNAVAILABLE | 503 | サービス利用不可 |

---

## 権限システム

### ロール一覧

| ロール | 説明 |
|-------|------|
| admin | システム管理者（全権限） |
| manager | マネージャー（承認権限あり） |
| engineer | エンジニア（読み書き可能） |
| viewer | 閲覧者（読み取りのみ） |
| quality_assurance | 品質保証担当（QA権限） |

### 権限マトリクス

| 操作 | admin | manager | engineer | viewer | QA |
|-----|-------|---------|----------|--------|-----|
| knowledge.read | ✓ | ✓ | ✓ | ✓ | ✓ |
| knowledge.create | ✓ | ✓ | ✓ | - | - |
| knowledge.update | ✓ | ✓ | ✓ | - | - |
| knowledge.delete | ✓ | ✓ | - | - | - |
| knowledge.approve | ✓ | ✓ | - | - | ✓ |
| sop.read | ✓ | ✓ | ✓ | ✓ | ✓ |
| incident.create | ✓ | ✓ | ✓ | - | - |
| metrics.view | ✓ | - | - | - | - |

---

## セキュリティ

### HTTPSの強制

本番環境ではHTTPS接続が必須です。HTTPでアクセスした場合、自動的にHTTPSへリダイレクトされます。

### セキュリティヘッダー

本番環境では以下のセキュリティヘッダーが設定されます:

```http
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

### CORS設定

クロスオリジンリクエストは環境変数 `MKS_CORS_ORIGINS` で指定されたオリジンからのみ許可されます。

### 入力検証

すべてのリクエストはMarshmallowスキーマによって検証されます。不正な入力は自動的に拒否されます。

---

## ベストプラクティス

### 1. トークン管理

- アクセストークンはローカルストレージではなくメモリ内に保持する
- リフレッシュトークンはHttpOnly Cookieまたは安全なストレージに保存
- トークン有効期限切れ時は自動的に更新を試みる

### 2. エラーハンドリング

```javascript
async function callAPI(url, options) {
  try {
    const response = await fetch(url, options);
    const data = await response.json();

    if (!response.ok) {
      if (response.status === 401) {
        // トークン更新を試みる
        await refreshToken();
        return callAPI(url, options);
      }
      throw new Error(data.error.message);
    }

    return data.data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}
```

### 3. レート制限の考慮

ログインAPIは厳しいレート制限があるため、以下を推奨します:

- ログイン失敗時はユーザーにわかりやすいメッセージを表示
- 連続ログイン失敗時は一時的にログインボタンを無効化
- リフレッシュトークンを活用して再ログインを最小化

### 4. ページネーション

将来的にページネーションが実装される可能性があるため、レスポンスの `pagination` フィールドを常に確認してください。

---

## 変更履歴

| バージョン | 日付 | 変更内容 |
|----------|------|---------|
| 1.0.0 | 2024-12-27 | 初版リリース |

---

## サポート

### ドキュメント

- [本番環境移行チェックリスト](../10_移行・展開(Deployment)/04_Production-Migration-Checklist.md)
- [HTTPS移行ガイド](../10_移行・展開(Deployment)/05_HTTPS-Migration-Guide.md)
- [運用マニュアル](../11_運用(Operations)/01_Operations-Manual.md)

### 問い合わせ

技術的な質問や問題がある場合は、開発チームまでお問い合わせください。

---

**最終更新日**: 2024年12月27日
**APIバージョン**: v1
**ドキュメントバージョン**: 1.0.0
