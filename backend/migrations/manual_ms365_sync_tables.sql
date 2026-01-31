-- =====================================================
-- Microsoft 365 Sync Tables Migration
-- =====================================================
-- 手動実行用SQLスクリプト
-- 実行方法: psql -U mirai_user -d mirai_knowledge -f migrations/manual_ms365_sync_tables.sql
-- =====================================================

-- 1. ms365_sync_config テーブル作成
CREATE TABLE IF NOT EXISTS public.ms365_sync_config (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    site_id VARCHAR(200) NOT NULL,
    drive_id VARCHAR(200) NOT NULL,
    folder_path VARCHAR(500) DEFAULT '/',
    file_extensions TEXT[],
    sync_schedule VARCHAR(100) DEFAULT '0 2 * * *',
    is_enabled BOOLEAN DEFAULT true,
    last_sync_at TIMESTAMP,
    next_sync_at TIMESTAMP,
    sync_strategy VARCHAR(50) DEFAULT 'incremental',
    metadata_mapping JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by_id INTEGER REFERENCES auth.users(id),
    updated_by_id INTEGER REFERENCES auth.users(id)
);

CREATE INDEX IF NOT EXISTS idx_ms365_sync_config_enabled ON public.ms365_sync_config(is_enabled);
CREATE INDEX IF NOT EXISTS idx_ms365_sync_config_next_sync ON public.ms365_sync_config(next_sync_at);

-- 2. ms365_sync_history テーブル作成
CREATE TABLE IF NOT EXISTS public.ms365_sync_history (
    id SERIAL PRIMARY KEY,
    config_id INTEGER NOT NULL REFERENCES public.ms365_sync_config(id) ON DELETE CASCADE,
    sync_started_at TIMESTAMP NOT NULL,
    sync_completed_at TIMESTAMP,
    status VARCHAR(50) NOT NULL,
    files_processed INTEGER DEFAULT 0,
    files_created INTEGER DEFAULT 0,
    files_updated INTEGER DEFAULT 0,
    files_skipped INTEGER DEFAULT 0,
    files_failed INTEGER DEFAULT 0,
    error_message TEXT,
    error_details JSONB,
    execution_time_seconds INTEGER,
    triggered_by VARCHAR(50) DEFAULT 'scheduler',
    triggered_by_user_id INTEGER REFERENCES auth.users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ms365_sync_history_config ON public.ms365_sync_history(config_id);
CREATE INDEX IF NOT EXISTS idx_ms365_sync_history_status ON public.ms365_sync_history(status);
CREATE INDEX IF NOT EXISTS idx_ms365_sync_history_started ON public.ms365_sync_history(sync_started_at DESC);

-- 3. ms365_file_mapping テーブル作成
CREATE TABLE IF NOT EXISTS public.ms365_file_mapping (
    id SERIAL PRIMARY KEY,
    config_id INTEGER NOT NULL REFERENCES public.ms365_sync_config(id) ON DELETE CASCADE,
    sharepoint_file_id VARCHAR(200) NOT NULL UNIQUE,
    sharepoint_file_name VARCHAR(500) NOT NULL,
    sharepoint_file_path VARCHAR(1000),
    sharepoint_modified_at TIMESTAMP,
    sharepoint_size_bytes BIGINT,
    knowledge_id INTEGER REFERENCES public.knowledge(id) ON DELETE SET NULL,
    sync_status VARCHAR(50) DEFAULT 'pending',
    last_synced_at TIMESTAMP,
    checksum VARCHAR(64),
    file_metadata JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ms365_file_mapping_config ON public.ms365_file_mapping(config_id);
CREATE INDEX IF NOT EXISTS idx_ms365_file_mapping_sp_file_id ON public.ms365_file_mapping(sharepoint_file_id);
CREATE INDEX IF NOT EXISTS idx_ms365_file_mapping_knowledge ON public.ms365_file_mapping(knowledge_id);
CREATE INDEX IF NOT EXISTS idx_ms365_file_mapping_status ON public.ms365_file_mapping(sync_status);

-- 4. 権限追加
INSERT INTO auth.permissions (name, resource, action, description)
VALUES
    ('ms365_sync.read', 'ms365_sync', 'read', 'View MS365 sync configurations'),
    ('ms365_sync.create', 'ms365_sync', 'create', 'Create MS365 sync configurations'),
    ('ms365_sync.update', 'ms365_sync', 'update', 'Update MS365 sync configurations'),
    ('ms365_sync.delete', 'ms365_sync', 'delete', 'Delete MS365 sync configurations'),
    ('ms365_sync.execute', 'ms365_sync', 'execute', 'Execute MS365 sync operations')
ON CONFLICT (name) DO NOTHING;

-- 5. admin ロールに権限付与
INSERT INTO auth.role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM auth.roles r
CROSS JOIN auth.permissions p
WHERE r.name = 'admin'
AND p.resource = 'ms365_sync'
AND NOT EXISTS (
    SELECT 1 FROM auth.role_permissions rp
    WHERE rp.role_id = r.id AND rp.permission_id = p.id
);

-- =====================================================
-- マイグレーション完了
-- =====================================================
-- 確認: SELECT * FROM public.ms365_sync_config;
-- 確認: SELECT * FROM auth.permissions WHERE resource = 'ms365_sync';
-- =====================================================
