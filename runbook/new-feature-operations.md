# 新機能導入運用手順 (New Feature Operations Guide)

## 概要

本ドキュメントは、新機能導入に伴う運用手順をまとめたものです。新機能の監視方法、トラブルシューティング、メンテナンス手順を含みます。

### 新機能の概要
- **機能名**: [新機能名]（例: ドキュメント共有機能）
- **目的**: [機能の目的]
- **影響範囲**: [影響するコンポーネント、ユーザー]
- **依存関係**: [必要なバックエンド、DB変更など]

## 監視方法

### メトリクス監視
新機能の導入に伴い、以下のメトリクスを監視します：

| メトリクス | 閾値 | 監視ツール | 対応 |
|-----------|------|-----------|------|
| 新機能APIレスポンスタイム | > 3秒 | Prometheus | Warningアラート |
| 新機能使用率 | < 10% (導入後1ヶ月) | Grafana | Info通知 |
| 新機能エラー率 | > 5% | ELK Stack | Criticalアラート |
| 新機能データベースクエリ時間 | > 2秒 | PostgreSQL監視 | Warningアラート |

### ログ監視
- **ログレベル**: INFO, WARNING, ERROR
- **フィルタ**: 新機能関連のログ（キーワード: "new-feature"）
- **監視ツール**: Loki / ELK Stack
- **通知**: Slackチャンネル #new-feature-alerts

### アラート設定
新機能専用のアラートを追加：

```yaml
# prometheus/rules.yml に追加
groups:
  - name: new-feature-alerts
    rules:
      - alert: NewFeatureHighErrorRate
        expr: rate(new_feature_errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "新機能エラー率が高くなっています"
          description: "新機能のエラー率が5%を超えています"

      - alert: NewFeatureSlowResponse
        expr: histogram_quantile(0.95, rate(new_feature_request_duration_seconds_bucket[5m])) > 3
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "新機能レスポンスが遅いです"
          description: "新機能の95パーセンタイルレスポンス時間が3秒を超えています"
```

## トラブルシューティング

### 一般的な障害パターン

#### 1. 新機能APIエラー (HTTP 5xx)
**症状**: 新機能使用時に500エラーが発生

**診断手順**:
1. ログ確認
   ```bash
   grep "new-feature" /var/log/mks-backend/error.log | tail -20
   ```

2. バックエンドサービスステータス確認
   ```bash
   systemctl status mks-backend
   ```

3. データベース接続確認
   ```bash
   psql -U mks_user -d mks_db -c "SELECT 1;"
   ```

**対応手順**:
1. サービス再起動
   ```bash
   sudo systemctl restart mks-backend
   ```

2. キャッシュクリア（必要な場合）
   ```bash
   redis-cli FLUSHALL
   ```

3. 復旧確認
   ```bash
   curl -f http://localhost:5100/api/v1/new-feature/health
   ```

#### 2. 新機能パフォーマンス低下
**症状**: レスポンスタイムが遅い

**診断手順**:
1. パフォーマンスメトリクス確認
   ```bash
   curl http://localhost:9100/metrics | grep new_feature
   ```

2. データベースクエリ分析
   ```bash
   # PostgreSQL slow query log確認
   tail -f /var/log/postgresql/postgresql-slow.log
   ```

3. リソース使用率確認
   ```bash
   top -p $(pgrep -f gunicorn)
   ```

**対応手順**:
1. クエリ最適化
2. インデックス追加（DBA判断）
3. スケールアップ検討

#### 3. 新機能データ不整合
**症状**: データが正しく表示されない

**診断手順**:
1. データベース整合性チェック
   ```bash
   psql -U mks_user -d mks_db -c "SELECT COUNT(*) FROM new_feature_table;"
   ```

2. キャッシュ確認
   ```bash
   redis-cli KEYS "new-feature:*"
   ```

**対応手順**:
1. データ修復スクリプト実行
   ```bash
   python scripts/fix_new_feature_data.py
   ```

2. キャッシュ無効化
   ```bash
   redis-cli DEL new-feature:*
   ```

### エスカレーションフロー

```
障害検知 → 一次対応（SRE） → 二次対応（開発チーム）
     ↓
復旧不可 → マネージャー通知 → 顧客影響評価
     ↓
恒久対策立案 → リリース計画
```

## メンテナンス手順

### 定期メンテナンス

#### 毎週メンテナンス
- [ ] 新機能使用統計確認
- [ ] パフォーマンスメトリクスレビュー
- [ ] エラーログ分析
- [ ] ユーザーフィードバック確認

#### 毎月メンテナンス
- [ ] 新機能データクリーンアップ
  ```bash
  # 古い一時データ削除
  psql -U mks_user -d mks_db -c "DELETE FROM new_feature_temp WHERE created_at < NOW() - INTERVAL '30 days';"
  ```
- [ ] キャッシュ最適化
  ```bash
  # Redisメモリ使用量確認
  redis-cli INFO memory
  ```
- [ ] バックアップ検証
  ```bash
  # 新機能データ含むバックアップテスト
  bash scripts/restore.sh --test new-feature
  ```

#### 毎四半期メンテナンス
- [ ] 新機能改善計画策定
- [ ] パフォーマンスチューニング
- [ ] セキュリティレビュー
- [ ] ドキュメント更新

### メンテナンススクリプト

#### 新機能ヘルスチェック
```bash
#!/bin/bash
# scripts/new-feature-health-check.sh

echo "=== 新機能ヘルスチェック ==="

# APIエンドポイント確認
curl -f http://localhost:5100/api/v1/new-feature/health || exit 1

# データベース接続確認
psql -U mks_user -d mks_db -c "SELECT COUNT(*) FROM new_feature_table;" > /dev/null || exit 1

# パフォーマンスチェック
RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" http://localhost:5100/api/v1/new-feature/test)
if (( $(echo "$RESPONSE_TIME > 3.0" | bc -l) )); then
    echo "WARNING: レスポンスタイムが遅いです: ${RESPONSE_TIME}s"
    exit 1
fi

echo "=== 新機能ヘルスチェック完了 ==="
```

#### 新機能データメンテナンス
```bash
#!/bin/bash
# scripts/new-feature-maintenance.sh

echo "=== 新機能データメンテナンス ==="

# データクリーンアップ
psql -U mks_user -d mks_db << EOF
DELETE FROM new_feature_logs WHERE timestamp < NOW() - INTERVAL '90 days';
VACUUM ANALYZE new_feature_table;
EOF

# 統計情報更新
psql -U mks_user -d mks_db -c "ANALYZE new_feature_table;"

echo "=== 新機能データメンテナンス完了 ==="
```

## 導入後の監視期間

### Phase 1: 導入直後 (1-7日)
- **監視レベル**: 高
- **対応時間**: Critical 30分以内
- **監視項目**: 全メトリクス、ユーザー影響

### Phase 2: 安定化期間 (1-4週間)
- **監視レベル**: 中
- **対応時間**: Critical 1時間以内
- **監視項目**: 主要メトリクス、エラー率

### Phase 3: 通常運用 (1ヶ月以降)
- **監視レベル**: 通常
- **対応時間**: SLA準拠
- **監視項目**: 定期レポートベース

## 関連リソース

- [アラート対応手順](./alert-response.md)
- [障害対応フロー](./incident-response.md)
- [定期メンテナンス](./maintenance-checklist.md)
- [バックアップ手順](./rollback-procedures.md)
- [監視ダッシュボード](https://monitoring.example.com/new-feature)
- [ログ集計](https://logs.example.com/new-feature)

## 変更履歴

| 日付 | バージョン | 変更内容 | 担当 |
|------|-----------|----------|------|
| 2025-01-09 | 1.0 | 新機能導入運用手順作成 | Ops Agent |</content>
<parameter name="filePath">Z:\Mirai-Knowledge-Systems\runbook\new-feature-operations.md