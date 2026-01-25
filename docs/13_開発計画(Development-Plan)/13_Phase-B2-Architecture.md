# Phase B-2: アーキテクチャ設計確定

## 目的
本番運用に耐えるシステム構成を確定し、拡張性・可用性・保守性を担保する

## システム全体構成

### レイヤー構成

```
┌─────────────────────────────────────────────────────────┐
│                    クライアント層                          │
│  - Webブラウザ（Chrome/Firefox/Edge）                    │
│  - モバイルブラウザ（将来対応）                           │
└─────────────────────────────────────────────────────────┘
                          │ HTTPS
┌─────────────────────────────────────────────────────────┐
│                    プレゼンテーション層                    │
│  - Nginx（リバースプロキシ）                              │
│  - 静的ファイル配信（HTML/CSS/JS）                        │
│  - TLS終端                                               │
│  - アクセスログ                                           │
└─────────────────────────────────────────────────────────┘
                          │ HTTP
┌─────────────────────────────────────────────────────────┐
│                    アプリケーション層                      │
│  - Flask API Server（Gunicorn）                         │
│  - 認証・認可（JWT + RBAC）                              │
│  - ビジネスロジック                                       │
│  - バリデーション                                         │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼───────┐ ┌───────▼───────┐ ┌──────▼───────┐
│  データ層      │ │   検索層      │ │  キャッシュ層 │
│               │ │               │ │              │
│ PostgreSQL    │ │ Meilisearch   │ │    Redis     │
│ - ナレッジDB  │ │ - 全文検索    │ │ - セッション │
│ - ユーザーDB  │ │ - タグ検索    │ │ - API結果    │
│ - 監査ログDB  │ │               │ │              │
└───────────────┘ └───────────────┘ └──────────────┘
```

## コンポーネント詳細

### 1. Webサーバー層（Nginx）

**役割**
- リバースプロキシ
- 静的ファイル配信
- TLS終端
- ロードバランシング（将来的）

**設定方針**
```nginx
server {
    listen 443 ssl http2;
    server_name knowledge.construction-company.local;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # 静的ファイル
    location / {
        root /var/www/webui;
        try_files $uri $uri/ /index.html;
    }
    
    # API
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # セキュリティヘッダー
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
}
```

### 2. アプリケーションサーバー層（Flask + Gunicorn）

**構成**
```
Master Process (Gunicorn)
  ├─ Worker 1 (Flask App)
  ├─ Worker 2 (Flask App)
  ├─ Worker 3 (Flask App)
  └─ Worker 4 (Flask App)
```

**プロセス管理**
- プロセス管理: systemd
- ワーカー数: CPU数 × 2 + 1
- タイムアウト: 30秒
- 再起動: Graceful reload

**gunicorn設定**
```python
# gunicorn.conf.py
bind = '127.0.0.1:5000'
workers = 5
worker_class = 'sync'
timeout = 30
keepalive = 2
accesslog = '/var/log/gunicorn/access.log'
errorlog = '/var/log/gunicorn/error.log'
loglevel = 'info'
```

### 3. データベース層（PostgreSQL）

**データベース構成**
```
mirai_knowledge_db
  ├─ schema: public
  │   ├─ knowledge (ナレッジ)
  │   ├─ sop (標準施工手順)
  │   ├─ regulations (法令・規格)
  │   ├─ incidents (事故レポート)
  │   ├─ consultations (専門家相談)
  │   ├─ approvals (承認フロー)
  │   └─ notifications (通知配信)
  ├─ schema: auth
  │   ├─ users (ユーザー)
  │   ├─ roles (役割)
  │   ├─ permissions (権限)
  │   └─ user_roles (ユーザー役割関連)
  └─ schema: audit
      ├─ access_logs (アクセスログ)
      ├─ change_logs (変更ログ)
      └─ distribution_logs (配信ログ)
```

**バックアップ戦略**
- フルバックアップ: 毎日1回（深夜3:00）
- 差分バックアップ: 6時間ごと
- WALアーカイブ: 継続的（RPO 24時間対応）
- 保管期間: 30日間

### 4. 検索層（Meilisearch）

**インデックス設計**
```
knowledge_index
  - id, title, summary, content
  - category, tags[], project
  - searchableAttributes: [title, summary, content, tags]
  - filterableAttributes: [category, project, status]
  - sortableAttributes: [updated_at, priority]
```

**パフォーマンス目標**
- インデックス更新: 5秒以内
- 検索応答: 100ms以内
- 同時検索: 100req/s

### 5. キャッシュ層（Redis）

**用途**
- セッション管理
- API応答キャッシュ
- レート制限（API制限）
- リアルタイム統計の一時保存

**キャッシュ戦略**
- セッション TTL: 24時間
- API結果 TTL: 5分
- 統計データ TTL: 1時間

## 非機能要件への対応

### パフォーマンス

| 要件 | 対策 |
|-----|-----|
| 主要画面3秒以内 | - 静的ファイルのCDN配信<br>- Gzip圧縮<br>- ブラウザキャッシュ |
| 検索2秒以内 | - Meilisearch導入<br>- インデックス最適化<br>- Redisキャッシュ |
| 同時300名 | - Gunicornマルチワーカー<br>- コネクションプール<br>- ロードバランサー（将来）|

### 可用性

| 要件 | 対策 |
|-----|-----|
| 稼働率99.5% | - ヘルスチェック<br>- 自動再起動<br>- 監視アラート |
| RTO 4時間 | - 自動バックアップ<br>- リストア手順書<br>- DR訓練 |
| RPO 24時間 | - WALアーカイブ<br>- レプリケーション（将来）|

### セキュリティ

| 要件 | 対策 |
|-----|-----|
| 通信暗号化 | - TLS 1.3<br>- HSTS有効化 |
| 認証 | - JWT + Refresh Token<br>- パスワードハッシュ（bcrypt）|
| 認可 | - RBAC実装<br>- エンドポイント単位の権限チェック |
| 入力検証 | - SQLインジェクション対策<br>- XSS対策<br>- CSRF対策 |

### 監査

| 要件 | 対策 |
|-----|-----|
| アクセスログ7年 | - PostgreSQL audit schema<br>- ログローテーション<br>- 圧縮保管 |
| 配信履歴5年 | - 配信ログテーブル<br>- 既読追跡 |
| 変更履歴 | - 全テーブルに updated_at, updated_by<br>- 変更差分記録 |

## デプロイ構成

### 開発環境
```
開発PC
  └─ Docker Compose
      ├─ Flask (開発サーバー)
      ├─ PostgreSQL
      ├─ Meilisearch
      └─ Redis
```

### 本番環境
```
オンプレミスサーバー
  ├─ Nginx (Port 443)
  ├─ Gunicorn + Flask (Port 5000)
  ├─ PostgreSQL (Port 5432)
  ├─ Meilisearch (Port 7700)
  └─ Redis (Port 6379)
```

**サーバースペック（推奨）**
- CPU: 4コア以上
- メモリ: 16GB以上
- ディスク: SSD 500GB以上
- OS: Ubuntu 22.04 LTS / CentOS Stream 9

## 監視・運用

### 監視項目

**システムリソース**
- CPU使用率
- メモリ使用率
- ディスク使用率
- ネットワークトラフィック

**アプリケーション**
- API応答時間
- エラー率
- リクエスト数
- アクティブユーザー数

**データベース**
- クエリ実行時間
- コネクション数
- デッドロック検出
- レプリケーション遅延（将来）

### ログ管理

**ログ種別**
```
/var/log/mirai-knowledge/
  ├─ nginx/
  │   ├─ access.log
  │   └─ error.log
  ├─ gunicorn/
  │   ├─ access.log
  │   └─ error.log
  ├─ flask/
  │   ├─ app.log
  │   └─ debug.log
  ├─ postgresql/
  │   └─ postgresql.log
  └─ audit/
      ├─ access_audit.log
      └─ change_audit.log
```

**ログローテーション**
- 日次ローテーション
- 圧縮保管（gzip）
- 保管期間: 90日

## 技術スタック確定

| レイヤー | 技術 | バージョン | 理由 |
|---------|-----|-----------|-----|
| Webサーバー | Nginx | 1.24+ | 高性能、安定性 |
| アプリケーション | Flask | 3.0+ | 軽量、柔軟性 |
| WSGIサーバー | Gunicorn | 21.2+ | 本番運用実績 |
| データベース | PostgreSQL | 15+ | 信頼性、JSON対応 |
| 検索エンジン | Meilisearch | 1.5+ | 高速、日本語対応 |
| キャッシュ | Redis | 7.2+ | 高速、汎用性 |
| ORM | SQLAlchemy | 2.0+ | 成熟、移行容易 |
| マイグレーション | Alembic | 1.13+ | SQLAlchemyと連携 |
| 認証 | Flask-JWT-Extended | 4.5+ | JWT標準対応 |
| バリデーション | Marshmallow | 3.20+ | スキーマ定義 |

## 拡張性の考慮

### 水平スケーリング（将来対応）
```
                      Load Balancer
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    App Server 1     App Server 2     App Server 3
          │                │                │
          └────────────────┼────────────────┘
                           │
                    PostgreSQL
                    (Master-Slave)
```

### マイクロサービス化（将来検討）
- 検索サービスの分離
- 通知サービスの分離
- ファイルストレージサービスの分離

## レビュー評価

| 観点 | 評価 | コメント |
|-----|-----|---------|
| 完成度 | 5/5 | 必要なコンポーネントを全て定義 |
| 一貫性 | 5/5 | レイヤー構成が明確で整合性あり |
| 実現性 | 5/5 | 実績ある技術スタックで実現可能 |
| リスク | 4/5 | バックアップ・監視計画が明確 |
| 受入準備 | 5/5 | 非機能要件への対応が具体的 |

**合計**: 24/25点 ✅ 合格

## Next Actions

1. **開発環境構築** (Phase B-3開始前)
   - Docker Compose設定ファイル作成
   - 開発用データベース初期化スクリプト

2. **本番環境準備** (Phase B-10)
   - サーバー調達・セットアップ
   - ネットワーク設定
   - SSL証明書取得

3. **移行計画策定** (Phase B-3)
   - JSONからPostgreSQLへの移行スクリプト
   - データ検証手順

## 変更履歴

| 日付 | バージョン | 変更内容 | 担当 |
| --- | --- | --- | --- |
| 2025-12-26 | 1.0 | 初版作成 | System |
