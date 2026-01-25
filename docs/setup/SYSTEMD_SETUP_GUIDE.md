# systemd サービスセットアップガイド

## 📋 概要

Mirai Knowledge Systemをsystemdサービスとしてセットアップするためのガイドです。

## 🎯 準備完了項目

- ✅ gunicorn 23.0.0 インストール済み
- ✅ サービスファイル作成済み
  - `mirai-knowledge-system-dev.service` (開発モード)
  - `mirai-knowledge-production.service` (本番モード)
- ✅ gunicorn設定をport 5100に変更済み
- ✅ requirements.txtにgunicornを追加済み

## 🚀 インストール方法

### 方法1: 自動インストールスクリプト（推奨）

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems
./install-systemd-service.sh
```

インタラクティブメニューで選択：
- **1**: 開発モード（python3直接実行）
- **2**: 本番モード（gunicorn使用、推奨）

### 方法2: 手動インストール

#### 開発モードの場合

```bash
# 既存サービスを停止
sudo systemctl stop mirai-knowledge-system.service 2>/dev/null || true

# サービスファイルをコピー
sudo cp mirai-knowledge-system-dev.service /etc/systemd/system/mirai-knowledge-system.service

# systemdリロード
sudo systemctl daemon-reload

# サービス有効化・起動
sudo systemctl enable mirai-knowledge-system.service
sudo systemctl start mirai-knowledge-system.service

# 状態確認
sudo systemctl status mirai-knowledge-system.service
```

#### 本番モードの場合（推奨）

```bash
# 既存サービスを停止
sudo systemctl stop mirai-knowledge-system.service 2>/dev/null || true

# サービスファイルをコピー
sudo cp mirai-knowledge-production.service /etc/systemd/system/mirai-knowledge-prod.service

# systemdリロード
sudo systemctl daemon-reload

# サービス有効化・起動
sudo systemctl enable mirai-knowledge-prod.service
sudo systemctl start mirai-knowledge-prod.service

# 状態確認
sudo systemctl status mirai-knowledge-prod.service
```

## 📊 サービス管理コマンド

### 開発モード

```bash
# 起動
sudo systemctl start mirai-knowledge-system

# 停止
sudo systemctl stop mirai-knowledge-system

# 再起動
sudo systemctl restart mirai-knowledge-system

# 状態確認
sudo systemctl status mirai-knowledge-system

# ログ確認（リアルタイム）
sudo journalctl -u mirai-knowledge-system -f

# ログ確認（最新100行）
sudo journalctl -u mirai-knowledge-system -n 100
```

### 本番モード

```bash
# 起動
sudo systemctl start mirai-knowledge-prod

# 停止
sudo systemctl stop mirai-knowledge-prod

# 再起動
sudo systemctl restart mirai-knowledge-prod

# Graceful reload（gunicornのみ）
sudo systemctl reload mirai-knowledge-prod

# 状態確認
sudo systemctl status mirai-knowledge-prod

# ログ確認（リアルタイム）
sudo journalctl -u mirai-knowledge-prod -f
```

## 🔍 トラブルシューティング

### ポートがすでに使用されている

```bash
# ポート5100を使用しているプロセスを確認
sudo lsof -i :5100

# プロセスを停止
kill <PID>
```

### サービス起動失敗

```bash
# 詳細なログを確認
sudo journalctl -u mirai-knowledge-system -n 50 --no-pager

# 設定ファイルの構文チェック
sudo systemd-analyze verify /etc/systemd/system/mirai-knowledge-system.service
```

### PostgreSQL接続エラー

```bash
# PostgreSQL起動確認
sudo systemctl status postgresql

# PostgreSQL起動
sudo systemctl start postgresql
```

## ⚙️ 設定詳細

### 開発モード vs 本番モード

| 項目 | 開発モード | 本番モード |
|------|----------|----------|
| 実行方法 | python3直接実行 | gunicorn WSGIサーバー |
| ポート | 5100 | 5100 |
| ワーカー数 | 1 | CPU数×2+1 |
| 自動リロード | なし | あり（HUPシグナル） |
| パフォーマンス | 低 | 高 |
| メモリ使用量 | 少 | 多 |
| 推奨環境 | 開発・テスト | 本番運用 |

### gunicorn設定（本番モード）

- **ワーカー数**: CPU コア数 × 2 + 1
- **ワーカークラス**: sync（同期）
- **タイムアウト**: 30秒
- **最大リクエスト数**: 1000（メモリリーク対策）
- **ログ**: `/var/log/mirai-knowledge/` に出力

## 🔐 セキュリティ設定

両モード共通のsystemdセキュリティ機能：

- `NoNewPrivileges=true` - 特権昇格防止
- `PrivateTmp=true` - プライベート/tmpディレクトリ

本番モード追加設定：

- `ProtectSystem=strict` - システムディレクトリ保護
- `ProtectHome=true` - ホームディレクトリ保護
- `ReadWritePaths` - 必要な書き込みパスのみ許可

## 📝 次のステップ

1. ✅ systemdサービスセットアップ完了
2. ⏭️ E2Eテスト実行
3. ⏭️ ログローテーション設定
4. ⏭️ 本番環境最終確認

---

**作成日**: 2026-01-08
**バージョン**: 1.0.0
