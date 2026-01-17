# MFA監査手順

## 概要
MFA（多要素認証）のセキュリティ監査手順を記載します。定期的な監査により、MFAの有効性とコンプライアンスを確保します。

## 監査の目的

### セキュリティ確保
- MFA設定の完全性を確認
- 設定ミスや脆弱性の検出
- セキュリティポリシーの遵守状況確認

### コンプライアンス対応
- GDPR、ISO 27001などの基準遵守
- 監査証跡の維持
- 定期報告の作成

### 運用改善
- MFA使用状況の分析
- 問題パターンの特定
- 改善策の立案

## 監査スケジュール

### 毎週監査
- MFA設定率の確認
- 失敗ログのレビュー
- 異常アクセスのチェック

### 毎月監査
- 詳細な使用状況分析
- バックアップコードの有効性確認
- ユーザー教育状況確認

### 毎四半期監査
- 包括的なセキュリティ監査
- ポリシー遵守状況確認
- 監査レポート作成

### 年次監査
- 包括的なコンプライアンス監査
- 外部監査人による検証
- 監査結果の経営層報告

## 監査項目

### 1. MFA設定状況監査

#### 設定率確認
```sql
-- 全ユーザーのMFA設定状況
SELECT
    COUNT(*) as total_users,
    SUM(CASE WHEN mfa_enabled = true THEN 1 ELSE 0 END) as mfa_enabled_users,
    ROUND(SUM(CASE WHEN mfa_enabled = true THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as mfa_rate
FROM users;
```

#### 管理者別設定状況
```sql
-- 管理者権限ユーザーのMFA設定状況
SELECT
    role,
    COUNT(*) as total,
    SUM(CASE WHEN mfa_enabled = true THEN 1 ELSE 0 END) as mfa_enabled,
    ROUND(SUM(CASE WHEN mfa_enabled = true THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as rate
FROM users
GROUP BY role;
```

#### 設定日時分析
```sql
-- MFA設定日時の分布
SELECT
    DATE_TRUNC('month', mfa_setup_date) as month,
    COUNT(*) as setups
FROM users
WHERE mfa_enabled = true
GROUP BY DATE_TRUNC('month', mfa_setup_date)
ORDER BY month DESC;
```

### 2. MFA使用状況監査

#### 認証成功/失敗統計
```sql
-- 過去30日間のMFA認証統計
SELECT
    DATE_TRUNC('day', created_at) as date,
    SUM(CASE WHEN success = true THEN 1 ELSE 0 END) as success_count,
    SUM(CASE WHEN success = false THEN 1 ELSE 0 END) as failure_count,
    ROUND(
        SUM(CASE WHEN success = false THEN 1 ELSE 0 END) * 100.0 /
        (SUM(CASE WHEN success = true THEN 1 ELSE 0 END) + SUM(CASE WHEN success = false THEN 1 ELSE 0 END)),
        2
    ) as failure_rate
FROM mfa_logs
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY date DESC;
```

#### ユーザー別使用状況
```sql
-- ユーザー別のMFA使用統計
SELECT
    u.username,
    COUNT(ml.*) as total_attempts,
    SUM(CASE WHEN ml.success = true THEN 1 ELSE 0 END) as success_count,
    SUM(CASE WHEN ml.success = false THEN 1 ELSE 0 END) as failure_count,
    MAX(ml.created_at) as last_attempt
FROM users u
LEFT JOIN mfa_logs ml ON u.id = ml.user_id
WHERE ml.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY u.username
ORDER BY total_attempts DESC;
```

#### バックアップコード使用状況
```sql
-- バックアップコード使用統計
SELECT
    DATE_TRUNC('month', used_at) as month,
    COUNT(*) as codes_used
FROM backup_code_usage
WHERE used_at >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY DATE_TRUNC('month', used_at)
ORDER BY month DESC;
```

### 3. セキュリティイベント監査

#### 異常アクセス検知
```sql
-- 短時間に複数回のMFA失敗
SELECT
    user_id,
    ip_address,
    COUNT(*) as failure_count,
    MIN(created_at) as first_failure,
    MAX(created_at) as last_failure
FROM mfa_logs
WHERE success = false
    AND created_at >= CURRENT_DATE - INTERVAL '1 day'
GROUP BY user_id, ip_address
HAVING COUNT(*) >= 5
ORDER BY failure_count DESC;
```

#### アカウントロック状況
```sql
-- アカウントロック履歴
SELECT
    username,
    locked_at,
    unlocked_at,
    lock_reason
FROM account_lock_history
WHERE locked_at >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY locked_at DESC;
```

#### MFAリセット履歴
```sql
-- MFAリセット履歴
SELECT
    username,
    reset_at,
    reset_reason,
    reset_by
FROM mfa_reset_history
WHERE reset_at >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY reset_at DESC;
```

### 4. コンプライアンス監査

#### GDPRコンプライアンス
- [ ] MFA設定はユーザーの同意に基づく
- [ ] 個人データの最小限収集
- [ ] データ削除時のMFA情報削除
- [ ] プライバシーポリシーの明記

#### セキュリティ基準遵守
- [ ] NIST SP 800-63B準拠
- [ ] ISO 27001認証取得
- [ ] 業界固有のセキュリティ基準

#### ログ保持確認
```sql
-- ログ保持期間確認
SELECT
    'mfa_logs' as table_name,
    MIN(created_at) as oldest_record,
    MAX(created_at) as newest_record,
    COUNT(*) as total_records
FROM mfa_logs
WHERE created_at >= CURRENT_DATE - INTERVAL '1 year';
```

### 5. システム構成監査

#### MFA設定確認
```bash
# MFA有効化設定確認
grep "MFA_ENABLED" /etc/mks/config.py
grep "MFA_REQUIRED" /etc/mks/config.py

# TOTP設定確認
grep "TOTP" /etc/mks/mfa_config.py
```

#### 依存関係確認
```bash
# MFAライブラリバージョン確認
pip list | grep -i mfa
pip list | grep pyotp
pip list | grep qrcode
```

#### 証明書有効性確認
```bash
# SSL証明書確認
openssl x509 -in /etc/ssl/certs/mfa.crt -text -noout | grep -A 2 "Validity"

# NTP同期確認
ntpq -p
```

## 監査手順

### 準備段階
1. **監査計画の策定**
   - 監査範囲の決定
   - 監査チームの構成
   - 監査スケジュールの設定

2. **データ収集**
   - ログデータの抽出
   - 設定ファイルのバックアップ
   - ユーザーアンケートの実施

3. **ツール準備**
   - SQLクエリツール
   - ログ分析ツール
   - レポート作成ツール

### 実行段階
1. **自動監査実行**
   - スクリプトによるデータ収集
   - 自動チェック項目の実行
   - 異常検知

2. **手動確認**
   - サンプルデータの検証
   - 設定ファイルの確認
   - ユーザーインタビューの実施

3. **問題特定**
   - 異常パターンの分析
   - 根本原因の調査
   - 影響範囲の評価

### 報告段階
1. **監査結果整理**
   - 発見事項の分類
   - 重要度の評価
   - 改善提案の作成

2. **レポート作成**
   - 実行概要
   - 発見事項
   - 改善勧告
   - アクションプラン

3. **是正措置**
   - 改善策の実施
   - フォローアップ監査
   - 効果測定

## 監査レポートテンプレート

```markdown
# MFAセキュリティ監査レポート

## 監査概要
- **監査期間**: [開始日] - [終了日]
- **監査対象**: [システム/コンポーネント]
- **監査担当**: [担当者名]

## 監査結果サマリー

### MFA設定状況
- **全体設定率**: [XX%] ([有効ユーザー数]/[総ユーザー数])
- **管理者設定率**: [XX%]
- **新規ユーザー設定率**: [XX%]

### 使用状況
- **月間認証成功数**: [XX]
- **月間認証失敗数**: [XX]
- **失敗率**: [X.X%]

### セキュリティイベント
- **アカウントロック数**: [XX]
- **MFAリセット数**: [XX]
- **異常アクセス検知数**: [XX]

## 発見事項

### 重大な問題
1. [問題1の詳細]
   - 影響: [影響度]
   - 原因: [原因]
   - 推奨: [改善策]

### 軽微な問題
1. [問題1の詳細]
   - 推奨: [改善策]

## コンプライアンス状況
- [ ] GDPR準拠
- [ ] ISO 27001準拠
- [ ] 業界基準準拠

## 改善勧告

### 即時対応が必要
1. [勧告1]
2. [勧告2]

### 中期対応
1. [勧告1]
2. [勧告2]

### 長期対応
1. [勧告1]
2. [勧告2]

## 結論
[監査結果のまとめと今後の対応方針]
```

## 監査スクリプト

### 自動監査スクリプト
```bash
#!/bin/bash
# scripts/mfa-audit.sh

echo "=== MFAセキュリティ監査開始 ==="

# MFA設定率チェック
echo "MFA設定率:"
psql -d mks_db -c "
SELECT
    ROUND(SUM(CASE WHEN mfa_enabled = true THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as mfa_rate
FROM users;
"

# 失敗率チェック
echo "過去30日間の失敗率:"
psql -d mks_db -c "
SELECT
    ROUND(
        SUM(CASE WHEN success = false THEN 1 ELSE 0 END) * 100.0 /
        COUNT(*),
        2
    ) as failure_rate
FROM mfa_logs
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days';
"

# 異常アクセスチェック
echo "異常アクセス検知:"
psql -d mks_db -c "
SELECT COUNT(*) as suspicious_attempts
FROM (
    SELECT user_id, ip_address, COUNT(*) as failures
    FROM mfa_logs
    WHERE success = false AND created_at >= CURRENT_DATE - INTERVAL '1 day'
    GROUP BY user_id, ip_address
    HAVING COUNT(*) >= 5
) t;
"

echo "=== 監査完了 ==="
```

## 監査後のフォローアップ

### 改善策実施
- 特定された問題の修正
- ポリシーの更新
- トレーニングの実施

### 再監査
- 改善効果の検証
- 新たな問題の発見
- 継続的な改善

### 報告
- 経営層への定期報告
- 監査結果の共有
- ベストプラクティスの展開