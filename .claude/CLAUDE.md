# Mirai Knowledge Systems - プロジェクトコンテキスト

## 📋 プロジェクト概要

**名称**: Mirai Knowledge Systems
**目的**: 建設土木業界向け統合ナレッジ管理システム
**バージョン**: 1.2.0
**開発フェーズ**: Phase D-3（2要素認証）完了✅ - セキュリティ強化完了（2026-01-31）

## 🛠️ 技術スタック

### バックエンド
- **Framework**: Flask 3.1.2（Python 3.14.0）
- **Database**: PostgreSQL 15+（本番）/ JSON（開発）
- **ORM**: SQLAlchemy 2.0.45
- **認証**: JWT（Flask-JWT-Extended 4.6.0） + 2FA（pyotp 2.9.0）
- **2FA**: TOTP（pyotp）+ QRコード（qrcode 7.4.2, pillow 10.1.0）
- **監視**: Prometheus + Grafana

### フロントエンド
- **Framework**: Vanilla JavaScript（ES6+）
- **Testing**: Jest 29.7.0 + Playwright 1.57.0
- **Linting**: ESLint 8.56.0 + Prettier 3.1.1

### インフラ
- **WSGI Server**: Gunicorn（本番）
- **Reverse Proxy**: Nginx（本番）
- **Service Manager**: systemd（本番）

## 🔐 重要な権限設定

### 許可する操作
```json
"permissions": {
  "allow": [
    "Bash(npm run:*)",
    "Bash(git:*)",
    "Read(.claude/**)",
    "Edit(.claude/**)",
    "Read(backend/**/*.py)",
    "Edit(backend/**/*.py)",
    "Read(webui/**/*.js)",
    "Edit(webui/**/*.js)"
  ]
}
```

### 拒否する操作
```json
"deny": [
  "Read(./.env)",
  "Read(./.env.*)",
  "Read(backend/.env)",
  "Read(backend/data/users.json)",
  "Edit(backend/data/**)",
  "Bash(rm -rf *)",
  "Bash(shutdown *)"
]
```

## 🌐 MCPサーバー設定

### 利用可能なMCPサーバー

1. **brave-search** - Web検索
   - 最新技術情報の検索
   - セキュリティ脆弱性の調査

2. **chrome-devtools** - ブラウザ検証
   - WebUI動作検証
   - コンソールエラー検出・修正

3. **context7** - ライブラリドキュメント
   - フレームワーク仕様参照
   - API仕様確認

4. **github** - GitHub統合
   - PRレビュー
   - Issue管理
   - コミット履歴確認

5. **memory** - セッション間メモリ
   - 設計決定の記憶
   - 頻繁に参照する情報

6. **memory-keeper** - 永続記憶
   - プロジェクト文脈の永続化
   - 意思決定履歴の保存

7. **playwright** - ブラウザ自動化
   - E2Eテストの実行
   - UIスクリーンショット

8. **sequential-thinking** - 段階的思考
   - 複雑なアーキテクチャ設計
   - パフォーマンス最適化

## 🎯 カスタムスキル

### /commit-push-pr
変更をコミット、プッシュ、PR作成

**使用例**: 「Phase B-6/B-7完了をコミットしてPR作成して」

### /commit-push-pr-merge
変更をコミット、プッシュ、PR作成、マージ

**使用例**: 「緊急修正をコミットしてマージまで完了して」

## 📊 プロジェクト構造

```
Mirai-Knowledge-Systems/
├── backend/                 # Flask API（2,356行のapp_v2.py）
│   ├── app_v2.py           # メインアプリケーション（36エンドポイント、+9 MFA API）
│   ├── auth/               # 認証モジュール（NEW v1.2.0）
│   │   ├── __init__.py
│   │   └── totp_manager.py # TOTP Manager（270行）
│   ├── models.py           # データモデル（11テーブル + mfa_backup_codes）
│   ├── schemas.py          # バリデーション
│   ├── password_policy.py  # パスワードポリシー
│   ├── csrf_protection.py  # CSRF対策
│   ├── migrations/         # DBマイグレーション
│   │   └── versions/add_mfa_backup_codes.py  # MFA対応（NEW）
│   ├── tests/              # テストスイート（557件、カバレッジ91%）
│   │   ├── unit/test_totp_manager.py        # MFAユニットテスト（19件）
│   │   ├── integration/test_mfa_flow.py     # MFA統合テスト（17件）
│   │   └── e2e/mfa-flow.spec.js             # MFAE2Eテスト
│   └── data/               # JSONデータ（開発環境）
├── webui/                  # フロントエンド（16ファイル）
│   ├── app.js              # メインロジック（2,500行+）
│   ├── mfa.js              # MFAライブラリ（380行、NEW v1.2.0）
│   ├── mfa-setup.html      # MFAセットアップウィザード（NEW）
│   ├── mfa-settings.html   # MFA設定管理画面（NEW）
│   ├── search-history.js   # 検索履歴
│   ├── search-pagination.js # ページネーション
│   └── auth-guard.js       # 認証ガード
├── docs/                   # ドキュメント
│   ├── security/2FA_IMPLEMENTATION.md        # 技術ドキュメント（NEW）
│   ├── user-guide/MFA_SETUP_GUIDE.md         # ユーザーガイド（NEW）
│   ├── deployment/2FA_DEPLOYMENT_GUIDE.md    # デプロイガイド（NEW）
│   └── 2FA_COMPLETION_SUMMARY.md             # 完了サマリー（NEW）
├── scripts/                 # クロスプラットフォームスクリプト
│   ├── common/             # Python共通スクリプト
│   │   └── setup-node-modules.py  # OS判定自動切替
│   ├── windows/            # Windows専用
│   │   └── setup-node-modules.ps1 # PowerShell版
│   └── linux/              # Linux専用
│       └── setup-node-modules.sh  # Bash版
├── mirai-knowledge-app.service     # systemd本番用
└── mirai-knowledge-app-dev.service # systemd開発用
```

## 🚀 開発状況

### Phase B: 本番環境開発（100%完了）✅

| Phase | 名称 | 進捗 | 状態 |
|-------|------|------|------|
| B-1〜B-5 | 基盤実装 | 100% | ✅ 完了 |
| B-6 | 検索・通知 | 100% | ✅ 完了 |
| B-7 | WebUI統合 | 100% | ✅ 完了 |
| B-8 | セキュリティ | 100% | ✅ 完了（2026-01-06）|
| B-9 | 品質保証 | 100% | ✅ 完了（カバレッジ91%、テスト538件）|
| B-10 | PostgreSQL移行 | 100% | ✅ 完了（PostgreSQL 16.11稼働）|
| B-11 | 本番準備 | 100% | ✅ 完了（SSL/HTTPS、E2E環境構築）|

### Phase E: クロスプラットフォーム対応（100%完了）✅

| Phase | 名称 | 進捗 | 状態 |
|-------|------|------|------|
| E-1 | Node.jsモジュールOS分離 | 100% | ✅ 完了（node_modules.windows/linux）|
| E-2 | WebUIタイトル環境表示 | 100% | ✅ 完了（[開発]/[本番]タイトル）|
| E-3 | 本番環境空状態表示 | 100% | ✅ 完了（○○データなし表示）|
| E-4 | systemdサービス分離 | 100% | ✅ 完了（dev/prod分離、2026-01-17）|

## 🐛 既知の問題

### Critical: 0件 ✅
すべて修正済み

### High: 0件 ✅
- ~~console.log残留~~ → セキュアロガー導入で解決
- ~~innerHTML使用~~ → 全てDOM APIに置換済み

### Medium: 2件
1. フロントエンドのモジュール化
2. N+1クエリ最適化

### 完了済み ✅
- ~~2要素認証（オプション）~~ → Phase D-3で実装完了（2026-01-31）

## 🎯 次のマイルストーン

### Phase C: 本番運用開始 🚀

| Phase | 名称 | 進捗 | 状態 |
|-------|------|------|------|
| C-1-1 | 本番サーバー稼働確認 | 100% | ✅ 完了（2026-01-25）|
| C-1-2 | systemdサービス自動起動確認 | 100% | ✅ 完了 |
| C-1-3 | SSL証明書有効期限確認 | 100% | ✅ 完了 |
| C-1-4 | バックアップスクリプト動作確認 | 100% | ✅ 完了 |
| C-2-1 | データ移行計画策定 | 100% | ✅ 完了 |
| C-2-2 | データ移行スクリプト作成 | 100% | ✅ 完了 |
| C-2-3 | 移行テスト実行 | 100% | ✅ 完了 |
| C-3 | 運用監視体制構築 | 100% | ✅ 完了（2026-01-25）|
| C-4 | ユーザートレーニング | 100% | ✅ 完了（2026-01-25）|

### Phase D: 機能拡張（100%完了）✅

| Phase | 名称 | 進捗 | 状態 |
|-------|------|------|------|
| D-3 | 2要素認証（2FA/MFA） | 100% | ✅ 完了（2026-01-31）|

#### Phase D-3: 2要素認証実装（v1.2.0）

**完了日**: 2026-01-31
**PR**: [#2593](https://github.com/Kensan196948G/Mirai-Knowledge-Systems/pull/2593)
**コミット**: `23ca118` → マージ `056f962`

##### 実装内容

**バックエンド（約800行）**:
- TOTP Manager（pyotp, qrcode, pillow）
- MFA API 9エンドポイント
  - セットアップ、有効化、無効化
  - ログイン検証（TOTP + バックアップコード）
  - バックアップコード再生成
  - MFAステータス取得
- データベースmfa_backup_codesカラム（JSONB）
- Rate limiting（ブルートフォース対策: 5回/15分）
- 監査ログイベント11種追加

**フロントエンド（約1,130行）**:
- MFAセットアップウィザード（3ステップ）
  1. QRコードスキャン
  2. TOTP検証
  3. バックアップコード保存
- MFA設定管理画面
- ログイン画面MFA対応
- mfa.jsライブラリ（380行）

**テスト（約1,000行）**:
- ✅ ユニットテスト: 19/19 PASSED (test_totp_manager.py)
- 統合テスト: 17件 (test_mfa_flow.py)
- E2Eテスト: Playwright対応 (mfa-flow.spec.js)

**ドキュメント（約1,500行）**:
- 技術ドキュメント（2FA_IMPLEMENTATION.md）
- ユーザーガイド（MFA_SETUP_GUIDE.md）
- デプロイガイド（2FA_DEPLOYMENT_GUIDE.md）
- 完了サマリー（2FA_COMPLETION_SUMMARY.md）

##### セキュリティ強化
- TOTP検証（RFC 6238準拠、±30秒ウィンドウ）
- バックアップコード（bcrypt、1回限り使用）
- Rate limiting（MFA検証: 5回/15分）
- mfa_token（5分有効期限）
- 監査ログ記録

##### 互換性
- **認証アプリ**: Google Authenticator, Microsoft Authenticator, Authy, 1Password, Bitwarden
- **ブラウザ**: Chrome/Edge 90+, Firefox 88+, Safari 14+

---

### Phase D: 今後の拡張（オプション）

| Phase | 名称 | 優先度 | 状態 |
|-------|------|--------|------|
| D-4 | Microsoft 365連携 | 中 | 未着手 |
| D-5 | モバイルアプリ対応（PWA） | 低 | 未着手 |
| D-3.1 | 2FA拡張（SMS/WebAuthn） | 低 | 未着手 |

## 🔧 環境情報

### 開発環境
- **OS**: Windows 11 / Linux (Ubuntu 24.04)
- **Database**: JSON（開発）
- **Port**: 5200 (HTTP) / 5243 (HTTPS)
- **共有フォルダ**: Z:\Mirai-Knowledge-Systems = /mnt/LinuxHDD/Mirai-Knowledge-Systems
- **Node.js**: node_modules.windows / node_modules.linux で分離
- **Linux**: http://192.168.0.187:5200 / https://192.168.0.187:5243
- **Windows**: http://192.168.0.145:5200 / https://192.168.0.145:5243

### 本番環境
- **OS**: Linux (Ubuntu 24.04)
- **Database**: PostgreSQL 16.11
- **Port**: 9100 (HTTP) / 9443 (HTTPS)
- **SSL**: 自己署名証明書（/etc/ssl/mks）
- **サーバー**: Nginx + Gunicorn + systemd
- **URL**: http://192.168.0.187:9100 / https://192.168.0.187:9443

## 📝 重要な注意事項

1. **データファイル**: backend/data/*.json は直接編集しない（APIを使用）
2. **.env ファイル**: 秘密鍵を含むため、Gitにコミットしない
3. **本番環境**: MKS_ENV=production 時はデモユーザー作成をスキップ
4. **テスト実行**: 本番環境では外部通知を無効化

## 🎨 コーディング規約

- **Python**: PEP 8準拠、black + isort推奨
- **JavaScript**: ESLint設定に従う、console.logは本番で削除
- **コミットメッセージ**: 「機能: 」「修正: 」等のプレフィックス使用

## 🤖 SubAgent 9体構成（必須遵守）

### SubAgent一覧

| # | Agent名 | 責務 | 成果物 |
|---|---------|------|--------|
| 1 | spec-planner | 要件・運用定義 | specs/*.md |
| 2 | arch-reviewer | 設計レビュー | design/*.md |
| 3 | code-implementer | 実装 | src/**, backend/**, webui/** |
| 4 | code-reviewer | 自動レビューゲート | reviews/*_feature_*.json |
| 5 | test-designer | テスト設計 | tests/*.md |
| 6 | test-reviewer | テストレビュー | reviews/*_test_review.json |
| 7 | ci-specialist | CI/リリース | ci/**, .github/workflows/** |
| 8 | sec-auditor | セキュリティ監査 | security/**, audits/** |
| 9 | ops-runbook | 運用手順書 | runbook/**, docs/operations/** |

### 工程遷移フロー（Hooks連携）

```
spec-planner → arch-reviewer → code-implementer → code-reviewer
                                                       ↓
                               ←←← FAIL ←←← [判定]
                                                       ↓ PASS
                                               test-designer → test-reviewer
                                                                      ↓
                                               ←←← FAIL ←←← [判定]
                                                                      ↓ PASS
                                                              ci-specialist
```

### 自動並列実行トリガー

#### 1. 複数の独立タスク
- 複数のバグ修正
- 複数の独立機能実装
- 自動起動: 複数のcode-implementerを単一メッセージで並列起動
- 制約: ファイルコンフリクトなし確認

#### 2. 新機能実装
- 検出条件: 「機能追加」「実装」「新規エンドポイント」
- 並列起動: spec-planner + arch-reviewer + test-designer
- 順次起動: code-implementer（設計完了後）
- 制約: 編集はcode-implementerのみ

#### 3. セキュリティ監査
- 検出条件: 「セキュリティチェック」「脆弱性スキャン」
- 順次起動: sec-auditor → code-implementer → test-designer
- MCP必須: brave-search（CVE情報）

#### 4. コードベース調査
- 検出条件: 「実装状況確認」「コードベース調査」
- 起動: arch-reviewer（Explore agent, thoroughness: medium）
- 制約: 編集禁止（調査のみ）

#### 5. ドキュメント整備
- 検出条件: 「運用手順書」「ドキュメント作成」
- 起動: ops-runbook（単独）
- 制約: docs/ またはrunbook/ のみ編集

### 並列実行の必須ルール

**CRITICAL**: 並列実行時は必ず単一メッセージで複数Task tool呼び出しを実行

### MCP使用ルール

- memory / memory-keeper: 過去の設計決定を必ず初動で確認
- github: 類似実装の検索に使用
- context7: ライブラリドキュメント確認
- chrome-devtools: WebUI検証・エラー修正
- sequential-thinking: 複雑な設計判断

---

**このファイルはClaude Codeが自動的に読み込みます。**
**プロジェクト固有の重要な情報を追記してください。**
