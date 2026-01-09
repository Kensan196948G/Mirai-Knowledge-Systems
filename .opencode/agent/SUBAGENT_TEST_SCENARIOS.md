# 🧪 SubAgent動作確認テストシナリオ

**作成日**: 2026-01-09
**ステータス**: ✅ 準備完了
**環境**: OpenCode CLI

---

## 📋 テスト概要

OpenCodeのSubAgent機能が正しく動作することを確認するためのテストシナリオです。

### ⚠️ 重要な注意事項

**OpenCodeのSubAgentは`opencode` CLIツールでのみ動作します。**

- ✅ **動作する環境**: `opencode` CLI（OpenCodeアプリケーション）
- ❌ **動作しない環境**: Claude Code CLI、通常のClaude API

### 🔧 前提条件

```bash
# OpenCodeがインストールされていること
which opencode

# プロジェクトディレクトリで実行
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems

# opencode.jsonにSubAgentが設定されていること
cat opencode.json | grep "agents"
```

---

## 🎯 テストシナリオ一覧

### 1. 🎯 spec-planner: 要件整理テスト

**目的**: タスク分解とチケット設計の機能確認

**OpenCodeでの実行方法**:
```bash
# OpenCode CLIで以下を実行
@spec-planner "ユーザープロファイル編集機能の実装タスクを分解してください"
```

**期待される出力**:
```markdown
## タイトル
[機能] ユーザープロファイル編集機能の実装

## 背景・目的
ユーザーが自分のプロファイル情報（名前、メールアドレス、所属部署等）を編集できる機能

## 完了基準（Acceptance Criteria）
- [ ] プロファイル編集画面を表示できる
- [ ] ユーザー情報を更新できる
- [ ] バリデーションエラーが適切に表示される
- [ ] 更新成功時に確認メッセージが表示される

## 関連ファイル
- backend/app_v2.py: ユーザー管理エンドポイント
- webui/profile.html: プロファイル編集画面（新規作成）
- webui/app.js: API呼び出し処理

## タスク分解
1. バックエンド: PATCH /api/v2/users/{user_id} エンドポイント作成
2. フロントエンド: profile.html 画面作成
3. フロントエンド: プロファイル編集API連携実装
4. テスト: 単体テスト・E2Eテスト作成
5. ドキュメント: API仕様書更新

## 優先度
中
```

**検証項目**:
- ✅ タスクが適切な粒度で分解されている
- ✅ 完了基準が明確に定義されている
- ✅ 関連ファイルが正しく特定されている
- ✅ Mirai Knowledge Systemsの技術スタックに準拠している

---

### 2. 🏗️ arch-reviewer: アーキテクチャレビューテスト

**目的**: 設計レビューと技術的助言の機能確認

**OpenCodeでの実行方法**:
```bash
@arch-reviewer "ファイルアップロード機能を追加する場合、アーキテクチャ上の考慮点を教えてください"
```

**期待される出力**:
```markdown
## アーキテクチャレビュー: ファイルアップロード機能

### 現状の構成確認
- バックエンド: Flask（同期処理）
- ストレージ: ローカルファイルシステム
- データベース: PostgreSQL
- 認証: JWT + RBAC

### 考慮すべき設計上の課題

#### 1. ファイルサイズ制限
- **推奨**: MAX_CONTENT_LENGTH設定（例: 16MB）
- **理由**: DoS攻撃対策、サーバーリソース保護

#### 2. ストレージ戦略
- **オプションA**: ローカルファイルシステム
  - メリット: 実装簡単、追加コストなし
  - デメリット: スケーラビリティに制限
- **オプションB**: オブジェクトストレージ（MinIO等）
  - メリット: スケーラブル、バックアップ容易
  - デメリット: 追加インフラ必要

#### 3. セキュリティ考慮事項
- ファイル名のサニタイゼーション（パストラバーサル対策）
- ファイルタイプの検証（MIMEタイプチェック）
- ウイルススキャン（将来的な検討事項）
- アクセス制御（誰がどのファイルにアクセス可能か）

#### 4. データベース設計
```sql
CREATE TABLE uploaded_files (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    filename VARCHAR(255),
    file_path VARCHAR(512),
    mime_type VARCHAR(100),
    file_size BIGINT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 推奨事項
1. **第1フェーズ**: ローカルファイルシステム + サイズ制限
2. **第2フェーズ**: オブジェクトストレージ移行検討

### 影響範囲
- backend/app_v2.py: 新規エンドポイント追加
- backend/models.py: UploadedFile モデル追加
- systemd/mirai-knowledge-app.service: ストレージパス設定
```

**検証項目**:
- ✅ 現状のアーキテクチャを正しく理解している
- ✅ 複数の実装オプションを提示している
- ✅ セキュリティリスクを指摘している
- ✅ 段階的な実装計画を提案している

---

### 3. 💻 code-implementer: コード実装テスト

**目的**: 実装能力と既存コードベースの理解確認

**OpenCodeでの実行方法**:
```bash
@code-implementer "GET /api/v2/health エンドポイントを追加して、データベース接続状態を返すようにしてください"
```

**期待される動作**:
1. backend/app_v2.pyを読み込む
2. 既存のエンドポイント構造を理解
3. 新しいヘルスチェックエンドポイントを追加
4. データベース接続確認ロジックを実装
5. 適切なエラーハンドリングを含める

**検証項目**:
- ✅ 既存のコードスタイルに準拠している
- ✅ エラーハンドリングが適切
- ✅ ログ出力が適切
- ✅ セキュリティ上の問題がない

---

### 4. 🧪 test-designer: テスト設計テスト

**目的**: テストケース設計能力の確認

**OpenCodeでの実行方法**:
```bash
@test-designer "POST /api/v2/users エンドポイントのテストケースを作成してください"
```

**期待される出力**:
```python
# backend/tests/test_user_endpoints.py

import pytest
from app_v2 import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

class TestUserCreate:
    """ユーザー作成エンドポイントのテスト"""

    def test_create_user_success(self, client):
        """正常系: ユーザー作成成功"""
        payload = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass123!",
            "role": "一般ユーザー"
        }
        response = client.post('/api/v2/users', json=payload)
        assert response.status_code == 201
        assert 'id' in response.json

    def test_create_user_duplicate_username(self, client):
        """異常系: 重複したユーザー名"""
        # ... テストコード

    def test_create_user_invalid_email(self, client):
        """異常系: 無効なメールアドレス"""
        # ... テストコード

    def test_create_user_weak_password(self, client):
        """異常系: 弱いパスワード"""
        # ... テストコード
```

**検証項目**:
- ✅ 正常系・異常系の両方をカバー
- ✅ pytestの規約に準拠
- ✅ 適切なアサーションを含む
- ✅ テストケース名が明確

---

### 5. 🚀 ci-specialist: CI/CD設定テスト

**目的**: GitHub Actionsワークフロー設計能力の確認

**OpenCodeでの実行方法**:
```bash
@ci-specialist "バックエンドのPythonテストを実行するGitHub Actionsワークフローを最適化してください"
```

**期待される動作**:
1. .github/workflows/ci-backend.ymlを読み込む
2. 既存のワークフローを分析
3. 最適化案を提示（キャッシュ、並列実行等）
4. ワークフローを更新

**検証項目**:
- ✅ 既存ワークフローの問題点を特定
- ✅ 実行時間の短縮策を提案
- ✅ Docker不使用の制約を守る
- ✅ セキュリティ設定が適切

---

### 6. 🔒 sec-auditor: セキュリティ監査テスト

**目的**: セキュリティリスク検出能力の確認

**OpenCodeでの実行方法**:
```bash
@sec-auditor "backend/app_v2.py のセキュリティリスクをチェックしてください"
```

**期待される出力**:
```markdown
## セキュリティ監査レポート: backend/app_v2.py

### 🔍 検出された問題

#### 1. SQLインジェクション対策 ✅
- 状態: **良好**
- 詳細: SQLAlchemy ORMを使用しており、パラメータ化クエリで実装されている

#### 2. XSS対策 ✅
- 状態: **良好**
- 詳細: JSONレスポンスのみで、HTMLをレンダリングしていない

#### 3. CSRF対策 ⚠️
- 状態: **要改善**
- 詳細: CSRF保護が実装されているが、全エンドポイントでの適用確認が必要

#### 4. 認証・認可 ✅
- 状態: **良好**
- 詳細: JWT認証 + RBAC実装済み

#### 5. 機密情報の露出 ⚠️
- 状態: **要確認**
- 行数: 1234
- 詳細: エラーメッセージに詳細なスタックトレースが含まれる可能性

### 📋 推奨事項
1. 本番環境でDEBUGモードを無効化
2. エラーメッセージの詳細を制限
3. セキュリティヘッダーの追加（CSP, X-Frame-Options等）
```

**検証項目**:
- ✅ 一般的な脆弱性を網羅的にチェック
- ✅ 具体的なコード箇所を指摘
- ✅ 改善策を提案
- ✅ 優先度を明示

---

### 7. 📚 ops-runbook: 運用手順書作成テスト

**目的**: 運用ドキュメント作成能力の確認

**OpenCodeでの実行方法**:
```bash
@ops-runbook "データベース接続エラー発生時の対応手順を作成してください"
```

**期待される出力**:
```markdown
# 🚨 障害対応: データベース接続エラー

## 症状
- アプリケーションが「Database connection failed」エラーを返す
- ログに`psycopg2.OperationalError`が記録される
- ユーザーがログインできない

## 影響範囲
- **重大度**: 🔴 Critical
- **影響ユーザー**: 全ユーザー
- **影響機能**: 全機能（読み取り・書き込み）

## 初動対応（5分以内）

### 1. データベースサービス状態確認
```bash
sudo systemctl status postgresql
```

**期待結果**: `active (running)`

**NGの場合**:
```bash
# PostgreSQL再起動
sudo systemctl restart postgresql

# ステータス確認
sudo systemctl status postgresql
```

### 2. 接続テスト
```bash
psql -U mks_user -d mirai_knowledge_db -h localhost
```

**接続できない場合**:
- パスワード確認: `/etc/postgresql/conf.d/mks.conf`
- ポート確認: `sudo netstat -tlnp | grep 5432`

### 3. アプリケーション再起動
```bash
sudo systemctl restart mirai-knowledge-app
sudo systemctl status mirai-knowledge-app
```

## 詳細調査（10分以内）

### ログ確認
```bash
# PostgreSQLログ
sudo tail -f /var/log/postgresql/postgresql-16-main.log

# アプリケーションログ
sudo journalctl -u mirai-knowledge-app -f
```

### 接続数確認
```sql
SELECT count(*) FROM pg_stat_activity;
```

**接続数が上限に達している場合**:
```sql
-- アイドル接続を強制終了
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle' AND state_change < now() - interval '10 minutes';
```

## エスカレーション判断

以下の場合は上位者にエスカレーション:
- PostgreSQL再起動後も接続できない
- ディスク容量が95%を超えている
- ハードウェア障害の兆候がある

## 予防策
1. 接続プーリング設定の最適化
2. 定期的な接続数モニタリング
3. ディスク容量アラート設定
```

**検証項目**:
- ✅ 段階的な対応手順が明確
- ✅ 実際に実行可能なコマンドを含む
- ✅ エスカレーション基準が明確
- ✅ 予防策を提案

---

## 🎯 テスト実行手順

### OpenCode CLIでの実行

```bash
# 1. OpenCodeを起動
opencode

# 2. プロジェクトディレクトリに移動
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems

# 3. SubAgentを呼び出す
@spec-planner "テスト"

# または
@arch-reviewer "現状のアーキテクチャを確認してください"

# 複数のSubAgentを連携
@spec-planner "ログイン機能の改善タスクを分解" && @arch-reviewer "設計レビュー"
```

### 動作確認チェックリスト

- [ ] `@spec-planner`が応答する
- [ ] `@arch-reviewer`が応答する
- [ ] `@code-implementer`が応答する
- [ ] `@test-designer`が応答する
- [ ] `@ci-specialist`が応答する
- [ ] `@sec-auditor`が応答する
- [ ] `@ops-runbook`が応答する
- [ ] SubAgentが適切なPermissionで動作している
- [ ] SubAgentが指定されたModelで動作している

---

## 📊 期待される結果

### 成功時の挙動
✅ SubAgentが指定されたタスクを実行
✅ 出力が期待される形式に準拠
✅ Permission設定が正しく適用される
✅ 適切なModelが使用される（Opus 4.5 / Sonnet 4.5）

### 失敗時の挙動
❌ SubAgentが認識されない → `opencode.json`の設定を確認
❌ Permission Deniedエラー → `.opencode/agent/*.md`のpermission設定を確認
❌ Model not foundエラー → `model`フィールドの値を確認

---

## 🔗 関連ドキュメント

- **SubAgent定義**: `.opencode/agent/*.md`
- **運用ガイド**: `.opencode/agent/AGENTS.md`
- **有効化レポート**: `.opencode/agent/SUBAGENT_ACTIVATION_REPORT.md`
- **OpenCode設定**: `opencode.json`

---

## 📅 更新履歴

| 日付 | 変更内容 |
|------|----------|
| 2026-01-09 | テストシナリオ初版作成 |
| 2026-01-09 | 7つのSubAgent全てのテストケースを追加 |

---

**🚀 OpenCode CLIでこれらのテストシナリオを実行して、SubAgentの動作を確認してください！✨**
