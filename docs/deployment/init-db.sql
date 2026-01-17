-- PostgreSQL初期化スクリプト
-- Docker Composeで自動実行される
-- Mirai Knowledge Systems - Phase B-10

-- 日本語対応の拡張機能をインストール
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- スキーマ作成
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS audit;

-- コメント追加
COMMENT ON SCHEMA public IS 'ナレッジドメイン';
COMMENT ON SCHEMA auth IS '認証・認可';
COMMENT ON SCHEMA audit IS '監査ログ';

-- ============================================================
-- Auth Schema - 認証・認可（先に作成、他が参照するため）
-- ============================================================

-- ユーザーテーブル
CREATE TABLE IF NOT EXISTS auth.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(200),
    department VARCHAR(100),
    position VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE auth.users IS 'ユーザー情報';

-- 役割テーブル
CREATE TABLE IF NOT EXISTS auth.roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE auth.roles IS '役割定義';

-- 権限テーブル
CREATE TABLE IF NOT EXISTS auth.permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT
);

COMMENT ON TABLE auth.permissions IS '権限定義';

-- ユーザー役割関連テーブル
CREATE TABLE IF NOT EXISTS auth.user_roles (
    user_id INTEGER REFERENCES auth.users(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES auth.roles(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

COMMENT ON TABLE auth.user_roles IS 'ユーザーと役割の関連';

-- 役割権限関連テーブル
CREATE TABLE IF NOT EXISTS auth.role_permissions (
    role_id INTEGER REFERENCES auth.roles(id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES auth.permissions(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id)
);

COMMENT ON TABLE auth.role_permissions IS '役割と権限の関連';

-- ============================================================
-- Public Schema - ナレッジドメイン
-- ============================================================

-- ナレッジテーブル
CREATE TABLE IF NOT EXISTS public.knowledge (
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
    updated_by_id INTEGER REFERENCES auth.users(id)
);

CREATE INDEX IF NOT EXISTS idx_knowledge_category ON public.knowledge(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_status ON public.knowledge(status);
CREATE INDEX IF NOT EXISTS idx_knowledge_updated ON public.knowledge(updated_at);
CREATE INDEX IF NOT EXISTS idx_knowledge_title ON public.knowledge(title);
CREATE INDEX IF NOT EXISTS idx_knowledge_owner ON public.knowledge(owner);
CREATE INDEX IF NOT EXISTS idx_knowledge_project ON public.knowledge(project);
CREATE INDEX IF NOT EXISTS idx_knowledge_tags ON public.knowledge USING GIN(tags);

COMMENT ON TABLE public.knowledge IS 'ナレッジ記事';

-- SOPテーブル
CREATE TABLE IF NOT EXISTS public.sop (
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
    updated_by_id INTEGER REFERENCES auth.users(id)
);

CREATE INDEX IF NOT EXISTS idx_sop_category ON public.sop(category);
CREATE INDEX IF NOT EXISTS idx_sop_status ON public.sop(status);
CREATE INDEX IF NOT EXISTS idx_sop_title ON public.sop(title);
CREATE INDEX IF NOT EXISTS idx_sop_version ON public.sop(version);
CREATE INDEX IF NOT EXISTS idx_sop_tags ON public.sop USING GIN(tags);

COMMENT ON TABLE public.sop IS '標準施工手順';

-- 法令・規格テーブル
CREATE TABLE IF NOT EXISTS public.regulations (
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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_regulations_category ON public.regulations(category);
CREATE INDEX IF NOT EXISTS idx_regulations_issuer ON public.regulations(issuer);

COMMENT ON TABLE public.regulations IS '法令・規格';

-- 事故・ヒヤリレポートテーブル
CREATE TABLE IF NOT EXISTS public.incidents (
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
    reporter_id INTEGER REFERENCES auth.users(id)
);

CREATE INDEX IF NOT EXISTS idx_incident_project ON public.incidents(project);
CREATE INDEX IF NOT EXISTS idx_incident_severity ON public.incidents(severity);
CREATE INDEX IF NOT EXISTS idx_incident_status ON public.incidents(status);
CREATE INDEX IF NOT EXISTS idx_incident_date ON public.incidents(incident_date);

COMMENT ON TABLE public.incidents IS '事故・ヒヤリレポート';

-- 専門家相談テーブル
CREATE TABLE IF NOT EXISTS public.consultations (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    question TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'pending',
    requester_id INTEGER REFERENCES auth.users(id),
    expert_id INTEGER REFERENCES auth.users(id),
    answer TEXT,
    answered_at TIMESTAMP,
    knowledge_id INTEGER REFERENCES public.knowledge(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_consultations_status ON public.consultations(status);
CREATE INDEX IF NOT EXISTS idx_consultations_category ON public.consultations(category);

COMMENT ON TABLE public.consultations IS '専門家相談';

-- 承認フローテーブル
CREATE TABLE IF NOT EXISTS public.approvals (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    type VARCHAR(100) NOT NULL,
    description TEXT,
    requester_id INTEGER REFERENCES auth.users(id),
    status VARCHAR(50) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'medium',
    related_entity_type VARCHAR(50),
    related_entity_id INTEGER,
    approval_flow JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    approver_id INTEGER REFERENCES auth.users(id)
);

CREATE INDEX IF NOT EXISTS idx_approvals_status ON public.approvals(status);
CREATE INDEX IF NOT EXISTS idx_approvals_type ON public.approvals(type);

COMMENT ON TABLE public.approvals IS '承認フロー';

-- 通知テーブル
CREATE TABLE IF NOT EXISTS public.notifications (
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

CREATE INDEX IF NOT EXISTS idx_notifications_status ON public.notifications(status);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON public.notifications(type);

COMMENT ON TABLE public.notifications IS '通知配信';

-- 通知既読管理テーブル
CREATE TABLE IF NOT EXISTS public.notification_reads (
    id SERIAL PRIMARY KEY,
    notification_id INTEGER REFERENCES public.notifications(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES auth.users(id) ON DELETE CASCADE,
    read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notification_reads_user ON public.notification_reads(user_id);

COMMENT ON TABLE public.notification_reads IS '通知既読管理';

-- ============================================================
-- Audit Schema - 監査ログ
-- ============================================================

-- アクセスログテーブル
CREATE TABLE IF NOT EXISTS audit.access_logs (
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_access_logs_user ON audit.access_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_action ON audit.access_logs(action);
CREATE INDEX IF NOT EXISTS idx_access_logs_created ON audit.access_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_access_logs_status ON audit.access_logs(status);

COMMENT ON TABLE audit.access_logs IS 'アクセスログ';

-- 変更ログテーブル
CREATE TABLE IF NOT EXISTS audit.change_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth.users(id),
    username VARCHAR(100),
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER,
    action VARCHAR(50) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_change_logs_table ON audit.change_logs(table_name);
CREATE INDEX IF NOT EXISTS idx_change_logs_action ON audit.change_logs(action);
CREATE INDEX IF NOT EXISTS idx_change_logs_created ON audit.change_logs(created_at);

COMMENT ON TABLE audit.change_logs IS '変更ログ';

-- 配信ログテーブル
CREATE TABLE IF NOT EXISTS audit.distribution_logs (
    id SERIAL PRIMARY KEY,
    notification_id INTEGER REFERENCES public.notifications(id),
    user_id INTEGER REFERENCES auth.users(id),
    delivery_channel VARCHAR(50),
    status VARCHAR(50),
    sent_at TIMESTAMP,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_distribution_logs_notification ON audit.distribution_logs(notification_id);
CREATE INDEX IF NOT EXISTS idx_distribution_logs_status ON audit.distribution_logs(status);

COMMENT ON TABLE audit.distribution_logs IS '通知配信ログ';

-- ============================================================
-- 初期データ投入
-- ============================================================

-- デフォルト役割
INSERT INTO auth.roles (name, description) VALUES
    ('admin', 'システム管理者'),
    ('editor', '編集者'),
    ('viewer', '閲覧者'),
    ('expert', '専門家')
ON CONFLICT (name) DO NOTHING;

-- デフォルト権限
INSERT INTO auth.permissions (name, resource, action, description) VALUES
    ('knowledge_read', 'knowledge', 'read', 'ナレッジ閲覧'),
    ('knowledge_write', 'knowledge', 'write', 'ナレッジ作成・編集'),
    ('knowledge_delete', 'knowledge', 'delete', 'ナレッジ削除'),
    ('sop_read', 'sop', 'read', 'SOP閲覧'),
    ('sop_write', 'sop', 'write', 'SOP作成・編集'),
    ('user_manage', 'user', 'manage', 'ユーザー管理'),
    ('admin', 'system', 'admin', 'システム管理')
ON CONFLICT (name) DO NOTHING;

-- 役割権限関連
INSERT INTO auth.role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM auth.roles r, auth.permissions p
WHERE r.name = 'admin'
ON CONFLICT DO NOTHING;

INSERT INTO auth.role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM auth.roles r, auth.permissions p
WHERE r.name = 'editor' AND p.action IN ('read', 'write')
ON CONFLICT DO NOTHING;

INSERT INTO auth.role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM auth.roles r, auth.permissions p
WHERE r.name = 'viewer' AND p.action = 'read'
ON CONFLICT DO NOTHING;

-- データベース作成完了メッセージ
DO $$
BEGIN
  RAISE NOTICE 'PostgreSQL初期化が完了しました - Mirai Knowledge Systems Phase B-10';
END $$;
