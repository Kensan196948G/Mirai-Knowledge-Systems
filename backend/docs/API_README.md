# Mirai Knowledge System API - 完全ガイド

## はじめに

Mirai Knowledge System API ドキュメントへようこそ！

このドキュメントセットは、建設・土木業界向けナレッジ管理システムのREST APIを包括的に説明します。

## ドキュメント構成

### 📚 主要ドキュメント

| ドキュメント | 説明 | 対象者 |
|------------|------|--------|
| [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) | 完全なAPIリファレンスガイド | 全開発者 |
| [AUTHENTICATION_FLOW.md](./AUTHENTICATION_FLOW.md) | 認証・認可の詳細説明 | セキュリティ担当者、開発者 |
| [openapi.yaml](../openapi.yaml) | OpenAPI 3.0.3仕様書 | 自動ツール、上級開発者 |

### 🌐 インタラクティブドキュメント

```
http://localhost:5100/api/docs - Swagger UI
```

Swagger UIでは以下が可能です：
- すべてのエンドポイントの閲覧
- リクエスト/レスポンスの確認
- ブラウザから直接APIをテスト
- トークンの自動管理

### 💻 コード例

| ファイル | 言語 | 説明 |
|---------|------|------|
| [python_example.py](./examples/python_example.py) | Python | Python requestsライブラリを使用した完全な例 |
| [javascript_example.js](./examples/javascript_example.js) | JavaScript | Node.js + Axiosを使用した完全な例 |
| [curl_examples.sh](./examples/curl_examples.sh) | Bash/cURL | cURLコマンドのコレクション |

## クイックスタート

### 前提条件

- Python 3.8以上
- pip
- （オプション）Postman、Insomnia等のAPIクライアント

### 1. サーバー起動

```bash
cd /path/to/backend
python app_v2.py
```

サーバーは `http://localhost:5100` で起動します。

### 2. Swagger UIでAPIを探索

ブラウザで以下にアクセス:

```
http://localhost:5100/api/docs
```

### 3. 最初のAPI呼び出し

#### cURLで試す

```bash
# ログイン
curl -X POST http://localhost:5100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# トークンを環境変数に保存
export TOKEN="your_access_token_here"

# ナレッジ一覧取得
curl -X GET http://localhost:5100/api/v1/knowledge \
  -H "Authorization: Bearer $TOKEN"
```

#### Pythonで試す

```bash
cd docs/examples
python python_example.py
```

#### JavaScriptで試す

```bash
cd docs/examples
npm install axios
node javascript_example.js
```

## 主要機能

### 1. 認証・認可

- **JWT認証**: セキュアなトークンベース認証
- **RBAC**: 5つのロールによる柔軟な権限管理
- **トークンリフレッシュ**: シームレスなセッション管理

詳細: [AUTHENTICATION_FLOW.md](./AUTHENTICATION_FLOW.md)

### 2. ナレッジ管理

- CRUD操作（作成、読取、更新、削除）
- カテゴリ・タグによるフィルタリング
- 全文検索（title、summary、content）
- 承認ワークフロー

```python
# ナレッジ作成例
knowledge = client.create_knowledge(
    title="コンクリート打設の品質管理",
    summary="品質確保のためのチェックポイント",
    content="## 打設前チェック\n1. 配筋検査完了確認...",
    category="品質管理",
    tags=["コンクリート", "品質管理"],
    priority="high"
)
```

### 3. 横断検索

複数のエンティティ（ナレッジ、SOP、事故レポート等）を一度に検索：

```python
results = client.unified_search(
    query="基礎工事",
    types="knowledge,sop,incidents",
    highlight=True
)

print(f"総検索結果: {results['total_results']}件")
```

### 4. 通知システム

- リアルタイム通知配信
- 未読管理
- Email/Teams連携（設定により）

```python
# 未読通知数取得
unread_count = client.get_unread_count()

# 通知を既読にする
client.mark_notification_read(notification_id)
```

### 5. ダッシュボード・メトリクス

- KPIダッシュボード
- Prometheusメトリクス
- システム監視

```python
stats = client.get_dashboard_stats()
print(f"ナレッジ総数: {stats['counts']['total_knowledge']}")
print(f"事故ゼロ継続日数: {stats['kpis']['accident_free_days']}")
```

## APIエンドポイント概要

### 認証 (Authentication)

| エンドポイント | メソッド | 説明 |
|--------------|---------|------|
| `/api/v1/auth/login` | POST | ログイン |
| `/api/v1/auth/refresh` | POST | トークンリフレッシュ |
| `/api/v1/auth/me` | GET | ユーザー情報取得 |

### ナレッジ (Knowledge)

| エンドポイント | メソッド | 説明 |
|--------------|---------|------|
| `/api/v1/knowledge` | GET | 一覧取得 |
| `/api/v1/knowledge/{id}` | GET | 詳細取得 |
| `/api/v1/knowledge` | POST | 作成 |
| `/api/v1/knowledge/{id}` | PUT | 更新 |
| `/api/v1/knowledge/{id}` | DELETE | 削除 |

### 検索 (Search)

| エンドポイント | メソッド | 説明 |
|--------------|---------|------|
| `/api/v1/search/unified` | GET | 横断検索 |

### 通知 (Notifications)

| エンドポイント | メソッド | 説明 |
|--------------|---------|------|
| `/api/v1/notifications` | GET | 一覧取得 |
| `/api/v1/notifications/{id}/read` | PUT | 既読マーク |
| `/api/v1/notifications/unread/count` | GET | 未読数取得 |

### その他

- SOP管理: `/api/v1/sop`
- 法令管理: `/api/v1/regulations`
- 事故レポート: `/api/v1/incidents`
- 専門家相談: `/api/v1/consultations`
- 承認フロー: `/api/v1/approvals`
- ダッシュボード: `/api/v1/dashboard/stats`
- メトリクス: `/api/v1/metrics`, `/metrics`

完全なリストは [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) を参照してください。

## デモユーザー

システムには以下のデモユーザーが用意されています：

| ユーザー名 | パスワード | ロール | 説明 |
|----------|----------|-------|------|
| admin | admin123 | admin | 全権限 |
| yamada | yamada123 | construction_manager | 施工管理者 |
| partner | partner123 | partner_company | 協力会社（閲覧のみ） |

## レート制限

### 開発環境

レート制限なし

### 本番環境

| エンドポイント | 制限 |
|--------------|------|
| `/api/v1/auth/login` | 5リクエスト/分、20リクエスト/時 |
| その他 | 1000リクエスト/分、10000リクエスト/時 |

詳細: [API_DOCUMENTATION.md - レート制限](./API_DOCUMENTATION.md#レート制限)

## エラーハンドリング

すべてのエラーレスポンスは統一された形式です：

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "エラーメッセージ",
    "details": {}
  }
}
```

### 主要エラーコード

| コード | HTTPステータス | 説明 |
|-------|--------------|------|
| `VALIDATION_ERROR` | 400 | 入力検証エラー |
| `UNAUTHORIZED` | 401 | 認証失敗 |
| `TOKEN_EXPIRED` | 401 | トークン期限切れ |
| `FORBIDDEN` | 403 | 権限不足 |
| `NOT_FOUND` | 404 | リソース未発見 |
| `RATE_LIMIT_EXCEEDED` | 429 | レート制限超過 |

詳細: [API_DOCUMENTATION.md - エラーハンドリング](./API_DOCUMENTATION.md#エラーハンドリング)

## セキュリティ

### 推奨事項

1. **HTTPS必須**: 本番環境では必ずHTTPSを使用
2. **トークン管理**: Access Tokenはセキュアストレージに保存
3. **環境変数**: 認証情報は環境変数で管理
4. **パスワード**: 強力なパスワードを使用
5. **監査ログ**: すべてのアクセスをログに記録

詳細: [AUTHENTICATION_FLOW.md - セキュリティ考慮事項](./AUTHENTICATION_FLOW.md#セキュリティ考慮事項)

## トラブルシューティング

### 1. トークンが無効

**症状**: `401 INVALID_TOKEN`

**解決策**:
```python
# トークンをリフレッシュ
client.refresh_access_token()
```

### 2. 権限エラー

**症状**: `403 FORBIDDEN`

**解決策**: 適切なロールを持つユーザーでログイン

### 3. レート制限

**症状**: `429 RATE_LIMIT_EXCEEDED`

**解決策**: 指数バックオフで再試行

詳細: [AUTHENTICATION_FLOW.md - トラブルシューティング](./AUTHENTICATION_FLOW.md#トラブルシューティング)

## 開発ワークフロー

### 1. ローカル開発

```bash
# 環境変数設定
export MKS_JWT_SECRET_KEY="your-secret-key"
export MKS_ENV="development"

# サーバー起動
python app_v2.py

# Swagger UIで確認
# http://localhost:5100/api/docs
```

### 2. テスト

```bash
# 単体テストに使用例スクリプトを実行
python docs/examples/python_example.py

# またはcURLスクリプト
./docs/examples/curl_examples.sh
```

### 3. 本番デプロイ

```bash
# 環境変数設定（本番用）
export MKS_ENV="production"
export MKS_FORCE_HTTPS="true"
export MKS_HSTS_ENABLED="true"

# Gunicornで起動
gunicorn -c gunicorn.conf.py app_v2:app
```

## ベストプラクティス

### 1. エラーハンドリング

```python
try:
    knowledge = client.create_knowledge(data)
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 400:
        print("入力検証エラー:", e.response.json()["error"]["details"])
    elif e.response.status_code == 401:
        client.refresh_access_token()
        # 再試行
    else:
        raise
```

### 2. トークン自動更新

```python
class APIClient:
    def request(self, method, endpoint, **kwargs):
        try:
            return self._make_request(method, endpoint, **kwargs)
        except TokenExpiredError:
            self.refresh_access_token()
            return self._make_request(method, endpoint, **kwargs)
```

### 3. レート制限対応

```python
@retry_on_rate_limit(max_retries=5)
def api_call():
    return client.list_knowledge()
```

詳細: [API_DOCUMENTATION.md - ベストプラクティス](./API_DOCUMENTATION.md#ベストプラクティス)

## よくある質問（FAQ）

### Q1: トークンの有効期限はどのくらいですか？

A: Access Tokenは1時間、Refresh Tokenは30日間有効です。

### Q2: パスワードをリセットするには？

A: 現在、管理者にお問い合わせください。パスワードリセット機能は今後のリリースで追加予定です。

### Q3: レート制限を超えたらどうなりますか？

A: `429 Too Many Requests`エラーが返されます。`retry_after`の秒数だけ待ってから再試行してください。

### Q4: 複数のロールを持つことはできますか？

A: はい、ユーザーは複数のロールを持つことができます。権限は各ロールの権限の和集合になります。

### Q5: APIのバージョニングはどうなっていますか？

A: 現在はv1（`/api/v1/*`）のみです。破壊的変更がある場合はv2を作成します。

## サポート・お問い合わせ

### ドキュメント

- **Swagger UI**: http://localhost:5100/api/docs
- **OpenAPI仕様**: http://localhost:5100/api/openapi.yaml

### テクニカルサポート

- **Email**: support@example.com
- **GitHub Issues**: https://github.com/yourorg/mirai-knowledge-system/issues

### コミュニティ

- **ドキュメント**: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- **認証ガイド**: [AUTHENTICATION_FLOW.md](./AUTHENTICATION_FLOW.md)

## 変更履歴

### v2.0.0 (2024-01-01)

- JWT認証の実装
- RBAC（役割ベースアクセス制御）の追加
- 横断検索機能の強化
- Prometheusメトリクスの追加
- レート制限の実装
- OpenAPI 3.0.3仕様書の作成
- Swagger UI統合

### v1.0.0 (2023-12-01)

- 初版リリース
- 基本的なCRUD操作
- ナレッジ・SOP管理機能

## ライセンス

Proprietary - All rights reserved

---

**最終更新**: 2024-01-01

このドキュメントは継続的に更新されます。最新版は常にリポジトリを参照してください。
