# 障害対応フロー (Incident Response Flow)

## 概要
システム障害発生時の対応手順とフローを定義します。迅速な障害復旧と影響最小化を目的とします。

## 障害レベル定義

| レベル | 定義 | 影響範囲 | 対応時間 | エスカレーション |
|--------|------|----------|----------|--------------|
| P0 (Critical) | サービス完全停止、データ損失 | 全ユーザー | 15分以内 | 即時管理職連絡 |
| P1 (High) | 機能使用不可 | 特定機能 | 1時間以内 | チームリーダー連絡 |
| P2 (Medium) | 機能制限 | 一部ユーザー | 4時間以内 | 通常業務時間内 |
| P3 (Low) | 軽微な問題 | 限定的 | 1営業日以内 | 定期報告 |

## 障害対応プロセス

### Phase 1: 検知・評価 (Detection & Assessment)

#### 1.1 障害検知
**自動検知:**
- 監視システムアラート (Prometheus/Alertmanager)
- ヘルスチェック失敗
- ユーザー報告

**手動検知:**
- 定期監視チェック
- ログ監視
- パフォーマンス監視

#### 1.2 初期評価
```bash
# サービスステータス確認
systemctl status mks-backend
systemctl status nginx
systemctl status postgresql

# ログ確認
tail -n 50 /var/log/mks-backend/error.log
tail -n 50 /var/log/nginx/error.log

# リソース確認
top -b -n1 | head -20
df -h
free -h
```

#### 1.3 影響範囲評価
**評価項目:**
- **機能影響**: どの機能が使用不可か
- **ユーザー影響**: 影響を受けるユーザー数/割合
- **ビジネス影響**: 収益/業務への影響度
- **データ影響**: データ損失の有無

**評価基準:**
```python
# 影響度計算例
def calculate_impact(user_affected, business_impact, data_loss):
    if user_affected > 0.8:  # 80%以上影響
        return "P0"
    elif business_impact == "high" or data_loss:
        return "P1"
    elif user_affected > 0.3:  # 30%以上影響
        return "P2"
    else:
        return "P3"
```

### Phase 2: 対応・復旧 (Response & Recovery)

#### 2.1 即時対応
**P0/P1障害:**
- オンコールチーム起動
- ステークホルダー通知
- 復旧作業開始

**P2/P3障害:**
- 担当チーム割り当て
- 定期ステータス更新

#### 2.2 診断・原因特定
**診断手法:**
1. **ログ分析**
   ```bash
   # エラーログ検索
   grep "ERROR\|CRITICAL" /var/log/mks-backend/*.log | tail -20
   
   # タイムスタンプ確認
   journalctl -u mks-backend --since "1 hour ago" --no-pager
   ```

2. **メトリクス確認**
   ```bash
   # Prometheusクエリ
   curl "http://localhost:9090/api/v1/query?query=up{job='mks-backend'}"
   
   # システムメトリクス
   iostat -x 1 5
   vmstat 1 5
   ```

3. **コンポーネントテスト**
   ```bash
   # APIエンドポイントテスト
   curl -f http://localhost:5100/api/v1/health
   
   # データベース接続テスト
   psql -U mks_user -d mks_db -c "SELECT 1;"
   ```

#### 2.3 復旧実行
**復旧戦略:**
- **サービス再起動**: 最も迅速な対応
- **設定ロールバック**: 設定変更が原因の場合
- **コードロールバック**: デプロイ失敗の場合
- **インフラ復旧**: ハードウェア/OS障害の場合

**復旧手順例:**
```bash
# サービス再起動
sudo systemctl restart mks-backend

# 設定確認
nginx -t && sudo systemctl reload nginx

# データベース復旧
sudo systemctl restart postgresql
```

### Phase 3: フォローアップ (Follow-up)

#### 3.1 復旧確認
**確認項目:**
- [ ] サービス起動確認
- [ ] 機能テスト実行
- [ ] パフォーマンス確認
- [ ] ユーザー影響確認

**テスト手順:**
```bash
# 自動テスト実行
python -m pytest tests/integration/ -v

# 手動テスト
curl -X GET http://localhost:5100/api/v1/projects
curl -X POST http://localhost:5100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'
```

#### 3.2 コミュニケーション
**内部コミュニケーション:**
- Slackチャンネル: #incidents
- ステータス更新: 30分ごと
- 最終報告: 復旧後24時間以内

**外部コミュニケーション:**
- ステータスページ更新
- 影響ユーザーへのメール通知
- SNS更新（重大障害時）

#### 3.3 事後レビュー
**レビュー内容:**
- **タイムライン**: 障害発生から復旧までの詳細時系列
- **根本原因**: 詳細な原因分析
- **影響分析**: 実際の影響度合い
- **対応評価**: 対応の適切性と改善点
- **予防策**: 再発防止のための対策

## 障害対応ツール

### 診断ツール
- **systemctl**: サービス管理
- **journalctl**: システムログ
- **psql**: データベース確認
- **curl**: APIテスト
- **top/htop**: プロセス監視
- **iostat/vmstat**: システムメトリクス

### コラボレーションツール
- **Slack/Microsoft Teams**: リアルタイムコミュニケーション
- **Jira/Linear**: インシデント管理
- **Google Docs**: 共有ドキュメント
- **Zoom**: 緊急会議

### 監視ツール
- **Prometheus/Grafana**: メトリクス監視
- **ELK Stack**: ログ分析
- **Nagios/Zabbix**: インフラ監視

## インシデント管理

### インシデント記録
**記録項目:**
- インシデントID
- 発生日時
- 検知方法
- 影響範囲
- 対応担当者
- 復旧時間
- 根本原因
- 予防対策

### インシデントレポートテンプレート
```markdown
# インシデントレポート: INC-2024-001

## 概要
[障害の簡単な説明]

## タイムライン
| 時刻 | イベント | 担当者 |
|------|---------|--------|
| 09:00 | 障害検知 | 監視システム |
| 09:05 | 初期対応開始 | SREチーム |
| 09:15 | 原因特定 | 開発チーム |
| 09:30 | 復旧完了 | SREチーム |

## 影響範囲
- **機能影響**: [影響機能]
- **ユーザー影響**: [影響ユーザー数]
- **ビジネス影響**: [高/中/低]

## 根本原因
[詳細な原因分析]

## 対応内容
1. [対応1]
2. [対応2]
3. [対応3]

## 予防対策
1. [対策1]
2. [対策2]

## 学習事項
- [ ] [学習事項1]
- [ ] [学習事項2]
```

## 定期訓練・改善

### 毎四半期活動
- **障害対応訓練**: 模擬障害シナリオ演習
- **ツール更新**: 監視ツールの改善
- **プロセス見直し**: 対応フローの最適化

### KPI監視
- **MTTR (Mean Time To Recovery)**: 平均復旧時間
- **MTTD (Mean Time To Detection)**: 平均検知時間
- **インシデント率**: 月間インシデント発生数
- **再発率**: 同様障害の再発率

### 継続的改善
- **レトロスペクティブ**: 毎月のインシデントレビュー
- **プロセス改善**: ボトルネック解消
- **ツール投資**: 自動化・監視強化

## 緊急連絡先

### オンコールローテーション
- **平日 9:00-18:00**: SREチーム
- **平日 18:00-9:00**: オンコール担当
- **休日**: オンコール担当

### エスカレーション
- **レベル1**: SREチームリーダー
- **レベル2**: 開発部長
- **レベル3**: CTO/経営層

### 外部連絡先
- **クラウドプロバイダ**: AWS/Azureサポート
- **インフラベンダー**: サーバー/ネットワーク保守
- **セキュリティ**: セキュリティインシデント対応</content>
<parameter name="filePath">docs/11_運用保守(Operations)/13_障害対応フロー(Incident-Response).md