# 建設土木ナレッジシステム

建設土木会社向けの統合ナレッジ管理システム。現場の知見、SOP、法令、事故レポート、専門家相談を一元管理します。

## 🎯 主な機能

### ナレッジ管理
- 施工計画、品質、安全、原価、出来形の知見を統合
- 種別別の登録・更新・閲覧
- タグ付与、関連付け、改訂履歴管理

### 検索・推薦
- 条件検索（工種/工区/発注者/更新日）
- 関連ナレッジの自動提示
- 全文検索対応

### 承認・配信フロー
- 多段承認フロー
- 配信先制御と配信履歴保存
- ステータス可視化

### 事故・ヒヤリレポート
- 事案登録、原因分析、再発防止策
- 重要アラート提示
- 現場への横展開

### 専門家相談
- 相談起案、専門家アサイン
- Q&A管理と回答配信
- ナレッジベース化

### 監査・レポート
- 参照/変更ログ記録
- 進捗・稼働ダッシュボード
- KPI可視化

## 📁 プロジェクト構造

```
Mirai-Knowledge-Systems/
├── README.md                    # このファイル
├── docs/                        # ドキュメント（要件定義、設計書など）
│   ├── setup/                   # セットアップガイド
│   │   ├── SETUP.md            # 基本セットアップガイド
│   │   ├── QUICK_START.md      # クイックスタート
│   │   └── SYSTEMD_SETUP.md    # systemd設定ガイド
│   ├── deployment/             # デプロイメント関連
│   │   ├── PRODUCTION_DEPLOYMENT.md
│   │   ├── DATABASE_DESIGN_COMPLETE.md
│   │   └── DATA_MIGRATION_GUIDE.md
│   ├── 01_概要(Overview)/
│   ├── 02_要件定義(Requirements)/
│   ├── 03_機能設計(Functional-Design)/
│   ├── 05_アーキテクチャ(Architecture)/
│   └── ... (その他のドキュメント)
├── backend/                     # バックエンド（Flask API）
│   ├── app.py                   # メインアプリケーション
│   ├── requirements.txt         # Python依存パッケージ
│   └── data/                    # JSONデータストレージ
│       ├── knowledge.json       # ナレッジデータ
│       ├── sop.json            # SOP（標準施工手順）
│       ├── regulations.json    # 法令・規格
│       ├── incidents.json      # 事故・ヒヤリレポート
│       ├── consultations.json  # 専門家相談
│       └── approvals.json      # 承認フロー
└── webui/                       # フロントエンド（静的HTML/CSS/JS）
    ├── index.html              # ダッシュボード
    ├── search-detail.html      # 検索結果詳細
    ├── sop-detail.html         # SOP詳細
    ├── law-detail.html         # 法令詳細
    ├── incident-detail.html    # 事故レポート詳細
    ├── expert-consult.html     # 専門家相談
    ├── styles.css              # スタイルシート
    └── app.js                  # JavaScriptロジック
```

## 🚀 クイックスタート

### 前提条件
- Python 3.8以上
- pip（Pythonパッケージマネージャー）
- Node.js 18以上（フロントエンド開発時）
- npm または yarn（フロントエンド開発時）
- モダンブラウザ（Chrome, Firefox, Edge等）

### インストール手順

1. **リポジトリのクローン**（既にダウンロード済みの場合はスキップ）
   ```bash
   cd Mirai-Knowledge-Systems
   ```

2. **Pythonパッケージのインストール**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **環境変数の設定（重要）**

   セキュリティのため、JWT秘密鍵の設定が必須です:

   ```bash
   # .envファイルを作成
   cp .env.example .env

   # JWT秘密鍵を生成して設定
   python3 -c "import secrets; print('MKS_JWT_SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env
   ```

   または、手動で `.env` ファイルを編集:
   ```bash
   # backend/.env
   MKS_JWT_SECRET_KEY=your-secure-random-jwt-secret-key-minimum-32-characters
   MKS_ENV=development
   ```

4. **サーバー起動（JWT認証対応版）**

   **開発/テスト用（手動起動）:**
   ```bash
   python app_v2.py
   ```

   **開発/テスト用（スクリプト起動）:**
   ```bash
   ./start_backend.sh
   ```

   **本番環境用（systemd自動起動）:**

   Linux環境では、systemdサービスとして登録することで、サーバー再起動時に自動起動できます：
   ```bash
   # 自動セットアップスクリプトを実行
   ./setup-systemd.sh
   ```

    詳細は [SYSTEMD_SETUP.md](docs/setup/SYSTEMD_SETUP.md) を参照してください。

   > 注: `app.py` は旧版（認証なし）、`app_v2.py` は新版（JWT認証 + RBAC対応）です。

5. **デモユーザー自動作成**
   
   サーバー起動時に以下のデモアカウントが自動作成されます:
   
   | ユーザー名 | パ スワード | 役割 | 権限 |
   |-----------|----------|------|------|
   | admin | admin123 | 管理者 | 全権限 |
   | yamada | yamada123 | 施工管理 | ナレッジ作成・閲覧、事故レポート作成 |
   | partner | partner123 | 協力会社 | 閲覧のみ |

6. **ログインしてアクセス**

   ブラウザで以下のURLを開きます：
   ```
   http://localhost:5100/login.html
   ```

   デモアカウントのいずれかでログイン後、ダッシュボードへ自動リダイレクトされます。

### デフォルトポート
- バックエンドAPI: `http://localhost:5100`
- ログイン画面: `http://localhost:5100/login.html`
- ダッシュボード: `http://localhost:5100/index.html`（認証要）
- フロントエンド開発サーバー: `http://localhost:5173`（Vite）

> **注**: ポート5100で起動します。ネットワーク経由でアクセスする場合は、サーバーのIPアドレスを使用してください（例: `http://<server-ip>:5100`）

### フロントエンド開発モード

フロントエンドの開発時は、Vite開発サーバーを使用することで高速なホットリロードが可能です。

```bash
# フロントエンド開発サーバー起動
npm install
npm run dev
# http://localhost:5173 でアクセス
```

Vite開発サーバーは自動的にバックエンドAPI（localhost:5200）へプロキシします。

### 本番ビルド

フロントエンドのコードをバンドル・最適化してビルドします。

```bash
# 本番ビルド実行
npm run build
# dist/ ディレクトリに出力

# ビルド結果のプレビュー
npm run preview
# http://localhost:4173 でアクセス
```

## 📊 API エンドポイント

### 認証 🆕
- `POST /api/v1/auth/login` - ログイン（トークン発行）
- `POST /api/v1/auth/refresh` - トークンリフレッシュ
- `GET /api/v1/auth/me` - 現在のユーザー情報取得

> **注**: 認証API以外のすべてのエンドポイントはJWT認証が必要です。  
> リクエストヘッダーに `Authorization: Bearer <access_token>` を含めてください。

### ナレッジ管理
- `GET /api/v1/knowledge` - ナレッジ一覧取得
- `GET /api/v1/knowledge/<id>` - ナレッジ詳細取得
- `POST /api/v1/knowledge` - 新規ナレッジ登録
- `PUT /api/v1/knowledge/<id>` - ナレッジ更新

### SOP管理
- `GET /api/v1/sop` - SOP一覧取得
- `GET /api/v1/sop/<id>` - SOP詳細取得

### 法令管理
- `GET /api/v1/regulations` - 法令一覧取得
- `GET /api/v1/regulations/<id>` - 法令詳細取得

### 事故レポート
- `GET /api/v1/incidents` - 事故レポート一覧取得
- `GET /api/v1/incidents/<id>` - 事故レポート詳細取得
- `POST /api/v1/incidents` - 新規事故レポート登録

### 専門家相談
- `GET /api/v1/consultations` - 専門家相談一覧取得
- `GET /api/v1/consultations/<id>` - 専門家相談詳細取得
- `POST /api/v1/consultations` - 新規相談登録

### 承認フロー
- `GET /api/v1/approvals` - 承認フロー一覧取得
- `POST /api/v1/approvals/<id>/approve` - 承認実行
- `POST /api/v1/approvals/<id>/reject` - 承認却下

### ダッシュボード
- `GET /api/v1/dashboard/stats` - ダッシュボード統計情報取得

## 🎨 UI/UXデザイン

### デザインコンセプト
- **和モダン**: 建設現場の信頼感と日本的な落ち着きを両立
- **情報密度**: 現場で必要な情報を一覧性高く表示
- **視認性**: 屋外や照度の低い環境でも見やすい配色

### カラーパレット
- **メインカラー**: Moss Green（現場の安全・自然）
- **アクセント**: Terracotta Orange（注意喚起・重要情報）
- **背景**: Warm Beige（目に優しい、長時間作業に適した色）

## 📈 開発の進捗状況
進捗の正本: `docs/13_開発計画(Development-Plan)/00_全体開発計画(Overall-Development-Plan).md`

### プロトタイプ開発環境
- ✅ フェーズ1: スコープ・課題定義
- ✅ フェーズ2: 情報設計・ナビゲーション設計
- ✅ フェーズ3: ワイヤーフレーム作成
- ✅ フェーズ4: ビジュアル設計・コンポーネント定義
- ✅ フェーズ5: 静的WebUI実装
- ✅ フェーズ6: 主要インタラクション実装
- ✅ フェーズ7: シナリオ検証・レビュー評価
- ✅ フェーズ8: 改善反映・本番移行要件整理

### 本番環境
- ✅ フェーズB-1: 本番要件確定
- ✅ フェーズB-2: アーキテクチャ設計確定
- ✅ フェーズB-3: データ設計確定
- ✅ フェーズB-4: API設計確定
- ✅ フェーズB-5: バックエンド基盤実装
- 🔄 フェーズB-6: 検索・通知機能実装（進行中 - 60%）
- 🔄 フェーズB-7: WebUI統合実装（進行中 - 70%）
- 🔄 フェーズB-8: セキュリティ/権限/監査強化（着手）
- 🔄 フェーズB-9: 品質保証・受入テスト（着手）
- ⬜ フェーズB-10: 展開準備・運用引継ぎ

## 🎯 KPI目標

- ナレッジ再利用率: **70%以上**
- 事故ゼロ継続日数の維持
- 承認フローのリードタイム: **30%短縮**
- 重大ナレッジの現場周知: **48時間以内**

## 🔒 セキュリティ

### 実装済み ✅

**認証・認可**
- JWT認証（Flask-JWT-Extended）
- 役割ベースアクセス制御（RBAC）
- パスワードハッシュ化（bcrypt）
- 監査ログ記録（全アクセスを自動記録）
- トークン期限切れ検知（1時間）
- 権限別API制御

**セキュリティ強化（Phase B-8）**
- **JWT秘密鍵の環境変数必須化**（デフォルト値削除）
- **本番環境でのHTTPS強制デフォルト有効化**
- **XSS対策強化**（innerHTML使用箇所の削除、DOM API使用）
- セキュリティヘッダー追加（CSP、X-Frame-Options、HSTS等）
- レート制限（本番環境のみ有効）
- Secure/HttpOnly Cookie設定
- トークンリフレッシュ機能

### 今後の強化
- CSRF対策の追加強化
- API入力値のさらなるバリデーション強化
- セキュリティ監査ログの詳細化

## 📝 ライセンス

公開利用条件は別途定義します（外部公開向けに内容整理済み）。

## 👥 想定利用部門

- 施工管理（主利用者）
- 品質保証室
- 安全衛生室
- 技術本部
- 本社管理部門
- 協力会社（閲覧中心）

## 📞 サポート

詳細な仕様については `docs/` と `backend/docs/` のドキュメントを参照してください。
構成一覧は `docs/00_リポジトリ構成(Repository-Structure).md` にまとめています。

## 📚 ドキュメント案内

- 全体構成: `docs/00_リポジトリ構成(Repository-Structure).md`
- 運用スクリプト: `docs/11_運用保守(Operations)/11_運用スクリプト一覧(Operations-Scripts).md`
- 本番移行: `docs/deployment/PRODUCTION_DEPLOYMENT.md`

## 変更履歴

| 日付 | バージョン | 変更内容 | 担当 |
| --- | --- | --- | --- |
| 2025-12-26 | 2.0 | JWT認証・ログイン機能実装、Phase B-6 & B-7 一部完了 | System |
| 2025-12-26 | 1.0 | 初版作成、バックエンドAPI実装 | System |
