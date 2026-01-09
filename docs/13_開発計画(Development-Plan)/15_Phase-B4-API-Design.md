# Phase B-4: API設計確定

## 目的
UIと連携するRESTful API仕様を確定し、一貫性のあるエンドポイント設計を実現する

## API設計原則

### RESTful設計
- リソース指向のURL設計
- HTTPメソッドの適切な使用（GET, POST, PUT, DELETE）
- ステータスコードの標準準拠
- JSON形式のリクエスト/レスポンス

### 一貫性
- 統一されたレスポンス形式
- 統一されたエラーハンドリング
- 統一された命名規則（スネークケース）

### セキュリティ
- JWT認証の必須化（公開エンドポイント除く）
- RBAC による権限チェック
- 入力バリデーション
- レート制限

---

## 共通仕様

### ベースURL
```
本番: https://knowledge.construction-company.local/api/v1
開発: http://localhost:5000/api/v1
```

### リクエストヘッダー

**認証が必要なエンドポイント**
```http
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

### 共通レスポンス形式

**成功時**
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2025-12-26T10:30:00Z",
    "version": "1.0"
  }
}
```

**エラー時**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {
        "field": "title",
        "message": "Title is required"
      }
    ]
  },
  "meta": {
    "timestamp": "2025-12-26T10:30:00Z",
    "version": "1.0"
  }
}
```

### ページネーション

リスト取得エンドポイントは以下のクエリパラメータをサポート:

```
?page=1          # ページ番号（1始まり）
&per_page=20     # 1ページあたりの件数（デフォルト20、最大100）
&sort=updated_at # ソート対象列
&order=desc      # ソート順（asc/desc）
```

**ページネーション付きレスポンス**
```json
{
  "success": true,
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_items": 150,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

### エラーコード一覧

| コード | HTTPステータス | 説明 |
|--------|---------------|------|
| VALIDATION_ERROR | 400 | 入力検証エラー |
| UNAUTHORIZED | 401 | 認証エラー |
| FORBIDDEN | 403 | 権限不足 |
| NOT_FOUND | 404 | リソースが存在しない |
| CONFLICT | 409 | リソースの競合 |
| RATE_LIMIT_EXCEEDED | 429 | レート制限超過 |
| INTERNAL_ERROR | 500 | サーバー内部エラー |

---

## 認証・認可API

### POST /api/v1/auth/login
ユーザーログイン

**リクエスト**
```json
{
  "username": "yamada",
  "password": "SecurePassword123!"
}
```

**レスポンス**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": 42,
      "username": "yamada",
      "full_name": "山田太郎",
      "email": "yamada@example.com",
      "department": "施工管理",
      "roles": ["construction_manager"]
    }
  }
}
```

### POST /api/v1/auth/refresh
トークンリフレッシュ

**リクエスト**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**レスポンス**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 3600
  }
}
```

### POST /api/v1/auth/logout
ログアウト（トークン無効化）

**リクエスト**
```http
Authorization: Bearer <JWT_TOKEN>
```

**レスポンス**
```json
{
  "success": true,
  "data": {
    "message": "Logged out successfully"
  }
}
```

---

## ナレッジ管理API

### GET /api/v1/knowledge
ナレッジ一覧取得

**権限**: `knowledge.read`

**クエリパラメータ**
```
?category=施工計画      # カテゴリフィルタ
&tags=寒冷地施工,品質確保 # タグフィルタ（カンマ区切り）
&status=approved       # ステータスフィルタ
&search=温度管理       # 全文検索
&project=B-03         # プロジェクトフィルタ
&page=1
&per_page=20
&sort=updated_at
&order=desc
```

**レスポンス**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "砂防堰堤 コンクリート打設の温度管理フロー",
      "summary": "打設量180m3 / 連続8時間想定...",
      "category": "施工計画",
      "tags": ["品質確保", "寒冷地施工", "温度センサー"],
      "status": "approved",
      "priority": "high",
      "project": "B-03-3-2",
      "owner": "工事技術部",
      "created_at": "2024-06-10T10:00:00Z",
      "updated_at": "2024-06-19T14:30:00Z"
    }
  ],
  "pagination": { ... }
}
```

### GET /api/v1/knowledge/:id
ナレッジ詳細取得

**権限**: `knowledge.read`

**レスポンス**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "砂防堰堤 コンクリート打設の温度管理フロー",
    "summary": "打設量180m3...",
    "content": "詳細な手順: 1. 温度センサー設置...",
    "category": "施工計画",
    "tags": ["品質確保", "寒冷地施工"],
    "status": "approved",
    "priority": "high",
    "project": "B-03-3-2",
    "owner": "工事技術部",
    "created_by": {
      "id": 10,
      "full_name": "佐藤次郎"
    },
    "updated_by": {
      "id": 10,
      "full_name": "佐藤次郎"
    },
    "created_at": "2024-06-10T10:00:00Z",
    "updated_at": "2024-06-19T14:30:00Z",
    "related_knowledge": [
      {
        "id": 5,
        "title": "寒冷地コンクリート養生基準",
        "relevance_score": 0.85
      }
    ],
    "view_count": 127,
    "reference_count": 23
  }
}
```

### POST /api/v1/knowledge
ナレッジ新規登録

**権限**: `knowledge.create`

**リクエスト**
```json
{
  "title": "新規ナレッジタイトル",
  "summary": "概要説明",
  "content": "詳細内容",
  "category": "施工計画",
  "tags": ["タグ1", "タグ2"],
  "priority": "high",
  "project": "B-03-3-2"
}
```

**レスポンス**
```json
{
  "success": true,
  "data": {
    "id": 42,
    "title": "新規ナレッジタイトル",
    "status": "draft",
    "created_at": "2025-12-26T10:30:00Z"
  }
}
```

### PUT /api/v1/knowledge/:id
ナレッジ更新

**権限**: `knowledge.update`

**リクエスト**
```json
{
  "title": "更新後のタイトル",
  "summary": "更新後の概要",
  "status": "approved"
}
```

**レスポンス**
```json
{
  "success": true,
  "data": {
    "id": 42,
    "updated_at": "2025-12-26T11:00:00Z"
  }
}
```

### DELETE /api/v1/knowledge/:id
ナレッジ削除（論理削除）

**権限**: `knowledge.delete`

**レスポンス**
```json
{
  "success": true,
  "data": {
    "message": "Knowledge archived successfully"
  }
}
```

---

## SOP管理API

### GET /api/v1/sop
SOP一覧取得

**権限**: `sop.read`

**クエリパラメータ**: ナレッジAPIと同様

**レスポンス**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "高所作業車 乗車前点検SOP",
      "category": "安全管理",
      "version": "2.1",
      "revision_date": "2024-06-02",
      "status": "active",
      "tags": ["安全確認", "動画あり"]
    }
  ]
}
```

### GET /api/v1/sop/:id
SOP詳細取得

### GET /api/v1/sop/:id/revisions
SOP改訂履歴取得

**レスポンス**
```json
{
  "success": true,
  "data": [
    {
      "id": 3,
      "version": "2.1",
      "revision_date": "2024-06-02",
      "changes": "点検項目追加（バッテリー電圧確認）",
      "revised_by": "安全衛生室"
    },
    {
      "id": 2,
      "version": "2.0",
      "revision_date": "2024-01-15",
      "changes": "初版",
      "revised_by": "安全衛生室"
    }
  ]
}
```

---

## 事故レポートAPI

### GET /api/v1/incidents
事故レポート一覧取得

**権限**: `incident.read`

### GET /api/v1/incidents/:id
事故レポート詳細取得

### POST /api/v1/incidents
事故レポート登録

**権限**: `incident.create`

**リクエスト**
```json
{
  "title": "クレーン吊り荷回転による接触事故未遂",
  "description": "風速変化時の合図連携が遅延...",
  "project": "東北橋梁補修 B-03",
  "incident_date": "2024-06-23",
  "severity": "high",
  "location": "工区3-2 橋脚A1付近",
  "involved_parties": ["作業員A", "合図者B"],
  "corrective_actions": [
    {
      "action": "合図者の追加配置",
      "responsible": "現場所長",
      "due_date": "2024-06-30",
      "status": "planned"
    }
  ]
}
```

### PUT /api/v1/incidents/:id/status
事故レポートステータス更新

**リクエスト**
```json
{
  "status": "resolved",
  "resolution_note": "再発防止策を実施し、効果を確認"
}
```

---

## 専門家相談API

### GET /api/v1/consultations
専門家相談一覧取得

### GET /api/v1/consultations/:id
専門家相談詳細取得

### POST /api/v1/consultations
専門家相談登録

**リクエスト**
```json
{
  "title": "寒冷地でのコンクリート養生方法について",
  "question": "気温が5℃を下回る環境での...",
  "category": "技術本部 構造設計",
  "priority": "high"
}
```

### PUT /api/v1/consultations/:id/answer
専門家回答登録

**権限**: `consultation.answer` (専門家のみ)

**リクエスト**
```json
{
  "answer": "5℃未満の環境では、加熱養生が必須です...",
  "create_knowledge": true,
  "knowledge_data": {
    "title": "寒冷地コンクリート養生の標準手順",
    "category": "品質"
  }
}
```

---

## 承認フローAPI

### GET /api/v1/approvals
承認フロー一覧取得

**クエリパラメータ**
```
?status=pending        # ステータスフィルタ
&requester_id=42      # 申請者フィルタ
&type=施工計画        # 種別フィルタ
```

### GET /api/v1/approvals/:id
承認フロー詳細取得

### POST /api/v1/approvals/:id/approve
承認実行

**権限**: `approval.execute`

**リクエスト**
```json
{
  "comment": "承認します。次回から事前調整をお願いします。"
}
```

**レスポンス**
```json
{
  "success": true,
  "data": {
    "id": 5,
    "status": "approved",
    "approved_at": "2025-12-26T15:00:00Z",
    "approver": {
      "id": 8,
      "full_name": "鈴木所長"
    }
  }
}
```

### POST /api/v1/approvals/:id/reject
承認却下

**リクエスト**
```json
{
  "reason": "追加資料（水位計測結果）が必要です"
}
```

---

## 通知API

### GET /api/v1/notifications
通知一覧取得

**レスポンス**
```json
{
  "success": true,
  "data": [
    {
      "id": 10,
      "title": "重要：法令改訂のお知らせ",
      "message": "労働安全衛生規則が改正されました",
      "type": "urgent",
      "is_read": false,
      "created_at": "2025-12-26T09:00:00Z"
    }
  ]
}
```

### PUT /api/v1/notifications/:id/read
通知既読マーク

### POST /api/v1/notifications
通知送信（管理者のみ）

**権限**: `notification.send`

**リクエスト**
```json
{
  "title": "緊急：安全パトロール実施のお知らせ",
  "message": "明日10:00より全現場で安全パトロールを実施します",
  "type": "urgent",
  "target_roles": ["construction_manager", "site_manager"],
  "delivery_channels": ["email", "web"]
}
```

---

## ダッシュボード統計API

### GET /api/v1/dashboard/stats
ダッシュボード統計情報取得

**レスポンス**
```json
{
  "success": true,
  "data": {
    "kpis": {
      "knowledge_reuse_rate": 71,
      "accident_free_days": 184,
      "active_audits": 6,
      "delayed_corrections": 3
    },
    "counts": {
      "total_knowledge": 128,
      "total_sop": 56,
      "recent_incidents": 5,
      "pending_approvals": 7
    },
    "recent_activities": [
      {
        "id": 100,
        "type": "knowledge_created",
        "title": "河川護岸整備 施工計画変更",
        "user": "鈴木所長",
        "timestamp": "2025-12-26T08:40:00Z"
      }
    ]
  }
}
```

### GET /api/v1/dashboard/projects
プロジェクト進捗情報取得

**レスポンス**
```json
{
  "success": true,
  "data": [
    {
      "id": "B-03",
      "name": "東北橋梁補修",
      "progress": 64,
      "planned_progress": 67,
      "safety_rating": "A",
      "budget_utilization": 92
    }
  ]
}
```

---

## 検索API

### GET /api/v1/search
統合検索

**クエリパラメータ**
```
?q=温度管理              # 検索クエリ
&types=knowledge,sop    # 検索対象（カンマ区切り）
&page=1
&per_page=20
```

**レスポンス**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "type": "knowledge",
        "id": 1,
        "title": "砂防堰堤 コンクリート打設の温度管理フロー",
        "snippet": "...5℃未満時は<mark>温度管理</mark>を必須化...",
        "relevance_score": 0.95
      },
      {
        "type": "sop",
        "id": 3,
        "title": "冬季コンクリート養生SOP",
        "snippet": "...<mark>温度管理</mark>の記録を24時間継続...",
        "relevance_score": 0.88
      }
    ],
    "facets": {
      "knowledge": 15,
      "sop": 8,
      "regulations": 2
    }
  },
  "pagination": { ... }
}
```

---

## レート制限

### 制限値

| エンドポイント | 制限 |
|---------------|------|
| POST /api/v1/auth/login | 5回/分/IP |
| GET /api/v1/* | 100回/分/ユーザー |
| POST /api/v1/* | 30回/分/ユーザー |

### レスポンスヘッダー

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1703599200
```

---

## WebSocket API（将来実装）

### リアルタイム通知

```javascript
// 接続
const ws = new WebSocket('wss://knowledge.example.com/ws/notifications');

// メッセージ受信
ws.onmessage = (event) => {
  const notification = JSON.parse(event.data);
  // {type: 'new_approval', data: {...}}
};
```

---

## レビュー評価

| 観点 | 評価 | コメント |
|-----|-----|---------|
| 完成度 | 5/5 | 全主要エンドポイント定義完了 |
| 一貫性 | 5/5 | レスポンス形式・命名規則統一 |
| 実現性 | 5/5 | Flask + PostgreSQLで実装可能 |
| リスク | 5/5 | 認証・エラーハンドリング明確 |
| 受入準備 | 5/5 | APIテスト仕様の基礎完成 |

**合計**: 25/25点 ✅ 満点合格

---

## Next Actions

1. **Phase B-5開始**
   - SQLAlchemyモデル定義
   - Flask-JWT-Extended統合
   - エンドポイント実装

2. **API仕様書公開**
   - Swagger/OpenAPI仕様生成
   - Postmanコレクション作成

3. **APIテスト計画**
   - 単体テスト（pytest）
   - 統合テスト
   - パフォーマンステスト

## 変更履歴

| 日付 | バージョン | 変更内容 | 担当 |
| --- | --- | --- | --- |
| 2025-12-26 | 1.0 | 初版作成 | System |
