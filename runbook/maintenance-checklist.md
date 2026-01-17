# 定期メンテナンスチェックリスト (Maintenance Checklist)

## 概要
システムの安定稼働とセキュリティを維持するための定期メンテナンス手順です。

## 毎週メンテナンス

### 月曜日 02:00 - システムチェック
- [ ] **ログディスク容量確認**
  ```bash
  df -h /var/log
  du -sh /var/log/mks-backend/
  ```
  - 容量 > 80%: ログローテーション実行
  - 容量 > 90%: 緊急対応

- [ ] **バックアップ成功確認**
  ```bash
  ls -la /backup/mks/
  # 最新バックアップが24時間以内か確認
  find /backup/mks/ -name "*.dump" -mtime -1
  ```
  - 失敗時: 手動バックアップ実行

- [ ] **SSL証明書期限確認**
  ```bash
  certbot certificates
  openssl x509 -in /etc/letsencrypt/live/example.com/cert.pem -text | grep "Not After"
  ```
  - 期限 < 30日: 更新実行

- [ ] **パフォーマンスモニタリング**
  ```bash
  # CPU使用率
  top -bn1 | grep "Cpu(s)"
  
  # メモリ使用率
  free -h
  
  # ディスクI/O
  iostat -x 1 5
  ```

### 水曜日 02:00 - セキュリティチェック
- [ ] **セキュリティパッチ適用確認**
  ```bash
  apt list --upgradable | grep -i security
  yum check-update | grep -i security
  ```

- [ ] **ファイアウォール設定確認**
  ```bash
  ufw status
  iptables -L
  ```

- [ ] **アクセスログ監査**
  ```bash
  # 不審なアクセス確認
  grep " 40[0-9] " /var/log/nginx/access.log | tail -20
  
  # ブルートフォース攻撃確認
  grep "POST /api/v1/auth/login" /var/log/nginx/access.log | grep " 401 " | wc -l
  ```

## 毎月メンテナンス

### 第1月曜日 03:00 - システム更新
- [ ] **依存パッケージのアップデート**
  ```bash
  # Pythonパッケージ更新
  pip list --outdated
  pip install --upgrade -r requirements.txt
  
  # OSパッケージ更新
  apt update && apt upgrade -y
  ```

- [ ] **セキュリティパッチの適用**
  ```bash
  # セキュリティ更新のみ
  apt update && apt install --only-upgrade $(apt list --upgradable | grep -i security | cut -d/ -f1)
  ```

- [ ] **ログローテーション確認**
  ```bash
  # logrotate設定確認
  cat /etc/logrotate.d/mks-backend
  
  # 手動実行テスト
  logrotate -f /etc/logrotate.d/mks-backend
  ```

- [ ] **バックアップテスト**
  ```bash
  # バックアップ実行
  bash scripts/backup.sh
  
  # リストアテスト（別環境で）
  bash scripts/restore.sh --test
  ```

### 第3月曜日 03:00 - パフォーマンス最適化
- [ ] **データベース最適化**
  ```bash
  # VACUUM ANALYZE実行
  psql -U mks_user -d mks_db -c "VACUUM ANALYZE;"
  
  # インデックス確認
  psql -U mks_user -d mks_db -c "SELECT * FROM pg_stat_user_indexes;"
  ```

- [ ] **キャッシュクリア**
  ```bash
  # Redisキャッシュクリア
  redis-cli FLUSHALL
  
  # アプリケーションキャッシュクリア
  curl -X POST http://localhost:5100/api/v1/admin/cache/clear
  ```

- [ ] **一時ファイルクリーンアップ**
  ```bash
  # 古いログ削除
  find /var/log/mks-backend/ -name "*.log.*" -mtime +30 -delete
  
  # 一時ファイル削除
  find /tmp -name "mks_*" -mtime +7 -delete
  ```

## 毎四半期メンテナンス

### 第1四半期 - 包括的レビュー
- [ ] **DR（災害復旧）訓練**
  ```bash
  # フェイルオーバーテスト
  # バックアップからの完全リストアテスト
  # RTO/RPO測定
  ```

- [ ] **アラート設定の見直し**
  ```bash
  # アラート閾値調整
  # 新しいアラートルール追加
  # 誤検知率分析
  ```

- [ ] **Runbook の更新**
  ```bash
  # 手順の正確性確認
  # 新しいシナリオ追加
  # チームフィードバック反映
  ```

- [ ] **セキュリティ監査**
  ```bash
  # 脆弱性スキャン
  # アクセス権限確認
  # 暗号化設定確認
  ```

### 第2四半期 - パフォーマンスレビュー
- [ ] **容量計画見直し**
  ```bash
  # ディスク使用量トレンド分析
  # CPU/メモリ使用量予測
  # スケーリング計画策定
  ```

- [ ] **バックアップ戦略見直し**
  ```bash
  # バックアップ頻度調整
  # 保存期間見直し
  # バックアップ方式改善
  ```

### 第3四半期 - プロセス改善
- [ ] **インシデントレビュー**
  ```bash
  # 過去四半期のインシデント分析
  # 再発防止策実施
  # 対応時間改善
  ```

- [ ] **トレーニング実施**
  ```bash
  # 新人向け運用トレーニング
  # 障害対応訓練
  # ツール使用トレーニング
  ```

### 第4四半期 - 年末調整
- [ ] **年間レポート作成**
  ```bash
  # 可用性レポート
  # インシデント統計
  # 改善施策まとめ
  ```

- [ ] **予算計画**
  ```bash
  # 次年度インフラ予算策定
  # ツールライセンス更新
  # トレーニング予算確保
  ```

## メンテナンス自動化

### Cron設定例
```bash
# /etc/cron.d/mks-maintenance

# 毎週月曜日 2:00 - システムチェック
0 2 * * 1 root /opt/mks/scripts/weekly-check.sh

# 毎月第1月曜日 3:00 - 月次メンテナンス
0 3 1-7 * * root [ "$(date '+\%u')" = "1" ] && /opt/mks/scripts/monthly-maintenance.sh

# 毎日 2:00 - バックアップ
0 2 * * * root /opt/mks/scripts/backup.sh

# 毎週日曜日 3:00 - ログローテーション
0 3 * * 0 root /opt/mks/scripts/log-rotate.sh
```

### 自動化スクリプト例
```bash
#!/bin/bash
# scripts/weekly-check.sh

echo "=== 週次システムチェック開始 ==="

# ディスク容量チェック
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "WARNING: Disk usage is ${DISK_USAGE}%"
    # アラート送信
fi

# バックアップ確認
if ! find /backup/mks/ -name "*.dump" -mtime -1 | grep -q .; then
    echo "ERROR: No recent backup found"
    # アラート送信
fi

echo "=== 週次システムチェック完了 ==="
```

## メンテナンス中の注意事項

### サービス停止時の対応
- **事前通知**: 影響を受けるユーザーに1週間前通知
- **代替手段**: メンテナンス中のアクセス制限
- **緊急連絡**: 緊急時の連絡先明記

### ロールバック準備
- **バックアップ取得**: メンテナンス前フルバックアップ
- **切り戻し手順確認**: ロールバック手順の検証
- **監視強化**: メンテナンス中は監視間隔短縮

### 完了確認
- **機能テスト**: 全主要機能の動作確認
- **パフォーマンステスト**: レスポンスタイム測定
- **監視再開**: 通常監視に戻す

## メンテナンス記録

### 記録項目
- **実施日時**: YYYY-MM-DD HH:MM
- **担当者**: 氏名
- **実施内容**: 詳細
- **結果**: 成功/失敗
- **所要時間**: HH:MM
- **特記事項**: 問題点や改善点

### 記録例
```markdown
## 2024-01-08 週次メンテナンス
- **担当者**: SREチーム
- **内容**: ログローテーション、パフォーマンスチェック
- **結果**: 成功
- **所要時間**: 00:30
- **特記事項**: ディスク使用率85% → ログクリーンアップ実施
```</content>
<parameter name="filePath">runbook/maintenance-checklist.md