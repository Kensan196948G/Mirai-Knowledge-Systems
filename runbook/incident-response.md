# 障害対応フロー (Incident Response Procedures)

## 障害レベル定義

| レベル | 定義 | 対応時間 | 例 | 影響範囲 |
|--------|------|----------|-----|----------|
| P0 (Critical) | サービス完全停止、データ損失 | 15分以内 | サーバーダウン、DB破損 | 全ユーザー |
| P1 (High) | 機能使用不可 | 1時間以内 | ログイン不可、アップロード失敗 | 特定機能 |
| P2 (Medium) | 機能制限 | 4時間以内 | 検索遅延、表示崩れ | 一部ユーザー |
| P3 (Low) | 軽微な問題 | 1営業日以内 | マイナーUI不具合 | 限定的 |

## 障害対応ステップ

### 1. 影響評価 (Impact Assessment)
**目的**: 障害の範囲と影響を迅速に把握

#### 評価項目
- **影響範囲**: [全体 / 特定機能 / 特定ユーザー]
- **影響ユーザー数**: [数値または割合]
- **ビジネス影響**: [高 / 中 / 低]
- **データ影響**: [あり / なし]

#### 確認手順
```bash
# サービスステータス確認
systemctl status mks-backend
systemctl status nginx
systemctl status postgresql

# データベース接続確認
psql -U mks_user -d mks_db -c "SELECT 1;"

# ログ確認
tail -n 50 /var/log/mks-backend/error.log
tail -n 50 /var/log/nginx/error.log
```

### 2. 即時対応 (Immediate Response)
**目的**: サービス復旧を優先

#### 自動対応
- サービス自動再起動
- ロードバランサーによるトラフィック分散
- キャッシュクリア

#### 手動対応
```bash
# サービス再起動
sudo systemctl restart mks-backend

# データベース再接続
sudo systemctl restart postgresql

# キャッシュクリア
redis-cli FLUSHALL
```

### 3. 根本原因分析 (Root Cause Analysis)
**目的**: 障害の根本原因を特定

#### 分析手法
1. **ログ分析**
   ```bash
   # エラーログ検索
   grep "ERROR" /var/log/mks-backend/*.log | tail -20
   
   # タイムスタンプ確認
   journalctl -u mks-backend --since "1 hour ago"
   ```

2. **メトリクス確認**
   - CPU/メモリ使用率
   - ネットワークI/O
   - データベース接続数

3. **コードレビュー**
   - 最近の変更確認
   - 設定ファイル確認

### 4. 恒久対策 (Permanent Fix)
**目的**: 再発防止

#### 対策例
- **コード修正**: バグフィックス
- **設定変更**: パラメータ調整
- **インフラ改善**: リソース増強
- **テスト追加**: 回帰テスト

### 5. 事後レビュー (Post-Mortem)
**目的**: 学習と改善

#### レビュー内容
- **タイムライン**: 障害発生から復旧までの時系列
- **影響分析**: 実際の影響度合い
- **対応評価**: 対応の適切性
- **改善策**: 再発防止策

## 障害対応テンプレート

### 障害: [障害名]

#### 概要
[障害の簡単な説明]

#### 影響範囲
- **影響機能**: [機能名]
- **影響ユーザー数**: [数]
- **ビジネス影響**: [高/中/低]
- **データ損失**: [あり/なし]

#### タイムライン
| 時刻 | イベント | 担当 |
|------|---------|------|
| 00:00 | 障害発生検知 | 監視システム |
| 00:05 | アラート通知 | SRE |
| 00:10 | 対応開始 | SRE |
| 00:20 | 根本原因特定 | 開発チーム |
| 00:30 | 復旧完了 | SRE |
| 01:00 | 事後レビュー | 全チーム |

#### 即時対応
1. **診断**
   ```bash
   # ステータス確認
   systemctl status mks-backend
   
   # ログ確認
   journalctl -u mks-backend --no-pager | tail -20
   ```

2. **対応**
   ```bash
   # サービス再起動
   sudo systemctl restart mks-backend
   
   # 設定確認
   cat /etc/mks/config.yml
   ```

3. **確認**
   ```bash
   # ヘルスチェック
   curl -f http://localhost:5100/api/v1/health
   
   # 機能テスト
   curl -X GET http://localhost:5100/api/v1/projects
   ```

#### 根本原因
[根本原因の詳細説明]

#### 恒久対策
1. **短期対策**: [即時対応]
2. **長期対策**: [恒久対応]
3. **予防策**: [再発防止]

#### 学習事項
- [ ] 監視強化
- [ ] テスト改善
- [ ] ドキュメント更新
- [ ] トレーニング実施

## コミュニケーション

### 内部コミュニケーション
- **Slackチャンネル**: #incidents
- **ステータスページ**: 内部用
- **定期アップデート**: 30分ごと

### 外部コミュニケーション
- **ステータスページ**: 公開用
- **メール通知**: 影響を受ける顧客
- **SNS**: 必要に応じて

## ツール・リソース

### 診断ツール
- `systemctl` - サービス管理
- `journalctl` - ログ確認
- `psql` - データベース確認
- `curl` - APIテスト

### 監視ツール
- Prometheus/Grafana
- ELK Stack
- Nagios/Zabbix

### コラボレーションツール
- Slack/Microsoft Teams
- Jira/Linear
- Google Docs

## 定期訓練

- **毎四半期**: 障害対応訓練
- **毎月**: ツール更新
- **毎週**: アラート確認</content>
<parameter name="filePath">runbook/incident-response.md