# Mirai Knowledge System - データベース設計書

**文書バージョン**: 1.0
**作成日**: 2026-01-02
**最終更新**: 2026-01-02

---

## 1. 概要

### 1.1 データベースシステム
- **DBMS**: PostgreSQL 16.x
- **ORM**: SQLAlchemy 2.0.23
- **マイグレーション**: Alembic 1.13.1
- **フォールバック**: JSON ファイルベース（開発環境用）

### 1.2 スキーマ構成
本システムは3つのスキーマで構成されています。

| スキーマ名 | 用途 | テーブル数 |
|-----------|------|-----------|
| `public` | ナレッジドメイン（主要業務データ） | 8 |
| `auth` | 認証・認可 | 5 |
| `audit` | 監査・ログ | 3 |

---

## 2. ER図（概念）

```
┌─────────────────────────────────────────────────────────────────────┐
│                          PUBLIC SCHEMA                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │  knowledge   │     │     sop      │     │ regulations  │        │
│  │  (ナレッジ)   │     │ (標準手順)   │     │  (法令規格)   │        │
│  └──────┬───────┘     └──────────────┘     └──────────────┘        │
│         │                                                            │
│         │ FK                                                         │
│         ▼                                                            │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │consultations │     │  incidents   │     │  approvals   │        │
│  │ (専門家相談) │     │ (事故報告)   │     │  (承認フロー) │        │
│  └──────────────┘     └──────────────┘     └──────────────┘        │
│                                                                      │
│  ┌──────────────┐     ┌───────────────────┐                         │
│  │notifications │────▶│notification_reads │                         │
│  │   (通知)     │     │   (既読管理)      │                         │
│  └──────────────┘     └───────────────────┘                         │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                           AUTH SCHEMA                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │    users     │     │    roles     │     │ permissions  │        │
│  │  (ユーザー)   │     │   (役割)     │     │   (権限)     │        │
│  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘        │
│         │                    │                    │                 │
│         │  ┌─────────────────┼────────────────────┘                 │
│         │  │                 │                                       │
│         ▼  ▼                 ▼                                       │
│  ┌──────────────┐     ┌───────────────────┐                         │
│  │  user_roles  │     │ role_permissions  │                         │
│  │(ユーザー役割)│     │   (役割権限)      │                         │
│  └──────────────┘     └───────────────────┘                         │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          AUDIT SCHEMA                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     ┌──────────────┐     ┌───────────────────┐   │
│  │ access_logs  │     │ change_logs  │     │ distribution_logs │   │
│  │(アクセスログ)│     │  (変更ログ)  │     │   (配信ログ)      │   │
│  └──────────────┘     └──────────────┘     └───────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. テーブル定義詳細

### 3.1 Public Schema

#### 3.1.1 knowledge（ナレッジ）

建設土木に関するナレッジ情報を管理するマスターテーブル。

| カラム名 | データ型 | NULL許可 | デフォルト | 説明 |
|----------|----------|----------|------------|------|
| id | INTEGER | NO | SERIAL | 主キー |
| title | VARCHAR(500) | NO | - | タイトル |
| summary | TEXT | NO | - | 概要 |
| content | TEXT | YES | - | 本文内容 |
| category | VARCHAR(100) | NO | - | カテゴリ |
| tags | VARCHAR[] | YES | - | タグ配列 |
| status | VARCHAR(50) | YES | 'draft' | ステータス |
| priority | VARCHAR(20) | YES | 'medium' | 優先度 |
| project | VARCHAR(100) | YES | - | プロジェクト名 |
| owner | VARCHAR(200) | NO | - | 所有者 |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 更新日時 |
| created_by_id | INTEGER | YES | - | 作成者ID (FK: auth.users) |
| updated_by_id | INTEGER | YES | - | 更新者ID (FK: auth.users) |

**インデックス**:
- `idx_knowledge_category` (category)
- `idx_knowledge_status` (status)
- `idx_knowledge_updated` (updated_at)
- `idx_knowledge_title` (title)
- `idx_knowledge_owner` (owner)
- `idx_knowledge_project` (project)

---

#### 3.1.2 sop（標準施工手順）

標準作業手順書（SOP）を管理するテーブル。

| カラム名 | データ型 | NULL許可 | デフォルト | 説明 |
|----------|----------|----------|------------|------|
| id | INTEGER | NO | SERIAL | 主キー |
| title | VARCHAR(500) | NO | - | タイトル |
| category | VARCHAR(100) | NO | - | カテゴリ |
| version | VARCHAR(50) | NO | - | バージョン |
| revision_date | DATE | NO | - | 改訂日 |
| target | VARCHAR(200) | YES | - | 対象 |
| tags | VARCHAR[] | YES | - | タグ配列 |
| content | TEXT | NO | - | 内容 |
| status | VARCHAR(50) | YES | 'active' | ステータス |
| supersedes_id | INTEGER | YES | - | 代替元ID (FK: sop) |
| attachments | JSONB | YES | - | 添付ファイル情報 |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 更新日時 |
| created_by_id | INTEGER | YES | - | 作成者ID (FK: auth.users) |
| updated_by_id | INTEGER | YES | - | 更新者ID (FK: auth.users) |

**インデックス**:
- `idx_sop_category` (category)
- `idx_sop_status` (status)
- `idx_sop_title` (title)
- `idx_sop_version` (version)

---

#### 3.1.3 regulations（法令・規格）

法令・規格情報を管理するテーブル。

| カラム名 | データ型 | NULL許可 | デフォルト | 説明 |
|----------|----------|----------|------------|------|
| id | INTEGER | NO | SERIAL | 主キー |
| title | VARCHAR(500) | NO | - | タイトル |
| issuer | VARCHAR(200) | NO | - | 発行元 |
| category | VARCHAR(100) | NO | - | カテゴリ |
| revision_date | DATE | NO | - | 改訂日 |
| applicable_scope | VARCHAR[] | YES | - | 適用範囲 |
| summary | TEXT | NO | - | 概要 |
| content | TEXT | YES | - | 内容 |
| status | VARCHAR(50) | YES | 'active' | ステータス |
| effective_date | DATE | YES | - | 施行日 |
| url | VARCHAR(1000) | YES | - | 参照URL |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 更新日時 |

---

#### 3.1.4 incidents（事故・ヒヤリレポート）

事故・ヒヤリハット報告を管理するテーブル。

| カラム名 | データ型 | NULL許可 | デフォルト | 説明 |
|----------|----------|----------|------------|------|
| id | INTEGER | NO | SERIAL | 主キー |
| title | VARCHAR(500) | NO | - | タイトル |
| description | TEXT | NO | - | 説明 |
| project | VARCHAR(100) | NO | - | プロジェクト名 |
| incident_date | DATE | NO | - | 発生日 |
| severity | VARCHAR(50) | NO | - | 重大度 |
| status | VARCHAR(50) | YES | 'reported' | ステータス |
| corrective_actions | JSONB | YES | - | 是正措置 |
| root_cause | TEXT | YES | - | 根本原因 |
| tags | VARCHAR[] | YES | - | タグ配列 |
| location | VARCHAR(300) | YES | - | 発生場所 |
| involved_parties | VARCHAR[] | YES | - | 関係者 |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 更新日時 |
| reporter_id | INTEGER | YES | - | 報告者ID (FK: auth.users) |

**インデックス**:
- `idx_incident_project` (project)
- `idx_incident_severity` (severity)
- `idx_incident_status` (status)
- `idx_incident_date` (incident_date)

---

#### 3.1.5 consultations（専門家相談）

専門家への相談を管理するテーブル。

| カラム名 | データ型 | NULL許可 | デフォルト | 説明 |
|----------|----------|----------|------------|------|
| id | INTEGER | NO | SERIAL | 主キー |
| title | VARCHAR(500) | NO | - | タイトル |
| question | TEXT | NO | - | 質問内容 |
| category | VARCHAR(100) | NO | - | カテゴリ |
| priority | VARCHAR(20) | YES | 'medium' | 優先度 |
| status | VARCHAR(50) | YES | 'pending' | ステータス |
| requester_id | INTEGER | YES | - | 依頼者ID (FK: auth.users) |
| expert_id | INTEGER | YES | - | 専門家ID (FK: auth.users) |
| answer | TEXT | YES | - | 回答 |
| answered_at | TIMESTAMP | YES | - | 回答日時 |
| knowledge_id | INTEGER | YES | - | 関連ナレッジID (FK: knowledge) |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 更新日時 |

---

#### 3.1.6 approvals（承認フロー）

承認ワークフローを管理するテーブル。

| カラム名 | データ型 | NULL許可 | デフォルト | 説明 |
|----------|----------|----------|------------|------|
| id | INTEGER | NO | SERIAL | 主キー |
| title | VARCHAR(500) | NO | - | タイトル |
| type | VARCHAR(100) | NO | - | 承認タイプ |
| description | TEXT | YES | - | 説明 |
| requester_id | INTEGER | YES | - | 依頼者ID (FK: auth.users) |
| status | VARCHAR(50) | YES | 'pending' | ステータス |
| priority | VARCHAR(20) | YES | 'medium' | 優先度 |
| related_entity_type | VARCHAR(50) | YES | - | 関連エンティティ種別 |
| related_entity_id | INTEGER | YES | - | 関連エンティティID |
| approval_flow | JSONB | YES | - | 承認フロー定義 |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 更新日時 |
| approved_at | TIMESTAMP | YES | - | 承認日時 |
| approver_id | INTEGER | YES | - | 承認者ID (FK: auth.users) |

---

#### 3.1.7 notifications（通知配信）

通知メッセージを管理するテーブル。

| カラム名 | データ型 | NULL許可 | デフォルト | 説明 |
|----------|----------|----------|------------|------|
| id | INTEGER | NO | SERIAL | 主キー |
| title | VARCHAR(500) | NO | - | タイトル |
| message | TEXT | NO | - | メッセージ本文 |
| type | VARCHAR(50) | NO | - | 通知タイプ |
| target_users | INTEGER[] | YES | - | 対象ユーザーID配列 |
| target_roles | VARCHAR[] | YES | - | 対象役割配列 |
| delivery_channels | VARCHAR[] | YES | - | 配信チャネル |
| related_entity_type | VARCHAR(50) | YES | - | 関連エンティティ種別 |
| related_entity_id | INTEGER | YES | - | 関連エンティティID |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |
| sent_at | TIMESTAMP | YES | - | 送信日時 |
| status | VARCHAR(50) | YES | 'pending' | ステータス |

---

#### 3.1.8 notification_reads（通知既読管理）

通知の既読状態を管理する中間テーブル。

| カラム名 | データ型 | NULL許可 | デフォルト | 説明 |
|----------|----------|----------|------------|------|
| id | INTEGER | NO | SERIAL | 主キー |
| notification_id | INTEGER | YES | - | 通知ID (FK: notifications) |
| user_id | INTEGER | YES | - | ユーザーID (FK: auth.users) |
| read_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 既読日時 |

---

### 3.2 Auth Schema

#### 3.2.1 users（ユーザー）

システムユーザーを管理するマスターテーブル。

| カラム名 | データ型 | NULL許可 | デフォルト | 説明 |
|----------|----------|----------|------------|------|
| id | INTEGER | NO | SERIAL | 主キー |
| username | VARCHAR(100) | NO | - | ユーザー名（一意） |
| email | VARCHAR(255) | NO | - | メールアドレス（一意） |
| password_hash | VARCHAR(255) | NO | - | パスワードハッシュ |
| full_name | VARCHAR(200) | YES | - | 氏名 |
| department | VARCHAR(100) | YES | - | 部署 |
| position | VARCHAR(100) | YES | - | 役職 |
| is_active | BOOLEAN | YES | TRUE | 有効フラグ |
| last_login | TIMESTAMP | YES | - | 最終ログイン日時 |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 更新日時 |

**制約**:
- `UNIQUE(username)`
- `UNIQUE(email)`

---

#### 3.2.2 roles（役割）

ユーザー役割を定義するマスターテーブル。

| カラム名 | データ型 | NULL許可 | デフォルト | 説明 |
|----------|----------|----------|------------|------|
| id | INTEGER | NO | SERIAL | 主キー |
| name | VARCHAR(100) | NO | - | 役割名（一意） |
| description | TEXT | YES | - | 説明 |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |

**制約**:
- `UNIQUE(name)`

---

#### 3.2.3 permissions（権限）

システム権限を定義するマスターテーブル。

| カラム名 | データ型 | NULL許可 | デフォルト | 説明 |
|----------|----------|----------|------------|------|
| id | INTEGER | NO | SERIAL | 主キー |
| name | VARCHAR(100) | NO | - | 権限名（一意） |
| resource | VARCHAR(100) | NO | - | リソース名 |
| action | VARCHAR(50) | NO | - | アクション |
| description | TEXT | YES | - | 説明 |

**制約**:
- `UNIQUE(name)`

---

#### 3.2.4 user_roles（ユーザー役割関連）

ユーザーと役割の多対多関連を管理する中間テーブル。

| カラム名 | データ型 | NULL許可 | デフォルト | 説明 |
|----------|----------|----------|------------|------|
| user_id | INTEGER | NO | - | ユーザーID (PK, FK: users) |
| role_id | INTEGER | NO | - | 役割ID (PK, FK: roles) |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |

**制約**:
- `PRIMARY KEY(user_id, role_id)`

---

#### 3.2.5 role_permissions（役割権限関連）

役割と権限の多対多関連を管理する中間テーブル。

| カラム名 | データ型 | NULL許可 | デフォルト | 説明 |
|----------|----------|----------|------------|------|
| role_id | INTEGER | NO | - | 役割ID (PK, FK: roles) |
| permission_id | INTEGER | NO | - | 権限ID (PK, FK: permissions) |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |

**制約**:
- `PRIMARY KEY(role_id, permission_id)`

---

### 3.3 Audit Schema

#### 3.3.1 access_logs（アクセスログ）

APIアクセスログを記録するテーブル。

| カラム名 | データ型 | NULL許可 | デフォルト | 説明 |
|----------|----------|----------|------------|------|
| id | INTEGER | NO | SERIAL | 主キー |
| user_id | INTEGER | YES | - | ユーザーID (FK: auth.users) |
| username | VARCHAR(100) | YES | - | ユーザー名 |
| action | VARCHAR(100) | NO | - | アクション名 |
| resource | VARCHAR(100) | YES | - | リソース名 |
| resource_id | INTEGER | YES | - | リソースID |
| ip_address | INET | YES | - | IPアドレス |
| user_agent | TEXT | YES | - | User-Agent |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |

---

#### 3.3.2 change_logs（変更ログ）

データ変更履歴を記録するテーブル。

| カラム名 | データ型 | NULL許可 | デフォルト | 説明 |
|----------|----------|----------|------------|------|
| id | INTEGER | NO | SERIAL | 主キー |
| user_id | INTEGER | YES | - | ユーザーID (FK: auth.users) |
| username | VARCHAR(100) | YES | - | ユーザー名 |
| table_name | VARCHAR(100) | NO | - | テーブル名 |
| record_id | INTEGER | YES | - | レコードID |
| action | VARCHAR(50) | NO | - | 操作種別（INSERT/UPDATE/DELETE） |
| old_values | JSONB | YES | - | 変更前の値 |
| new_values | JSONB | YES | - | 変更後の値 |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |

---

#### 3.3.3 distribution_logs（配信ログ）

通知配信履歴を記録するテーブル。

| カラム名 | データ型 | NULL許可 | デフォルト | 説明 |
|----------|----------|----------|------------|------|
| id | INTEGER | NO | SERIAL | 主キー |
| notification_id | INTEGER | YES | - | 通知ID (FK: notifications) |
| user_id | INTEGER | YES | - | ユーザーID (FK: auth.users) |
| delivery_channel | VARCHAR(50) | YES | - | 配信チャネル |
| status | VARCHAR(50) | YES | - | 配信ステータス |
| sent_at | TIMESTAMP | YES | - | 送信日時 |
| read_at | TIMESTAMP | YES | - | 既読日時 |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |

---

## 4. コネクションプール設定

| パラメータ | デフォルト値 | 環境変数 | 説明 |
|-----------|-------------|----------|------|
| pool_size | 10 | MKS_DB_POOL_SIZE | プール内の接続数 |
| max_overflow | 20 | MKS_DB_MAX_OVERFLOW | 追加接続の最大数 |
| pool_timeout | 30 | MKS_DB_POOL_TIMEOUT | 接続取得タイムアウト（秒） |
| pool_recycle | 3600 | MKS_DB_POOL_RECYCLE | 接続再利用間隔（秒） |
| pool_pre_ping | True | - | 接続健全性チェック |

---

## 5. マイグレーション

### 5.1 Alembic設定

マイグレーションファイルは `backend/migrations/versions/` に格納されています。

```bash
# マイグレーション作成
cd backend
alembic revision --autogenerate -m "説明"

# マイグレーション実行
alembic upgrade head

# ロールバック
alembic downgrade -1
```

---

## 6. バックアップ・リストア

### 6.1 バックアップ

```bash
# フルバックアップ
pg_dump -h localhost -U postgres -d mirai_knowledge_db > backup_$(date +%Y%m%d).sql

# スキーマ別バックアップ
pg_dump -h localhost -U postgres -d mirai_knowledge_db -n public > backup_public.sql
pg_dump -h localhost -U postgres -d mirai_knowledge_db -n auth > backup_auth.sql
pg_dump -h localhost -U postgres -d mirai_knowledge_db -n audit > backup_audit.sql
```

### 6.2 リストア

```bash
# リストア
psql -h localhost -U postgres -d mirai_knowledge_db < backup_YYYYMMDD.sql
```

---

## 7. セキュリティ考慮事項

1. **パスワード保護**: `password_hash` はWerkzeugの `generate_password_hash` を使用
2. **接続暗号化**: 本番環境ではSSL/TLS接続を推奨
3. **権限分離**: RBAC (Role-Based Access Control) による権限管理
4. **監査ログ**: すべてのアクセス・変更を `audit` スキーマに記録

---

## 8. パフォーマンス最適化

### 8.1 インデックス戦略

- 頻繁に検索されるカラムにB-treeインデックスを設定
- タグ配列には GIN インデックスを検討（将来対応）
- 複合インデックスは使用頻度の高いクエリパターンに基づいて設計

### 8.2 JSONB活用

- `corrective_actions`, `approval_flow`, `attachments` など
- 柔軟なスキーマレス格納が可能
- JSONBインデックスで高速検索可能

---

## 9. 付録

### 9.1 ステータス値一覧

**ナレッジ (knowledge.status)**:
- `draft`: 下書き
- `pending_review`: レビュー待ち
- `published`: 公開済み
- `archived`: アーカイブ

**SOP (sop.status)**:
- `active`: 有効
- `obsolete`: 廃止
- `draft`: 下書き

**事故報告 (incidents.status)**:
- `reported`: 報告済み
- `investigating`: 調査中
- `resolved`: 解決済み
- `closed`: クローズ

**承認 (approvals.status)**:
- `pending`: 承認待ち
- `approved`: 承認済み
- `rejected`: 却下
- `cancelled`: キャンセル

---

**文書管理情報**
- 作成者: Claude Code (自動生成)
- レビュー担当: システム管理者
