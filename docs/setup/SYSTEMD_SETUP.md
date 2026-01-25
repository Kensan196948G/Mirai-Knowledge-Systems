# Mirai Knowledge System - systemd 自動起動設定

このガイドでは、Mirai Knowledge Systemをsystemdサービスとして登録し、サーバー再起動時に自動起動するように設定します。

## 前提条件

- Linux環境（systemd対応）
- sudo権限
- プロジェクトパス: `/mnt/LinuxHDD/Mirai-Knowledge-Systems`

## ポート番号（固定）

| 環境 | HTTP | HTTPS | サービスファイル |
|------|------|-------|-----------------|
| 開発 | 5100 | 5443 | `mirai-knowledge-app-dev.service` |
| 本番 | 8100 | 8443 | `mirai-knowledge-app.service` |

> **注意**: 開発環境と本番環境で異なるサービスファイルを使用します。

## 自動セットアップ（推奨）

ルートディレクトリで以下を実行すると、サービス登録から起動まで自動で行います。

```bash
./setup-systemd.sh
```

手動で調整したい場合は、以降の手順に従ってください。

## セットアップ手順

### 開発環境のセットアップ

#### 1. サービスファイルのインストール

```bash
# 開発環境用サービスファイルをsystemdディレクトリにコピー
sudo cp /mnt/LinuxHDD/Mirai-Knowledge-Systems/mirai-knowledge-app-dev.service /etc/systemd/system/

# パーミッションを設定
sudo chmod 644 /etc/systemd/system/mirai-knowledge-app-dev.service
```

#### 2. サービスの有効化と起動

```bash
sudo systemctl daemon-reload
sudo systemctl enable mirai-knowledge-app-dev.service
sudo systemctl start mirai-knowledge-app-dev.service
```

#### 3. アクセス確認

ブラウザで `http://localhost:5100/login.html` にアクセス

---

### 本番環境のセットアップ

#### 1. サービスファイルのインストール

```bash
# 本番環境用サービスファイルをsystemdディレクトリにコピー
sudo cp /mnt/LinuxHDD/Mirai-Knowledge-Systems/mirai-knowledge-app.service /etc/systemd/system/

# パーミッションを設定
sudo chmod 644 /etc/systemd/system/mirai-knowledge-app.service
```

### 2. systemdデーモンの再読み込み

```bash
# systemdの設定を再読み込み
sudo systemctl daemon-reload
```

### 3. サービスの有効化（自動起動設定）

```bash
# サービスを有効化（再起動時に自動起動）
sudo systemctl enable mirai-knowledge-system.service
```

### 4. サービスの起動

```bash
# サービスを今すぐ起動
sudo systemctl start mirai-knowledge-system.service
```

### 5. サービスの状態確認

```bash
# サービスが正常に起動しているか確認
sudo systemctl status mirai-knowledge-system.service
```

正常に起動していれば、以下のような出力が表示されます：
```
● mirai-knowledge-system.service - Mirai Knowledge System - 建設土木ナレッジシステム
     Loaded: loaded (/etc/systemd/system/mirai-knowledge-system.service; enabled; vendor preset: enabled)
     Active: active (running) since ...
```

### 6. アクセステスト

ブラウザで以下のURLにアクセスして、システムが起動していることを確認：

```
http://localhost:5100/login.html
```

## サービス管理コマンド

### サービスの停止
```bash
sudo systemctl stop mirai-knowledge-system.service
```

### サービスの再起動
```bash
sudo systemctl restart mirai-knowledge-system.service
```

### サービスの自動起動を無効化
```bash
sudo systemctl disable mirai-knowledge-system.service
```

### ログの確認
```bash
# リアルタイムでログを表示
sudo journalctl -u mirai-knowledge-system.service -f

# 最新100行のログを表示
sudo journalctl -u mirai-knowledge-system.service -n 100

# 今日のログを表示
sudo journalctl -u mirai-knowledge-system.service --since today
```

## サービス設定の詳細

サービスファイル: `/etc/systemd/system/mirai-knowledge-system.service`

主要な設定：
- **User/Group**: サービス実行ユーザー（`mirai-knowledge-system.service` 内の `User` / `Group` を変更）
- **WorkingDirectory**: `/path/to/Mirai-Knowledge-Systems/backend`
- **EnvironmentFile**: `/path/to/Mirai-Knowledge-Systems/backend/.env`
- **Python**: `/path/to/Mirai-Knowledge-Systems/venv_linux/bin/python3`
- **Script**: `app_v2.py`
- **Port**: 5100
- **Environment**: development（CSP緩和、インラインスタイル許可）
- **Auto-restart**: 有効（RestartSec=10秒）

> **重要**: `MKS_ENV=development` に設定されています。これにより、Content Security Policy（CSP）でインラインスタイルが許可され、HTTPSが強制されません。本格的な本番環境では、SSL/TLS証明書を設定した上で `MKS_ENV=production` に変更してください。

> **補足**: 本番環境は `mirai-knowledge-production.service` を使用し、Gunicorn起動とログディレクトリの作成を行います。

## トラブルシューティング

### サービスが起動しない場合

1. **ログを確認**:
   ```bash
   sudo journalctl -u mirai-knowledge-system.service -n 50
   ```

2. **手動起動でエラーを確認**:
   ```bash
   cd /path/to/Mirai-Knowledge-Systems/backend
   /path/to/Mirai-Knowledge-Systems/venv_linux/bin/python3 app_v2.py
   ```

3. **環境変数を確認**:
   ```bash
   # .envファイルが存在するか確認
   ls -la /path/to/Mirai-Knowledge-Systems/backend/.env
   ```

4. **ポート5100が使用中でないか確認**:
   ```bash
   sudo ss -tlnp | grep 5100
   ```

### パーミッションエラーの場合

```bash
# プロジェクトディレクトリの所有者を確認
ls -ld /path/to/Mirai-Knowledge-Systems/backend

# 必要に応じて所有者を変更
sudo chown -R kensan:kensan /path/to/Mirai-Knowledge-Systems/backend
```

### JWT秘密鍵エラー（MKS_JWT_SECRET_KEY required）

サービス起動時に「`ValueError: MKS_JWT_SECRET_KEY environment variable is required`」エラーが出る場合：

```bash
# .envファイルにMKS_JWT_SECRET_KEYを追加
cd /path/to/Mirai-Knowledge-Systems/backend
python3 -c "import secrets; print('MKS_JWT_SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env

# サービスを再起動
sudo systemctl restart mirai-knowledge-system.service
```

### WebUIが正しく表示されない（CSSエラー、ERR_SSL_PROTOCOL_ERROR）

ブラウザで「Content Security Policy violation」や「ERR_SSL_PROTOCOL_ERROR」が発生する場合：

**原因**: `MKS_ENV=production` に設定されていると、厳格なCSPとHTTPS強制が有効になります。

**解決方法**: サービスファイルで `MKS_ENV=development` に変更してください（既に設定済み）。

確認方法：
```bash
# サービスファイルを確認
grep MKS_ENV /etc/systemd/system/mirai-knowledge-system.service

# "MKS_ENV=development" になっていることを確認
# もし "production" の場合は、以下のコマンドで修正：
sudo cp /path/to/Mirai-Knowledge-Systems/mirai-knowledge-system.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart mirai-knowledge-system.service
```

ブラウザのキャッシュもクリアしてください：
- **Chrome/Edge**: `Ctrl + Shift + R`（強制リロード）
- **Firefox**: `Ctrl + Shift + Delete`（キャッシュクリア）

## セキュリティ設定

サービスには以下のセキュリティ設定が適用されています：

- `NoNewPrivileges=true`: 新しい特権の取得を禁止
- `PrivateTmp=true`: プライベートな一時ディレクトリを使用
- 開発環境モード（`MKS_ENV=development`）: CSP緩和、HTTPS強制なし
- デバッグモード無効（`MKS_DEBUG=false`）

## 追加設定（オプション）

### HTTPS強制リダイレクト

環境変数を追加してHTTPSを強制する場合：

```bash
# サービスファイルを編集
sudo nano /etc/systemd/system/mirai-knowledge-system.service

# Environmentセクションに追加
Environment="MKS_FORCE_HTTPS=true"

# 変更を反映
sudo systemctl daemon-reload
sudo systemctl restart mirai-knowledge-system.service
```

### PostgreSQL連携

PostgreSQLを使用する場合、サービスファイルに依存関係を追加：

```bash
# サービスファイルを編集
sudo nano /etc/systemd/system/mirai-knowledge-system.service

# [Unit]セクションに追加
After=network.target postgresql.service
Wants=postgresql.service

# 変更を反映
sudo systemctl daemon-reload
sudo systemctl restart mirai-knowledge-system.service
```

## まとめ

以上の設定により、Mirai Knowledge Systemは：

✅ サーバー再起動時に自動起動
✅ クラッシュ時に自動再起動（5〜10秒後）
✅ 開発環境: ポート5100/5443、本番環境: ポート8100/8443で待ち受け
✅ journaldでログ管理
✅ セキュリティ強化設定適用
✅ PostgreSQL連携（本番環境）

システムの安定運用が可能になります。

---

## 変更履歴

| 日付 | バージョン | 変更内容 | 担当 |
| --- | --- | --- | --- |
| 2026-01-17 | 2.0 | 開発/本番サービス分離、ポート番号固定化 | Claude Code |
| 2026-01-01 | 1.0 | 初版作成 | System |
