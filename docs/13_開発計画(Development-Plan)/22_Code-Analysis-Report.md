# コード分析レポート - 本番環境移行準備

**作成日**: 2025-12-27
**バージョン**: v2.0
**対象環境**: 開発環境 → 本番環境
**分析対象コード行数**: 6,524行

---

## 1. エグゼクティブサマリー

本レポートは、建設土木ナレッジシステムの開発環境から本番環境への移行に向けた包括的なコード分析結果をまとめたものです。

### 主要な発見事項

✅ **強み**
- JWT認証とRBAC（ロールベースアクセス制御）の実装が完了
- XSS/CSRF対策を含む包括的なセキュリティヘッダーの実装
- HTTPS強制リダイレクトミドルウェアの実装
- 入力検証（Marshmallow）の実装
- レート制限（Flask-Limiter）の実装
- 監査ログ・アクセスログの記録機能

⚠️ **改善が必要な領域**
1. **セキュリティ**: デバッグログに機密情報が出力される可能性
2. **エラーハンドリング**: 一部のエラーハンドリングが不十分
3. **環境設定**: 本番環境用の秘密鍵がデフォルト値のままの可能性
4. **HTTPSチェック**: フロントエンドに`http://`ハードコードが存在しない（動的URL生成で対応済み）
5. **未実装機能**: 一部のUI機能がプレースホルダー実装のみ

---

## 2. 既存機能一覧と実装状況

### 2.1 APIエンドポイントマッピング

#### 認証系 (`/api/v1/auth/*`)

| エンドポイント | メソッド | 実装状態 | 権限 | 備考 |
|--------------|---------|---------|------|------|
| `/api/v1/auth/login` | POST | ✅ 完全実装 | Public | レート制限: 5回/分、20回/時 |
| `/api/v1/auth/refresh` | POST | ✅ 完全実装 | Refresh Token | リフレッシュトークン更新 |
| `/api/v1/auth/me` | GET | ✅ 完全実装 | JWT必須 | ユーザー情報取得 |

**セキュリティ機能**:
- bcryptによるパスワードハッシュ化
- レガシーSHA256サポート（後方互換性のみ、警告あり）
- トークンの自動リフレッシュ機能（フロントエンド実装済み）
- アクセストークン有効期限: 1時間
- リフレッシュトークン有効期限: 30日

#### ナレッジ管理 (`/api/v1/knowledge/*`)

| エンドポイント | メソッド | 実装状態 | 権限 | 備考 |
|--------------|---------|---------|------|------|
| `/api/v1/knowledge` | GET | ✅ 完全実装 | `knowledge.read` | 検索・フィルタリング対応 |
| `/api/v1/knowledge/<id>` | GET | ✅ 完全実装 | `knowledge.read` | 詳細情報取得 |
| `/api/v1/knowledge` | POST | ✅ 完全実装 | `knowledge.create` | 入力検証付き |

**機能**:
- カテゴリフィルタリング（category）
- 全文検索（title, summary, content対応）
- タグ検索（複数タグのOR検索）
- ハイライト機能（検索語のマーキング）
- 関連度スコアリング（title: 1.0, summary: 0.7, content: 0.5）
- 通知作成（承認待ち通知を自動生成）

#### 横断検索 (`/api/v1/search/*`)

| エンドポイント | メソッド | 実装状態 | 権限 | 備考 |
|--------------|---------|---------|------|------|
| `/api/v1/search/unified` | GET | ✅ 完全実装 | JWT必須 | 複数エンティティ横断検索 |

**対応エンティティ**:
- knowledge（ナレッジ）
- sop（標準施工手順）
- incidents（事故・ヒヤリレポート）
- consultations（専門家相談）※データ構造定義済み
- regulations（法令・規格）※データ構造定義済み

#### 通知機能 (`/api/v1/notifications/*`)

| エンドポイント | メソッド | 実装状態 | 権限 | 備考 |
|--------------|---------|---------|------|------|
| `/api/v1/notifications` | GET | ✅ 完全実装 | JWT必須 | ユーザー・ロール別通知取得 |
| `/api/v1/notifications/<id>/read` | PUT | ✅ 完全実装 | JWT必須 | 既読マーク機能 |
| `/api/v1/notifications/unread/count` | GET | ✅ 完全実装 | JWT必須 | 未読数カウント |

**機能**:
- ユーザー指定配信（`target_users`）
- ロール指定配信（`target_roles`）
- 優先度設定（low, medium, high）
- 関連エンティティリンク
- 既読管理（複数ユーザー対応）

#### その他のエンドポイント

| エンドポイント | メソッド | 実装状態 | 権限 | 備考 |
|--------------|---------|---------|------|------|
| `/api/v1/sop` | GET | ✅ 完全実装 | `sop.read` | 標準施工手順一覧 |
| `/api/v1/dashboard/stats` | GET | ✅ 完全実装 | JWT必須 | ダッシュボード統計 |
| `/api/v1/approvals` | GET | ✅ 完全実装 | JWT必須 | 承認フロー一覧 |
| `/api/v1/metrics` | GET | ✅ 完全実装 | Public | Prometheus互換メトリクス |

### 2.2 権限設計（RBAC）

#### ロール定義

| ロール | 権限レベル | 主要権限 |
|--------|-----------|---------|
| `admin` | 最高（4） | 全権限（`*`） |
| `construction_manager` | 3 | ナレッジ作成・更新、承認申請、相談作成 |
| `quality_assurance` | 2 | ナレッジ承認、SOP更新、承認実行 |
| `safety_officer` | - | 事故報告作成・更新、ナレッジ閲覧 |
| `partner_company` | 最低（1） | ナレッジ・SOP・事故報告の閲覧のみ |

#### 権限チェック実装

**バックエンド**:
```python
@check_permission('knowledge.create')  # デコレータベース
def create_knowledge():
    # 権限チェック後に処理実行
```

**フロントエンド**:
```javascript
// RBAC UI制御
<button data-required-role="construction_manager">新規ナレッジ登録</button>
<button data-permission="knowledge.approve">承認</button>
```

### 2.3 フロントエンド機能

#### 実装済み機能

1. **認証・セッション管理**
   - ログイン/ログアウト
   - トークン自動リフレッシュ（401エラー時）
   - ユーザー情報表示
   - RBAC UI制御（権限に応じた表示/非表示）

2. **ナレッジ管理**
   - 一覧表示（カード形式）
   - 検索・フィルタリング
   - 詳細表示（別ページ遷移）
   - 新規登録モーダル（簡易版）
   - 編集権限チェック（作成者または管理者のみ）

3. **通知機能**
   - 未読通知バッジ
   - 通知パネル（ドロップダウン）
   - 既読マーク
   - 5分ごとの自動ポーリング
   - 相対時間表示（「3分前」など）

4. **セキュリティ対策**
   - XSS対策（DOM API使用、innerHTML禁止）
   - HTMLエスケープ関数
   - 動的URL生成（HTTP/HTTPS対応）
   - CSP（Content Security Policy）対応

#### プレースホルダー実装（未実装機能）

以下の機能は`alert()`や`console.log()`による仮実装のみ:

- PDF生成・ダウンロード
- ダッシュボード共有（メール送信）
- 朝礼用サマリ生成
- 配信申請処理
- 改訂提案フォーム
- 点検表開始
- 影響評価記録
- 是正措置登録
- 再発防止策作成
- 専門家相談の詳細フォーム
- 資料添付機能
- 差分表示・バージョン比較

---

## 3. データフロー分析

### 3.1 認証フロー

```
[ログイン画面]
    ↓ POST /api/v1/auth/login
    ├─ ユーザー名検証
    ├─ パスワード検証（bcrypt）
    ├─ アクセストークン生成（1時間有効）
    ├─ リフレッシュトークン生成（30日有効）
    └─ ユーザー情報返却
         ↓
[ダッシュボード]
    ↓ トークン期限切れ（401エラー）
    ├─ POST /api/v1/auth/refresh（自動リトライ）
    ├─ 新しいアクセストークン取得
    └─ リクエスト再実行
```

### 3.2 ナレッジ登録フロー

```
[新規ナレッジ登録ボタン]
    ↓ checkPermission('construction_manager')
    ├─ 権限あり → モーダル表示
    └─ 権限なし → alert('権限がありません')
         ↓
[入力フォーム]
    ↓ POST /api/v1/knowledge
    ├─ @validate_request(KnowledgeCreateSchema)
    ├─ title（1-200文字）
    ├─ summary（1-500文字）
    ├─ content（1-50,000文字）
    ├─ category（選択肢検証）
    ├─ tags（最大20個、各30文字以内）
    └─ status='draft'で保存
         ↓
[通知生成]
    ├─ create_notification()
    ├─ target_roles=['admin', 'quality_assurance']
    ├─ type='approval_required'
    └─ 承認者に通知配信
```

### 3.3 検索フロー

```
[検索入力]
    ↓ GET /api/v1/knowledge?search=<query>&highlight=true
    ├─ search_in_fields(item, query, ['title', 'summary', 'content'])
    ├─ 関連度スコア計算
    │   ├─ title: 1.0
    │   ├─ summary: 0.7
    │   └─ content: 0.5
    ├─ highlight_text()（ハイライトマーク挿入）
    └─ スコア順ソート
         ↓
[検索結果表示]
    ├─ matched_fields表示
    ├─ relevance_score表示
    └─ <mark>タグでハイライト
```

### 3.4 データ永続化

**現在の実装**（JSONファイルベース）:
```
backend/data/
├── users.json          # ユーザー情報（パスワードハッシュ含む）
├── knowledge.json      # ナレッジデータ
├── sop.json           # 標準施工手順
├── incidents.json     # 事故・ヒヤリレポート
├── consultations.json # 専門家相談
├── approvals.json     # 承認フロー
├── notifications.json # 通知データ
└── access_logs.json   # アクセスログ
```

**PostgreSQL移行準備完了**:
- `models.py`: SQLAlchemy 2.0モデル定義済み
- スキーマ設計: public, auth, audit
- マイグレーションツール: `migrate_json_to_postgres.py`

---

## 4. 依存関係分析

### 4.1 バックエンド依存関係

```
Flask==3.0.0                  # Webフレームワーク
Flask-CORS==4.0.0             # CORS対応
Flask-JWT-Extended==4.6.0     # JWT認証
Flask-Limiter==3.5.0          # レート制限
bcrypt==4.1.2                 # パスワードハッシュ化
marshmallow==3.20.1           # 入力検証
psutil==5.9.6                 # システムメトリクス
python-dotenv==1.0.0          # 環境変数管理
SQLAlchemy==2.0.23            # ORM（PostgreSQL移行用）
psycopg2-binary==2.9.9        # PostgreSQLドライバ
```

### 4.2 潜在的な依存関係の問題

❌ **見つかった問題**:
1. **Redisの設定がオプション**: レート制限がメモリベース（再起動でリセット）
2. **テストフレームワーク**: requirements.txtに含まれているが、テストコードは未作成

✅ **問題なし**:
- 全ての依存関係が最新の安定版
- セキュリティ脆弱性のあるバージョンは使用していない

---

## 5. 潜在的なバグと改善点

### 5.1 セキュリティリスク

#### 🔴 高優先度

1. **デバッグログに機密情報が出力される可能性**

   **場所**: `backend/app_v2.py`
   ```python
   # 行365-392
   print(f'[DEBUG] check_permission: user_id={user_id_int}, required={required_permission}')
   print(f'[DEBUG] User not found: {current_user_id}')
   print(f'[DEBUG] User permissions: {permissions}')
   ```

   **リスク**: 本番環境でユーザーIDや権限情報がログに記録される

   **推奨対応**:
   ```python
   # 環境変数で制御
   if os.environ.get('MKS_DEBUG', 'false').lower() in ('true', '1', 'yes'):
       print(f'[DEBUG] check_permission: user_id={user_id_int}')
   ```

2. **JWT秘密鍵がデフォルト値のままの可能性**

   **場所**: `backend/app_v2.py` 行116
   ```python
   JWT_SECRET = 'mirai-knowledge-system-jwt-secret-key-2025'
   app.config['JWT_SECRET_KEY'] = os.environ.get('MKS_JWT_SECRET_KEY', JWT_SECRET)
   ```

   **リスク**: 環境変数が設定されていない場合、既知の秘密鍵でトークンが生成される

   **推奨対応**:
   ```python
   # 本番環境では環境変数必須
   if IS_PRODUCTION:
       jwt_secret = os.environ.get('MKS_JWT_SECRET_KEY')
       if not jwt_secret or jwt_secret == JWT_SECRET:
           raise ValueError('MKS_JWT_SECRET_KEY must be set in production')
   ```

3. **レガシーSHA256パスワードハッシュのサポート**

   **場所**: `backend/app_v2.py` 行316-320
   ```python
   # レガシーSHA256サポート（後方互換性）
   print(f'[WARNING] Using legacy SHA256 verification for password.')
   legacy_hash = hashlib.sha256(password.encode()).hexdigest()
   return legacy_hash == password_hash
   ```

   **リスク**: SHA256はパスワードハッシュとして脆弱（レインボーテーブル攻撃）

   **推奨対応**:
   - 全ユーザーのパスワードをbcryptに移行
   - 移行後、レガシーサポートを削除
   - 移行スクリプトの実行を本番移行時に実施

#### 🟡 中優先度

4. **アクセスログにIPアドレスが記録されるがGDPR対応が不明確**

   **場所**: `backend/app_v2.py` 行444
   ```python
   'ip_address': request.remote_addr,
   'user_agent': request.headers.get('User-Agent'),
   ```

   **推奨対応**:
   - IPアドレスの保存期間を明示（例: 90日）
   - ログローテーション・自動削除の実装
   - プライバシーポリシーへの記載

5. **CORS設定が環境変数ベースだが検証なし**

   **場所**: `backend/app_v2.py` 行96
   ```python
   allowed_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:5000').split(',')
   ```

   **推奨対応**:
   ```python
   # 本番環境では必ず設定
   if IS_PRODUCTION and 'localhost' in allowed_origins:
       raise ValueError('localhost in CORS_ORIGINS is not allowed in production')
   ```

### 5.2 エラーハンドリングの改善

#### 🟡 中優先度

6. **例外ハンドリングが不完全**

   **場所**: `backend/migrate_json_to_postgres.py` 行21
   ```python
   except:
       return []
   ```

   **問題**: すべての例外を無視するため、エラー原因が不明

   **推奨対応**:
   ```python
   except FileNotFoundError:
       return []
   except json.JSONDecodeError as e:
       print(f'[ERROR] Invalid JSON: {e}')
       return []
   except Exception as e:
       print(f'[ERROR] Unexpected error: {e}')
       raise
   ```

7. **ユーザー取得時のエラーハンドリング**

   **場所**: `backend/app_v2.py` 行547-553
   ```python
   users = load_users()
   user = next((u for u in users if u['id'] == current_user_id), None)

   if not user:
       return jsonify({'success': False, 'error': 'User not found'}), 404
   ```

   **問題**: `current_user_id`の型変換エラーの可能性

   **推奨対応**:
   ```python
   try:
       user_id_int = int(current_user_id)
   except (ValueError, TypeError):
       return jsonify({'success': False, 'error': 'Invalid user ID'}), 400
   ```

### 5.3 パフォーマンス・スケーラビリティ

#### 🟢 低優先度（将来対応）

8. **JSONファイルベースのデータ保存**

   **問題点**:
   - ファイル全体を読み込むため、大量データで遅延
   - 同時書き込みでデータ破損のリスク
   - 検索パフォーマンスが低い（O(n)）

   **推奨対応**:
   - PostgreSQLへの移行（モデル定義済み）
   - 全文検索インデックスの作成
   - トランザクション管理の実装

9. **検索処理が非効率**

   **場所**: `backend/app_v2.py` 行638-665
   ```python
   for k in filtered:
       if query_lower in str(k.get(field, '')).lower():
           # マッチング処理
   ```

   **問題**: 全データをメモリに読み込んで線形探索

   **推奨対応**:
   - PostgreSQLの全文検索（GINインデックス）
   - Elasticsearch導入（将来検討）

10. **通知ポーリングが5分間隔**

    **場所**: `webui/notifications.js` 行157-159
    ```javascript
    setInterval(() => {
      loadUnreadNotificationCount();
    }, 5 * 60 * 1000);
    ```

    **問題**: リアルタイム性が低い

    **推奨対応**:
    - WebSocketまたはServer-Sent Events（SSE）の導入
    - プッシュ通知の実装

---

## 6. 本番環境移行時のチェックリスト

### 6.1 HTTPからHTTPSへの移行

#### ✅ 実装済み

- [x] HTTPS強制リダイレクトミドルウェア（`HTTPSRedirectMiddleware`）
- [x] 動的URL生成（フロントエンド）
  ```javascript
  const API_BASE = `${window.location.origin}/api/v1`;
  ```
- [x] HSTS（HTTP Strict Transport Security）ヘッダー対応
- [x] upgrade-insecure-requests CSPディレクティブ

#### ⚠️ 移行時の確認事項

1. **環境変数の設定**
   ```bash
   # .env.production
   MKS_ENV=production
   MKS_FORCE_HTTPS=true
   MKS_TRUST_PROXY_HEADERS=true  # Nginx経由の場合
   MKS_HSTS_ENABLED=true
   MKS_HSTS_MAX_AGE=31536000  # 1年
   ```

2. **Nginx設定例**
   ```nginx
   server {
       listen 443 ssl http2;
       server_name api.example.com;

       ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;

       # セキュリティヘッダー
       add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

       # プロキシ設定
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }

   # HTTPからHTTPSへリダイレクト
   server {
       listen 80;
       server_name api.example.com;
       return 301 https://$server_name$request_uri;
   }
   ```

3. **SSL証明書の取得**
   ```bash
   # Let's Encrypt（推奨）
   sudo certbot certonly --nginx -d api.example.com -d app.example.com

   # 自動更新設定
   sudo certbot renew --dry-run
   ```

### 6.2 環境依存の設定確認

#### 🔴 必須設定

| 項目 | 環境変数 | デフォルト値 | 本番推奨値 |
|------|---------|------------|----------|
| 環境モード | `MKS_ENV` | `development` | `production` |
| デバッグモード | `MKS_DEBUG` | `false` | `false` |
| JWT秘密鍵 | `MKS_JWT_SECRET_KEY` | 固定値（危険） | 32文字以上のランダム文字列 |
| アプリ秘密鍵 | `MKS_SECRET_KEY` | なし | 32文字以上のランダム文字列 |
| HTTPS強制 | `MKS_FORCE_HTTPS` | `false` | `true` |
| CORS許可オリジン | `MKS_CORS_ORIGINS` | `http://localhost:5000` | `https://example.com` |

#### 🟡 推奨設定

| 項目 | 環境変数 | デフォルト値 | 本番推奨値 |
|------|---------|------------|----------|
| HSTS有効化 | `MKS_HSTS_ENABLED` | `false` | `true` |
| HSTS有効期間 | `MKS_HSTS_MAX_AGE` | `31536000` | `31536000`（1年） |
| データディレクトリ | `MKS_DATA_DIR` | `backend/data` | `/var/lib/mirai-knowledge-system/data` |
| ログファイル | `MKS_LOG_FILE` | なし | `/var/log/mirai-knowledge-system/app.log` |

#### 秘密鍵の生成方法

```bash
# JWT秘密鍵
python3 -c "import secrets; print(secrets.token_hex(32))"

# アプリケーション秘密鍵
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 6.3 セキュリティ強化チェックリスト

- [ ] JWT秘密鍵を環境変数で設定（デフォルト値禁止）
- [ ] HTTPS強制リダイレクトの有効化
- [ ] HSTS有効化（最低1年）
- [ ] CSP（Content Security Policy）の本番設定確認
- [ ] CORS許可オリジンの制限（localhost除外）
- [ ] デバッグログの無効化
- [ ] レート制限の確認（Redis推奨）
- [ ] アクセスログのローテーション設定
- [ ] ファイアウォール設定（必要なポートのみ開放）
- [ ] 定期的なセキュリティアップデート計画

### 6.4 パフォーマンス・スケーラビリティ

- [ ] Gunicorn設定（ワーカー数 = CPU数 × 2 + 1）
- [ ] PostgreSQL移行の検討（JSONファイルの限界）
- [ ] Redisの導入（レート制限・セッション管理）
- [ ] 静的ファイルのCDN配信
- [ ] データベース接続プールの設定
- [ ] 監視ツールの導入（Prometheus + Grafana）
- [ ] ログ集約システム（ELK Stack等）

### 6.5 運用・保守

- [ ] バックアップスクリプトの作成
- [ ] リストア手順の確認
- [ ] ログローテーション設定（logrotate）
- [ ] システムヘルスチェックエンドポイントの確認
- [ ] インシデント対応手順書の作成
- [ ] ロールバック手順の確認
- [ ] 定期メンテナンス計画

---

## 7. セキュリティリスク評価

### 7.1 OWASP Top 10 (2021) 対応状況

| リスク | 対応状況 | 実装内容 |
|-------|---------|---------|
| A01: アクセス制御の不備 | ✅ 対応済み | JWT + RBAC実装、権限チェックデコレータ |
| A02: 暗号化の失敗 | ⚠️ 一部対応 | bcrypt導入、HTTPS対応、レガシーSHA256削除必要 |
| A03: インジェクション | ✅ 対応済み | Marshmallow入力検証、SQLAlchemy ORM（準備済み） |
| A04: 安全でない設計 | ✅ 対応済み | レート制限、CSRF対策、監査ログ |
| A05: セキュリティ設定ミス | ⚠️ 要確認 | デバッグログ削除、秘密鍵検証強化必要 |
| A06: 脆弱なコンポーネント | ✅ 対応済み | 最新の安定版ライブラリ使用 |
| A07: 認証・認可の失敗 | ✅ 対応済み | JWT有効期限、リフレッシュトークン、レート制限 |
| A08: ソフトウェア・データ整合性 | ⚠️ 一部対応 | SRI未実装、署名検証なし |
| A09: セキュリティログ・監視 | ✅ 対応済み | アクセスログ、監査ログ、メトリクス |
| A10: サーバーサイドリクエストフォージェリ | N/A | 外部APIリクエストなし |

### 7.2 追加のセキュリティ推奨事項

1. **Rate Limiting強化**
   - 現在: メモリベース（再起動でリセット）
   - 推奨: Redis導入で永続化

2. **Content Security Policy強化**
   - 現在: `script-src 'self'`（本番）
   - 推奨: nonceまたはhashベースのCSP

3. **APIレスポンスの署名**
   - 中間者攻撃対策としてJWS（JSON Web Signature）の導入検討

4. **依存関係の定期スキャン**
   ```bash
   pip install safety
   safety check
   ```

---

## 8. 推奨される修正事項（優先順位付き）

### 🔴 本番リリース前に必須

1. **JWT秘密鍵のバリデーション強化**
   - ファイル: `backend/app_v2.py`
   - 実装: 本番環境でデフォルト値を禁止

2. **デバッグログの削除**
   - ファイル: `backend/app_v2.py`
   - 実装: 環境変数で制御

3. **レガシーSHA256パスワードハッシュの無効化**
   - ファイル: `backend/app_v2.py`
   - 実装: 全ユーザーをbcryptに移行後、削除

4. **環境変数の検証スクリプト作成**
   ```python
   # scripts/validate_env.py
   def validate_production_env():
       required_vars = ['MKS_JWT_SECRET_KEY', 'MKS_SECRET_KEY', 'MKS_CORS_ORIGINS']
       for var in required_vars:
           if not os.environ.get(var):
               raise ValueError(f'{var} is required in production')
   ```

### 🟡 本番リリース後1ヶ月以内

5. **PostgreSQL移行**
   - 理由: JSONファイルはスケールしない
   - 実装: `models.py`のモデル使用、マイグレーションツール実行

6. **Redis導入**
   - 理由: レート制限の永続化、セッション管理
   - 実装: `MKS_REDIS_URL`環境変数設定

7. **監視システム導入**
   - Prometheus + Grafana
   - `/api/v1/metrics`エンドポイント活用

8. **自動テスト追加**
   - pytest導入（requirements.txt済み）
   - カバレッジ目標: 80%以上

### 🟢 将来的な改善

9. **WebSocket/SSE導入**
   - リアルタイム通知
   - 現在の5分ポーリングから置き換え

10. **全文検索エンジン導入**
    - Elasticsearchまたは PostgreSQL GINインデックス
    - 検索パフォーマンス向上

11. **ファイルアップロード機能**
    - 添付ファイル機能（現在未実装）
    - S3互換ストレージ連携

---

## 9. データ移行計画

### 9.1 JSONからPostgreSQLへの移行手順

#### フェーズ1: 準備（移行前）

1. **バックアップ作成**
   ```bash
   tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz backend/data/
   ```

2. **PostgreSQL環境構築**
   ```bash
   # Docker Compose推奨
   docker-compose up -d postgres
   ```

3. **マイグレーション実行（テスト環境）**
   ```bash
   python backend/migrate_json_to_postgres.py
   ```

4. **データ整合性チェック**
   ```sql
   SELECT COUNT(*) FROM public.knowledge;
   SELECT COUNT(*) FROM auth.users;
   ```

#### フェーズ2: 移行実行（本番）

1. **メンテナンスモード開始**
   - サービス停止または読み取り専用モード

2. **最終バックアップ**
   ```bash
   pg_dump -h localhost -U postgres mirai_knowledge > backup_final.sql
   ```

3. **マイグレーション実行**
   ```bash
   MKS_ENV=production python backend/migrate_json_to_postgres.py
   ```

4. **検証**
   - レコード数確認
   - サンプルデータの整合性確認

5. **アプリケーション切り替え**
   ```bash
   # 環境変数変更
   MKS_DATABASE_URL=postgresql://user:pass@localhost:5432/mirai_knowledge
   ```

#### フェーズ3: 移行後

1. **旧JSONファイルの保存**
   ```bash
   mv backend/data backend/data_archive_$(date +%Y%m%d)
   ```

2. **監視強化**
   - データベース接続数
   - クエリパフォーマンス
   - エラーログ

3. **ロールバック手順確認**
   - JSONファイルに戻す手順書

---

## 10. テスト計画（今後の実装）

### 10.1 推奨されるテスト種別

#### 単体テスト（Unit Test）

```python
# tests/test_auth.py
def test_login_success(client):
    response = client.post('/api/v1/auth/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json['data']

def test_login_invalid_password(client):
    response = client.post('/api/v1/auth/login', json={
        'username': 'admin',
        'password': 'wrong'
    })
    assert response.status_code == 401
```

#### 統合テスト（Integration Test）

```python
# tests/test_knowledge_workflow.py
def test_knowledge_creation_workflow(client, auth_headers):
    # 1. ナレッジ作成
    response = client.post('/api/v1/knowledge',
        headers=auth_headers,
        json={'title': 'Test', 'summary': 'Test', ...})
    knowledge_id = response.json['data']['id']

    # 2. 通知が生成されたか確認
    response = client.get('/api/v1/notifications', headers=auth_headers)
    assert any(n['related_entity_id'] == knowledge_id for n in response.json['data'])
```

#### パフォーマンステスト（Load Test）

```python
# tests/locustfile.py
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def search_knowledge(self):
        self.client.get("/api/v1/knowledge?search=test",
            headers={"Authorization": f"Bearer {self.token}"})
```

#### セキュリティテスト

```bash
# OWASP ZAP
docker run -t owasp/zap2docker-stable zap-baseline.py -t https://api.example.com

# SQLインジェクション検証（SQLAlchemy使用で安全）
curl -X POST https://api.example.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin' OR '1'='1", "password": "test"}'
```

---

## 11. まとめと推奨アクション

### 11.1 システムの成熟度

| 領域 | 成熟度 | 備考 |
|------|-------|------|
| 認証・認可 | ⭐⭐⭐⭐☆ | JWT + RBAC実装済み、秘密鍵強化必要 |
| セキュリティ | ⭐⭐⭐☆☆ | HTTPS対応済み、デバッグログ削除必要 |
| API設計 | ⭐⭐⭐⭐☆ | RESTful設計、入力検証実装済み |
| フロントエンド | ⭐⭐⭐☆☆ | 基本機能実装済み、一部プレースホルダー |
| データ管理 | ⭐⭐☆☆☆ | JSONベース、PostgreSQL移行推奨 |
| 監視・運用 | ⭐⭐⭐☆☆ | メトリクス実装済み、監視ツール未導入 |
| テスト | ⭐☆☆☆☆ | フレームワーク導入済み、テストコード未作成 |

### 11.2 本番リリース判定

#### ✅ リリース可能（条件付き）

以下の**必須修正**を実施後、本番環境への移行が可能:

1. JWT秘密鍵のバリデーション強化
2. デバッグログの削除
3. 環境変数の適切な設定
4. HTTPS環境の構築
5. バックアップ・リストア手順の確認

#### ⚠️ リリース後の早期対応

1. PostgreSQL移行（1ヶ月以内）
2. 自動テストの追加（2週間以内）
3. 監視システム導入（2週間以内）

### 11.3 次のステップ

#### 即時対応（本日〜3日以内）

1. `scripts/validate_env.py` 作成
2. デバッグログの環境変数制御化
3. `.env.production` テンプレートの確認

#### 短期対応（1週間以内）

4. テストコードの作成開始
5. PostgreSQL移行のリハーサル（開発環境）
6. 監視ダッシュボードのプロトタイプ作成

#### 中期対応（1ヶ月以内）

7. PostgreSQL本番移行
8. Redis導入
9. 自動テストカバレッジ80%達成
10. 未実装機能のロードマップ策定

---

## 付録A: ファイル一覧

### バックエンド

```
backend/
├── app_v2.py                    # メインアプリケーション（1,389行）
├── models.py                    # SQLAlchemyモデル（356行）
├── schemas.py                   # Marshmallowスキーマ（124行）
├── requirements.txt             # 依存関係
├── .env.example                 # 開発環境設定例
├── .env.production.example      # 本番環境設定例
└── data/                        # JSONデータストレージ
    ├── users.json
    ├── knowledge.json
    ├── sop.json
    ├── incidents.json
    ├── consultations.json
    ├── approvals.json
    ├── notifications.json
    └── access_logs.json
```

### フロントエンド

```
webui/
├── index.html                   # ダッシュボード（460行）
├── login.html                   # ログイン画面（440行）
├── app.js                       # メインJavaScript（890行）
├── notifications.js             # 通知機能（165行）
├── actions.js                   # アクション関数（182行）
├── search-detail.html           # 検索詳細
├── sop-detail.html              # SOP詳細
├── incident-detail.html         # 事故レポート詳細
├── law-detail.html              # 法令詳細
├── expert-consult.html          # 専門家相談
└── admin.html                   # 管理画面
```

### 総コード行数

- **バックエンド**: 約1,900行（Python）
- **フロントエンド**: 約4,600行（HTML + JavaScript）
- **合計**: 約6,500行

---

## 付録B: 環境変数一覧

| 環境変数 | 必須 | デフォルト値 | 説明 |
|---------|-----|------------|------|
| `MKS_ENV` | ○ | `development` | 環境モード（development/production） |
| `MKS_DEBUG` | - | `false` | デバッグモード |
| `MKS_SECRET_KEY` | ○ | - | Flask秘密鍵 |
| `MKS_JWT_SECRET_KEY` | ○ | 固定値 | JWT秘密鍵 |
| `MKS_FORCE_HTTPS` | - | `false` | HTTPS強制リダイレクト |
| `MKS_TRUST_PROXY_HEADERS` | - | `false` | プロキシヘッダー信頼 |
| `MKS_HSTS_ENABLED` | - | `false` | HSTS有効化 |
| `MKS_HSTS_MAX_AGE` | - | `31536000` | HSTS有効期間（秒） |
| `MKS_HSTS_INCLUDE_SUBDOMAINS` | - | `true` | HSTSサブドメイン適用 |
| `MKS_CORS_ORIGINS` | ○ | `http://localhost:5000` | CORS許可オリジン |
| `MKS_DATA_DIR` | - | `backend/data` | データディレクトリ |
| `MKS_LOG_FILE` | - | - | ログファイルパス |
| `MKS_LOG_LEVEL` | - | `INFO` | ログレベル |
| `MKS_DATABASE_URL` | - | - | PostgreSQL接続URL |
| `MKS_REDIS_URL` | - | - | Redis接続URL |

---

## 付録C: APIエンドポイント一覧表

| エンドポイント | メソッド | 権限 | レート制限 | 実装状態 |
|--------------|---------|------|----------|---------|
| `/api/v1/auth/login` | POST | Public | 5/分, 20/時 | ✅ |
| `/api/v1/auth/refresh` | POST | Refresh Token | - | ✅ |
| `/api/v1/auth/me` | GET | JWT | - | ✅ |
| `/api/v1/knowledge` | GET | `knowledge.read` | - | ✅ |
| `/api/v1/knowledge/<id>` | GET | `knowledge.read` | - | ✅ |
| `/api/v1/knowledge` | POST | `knowledge.create` | - | ✅ |
| `/api/v1/search/unified` | GET | JWT | - | ✅ |
| `/api/v1/notifications` | GET | JWT | - | ✅ |
| `/api/v1/notifications/<id>/read` | PUT | JWT | - | ✅ |
| `/api/v1/notifications/unread/count` | GET | JWT | - | ✅ |
| `/api/v1/sop` | GET | `sop.read` | - | ✅ |
| `/api/v1/dashboard/stats` | GET | JWT | - | ✅ |
| `/api/v1/approvals` | GET | JWT | - | ✅ |
| `/api/v1/metrics` | GET | Public | - | ✅ |

---

**レポート作成者**: Claude (Anthropic AI)
**レビュー推奨者**: 開発リーダー、セキュリティ担当者、インフラ担当者
**次回レビュー日**: 本番リリース後1ヶ月
