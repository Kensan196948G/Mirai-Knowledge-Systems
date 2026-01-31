# MS365同期機能デプロイメントガイド

## 概要

このガイドでは、Mirai Knowledge SystemsのMicrosoft 365自動同期機能のデプロイ手順を説明します。

## 前提条件

- Azure ADテナントへの管理者アクセス
- Microsoft 365環境（SharePoint/OneDrive）
- PostgreSQL 15+がインストール済み
- Python 3.10+環境

## 1. Azure ADアプリケーション登録

### 1.1 アプリ登録の作成

1. Azure Portal (https://portal.azure.com) にログイン
2. 「Azure Active Directory」→「アプリの登録」を選択
3. 「新規登録」をクリック

**設定値**:
- 名前: `Mirai-Knowledge-MS365-Sync`
- サポートされているアカウントの種類: 「この組織ディレクトリのみのアカウント」
- リダイレクトURI: （空白）

### 1.2 クライアントシークレットの作成

1. 登録したアプリを開く
2. 「証明書とシークレット」→「新しいクライアントシークレット」
3. 説明: `MKS Sync Secret`
4. 有効期限: 24か月（推奨）
5. 生成された**シークレット値をコピー**（後で使用）

### 1.3 必要なAPI権限の付与

「APIのアクセス許可」→「アクセス許可の追加」→「Microsoft Graph」

**必要な権限（Application permissions）**:

| API権限 | 用途 |
|---------|------|
| `Sites.Read.All` | SharePointサイト読み取り |
| `Files.Read.All` | ファイル読み取り |
| `User.Read.All` | ユーザー情報取得（オプション） |

**重要**: 権限追加後、「管理者の同意を付与」をクリック

### 1.4 アプリケーション情報の取得

以下の情報をメモ:
- **テナントID**: 「概要」ページの「ディレクトリ (テナント) ID」
- **クライアントID**: 「概要」ページの「アプリケーション (クライアント) ID」
- **クライアントシークレット**: 1.2でコピーした値

## 2. 環境変数設定

### 2.1 .envファイルの編集

`backend/.env`ファイルに以下を追加:

```bash
# Microsoft 365連携設定
AZURE_TENANT_ID=your-tenant-id-here
AZURE_CLIENT_ID=your-client-id-here
AZURE_CLIENT_SECRET=your-client-secret-here

# オプション: 証明書認証を使用する場合
# AZURE_CLIENT_CERTIFICATE_PATH=/path/to/certificate.pem
# AZURE_CLIENT_CERTIFICATE_KEY_PATH=/path/to/private-key.pem

# MS365同期機能の有効化
MS365_SYNC_ENABLED=true
MS365_SYNC_DEFAULT_SCHEDULE=0 2 * * *
```

### 2.2 環境変数の確認

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend
source ../venv_linux/bin/activate
python -c "import os; print('AZURE_TENANT_ID:', 'OK' if os.getenv('AZURE_TENANT_ID') else 'NG')"
```

## 3. データベースマイグレーション

### 3.1 マイグレーションスクリプトの作成

既に`backend/migrations/versions/`に以下のファイルがあることを確認:
- `add_ms365_sync_tables.py`

### 3.2 マイグレーション実行

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend
source ../venv_linux/bin/activate

# マイグレーション実行
alembic upgrade head

# 確認
psql -U mirai_user -d mirai_knowledge -c "\dt" | grep ms365
```

期待される出力:
```
 public | ms365_sync_configs  | table | mirai_user
 public | ms365_sync_history  | table | mirai_user
 public | ms365_file_metadata | table | mirai_user
```

## 4. 接続テスト

### 4.1 Graph API接続確認

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend
python -m integrations.microsoft_graph --test
```

**期待される出力**:
```json
{
  "configured": true,
  "connected": true,
  "tenant_id": "your-tenant-id",
  "client_id": "your-client-id",
  "auth_type": "secret",
  "token_acquired": true,
  "organization": "Your Organization Name",
  "errors": []
}
```

### 4.2 SharePointサイトの確認

```bash
python -m integrations.microsoft_graph --sites
```

利用可能なSharePointサイトが表示されることを確認。

## 5. systemdサービスのインストール

### 5.1 サービスファイルのコピー

```bash
sudo cp /mnt/LinuxHDD/Mirai-Knowledge-Systems/config/mirai-ms365-sync.service \
        /etc/systemd/system/
```

### 5.2 サービスの有効化と起動

```bash
# サービスを再読み込み
sudo systemctl daemon-reload

# サービスを有効化（自動起動）
sudo systemctl enable mirai-ms365-sync.service

# サービスを起動
sudo systemctl start mirai-ms365-sync.service

# ステータス確認
sudo systemctl status mirai-ms365-sync.service
```

**期待されるステータス**:
```
● mirai-ms365-sync.service - Mirai Knowledge Systems - MS365 Sync Scheduler
   Loaded: loaded (/etc/systemd/system/mirai-ms365-sync.service; enabled)
   Active: active (running) since ...
```

### 5.3 ログの確認

```bash
# リアルタイムログ表示
sudo journalctl -u mirai-ms365-sync.service -f

# 最新100行を表示
sudo journalctl -u mirai-ms365-sync.service -n 100
```

## 6. 同期設定の作成

### 6.1 管理画面から設定

1. ブラウザで管理画面にアクセス: `https://192.168.0.187:9443/admin.html`
2. 管理者でログイン
3. 「MS365同期設定」セクションに移動
4. 「新規同期設定を作成」をクリック

**設定例**:
- 名前: `SharePoint建設ドキュメント同期`
- サイトID: `contoso.sharepoint.com,abc123,def456`（接続テストで確認）
- ドライブID: `b!xyz789...`（接続テストで確認）
- フォルダパス: `/施工管理`
- ファイル拡張子: `pdf, docx, xlsx`
- 同期スケジュール: `0 2 * * *`（毎日午前2時）
- 同期戦略: `incremental`（増分同期）

### 6.2 APIから設定（オプション）

```bash
curl -X POST https://192.168.0.187:9443/api/v1/ms365/sync/configs \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SharePoint建設ドキュメント同期",
    "site_id": "contoso.sharepoint.com,abc123,def456",
    "drive_id": "b!xyz789...",
    "folder_path": "/施工管理",
    "file_extensions": ["pdf", "docx", "xlsx"],
    "sync_schedule": "0 2 * * *",
    "sync_strategy": "incremental",
    "is_enabled": true
  }'
```

## 7. 手動同期テスト

### 7.1 接続テストの実行

```bash
curl -X POST https://192.168.0.187:9443/api/v1/ms365/sync/configs/1/test \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**期待されるレスポンス**:
```json
{
  "success": true,
  "data": {
    "connected": true,
    "site_accessible": true,
    "drive_accessible": true,
    "files_found": 15
  }
}
```

### 7.2 手動同期の実行

```bash
curl -X POST https://192.168.0.187:9443/api/v1/ms365/sync/configs/1/execute \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 7.3 同期結果の確認

```bash
curl https://192.168.0.187:9443/api/v1/ms365/sync/configs/1/history \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 8. 監視設定

### 8.1 Prometheusメトリクス確認

```bash
curl http://192.168.0.187:9100/metrics | grep ms365_sync
```

**主要メトリクス**:
- `ms365_sync_total` - 同期実行回数
- `ms365_sync_success_total` - 成功回数
- `ms365_sync_errors_total` - エラー回数
- `ms365_sync_files_synced` - 同期されたファイル数
- `ms365_sync_duration_seconds` - 同期所要時間

### 8.2 Grafanaダッシュボード

1. Grafana (`http://192.168.0.187:3000`) にアクセス
2. 「MS365 Sync Monitor」ダッシュボードをインポート
3. ファイル: `backend/monitoring/grafana/dashboards/ms365-sync.json`

## 9. トラブルシューティング

### 9.1 認証エラー

**症状**: `InvalidAuthenticationToken` エラー

**対処**:
1. クライアントシークレットが正しいか確認
2. シークレットの有効期限を確認
3. 環境変数が正しく設定されているか確認

```bash
python -m integrations.microsoft_graph --test
```

### 9.2 権限エラー

**症状**: `Forbidden` または `Access denied` エラー

**対処**:
1. Azure ADの「APIのアクセス許可」を確認
2. 「管理者の同意を付与」が実行されているか確認
3. 必要な権限: `Sites.Read.All`, `Files.Read.All`

### 9.3 サイトが見つからない

**症状**: `Site not found` エラー

**対処**:
1. サイトIDを確認:
   ```bash
   python -m integrations.microsoft_graph --sites
   ```
2. サイトURLからIDを取得:
   ```bash
   curl "https://graph.microsoft.com/v1.0/sites/YOUR_DOMAIN.sharepoint.com:/sites/YOUR_SITE" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

### 9.4 同期が実行されない

**症状**: スケジュールされた同期が動作しない

**対処**:
1. systemdサービスのステータス確認:
   ```bash
   sudo systemctl status mirai-ms365-sync.service
   ```
2. ログを確認:
   ```bash
   sudo journalctl -u mirai-ms365-sync.service -n 100
   ```
3. cron形式のスケジュールを確認

## 10. セキュリティ推奨事項

### 10.1 証明書認証の使用（推奨）

クライアントシークレットの代わりに証明書認証を使用することを推奨:

```bash
# 自己署名証明書の作成
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Azure ADにアップロード
# Azure Portal → アプリの登録 → 証明書とシークレット → 証明書 → 証明書のアップロード
```

環境変数:
```bash
AZURE_CLIENT_CERTIFICATE_PATH=/path/to/cert.pem
AZURE_CLIENT_CERTIFICATE_KEY_PATH=/path/to/key.pem
```

### 10.2 最小権限の原則

必要最小限の権限のみを付与:
- 読み取り専用操作には `.Read.All` 権限を使用
- 書き込みが必要な場合のみ `.ReadWrite.All` を使用

### 10.3 監査ログの有効化

すべての同期操作はアクセスログに記録されます:

```bash
# アクセスログの確認
psql -U mirai_user -d mirai_knowledge -c \
  "SELECT * FROM access_logs WHERE action LIKE 'ms365%' ORDER BY timestamp DESC LIMIT 10;"
```

## 11. 本番運用チェックリスト

- [ ] Azure ADアプリケーションが正しく登録されている
- [ ] 必要なAPI権限が付与され、管理者の同意が完了している
- [ ] 環境変数が正しく設定されている
- [ ] データベースマイグレーションが完了している
- [ ] Graph API接続テストが成功している
- [ ] systemdサービスが起動し、自動起動設定されている
- [ ] 手動同期テストが成功している
- [ ] 監視ダッシュボードが設定されている
- [ ] エラー通知が設定されている
- [ ] バックアップスクリプトにMS365設定テーブルが含まれている

## 12. 関連ドキュメント

- [MS365同期機能実装概要](../2FA_COMPLETION_SUMMARY.md)
- [API仕様書](../backend/docs/API_DOCUMENTATION.md)
- [運用ガイド](../docs/11_運用保守(Operations)/05_End-User-Guide.md)

## 付録A: サイトID・ドライブID取得方法

### PowerShellを使用（Windows）

```powershell
Connect-PnPOnline -Url "https://yourtenant.sharepoint.com/sites/yoursite" -Interactive
$site = Get-PnPSite
$site.Id

$drive = Get-PnPList -Identity "Documents"
$drive.Id
```

### Graph Explorerを使用

1. https://developer.microsoft.com/en-us/graph/graph-explorer にアクセス
2. サインイン
3. クエリ実行:
   ```
   GET https://graph.microsoft.com/v1.0/sites?search=YourSiteName
   GET https://graph.microsoft.com/v1.0/sites/{site-id}/drives
   ```

## 付録B: cronスケジュール例

| スケジュール | 説明 |
|------------|------|
| `0 2 * * *` | 毎日午前2時 |
| `0 */6 * * *` | 6時間ごと |
| `0 0 * * 0` | 毎週日曜日の午前0時 |
| `0 9 1 * *` | 毎月1日の午前9時 |
| `*/30 * * * *` | 30分ごと |

---

**作成日**: 2026-01-31
**バージョン**: 1.0
**担当**: Development Team
