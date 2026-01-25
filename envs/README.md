# 🔧 Mirai Knowledge Systems - 環境設定ガイド

**作成日**: 2026-01-17
**バージョン**: 1.0.0

---

## 📋 概要

このディレクトリには、開発環境と本番環境の設定ファイルが格納されています。

## 📁 ディレクトリ構造

```
envs/
├── README.md                      # このファイル
├── development/
│   ├── .env.development           # 開発環境設定
│   └── data/                      # 開発用データ（サンプルデータへのリンク）
└── production/
    ├── .env.production            # 本番環境設定
    └── data/                      # 本番用データ（空）
```

---

## 🔒 ポート番号（固定）

⚠️ **重要**: ポート番号は固定です。開発途中で変更しないでください。

| 環境 | HTTP | HTTPS | 用途 |
|------|------|-------|------|
| **開発環境** | **5100** | **5443** | 開発・テスト |
| **本番環境** | **8100** | **8443** | 本番運用 |

---

## 🚀 クイックスタート

### 開発環境

```bash
# Linux
./scripts/linux/start-dev.sh

# Windows (PowerShell)
.\scripts\windows\start-dev.ps1
```

**アクセスURL**:
- HTTP: `http://localhost:5100` [開発]
- HTTPS: `https://localhost:5443` [開発]

### 本番環境

```bash
# Linux
./scripts/linux/start-prod.sh

# Windows (PowerShell)
.\scripts\windows\start-prod.ps1
```

**アクセスURL**:
- HTTP: `http://192.168.0.187:8100` [本番]
- HTTPS: `https://192.168.0.187:8443` [本番]

---

## ⚙️ 環境変数の説明

### 共通設定

| 変数名 | 説明 | 開発 | 本番 |
|--------|------|------|------|
| `MKS_ENV` | 環境モード | `development` | `production` |
| `MKS_HTTP_PORT` | HTTPポート | `5100` | `8100` |
| `MKS_HTTPS_PORT` | HTTPSポート | `5443` | `8443` |
| `MKS_DEBUG` | デバッグモード | `true` | `false` |
| `MKS_SECRET_KEY` | アプリ秘密鍵 | 開発用固定値 | **要変更** |
| `MKS_JWT_SECRET_KEY` | JWT秘密鍵 | 開発用固定値 | **要変更** |

### データベース設定

| 変数名 | 説明 | 開発 | 本番 |
|--------|------|------|------|
| `MKS_USE_POSTGRESQL` | PostgreSQL使用 | `false` | `true` |
| `DATABASE_URL` | DB接続URL | - | **必須** |
| `MKS_DATA_DIR` | JSONデータディレクトリ | `backend/data` | - |

### セキュリティ設定

| 変数名 | 説明 | 開発 | 本番 |
|--------|------|------|------|
| `MKS_FORCE_HTTPS` | HTTPS強制 | `false` | `true` |
| `MKS_HSTS_ENABLED` | HSTS有効化 | `false` | `true` |
| `CORS_ORIGINS` | 許可オリジン | localhost | 本番URL |

### サンプルデータ設定

| 変数名 | 説明 | 開発 | 本番 |
|--------|------|------|------|
| `MKS_LOAD_SAMPLE_DATA` | サンプルデータ読込 | `true` | `false` |
| `MKS_CREATE_DEMO_USERS` | デモユーザー作成 | `true` | `false` |

---

## 🔐 本番環境のセキュリティ設定

### 秘密鍵の生成

```bash
# Python で安全な秘密鍵を生成
python3 -c "import secrets; print(secrets.token_hex(32))"
```

生成した値を `.env.production` の以下の変数に設定してください：
- `MKS_SECRET_KEY`
- `MKS_JWT_SECRET_KEY`

### SSL証明書

本番環境では自己署名SSL証明書を使用します：
- 証明書: `ssl/server.crt`
- 秘密鍵: `ssl/server.key`

---

## ✅ 環境変数の検証

環境変数が正しく設定されているか確認するには：

```bash
# 開発環境の検証
python scripts/common/env-validator.py development

# 本番環境の検証
python scripts/common/env-validator.py production

# 両方の環境を検証
python scripts/common/env-validator.py all
```

---

## 📝 ブックマーク設定

ブラウザのブックマークには環境名を明記してください：

| 環境 | URL | ブックマーク名 |
|------|-----|--------------|
| 開発 | `https://localhost:5443` | **[開発] Mirai Knowledge** |
| 本番 | `https://192.168.0.187:8443` | **[本番] Mirai Knowledge** |

---

## ⚠️ 注意事項

1. **本番環境の `.env.production` はGitにコミットしないでください**
   - `.gitignore` に登録済みです

2. **ポート番号は変更しないでください**
   - 開発: 5100/5443
   - 本番: 8100/8443

3. **本番環境では必ず秘密鍵を変更してください**
   - `MKS_SECRET_KEY`
   - `MKS_JWT_SECRET_KEY`

4. **サンプルデータは本番環境では無効にしてください**
   - `MKS_LOAD_SAMPLE_DATA=false`
   - `MKS_CREATE_DEMO_USERS=false`

---

## 📊 環境比較表

| 項目 | 開発環境 | 本番環境 |
|------|----------|----------|
| ポート | 5100/5443 | 8100/8443 |
| デバッグ | 有効 | 無効 |
| HTTPS強制 | 無効 | 有効 |
| サンプルデータ | 有効 | 無効 |
| デモユーザー | 有効 | 無効 |
| PostgreSQL | オプション | 必須 |
| ログレベル | DEBUG | WARNING |
| レート制限 | 無効 | 有効 |

---

## 📅 更新履歴

| 日付 | 変更内容 |
|------|----------|
| 2026-01-17 | 初版作成 |

---

**🚀 Mirai Knowledge Systems で建設土木の知識を共有しましょう！**
