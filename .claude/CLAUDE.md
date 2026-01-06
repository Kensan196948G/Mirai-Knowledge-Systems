# Mirai Knowledge Systems - プロジェクトコンテキスト

## 📋 プロジェクト概要

**名称**: Mirai Knowledge Systems
**目的**: 建設土木業界向け統合ナレッジ管理システム
**バージョン**: 2.0.0
**開発フェーズ**: Phase B-8 (95%完了)

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
│   ├── tests/              # テストスイート（547件）
│   └── data/               # JSONデータ（開発環境）
└── webui/                  # フロントエンド（13ファイル）
    ├── app.js              # メインロジック（2,428行）
    ├── search-history.js   # 検索履歴
    ├── search-pagination.js # ページネーション
    └── auth-guard.js       # 認証ガード
```

## 🚀 開発状況

### Phase B: 本番環境開発（85%完了）

| Phase | 名称 | 進捗 | 状態 |
|-------|------|------|------|
| B-1〜B-5 | 基盤実装 | 100% | ✅ 完了 |
| B-6 | 検索・通知 | 100% | ✅ 完了 |
| B-7 | WebUI統合 | 100% | ✅ 完了 |
| B-8 | セキュリティ | 95% | 🔄 進行中 |
| B-9 | 品質保証 | 45% | 📋 次のステップ |
| B-10 | 本番デプロイ | 5% | 📋 計画中 |

## 🐛 既知の問題

### Critical: 0件 ✅
すべて修正済み

### High: 2件
1. console.log残留（334件）- ESLintで検出可能
2. innerHTML使用（30箇所）- 段階的に修正中

### Medium: 3件
1. フロントエンドのモジュール化
2. N+1クエリ最適化
3. 2要素認証（オプション）

## 🎯 次のマイルストーン

- **今週**: Phase B-9完了（品質保証・受入テスト）
- **2週間後**: Phase B-10完了（本番デプロイ）
- **3週間後**: 本番稼働開始 🚀

## 🔧 環境情報

- **OS**: Windows 11
- **IP**: 172.23.10.109
- **Port**: 5100
- **サーバー**: ✅ 稼働中

## 📝 重要な注意事項

1. **データファイル**: backend/data/*.json は直接編集しない（APIを使用）
2. **.env ファイル**: 秘密鍵を含むため、Gitにコミットしない
3. **本番環境**: MKS_ENV=production 時はデモユーザー作成をスキップ
4. **テスト実行**: 本番環境では外部通知を無効化

## 🎨 コーディング規約

- **Python**: PEP 8準拠、black + isort推奨
- **JavaScript**: ESLint設定に従う、console.logは本番で削除
- **コミットメッセージ**: 「機能: 」「修正: 」等のプレフィックス使用

---

**このファイルはClaude Codeが自動的に読み込みます。**
**プロジェクト固有の重要な情報を追記してください。**
