# Mirai Knowledge Systems - リポジトリ構成

**最終更新**: 2026-01-08  
**バージョン**: 1.0.0

## ディレクトリ構造

```
Mirai-Knowledge-Systems/
├── backend/                    # バックエンド（Flask API）
│   ├── app_v2.py              # メインアプリケーション（2,400行）
│   ├── models.py              # SQLAlchemyモデル（11テーブル）
│   ├── schemas.py             # バリデーションスキーマ
│   ├── database.py            # DB接続管理
│   ├── password_policy.py     # パスワードポリシー
│   ├── csrf_protection.py     # CSRF対策
│   ├── data/                  # データファイル
│   │   ├── knowledge.json     # ナレッジデータ
│   │   ├── sop.json           # SOP
│   │   ├── incidents.json     # 事故レポート
│   │   └── users.json         # ユーザー
│   ├── scripts/               # 運用スクリプト
│   │   ├── create_production_users.py
│   │   ├── import_data.py
│   │   ├── backup.sh
│   │   └── ...
│   ├── tests/                 # テストスイート
│   │   ├── unit/              # ユニットテスト
│   │   ├── integration/       # 統合テスト
│   │   ├── e2e/               # E2Eテスト
│   │   └── load/              # 負荷テスト
│   ├── monitoring/            # 監視設定
│   │   ├── prometheus/
│   │   ├── grafana/
│   │   └── docker-compose.yml
│   └── logs/                  # ログファイル
│
├── webui/                     # フロントエンド（Vanilla JS）
│   ├── index.html             # ダッシュボード
│   ├── login.html             # ログイン画面
│   ├── admin.html             # 管理画面
│   ├── search-detail.html     # ナレッジ詳細
│   ├── sop-detail.html        # SOP詳細
│   ├── incident-detail.html   # 事故レポート詳細
│   ├── app.js                 # メインロジック（2,450行）
│   ├── detail-pages.js        # 詳細ページ（3,100行）
│   ├── auth-guard.js          # 認証ガード
│   └── styles.css             # スタイルシート
│
├── docs/                      # ドキュメント
│   ├── 00_リポジトリ構成/     # 本ファイル
│   ├── 01_概要/               # プロジェクト概要
│   ├── 11_運用保守/           # 運用ガイド
│   └── 13_開発計画/           # 開発計画
│
├── monitoring/                # 監視（ルートレベル）
│   ├── prometheus.yml
│   ├── grafana-dashboard.json
│   └── alert_rules.yml
│
├── .claude/                   # Claude Code設定
│   └── CLAUDE.md              # プロジェクトコンテキスト
│
├── .env                       # 環境変数（Git管理外）
├── .gitignore
├── README.md                  # プロジェクトREADME
└── requirements.txt           # Python依存パッケージ
```

## 主要ファイル説明

### バックエンド

| ファイル | 行数 | 説明 |
|---------|------|------|
| app_v2.py | 2,400 | Flask APIメイン（27エンドポイント） |
| models.py | 320 | SQLAlchemyモデル定義 |
| schemas.py | 250 | Marshmallowバリデーション |

### フロントエンド

| ファイル | 行数 | 説明 |
|---------|------|------|
| app.js | 2,450 | メインロジック、API呼び出し |
| detail-pages.js | 3,100 | 詳細ページ、URL遷移 |
| styles.css | 2,800 | スタイルシート |

### テスト

| ディレクトリ | テスト数 | カバレッジ |
|-------------|---------|-----------|
| unit/ | 40+ | - |
| integration/ | 130+ | - |
| e2e/ | 20+ | - |
| **合計** | **502** | **91%** |

## データフロー

```
ユーザー → Nginx (443) → Flask (5100) → PostgreSQL (5432)
                ↓                ↓
          access.log      audit.access_logs
```

---

**このドキュメントはリポジトリ構成の概要を提供します。**
