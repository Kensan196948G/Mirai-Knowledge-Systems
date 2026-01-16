# Mirai Knowledge Systems - プロジェクトコンテキスト

## 📋 プロジェクト概要

**名称**: Mirai Knowledge Systems
**目的**: 建設土木業界向け統合ナレッジ管理システム
**バージョン**: 1.0.0
**開発フェーズ**: Phase B-11（本番準備）完了✅ - 本番稼働可能

## 🛠️ 技術スタック

### バックエンド
- **Framework**: Flask 3.1.2（Python 3.14.0）
- **Database**: PostgreSQL 15+（本番）/ JSON（開発）
- **ORM**: SQLAlchemy 2.0.45
- **認証**: JWT（Flask-JWT-Extended 4.6.0）
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

2. **github** - GitHub統合
   - PRレビュー
   - Issue管理
   - コミット履歴確認

3. **memory** - セッション間メモリ
   - 設計決定の記憶
   - 頻繁に参照する情報

4. **sqlite** - データベースクエリ
   - 開発環境のデータ確認
   - テストデータの作成

5. **playwright** - ブラウザ自動化
   - E2Eテストの実行
   - UIスクリーンショット

6. **sequential-thinking** - 段階的思考
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
│   ├── app_v2.py           # メインアプリケーション（27エンドポイント）
│   ├── models.py           # データモデル（11テーブル）
│   ├── schemas.py          # バリデーション
│   ├── password_policy.py  # パスワードポリシー
│   ├── csrf_protection.py  # CSRF対策
│   ├── tests/              # テストスイート（538件、カバレッジ91%）
│   └── data/               # JSONデータ（開発環境）
└── webui/                  # フロントエンド（13ファイル）
    ├── app.js              # メインロジック（2,428行）
    ├── search-history.js   # 検索履歴
    ├── search-pagination.js # ページネーション
    └── auth-guard.js       # 認証ガード
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

## 🐛 既知の問題

### Critical: 0件 ✅
すべて修正済み

### High: 0件 ✅
- ~~console.log残留~~ → セキュアロガー導入で解決
- ~~innerHTML使用~~ → 全てDOM APIに置換済み

### Medium: 3件
1. フロントエンドのモジュール化
2. N+1クエリ最適化
3. 2要素認証（オプション）

## 🎯 次のマイルストーン

- **Phase C: 本番運用開始** 🚀
  - 本番データ移行
  - ユーザートレーニング
  - 運用監視体制構築
- **Phase D: 機能拡張（オプション）**
  - Microsoft 365連携（SharePoint/OneDrive）
  - 2要素認証
  - モバイルアプリ対応

## 🔧 環境情報

- **OS**: Linux (Ubuntu 24.04)
- **Database**: PostgreSQL 16.11
- **Port**: 5100 (HTTP) / 443 (HTTPS)
- **SSL**: 自己署名証明書（/etc/ssl/mks）
- **サーバー**: ✅ 稼働中（Nginx + Gunicorn + systemd）

## 📝 重要な注意事項

1. **データファイル**: backend/data/*.json は直接編集しない（APIを使用）
2. **.env ファイル**: 秘密鍵を含むため、Gitにコミットしない
3. **本番環境**: MKS_ENV=production 時はデモユーザー作成をスキップ
4. **テスト実行**: 本番環境では外部通知を無効化

## 🎨 コーディング規約

- **Python**: PEP 8準拠、black + isort推奨
- **JavaScript**: ESLint設定に従う、console.logは本番で削除
- **コミットメッセージ**: 「機能: 」「修正: 」等のプレフィックス使用

## 🤖 SubAgent自動起動ルール（必須遵守）

### 基本原則

すべての開発タスクで、以下のルールに従ってSubAgentを自動起動すること。

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

- memory: 過去の設計決定を必ず初動で確認
- github: 類似実装の検索に使用
- context7: ライブラリドキュメント確認
- brave-search: 最新情報・CVE検索

---

**このファイルはClaude Codeが自動的に読み込みます。**
**プロジェクト固有の重要な情報を追記してください。**
