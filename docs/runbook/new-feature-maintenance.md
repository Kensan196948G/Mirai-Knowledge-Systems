# 新機能メンテナンス手順

## 概要
新機能（ナレッジ共有機能）の定期メンテナンス手順です。

## メンテナンススケジュール

### 毎週
- [ ] ヘルスチェック実行
- [ ] ログ容量確認
- [ ] パフォーマンスレポート確認

### 毎月
- [ ] データクリーンアップ
- [ ] 統計情報更新
- [ ] バックアップ検証

### 毎四半期
- [ ] セキュリティパッチ適用
- [ ] パフォーマンス最適化
- [ ] ドキュメント更新

## メンテナンス手順

### データクリーンアップ
```bash
# スクリプト実行
bash scripts/new-feature-maintenance.sh

# 手動実行の場合
psql -U mks_user -d mks_db << EOF
DELETE FROM new_feature_logs WHERE timestamp < NOW() - INTERVAL '90 days';
VACUUM ANALYZE new_feature_table;
EOF
```

### バックアップ検証
```bash
# バックアップ確認
ls -la /backup/mks/new-feature-*

# リストアテスト
pg_restore -U mks_user -d test_db /backup/mks/new-feature-latest.dump
```

### パフォーマンス最適化
1. インデックス確認
   ```sql
   SELECT * FROM pg_stat_user_indexes WHERE tablename = 'new_feature_table';
   ```
2. クエリ最適化
3. キャッシュ設定調整

### セキュリティチェック
- 依存パッケージ更新
- 脆弱性スキャン
- アクセス権限確認

## メンテナンスチェックリスト

### 前準備
- [ ] メンテナンス予告通知
- [ ] バックアップ取得
- [ ] テスト環境検証

### 実行中
- [ ] サービス停止（必要な場合）
- [ ] スクリプト実行
- [ ] ログ監視

### 後処理
- [ ] サービス起動確認
- [ ] ヘルスチェック実行
- [ ] ユーザー通知

## ロールバック手順
万一の障害発生時の切り戻し手順

1. バックアップからリストア
   ```bash
   bash scripts/restore.sh <backup-date>
   ```
2. サービス再起動
   ```bash
   sudo systemctl restart mks-backend
   ```
3. 検証
   ```bash
   bash scripts/new-feature-health-check.sh
   ```

## 関連スクリプト
- `scripts/new-feature-maintenance.sh`: データメンテナンス
- `scripts/new-feature-health-check.sh`: ヘルスチェック
- `scripts/backup.sh`: バックアップ
- `scripts/restore.sh`: リストア