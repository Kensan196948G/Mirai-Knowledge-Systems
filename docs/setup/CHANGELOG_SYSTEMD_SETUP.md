# systemd自動起動設定 - 変更履歴

**日付**: 2026-01-01
**担当**: Claude Code
**目的**: サーバー再起動時の自動起動設定とドキュメント更新

---

## 📋 変更概要

Mirai Knowledge Systemにsystemdサービスとしての自動起動機能を追加し、関連ドキュメントを更新しました。

---

## 🔧 実装内容

### 1. systemdサービスファイルの作成

**ファイル**: `mirai-knowledge-system.service`

主要な設定：
- サービス名: `mirai-knowledge-system.service`
- ユーザー: kensan
- 作業ディレクトリ: `/path/to/Mirai-Knowledge-Systems/backend`
- 実行ファイル: `app_v2.py`
- ポート: **5100**
- 環境モード: **development**
- 自動再起動: 有効（10秒後）
- 環境ファイル: `/path/to/Mirai-Knowledge-Systems/backend/.env`

```ini
[Service]
Type=simple
User=kensan
Group=kensan
WorkingDirectory=/path/to/Mirai-Knowledge-Systems/backend
EnvironmentFile=/path/to/Mirai-Knowledge-Systems/backend/.env
Environment="PATH=/path/to/Mirai-Knowledge-Systems/venv_linux/bin:/usr/local/bin:/usr/bin:/bin"
Environment="MKS_ENV=development"
Environment="MKS_DEBUG=false"
ExecStart=/path/to/Mirai-Knowledge-Systems/venv_linux/bin/python3 app_v2.py
Restart=always
RestartSec=10
```

### 2. 自動セットアップスクリプトの作成

**ファイル**: `setup-systemd.sh`

機能：
- サービスファイルのインストール
- systemdデーモンの再読み込み
- サービスの有効化（自動起動設定）
- サービスの起動
- ステータス確認

### 3. セットアップガイドの作成

**ファイル**: `SYSTEMD_SETUP.md`

内容：
- 詳細なセットアップ手順
- サービス管理コマンド
- トラブルシューティング（JWT秘密鍵エラー、CSP/SSLエラー対処法）
- セキュリティ設定の説明
- 本番環境への移行ガイド

---

## 🔑 環境変数の追加

### `.env` ファイルへの追加

```bash
MKS_JWT_SECRET_KEY=h-wX3sbcsOpL7EX5WEdClcHHMtZqSeLJRU7hMFXEM0o
```

- JWT認証に必要な秘密鍵を追加
- セキュアなランダム文字列（32文字以上）

### `.env.example` の更新

```bash
# JWT秘密鍵（必須: 最低32文字以上の安全なランダム文字列）
# 生成例: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# 注意: 本番環境では必ず以下のコマンドで安全な鍵を生成してください
#       python3 -c "import secrets; print('MKS_JWT_SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env
MKS_JWT_SECRET_KEY=your-secure-random-jwt-secret-key-minimum-32-characters
```

---

## 🐛 トラブルシューティング対応

### 問題1: JWT秘密鍵エラー

**エラー**: `ValueError: MKS_JWT_SECRET_KEY environment variable is required`

**解決**: `.env`ファイルに`MKS_JWT_SECRET_KEY`を追加

### 問題2: WebUI表示エラー（CSP違反、SSL/TLSエラー）

**エラー**:
- `Content Security Policy violation: Applying inline style violates...`
- `ERR_SSL_PROTOCOL_ERROR`

**原因**: `MKS_ENV=production` 設定により、厳格なCSPとHTTPS強制が有効

**解決**: systemdサービスファイルで `MKS_ENV=development` に変更

**影響**:
- CSPでインラインスタイルが許可される
- HTTPS強制が無効化される
- HTTPで正常にアクセス可能

---

## 📝 ドキュメント更新

### 1. README.md

**変更内容**:
- ポート番号を5000 → **5100**に更新
- systemd自動起動の説明を追加
- ネットワーク経由アクセスの注記を追加
- セットアップ手順にsystemdスクリプトの案内を追加

### 2. SETUP.md

**変更内容**:
- ポート番号を5000 → **5100**に更新
- JWT秘密鍵の設定手順を追加
- systemd自動起動セクションを追加
- トラブルシューティングを更新（ポート5100対応、systemd停止コマンド追加）
- 本番環境への移行ガイドを更新

### 3. backend/.env.example

**変更内容**:
- JWT秘密鍵生成コマンドの詳細説明を追加
- セキュリティに関する注意事項を強化

### 4. SYSTEMD_SETUP.md（新規作成）

**内容**:
- systemd自動起動の詳細ガイド
- セットアップ手順（手動/自動）
- サービス管理コマンド一覧
- トラブルシューティング（JWT、CSP、SSL対応）
- セキュリティ設定の説明

### 5. setup-systemd.sh（新規作成）

**内容**:
- ワンコマンドセットアップスクリプト
- 自動エラーチェック
- 詳細な進捗表示
- アクセスURL、デモアカウント情報の表示

---

## ✅ テスト結果

### 動作確認

1. ✅ サービスが正常に起動
2. ✅ ポート5100でアクセス可能
3. ✅ WebUIが正しく表示（CSP問題解決）
4. ✅ ログインページが機能
5. ✅ 自動起動が有効化

### 確認コマンド

```bash
# サービスステータス
sudo systemctl status mirai-knowledge-system.service

# 出力例:
● mirai-knowledge-system.service - Mirai Knowledge System - 建設土木ナレッジシステム
     Loaded: loaded (/etc/systemd/system/mirai-knowledge-system.service; enabled; preset: enabled)
     Active: active (running)
```

---

## 🔒 セキュリティ考慮事項

### 現在の設定（開発モード）

- **環境**: `MKS_ENV=development`
- **CSP**: インラインスタイル許可（`unsafe-inline`）
- **HTTPS**: 強制なし
- **用途**: 開発・テスト環境

### 本番環境への移行時の推奨設定

1. SSL/TLS証明書の設定
2. `MKS_ENV=production` に変更
3. `MKS_FORCE_HTTPS=true` に設定
4. 本番用WSGIサーバー（Gunicorn等）の導入
5. PostgreSQLへの移行

---

## 📊 ファイル一覧

### 新規作成

- `mirai-knowledge-system.service` - systemdサービス定義
- `setup-systemd.sh` - 自動セットアップスクリプト
- `SYSTEMD_SETUP.md` - systemdセットアップガイド
- `CHANGELOG_SYSTEMD_SETUP.md` - この変更履歴（本ファイル）

### 更新

- `README.md` - ポート5100、systemd情報追加
- `SETUP.md` - ポート5100、systemd、JWT秘密鍵情報更新
- `backend/.env` - MKS_JWT_SECRET_KEY追加
- `backend/.env.example` - JWT秘密鍵の詳細説明追加

---

## 🚀 今後の改善案

1. **Gunicorn統合**: 本番用WSGIサーバーのsystemd設定
2. **PostgreSQL統合**: データベース起動順序の依存関係設定
3. **ログローテーション**: journaldログの自動アーカイブ設定
4. **モニタリング**: Prometheus/Grafana統合
5. **SSL/TLS**: Let's Encrypt自動更新設定

---

## 📞 サポート

問題が発生した場合：

1. [SYSTEMD_SETUP.md](SYSTEMD_SETUP.md) のトラブルシューティングセクションを参照
2. ログを確認: `sudo journalctl -u mirai-knowledge-system.service -n 50`
3. サービスを再起動: `sudo systemctl restart mirai-knowledge-system.service`

---

**変更完了日**: 2026-01-01
**バージョン**: v1.0 (systemd対応)
