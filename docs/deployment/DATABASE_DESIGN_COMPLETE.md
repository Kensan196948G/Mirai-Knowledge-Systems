# PostgreSQLデータベース構造設計書（完全版）

**プロジェクト**: Mirai Knowledge Systems
**バージョン**: 2.0
**データベース**: PostgreSQL 16.11
**最終更新**: 2026-01-08
**対象フェーズ**: Phase C（本番運用）

---

## 目次

1. [概要](#1-概要)
2. [エンティティ一覧](#2-エンティティ一覧)
3. [論理データモデル](#3-論理データモデル)
4. [物理データモデル](#4-物理データモデル)
5. [インデックス戦略](#5-インデックス戦略)
6. [制約とリレーション](#6-制約とリレーション)
7. [マイグレーション戦略](#7-マイグレーション戦略)
8. [パフォーマンス最適化](#8-パフォーマンス最適化)
9. [運用ガイドライン](#9-運用ガイドライン)

---

## 1. 概要

### 1.1 設計思想

Mirai Knowledge Systemsのデータベースは、**建設土木業界の知識集約型ワークフロー**を支援するために設計されています。主要な設計原則は以下の通りです。

- **スキーマ分離**: ドメイン、認証、監査を明確に分離
- **拡張性**: PostgreSQLの配列型(ARRAY)、JSONB型を活用した柔軟なデータ構造
- **監査対応**: すべての変更を追跡可能な監査ログ
- **パフォーマンス**: 検索頻度の高いカラムへの戦略的インデックス配置
- **RBAC**: ロールベースアクセス制御による細粒度な権限管理

### 1.2 スキーマ構成

| スキーマ名 | 役割 | テーブル数 | 用途 |
|-----------|------|-----------|------|
| **auth** | 認証・認可 | 5 | ユーザー、ロール、権限の管理 |
| **public** | ナレッジドメイン | 8 | 業務データ（ナレッジ、SOP、事故等） |
| **audit** | 監査ログ | 3 | アクセス、変更、配信の追跡 |

合計: **16テーブル**

### 1.3 技術仕様

- **RDBMS**: PostgreSQL 16.11
- **ORM**: SQLAlchemy 2.0.45
- **文字コード**: UTF-8（日本語対応）
- **タイムゾーン**: UTC（アプリケーション層でJSTに変換）
- **マイグレーション**: Alembic（未導入 - Phase C推奨）

---

## 2. エンティティ一覧

### 2.1 全16テーブル概要

#### auth スキーマ（認証・認可）

| # | テーブル名 | エンティティ名 | 責務 | レコード想定数 |
|---|-----------|--------------|------|--------------|
| 1 | auth.users | User | ユーザー情報管理 | 100-500 |
| 2 | auth.roles | Role | 役割定義 | 4-10 |
| 3 | auth.permissions | Permission | 権限定義 | 20-50 |
| 4 | auth.user_roles | UserRole | ユーザー-役割マッピング（N:M） | 100-1,000 |
| 5 | auth.role_permissions | RolePermission | 役割-権限マッピング（N:M） | 50-200 |

#### public スキーマ（ナレッジドメイン）

| # | テーブル名 | エンティティ名 | 責務 | レコード想定数 |
|---|-----------|--------------|------|--------------|
| 6 | public.knowledge | Knowledge | ナレッジ記事 | 1,000-10,000 |
| 7 | public.sop | SOP | 標準施工手順 | 100-500 |
| 8 | public.regulations | Regulation | 法令・規格 | 50-200 |
| 9 | public.incidents | Incident | 事故・ヒヤリレポート | 500-5,000 |
| 10 | public.consultations | Consultation | 専門家相談 | 200-2,000 |
| 11 | public.approvals | Approval | 承認フロー | 500-5,000 |
| 12 | public.notifications | Notification | 通知配信 | 10,000-100,000 |
| 13 | public.notification_reads | NotificationRead | 通知既読管理 | 50,000-500,000 |

#### audit スキーマ（監査ログ）

| # | テーブル名 | エンティティ名 | 責務 | レコード想定数 |
|---|-----------|--------------|------|--------------|
| 14 | audit.access_logs | AccessLog | アクセスログ | 100,000-1,000,000 |
| 15 | audit.change_logs | ChangeLog | データ変更ログ | 50,000-500,000 |
| 16 | audit.distribution_logs | DistributionLog | 通知配信ログ | 50,000-500,000 |

### 2.2 各エンティティの詳細

#### 2.2.1 Knowledge（ナレッジ記事）

**目的**: 建設現場で蓄積された知識を構造化して保存

**主要属性**:
- タイトル、要約、本文（Markdown対応）
- カテゴリ、タグ（配列型）
- ステータス（draft/published/archived）
- プロジェクト紐付け
- 作成者・更新者追跡

**ビジネスルール**:
- 所有者(owner)は削除できない
- 公開(published)後は履歴保持が必須
- タグは最大10個まで推奨

#### 2.2.2 SOP（標準施工手順）

**目的**: バージョン管理された施工手順の保存

**主要属性**:
- バージョン番号（セマンティックバージョニング推奨）
- 改訂日（revision_date）
- 旧版参照（supersedes_id）
- 添付ファイルメタデータ（JSONB）

**ビジネスルール**:
- 新版作成時は旧版を非推奨(deprecated)に更新
- 有効なSOPは常に1バージョンのみ
- 削除は論理削除のみ

#### 2.2.3 Incident（事故・ヒヤリレポート）

**目的**: 建設現場の安全管理

**主要属性**:
- 重大度（minor/moderate/major/critical）
- 是正措置（JSONB配列）
- 根本原因分析（root_cause）
- 関係者情報

**ビジネスルール**:
- 重大度が「critical」の場合は即時通知
- 30日以内に是正措置必須
- 解決済み(resolved)後も編集不可

---

## 3. 論理データモデル

### 3.1 ER図（全体像）

```
┌────────────────────────────────────────────────────────────────────┐
│                      AUTH スキーマ（認証・認可）                     │
└────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────┐
                    │    auth.users        │
                    │──────────────────────│
                    │ PK  id               │
                    │ UQ  username         │
                    │ UQ  email            │
                    │     password_hash    │
                    │     full_name        │
                    │     department       │
                    │     position         │
                    │     is_active        │
                    │     last_login       │
                    │     created_at       │
                    │     updated_at       │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐
    │ auth.user_roles │  │public.knowledge │  │audit.access_logs │
    │─────────────────│  │─────────────────│  │──────────────────│
    │ PK FK user_id   │  │ PK id           │  │ PK id            │
    │ PK FK role_id   │  │    title        │  │ FK user_id       │
    │     created_at  │  │    summary      │  │    action        │
    └────────┬────────┘  │    content      │  │    resource      │
             │           │    category     │  │    ip_address    │
             ▼           │    tags[]       │  │    created_at    │
    ┌─────────────────┐  │    status       │  └──────────────────┘
    │   auth.roles    │  │    priority     │
    │─────────────────│  │    project      │
    │ PK id           │  │    owner        │
    │ UQ name         │  │ FK created_by_id│
    │    description  │  │ FK updated_by_id│
    │    created_at   │  │    created_at   │
    └────────┬────────┘  │    updated_at   │
             │           └─────────────────┘
             ▼
    ┌──────────────────────┐
    │ auth.role_permissions│
    │──────────────────────│
    │ PK FK role_id        │
    │ PK FK permission_id  │
    │     created_at       │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │  auth.permissions    │
    │──────────────────────│
    │ PK id                │
    │ UQ name              │
    │    resource          │
    │    action            │
    │    description       │
    └──────────────────────┘
```

### 3.2 ナレッジドメインのリレーション

```
┌────────────────────────────────────────────────────────────────────┐
│                   PUBLIC スキーマ（ナレッジドメイン）                 │
└────────────────────────────────────────────────────────────────────┘

  ┌──────────────────┐         ┌──────────────────┐
  │public.knowledge  │         │   public.sop     │
  │──────────────────│         │──────────────────│
  │ PK id            │         │ PK id            │
  │    title         │         │    title         │
  │    summary       │         │    category      │
  │    category      │         │    version       │
  │    tags[]        │    ┌────│ FK supersedes_id │
  │    status        │    │    │    content       │
  │ FK created_by_id │    │    │    status        │
  └──────┬───────────┘    │    │ FK created_by_id │
         │                │    └──────────────────┘
         │                │     (self-reference)
         │                │
         ▼                ▼
  ┌───────────────────────────┐    ┌──────────────────┐
  │ public.consultations      │    │public.regulations│
  │───────────────────────────│    │──────────────────│
  │ PK id                     │    │ PK id            │
  │    title                  │    │    title         │
  │    question               │    │    issuer        │
  │    answer                 │    │    category      │
  │ FK requester_id (users)   │    │    summary       │
  │ FK expert_id (users)      │    │    status        │
  │ FK knowledge_id ──────────┘    │    url           │
  │    status                      │    effective_date│
  │    answered_at                 └──────────────────┘
  └───────────────────────────┘

  ┌──────────────────┐         ┌──────────────────────┐
  │public.incidents  │         │  public.approvals    │
  │──────────────────│         │──────────────────────│
  │ PK id            │         │ PK id                │
  │    title         │         │    title             │
  │    description   │         │    type              │
  │    project       │         │    status            │
  │    severity      │         │    priority          │
  │    status        │         │    related_entity_id │
  │    corrective_   │         │ FK requester_id      │
  │    actions (JSON)│         │ FK approver_id       │
  │ FK reporter_id   │         │    approval_flow     │
  └──────────────────┘         │    approved_at       │
                               └──────────────────────┘

  ┌────────────────────┐       ┌──────────────────────────┐
  │public.notifications│       │public.notification_reads │
  │────────────────────│       │──────────────────────────│
  │ PK id              │◄──────│ PK id                    │
  │    title           │       │ FK notification_id       │
  │    message         │       │ FK user_id               │
  │    type            │       │    read_at               │
  │    target_users[]  │       └──────────────────────────┘
  │    target_roles[]  │
  │    status          │
  │    sent_at         │
  └────────────────────┘
```

### 3.3 監査スキーマのリレーション

```
┌────────────────────────────────────────────────────────────────────┐
│                     AUDIT スキーマ（監査ログ）                       │
└────────────────────────────────────────────────────────────────────┘

  ┌────────────────────┐       ┌──────────────────────┐
  │audit.access_logs   │       │  audit.change_logs   │
  │────────────────────│       │──────────────────────│
  │ PK id              │       │ PK id                │
  │ FK user_id         │       │ FK user_id           │
  │    username        │       │    username          │
  │    action          │       │    table_name        │
  │    resource        │       │    record_id         │
  │    resource_id     │       │    action            │
  │    ip_address      │       │    old_values (JSONB)│
  │    user_agent      │       │    new_values (JSONB)│
  │    created_at      │       │    created_at        │
  └────────────────────┘       └──────────────────────┘

  ┌──────────────────────────┐
  │audit.distribution_logs   │
  │──────────────────────────│
  │ PK id                    │
  │ FK notification_id       │
  │ FK user_id               │
  │    delivery_channel      │
  │    status                │
  │    sent_at               │
  │    read_at               │
  │    created_at            │
  └──────────────────────────┘
```

### 3.4 カーディナリティマトリクス

| 親エンティティ | 子エンティティ | 関係性 | カーディナリティ | 外部キー |
|-------------|--------------|--------|----------------|---------|
| User | Knowledge | 作成 | 1:N | knowledge.created_by_id |
| User | Knowledge | 更新 | 1:N | knowledge.updated_by_id |
| User | Incident | 報告 | 1:N | incidents.reporter_id |
| User | Consultation | 質問 | 1:N | consultations.requester_id |
| User | Consultation | 回答 | 1:N | consultations.expert_id |
| User | Approval | 申請 | 1:N | approvals.requester_id |
| User | Approval | 承認 | 1:N | approvals.approver_id |
| User | Role | 割当 | N:M | user_roles (中間テーブル) |
| Role | Permission | 付与 | N:M | role_permissions (中間テーブル) |
| Knowledge | Consultation | 参照 | 1:N | consultations.knowledge_id |
| SOP | SOP | 版管理 | 1:1 (self) | sop.supersedes_id |
| Notification | NotificationRead | 既読 | 1:N | notification_reads.notification_id |
| Notification | DistributionLog | 配信 | 1:N | distribution_logs.notification_id |

---

## 4. 物理データモデル

### 4.1 auth.users（ユーザー情報）

```sql
CREATE TABLE auth.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(200),
    department VARCHAR(100),
    position VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX idx_users_username ON auth.users(username);
CREATE INDEX idx_users_email ON auth.users(email);
CREATE INDEX idx_users_is_active ON auth.users(is_active);
```

**カラム詳細**:

| カラム名 | データ型 | 制約 | デフォルト | 説明 |
|---------|---------|-----|-----------|------|
| id | SERIAL | PK, NOT NULL | AUTO | 主キー（自動採番） |
| username | VARCHAR(100) | NOT NULL, UNIQUE | - | ログインID（英数字、ハイフン、アンダースコア） |
| email | VARCHAR(255) | NOT NULL, UNIQUE | - | メールアドレス（RFC 5322準拠） |
| password_hash | VARCHAR(255) | NOT NULL | - | bcryptハッシュ（コスト=12） |
| full_name | VARCHAR(200) | NULL | NULL | フルネーム（姓名） |
| department | VARCHAR(100) | NULL | NULL | 所属部署 |
| position | VARCHAR(100) | NULL | NULL | 役職 |
| is_active | BOOLEAN | NULL | TRUE | アクティブフラグ（論理削除用） |
| last_login | TIMESTAMP | NULL | NULL | 最終ログイン日時（UTC） |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 作成日時（UTC） |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 更新日時（UTC） |

**セキュリティ要件**:
- パスワードハッシュはbcryptで12ラウンド
- emailは小文字に正規化してから保存
- is_activeがFALSEの場合はログイン不可

---

### 4.2 auth.roles（役割定義）

```sql
CREATE TABLE auth.roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 初期データ
INSERT INTO auth.roles (name, description) VALUES
    ('admin', 'システム管理者'),
    ('editor', '編集者'),
    ('viewer', '閲覧者'),
    ('expert', '専門家（相談対応）');
```

**カラム詳細**:

| カラム名 | データ型 | 制約 | デフォルト | 説明 |
|---------|---------|-----|-----------|------|
| id | SERIAL | PK, NOT NULL | AUTO | 主キー |
| name | VARCHAR(100) | NOT NULL, UNIQUE | - | 役割名（英小文字、アンダースコア） |
| description | TEXT | NULL | NULL | 説明（日本語可） |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 作成日時 |

**初期役割の権限マトリクス**:

| 役割 | 閲覧 | 作成 | 編集 | 削除 | 承認 | ユーザー管理 |
|-----|-----|-----|-----|-----|-----|------------|
| admin | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| editor | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| viewer | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| expert | ✓ | ✓ | ✓ | ✗ | ✓ (相談のみ) | ✗ |

---

### 4.3 auth.permissions（権限定義）

```sql
CREATE TABLE auth.permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT
);

-- インデックス
CREATE INDEX idx_permissions_resource ON auth.permissions(resource);

-- 初期データ例
INSERT INTO auth.permissions (name, resource, action, description) VALUES
    ('knowledge_read', 'knowledge', 'read', 'ナレッジ閲覧'),
    ('knowledge_write', 'knowledge', 'write', 'ナレッジ作成・編集'),
    ('knowledge_delete', 'knowledge', 'delete', 'ナレッジ削除'),
    ('sop_read', 'sop', 'read', 'SOP閲覧'),
    ('sop_write', 'sop', 'write', 'SOP作成・編集'),
    ('user_manage', 'user', 'manage', 'ユーザー管理'),
    ('admin', '*', '*', '全権限');
```

**カラム詳細**:

| カラム名 | データ型 | 制約 | デフォルト | 説明 |
|---------|---------|-----|-----------|------|
| id | SERIAL | PK, NOT NULL | AUTO | 主キー |
| name | VARCHAR(100) | NOT NULL, UNIQUE | - | 権限名（resource_action形式） |
| resource | VARCHAR(100) | NOT NULL | - | 対象リソース（knowledge, sop, user等） |
| action | VARCHAR(50) | NOT NULL | - | アクション（read, write, delete, manage） |
| description | TEXT | NULL | NULL | 説明 |

---

### 4.4 public.knowledge（ナレッジ記事）

```sql
CREATE TABLE public.knowledge (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    summary TEXT NOT NULL,
    content TEXT,
    category VARCHAR(100) NOT NULL,
    tags TEXT[],
    status VARCHAR(50) DEFAULT 'draft',
    priority VARCHAR(20) DEFAULT 'medium',
    project VARCHAR(100),
    owner VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES auth.users(id),
    updated_by_id INTEGER REFERENCES auth.users(id),

    CONSTRAINT chk_knowledge_status CHECK (status IN ('draft', 'published', 'archived')),
    CONSTRAINT chk_knowledge_priority CHECK (priority IN ('low', 'medium', 'high', 'critical'))
);

-- インデックス（6個）
CREATE INDEX idx_knowledge_category ON public.knowledge(category);
CREATE INDEX idx_knowledge_status ON public.knowledge(status);
CREATE INDEX idx_knowledge_updated_at ON public.knowledge(updated_at);
CREATE INDEX idx_knowledge_title ON public.knowledge(title);
CREATE INDEX idx_knowledge_owner ON public.knowledge(owner);
CREATE INDEX idx_knowledge_project ON public.knowledge(project);
CREATE INDEX idx_knowledge_tags ON public.knowledge USING GIN(tags);

-- 全文検索用（オプション）
CREATE INDEX idx_knowledge_fulltext ON public.knowledge
    USING GIN(to_tsvector('japanese', title || ' ' || summary || ' ' || COALESCE(content, '')));
```

**カラム詳細**:

| カラム名 | データ型 | 制約 | デフォルト | 説明 |
|---------|---------|-----|-----------|------|
| id | SERIAL | PK, NOT NULL | AUTO | 主キー |
| title | VARCHAR(500) | NOT NULL | - | タイトル（最大500文字） |
| summary | TEXT | NOT NULL | - | 要約（必須、検索対象） |
| content | TEXT | NULL | NULL | 本文（Markdown形式） |
| category | VARCHAR(100) | NOT NULL | - | カテゴリ（技術/安全/品質等） |
| tags | TEXT[] | NULL | NULL | タグ配列（最大10個推奨） |
| status | VARCHAR(50) | CHECK | 'draft' | ステータス（draft/published/archived） |
| priority | VARCHAR(20) | CHECK | 'medium' | 優先度（low/medium/high/critical） |
| project | VARCHAR(100) | NULL | NULL | プロジェクトコード |
| owner | VARCHAR(200) | NOT NULL | - | 所有者名 |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 更新日時 |
| created_by_id | INTEGER | FK | NULL | 作成者（auth.users） |
| updated_by_id | INTEGER | FK | NULL | 更新者（auth.users） |

**ビジネスロジック**:
- `status='published'` の場合、change_logsに変更履歴必須
- `tags`配列は重複を許可しない（アプリケーション層で制御）
- `content`はMarkdown形式でHTML変換はフロントエンド側で実施

---

### 4.5 public.sop（標準施工手順）

```sql
CREATE TABLE public.sop (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    category VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    revision_date DATE NOT NULL,
    target VARCHAR(200),
    tags TEXT[],
    content TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    supersedes_id INTEGER REFERENCES public.sop(id),
    attachments JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES auth.users(id),
    updated_by_id INTEGER REFERENCES auth.users(id),

    CONSTRAINT chk_sop_status CHECK (status IN ('active', 'deprecated', 'draft')),
    CONSTRAINT chk_sop_version_format CHECK (version ~ '^[0-9]+\.[0-9]+\.[0-9]+$')
);

-- インデックス（4個）
CREATE INDEX idx_sop_category ON public.sop(category);
CREATE INDEX idx_sop_status ON public.sop(status);
CREATE INDEX idx_sop_title ON public.sop(title);
CREATE INDEX idx_sop_version ON public.sop(version);
CREATE INDEX idx_sop_tags ON public.sop USING GIN(tags);
```

**カラム詳細**:

| カラム名 | データ型 | 制約 | デフォルト | 説明 |
|---------|---------|-----|-----------|------|
| id | SERIAL | PK, NOT NULL | AUTO | 主キー |
| title | VARCHAR(500) | NOT NULL | - | タイトル |
| category | VARCHAR(100) | NOT NULL | - | カテゴリ |
| version | VARCHAR(50) | NOT NULL, CHECK | - | バージョン（SemVer: 1.0.0形式） |
| revision_date | DATE | NOT NULL | - | 改訂日 |
| target | VARCHAR(200) | NULL | NULL | 対象工種・作業 |
| tags | TEXT[] | NULL | NULL | タグ配列 |
| content | TEXT | NOT NULL | - | 手順内容 |
| status | VARCHAR(50) | CHECK | 'active' | ステータス（active/deprecated/draft） |
| supersedes_id | INTEGER | FK | NULL | 旧版SOP ID（自己参照） |
| attachments | JSONB | NULL | NULL | 添付ファイルメタデータ |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 更新日時 |
| created_by_id | INTEGER | FK | NULL | 作成者 |
| updated_by_id | INTEGER | FK | NULL | 更新者 |

**attachments JSONB構造例**:
```json
[
  {
    "filename": "procedure_diagram.pdf",
    "size": 2048576,
    "mime_type": "application/pdf",
    "uploaded_at": "2026-01-08T10:30:00Z",
    "url": "https://storage.example.com/sop/123/diagram.pdf"
  }
]
```

---

### 4.6 public.incidents（事故・ヒヤリレポート）

```sql
CREATE TABLE public.incidents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    project VARCHAR(100) NOT NULL,
    incident_date DATE NOT NULL,
    severity VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'reported',
    corrective_actions JSONB,
    root_cause TEXT,
    tags TEXT[],
    location VARCHAR(300),
    involved_parties TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reporter_id INTEGER REFERENCES auth.users(id),

    CONSTRAINT chk_incident_severity CHECK (severity IN ('minor', 'moderate', 'major', 'critical')),
    CONSTRAINT chk_incident_status CHECK (status IN ('reported', 'investigating', 'resolved', 'closed'))
);

-- インデックス（4個）
CREATE INDEX idx_incident_project ON public.incidents(project);
CREATE INDEX idx_incident_severity ON public.incidents(severity);
CREATE INDEX idx_incident_status ON public.incidents(status);
CREATE INDEX idx_incident_date ON public.incidents(incident_date);
```

**corrective_actions JSONB構造例**:
```json
[
  {
    "action": "作業手順書の改訂",
    "responsible": "安全管理部",
    "deadline": "2026-02-01",
    "status": "completed",
    "completed_at": "2026-01-25"
  },
  {
    "action": "全作業員への安全教育",
    "responsible": "現場監督",
    "deadline": "2026-01-31",
    "status": "in_progress"
  }
]
```

---

### 4.7 audit.access_logs（アクセスログ）

```sql
CREATE TABLE audit.access_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth.users(id),
    username VARCHAR(100),
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100),
    resource_id INTEGER,
    ip_address INET,
    user_agent TEXT,
    request_method VARCHAR(10),
    request_path VARCHAR(500),
    session_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'success',
    details JSONB,
    changes JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_access_log_status CHECK (status IN ('success', 'failed', 'blocked'))
);

-- インデックス（4個）
CREATE INDEX idx_access_log_user_id ON audit.access_logs(user_id);
CREATE INDEX idx_access_log_action ON audit.access_logs(action);
CREATE INDEX idx_access_log_created_at ON audit.access_logs(created_at);
CREATE INDEX idx_access_log_status ON audit.access_logs(status);

-- パーティショニング（月次、オプション）
-- Phase Cで検討推奨
```

**カラム詳細**:

| カラム名 | データ型 | 制約 | デフォルト | 説明 |
|---------|---------|-----|-----------|------|
| id | SERIAL | PK, NOT NULL | AUTO | 主キー |
| user_id | INTEGER | FK | NULL | ユーザーID（未認証時はNULL） |
| username | VARCHAR(100) | NULL | NULL | ユーザー名（非正規化） |
| action | VARCHAR(100) | NOT NULL | - | アクション（login, view, create等） |
| resource | VARCHAR(100) | NULL | NULL | 操作対象（knowledge, sop等） |
| resource_id | INTEGER | NULL | NULL | 操作対象ID |
| ip_address | INET | NULL | NULL | IPアドレス（IPv4/IPv6対応） |
| user_agent | TEXT | NULL | NULL | ユーザーエージェント |
| request_method | VARCHAR(10) | NULL | NULL | HTTPメソッド（GET, POST等） |
| request_path | VARCHAR(500) | NULL | NULL | リクエストパス |
| session_id | VARCHAR(100) | NULL | NULL | セッションID |
| status | VARCHAR(50) | CHECK | 'success' | 結果（success/failed/blocked） |
| details | JSONB | NULL | NULL | 詳細情報 |
| changes | JSONB | NULL | NULL | 変更内容（before/after） |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | ログ記録日時 |

**保存期間**:
- 通常ログ: 1年間
- セキュリティイベント（status='blocked'）: 3年間
- 定期アーカイブをcronで実施

---

## 5. インデックス戦略

### 5.1 インデックス総数

**合計: 54個のインデックス**

| インデックス種別 | 個数 | 用途 |
|---------------|-----|------|
| PRIMARY KEY | 16 | 主キー（自動作成） |
| UNIQUE | 6 | 一意制約（username, email, name等） |
| B-tree | 40 | 範囲検索、ソート |
| GIN | 8 | 配列検索、全文検索 |

### 5.2 スキーマ別インデックス配置

#### auth スキーマ（12個）

| テーブル | インデックス名 | 種別 | カラム | 用途 |
|---------|--------------|-----|--------|------|
| users | users_pkey | PRIMARY | id | 主キー |
| users | users_username_key | UNIQUE | username | ログイン検索 |
| users | users_email_key | UNIQUE | email | メール検索 |
| users | idx_users_is_active | B-tree | is_active | アクティブユーザー抽出 |
| roles | roles_pkey | PRIMARY | id | 主キー |
| roles | roles_name_key | UNIQUE | name | 役割名検索 |
| permissions | permissions_pkey | PRIMARY | id | 主キー |
| permissions | permissions_name_key | UNIQUE | name | 権限名検索 |
| permissions | idx_permissions_resource | B-tree | resource | リソース別権限 |
| user_roles | user_roles_pkey | PRIMARY | (user_id, role_id) | 複合主キー |
| role_permissions | role_permissions_pkey | PRIMARY | (role_id, permission_id) | 複合主キー |

#### public スキーマ（30個）

| テーブル | インデックス名 | 種別 | カラム | 用途 |
|---------|--------------|-----|--------|------|
| knowledge | knowledge_pkey | PRIMARY | id | 主キー |
| knowledge | idx_knowledge_category | B-tree | category | カテゴリ検索 |
| knowledge | idx_knowledge_status | B-tree | status | ステータス検索 |
| knowledge | idx_knowledge_updated_at | B-tree | updated_at | 更新日ソート |
| knowledge | idx_knowledge_title | B-tree | title | タイトル検索 |
| knowledge | idx_knowledge_owner | B-tree | owner | 所有者検索 |
| knowledge | idx_knowledge_project | B-tree | project | プロジェクト検索 |
| knowledge | idx_knowledge_tags | GIN | tags | タグ検索（配列） |
| sop | sop_pkey | PRIMARY | id | 主キー |
| sop | idx_sop_category | B-tree | category | カテゴリ検索 |
| sop | idx_sop_status | B-tree | status | ステータス検索 |
| sop | idx_sop_title | B-tree | title | タイトル検索 |
| sop | idx_sop_version | B-tree | version | バージョン検索 |
| sop | idx_sop_tags | GIN | tags | タグ検索 |
| regulations | regulations_pkey | PRIMARY | id | 主キー |
| regulations | idx_regulations_category | B-tree | category | カテゴリ検索 |
| regulations | idx_regulations_issuer | B-tree | issuer | 発行元検索 |
| incidents | incidents_pkey | PRIMARY | id | 主キー |
| incidents | idx_incident_project | B-tree | project | プロジェクト検索 |
| incidents | idx_incident_severity | B-tree | severity | 重大度検索 |
| incidents | idx_incident_status | B-tree | status | ステータス検索 |
| incidents | idx_incident_date | B-tree | incident_date | 発生日検索 |
| consultations | consultations_pkey | PRIMARY | id | 主キー |
| consultations | idx_consultations_status | B-tree | status | ステータス検索 |
| consultations | idx_consultations_category | B-tree | category | カテゴリ検索 |
| approvals | approvals_pkey | PRIMARY | id | 主キー |
| approvals | idx_approvals_status | B-tree | status | ステータス検索 |
| approvals | idx_approvals_type | B-tree | type | 承認種別検索 |
| notifications | notifications_pkey | PRIMARY | id | 主キー |
| notifications | idx_notifications_status | B-tree | status | ステータス検索 |
| notifications | idx_notifications_type | B-tree | type | 通知種別検索 |
| notification_reads | notification_reads_pkey | PRIMARY | id | 主キー |
| notification_reads | idx_notification_reads_user | B-tree | user_id | ユーザー別既読 |

#### audit スキーマ（12個）

| テーブル | インデックス名 | 種別 | カラム | 用途 |
|---------|--------------|-----|--------|------|
| access_logs | access_logs_pkey | PRIMARY | id | 主キー |
| access_logs | idx_access_log_user_id | B-tree | user_id | ユーザー別ログ |
| access_logs | idx_access_log_action | B-tree | action | アクション別ログ |
| access_logs | idx_access_log_created_at | B-tree | created_at | 時系列検索 |
| access_logs | idx_access_log_status | B-tree | status | ステータス検索 |
| change_logs | change_logs_pkey | PRIMARY | id | 主キー |
| change_logs | idx_change_log_table_name | B-tree | table_name | テーブル別変更 |
| change_logs | idx_change_log_action | B-tree | action | アクション別変更 |
| change_logs | idx_change_log_created_at | B-tree | created_at | 時系列検索 |
| distribution_logs | distribution_logs_pkey | PRIMARY | id | 主キー |
| distribution_logs | idx_distribution_log_notification | B-tree | notification_id | 通知別配信 |
| distribution_logs | idx_distribution_log_status | B-tree | status | ステータス検索 |

### 5.3 インデックス最適化のベストプラクティス

#### 5.3.1 GINインデックスの活用

```sql
-- 配列カラムのタグ検索
SELECT * FROM public.knowledge
WHERE tags @> ARRAY['安全', '品質'];  -- GINインデックス使用

-- 全文検索（日本語対応）
SELECT * FROM public.knowledge
WHERE to_tsvector('japanese', title || ' ' || summary)
      @@ to_tsquery('japanese', '建設 & 安全');
```

#### 5.3.2 複合インデックス検討（Phase C推奨）

```sql
-- よく使われるクエリパターン
-- 例: カテゴリ + ステータス + 更新日でフィルタ
CREATE INDEX idx_knowledge_composite
ON public.knowledge(category, status, updated_at DESC);

-- 例: プロジェクト + 重大度でフィルタ
CREATE INDEX idx_incident_composite
ON public.incidents(project, severity, incident_date DESC);
```

#### 5.3.3 パーシャルインデックス

```sql
-- 公開済みナレッジのみインデックス（検索対象の絞り込み）
CREATE INDEX idx_knowledge_published
ON public.knowledge(updated_at DESC)
WHERE status = 'published';

-- アクティブユーザーのみインデックス
CREATE INDEX idx_users_active
ON auth.users(username)
WHERE is_active = TRUE;
```

---

## 6. 制約とリレーション

### 6.1 外部キー制約（22個）

| 子テーブル | 子カラム | 親テーブル | 親カラム | ON DELETE | ON UPDATE |
|----------|---------|----------|---------|-----------|-----------|
| user_roles | user_id | users | id | CASCADE | CASCADE |
| user_roles | role_id | roles | id | CASCADE | CASCADE |
| role_permissions | role_id | roles | id | CASCADE | CASCADE |
| role_permissions | permission_id | permissions | id | CASCADE | CASCADE |
| knowledge | created_by_id | users | id | SET NULL | CASCADE |
| knowledge | updated_by_id | users | id | SET NULL | CASCADE |
| sop | created_by_id | users | id | SET NULL | CASCADE |
| sop | updated_by_id | users | id | SET NULL | CASCADE |
| sop | supersedes_id | sop | id | SET NULL | CASCADE |
| incidents | reporter_id | users | id | SET NULL | CASCADE |
| consultations | requester_id | users | id | SET NULL | CASCADE |
| consultations | expert_id | users | id | SET NULL | CASCADE |
| consultations | knowledge_id | knowledge | id | SET NULL | CASCADE |
| approvals | requester_id | users | id | SET NULL | CASCADE |
| approvals | approver_id | users | id | SET NULL | CASCADE |
| notification_reads | notification_id | notifications | id | CASCADE | CASCADE |
| notification_reads | user_id | users | id | CASCADE | CASCADE |
| access_logs | user_id | users | id | SET NULL | CASCADE |
| change_logs | user_id | users | id | SET NULL | CASCADE |
| distribution_logs | notification_id | notifications | id | SET NULL | CASCADE |
| distribution_logs | user_id | users | id | SET NULL | CASCADE |

**削除ポリシー**:
- `CASCADE`: ユーザー-ロール、ロール-権限の関連（整合性優先）
- `SET NULL`: ナレッジの作成者、更新者（履歴保持優先）

### 6.2 CHECK制約（11個）

| テーブル | 制約名 | 条件 | 説明 |
|---------|-------|-----|------|
| knowledge | chk_knowledge_status | status IN ('draft', 'published', 'archived') | ステータス値制限 |
| knowledge | chk_knowledge_priority | priority IN ('low', 'medium', 'high', 'critical') | 優先度値制限 |
| sop | chk_sop_status | status IN ('active', 'deprecated', 'draft') | ステータス値制限 |
| sop | chk_sop_version_format | version ~ '^[0-9]+\.[0-9]+\.[0-9]+$' | バージョン形式（SemVer） |
| regulations | chk_regulations_status | status IN ('active', 'deprecated') | ステータス値制限 |
| incidents | chk_incident_severity | severity IN ('minor', 'moderate', 'major', 'critical') | 重大度値制限 |
| incidents | chk_incident_status | status IN ('reported', 'investigating', 'resolved', 'closed') | ステータス値制限 |
| consultations | chk_consultations_status | status IN ('pending', 'answered', 'closed') | ステータス値制限 |
| approvals | chk_approvals_status | status IN ('pending', 'approved', 'rejected') | ステータス値制限 |
| access_logs | chk_access_log_status | status IN ('success', 'failed', 'blocked') | ステータス値制限 |
| change_logs | chk_change_log_action | action IN ('INSERT', 'UPDATE', 'DELETE') | アクション値制限 |

### 6.3 UNIQUE制約（6個）

| テーブル | カラム | 説明 |
|---------|-------|------|
| users | username | ユーザー名の一意性 |
| users | email | メールアドレスの一意性 |
| roles | name | 役割名の一意性 |
| permissions | name | 権限名の一意性 |
| user_roles | (user_id, role_id) | ユーザー-役割の一意性（複合主キー） |
| role_permissions | (role_id, permission_id) | 役割-権限の一意性（複合主キー） |

---

## 7. マイグレーション戦略

### 7.1 Alembicマイグレーション導入（Phase C推奨）

現在のシステムは**SQLAlchemy ORM**でスキーマを管理していますが、本番運用では**Alembic**によるバージョン管理が必須です。

#### 7.1.1 Alembicセットアップ

```bash
# Alembicインストール
pip install alembic

# 初期化
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend
alembic init alembic

# alembic.iniの編集
# sqlalchemy.url = postgresql://mirai_admin:yourpassword@localhost/mirai_knowledge_db
```

#### 7.1.2 初回マイグレーション作成

```python
# alembic/env.py の編集
from models import Base
target_metadata = Base.metadata

# 現在のスキーマをベースライン化
alembic revision --autogenerate -m "Initial schema from SQLAlchemy models"

# マイグレーション実行
alembic upgrade head
```

#### 7.1.3 スキーマ変更の手順

```bash
# 1. models.pyを編集（例: knowledgeテーブルにversion_numberカラム追加）
# 2. マイグレーションファイル自動生成
alembic revision --autogenerate -m "Add version_number to knowledge table"

# 3. 生成されたマイグレーションファイルをレビュー
# alembic/versions/XXXXXX_add_version_number_to_knowledge_table.py

# 4. 本番適用前にステージング環境でテスト
alembic upgrade head --sql > migration_preview.sql

# 5. 本番適用
alembic upgrade head
```

### 7.2 マイグレーションパターン

#### 7.2.1 カラム追加（非破壊的）

```python
# alembic/versions/xxxx_add_column.py
def upgrade():
    op.add_column('knowledge',
        sa.Column('view_count', sa.Integer, server_default='0')
    )
    op.create_index('idx_knowledge_view_count', 'knowledge', ['view_count'])

def downgrade():
    op.drop_index('idx_knowledge_view_count', table_name='knowledge')
    op.drop_column('knowledge', 'view_count')
```

#### 7.2.2 カラム削除（破壊的 - バックアップ必須）

```python
def upgrade():
    # 1. データ移行が必要な場合は先に実施
    # op.execute("UPDATE knowledge SET new_column = old_column")

    # 2. 削除実行
    op.drop_column('knowledge', 'old_column')

def downgrade():
    # ロールバック時のデータ復元は不可能なため警告
    raise Exception("Downgrade not supported - data loss would occur")
```

#### 7.2.3 インデックス追加（ロック最小化）

```sql
-- PostgreSQL 11+のCONCURRENTLYオプション使用
CREATE INDEX CONCURRENTLY idx_knowledge_created_at
ON public.knowledge(created_at DESC);

-- Alembicでの記述
def upgrade():
    op.create_index(
        'idx_knowledge_created_at',
        'knowledge',
        ['created_at'],
        postgresql_concurrently=True
    )
```

### 7.3 データ移行パターン

#### 7.3.1 大量データのバッチ更新

```python
# alembic/versions/xxxx_migrate_data.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

def upgrade():
    connection = op.get_bind()

    # バッチサイズを指定して段階的に更新
    batch_size = 1000
    offset = 0

    while True:
        result = connection.execute(
            sa.text("""
                UPDATE knowledge
                SET normalized_title = LOWER(title)
                WHERE id IN (
                    SELECT id FROM knowledge
                    ORDER BY id
                    LIMIT :limit OFFSET :offset
                )
            """),
            {"limit": batch_size, "offset": offset}
        )

        if result.rowcount == 0:
            break

        offset += batch_size
```

#### 7.3.2 JSONBデータの変換

```python
def upgrade():
    # 既存のJSON配列をJSONBオブジェクト配列に変換
    op.execute("""
        UPDATE public.incidents
        SET corrective_actions = (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'action', elem,
                    'status', 'pending',
                    'created_at', NOW()
                )
            )
            FROM jsonb_array_elements_text(corrective_actions) AS elem
        )
        WHERE jsonb_typeof(corrective_actions) = 'array'
    """)
```

### 7.4 ロールバック戦略

#### 7.4.1 段階的ロールバック

```bash
# 現在のバージョン確認
alembic current

# 1つ前のバージョンに戻す
alembic downgrade -1

# 特定のバージョンに戻す
alembic downgrade a3f4b8c21d9e

# 全てロールバック（開発環境のみ）
alembic downgrade base
```

#### 7.4.2 バックアップ先行ロールバック

```bash
# 1. マイグレーション前に必ずバックアップ
pg_dump -h localhost -U mirai_admin -d mirai_knowledge_db \
    -F c -f backup_before_migration_$(date +%Y%m%d_%H%M%S).dump

# 2. マイグレーション実行
alembic upgrade head

# 3. 問題発生時は即座にバックアップからリストア
pg_restore -h localhost -U mirai_admin -d mirai_knowledge_db \
    -c backup_before_migration_YYYYMMDD_HHMMSS.dump
```

---

## 8. パフォーマンス最適化

### 8.1 クエリ最適化

#### 8.1.1 N+1問題の回避

**問題のあるコード**:
```python
# ❌ N+1クエリ発生
knowledges = session.query(Knowledge).all()
for k in knowledges:
    print(k.created_by.username)  # 各レコードでSELECT発行
```

**最適化されたコード**:
```python
# ✅ JOINを使った一括取得
knowledges = session.query(Knowledge)\
    .options(joinedload(Knowledge.created_by))\
    .all()
for k in knowledges:
    print(k.created_by.username)  # 追加クエリなし
```

#### 8.1.2 インデックスヒントの使用

```sql
-- EXPLAIN ANALYZEでインデックス使用を確認
EXPLAIN ANALYZE
SELECT * FROM public.knowledge
WHERE category = '技術' AND status = 'published'
ORDER BY updated_at DESC
LIMIT 20;

-- インデックスが使われない場合は複合インデックス追加
CREATE INDEX idx_knowledge_category_status_updated
ON public.knowledge(category, status, updated_at DESC);
```

#### 8.1.3 ページネーション最適化

```sql
-- ❌ 遅い（OFFSET大きいと全件スキャン）
SELECT * FROM public.knowledge
ORDER BY id
LIMIT 20 OFFSET 10000;

-- ✅ 速い（キーセットページネーション）
SELECT * FROM public.knowledge
WHERE id > 10000
ORDER BY id
LIMIT 20;
```

### 8.2 パーティショニング（Phase C推奨）

#### 8.2.1 時系列データのパーティション

```sql
-- audit.access_logsを月次パーティション
CREATE TABLE audit.access_logs (
    id SERIAL,
    created_at TIMESTAMP NOT NULL,
    ...
) PARTITION BY RANGE (created_at);

-- パーティション作成
CREATE TABLE audit.access_logs_2026_01
PARTITION OF audit.access_logs
FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE audit.access_logs_2026_02
PARTITION OF audit.access_logs
FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- 自動パーティション作成（pg_partmanツール使用推奨）
```

#### 8.2.2 古いパーティションのアーカイブ

```bash
# 1年前のログをアーカイブテーブルに移動
psql -U mirai_admin -d mirai_knowledge_db <<EOF
ALTER TABLE audit.access_logs
DETACH PARTITION audit.access_logs_2025_01;

-- 別スキーマに移動
ALTER TABLE audit.access_logs_2025_01
SET SCHEMA archive;
EOF
```

### 8.3 VACUUMとANALYZE

```bash
# 定期的なメンテナンス（cron推奨）
# /etc/cron.daily/pg_maintenance.sh

#!/bin/bash
psql -U mirai_admin -d mirai_knowledge_db <<EOF
-- 統計情報更新
ANALYZE;

-- 不要領域の回収（軽量）
VACUUM;

-- 月次フルVACUUM（週末深夜）
-- VACUUM FULL;  -- テーブルロック発生のため注意
EOF
```

### 8.4 コネクションプーリング

```python
# app_v2.py の最適化
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,           # 最大20コネクション
    max_overflow=10,        # 超過時+10
    pool_pre_ping=True,     # コネクション有効性チェック
    pool_recycle=3600       # 1時間でリサイクル
)
```

---

## 9. 運用ガイドライン

### 9.1 バックアップ戦略

#### 9.1.1 日次バックアップ

```bash
#!/bin/bash
# /opt/mks/scripts/daily_backup.sh

BACKUP_DIR="/mnt/backup/postgresql"
DATE=$(date +%Y%m%d)
RETENTION_DAYS=30

# フルバックアップ
pg_dump -h localhost -U mirai_admin -d mirai_knowledge_db \
    -F c -b -v -f "${BACKUP_DIR}/mks_full_${DATE}.dump"

# 古いバックアップ削除
find "${BACKUP_DIR}" -name "mks_full_*.dump" -mtime +${RETENTION_DAYS} -delete

# クラウドストレージへアップロード（オプション）
# aws s3 cp "${BACKUP_DIR}/mks_full_${DATE}.dump" s3://mks-backups/
```

#### 9.1.2 リストア手順

```bash
# 1. データベース再作成
psql -U postgres <<EOF
DROP DATABASE IF EXISTS mirai_knowledge_db;
CREATE DATABASE mirai_knowledge_db
    OWNER mirai_admin
    ENCODING 'UTF8'
    LC_COLLATE 'ja_JP.UTF-8'
    LC_CTYPE 'ja_JP.UTF-8';
EOF

# 2. バックアップからリストア
pg_restore -h localhost -U mirai_admin -d mirai_knowledge_db \
    -v /mnt/backup/postgresql/mks_full_20260108.dump

# 3. 統計情報更新
psql -U mirai_admin -d mirai_knowledge_db -c "ANALYZE;"
```

### 9.2 監視項目

#### 9.2.1 PostgreSQL監視クエリ

```sql
-- 長時間実行クエリ（5秒以上）
SELECT pid, now() - query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '5 seconds'
ORDER BY duration DESC;

-- テーブルサイズ
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname IN ('public', 'auth', 'audit')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- インデックス使用率
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan AS index_scans,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched
FROM pg_stat_user_indexes
WHERE idx_scan = 0  -- 未使用インデックス検出
ORDER BY schemaname, tablename;

-- コネクション数
SELECT count(*) AS connections, state
FROM pg_stat_activity
GROUP BY state;
```

#### 9.2.2 Prometheusメトリクス

```yaml
# prometheus.yml 抜粋
scrape_configs:
  - job_name: 'mks_postgresql'
    static_configs:
      - targets: ['localhost:9187']  # postgres_exporter
    metrics_path: '/metrics'
```

### 9.3 セキュリティガイドライン

#### 9.3.1 ユーザー権限管理

```sql
-- 読み取り専用ユーザー作成（レポート用）
CREATE ROLE mks_readonly;
GRANT CONNECT ON DATABASE mirai_knowledge_db TO mks_readonly;
GRANT USAGE ON SCHEMA public, auth, audit TO mks_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public, auth, audit TO mks_readonly;

-- バックアップ専用ユーザー
CREATE ROLE mks_backup WITH LOGIN PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE mirai_knowledge_db TO mks_backup;
ALTER ROLE mks_backup WITH REPLICATION;
```

#### 9.3.2 SSL/TLS接続

```bash
# postgresql.conf
ssl = on
ssl_cert_file = '/etc/ssl/certs/postgresql.crt'
ssl_key_file = '/etc/ssl/private/postgresql.key'

# pg_hba.conf（パスワード認証をSSL必須に）
hostssl all all 0.0.0.0/0 scram-sha-256
```

#### 9.3.3 監査ログ設定

```bash
# postgresql.conf
log_statement = 'mod'  # DDL/DML のみ
log_duration = on
log_line_prefix = '%t [%p]: user=%u,db=%d,app=%a,client=%h '
```

### 9.4 トラブルシューティング

#### 9.4.1 デッドロック解消

```sql
-- デッドロック検出
SELECT
    blocked_locks.pid AS blocked_pid,
    blocking_locks.pid AS blocking_pid,
    blocked_activity.query AS blocked_query,
    blocking_activity.query AS blocking_query
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted AND blocking_locks.granted;

-- プロセスキル（最終手段）
SELECT pg_terminate_backend(12345);  -- PIDを指定
```

#### 9.4.2 ディスク容量不足

```bash
# 不要なログファイル削除
find /var/lib/postgresql/16/main/pg_log -name "*.log" -mtime +7 -delete

# VACUUM FULLでテーブル圧縮（要ダウンタイム）
psql -U mirai_admin -d mirai_knowledge_db -c "VACUUM FULL;"

# テーブルスペース追加（ディスク拡張）
CREATE TABLESPACE archive_space LOCATION '/mnt/archive';
ALTER TABLE audit.access_logs SET TABLESPACE archive_space;
```

---

## 付録A: DDL全文

### A.1 スキーマ作成スクリプト

```sql
-- ============================================================
-- Mirai Knowledge Systems - PostgreSQL Schema
-- Version: 2.0
-- Date: 2026-01-08
-- ============================================================

-- スキーマ作成
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS audit;
-- public スキーマはデフォルトで存在

-- 拡張機能有効化
CREATE EXTENSION IF NOT EXISTS pg_trgm;      -- 日本語あいまい検索
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- UUID生成

-- ============================================================
-- AUTH スキーマ
-- ============================================================

CREATE TABLE auth.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(200),
    department VARCHAR(100),
    position VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE auth.roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE auth.permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT
);

CREATE TABLE auth.user_roles (
    user_id INTEGER NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES auth.roles(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE auth.role_permissions (
    role_id INTEGER NOT NULL REFERENCES auth.roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES auth.permissions(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id)
);

-- ============================================================
-- PUBLIC スキーマ
-- ============================================================

CREATE TABLE public.knowledge (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    summary TEXT NOT NULL,
    content TEXT,
    category VARCHAR(100) NOT NULL,
    tags TEXT[],
    status VARCHAR(50) DEFAULT 'draft',
    priority VARCHAR(20) DEFAULT 'medium',
    project VARCHAR(100),
    owner VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES auth.users(id) ON DELETE SET NULL,
    updated_by_id INTEGER REFERENCES auth.users(id) ON DELETE SET NULL,
    CONSTRAINT chk_knowledge_status CHECK (status IN ('draft', 'published', 'archived')),
    CONSTRAINT chk_knowledge_priority CHECK (priority IN ('low', 'medium', 'high', 'critical'))
);

CREATE TABLE public.sop (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    category VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    revision_date DATE NOT NULL,
    target VARCHAR(200),
    tags TEXT[],
    content TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    supersedes_id INTEGER REFERENCES public.sop(id) ON DELETE SET NULL,
    attachments JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES auth.users(id) ON DELETE SET NULL,
    updated_by_id INTEGER REFERENCES auth.users(id) ON DELETE SET NULL,
    CONSTRAINT chk_sop_status CHECK (status IN ('active', 'deprecated', 'draft'))
);

CREATE TABLE public.regulations (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    issuer VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    revision_date DATE NOT NULL,
    applicable_scope TEXT[],
    summary TEXT NOT NULL,
    content TEXT,
    status VARCHAR(50) DEFAULT 'active',
    effective_date DATE,
    url VARCHAR(1000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_regulations_status CHECK (status IN ('active', 'deprecated'))
);

CREATE TABLE public.incidents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    project VARCHAR(100) NOT NULL,
    incident_date DATE NOT NULL,
    severity VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'reported',
    corrective_actions JSONB,
    root_cause TEXT,
    tags TEXT[],
    location VARCHAR(300),
    involved_parties TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reporter_id INTEGER REFERENCES auth.users(id) ON DELETE SET NULL,
    CONSTRAINT chk_incident_severity CHECK (severity IN ('minor', 'moderate', 'major', 'critical')),
    CONSTRAINT chk_incident_status CHECK (status IN ('reported', 'investigating', 'resolved', 'closed'))
);

CREATE TABLE public.consultations (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    question TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'pending',
    requester_id INTEGER REFERENCES auth.users(id) ON DELETE SET NULL,
    expert_id INTEGER REFERENCES auth.users(id) ON DELETE SET NULL,
    answer TEXT,
    answered_at TIMESTAMP,
    knowledge_id INTEGER REFERENCES public.knowledge(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_consultations_status CHECK (status IN ('pending', 'answered', 'closed'))
);

CREATE TABLE public.approvals (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    type VARCHAR(100) NOT NULL,
    description TEXT,
    requester_id INTEGER REFERENCES auth.users(id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'medium',
    related_entity_type VARCHAR(50),
    related_entity_id INTEGER,
    approval_flow JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    approver_id INTEGER REFERENCES auth.users(id) ON DELETE SET NULL,
    CONSTRAINT chk_approvals_status CHECK (status IN ('pending', 'approved', 'rejected'))
);

CREATE TABLE public.notifications (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) NOT NULL,
    target_users INTEGER[],
    target_roles TEXT[],
    delivery_channels TEXT[],
    related_entity_type VARCHAR(50),
    related_entity_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending'
);

CREATE TABLE public.notification_reads (
    id SERIAL PRIMARY KEY,
    notification_id INTEGER NOT NULL REFERENCES public.notifications(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- AUDIT スキーマ
-- ============================================================

CREATE TABLE audit.access_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth.users(id) ON DELETE SET NULL,
    username VARCHAR(100),
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100),
    resource_id INTEGER,
    ip_address INET,
    user_agent TEXT,
    request_method VARCHAR(10),
    request_path VARCHAR(500),
    session_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'success',
    details JSONB,
    changes JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_access_log_status CHECK (status IN ('success', 'failed', 'blocked'))
);

CREATE TABLE audit.change_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth.users(id) ON DELETE SET NULL,
    username VARCHAR(100),
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER,
    action VARCHAR(50) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_change_log_action CHECK (action IN ('INSERT', 'UPDATE', 'DELETE'))
);

CREATE TABLE audit.distribution_logs (
    id SERIAL PRIMARY KEY,
    notification_id INTEGER REFERENCES public.notifications(id) ON DELETE SET NULL,
    user_id INTEGER REFERENCES auth.users(id) ON DELETE SET NULL,
    delivery_channel VARCHAR(50),
    status VARCHAR(50),
    sent_at TIMESTAMP,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- インデックス作成
-- ============================================================

-- auth.users
CREATE INDEX idx_users_username ON auth.users(username);
CREATE INDEX idx_users_email ON auth.users(email);
CREATE INDEX idx_users_is_active ON auth.users(is_active);

-- auth.permissions
CREATE INDEX idx_permissions_resource ON auth.permissions(resource);

-- public.knowledge
CREATE INDEX idx_knowledge_category ON public.knowledge(category);
CREATE INDEX idx_knowledge_status ON public.knowledge(status);
CREATE INDEX idx_knowledge_updated_at ON public.knowledge(updated_at DESC);
CREATE INDEX idx_knowledge_title ON public.knowledge(title);
CREATE INDEX idx_knowledge_owner ON public.knowledge(owner);
CREATE INDEX idx_knowledge_project ON public.knowledge(project);
CREATE INDEX idx_knowledge_tags ON public.knowledge USING GIN(tags);

-- public.sop
CREATE INDEX idx_sop_category ON public.sop(category);
CREATE INDEX idx_sop_status ON public.sop(status);
CREATE INDEX idx_sop_title ON public.sop(title);
CREATE INDEX idx_sop_version ON public.sop(version);
CREATE INDEX idx_sop_tags ON public.sop USING GIN(tags);

-- public.regulations
CREATE INDEX idx_regulations_category ON public.regulations(category);
CREATE INDEX idx_regulations_issuer ON public.regulations(issuer);

-- public.incidents
CREATE INDEX idx_incident_project ON public.incidents(project);
CREATE INDEX idx_incident_severity ON public.incidents(severity);
CREATE INDEX idx_incident_status ON public.incidents(status);
CREATE INDEX idx_incident_date ON public.incidents(incident_date);

-- public.consultations
CREATE INDEX idx_consultations_status ON public.consultations(status);
CREATE INDEX idx_consultations_category ON public.consultations(category);

-- public.approvals
CREATE INDEX idx_approvals_status ON public.approvals(status);
CREATE INDEX idx_approvals_type ON public.approvals(type);

-- public.notifications
CREATE INDEX idx_notifications_status ON public.notifications(status);
CREATE INDEX idx_notifications_type ON public.notifications(type);

-- public.notification_reads
CREATE INDEX idx_notification_reads_user ON public.notification_reads(user_id);

-- audit.access_logs
CREATE INDEX idx_access_log_user_id ON audit.access_logs(user_id);
CREATE INDEX idx_access_log_action ON audit.access_logs(action);
CREATE INDEX idx_access_log_created_at ON audit.access_logs(created_at);
CREATE INDEX idx_access_log_status ON audit.access_logs(status);

-- audit.change_logs
CREATE INDEX idx_change_log_table_name ON audit.change_logs(table_name);
CREATE INDEX idx_change_log_action ON audit.change_logs(action);
CREATE INDEX idx_change_log_created_at ON audit.change_logs(created_at);

-- audit.distribution_logs
CREATE INDEX idx_distribution_log_notification ON audit.distribution_logs(notification_id);
CREATE INDEX idx_distribution_log_status ON audit.distribution_logs(status);

-- ============================================================
-- 初期データ投入
-- ============================================================

-- 役割
INSERT INTO auth.roles (name, description) VALUES
    ('admin', 'システム管理者 - 全権限'),
    ('editor', '編集者 - ナレッジ作成・編集'),
    ('viewer', '閲覧者 - 参照のみ'),
    ('expert', '専門家 - 相談対応');

-- 権限
INSERT INTO auth.permissions (name, resource, action, description) VALUES
    ('admin', '*', '*', '全権限'),
    ('knowledge_read', 'knowledge', 'read', 'ナレッジ閲覧'),
    ('knowledge_write', 'knowledge', 'write', 'ナレッジ作成・編集'),
    ('knowledge_delete', 'knowledge', 'delete', 'ナレッジ削除'),
    ('sop_read', 'sop', 'read', 'SOP閲覧'),
    ('sop_write', 'sop', 'write', 'SOP作成・編集'),
    ('sop_delete', 'sop', 'delete', 'SOP削除'),
    ('incident_read', 'incident', 'read', '事故レポート閲覧'),
    ('incident_write', 'incident', 'write', '事故レポート作成'),
    ('user_manage', 'user', 'manage', 'ユーザー管理'),
    ('consultation_answer', 'consultation', 'answer', '専門家相談回答');

-- 役割-権限マッピング
INSERT INTO auth.role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM auth.roles r, auth.permissions p
WHERE r.name = 'admin' AND p.name = 'admin';

INSERT INTO auth.role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM auth.roles r, auth.permissions p
WHERE r.name = 'editor' AND p.name IN ('knowledge_read', 'knowledge_write', 'sop_read', 'sop_write', 'incident_read', 'incident_write');

INSERT INTO auth.role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM auth.roles r, auth.permissions p
WHERE r.name = 'viewer' AND p.name IN ('knowledge_read', 'sop_read', 'incident_read');

INSERT INTO auth.role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM auth.roles r, auth.permissions p
WHERE r.name = 'expert' AND p.name IN ('knowledge_read', 'knowledge_write', 'sop_read', 'consultation_answer');

-- 完了
-- スキーマ作成完了: 16テーブル、54インデックス、22外部キー
```

---

## 付録B: データ辞書

### B.1 ステータス値一覧

| テーブル | カラム | 値 | 日本語 | 説明 |
|---------|--------|---|--------|------|
| knowledge | status | draft | 下書き | 編集中、未公開 |
| knowledge | status | published | 公開 | 一般ユーザーに公開 |
| knowledge | status | archived | アーカイブ | 古い記事の保管 |
| sop | status | active | 有効 | 現在使用中 |
| sop | status | deprecated | 非推奨 | 新版に置き換え済み |
| sop | status | draft | 下書き | 作成中 |
| regulations | status | active | 有効 | 現行法令 |
| regulations | status | deprecated | 廃止 | 失効済み |
| incidents | status | reported | 報告済み | 初期報告完了 |
| incidents | status | investigating | 調査中 | 原因分析中 |
| incidents | status | resolved | 解決済み | 是正措置完了 |
| incidents | status | closed | クローズ | 最終承認済み |
| consultations | status | pending | 未回答 | 専門家待ち |
| consultations | status | answered | 回答済み | 回答完了 |
| consultations | status | closed | クローズ | 質問者確認済み |
| approvals | status | pending | 承認待ち | 未承認 |
| approvals | status | approved | 承認済み | 承認完了 |
| approvals | status | rejected | 却下 | 却下済み |

### B.2 優先度・重大度値

| カラム | 値 | 日本語 | 対応時間 |
|--------|---|--------|---------|
| priority | low | 低 | 1週間以内 |
| priority | medium | 中 | 3日以内 |
| priority | high | 高 | 1日以内 |
| priority | critical | 緊急 | 即座 |
| severity (incidents) | minor | 軽微 | 通常対応 |
| severity (incidents) | moderate | 中程度 | 注意喚起 |
| severity (incidents) | major | 重大 | 即時報告 |
| severity (incidents) | critical | 致命的 | 緊急停止 |

---

## 付録C: 変更履歴

| バージョン | 日付 | 変更内容 | 担当 |
|----------|------|---------|------|
| 1.0 | 2026-01-07 | 初版作成（PostgreSQL移行完了時） | Claude Code |
| 2.0 | 2026-01-08 | 完全版作成（論理/物理モデル、マイグレーション戦略追加） | Claude Sonnet 4.5 |

---

**文書管理**: `/mnt/LinuxHDD/Mirai-Knowledge-Systems/DATABASE_DESIGN_COMPLETE.md`
**関連文書**:
- `/docs/06_データ設計(Data-Design)/04_DB構造設計書(Database-Structure).md`
- `/backend/models.py`（SQLAlchemy ORM定義）
- `/docs/PostgreSQL移行手順.md`（移行手順書）

**次のアクション**:
1. Alembic導入によるマイグレーション管理（Phase C優先）
2. パーティショニング検討（audit.access_logs, audit.change_logs）
3. 複合インデックスの追加（クエリパフォーマンス分析後）
