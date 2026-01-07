# データベース構造設計書

## 更新日: 2026-01-07
## バージョン: 1.0
## データベース: PostgreSQL 16.11

---

## 1. 概要

Mirai Knowledge Systemsのデータベースは、建設土木業界向けナレッジ管理に最適化された3スキーマ構成を採用しています。

### 1.1 スキーマ構成

| スキーマ名 | 用途 | テーブル数 |
|-----------|------|-----------|
| `auth` | 認証・認可 | 5 |
| `public` | ナレッジドメイン | 8 |
| `audit` | 監査ログ | 3 |

---

## 2. 論理データモデル（ER図）

```
                              ┌─────────────────────────┐
                              │       auth.users        │
                              │─────────────────────────│
                              │ PK id                   │
                              │    username             │
                              │    email                │
                              │    password_hash        │
                              │    full_name            │
                              │    department           │
                              │    is_active            │
                              └───────────┬─────────────┘
                                          │
          ┌───────────────────────────────┼───────────────────────────────┐
          │                               │                               │
          ▼                               ▼                               ▼
┌─────────────────────┐       ┌─────────────────────┐       ┌─────────────────────┐
│   auth.user_roles   │       │  public.knowledge   │       │  audit.access_logs  │
│─────────────────────│       │─────────────────────│       │─────────────────────│
│ FK user_id          │       │ PK id               │       │ PK id               │
│ FK role_id          │       │    title            │       │ FK user_id          │
└─────────┬───────────┘       │    summary          │       │    action           │
          │                   │    category         │       │    resource         │
          ▼                   │    status           │       │    ip_address       │
┌─────────────────────┐       │    owner            │       │    created_at       │
│     auth.roles      │       │ FK created_by_id    │       └─────────────────────┘
│─────────────────────│       └───────────┬─────────┘
│ PK id               │                   │
│    name             │                   │
│    description      │   ┌───────────────┴───────────────┐
└─────────┬───────────┘   │                               │
          │               ▼                               ▼
          ▼       ┌─────────────────────┐       ┌─────────────────────┐
┌─────────────────│ public.approvals    │       │public.notifications │
│ auth.role_      │─────────────────────│       │─────────────────────│
│ permissions     │ PK id               │       │ PK id               │
│─────────────────│    type             │       │    title            │
│ FK role_id      │    status           │       │    message          │
│ FK permission_id│ FK requester_id     │       │    target_users[]   │
└─────────┬───────│ FK approver_id      │       │    status           │
          │       └─────────────────────┘       └───────────┬─────────┘
          ▼                                                 │
┌─────────────────────┐                                     ▼
│  auth.permissions   │                       ┌─────────────────────────┐
│─────────────────────│                       │public.notification_reads│
│ PK id               │                       │─────────────────────────│
│    name             │                       │ PK id                   │
│    resource         │                       │ FK notification_id      │
│    action           │                       │ FK user_id              │
└─────────────────────┘                       │    read_at              │
                                              └─────────────────────────┘

        ┌─────────────────────────────────────────────────────────────┐
        │                    ナレッジドメイン                          │
        └─────────────────────────────────────────────────────────────┘

┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│     public.sop      │   │ public.regulations  │   │  public.incidents   │
│─────────────────────│   │─────────────────────│   │─────────────────────│
│ PK id               │   │ PK id               │   │ PK id               │
│    title            │   │    title            │   │    title            │
│    category         │   │    issuer           │   │    description      │
│    version          │   │    category         │   │    project          │
│    revision_date    │   │    revision_date    │   │    severity         │
│    content          │   │    summary          │   │    status           │
│    status           │   │    status           │   │    corrective_actions│
│ FK supersedes_id    │   │    effective_date   │   │ FK reporter_id      │
│ FK created_by_id    │   │    url              │   └─────────────────────┘
└─────────────────────┘   └─────────────────────┘

┌─────────────────────┐
│public.consultations │
│─────────────────────│
│ PK id               │
│    title            │
│    question         │
│    category         │
│    status           │
│ FK requester_id     │
│ FK expert_id        │
│    answer           │
│ FK knowledge_id     │
└─────────────────────┘
```

---

## 3. 物理データモデル（テーブル定義書）

### 3.1 auth スキーマ

#### auth.users（ユーザー情報）

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|----------|----------|------|-----------|------|
| id | SERIAL | NO | AUTO | 主キー |
| username | VARCHAR(100) | NO | - | ユーザー名（一意） |
| email | VARCHAR(255) | NO | - | メールアドレス（一意） |
| password_hash | VARCHAR(255) | NO | - | パスワードハッシュ |
| full_name | VARCHAR(200) | YES | NULL | 氏名 |
| department | VARCHAR(100) | YES | NULL | 部署 |
| position | VARCHAR(100) | YES | NULL | 役職 |
| is_active | BOOLEAN | YES | TRUE | アクティブフラグ |
| last_login | TIMESTAMP | YES | NULL | 最終ログイン日時 |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 更新日時 |

#### auth.roles（役割定義）

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|----------|----------|------|-----------|------|
| id | SERIAL | NO | AUTO | 主キー |
| name | VARCHAR(100) | NO | - | 役割名（一意） |
| description | TEXT | YES | NULL | 説明 |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |

**初期データ**: admin, editor, viewer, expert

#### auth.permissions（権限定義）

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|----------|----------|------|-----------|------|
| id | SERIAL | NO | AUTO | 主キー |
| name | VARCHAR(100) | NO | - | 権限名（一意） |
| resource | VARCHAR(100) | NO | - | 対象リソース |
| action | VARCHAR(50) | NO | - | アクション種別 |
| description | TEXT | YES | NULL | 説明 |

**初期データ**: knowledge_read, knowledge_write, knowledge_delete, sop_read, sop_write, user_manage, admin

#### auth.user_roles（ユーザー役割関連）

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|----------|----------|------|-----------|------|
| user_id | INTEGER | NO | - | FK→auth.users |
| role_id | INTEGER | NO | - | FK→auth.roles |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |

**主キー**: (user_id, role_id)

#### auth.role_permissions（役割権限関連）

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|----------|----------|------|-----------|------|
| role_id | INTEGER | NO | - | FK→auth.roles |
| permission_id | INTEGER | NO | - | FK→auth.permissions |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |

**主キー**: (role_id, permission_id)

---

### 3.2 public スキーマ

#### public.knowledge（ナレッジ記事）

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|----------|----------|------|-----------|------|
| id | SERIAL | NO | AUTO | 主キー |
| title | VARCHAR(500) | NO | - | タイトル |
| summary | TEXT | NO | - | 要約 |
| content | TEXT | YES | NULL | 本文 |
| category | VARCHAR(100) | NO | - | カテゴリ |
| tags | TEXT[] | YES | NULL | タグ配列 |
| status | VARCHAR(50) | YES | 'draft' | ステータス |
| priority | VARCHAR(20) | YES | 'medium' | 優先度 |
| project | VARCHAR(100) | YES | NULL | プロジェクト |
| owner | VARCHAR(200) | NO | - | 所有者 |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 更新日時 |
| created_by_id | INTEGER | YES | NULL | FK→auth.users |
| updated_by_id | INTEGER | YES | NULL | FK→auth.users |

**インデックス**: category, status, updated_at, title, owner, project, tags(GIN)

#### public.sop（標準施工手順）

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|----------|----------|------|-----------|------|
| id | SERIAL | NO | AUTO | 主キー |
| title | VARCHAR(500) | NO | - | タイトル |
| category | VARCHAR(100) | NO | - | カテゴリ |
| version | VARCHAR(50) | NO | - | バージョン |
| revision_date | DATE | NO | - | 改訂日 |
| target | VARCHAR(200) | YES | NULL | 対象 |
| tags | TEXT[] | YES | NULL | タグ配列 |
| content | TEXT | NO | - | 内容 |
| status | VARCHAR(50) | YES | 'active' | ステータス |
| supersedes_id | INTEGER | YES | NULL | FK→public.sop（旧版） |
| attachments | JSONB | YES | NULL | 添付ファイル |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 更新日時 |
| created_by_id | INTEGER | YES | NULL | FK→auth.users |
| updated_by_id | INTEGER | YES | NULL | FK→auth.users |

**インデックス**: category, status, title, version, tags(GIN)

#### public.regulations（法令・規格）

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|----------|----------|------|-----------|------|
| id | SERIAL | NO | AUTO | 主キー |
| title | VARCHAR(500) | NO | - | タイトル |
| issuer | VARCHAR(200) | NO | - | 発行元 |
| category | VARCHAR(100) | NO | - | カテゴリ |
| revision_date | DATE | NO | - | 改訂日 |
| applicable_scope | TEXT[] | YES | NULL | 適用範囲 |
| summary | TEXT | NO | - | 要約 |
| content | TEXT | YES | NULL | 内容 |
| status | VARCHAR(50) | YES | 'active' | ステータス |
| effective_date | DATE | YES | NULL | 施行日 |
| url | VARCHAR(1000) | YES | NULL | 参照URL |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 更新日時 |

**インデックス**: category, issuer

#### public.incidents（事故・ヒヤリレポート）

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|----------|----------|------|-----------|------|
| id | SERIAL | NO | AUTO | 主キー |
| title | VARCHAR(500) | NO | - | タイトル |
| description | TEXT | NO | - | 詳細 |
| project | VARCHAR(100) | NO | - | プロジェクト |
| incident_date | DATE | NO | - | 発生日 |
| severity | VARCHAR(50) | NO | - | 重大度 |
| status | VARCHAR(50) | YES | 'reported' | ステータス |
| corrective_actions | JSONB | YES | NULL | 是正措置 |
| root_cause | TEXT | YES | NULL | 根本原因 |
| tags | TEXT[] | YES | NULL | タグ配列 |
| location | VARCHAR(300) | YES | NULL | 発生場所 |
| involved_parties | TEXT[] | YES | NULL | 関係者 |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 更新日時 |
| reporter_id | INTEGER | YES | NULL | FK→auth.users |

**インデックス**: project, severity, status, incident_date

#### public.consultations（専門家相談）

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|----------|----------|------|-----------|------|
| id | SERIAL | NO | AUTO | 主キー |
| title | VARCHAR(500) | NO | - | タイトル |
| question | TEXT | NO | - | 質問内容 |
| category | VARCHAR(100) | NO | - | カテゴリ |
| priority | VARCHAR(20) | YES | 'medium' | 優先度 |
| status | VARCHAR(50) | YES | 'pending' | ステータス |
| requester_id | INTEGER | YES | NULL | FK→auth.users |
| expert_id | INTEGER | YES | NULL | FK→auth.users |
| answer | TEXT | YES | NULL | 回答 |
| answered_at | TIMESTAMP | YES | NULL | 回答日時 |
| knowledge_id | INTEGER | YES | NULL | FK→public.knowledge |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 更新日時 |

**インデックス**: status, category

#### public.approvals（承認フロー）

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|----------|----------|------|-----------|------|
| id | SERIAL | NO | AUTO | 主キー |
| title | VARCHAR(500) | NO | - | タイトル |
| type | VARCHAR(100) | NO | - | 承認種別 |
| description | TEXT | YES | NULL | 説明 |
| requester_id | INTEGER | YES | NULL | FK→auth.users |
| status | VARCHAR(50) | YES | 'pending' | ステータス |
| priority | VARCHAR(20) | YES | 'medium' | 優先度 |
| related_entity_type | VARCHAR(50) | YES | NULL | 関連エンティティ種別 |
| related_entity_id | INTEGER | YES | NULL | 関連エンティティID |
| approval_flow | JSONB | YES | NULL | 承認フロー定義 |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 更新日時 |
| approved_at | TIMESTAMP | YES | NULL | 承認日時 |
| approver_id | INTEGER | YES | NULL | FK→auth.users |

**インデックス**: status, type

#### public.notifications（通知配信）

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|----------|----------|------|-----------|------|
| id | SERIAL | NO | AUTO | 主キー |
| title | VARCHAR(500) | NO | - | タイトル |
| message | TEXT | NO | - | メッセージ |
| type | VARCHAR(50) | NO | - | 通知種別 |
| target_users | INTEGER[] | YES | NULL | 対象ユーザーID配列 |
| target_roles | TEXT[] | YES | NULL | 対象役割配列 |
| delivery_channels | TEXT[] | YES | NULL | 配信チャンネル |
| related_entity_type | VARCHAR(50) | YES | NULL | 関連エンティティ種別 |
| related_entity_id | INTEGER | YES | NULL | 関連エンティティID |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |
| sent_at | TIMESTAMP | YES | NULL | 送信日時 |
| status | VARCHAR(50) | YES | 'pending' | ステータス |

**インデックス**: status, type

#### public.notification_reads（通知既読管理）

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|----------|----------|------|-----------|------|
| id | SERIAL | NO | AUTO | 主キー |
| notification_id | INTEGER | NO | - | FK→public.notifications |
| user_id | INTEGER | NO | - | FK→auth.users |
| read_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 既読日時 |

**インデックス**: user_id

---

### 3.3 audit スキーマ

#### audit.access_logs（アクセスログ）

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|----------|----------|------|-----------|------|
| id | SERIAL | NO | AUTO | 主キー |
| user_id | INTEGER | YES | NULL | FK→auth.users |
| username | VARCHAR(100) | YES | NULL | ユーザー名 |
| action | VARCHAR(100) | NO | - | アクション |
| resource | VARCHAR(100) | YES | NULL | リソース |
| resource_id | INTEGER | YES | NULL | リソースID |
| ip_address | INET | YES | NULL | IPアドレス |
| user_agent | TEXT | YES | NULL | ユーザーエージェント |
| request_method | VARCHAR(10) | YES | NULL | HTTPメソッド |
| request_path | VARCHAR(500) | YES | NULL | リクエストパス |
| session_id | VARCHAR(100) | YES | NULL | セッションID |
| status | VARCHAR(50) | YES | 'success' | ステータス |
| details | JSONB | YES | NULL | 詳細情報 |
| changes | JSONB | YES | NULL | 変更内容 |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |

**インデックス**: user_id, action, created_at, status

#### audit.change_logs（変更ログ）

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|----------|----------|------|-----------|------|
| id | SERIAL | NO | AUTO | 主キー |
| user_id | INTEGER | YES | NULL | FK→auth.users |
| username | VARCHAR(100) | YES | NULL | ユーザー名 |
| table_name | VARCHAR(100) | NO | - | テーブル名 |
| record_id | INTEGER | YES | NULL | レコードID |
| action | VARCHAR(50) | NO | - | アクション |
| old_values | JSONB | YES | NULL | 変更前値 |
| new_values | JSONB | YES | NULL | 変更後値 |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |

**インデックス**: table_name, action, created_at

#### audit.distribution_logs（通知配信ログ）

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|----------|----------|------|-----------|------|
| id | SERIAL | NO | AUTO | 主キー |
| notification_id | INTEGER | YES | NULL | FK→public.notifications |
| user_id | INTEGER | YES | NULL | FK→auth.users |
| delivery_channel | VARCHAR(50) | YES | NULL | 配信チャンネル |
| status | VARCHAR(50) | YES | NULL | ステータス |
| sent_at | TIMESTAMP | YES | NULL | 送信日時 |
| read_at | TIMESTAMP | YES | NULL | 既読日時 |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | 作成日時 |

**インデックス**: notification_id, status

---

## 4. インデックス設計

### 4.1 GINインデックス（配列・全文検索用）

| テーブル | カラム | 用途 |
|----------|--------|------|
| public.knowledge | tags | タグ検索 |
| public.sop | tags | タグ検索 |

### 4.2 拡張機能

| 拡張機能 | 用途 |
|----------|------|
| pg_trgm | 日本語あいまい検索（トライグラム） |
| uuid-ossp | UUID生成 |

---

## 5. データ辞書

### 5.1 ステータス値

| テーブル | カラム | 値 | 説明 |
|----------|--------|-----|------|
| knowledge | status | draft | 下書き |
| knowledge | status | published | 公開 |
| knowledge | status | archived | アーカイブ |
| sop | status | active | 有効 |
| sop | status | deprecated | 非推奨 |
| incidents | status | reported | 報告済み |
| incidents | status | investigating | 調査中 |
| incidents | status | resolved | 解決済み |
| consultations | status | pending | 未回答 |
| consultations | status | answered | 回答済み |
| approvals | status | pending | 承認待ち |
| approvals | status | approved | 承認済み |
| approvals | status | rejected | 却下 |

### 5.2 優先度値

| 値 | 説明 |
|----|------|
| low | 低 |
| medium | 中 |
| high | 高 |
| critical | 緊急 |

### 5.3 重大度値（incidents）

| 値 | 説明 |
|----|------|
| minor | 軽微 |
| moderate | 中程度 |
| major | 重大 |
| critical | 致命的 |

---

## 6. バックアップ・リストア

### 6.1 バックアップコマンド

```bash
# 全データベースバックアップ
pg_dump -h localhost -U postgres -d mirai_knowledge_db -F c -f backup_$(date +%Y%m%d).dump

# スキーマのみ
pg_dump -h localhost -U postgres -d mirai_knowledge_db -s -f schema_$(date +%Y%m%d).sql
```

### 6.2 リストアコマンド

```bash
# リストア
pg_restore -h localhost -U postgres -d mirai_knowledge_db -c backup_YYYYMMDD.dump
```

---

## 変更履歴

| 日付 | バージョン | 変更内容 | 担当 |
|------|-----------|----------|------|
| 2026-01-07 | 1.0 | 初版作成（PostgreSQL移行完了に伴う） | Claude Code |
