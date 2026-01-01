# Mirai Knowledge System API ドキュメント

## 目次

1. [概要](#概要)
2. [クイックスタート](#クイックスタート)
3. [認証・認可](#認証認可)
4. [エンドポイント一覧](#エンドポイント一覧)
5. [使用例](#使用例)
6. [エラーハンドリング](#エラーハンドリング)
7. [ベストプラクティス](#ベストプラクティス)
8. [レート制限](#レート制限)

---

## 概要

Mirai Knowledge System APIは、建設・土木業界向けのナレッジ管理システムを提供するREST APIです。

### 主要機能

- **ナレッジ管理**: 施工ノウハウ、品質管理ポイント、安全対策などの共有
- **SOP管理**: 標準施工手順の作成・配信・改訂管理
- **法令・規格管理**: 建設関連法令・規格の一元管理
- **事故・ヒヤリレポート**: インシデント報告・是正措置追跡
- **専門家相談**: 技術的な質問・回答のプラットフォーム
- **承認フロー**: ナレッジ・SOP承認プロセスの自動化
- **通知配信**: Email/Teams/アプリ内通知
- **横断検索**: 全エンティティ横断の高度な検索機能

### 技術仕様

- **プロトコル**: HTTPS (本番環境)
- **認証方式**: JWT (JSON Web Token)
- **データ形式**: JSON
- **APIバージョン**: v1 (`/api/v1/*`)
- **文字エンコーディング**: UTF-8

### ベースURL

```
開発環境: http://localhost:5100
本番環境: https://api.mks.example.com
```

### APIドキュメント

- **Swagger UI**: `/api/docs` - インタラクティブなAPIドキュメント
- **OpenAPI仕様**: `/api/openapi.yaml` - OpenAPI 3.0.3形式の仕様書

---

## クイックスタート

### 1. ログイン

```bash
curl -X POST http://localhost:5100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

**レスポンス例:**

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "roles": ["admin"]
    }
  }
}
```

### 2. ナレッジ一覧取得

```bash
curl -X GET http://localhost:5100/api/v1/knowledge \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. 新規ナレッジ作成

```bash
curl -X POST http://localhost:5100/api/v1/knowledge \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "基礎コンクリート打設時の品質管理",
    "summary": "品質確保のためのチェックリスト",
    "content": "## 打設前チェック\n1. 配筋検査完了確認...",
    "category": "品質管理",
    "tags": ["基礎工事", "コンクリート"],
    "priority": "high"
  }'
```

---

## 認証・認可

### 認証フロー

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant JWT

    Client->>API: POST /api/v1/auth/login
    API->>JWT: Generate tokens
    JWT-->>API: access_token + refresh_token
    API-->>Client: Return tokens

    Client->>API: GET /api/v1/knowledge (with Bearer token)
    API->>JWT: Validate token
    JWT-->>API: Valid
    API-->>Client: Return data

    Note over Client,API: Token expires after 1 hour

    Client->>API: POST /api/v1/auth/refresh (with refresh token)
    API->>JWT: Generate new access_token
    JWT-->>API: new access_token
    API-->>Client: Return new token
```

### JWT トークンの使用

すべての認証が必要なエンドポイントでは、`Authorization`ヘッダーにBearer トークンを含める必要があります。

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### トークンのライフサイクル

| トークンタイプ | 有効期限 | 用途 |
|--------------|---------|------|
| Access Token | 1時間 | API呼び出し用 |
| Refresh Token | 30日 | Access Tokenの更新用 |

### トークンのリフレッシュ

Access Tokenの有効期限が切れた場合、Refresh Tokenを使用して新しいAccess Tokenを取得できます。

```bash
curl -X POST http://localhost:5100/api/v1/auth/refresh \
  -H "Authorization: Bearer YOUR_REFRESH_TOKEN"
```

### 役割ベースのアクセス制御（RBAC）

システムは5つのロールを定義しています:

#### 1. admin（管理者）
- **権限**: すべての操作
- **用途**: システム管理者、IT部門

#### 2. construction_manager（施工管理者）
- **権限**:
  - ナレッジ作成・更新・閲覧
  - SOP閲覧
  - 事故レポート作成・閲覧
  - 専門家相談作成
  - 承認依頼
- **用途**: 現場管理者、工事主任

#### 3. quality_assurance（品質管理者）
- **権限**:
  - ナレッジ承認・閲覧
  - SOP更新・閲覧
  - 事故レポート閲覧
  - 承認実行
- **用途**: 品質管理部門、検査担当

#### 4. safety_officer（安全管理者）
- **権限**:
  - ナレッジ・SOP閲覧
  - 事故レポート作成・更新・閲覧
  - 承認依頼・閲覧
- **用途**: 安全衛生管理者

#### 5. partner_company（協力会社）
- **権限**:
  - ナレッジ・SOP・事故レポート閲覧のみ
- **用途**: 外部協力企業、下請け業者

### 権限チェック例

各エンドポイントは必要な権限を定義しています:

```python
# ナレッジ作成には knowledge.create 権限が必要
POST /api/v1/knowledge  # 必要権限: knowledge.create

# ナレッジ閲覧には knowledge.read 権限が必要
GET /api/v1/knowledge   # 必要権限: knowledge.read
```

権限が不足している場合は`403 Forbidden`エラーが返されます。

---

## エンドポイント一覧

### 認証 (Authentication)

| メソッド | エンドポイント | 説明 | 認証 |
|---------|---------------|------|------|
| POST | `/api/v1/auth/login` | ログイン | 不要 |
| POST | `/api/v1/auth/refresh` | トークンリフレッシュ | Refresh Token |
| GET | `/api/v1/auth/me` | 現在のユーザー情報取得 | 必要 |

### ナレッジ管理 (Knowledge)

| メソッド | エンドポイント | 説明 | 必要権限 |
|---------|---------------|------|---------|
| GET | `/api/v1/knowledge` | ナレッジ一覧取得 | knowledge.read |
| GET | `/api/v1/knowledge/{id}` | ナレッジ詳細取得 | knowledge.read |
| POST | `/api/v1/knowledge` | 新規ナレッジ作成 | knowledge.create |
| PUT | `/api/v1/knowledge/{id}` | ナレッジ更新 | knowledge.update |
| DELETE | `/api/v1/knowledge/{id}` | ナレッジ削除 | knowledge.delete |

### SOP管理 (Standard Operating Procedures)

| メソッド | エンドポイント | 説明 | 必要権限 |
|---------|---------------|------|---------|
| GET | `/api/v1/sop` | SOP一覧取得 | sop.read |
| GET | `/api/v1/sop/{id}` | SOP詳細取得 | sop.read |
| POST | `/api/v1/sop` | 新規SOP作成 | sop.create |
| PUT | `/api/v1/sop/{id}` | SOP更新 | sop.update |

### 検索 (Search)

| メソッド | エンドポイント | 説明 | 必要権限 |
|---------|---------------|------|---------|
| GET | `/api/v1/search/unified` | 横断検索 | 各エンティティの read 権限 |

### 通知 (Notifications)

| メソッド | エンドポイント | 説明 | 必要権限 |
|---------|---------------|------|---------|
| GET | `/api/v1/notifications` | 通知一覧取得 | 認証済み |
| PUT | `/api/v1/notifications/{id}/read` | 通知を既読にする | 認証済み |
| GET | `/api/v1/notifications/unread/count` | 未読通知数取得 | 認証済み |

### 承認フロー (Approvals)

| メソッド | エンドポイント | 説明 | 必要権限 |
|---------|---------------|------|---------|
| GET | `/api/v1/approvals` | 承認フロー一覧取得 | 認証済み |

### ダッシュボード (Dashboard)

| メソッド | エンドポイント | 説明 | 必要権限 |
|---------|---------------|------|---------|
| GET | `/api/v1/dashboard/stats` | 統計情報取得 | 認証済み |

### メトリクス (Metrics)

| メソッド | エンドポイント | 説明 | 認証 |
|---------|---------------|------|------|
| GET | `/api/v1/metrics` | Prometheusメトリクス | 不要 |
| GET | `/metrics` | システムメトリクス | 不要 |
| GET | `/api/metrics/summary` | メトリクスサマリー | 必要 |

---

## 使用例

### Python (requests)

```python
import requests

# ベースURL
BASE_URL = "http://localhost:5100"

# ログイン
login_response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    json={
        "username": "admin",
        "password": "admin123"
    }
)
login_data = login_response.json()
access_token = login_data["data"]["access_token"]

# 認証ヘッダー
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# ナレッジ一覧取得
knowledge_response = requests.get(
    f"{BASE_URL}/api/v1/knowledge",
    headers=headers
)
knowledge_list = knowledge_response.json()["data"]
print(f"ナレッジ数: {len(knowledge_list)}")

# 新規ナレッジ作成
new_knowledge = {
    "title": "型枠工事の品質管理ポイント",
    "summary": "型枠の精度確保と安全性確認",
    "content": """
## 型枠設置前の確認事項
1. 図面との整合性確認
2. 材料の損傷チェック
3. 支保工の安定性確認

## 設置時の注意点
- 垂直・水平の精度確認
- 締付けボルトの確実な締結
- 離型剤の適切な塗布
    """,
    "category": "品質管理",
    "tags": ["型枠", "品質管理", "施工管理"],
    "priority": "high"
}

create_response = requests.post(
    f"{BASE_URL}/api/v1/knowledge",
    headers=headers,
    json=new_knowledge
)
created_knowledge = create_response.json()["data"]
print(f"作成されたナレッジID: {created_knowledge['id']}")

# 横断検索
search_response = requests.get(
    f"{BASE_URL}/api/v1/search/unified",
    headers=headers,
    params={
        "q": "コンクリート",
        "types": "knowledge,sop,incidents",
        "highlight": "true"
    }
)
search_results = search_response.json()["data"]
print(f"検索結果総数: {search_response.json()['total_results']}")
```

### JavaScript (Axios)

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:5100';

// ログイン関数
async function login(username, password) {
  const response = await axios.post(`${BASE_URL}/api/v1/auth/login`, {
    username,
    password
  });
  return response.data.data.access_token;
}

// ナレッジ取得関数
async function getKnowledge(token, filters = {}) {
  const response = await axios.get(`${BASE_URL}/api/v1/knowledge`, {
    headers: {
      'Authorization': `Bearer ${token}`
    },
    params: filters
  });
  return response.data.data;
}

// メイン処理
async function main() {
  try {
    // ログイン
    const token = await login('admin', 'admin123');
    console.log('ログイン成功');

    // ナレッジ一覧取得
    const knowledgeList = await getKnowledge(token);
    console.log(`ナレッジ数: ${knowledgeList.length}`);

    // カテゴリでフィルタ
    const qualityKnowledge = await getKnowledge(token, {
      category: '品質管理',
      search: 'コンクリート'
    });
    console.log(`品質管理カテゴリのナレッジ: ${qualityKnowledge.length}`);

  } catch (error) {
    console.error('エラー:', error.response?.data || error.message);
  }
}

main();
```

### cURL

#### ナレッジ検索（カテゴリ・キーワードフィルタ）

```bash
curl -X GET "http://localhost:5100/api/v1/knowledge?category=品質管理&search=コンクリート" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 横断検索（ハイライト有効）

```bash
curl -X GET "http://localhost:5100/api/v1/search/unified?q=基礎工事&types=knowledge,sop&highlight=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 通知一覧取得

```bash
curl -X GET http://localhost:5100/api/v1/notifications \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 通知を既読にする

```bash
curl -X PUT http://localhost:5100/api/v1/notifications/5/read \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### ダッシュボード統計取得

```bash
curl -X GET http://localhost:5100/api/v1/dashboard/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## エラーハンドリング

### 標準エラーレスポンス形式

すべてのエラーレスポンスは以下の形式で返されます:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "人間が読めるエラーメッセージ",
    "details": {
      "additional": "info"
    }
  }
}
```

### エラーコード一覧

| HTTPステータス | エラーコード | 説明 | 対処方法 |
|--------------|------------|------|---------|
| 400 | `VALIDATION_ERROR` | 入力検証エラー | リクエストボディを確認 |
| 400 | `INVALID_JSON` | 不正なJSON | JSON形式を確認 |
| 400 | `MISSING_QUERY` | 必須パラメータ不足 | クエリパラメータを確認 |
| 401 | `UNAUTHORIZED` | 認証失敗 | ユーザー名・パスワードを確認 |
| 401 | `MISSING_TOKEN` | トークンなし | Authorizationヘッダーを追加 |
| 401 | `INVALID_TOKEN` | 無効なトークン | 正しいトークンを使用 |
| 401 | `TOKEN_EXPIRED` | トークン期限切れ | トークンをリフレッシュ |
| 403 | `FORBIDDEN` | 権限不足 | 必要な権限を確認 |
| 404 | `NOT_FOUND` | リソースが見つからない | IDを確認 |
| 409 | `CONFLICT` | リソースの競合 | データを確認 |
| 422 | `VALIDATION_ERROR` | バリデーションエラー | 入力値を確認 |
| 429 | `RATE_LIMIT_EXCEEDED` | レート制限超過 | しばらく待機 |
| 500 | `INTERNAL_ERROR` | サーバー内部エラー | 管理者に連絡 |

### エラーハンドリング例（Python）

```python
import requests

try:
    response = requests.post(
        f"{BASE_URL}/api/v1/knowledge",
        headers=headers,
        json=knowledge_data
    )
    response.raise_for_status()  # HTTPエラーチェック

    data = response.json()
    if not data.get("success"):
        error = data.get("error", {})
        print(f"エラー: {error.get('code')} - {error.get('message')}")
        if "details" in error:
            print(f"詳細: {error['details']}")
    else:
        print("成功:", data["data"])

except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        print("認証エラー: トークンをリフレッシュしてください")
    elif e.response.status_code == 403:
        print("権限エラー: このリソースにアクセスする権限がありません")
    elif e.response.status_code == 429:
        print("レート制限: しばらく待ってから再試行してください")
    else:
        print(f"HTTPエラー: {e}")

except requests.exceptions.RequestException as e:
    print(f"リクエストエラー: {e}")
```

---

## ベストプラクティス

### 1. トークン管理

#### ✅ 推奨

```python
class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None

    def login(self, username, password):
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"username": username, "password": password}
        )
        data = response.json()["data"]
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]

    def refresh_access_token(self):
        response = requests.post(
            f"{self.base_url}/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {self.refresh_token}"}
        )
        self.access_token = response.json()["data"]["access_token"]

    def request(self, method, endpoint, **kwargs):
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"

        try:
            response = requests.request(
                method,
                f"{self.base_url}{endpoint}",
                headers=headers,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                # トークンリフレッシュして再試行
                self.refresh_access_token()
                headers["Authorization"] = f"Bearer {self.access_token}"
                response = requests.request(
                    method,
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
            raise
```

#### ❌ 非推奨

```python
# トークンをハードコーディング
headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}

# トークンをGitにコミット
API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 2. エラーハンドリング

#### ✅ 推奨

```python
def create_knowledge_safe(client, knowledge_data):
    """エラーハンドリング付きナレッジ作成"""
    try:
        response = client.request(
            "POST",
            "/api/v1/knowledge",
            json=knowledge_data
        )
        return response["data"]
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            error_details = e.response.json().get("error", {}).get("details", {})
            print("入力検証エラー:")
            for field, errors in error_details.items():
                print(f"  {field}: {', '.join(errors)}")
        elif e.response.status_code == 403:
            print("権限エラー: ナレッジ作成権限がありません")
        else:
            print(f"予期しないエラー: {e}")
        return None
```

### 3. ページング・フィルタリング

#### ✅ 推奨

```python
def get_all_quality_knowledge(client):
    """品質管理カテゴリのナレッジを全件取得"""
    knowledge_list = []

    response = client.request(
        "GET",
        "/api/v1/knowledge",
        params={"category": "品質管理"}
    )

    knowledge_list.extend(response["data"])
    return knowledge_list

def search_knowledge(client, query, filters=None):
    """高度な検索"""
    params = {"search": query, "highlight": "true"}
    if filters:
        params.update(filters)

    response = client.request(
        "GET",
        "/api/v1/knowledge",
        params=params
    )

    return response["data"]
```

### 4. レート制限対応

#### ✅ 推奨

```python
import time
from functools import wraps

def retry_on_rate_limit(max_retries=3, backoff_factor=2):
    """レート制限時に自動リトライ"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = backoff_factor ** attempt
                            print(f"レート制限: {wait_time}秒待機...")
                            time.sleep(wait_time)
                        else:
                            raise
                    else:
                        raise
            return None
        return wrapper
    return decorator

@retry_on_rate_limit(max_retries=5)
def login(username, password):
    # ログイン処理
    pass
```

### 5. セキュリティ

#### ✅ 推奨

```python
import os
from dotenv import load_dotenv

# 環境変数から認証情報を読み込み
load_dotenv()
username = os.getenv("MKS_USERNAME")
password = os.getenv("MKS_PASSWORD")
```

#### ❌ 非推奨

```python
# コード内にパスワードをハードコーディング
username = "admin"
password = "admin123"
```

---

## レート制限

### 制限内容

| 環境 | 制限 |
|-----|------|
| 開発環境 | 制限なし |
| 本番環境 | 1000リクエスト/分、10000リクエスト/時、100000リクエスト/日 |

### 特別な制限

| エンドポイント | 制限 |
|--------------|------|
| `/api/v1/auth/login` | 5リクエスト/分、20リクエスト/時 |

### レート制限超過時の対応

レート制限を超えると、`429 Too Many Requests`エラーが返されます。

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "リクエストが多すぎます。しばらく待ってから再試行してください。",
    "details": {
      "retry_after": "60 seconds"
    }
  }
}
```

**対処方法:**
1. `retry_after`の秒数だけ待機
2. 指数バックオフを実装
3. リクエストをバッチ処理

---

## サポート

### Swagger UI

APIドキュメントはSwagger UIで確認できます:

```
http://localhost:5100/api/docs
```

### OpenAPI仕様

OpenAPI 3.0.3形式の仕様書:

```
http://localhost:5100/api/openapi.yaml
```

### お問い合わせ

技術的な質問やサポートが必要な場合は、以下にご連絡ください:

- Email: support@example.com
- GitHub Issues: https://github.com/yourorg/mirai-knowledge-system/issues

---

## 変更履歴

### v2.0.0 (2024-01-01)
- JWT認証の実装
- RBAC（役割ベースアクセス制御）の追加
- 横断検索機能の強化
- Prometheusメトリクスの追加
- レート制限の実装
- OpenAPI 3.0.3仕様書の作成

### v1.0.0 (2023-12-01)
- 初版リリース
- 基本的なCRUD操作
- ナレッジ・SOP管理機能
