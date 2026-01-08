# タスクテンプレート - Task Templates

本番環境でよくあるタスクの実行テンプレート集です。
各テンプレートをコピーしてClaude Codeに指示してください。

---

## 📊 テンプレート一覧

| カテゴリ | タスク名 | リスク | 所要時間 |
|---------|---------|--------|----------|
| 🗄️ データベース | [PostgreSQL移行](#postgresql移行タスク) | High | 2-4時間 |
| 🗄️ データベース | [データバックアップ](#データバックアップタスク) | Low | 10分 |
| 🗄️ データベース | [データリストア](#データリストアタスク) | High | 30分 |
| 🔒 セキュリティ | [依存関係更新](#セキュリティ更新タスク) | Medium | 30分 |
| 🔒 セキュリティ | [パスワードポリシー変更](#パスワードポリシー変更タスク) | Low | 15分 |
| ⚡ パフォーマンス | [N+1クエリ最適化](#パフォーマンスチューニングタスク) | Medium | 1-2時間 |
| ⚡ パフォーマンス | [インデックス追加](#インデックス追加タスク) | Low | 30分 |
| 🐛 バグ修正 | [APIエラー修正](#バグ修正タスク) | Medium | 1時間 |
| 🐛 バグ修正 | [フロントエンド不具合](#フロントエンドバグ修正タスク) | Low | 30分 |
| ✨ 機能追加 | [新規APIエンドポイント](#機能追加タスク) | Medium | 2-3時間 |
| ✨ 機能追加 | [UI改善](#ui改善タスク) | Low | 1時間 |

---

## 🗄️ データベース移行タスク

### PostgreSQL移行タスク

**リスク:** High
**所要時間:** 2-4時間
**前提条件:** PostgreSQL 15+インストール済み

```markdown
## タスク: PostgreSQL移行

### ゴール
JSON形式のデータストレージからPostgreSQLへ移行する

### 事前確認
- [ ] PostgreSQLサーバーが稼働している（psql --version）
- [ ] バックアップが24時間以内に取得されている
- [ ] テスト環境で移行スクリプトを検証済み
- [ ] ダウンタイム計画をユーザーに通知済み

### 実行手順

#### Step 1: データベース準備
```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend

# PostgreSQL接続確認
psql -h localhost -U postgres -c "SELECT version();"

# データベース作成
psql -h localhost -U postgres -c "CREATE DATABASE mirai_knowledge_db;"
psql -h localhost -U postgres -c "CREATE USER mks_user WITH PASSWORD 'secure_password';"
psql -h localhost -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE mirai_knowledge_db TO mks_user;"
```

#### Step 2: スキーマ作成
```bash
# マイグレーションスクリプト実行
python -c "
from app_v2 import app, db
with app.app_context():
    db.create_all()
    print('Database schema created successfully')
"
```

#### Step 3: データ移行
```bash
# JSONからPostgreSQLへデータインポート
python scripts/migrate_json_to_postgresql.py \
    --source data/ \
    --target postgresql://mks_user:secure_password@localhost/mirai_knowledge_db \
    --dry-run  # まずドライラン

# 実際の移行（ドライラン確認後）
python scripts/migrate_json_to_postgresql.py \
    --source data/ \
    --target postgresql://mks_user:secure_password@localhost/mirai_knowledge_db
```

#### Step 4: データ検証
```bash
# レコード数確認
python -c "
from app_v2 import app, db, User, Knowledge
with app.app_context():
    print(f'Users: {User.query.count()}')
    print(f'Knowledges: {Knowledge.query.count()}')
"

# サンプルデータ確認
psql -h localhost -U mks_user -d mirai_knowledge_db -c "SELECT COUNT(*) FROM users;"
psql -h localhost -U mks_user -d mirai_knowledge_db -c "SELECT COUNT(*) FROM knowledges;"
```

#### Step 5: アプリケーション設定変更
```bash
# .env.production を更新（直接編集せず、新規作成）
# DATABASE_URL=postgresql://mks_user:secure_password@localhost/mirai_knowledge_db
```

#### Step 6: テスト
```bash
# テストスイート実行
pytest tests/ -v --cov=. --cov-report=term

# 統合テスト
pytest tests/test_integration.py -v
```

#### Step 7: 本番適用
```bash
# サービス再起動
sudo systemctl restart mirai-knowledge-system

# ヘルスチェック
curl https://localhost:443/health

# 動作確認
curl -X POST https://localhost:443/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"test"}'
```

### ロールバック手順
```bash
# Step 1: サービス停止
sudo systemctl stop mirai-knowledge-system

# Step 2: .env.production を元に戻す
# DATABASE_URL=sqlite:///data/app.db  # または JSON形式

# Step 3: サービス起動
sudo systemctl start mirai-knowledge-system
```

### 成功基準
- [ ] 全データが正常に移行された（レコード数一致）
- [ ] テストスイートが全てパス
- [ ] API動作確認完了
- [ ] パフォーマンスが改善または同等
```

---

## 🔒 セキュリティ更新タスク

### 依存関係更新タスク

**リスク:** Medium
**所要時間:** 30分

```markdown
## タスク: 依存関係のセキュリティ更新

### ゴール
脆弱性のある依存パッケージを安全に更新する

### 事前確認
- [ ] 現在のテストスイートが全てパス
- [ ] requirements.txt のバックアップ取得済み

### 実行手順

#### Step 1: 脆弱性スキャン
```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend

# 脆弱性チェック（pip-audit使用）
pip install pip-audit
pip-audit

# または safety使用
pip install safety
safety check
```

#### Step 2: 更新対象の特定
```bash
# アップデート可能なパッケージ確認
pip list --outdated

# 重要度の高いセキュリティアップデートを優先
# Critical > High > Medium > Low
```

#### Step 3: 段階的更新
```bash
# パターン1: 単一パッケージ更新（推奨）
pip install --upgrade <package_name>==<new_version>

# パターン2: 全パッケージ更新（リスク高）
pip install --upgrade -r requirements.txt
```

#### Step 4: requirements.txt更新
```bash
pip freeze > requirements.txt
```

#### Step 5: テスト実行
```bash
# 全テストスイート実行
pytest tests/ -v --cov=. --cov-report=term

# 特定機能のテスト
pytest tests/test_auth.py -v
pytest tests/test_knowledge.py -v
```

#### Step 6: 動作確認
```bash
# 開発サーバー起動
python app_v2.py

# APIエンドポイント確認
curl http://localhost:5100/health
```

#### Step 7: コミット
```bash
git add requirements.txt
git commit -m "$(cat <<'EOF'
セキュリティ: 依存関係のセキュリティ更新

- <package_name>: <old_version> → <new_version>
- 脆弱性ID: CVE-XXXX-XXXXX
- テスト結果: 全テストパス

Co-Authored-By: Claude Sonnet 4.5 (1M context) <noreply@anthropic.com>
EOF
)"
```

### ロールバック手順
```bash
# requirements.txtを以前のバージョンに戻す
git checkout HEAD~1 requirements.txt
pip install -r requirements.txt
```

### 成功基準
- [ ] 脆弱性が解消された
- [ ] 全テストがパス
- [ ] API動作確認完了
- [ ] パフォーマンス劣化なし
```

---

## ⚡ パフォーマンスチューニングタスク

### N+1クエリ最適化タスク

**リスク:** Medium
**所要時間:** 1-2時間

```markdown
## タスク: N+1クエリの最適化

### ゴール
N+1クエリ問題を特定し、eager loadingで最適化する

### 事前確認
- [ ] 現在のレスポンスタイム計測済み
- [ ] プロファイリング結果取得済み

### 実行手順

#### Step 1: N+1クエリの検出
```python
# Flask-DebugToolbar または SQLAlchemy echo で検出
# app_v2.py に追加（開発環境のみ）

if os.getenv('MKS_ENV') == 'development':
    app.config['SQLALCHEMY_ECHO'] = True
```

#### Step 2: 問題のあるコード特定
```bash
# ログから重複クエリを検索
grep "SELECT" logs/sqlalchemy.log | sort | uniq -c | sort -rn
```

#### Step 3: Eager Loadingの実装
```python
# Before (N+1 problem)
knowledges = Knowledge.query.all()
for k in knowledges:
    print(k.author.username)  # 各ナレッジごとにクエリ発行

# After (Optimized with joinedload)
from sqlalchemy.orm import joinedload

knowledges = Knowledge.query.options(
    joinedload(Knowledge.author)
).all()
for k in knowledges:
    print(k.author.username)  # 1回のクエリで取得
```

#### Step 4: パフォーマンス測定
```bash
# ベンチマークツール使用
ab -n 100 -c 10 https://localhost:443/api/v1/knowledges

# または Python timeit
python -m timeit -s "import requests" "requests.get('https://localhost:443/api/v1/knowledges')"
```

#### Step 5: テスト
```bash
# 既存テストがパスすることを確認
pytest tests/ -v

# パフォーマンステスト追加
pytest tests/test_performance.py -v
```

#### Step 6: コミット
```bash
git add <変更ファイル>
git commit -m "$(cat <<'EOF'
パフォーマンス: N+1クエリ最適化（Knowledge一覧API）

- Knowledge.query に joinedload(Knowledge.author) を追加
- クエリ数: 101回 → 1回に削減
- レスポンスタイム: 850ms → 120ms（約85%改善）

Co-Authored-By: Claude Sonnet 4.5 (1M context) <noreply@anthropic.com>
EOF
)"
```

### 成功基準
- [ ] クエリ数が削減された
- [ ] レスポンスタイムが改善された（50%以上）
- [ ] テストスイートがパス
- [ ] メモリ使用量が増加していない
```

---

## 🐛 バグ修正タスク

### バグ修正タスク

**リスク:** Medium
**所要時間:** 1時間

```markdown
## タスク: バグ修正

### ゴール
報告されたバグを特定・修正する

### 事前確認
- [ ] バグ再現手順を確認済み
- [ ] 影響範囲を把握済み

### 実行手順

#### Step 1: バグ再現
```bash
# 再現手順を実行
curl -X POST https://localhost:443/api/v1/knowledges \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -d '{"title":"Test","content":"..."}'

# エラーログ確認
tail -n 100 logs/error.log
```

#### Step 2: 原因特定
```bash
# 関連コード読み込み
Read(backend/app_v2.py)
Grep("def create_knowledge", path="backend", output_mode="content")

# エラースタックトレース確認
# - どの関数でエラーが発生しているか
# - エラーメッセージの内容
```

#### Step 3: テストケース作成（TDD推奨）
```python
# tests/test_knowledge_bug.py
def test_create_knowledge_with_empty_tags():
    """空のタグ配列でナレッジ作成時にエラーが発生しないこと"""
    response = client.post('/api/v1/knowledges', json={
        'title': 'Test',
        'content': 'Content',
        'tags': []  # 空配列でバグ発生
    })
    assert response.status_code == 201
```

#### Step 4: バグ修正
```python
# app_v2.py
# Before
tags = data['tags']
for tag in tags:  # tags=[]の場合、問題なし。だが tags=None の場合はエラー
    ...

# After
tags = data.get('tags', [])  # デフォルト値設定
if tags:  # None チェック追加
    for tag in tags:
        ...
```

#### Step 5: テスト実行
```bash
# 修正したバグのテスト
pytest tests/test_knowledge_bug.py -v

# 全テストスイート（リグレッション確認）
pytest tests/ -v --cov=. --cov-report=term
```

#### Step 6: 手動確認
```bash
# 実際のAPIで動作確認
curl -X POST https://localhost:443/api/v1/knowledges \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -d '{"title":"Test","content":"...","tags":[]}'
```

#### Step 7: コミット
```bash
git add backend/app_v2.py tests/test_knowledge_bug.py
git commit -m "$(cat <<'EOF'
修正: ナレッジ作成時の空タグ配列処理

- tags が None または空配列の場合の処理を追加
- テストケース追加: test_create_knowledge_with_empty_tags
- 影響範囲: POST /api/v1/knowledges

Fixes #123

Co-Authored-By: Claude Sonnet 4.5 (1M context) <noreply@anthropic.com>
EOF
)"
```

### 成功基準
- [ ] バグが再現しない
- [ ] テストケースが追加された
- [ ] 全テストがパス
- [ ] 関連機能に影響がない
```

---

## ✨ 機能追加タスク

### 機能追加タスク

**リスク:** Medium
**所要時間:** 2-3時間

```markdown
## タスク: 新規機能追加

### ゴール
要件定義に基づいた新機能を実装する

### 事前確認
- [ ] 要件定義が明確
- [ ] UI/UXデザインが確定（該当する場合）
- [ ] データモデル変更の有無を確認

### 実行手順

#### Step 1: 設計
```markdown
## 機能設計: <機能名>

### エンドポイント
- POST /api/v1/<resource>
- GET /api/v1/<resource>/:id
- PUT /api/v1/<resource>/:id
- DELETE /api/v1/<resource>/:id

### データモデル
- <Resource> モデル
  - id: Integer (PK)
  - name: String(100)
  - created_at: DateTime

### バリデーション
- name: 必須, 最大100文字

### 権限
- 作成: 認証済みユーザー
- 参照: 全ユーザー
- 更新: 作成者または管理者
- 削除: 作成者または管理者
```

#### Step 2: データモデル実装
```python
# backend/models.py
class Resource(db.Model):
    __tablename__ = 'resources'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat()
        }
```

#### Step 3: スキーマ定義
```python
# backend/schemas.py
class ResourceSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(max=100))
```

#### Step 4: APIエンドポイント実装
```python
# backend/app_v2.py
@app.route('/api/v1/resources', methods=['POST'])
@jwt_required()
def create_resource():
    """リソース作成"""
    schema = ResourceSchema()
    errors = schema.validate(request.json)
    if errors:
        return jsonify({'errors': errors}), 400

    data = schema.load(request.json)
    resource = Resource(name=data['name'])
    db.session.add(resource)
    db.session.commit()

    return jsonify(resource.to_dict()), 201
```

#### Step 5: テスト実装
```python
# tests/test_resource.py
class TestResourceAPI:
    def test_create_resource(self, client, auth_token):
        """リソース作成のテスト"""
        response = client.post('/api/v1/resources',
            headers={'Authorization': f'Bearer {auth_token}'},
            json={'name': 'Test Resource'})

        assert response.status_code == 201
        assert response.json['name'] == 'Test Resource'

    def test_create_resource_validation(self, client, auth_token):
        """バリデーションのテスト"""
        response = client.post('/api/v1/resources',
            headers={'Authorization': f'Bearer {auth_token}'},
            json={'name': 'a' * 101})  # 最大長超過

        assert response.status_code == 400
```

#### Step 6: テスト実行
```bash
# 新規テスト実行
pytest tests/test_resource.py -v

# 全テストスイート（リグレッション確認）
pytest tests/ -v --cov=. --cov-report=term
```

#### Step 7: ドキュメント更新
```bash
# API仕様書更新
Edit(docs/API.md)

# 追加内容:
# ## Resource API
# - POST /api/v1/resources - リソース作成
# - GET /api/v1/resources - リソース一覧取得
```

#### Step 8: フロントエンド実装（該当する場合）
```javascript
// webui/resource.js
async function createResource(name) {
    const response = await fetch('/api/v1/resources', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${getToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name })
    });

    if (!response.ok) {
        throw new Error('Failed to create resource');
    }

    return await response.json();
}
```

#### Step 9: コミット
```bash
git add backend/models.py backend/schemas.py backend/app_v2.py tests/test_resource.py docs/API.md
git commit -m "$(cat <<'EOF'
機能: リソース管理機能の追加

- Resource モデル追加
- POST /api/v1/resources エンドポイント追加
- テストケース追加（test_resource.py）
- API仕様書更新

Co-Authored-By: Claude Sonnet 4.5 (1M context) <noreply@anthropic.com>
EOF
)"
```

### 成功基準
- [ ] 要件を満たしている
- [ ] テストカバレッジ80%以上
- [ ] ドキュメント更新済み
- [ ] 既存機能に影響がない
```

---

## 🎨 フロントエンドタスク

### UI改善タスク

**リスク:** Low
**所要時間:** 1時間

```markdown
## タスク: UI改善

### ゴール
ユーザビリティ向上のためのUI改善

### 実行手順

#### Step 1: 現状確認
```bash
# 対象HTMLファイル確認
Read(webui/index.html)
Read(webui/app.js)
```

#### Step 2: 改善実装
```javascript
// Before
document.getElementById('submit-btn').onclick = function() {
    // 処理
}

// After: アクセシビリティ改善
const submitBtn = document.getElementById('submit-btn');
submitBtn.setAttribute('aria-label', 'ナレッジを投稿');
submitBtn.addEventListener('click', function() {
    // 処理
});
```

#### Step 3: ESLint確認
```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/webui
npx eslint app.js
```

#### Step 4: ブラウザテスト
```bash
# ローカルサーバー起動
python -m http.server 8000

# ブラウザで確認
# - レイアウト崩れがないか
# - レスポンシブ対応
# - アクセシビリティ
```

#### Step 5: コミット
```bash
git add webui/app.js
git commit -m "$(cat <<'EOF'
UI改善: 投稿ボタンのアクセシビリティ向上

- aria-label 属性追加
- イベントリスナーの改善

Co-Authored-By: Claude Sonnet 4.5 (1M context) <noreply@anthropic.com>
EOF
)"
```
```

---

## 📝 その他の定型タスク

### データバックアップタスク

```bash
# 手動バックアップ実行
sudo /usr/local/bin/backup_full.sh

# バックアップ確認
sudo /usr/local/bin/verify_backup.sh
```

### データリストアタスク

```bash
# 最新バックアップからリストア
LATEST_BACKUP=$(ls -t /backup/mirai-knowledge-system/daily/ | head -1)
sudo /usr/local/bin/restore_full.sh /backup/mirai-knowledge-system/daily/$LATEST_BACKUP
```

### ログ確認タスク

```bash
# エラーログ確認
tail -n 100 /var/log/mirai-knowledge-system/error.log

# アクセスログ確認
tail -n 100 /var/log/nginx/access.log

# 認証ログ確認
grep "Authentication" /var/log/mirai-knowledge-system/auth.log
```

---

## 参考資料

- [本番運用ガイド](PRODUCTION_OPERATIONS.md)
- [安全チェックリスト](SAFETY_CHECKLIST.md)
- [エージェント役割分担](AGENT_ROLES.md)

---

**更新履歴**

| 日付 | バージョン | 変更内容 |
|------|-----------|----------|
| 2026-01-08 | 1.0 | 初版作成 - タスクテンプレート策定 |
