# 本番運用ガイド - Production Operations

本番環境でのシステム変更・運用時のガイドラインです。
**本番環境では安全性と慎重さが最優先されます。**

---

## 🔴 本番環境における絶対ルール

### 1. データ保護の最優先

```bash
# ❌ 絶対にやってはいけないこと
rm -rf backend/data/*              # 本番データの直接削除
Edit(backend/data/users.json)      # データファイルの直接編集
Bash(shutdown *)                    # サーバーの強制停止
```

**必須ルール:**
- データファイル（backend/data/*.json）は直接編集しない → APIを使用
- .env ファイルは読み取らない
- データ変更前は必ずバックアップ確認
- 不可逆的な操作は必ずユーザー確認を得る

### 2. 変更前の確認事項

**全ての本番変更前にチェック:**

```markdown
- [ ] バックアップが24時間以内に取得されている
- [ ] テスト環境で動作確認済み（該当する場合）
- [ ] 影響範囲を理解している
- [ ] ロールバック手順を準備している
- [ ] ユーザーへの通知が必要か確認している
```

### 3. 変更の3段階承認

本番環境での変更は以下のフローに従う:

```
1. ユーザーからの明示的な指示確認
   ↓
2. Claude Codeによる影響範囲の説明とリスク提示
   ↓
3. ユーザーによる最終承認
```

---

## 🛡️ システム変更時の安全手順

### パターン1: コード変更（バックエンドAPI）

```bash
# ステップ1: 現在の状態確認
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend
git status
git log -3 --oneline

# ステップ2: テスト実行（変更前）
python -m pytest tests/ -v --cov=. --cov-report=term

# ステップ3: コード変更（Edit tool使用）
# (変更内容)

# ステップ4: テスト実行（変更後）
python -m pytest tests/ -v --cov=. --cov-report=term

# ステップ5: 本番環境での影響確認
# - エンドポイント変更の有無
# - データモデル変更の有無
# - 既存機能への影響

# ステップ6: コミット前の確認
git diff
git status

# ステップ7: コミット（ユーザー承認後）
git add <変更ファイル>
git commit -m "$(cat <<'EOF'
修正: <変更内容の概要>

- 詳細な変更内容
- 影響範囲
- テスト結果

Co-Authored-By: Claude Sonnet 4.5 (1M context) <noreply@anthropic.com>
EOF
)"
```

### パターン2: データベーススキーマ変更

```bash
# ⚠️ Critical: 本番DBスキーマ変更は高リスク操作

# ステップ1: 現在のスキーマ確認
Read(backend/models.py)

# ステップ2: マイグレーションスクリプト作成
# - 既存データの保持を確認
# - ロールバックスクリプトも作成

# ステップ3: テスト環境で検証
# - サンプルデータでテスト
# - マイグレーション成功確認
# - ロールバック成功確認

# ステップ4: 本番適用前チェックリスト
# - [ ] バックアップ取得済み
# - [ ] ダウンタイム見積もり完了
# - [ ] ロールバック手順確認済み
# - [ ] ユーザー通知済み

# ステップ5: 本番適用（ユーザー承認後）
# - メンテナンスモード設定
# - マイグレーション実行
# - 動作確認
# - メンテナンスモード解除
```

### パターン3: 設定変更（.env, Nginx, systemd）

```bash
# ⚠️ 設定変更はサービス再起動が必要

# ステップ1: 現在の設定バックアップ
sudo cp /etc/nginx/sites-available/mirai-knowledge-system \
        /etc/nginx/sites-available/mirai-knowledge-system.backup.$(date +%Y%m%d_%H%M%S)

# ステップ2: 設定ファイル編集
# (Edit tool使用)

# ステップ3: 設定ファイル検証
sudo nginx -t  # Nginx設定の文法チェック

# ステップ4: サービス再起動（ユーザー承認後）
sudo systemctl reload nginx  # グレースフルリロード推奨

# ステップ5: 動作確認
curl -v https://localhost:443/health
tail -f /var/log/nginx/error.log
```

---

## 🔄 ロールバック手順

### コード変更のロールバック

```bash
# パターン1: 最新コミットの取り消し（プッシュ前）
git reset --soft HEAD~1  # コミット取り消し、変更は保持
git reset --hard HEAD~1  # コミット取り消し、変更も破棄

# パターン2: プッシュ済みコミットの取り消し
git revert HEAD  # 新しいコミットで前のコミットを打ち消す

# パターン3: 特定コミットまで戻す
git log --oneline -10
git revert <commit-hash>
```

### サービスのロールバック

```bash
# ステップ1: サービス停止
sudo systemctl stop mirai-knowledge-system

# ステップ2: 以前のバージョンにチェックアウト
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend
git checkout <previous-commit-hash>

# ステップ3: 依存関係の再インストール（必要な場合）
source venv/bin/activate
pip install -r requirements.txt

# ステップ4: サービス起動
sudo systemctl start mirai-knowledge-system

# ステップ5: 動作確認
curl https://localhost:443/health
sudo systemctl status mirai-knowledge-system
```

### データベースのロールバック

```bash
# ⚠️ データロールバックは最も慎重に

# オプション1: バックアップからの復元
sudo /usr/local/bin/restore_full.sh /backup/mirai-knowledge-system/daily/<timestamp>

# オプション2: 特定ファイルのみ復元
RESTORE_SOURCE="/backup/mirai-knowledge-system/daily/<timestamp>"
TARGET_FILE="knowledges.json"
DATA_DIR="/var/lib/mirai-knowledge-system/data"

# 現在のファイルをバックアップ
cp "$DATA_DIR/$TARGET_FILE" "$DATA_DIR/${TARGET_FILE}.before_restore"

# バックアップから復元
cp "$RESTORE_SOURCE/data/$TARGET_FILE" "$DATA_DIR/$TARGET_FILE"

# パーミッション設定
chown www-data:www-data "$DATA_DIR/$TARGET_FILE"
chmod 644 "$DATA_DIR/$TARGET_FILE"

# JSON整合性チェック
python3 -c "import json; json.load(open('$DATA_DIR/$TARGET_FILE'))"

# サービス再起動
sudo systemctl restart mirai-knowledge-system
```

---

## 🚨 緊急時対応フロー

### レベル1: サービス停止（Critical）

**症状:** APIが応答しない、500エラー多発

```bash
# 1. 現状確認
sudo systemctl status mirai-knowledge-system
sudo journalctl -u mirai-knowledge-system -n 100 --no-pager

# 2. エラーログ確認
tail -n 100 /var/log/mirai-knowledge-system/error.log

# 3. 応急処置: サービス再起動
sudo systemctl restart mirai-knowledge-system

# 4. 復旧確認
curl https://localhost:443/health

# 5. 原因調査（再起動で復旧した場合）
# - メモリリーク確認
# - ディスク容量確認
# - データベース接続確認
```

### レベル2: データ破損（High）

**症状:** JSONファイル破損、データ読み込みエラー

```bash
# 1. サービス停止
sudo systemctl stop mirai-knowledge-system

# 2. 破損ファイル特定
cd /var/lib/mirai-knowledge-system/data
for file in *.json; do
    echo "Checking $file..."
    python3 -c "import json; json.load(open('$file'))" || echo "ERROR: $file"
done

# 3. 最新バックアップから復元
LATEST_BACKUP=$(ls -t /backup/mirai-knowledge-system/daily/ | head -1)
sudo /usr/local/bin/restore_full.sh /backup/mirai-knowledge-system/daily/$LATEST_BACKUP

# 4. 復旧確認
sudo systemctl start mirai-knowledge-system
curl https://localhost:443/health
```

### レベル3: セキュリティインシデント（Critical）

**症状:** 不正アクセス検知、データ漏洩の疑い

```bash
# 1. 即座にネットワーク隔離
sudo systemctl stop nginx
sudo systemctl stop mirai-knowledge-system

# 2. アクセスログ確認
tail -n 1000 /var/log/nginx/access.log | grep -E "(POST|DELETE|PUT)" > /tmp/suspicious_access.log

# 3. 認証ログ確認
grep "Authentication failed" /var/log/mirai-knowledge-system/auth.log

# 4. セキュリティ専門家へエスカレーション
# - ログファイル保全
# - インシデントレポート作成
# - 影響範囲調査

# 5. 復旧計画（承認後）
# - パスワードリセット
# - セキュリティパッチ適用
# - サービス再開
```

---

## 📊 本番環境での監視・確認

### 日次チェック（自動化推奨）

```bash
#!/bin/bash
# daily_health_check.sh

echo "=== Daily Health Check $(date) ==="

# 1. サービス稼働確認
systemctl is-active mirai-knowledge-system && echo "✓ Service is running" || echo "✗ Service is DOWN"

# 2. ディスク容量確認
df -h / | tail -1 | awk '{if ($5+0 > 80) print "⚠ Disk usage high: "$5; else print "✓ Disk usage OK: "$5}'

# 3. メモリ使用量確認
free -h | grep Mem | awk '{print "Memory: "$3"/"$2}'

# 4. エラーログ確認（過去24時間）
ERROR_COUNT=$(find /var/log/mirai-knowledge-system/ -name "error.log" -mtime -1 -exec grep -c "ERROR" {} \; | awk '{sum+=$1} END {print sum}')
echo "Errors (24h): $ERROR_COUNT"

# 5. バックアップ確認
LATEST_BACKUP=$(ls -t /backup/mirai-knowledge-system/daily/ | head -1)
echo "Latest backup: $LATEST_BACKUP"

# 6. API疎通確認
curl -s -o /dev/null -w "API Response: %{http_code}\n" https://localhost:443/health
```

### 週次チェック

```bash
# 1. バックアップリストアテスト
sudo /usr/local/bin/verify_backup.sh

# 2. セキュリティスキャン
# - 依存関係の脆弱性チェック
pip list --outdated

# 3. ログローテーション確認
ls -lh /var/log/mirai-knowledge-system/

# 4. データベース整合性チェック
cd /var/lib/mirai-knowledge-system/data
for file in *.json; do
    python3 -c "import json; json.load(open('$file'))"
done
```

---

## 📝 変更記録テンプレート

本番環境での変更は必ず記録を残す:

```markdown
# 変更記録: YYYY-MM-DD

## 変更概要
- 変更内容の1行サマリ

## 変更理由
- なぜこの変更が必要だったか

## 変更内容
- 具体的な変更内容
- 変更したファイル一覧
- 設定変更項目

## 影響範囲
- 影響を受ける機能
- ダウンタイムの有無
- ユーザー影響

## テスト結果
- テスト環境での検証結果
- 本番環境での動作確認結果

## ロールバック手順
- 問題発生時のロールバック手順

## 実施者
- Claude Code (指示: ユーザー名)

## 承認
- ユーザー承認取得日時
```

---

## 🎯 本番運用のベストプラクティス

### 1. 変更は小さく頻繁に

```bash
# Good: 1機能ずつコミット
git commit -m "修正: ユーザー検索のページネーション不具合"

# Bad: 複数機能をまとめてコミット
git commit -m "色々修正"
```

### 2. テストカバレッジを維持

```bash
# 変更前のカバレッジ確認
pytest --cov=. --cov-report=term | grep TOTAL

# 変更後も同等以上のカバレッジを維持
```

### 3. ログを活用

```python
# Good: 構造化ログ
logger.info("User login successful", extra={
    "user_id": user.id,
    "ip_address": request.remote_addr
})

# Bad: print文
print("User logged in")
```

### 4. 本番環境での直接デバッグは避ける

```bash
# ❌ 本番環境で直接実験
python app_v2.py  # デバッグモード

# ✅ ログとメトリクスで調査
tail -f logs/error.log
curl https://localhost:443/metrics
```

---

## 参考資料

- [運用手順](../../docs/11_運用保守(Operations)/01_運用手順(Operations-Guide).md)
- [インシデント対応](../../docs/11_運用保守(Operations)/02_インシデント対応(Incident-Response).md)
- [バックアップ・リストア手順](../../docs/11_運用保守(Operations)/08_Backup-Restore-Procedures.md)
- [変更管理](../../docs/12_変更管理(Change-Management)/01_変更管理(Change-Control).md)

---

**更新履歴**

| 日付 | バージョン | 変更内容 |
|------|-----------|----------|
| 2026-01-08 | 1.0 | 初版作成 - 本番運用ガイドライン策定 |
