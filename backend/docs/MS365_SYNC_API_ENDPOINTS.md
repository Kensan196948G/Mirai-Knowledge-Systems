# Microsoft 365同期API エンドポイント一覧

## ベースURL
```
/api/v1/integrations/microsoft365/sync
```

## エンドポイント概要

| # | メソッド | パス | 説明 | Rate Limit |
|---|----------|------|------|------------|
| 1 | GET | `/configs` | 設定一覧取得 | なし |
| 2 | POST | `/configs` | 設定作成 | 10/min |
| 3 | GET | `/configs/<id>` | 設定取得 | なし |
| 4 | PUT | `/configs/<id>` | 設定更新 | 10/min |
| 5 | DELETE | `/configs/<id>` | 設定削除 | 10/min |
| 6 | POST | `/configs/<id>/execute` | 手動同期実行 | 5/min |
| 7 | POST | `/configs/<id>/test` | 接続テスト | 10/min |
| 8 | GET | `/configs/<id>/history` | 同期履歴取得 | なし |
| 9 | GET | `/stats` | 統計情報取得 | なし |
| 10 | GET | `/status` | サービスステータス | なし |

## 詳細仕様

### 1. 設定一覧取得
```http
GET /api/v1/integrations/microsoft365/sync/configs
Authorization: Bearer <token>
```

**レスポンス**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "SharePoint同期",
      "site_id": "...",
      "drive_id": "...",
      "folder_path": "/Documents",
      "sync_schedule": "0 2 * * *",
      "sync_strategy": "incremental",
      "file_extensions": ["pdf", "docx"],
      "is_enabled": true,
      "created_at": "2026-01-31T10:00:00Z",
      "last_sync_at": "2026-01-31T02:00:00Z",
      "next_sync_at": "2026-02-01T02:00:00Z"
    }
  ]
}
```

### 2. 設定作成
```http
POST /api/v1/integrations/microsoft365/sync/configs
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "SharePoint同期",
  "site_id": "contoso.sharepoint.com,xxx,yyy",
  "drive_id": "b!xxx",
  "folder_path": "/Documents",
  "sync_schedule": "0 2 * * *",
  "sync_strategy": "incremental",
  "file_extensions": ["pdf", "docx"],
  "is_enabled": true
}
```

**必須フィールド**:
- `name` (string): 設定名
- `site_id` (string): SharePointサイトID
- `drive_id` (string): ドライブID

**オプションフィールド**:
- `folder_path` (string): 同期対象フォルダパス（デフォルト: `/`）
- `sync_schedule` (string): cronスケジュール（デフォルト: `0 2 * * *`）
- `sync_strategy` (string): `incremental` または `full`（デフォルト: `incremental`）
- `file_extensions` (array): 拡張子フィルタ（例: `["pdf", "docx"]`）
- `is_enabled` (boolean): 有効/無効（デフォルト: `true`）

**レスポンス**: 201 Created
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "SharePoint同期",
    ...
  }
}
```

### 3. 設定取得
```http
GET /api/v1/integrations/microsoft365/sync/configs/1
Authorization: Bearer <token>
```

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "SharePoint同期",
    ...
  }
}
```

### 4. 設定更新
```http
PUT /api/v1/integrations/microsoft365/sync/configs/1
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "更新されたSharePoint同期",
  "sync_schedule": "0 3 * * *",
  "is_enabled": false
}
```

**更新可能フィールド**:
- `name`
- `folder_path`
- `sync_schedule`
- `sync_strategy`
- `file_extensions`
- `is_enabled`

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "更新されたSharePoint同期",
    ...
  }
}
```

### 5. 設定削除
```http
DELETE /api/v1/integrations/microsoft365/sync/configs/1
Authorization: Bearer <token>
```

**レスポンス**:
```json
{
  "success": true,
  "message": "Sync config 1 deleted successfully"
}
```

### 6. 手動同期実行
```http
POST /api/v1/integrations/microsoft365/sync/configs/1/execute
Authorization: Bearer <token>
```

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "history_id": 123,
    "status": "completed",
    "execution_time_seconds": 45,
    "files_processed": 10,
    "files_created": 3,
    "files_updated": 5,
    "files_skipped": 2,
    "files_failed": 0,
    "errors": []
  }
}
```

### 7. 接続テスト
```http
POST /api/v1/integrations/microsoft365/sync/configs/1/test
Authorization: Bearer <token>
```

**レスポンス（成功）**:
```json
{
  "success": true,
  "data": {
    "success": true,
    "message": "接続テスト成功",
    "organization": "Contoso Ltd.",
    "files_found": 15,
    "sample_files": [
      {
        "id": "...",
        "name": "document1.pdf",
        "size": 12345,
        "lastModifiedDateTime": "2026-01-30T10:00:00Z"
      }
    ]
  }
}
```

**レスポンス（失敗）**:
```json
{
  "success": false,
  "error": {
    "code": "CONNECTION_FAILED",
    "message": "Graph API接続失敗"
  }
}
```

### 8. 同期履歴取得
```http
GET /api/v1/integrations/microsoft365/sync/configs/1/history?page=1&per_page=20
Authorization: Bearer <token>
```

**クエリパラメータ**:
- `page` (int): ページ番号（デフォルト: 1）
- `per_page` (int): 1ページあたりの件数（デフォルト: 20）

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 123,
        "config_id": 1,
        "sync_started_at": "2026-01-31T02:00:00Z",
        "sync_completed_at": "2026-01-31T02:00:45Z",
        "status": "completed",
        "triggered_by": "scheduler",
        "execution_time_seconds": 45,
        "files_processed": 10,
        "files_created": 3,
        "files_updated": 5,
        "files_skipped": 2,
        "files_failed": 0
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 45,
      "pages": 3
    }
  }
}
```

### 9. 統計情報取得
```http
GET /api/v1/integrations/microsoft365/sync/stats
Authorization: Bearer <token>
```

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "total_configs": 5,
    "enabled_configs": 3,
    "disabled_configs": 2,
    "recent_syncs": {
      "total": 15,
      "completed": 12,
      "failed": 2,
      "running": 1
    },
    "last_sync": {
      "config_id": 3,
      "status": "completed",
      "completed_at": "2026-01-31T10:30:00Z",
      "files_processed": 8
    }
  }
}
```

### 10. サービスステータス取得
```http
GET /api/v1/integrations/microsoft365/sync/status
Authorization: Bearer <token>
```

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "sync_service_available": true,
    "scheduler_service_available": true,
    "scheduler_running": true,
    "scheduled_jobs": [
      {
        "id": "ms365_sync_1",
        "name": "MS365 Sync: SharePoint同期",
        "next_run_time": "2026-02-01T02:00:00Z",
        "trigger": "cron[hour='2']"
      }
    ],
    "graph_api_configured": true
  }
}
```

## エラーレスポンス

全エンドポイントで統一されたエラーフォーマット:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "エラーメッセージ"
  }
}
```

**HTTPステータスコード**:
- `200 OK`: 成功
- `201 Created`: リソース作成成功
- `400 Bad Request`: バリデーションエラー、接続失敗
- `403 Forbidden`: 権限エラー
- `404 Not Found`: リソースが見つからない
- `429 Too Many Requests`: Rate limit超過
- `500 Internal Server Error`: サーバーエラー
- `503 Service Unavailable`: サービス利用不可

**エラーコード一覧**:
- `VALIDATION_ERROR`: バリデーションエラー
- `NOT_FOUND`: リソースが見つからない
- `PERMISSION_ERROR`: 権限エラー
- `CONNECTION_FAILED`: 接続失敗
- `SERVICE_UNAVAILABLE`: サービス利用不可
- `SERVER_ERROR`: サーバーエラー

## 認証・認可

### 認証
全エンドポイントでJWT Bearer認証が必須:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 認可
全エンドポイントで `integration.manage` 権限が必要。

**権限を持つロール**:
- `admin`: 管理者
- `manager`: マネージャー

### 監査ログ
全操作は監査ログに記録されます:

```python
log_access(user_id, action, resource_type, resource_id)
```

## 使用例（curl）

### 設定を作成して同期を実行

```bash
# 1. ログインしてトークン取得
TOKEN=$(curl -X POST http://localhost:5200/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin123!"}' \
  | jq -r '.data.access_token')

# 2. 同期設定を作成
CONFIG_ID=$(curl -X POST http://localhost:5200/api/v1/integrations/microsoft365/sync/configs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "テスト同期",
    "site_id": "test-site",
    "drive_id": "test-drive",
    "folder_path": "/Documents",
    "is_enabled": false
  }' | jq -r '.data.id')

# 3. 接続テスト
curl -X POST "http://localhost:5200/api/v1/integrations/microsoft365/sync/configs/$CONFIG_ID/test" \
  -H "Authorization: Bearer $TOKEN"

# 4. 手動同期実行
curl -X POST "http://localhost:5200/api/v1/integrations/microsoft365/sync/configs/$CONFIG_ID/execute" \
  -H "Authorization: Bearer $TOKEN"

# 5. 履歴確認
curl -X GET "http://localhost:5200/api/v1/integrations/microsoft365/sync/configs/$CONFIG_ID/history" \
  -H "Authorization: Bearer $TOKEN"

# 6. 統計情報確認
curl -X GET "http://localhost:5200/api/v1/integrations/microsoft365/sync/stats" \
  -H "Authorization: Bearer $TOKEN"
```

## クライアント実装例（JavaScript）

```javascript
class MS365SyncClient {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  async getConfigs() {
    const response = await fetch(
      `${this.baseUrl}/integrations/microsoft365/sync/configs`,
      {
        headers: {
          'Authorization': `Bearer ${this.token}`
        }
      }
    );
    return response.json();
  }

  async createConfig(config) {
    const response = await fetch(
      `${this.baseUrl}/integrations/microsoft365/sync/configs`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
      }
    );
    return response.json();
  }

  async executeSync(configId) {
    const response = await fetch(
      `${this.baseUrl}/integrations/microsoft365/sync/configs/${configId}/execute`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token}`
        }
      }
    );
    return response.json();
  }

  async getHistory(configId, page = 1, perPage = 20) {
    const response = await fetch(
      `${this.baseUrl}/integrations/microsoft365/sync/configs/${configId}/history?page=${page}&per_page=${perPage}`,
      {
        headers: {
          'Authorization': `Bearer ${this.token}`
        }
      }
    );
    return response.json();
  }

  async getStats() {
    const response = await fetch(
      `${this.baseUrl}/integrations/microsoft365/sync/stats`,
      {
        headers: {
          'Authorization': `Bearer ${this.token}`
        }
      }
    );
    return response.json();
  }
}

// 使用例
const client = new MS365SyncClient('http://localhost:5200/api/v1', token);
const stats = await client.getStats();
console.log(stats);
```

## 次のステップ

1. **WebUI実装** (Phase 4)
   - 同期設定管理画面
   - 同期履歴ビューア
   - リアルタイム同期状況表示

2. **テスト追加** (Phase 5)
   - 統合テスト
   - E2Eテスト
   - パフォーマンステスト

3. **ドキュメント整備**
   - OpenAPI/Swagger仕様追加
   - 運用ガイド作成
