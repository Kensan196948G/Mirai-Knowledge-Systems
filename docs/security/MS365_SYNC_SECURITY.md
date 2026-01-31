# Microsoft 365同期 セキュリティガイド

## 概要

このドキュメントは、Microsoft 365同期機能のセキュリティベストプラクティス、認証情報の管理、監査ログの確認方法について説明します。

---

## 1. 認証情報の安全な管理

### 1.1 環境変数の保護

**必須環境変数**:
```bash
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret  # または証明書認証
```

**セキュリティ対策**:

1. **環境変数ファイルの権限設定**:
   ```bash
   chmod 600 /path/to/.env
   chown mks-user:mks-user /path/to/.env
   ```

2. **Git除外設定**:
   `.gitignore`に以下を追加:
   ```
   .env
   .env.*
   *.pem
   *.pfx
   ```

3. **本番環境での管理**:
   - systemd環境変数ファイルを使用
   - ファイルパス: `/etc/mirai-knowledge-system/ms365-sync.env`
   - 権限: `600 (root:root)`

### 1.2 シークレット vs 証明書認証

| 認証方式 | セキュリティレベル | 推奨環境 | 有効期限 |
|---------|------------------|---------|---------|
| クライアントシークレット | 中 | 開発・テスト | 最大2年 |
| 証明書認証 | 高 | **本番環境** | 最大3年 |

**本番環境では証明書認証を強く推奨**

---

## 2. 証明書認証の推奨（本番環境）

### 2.1 証明書の生成

**OpenSSLで自己署名証明書を生成**:
```bash
# 秘密鍵と証明書の生成
openssl req -x509 -newkey rsa:4096 -keyout ms365-cert.pem -out ms365-cert.crt -days 1095 -nodes

# PKCS#12形式に変換（Azureアップロード用）
openssl pkcs12 -export -out ms365-cert.pfx -inkey ms365-cert.pem -in ms365-cert.crt
```

### 2.2 証明書の保管

**ディレクトリ構成**:
```
/etc/ssl/mirai-knowledge-system/
├── ms365-cert.pem       # 秘密鍵（権限: 400）
├── ms365-cert.crt       # 公開証明書（権限: 644）
└── ms365-cert.pfx       # Azure用（一時的、アップロード後削除）
```

**権限設定**:
```bash
sudo chmod 400 /etc/ssl/mirai-knowledge-system/ms365-cert.pem
sudo chmod 644 /etc/ssl/mirai-knowledge-system/ms365-cert.crt
sudo chown root:root /etc/ssl/mirai-knowledge-system/*
```

### 2.3 Azure ADでの証明書登録

1. Azure Portal → Azure Active Directory → App registrations
2. 対象アプリを選択 → Certificates & secrets
3. Certificates タブ → Upload certificate
4. `ms365-cert.crt`をアップロード
5. アップロード後、`ms365-cert.pfx`を削除

**環境変数設定**:
```bash
AZURE_CLIENT_CERTIFICATE_PATH=/etc/ssl/mirai-knowledge-system/ms365-cert.pem
# AZURE_CLIENT_SECRET は設定不要
```

---

## 3. APIキーのローテーション手順

### 3.1 クライアントシークレットのローテーション

**推奨頻度**: 90日ごと

**手順**:

1. **新しいシークレットの作成**:
   - Azure Portal → App registrations → Certificates & secrets
   - New client secret
   - 有効期限: 90日または180日

2. **新シークレットのテスト**:
   ```bash
   # テスト環境で新シークレットを設定
   AZURE_CLIENT_SECRET=new-secret-value

   # 同期テスト実行
   python test_ms365_connection.py
   ```

3. **本番環境への反映**:
   ```bash
   sudo nano /etc/mirai-knowledge-system/ms365-sync.env
   # AZURE_CLIENT_SECRET を更新

   sudo systemctl restart mirai-ms365-sync
   ```

4. **旧シークレットの削除**:
   - 新シークレット稼働確認後、Azure Portalで旧シークレットを削除

### 3.2 証明書のローテーション

**推奨頻度**: 365日ごと（有効期限の90日前）

**手順**:

1. 新しい証明書を生成（上記2.1参照）
2. Azure ADに新証明書をアップロード（旧証明書は削除しない）
3. 環境変数を新証明書パスに更新
4. サービス再起動
5. 動作確認後、旧証明書を削除

---

## 4. 監査ログの確認方法

### 4.1 同期実行ログ

**ログファイル**:
```
/var/log/mirai-knowledge-system/ms365-sync.log
```

**重要なログエントリ**:
```
[Sync 123] 同期開始: config_id=1
[Sync 123] ファイル一覧取得開始: site=xxx, drive=yyy
[Sync 123] 20 件のファイルを検出
[Sync 123] 同期完了: {'files_created': 5, 'files_updated': 3, ...}
```

**エラーログの確認**:
```bash
# 認証エラー
grep "authentication" /var/log/mirai-knowledge-system/ms365-sync.log

# ネットワークエラー
grep "network\|timeout" /var/log/mirai-knowledge-system/ms365-sync.log

# レート制限
grep "rate limit\|429" /var/log/mirai-knowledge-system/ms365-sync.log
```

### 4.2 PostgreSQLデータベース監査

**同期履歴の確認**:
```sql
-- 最近の同期履歴
SELECT
    id,
    config_id,
    status,
    triggered_by,
    sync_started_at,
    execution_time_seconds,
    files_created,
    files_updated,
    files_failed
FROM ms365_sync_history
ORDER BY sync_started_at DESC
LIMIT 20;

-- 失敗した同期
SELECT
    id,
    config_id,
    error_message,
    sync_started_at
FROM ms365_sync_history
WHERE status = 'failed'
ORDER BY sync_started_at DESC;
```

**ファイルマッピングの確認**:
```sql
-- SharePointファイルとナレッジの対応
SELECT
    mfm.sharepoint_file_id,
    mfm.sharepoint_file_name,
    k.title,
    k.created_at,
    mfm.last_synced_at
FROM ms365_file_mapping mfm
JOIN knowledge k ON k.id = mfm.knowledge_id
WHERE mfm.config_id = 1
ORDER BY mfm.last_synced_at DESC;
```

### 4.3 Prometheusメトリクス監査

**Grafanaダッシュボード**:
- URL: `http://your-server:3000/d/ms365-sync`
- パネル: Sync Success Rate, Error Rate by Type

**PromQL クエリ例**:
```promql
# 成功率（過去24時間）
100 * sum(rate(mks_ms365_sync_executions_total{status="success"}[24h]))
/ sum(rate(mks_ms365_sync_executions_total[24h]))

# エラー総数（config別）
sum by (config_id, error_type) (mks_ms365_sync_errors_total)

# 平均同期時間
rate(mks_ms365_sync_duration_seconds_sum[5m])
/ rate(mks_ms365_sync_duration_seconds_count[5m])
```

---

## 5. RBAC権限マトリクス

### 5.1 ロール定義

| ロール | MS365設定閲覧 | MS365設定編集 | 手動同期実行 | 同期履歴閲覧 |
|-------|-------------|-------------|------------|------------|
| **admin** | ✅ | ✅ | ✅ | ✅ |
| **editor** | ✅ | ❌ | ✅ | ✅ |
| **viewer** | ✅ | ❌ | ❌ | ✅ |
| **guest** | ❌ | ❌ | ❌ | ❌ |

### 5.2 APIエンドポイント権限

| エンドポイント | Method | 必要権限 | 説明 |
|--------------|--------|---------|------|
| `/api/ms365/configs` | GET | `viewer` | 同期設定一覧取得 |
| `/api/ms365/configs` | POST | `admin` | 同期設定作成 |
| `/api/ms365/configs/{id}` | PUT | `admin` | 同期設定更新 |
| `/api/ms365/configs/{id}` | DELETE | `admin` | 同期設定削除 |
| `/api/ms365/sync/{config_id}` | POST | `editor` | 手動同期実行 |
| `/api/ms365/history` | GET | `viewer` | 同期履歴取得 |

### 5.3 Microsoft Graph API権限

**必要なアプリケーション権限**:

| 権限 | タイプ | 用途 |
|------|------|------|
| `Sites.Read.All` | Application | SharePointサイト読み取り |
| `Files.Read.All` | Application | OneDrive/SharePointファイル読み取り |
| `User.Read.All` | Application | ユーザー情報取得（オプション） |

**権限設定手順**:
1. Azure Portal → App registrations → API permissions
2. Add a permission → Microsoft Graph → Application permissions
3. 上記3つの権限を追加
4. **Grant admin consent** をクリック（管理者承認必須）

---

## 6. セキュリティベストプラクティス

### 6.1 ネットワークセキュリティ

**ファイアウォール設定**:
```bash
# Azure Graph API エンドポイントへのHTTPS通信を許可
# IPアドレス: Microsoft Graph API (動的)
# ポート: 443 (HTTPS)
```

**プロキシ経由のアクセス**:
```bash
export HTTPS_PROXY=http://proxy.example.com:8080
export NO_PROXY=localhost,127.0.0.1
```

### 6.2 最小権限の原則

- Azure ADアプリには必要最小限の権限のみ付与
- `Sites.Read.All`（読み取り専用）を使用し、書き込み権限は避ける
- 特定のサイトやドライブへのアクセスを制限

### 6.3 監視とアラート

**アラート設定**:

| メトリクス | しきい値 | アクション |
|----------|---------|----------|
| 同期成功率 | < 90% | 管理者に通知 |
| エラー発生数 | > 10/hour | 即時調査 |
| 同期実行時間 | > 60秒 | パフォーマンス調査 |

**Prometheus Alertmanager設定**:
```yaml
groups:
  - name: ms365_sync
    rules:
      - alert: MS365SyncFailureRate
        expr: |
          100 * sum(rate(mks_ms365_sync_executions_total{status="failed"}[1h]))
          / sum(rate(mks_ms365_sync_executions_total[1h])) > 10
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "MS365同期の失敗率が高い"
          description: "過去1時間の同期失敗率が10%を超えています"
```

### 6.4 データ保護

**暗号化**:
- 通信: TLS 1.2以上（Microsoft Graph API）
- 保存: PostgreSQL接続時にSSL/TLS使用（本番環境）
- 認証情報: systemd環境変数ファイルで暗号化保存

**バックアップ**:
```bash
# 同期設定のバックアップ
pg_dump -U postgres -t ms365_sync_config mirai_knowledge_db > ms365_config_backup.sql

# 復元
psql -U postgres mirai_knowledge_db < ms365_config_backup.sql
```

---

## 7. インシデント対応

### 7.1 認証エラー発生時

**症状**:
```
[ERROR] 同期失敗: Authentication error
```

**対処手順**:
1. クライアントシークレット/証明書の有効期限確認
2. Azure ADアプリの状態確認（無効化されていないか）
3. API権限の再確認（管理者承認が必要）
4. テナントIDとクライアントIDの確認

### 7.2 レート制限エラー発生時

**症状**:
```
[ERROR] Rate limit exceeded (429)
```

**対処手順**:
1. 同期頻度を下げる（例: 1時間ごと → 4時間ごと）
2. ファイル数の多いフォルダを分割
3. バッチサイズの調整（一度に取得するファイル数を減らす）

### 7.3 データ整合性エラー

**症状**:
- 重複したナレッジエントリ
- ファイルマッピングの不整合

**対処手順**:
```sql
-- 重複チェック
SELECT sharepoint_file_id, COUNT(*)
FROM ms365_file_mapping
GROUP BY sharepoint_file_id
HAVING COUNT(*) > 1;

-- 孤立したマッピング削除
DELETE FROM ms365_file_mapping
WHERE knowledge_id NOT IN (SELECT id FROM knowledge);
```

---

## 8. コンプライアンスとプライバシー

### 8.1 個人情報の取り扱い

- SharePointファイルに個人情報が含まれる場合、GDPR/個人情報保護法に準拠
- アクセスログに個人情報を記録しない
- ユーザー同意の取得（必要に応じて）

### 8.2 データ保持ポリシー

**同期履歴**:
- 保持期間: 90日間
- 自動削除クエリ（cronで実行）:
  ```sql
  DELETE FROM ms365_sync_history
  WHERE sync_started_at < NOW() - INTERVAL '90 days';
  ```

**ファイルマッピング**:
- SharePointから削除されたファイルの対応ナレッジを手動レビュー
- 自動削除は無効（データロスを防ぐため）

---

## 9. セキュリティチェックリスト

### 導入前チェックリスト

- [ ] Azure ADアプリ登録完了
- [ ] 必要最小限のAPI権限のみ付与
- [ ] 本番環境では証明書認証を使用
- [ ] 証明書ファイルの権限設定（400）
- [ ] 環境変数ファイルの権限設定（600）
- [ ] `.gitignore`に認証情報を追加
- [ ] ファイアウォールルール設定
- [ ] 監視・アラート設定完了

### 運用時チェックリスト（月次）

- [ ] 同期成功率の確認（目標: 95%以上）
- [ ] エラーログの確認
- [ ] 証明書/シークレットの有効期限確認
- [ ] 不要なファイルマッピングのクリーンアップ
- [ ] PostgreSQLバックアップの確認

### セキュリティ監査チェックリスト（四半期ごと）

- [ ] API権限の見直し
- [ ] アクセス権限マトリクスの見直し
- [ ] 認証情報のローテーション実施
- [ ] 脆弱性スキャン実施
- [ ] ログ分析・異常検知
- [ ] インシデント対応手順の見直し

---

## 10. 参考リンク

- [Microsoft Graph APIセキュリティベストプラクティス](https://learn.microsoft.com/ja-jp/graph/security-authorization)
- [Azure ADアプリケーション権限](https://learn.microsoft.com/ja-jp/graph/permissions-reference)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [Mirai Knowledge Systems デプロイガイド](../deployment/MS365_SYNC_DEPLOYMENT.md)
- [Mirai Knowledge Systems ユーザーガイド](../user-guide/MS365_SYNC_GUIDE.md)

---

**最終更新**: 2026-01-31
**バージョン**: 1.0.0
