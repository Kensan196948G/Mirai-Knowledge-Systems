# エージェント役割分担 - Agent Roles & Workflows

Claude Codeの各機能（SubAgent/Hooks/MCP/標準ツール）を効果的に使い分けるためのガイドです。

---

## 🎯 機能マトリクス

| 機能 | 用途 | 並列実行 | 使用例 |
|------|------|---------|--------|
| **標準ツール** | ファイル操作・検索 | ⭐⭐⭐ | Read/Edit/Grep/Bash |
| **MCP** | 外部連携・知識検索 | ⭐⭐ | brave-search/github/memory |
| **カスタムスキル** | 定型作業の自動化 | ⭐ | commit-push-pr |
| **sequential-thinking** | 複雑な設計・分析 | ❌ | アーキテクチャ設計 |

---

## 📦 標準ツール - 基本的なファイル操作

### Read - ファイル読み取り

**使用タイミング:**
- コードレビュー時
- バグ調査時
- 設定ファイル確認時

**並列実行の推奨:**
```javascript
// ✅ Good: 複数ファイルを並列読み取り
Read(backend/app_v2.py)
Read(backend/models.py)
Read(backend/schemas.py)

// ❌ Bad: 順次実行
Read(backend/app_v2.py)
// 結果待ち...
Read(backend/models.py)
// 結果待ち...
```

**実践例:**
```markdown
ユーザー: 「認証周りのコードをレビューして」

Claude Code:
1. 並列で関連ファイルを読み込み
   - Read(backend/app_v2.py) ← 認証エンドポイント
   - Read(backend/models.py) ← Userモデル
   - Read(backend/password_policy.py) ← パスワードポリシー
   - Read(backend/csrf_protection.py) ← CSRF対策

2. 読み込み結果を統合分析

3. レビューコメント提示
```

---

### Edit - ファイル編集

**使用タイミング:**
- バグ修正
- 機能追加
- リファクタリング

**重要ルール:**
1. 編集前に必ずReadで内容確認
2. old_stringは一意である必要がある
3. インデントを正確に保つ

**実践例:**
```python
# Step 1: Read で現在の内容確認
Read(backend/app_v2.py)

# Step 2: Edit で修正
Edit(
    file_path="/mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/app_v2.py",
    old_string="""def create_knowledge():
    data = request.json
    knowledge = Knowledge(**data)""",
    new_string="""def create_knowledge():
    data = request.json
    # バリデーション追加
    schema = KnowledgeSchema()
    errors = schema.validate(data)
    if errors:
        return jsonify({'errors': errors}), 400
    knowledge = Knowledge(**data)"""
)
```

---

### Grep - コード検索

**使用タイミング:**
- 特定パターンの検索
- 関数・変数の使用箇所特定
- エラーメッセージの調査

**効率的な使い方:**
```bash
# パターン1: ファイル一覧を取得（デフォルト）
Grep(pattern="def create_knowledge", path="backend", output_mode="files_with_matches")

# パターン2: マッチ行の内容を表示
Grep(pattern="def create_knowledge", path="backend", output_mode="content", -n=true)

# パターン3: 前後の行も表示
Grep(pattern="def create_knowledge", path="backend", output_mode="content", -C=5)

# パターン4: 複数ファイルタイプから検索
Grep(pattern="jwt_required", path="backend", type="py")
```

**並列検索の推奨:**
```javascript
// ✅ Good: 複数パターンを並列検索
Grep(pattern="@jwt_required", path="backend")
Grep(pattern="@admin_required", path="backend")
Grep(pattern="Authentication failed", path="backend/logs")

// 結果を統合分析
```

---

### Bash - コマンド実行

**使用タイミング:**
- Git操作
- テスト実行
- パッケージインストール
- サービス管理

**並列実行の活用:**
```bash
# ✅ Good: 独立したコマンドは並列実行
Bash("git status")
Bash("git diff")
Bash("git log -3 --oneline")

# ❌ Bad: 依存関係のあるコマンドを並列実行
Bash("git add .")  # これが完了する前に...
Bash("git commit -m 'test'")  # これを実行するとエラー

# ✅ Good: 依存関係のあるコマンドは && で連結
Bash("git add . && git commit -m 'test' && git push")
```

**テスト実行の例:**
```bash
# 並列実行可能な独立したテスト
Bash("pytest tests/test_auth.py -v")
Bash("pytest tests/test_knowledge.py -v")
Bash("pytest tests/test_user.py -v")

# 全テストスイート（カバレッジ含む）
Bash("pytest tests/ -v --cov=. --cov-report=term")
```

---

## 🌐 MCP - 外部連携

### brave-search - Web検索

**使用タイミング:**
- 最新技術情報の調査
- セキュリティ脆弱性の確認
- ライブラリのベストプラクティス調査

**実践例:**
```markdown
ユーザー: 「Flask 3.1のセキュリティベストプラクティスを調査して」

Claude Code:
1. MCPSearch で brave-search ツールをロード
   MCPSearch("select:mcp__brave-search__brave_web_search")

2. Web検索実行
   mcp__brave-search__brave_web_search(
       query="Flask 3.1 security best practices 2026"
   )

3. 検索結果を分析・要約

4. プロジェクトへの適用提案
```

---

### github - GitHub連携

**使用タイミング:**
- PRレビュー
- Issue確認
- コミット履歴調査

**実践例:**
```markdown
ユーザー: 「最新のPRをレビューして」

Claude Code:
1. MCPSearch で GitHub ツールをロード
   MCPSearch("select:mcp__github__list_pull_requests")

2. PR一覧取得
   mcp__github__list_pull_requests(
       owner="your-org",
       repo="Mirai-Knowledge-Systems",
       state="open"
   )

3. PR詳細取得
   mcp__github__get_pull_request(
       owner="your-org",
       repo="Mirai-Knowledge-Systems",
       pull_number=123
   )

4. レビューコメント作成
```

---

### memory - セッション間メモリ

**使用タイミング:**
- 設計決定の記録
- 頻繁に参照する情報の保存
- プロジェクト知識の蓄積

**実践例:**
```markdown
# 重要な設計決定を記録
MCPSearch("select:mcp__memory__create_entities")

mcp__memory__create_entities(
    entities=[{
        "name": "Authentication Design",
        "entityType": "design_decision",
        "observations": [
            "JWT with 24h expiration",
            "Refresh token not implemented",
            "CSRF protection with double-submit cookie"
        ]
    }]
)

# 後で検索
MCPSearch("select:mcp__memory__search_nodes")
mcp__memory__search_nodes(query="authentication")
```

---

### sequential-thinking - 段階的思考

**使用タイミング:**
- 複雑なアーキテクチャ設計
- パフォーマンス最適化の計画
- セキュリティレビュー

**実践例:**
```markdown
ユーザー: 「ナレッジ検索のパフォーマンス最適化を設計して」

Claude Code:
1. MCPSearch でツールをロード
   MCPSearch("select:mcp__sequential-thinking__sequentialthinking")

2. 段階的思考を開始
   mcp__sequential-thinking__sequentialthinking(
       task="ナレッジ検索のパフォーマンス最適化設計",
       context={
           "current_response_time": "850ms",
           "target_response_time": "200ms",
           "database": "PostgreSQL",
           "data_volume": "10,000 knowledges"
       }
   )

3. 思考プロセス:
   - 現状分析（N+1クエリ、インデックス不足）
   - 最適化案の列挙（eager loading, インデックス追加, キャッシュ）
   - 優先順位付け
   - 実装計画

4. 詳細設計を返却
```

---

## 🚀 カスタムスキル - 定型作業の自動化

### commit-push-pr - コミット・プッシュ・PR作成

**使用タイミング:**
- 機能開発完了時
- バグ修正完了時

**実践例:**
```markdown
ユーザー: 「ユーザー検索機能の実装をコミットしてPR作成して」

Claude Code:
Skill(skill="commit-push-pr")

# 自動で以下を実行:
1. git status で変更確認
2. git diff で差分確認
3. git log で履歴確認
4. コミットメッセージ生成
5. git add <変更ファイル>
6. git commit
7. git push
8. gh pr create
```

---

### commit-push-pr-merge - 緊急修正フロー

**使用タイミング:**
- 緊急バグ修正（ホットフィックス）
- セキュリティパッチ適用

**実践例:**
```markdown
ユーザー: 「認証バグの緊急修正をマージまで完了して」

Claude Code:
Skill(skill="commit-push-pr-merge")

# 自動で以下を実行:
1. commit-push-pr と同じ1-8
9. gh pr merge --squash
```

---

## 🎨 効率的なワークフロー例

### ワークフロー1: バグ修正

```markdown
1. 問題の特定（並列実行）
   Read(backend/app_v2.py)
   Grep(pattern="def create_knowledge", output_mode="content", -C=10)
   Bash("tail -n 100 logs/error.log")

2. 関連テスト確認
   Read(tests/test_knowledge.py)
   Bash("pytest tests/test_knowledge.py -v")

3. 修正実装
   Edit(backend/app_v2.py, old_string="...", new_string="...")

4. テスト実行
   Bash("pytest tests/test_knowledge.py -v")
   Bash("pytest tests/ -v --cov=.")

5. コミット・PR作成
   Skill(skill="commit-push-pr")
```

---

### ワークフロー2: 新機能開発

```markdown
1. 要件確認・設計（sequential-thinking使用）
   MCPSearch("select:mcp__sequential-thinking__sequentialthinking")
   mcp__sequential-thinking__sequentialthinking(
       task="タグ管理機能の設計"
   )

2. 既存コード調査（並列実行）
   Read(backend/models.py)
   Read(backend/schemas.py)
   Grep(pattern="class.*\(db.Model\)", output_mode="content")

3. データモデル実装
   Edit(backend/models.py, ...)

4. スキーマ定義
   Edit(backend/schemas.py, ...)

5. APIエンドポイント実装
   Edit(backend/app_v2.py, ...)

6. テスト実装
   Edit(tests/test_tags.py, ...)

7. テスト実行（並列可能）
   Bash("pytest tests/test_tags.py -v")
   Bash("pytest tests/ -v --cov=.")

8. ドキュメント更新
   Edit(docs/API.md, ...)

9. コミット・PR作成
   Skill(skill="commit-push-pr")
```

---

### ワークフロー3: セキュリティ更新

```markdown
1. 脆弱性調査（Web検索）
   MCPSearch("select:mcp__brave-search__brave_web_search")
   mcp__brave-search__brave_web_search(
       query="Flask 3.1 CVE 2026"
   )

2. 現在の依存関係確認
   Read(backend/requirements.txt)
   Bash("pip list --outdated")

3. 更新計画策定
   # sequential-thinking で段階的更新計画

4. 依存関係更新
   Bash("pip install --upgrade flask==3.1.3")
   Bash("pip freeze > requirements.txt")

5. テスト実行
   Bash("pytest tests/ -v --cov=.")

6. コミット・PR作成
   Skill(skill="commit-push-pr")
```

---

### ワークフロー4: パフォーマンス調査

```markdown
1. 現状把握（並列実行）
   Bash("ab -n 100 -c 10 https://localhost:443/api/v1/knowledges")
   Read(backend/app_v2.py)
   Grep(pattern="Knowledge.query", output_mode="content", -C=5)

2. プロファイリング
   Bash("python -m cProfile -o profile.stats app_v2.py")
   Bash("python -c 'import pstats; p=pstats.Stats(\"profile.stats\"); p.sort_stats(\"cumulative\").print_stats(20)'")

3. ボトルネック特定
   # N+1クエリ、インデックス不足など

4. 最適化実装
   Edit(backend/app_v2.py, ...)

5. パフォーマンス測定（改善確認）
   Bash("ab -n 100 -c 10 https://localhost:443/api/v1/knowledges")

6. テスト・コミット
   Bash("pytest tests/ -v")
   Skill(skill="commit-push-pr")
```

---

## ⚡ 並列実行のベストプラクティス

### 並列実行可能な操作

```javascript
// ✅ ファイル読み取り（独立）
Read(backend/app_v2.py)
Read(backend/models.py)
Read(tests/test_knowledge.py)

// ✅ 検索操作（独立）
Grep(pattern="jwt_required", path="backend")
Grep(pattern="admin_required", path="backend")

// ✅ 独立したBashコマンド
Bash("git status")
Bash("git log -3")
Bash("pytest --version")
```

### 並列実行できない操作（依存関係あり）

```bash
# ❌ 順序が重要な操作
Bash("git add .")
Bash("git commit -m 'test'")  # git add の完了が必要

# ✅ && で連結
Bash("git add . && git commit -m 'test'")

# ❌ ファイル編集と読み取り
Edit(app.py, ...)
Read(app.py)  # 編集完了を待つ必要がある

# ✅ 順次実行
Edit(app.py, ...)
# (編集完了を待つ)
Read(app.py)
```

---

## 🎯 状況別の推奨アプローチ

| 状況 | 推奨ツール | 理由 |
|------|-----------|------|
| コードレビュー | Read (並列) | 複数ファイルを効率的に読み込み |
| バグ調査 | Grep + Read + Bash | パターン検索→詳細確認→ログ確認 |
| 機能追加 | sequential-thinking + Edit | 設計→実装の段階的アプローチ |
| セキュリティ更新 | brave-search + Bash | 最新情報確認→更新適用 |
| PR作成 | Skill(commit-push-pr) | 定型作業の自動化 |
| 緊急修正 | Skill(commit-push-pr-merge) | 迅速なマージまで完了 |
| 設計レビュー | sequential-thinking + memory | 複雑な思考→記録保存 |
| GitHub連携 | github MCP | PR/Issue管理 |

---

## 📊 パフォーマンス比較

| タスク | 並列実行なし | 並列実行あり | 改善率 |
|--------|-------------|-------------|--------|
| 5ファイル読み取り | 25秒 | 5秒 | 80% |
| 3パターン検索 | 15秒 | 5秒 | 67% |
| コードレビュー（10ファイル） | 50秒 | 10秒 | 80% |

**結論:** 独立した操作は積極的に並列実行すべき

---

## 参考資料

- [本番運用ガイド](PRODUCTION_OPERATIONS.md)
- [タスクテンプレート](TASK_TEMPLATES.md)
- [安全チェックリスト](SAFETY_CHECKLIST.md)

---

**更新履歴**

| 日付 | バージョン | 変更内容 |
|------|-----------|----------|
| 2026-01-08 | 1.0 | 初版作成 - エージェント役割分担の策定 |
