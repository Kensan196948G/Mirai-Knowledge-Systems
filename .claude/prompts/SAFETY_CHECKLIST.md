# 安全チェックリスト - Safety Checklist

本番環境での作業時に使用する安全チェックリストです。
**全ての本番変更前に必ず確認してください。**

---

## 🔴 作業開始前の必須確認

### レベル1: 全ての作業で確認

```markdown
- [ ] 作業内容を理解している
- [ ] 影響範囲を把握している
- [ ] ロールバック方法を知っている
- [ ] バックアップが24時間以内に取得されている
- [ ] テスト環境で動作確認済み（該当する場合）
```

### レベル2: データ変更を伴う作業

```markdown
- [ ] データファイル（backend/data/*.json）を直接編集しない
- [ ] APIを使用したデータ変更である
- [ ] 変更前のデータスナップショットを取得している
- [ ] データロールバック手順を準備している
```

### レベル3: システム変更を伴う作業

```markdown
- [ ] ダウンタイムの見積もりが完了している
- [ ] ユーザーへの事前通知が完了している（必要な場合）
- [ ] メンテナンスウィンドウ内での作業である
- [ ] 緊急連絡先を確認している
```

---

## 📝 コミット前チェックリスト

### コード品質

```markdown
- [ ] コーディング規約に準拠している
  - Python: PEP 8準拠
  - JavaScript: ESLint準拠
- [ ] console.log / print文が本番コードに残っていない
- [ ] コメントが適切に記述されている
- [ ] ハードコードされた値がない（設定ファイル化）
- [ ] セキュリティ上の問題がない（後述の詳細チェック）
```

### テスト

```markdown
- [ ] 単体テストが全てパスしている
  ```bash
  pytest tests/ -v
  ```
- [ ] テストカバレッジが維持されている（目標: 80%以上）
  ```bash
  pytest --cov=. --cov-report=term
  ```
- [ ] 新規機能にはテストケースが追加されている
- [ ] エッジケースのテストが含まれている
- [ ] リグレッションテストが完了している
```

### Git操作

```markdown
- [ ] 変更内容を確認している
  ```bash
  git status
  git diff
  ```
- [ ] コミットメッセージが明確である
  - プレフィックス使用（機能:/修正:/改善: など）
  - 変更内容の簡潔な説明
  - 影響範囲の記述
- [ ] 不要なファイルが含まれていない
  - .env / .env.*
  - *.log
  - __pycache__/
  - *.pyc
- [ ] センシティブ情報が含まれていない
  - パスワード
  - APIキー
  - トークン
```

---

## 🧪 テスト実行必須項目

### バックエンドテスト

```bash
# 1. 全テストスイート実行
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend
pytest tests/ -v --cov=. --cov-report=term

# 2. 特定機能のテスト（該当する場合）
pytest tests/test_auth.py -v
pytest tests/test_knowledge.py -v
pytest tests/test_user.py -v

# 3. セキュリティテスト
pytest tests/test_security.py -v

# 4. パフォーマンステスト（重要な変更の場合）
pytest tests/test_performance.py -v
```

**成功基準:**
```markdown
- [ ] 全テストがパス（FAILED: 0件）
- [ ] カバレッジが80%以上
- [ ] 警告（WARNING）が増加していない
- [ ] テスト実行時間が大幅に増加していない（10%以内）
```

### フロントエンドテスト

```bash
# 1. ESLint実行
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/webui
npx eslint *.js

# 2. Jest実行（該当する場合）
npm test

# 3. ブラウザテスト
# - レイアウト崩れがないか
# - JavaScript エラーがないか（DevToolsコンソール確認）
# - レスポンシブ対応確認
```

**成功基準:**
```markdown
- [ ] ESLintエラー: 0件
- [ ] Jestテスト: 全てパス
- [ ] ブラウザコンソールエラー: 0件
- [ ] 主要ブラウザで動作確認（Chrome, Firefox, Safari）
```

---

## 💾 バックアップ確認

### 自動バックアップの確認

```bash
# 1. 最新バックアップの確認
ls -lth /backup/mirai-knowledge-system/daily/ | head -5

# 2. バックアップサイズの確認（異常に小さくないか）
du -sh /backup/mirai-knowledge-system/daily/$(ls -t /backup/mirai-knowledge-system/daily/ | head -1)

# 3. バックアップの整合性確認
sudo /usr/local/bin/verify_backup.sh
```

**確認項目:**
```markdown
- [ ] 最新バックアップが24時間以内に作成されている
- [ ] バックアップサイズが妥当（通常: 50MB-500MB）
- [ ] チェックサム検証が成功している
- [ ] JSON整合性チェックが成功している
```

### 手動バックアップの作成（重要な変更前）

```bash
# スナップショットバックアップ作成
sudo /usr/local/bin/backup_full.sh

# または特定ファイルのみバックアップ
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp /var/lib/mirai-knowledge-system/data/users.json \
   /var/lib/mirai-knowledge-system/data/users.json.backup.$TIMESTAMP
```

---

## 🔄 ロールバック準備

### ロールバック手順の確認

**コード変更のロールバック:**
```markdown
- [ ] ロールバック用のコマンドを把握している
  ```bash
  git log --oneline -5
  git revert <commit-hash>
  ```
- [ ] ロールバック後の動作確認手順を準備している
```

**データベース変更のロールバック:**
```markdown
- [ ] ロールバック用のSQLスクリプトを準備している
- [ ] バックアップからの復元手順を確認している
  ```bash
  sudo /usr/local/bin/restore_full.sh /backup/mirai-knowledge-system/daily/<timestamp>
  ```
```

**設定変更のロールバック:**
```markdown
- [ ] 設定ファイルのバックアップが取得されている
  ```bash
  sudo cp /etc/nginx/sites-available/mirai-knowledge-system \
          /etc/nginx/sites-available/mirai-knowledge-system.backup.$(date +%Y%m%d_%H%M%S)
  ```
- [ ] サービス再起動手順を確認している
```

---

## 🔒 セキュリティチェックリスト

### 認証・認可

```markdown
- [ ] 認証が必要なエンドポイントに @jwt_required() が適用されている
- [ ] 管理者専用機能に @admin_required() が適用されている
- [ ] パスワードがハッシュ化されている（平文保存していない）
- [ ] トークンの有効期限が適切に設定されている
```

### 入力検証

```markdown
- [ ] 全ての入力値がバリデーションされている
- [ ] SQLインジェクション対策が実施されている（ORMの適切な使用）
- [ ] XSS対策が実施されている（エスケープ処理）
- [ ] CSRF対策が実施されている（トークン検証）
- [ ] ファイルアップロードの検証が実施されている（拡張子・サイズ）
```

### データ保護

```markdown
- [ ] センシティブ情報がログに出力されていない
- [ ] エラーメッセージに内部情報が含まれていない
- [ ] API応答に不要な情報が含まれていない
- [ ] HTTPSが強制されている（本番環境）
```

### 依存関係

```markdown
- [ ] 既知の脆弱性を持つパッケージが含まれていない
  ```bash
  pip install pip-audit
  pip-audit
  ```
- [ ] 最新のセキュリティパッチが適用されている
```

---

## 📊 パフォーマンスチェック

### API応答時間

```bash
# 主要エンドポイントの応答時間確認
time curl -X GET https://localhost:443/api/v1/knowledges \
    -H "Authorization: Bearer <token>"

# または Apache Bench使用
ab -n 100 -c 10 https://localhost:443/api/v1/knowledges
```

**成功基準:**
```markdown
- [ ] 応答時間が要件を満たしている（目標: <500ms）
- [ ] 変更前と比較して大幅な劣化がない（10%以内）
```

### データベースクエリ

```markdown
- [ ] N+1クエリが発生していない
- [ ] 適切なインデックスが設定されている
- [ ] クエリ数が適切である（不要なクエリがない）
```

### リソース使用量

```bash
# メモリ使用量確認
free -h

# ディスク使用量確認
df -h

# プロセス確認
ps aux | grep gunicorn
```

**成功基準:**
```markdown
- [ ] メモリ使用量が80%未満
- [ ] ディスク使用量が80%未満
- [ ] CPUアイドルが20%以上
```

---

## 🚀 本番デプロイ前チェック

### デプロイ準備

```markdown
- [ ] リリースノートを作成している
- [ ] 変更内容をチーム/ユーザーに通知している
- [ ] デプロイ手順書を準備している
- [ ] ロールバック手順書を準備している
- [ ] メンテナンスウィンドウを確保している（必要な場合）
```

### デプロイ実行

```markdown
- [ ] 本番環境のバックアップを取得している
- [ ] サービス状態を確認している
  ```bash
  sudo systemctl status mirai-knowledge-system
  sudo systemctl status nginx
  ```
- [ ] デプロイコマンドを確認している
  ```bash
  git pull origin main
  pip install -r requirements.txt
  sudo systemctl restart mirai-knowledge-system
  ```
```

### デプロイ後確認

```markdown
- [ ] サービスが正常に起動している
  ```bash
  sudo systemctl status mirai-knowledge-system
  ```
- [ ] ヘルスチェックが成功している
  ```bash
  curl https://localhost:443/health
  ```
- [ ] ログにエラーがない
  ```bash
  tail -f /var/log/mirai-knowledge-system/error.log
  ```
- [ ] 主要機能の動作確認が完了している
  - ログイン
  - ナレッジ検索
  - ナレッジ作成
  - ユーザー管理（管理者）
- [ ] パフォーマンスが正常である
  ```bash
  ab -n 100 -c 10 https://localhost:443/api/v1/knowledges
  ```
```

---

## 📝 変更記録

### 変更記録テンプレート

```markdown
# 変更記録: YYYY-MM-DD HH:MM

## 変更概要
- 1行サマリ

## 変更理由
- なぜこの変更が必要だったか

## 変更内容
- 具体的な変更内容
- 変更ファイル一覧

## 影響範囲
- 影響を受ける機能
- ユーザー影響

## テスト結果
- [ ] 単体テスト: 全てパス
- [ ] 統合テスト: 全てパス
- [ ] カバレッジ: XX%

## ロールバック手順
- ロールバック方法の記述

## 実施者
- Claude Code (指示: <ユーザー名>)
```

---

## 🆘 緊急時の連絡先

```markdown
### システム管理者
- 名前: <管理者名>
- 連絡先: <電話番号/Email>

### 技術サポート
- Slack: #mks-support
- Email: support@example.com

### エスカレーション
- レベル1（軽微）: チームリード
- レベル2（重大）: システム管理者
- レベル3（致命的）: CTO/技術責任者
```

---

## 📚 チェックリスト使用例

### 例1: バグ修正

```markdown
✅ 作業開始前の必須確認
  ✅ 作業内容を理解している
  ✅ 影響範囲を把握している（POST /api/v1/knowledges）
  ✅ ロールバック方法を知っている（git revert）
  ✅ バックアップが24時間以内に取得されている
  ✅ テスト環境で動作確認済み

✅ コミット前チェックリスト
  ✅ PEP 8準拠
  ✅ print文なし
  ✅ コメント追加
  ✅ ハードコード値なし

✅ テスト実行
  ✅ pytest tests/ -v: PASSED
  ✅ カバレッジ: 91% (維持)
  ✅ 新規テストケース追加

✅ Git操作
  ✅ git diff 確認
  ✅ コミットメッセージ作成
  ✅ センシティブ情報なし

✅ デプロイ後確認
  ✅ サービス起動確認
  ✅ ヘルスチェック成功
  ✅ ログエラーなし
  ✅ 主要機能動作確認
```

---

## 🎯 チェックリストのカスタマイズ

プロジェクト固有のチェック項目を追加してください:

```markdown
### プロジェクト固有チェック

- [ ] <プロジェクト固有の要件1>
- [ ] <プロジェクト固有の要件2>
- [ ] <プロジェクト固有の要件3>
```

---

## 参考資料

- [本番運用ガイド](PRODUCTION_OPERATIONS.md)
- [タスクテンプレート](TASK_TEMPLATES.md)
- [エージェント役割分担](AGENT_ROLES.md)
- [運用手順](../../docs/11_運用保守(Operations)/01_運用手順(Operations-Guide).md)
- [変更管理](../../docs/12_変更管理(Change-Management)/01_変更管理(Change-Control).md)

---

**更新履歴**

| 日付 | バージョン | 変更内容 |
|------|-----------|----------|
| 2026-01-08 | 1.0 | 初版作成 - 安全チェックリスト策定 |
