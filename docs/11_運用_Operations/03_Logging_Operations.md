# Mirai Knowledge Systems - ログ運用マニュアル

**Phase**: G-15
**対象**: 運用担当者、SRE、DevOps
**Version**: 1.6.0
**Date**: 2026-02-17

---

## 📋 目次

1. [ログアーキテクチャ](#ログアーキテクチャ)
2. [日常運用](#日常運用)
3. [トラブルシューティング](#トラブルシューティング)
4. [アラート対応](#アラート対応)
5. [ログ保全・監査](#ログ保全監査)

---

## ログアーキテクチャ

### ログ出力先

| 環境 | 形式 | 出力先 | ローテーション |
|------|------|--------|--------------|
| **本番** | JSON | `/var/log/mirai-knowledge/app.log` | 100MB × 10世代 |
| **開発** | Plain Text | Console（標準出力） | なし |

### ログレベル

| レベル | 目的 | アクション |
|--------|------|-----------|
| `INFO` | 通常動作記録 | 監視のみ |
| `WARNING` | 警告（処理継続） | 調査推奨 |
| `ERROR` | エラー（処理失敗） | **即座調査** |
| `CRITICAL` | 致命的エラー | **緊急対応** |

---

## 日常運用

### 1. ログ確認（日次チェック）

**ERROR ログ確認**（毎日9:00実施）:
```bash
# 過去24時間のERRORログ
jq 'select(.level == "ERROR")' < /var/log/mirai-knowledge/app.log | \
  jq -s 'group_by(.message) | map({message: .[0].message, count: length}) | sort_by(.count) | reverse'

# 出力例:
# [
#   {"message": "Database connection timeout", "count": 15},
#   {"message": "MS365 sync failed", "count": 3}
# ]
```

**アクション**:
- Count > 10: 即座調査（パターンエラー）
- Count 1-10: 監視継続
- Count 0: 正常 ✅

---

### 2. ディスク容量監視（週次チェック）

**ログ容量確認**（毎週月曜9:00実施）:
```bash
# ログディレクトリ容量
du -sh /var/log/mirai-knowledge/

# 出力例: 850M /var/log/mirai-knowledge/

# ローテーションファイル確認
ls -lh /var/log/mirai-knowledge/app.log*
```

**閾値**:
- < 1GB: 正常 ✅
- 1GB - 1.5GB: 監視強化
- > 1.5GB: **即座対応**（手動削除またはローテーション設定確認）

---

### 3. パフォーマンス監視（週次チェック）

**遅いリクエスト検出**（毎週月曜9:00実施）:
```bash
# 過去7日間で1秒超えリクエスト
jq 'select(.duration_ms > 1000) | {timestamp, endpoint, duration_ms, correlation_id}' < app.log | \
  jq -s 'sort_by(.duration_ms) | reverse | .[:10]'

# 出力例:
# [
#   {"timestamp": "2026-02-17T14:32:01", "endpoint": "get_related_knowledge", "duration_ms": 1500.2, "correlation_id": "..."},
#   ...
# ]
```

**アクション**:
- 1秒超えが10件以上/日: パフォーマンス調査
- 2秒超えが1件以上: **即座調査**

---

## トラブルシューティング

### シナリオ1: ユーザーがエラー報告

**報告例**: 「ナレッジ登録時にエラーが出ました（2026-02-17 14:32頃）」

**Step 1**: タイムスタンプでログ検索
```bash
# 時刻範囲でERROR抽出
jq 'select(.level == "ERROR") | select(.timestamp | startswith("2026-02-17T14:3"))' < app.log

# ユーザー名で絞り込み
jq 'select(.username == "報告者名") | select(.timestamp | startswith("2026-02-17T14:3"))' < app.log
```

**Step 2**: Correlation IDを特定
```bash
# 出力例:
# {"correlation_id": "a7f3c9e1-...", "message": "Knowledge creation failed", "exception": "ValidationError: ..."}
```

**Step 3**: Correlation IDで全ログ抽出
```bash
# リクエスト全体のログ追跡
jq 'select(.correlation_id == "a7f3c9e1-4b2d-4a5e-8f1c-3d2e9b6c4a8f")' < app.log
```

**Step 4**: 根本原因特定
- Stack traceを確認
- 直前のINFO/WARNINGログで状態確認
- SQLクエリログがあれば検証

---

### シナリオ2: API全体が遅い

**報告例**: 「ダッシュボードの表示が遅いです」

**Step 1**: 平均レスポンスタイム確認
```bash
# 過去1時間のリクエスト完了ログ
jq 'select(.message == "Request completed") | .duration_ms' < app.log | \
  awk '{sum+=$1; count++} END {print "Average:", sum/count, "ms"}'

# 出力例: Average: 150.5 ms
```

**Step 2**: 遅いエンドポイント特定
```bash
# エンドポイント別平均時間
jq 'select(.message == "Request completed") | {endpoint, duration_ms}' < app.log | \
  jq -s 'group_by(.endpoint) | map({endpoint: .[0].endpoint, avg: (map(.duration_ms) | add / length)}) | sort_by(.avg) | reverse'

# 出力例:
# [
#   {"endpoint": "get_related_knowledge", "avg": 850.2},
#   {"endpoint": "get_knowledge_tags", "avg": 320.5},
#   ...
# ]
```

**Step 3**: キャッシュヒット率確認
```bash
# キャッシュヒットログ検索
grep -c "Cache hit" /var/log/mirai-knowledge/app.log
grep -c "Cache set" /var/log/mirai-knowledge/app.log

# ヒット率計算
# Hit Rate = Hits / (Hits + Misses) × 100%
```

**Step 4**: 対策実施
- ヒット率 < 50%: キャッシュTTL延長検討
- 特定EP遅い: コード最適化またはキャッシュ追加

---

### シナリオ3: セキュリティインシデント

**報告例**: 「不正ログイン試行の疑い」

**Step 1**: 認証失敗ログ抽出
```bash
# 過去24時間の認証失敗
jq 'select(.message | contains("authentication failed"))' < app.log

# IPアドレス別集計
jq 'select(.message | contains("authentication failed")) | .ip_address' < app.log | \
  sort | uniq -c | sort -nr

# 出力例:
# 15 192.168.0.200  ← 疑わしいIP
#  3 192.168.0.145
#  1 192.168.0.187
```

**Step 2**: 疑わしいIPの全アクティビティ
```bash
jq 'select(.ip_address == "192.168.0.200")' < app.log | jq -s 'sort_by(.timestamp)'
```

**Step 3**: ブロック判断
- 15回/日以上: **即座IPブロック**（ファイアウォール設定）
- 5-15回/日: 監視継続
- <5回/日: 誤入力の可能性

---

## アラート対応

### Alert 1: ERROR Spike（エラー急増）

**トリガー**: 過去5分間でERROR > 10件

**Grafanaアラート設定**:
```yaml
alert: ErrorSpike
expr: rate({job="mirai-knowledge-backend"} | json | level="ERROR" [5m]) > 2
for: 2m
annotations:
  summary: "ERROR spike detected"
```

**対応手順**:
1. Recent Errorsパネル確認（Grafana）
2. エラーメッセージでパターン特定
3. Correlation IDで初回エラーの根本原因調査
4. 必要に応じてサービス再起動
5. インシデントレポート作成

---

### Alert 2: Slow Requests（遅延急増）

**トリガー**: p95レスポンスタイム > 2秒

**Grafanaアラート設定**:
```yaml
alert: SlowRequests
expr: histogram_quantile(0.95, rate(duration_ms_bucket[5m])) > 2000
for: 5m
```

**対応手順**:
1. Slow Queriesパネル確認（Grafana）
2. 遅いエンドポイント特定
3. キャッシュヒット率確認
4. Redisメモリ使用量確認
5. 必要に応じてRedis再起動またはキャッシュクリア

---

### Alert 3: Disk Full（ディスク容量不足）

**トリガー**: `/var/log`パーティション使用率 > 85%

**対応手順**:
```bash
# 1. ログディレクトリ容量確認
du -sh /var/log/mirai-knowledge/

# 2. 古いログ削除（90日以前）
find /var/log/mirai-knowledge/ -name "app.log.*" -mtime +90 -delete

# 3. 手動ローテーション実行
python3 -c "from logging.handlers import RotatingFileHandler; \
  h = RotatingFileHandler('/var/log/mirai-knowledge/app.log', maxBytes=100*1024*1024, backupCount=10); \
  h.doRollover()"

# 4. ディスク容量再確認
df -h /var/log
```

---

## ログ保全・監査

### 法的要件（90日保持）

**バックアップスケジュール**:
```bash
# 週次バックアップ（毎週日曜3:00 AM）
0 3 * * 0 tar -czf /backup/logs/mirai-knowledge-$(date +\%Y\%m\%d).tar.gz /var/log/mirai-knowledge/
```

**保持ポリシー**:
- アクティブログ: 10世代（約1GB）
- アーカイブログ: 90日間（圧縮）
- 90日経過: 自動削除

---

### 監査ログ抽出

**ユーザーアクティビティ監査**:
```bash
# 特定ユーザーの全操作
jq 'select(.username == "admin") | {timestamp, message, method, path, status_code}' < app.log > audit_admin.json

# 権限昇格操作
jq 'select(.message | contains("permission granted") or contains("role assigned"))' < app.log

# データ削除操作
jq 'select(.method == "DELETE" and .status_code == 200)' < app.log
```

**セキュリティ監査**:
```bash
# 認証失敗（ブルートフォース検出）
jq 'select(.message | contains("authentication failed")) | {timestamp, ip_address, username}' < app.log | \
  jq -s 'group_by(.ip_address) | map({ip: .[0].ip_address, attempts: length}) | sort_by(.attempts) | reverse'

# 不正アクセス試行（403 Forbidden）
jq 'select(.status_code == 403) | {timestamp, username, path, ip_address}' < app.log
```

---

## ベストプラクティス

### ✅ DO（推奨）

1. **定期的なログレビュー**:
   - 日次: ERRORログ確認（9:00 AM）
   - 週次: パフォーマンス分析（月曜9:00 AM）
   - 月次: セキュリティ監査（第1月曜）

2. **Correlation IDを保存**:
   - ユーザー報告時に correlation_id を聞く
   - Grafana URLに correlation_id をパラメータ化

3. **ログアーカイブ**:
   - 週次バックアップ（日曜3:00 AM）
   - 90日後自動削除

### ❌ DON'T（非推奨）

1. **本番環境でDEBUGレベル使用禁止**:
   ```bash
   # ❌ BAD
   MKS_LOG_LEVEL=DEBUG  # ログ肥大化

   # ✅ GOOD
   MKS_LOG_LEVEL=INFO  # 本番デフォルト
   ```

2. **ログファイル手動削除禁止**:
   ```bash
   # ❌ BAD
   rm /var/log/mirai-knowledge/app.log  # 証跡消失

   # ✅ GOOD
   # ローテーション自動化に任せる
   ```

---

## 付録

### A. ログクエリチートシート

| 目的 | コマンド |
|------|---------|
| ERROR抽出 | `jq 'select(.level == "ERROR")' < app.log` |
| ユーザー検索 | `jq 'select(.username == "admin")' < app.log` |
| 時刻範囲 | `jq 'select(.timestamp \| startswith("2026-02-17T14:"))' < app.log` |
| 遅いリクエスト | `jq 'select(.duration_ms > 1000)' < app.log` |
| エンドポイント | `jq 'select(.endpoint == "get_knowledge")' < app.log` |
| Correlation ID | `jq 'select(.correlation_id == "...")' < app.log` |

### B. 緊急連絡先

| 役割 | 担当者 | 連絡先 | 対応範囲 |
|------|--------|--------|----------|
| システム管理者 | 有藤 健太郎 | internal | ログ分析、インシデント対応 |
| SRE | - | - | パフォーマンス調査 |
| セキュリティ | - | - | 不正アクセス対応 |

---

**最終更新**: 2026-02-17
**バージョン**: Phase G-15 Phase 2
**レビュー**: code-reviewer agent ✅
