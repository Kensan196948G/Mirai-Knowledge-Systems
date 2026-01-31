"""Add Microsoft 365 sync tables

Revision ID: e1f2a3b4c5d6
Revises: d4e5f6a7b8c9
Create Date: 2026-01-31 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e1f2a3b4c5d6'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade():
    """Create Microsoft 365 sync tables and permissions"""

    # 1. ms365_sync_config テーブル作成
    op.create_table(
        'ms365_sync_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('site_id', sa.String(length=200), nullable=False),
        sa.Column('drive_id', sa.String(length=200), nullable=False),
        sa.Column('folder_path', sa.String(length=500), server_default='/', nullable=True),
        sa.Column('file_extensions', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('sync_schedule', sa.String(length=100), server_default='0 2 * * *', nullable=True),
        sa.Column('is_enabled', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('next_sync_at', sa.DateTime(), nullable=True),
        sa.Column('sync_strategy', sa.String(length=50), server_default='incremental', nullable=True),
        sa.Column('metadata_mapping', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['auth.users.id'], ),
        sa.ForeignKeyConstraint(['updated_by_id'], ['auth.users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )

    # インデックス作成
    op.create_index('idx_ms365_sync_config_enabled', 'ms365_sync_config', ['is_enabled'], schema='public')
    op.create_index('idx_ms365_sync_config_next_sync', 'ms365_sync_config', ['next_sync_at'], schema='public')

    # 2. ms365_sync_history テーブル作成
    op.create_table(
        'ms365_sync_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('config_id', sa.Integer(), nullable=False),
        sa.Column('sync_started_at', sa.DateTime(), nullable=False),
        sa.Column('sync_completed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('files_processed', sa.Integer(), server_default='0', nullable=True),
        sa.Column('files_created', sa.Integer(), server_default='0', nullable=True),
        sa.Column('files_updated', sa.Integer(), server_default='0', nullable=True),
        sa.Column('files_skipped', sa.Integer(), server_default='0', nullable=True),
        sa.Column('files_failed', sa.Integer(), server_default='0', nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('execution_time_seconds', sa.Integer(), nullable=True),
        sa.Column('triggered_by', sa.String(length=50), server_default='scheduler', nullable=True),
        sa.Column('triggered_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['config_id'], ['public.ms365_sync_config.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['triggered_by_user_id'], ['auth.users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )

    # インデックス作成
    op.create_index('idx_ms365_sync_history_config', 'ms365_sync_history', ['config_id'], schema='public')
    op.create_index('idx_ms365_sync_history_status', 'ms365_sync_history', ['status'], schema='public')
    op.create_index('idx_ms365_sync_history_started', 'ms365_sync_history', ['sync_started_at'], schema='public')

    # 3. ms365_file_mapping テーブル作成
    op.create_table(
        'ms365_file_mapping',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('config_id', sa.Integer(), nullable=False),
        sa.Column('sharepoint_file_id', sa.String(length=200), nullable=False),
        sa.Column('sharepoint_file_name', sa.String(length=500), nullable=False),
        sa.Column('sharepoint_file_path', sa.String(length=1000), nullable=True),
        sa.Column('sharepoint_modified_at', sa.DateTime(), nullable=True),
        sa.Column('sharepoint_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('knowledge_id', sa.Integer(), nullable=True),
        sa.Column('sync_status', sa.String(length=50), server_default='pending', nullable=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('checksum', sa.String(length=64), nullable=True),
        sa.Column('file_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['config_id'], ['public.ms365_sync_config.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['knowledge_id'], ['public.knowledge.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sharepoint_file_id'),
        schema='public'
    )

    # インデックス作成
    op.create_index('idx_ms365_file_mapping_config', 'ms365_file_mapping', ['config_id'], schema='public')
    op.create_index('idx_ms365_file_mapping_sp_file_id', 'ms365_file_mapping', ['sharepoint_file_id'], schema='public')
    op.create_index('idx_ms365_file_mapping_knowledge', 'ms365_file_mapping', ['knowledge_id'], schema='public')
    op.create_index('idx_ms365_file_mapping_status', 'ms365_file_mapping', ['sync_status'], schema='public')

    # 4. 権限追加（auth.permissions テーブルが存在する場合）
    op.execute("""
        INSERT INTO auth.permissions (name, resource, action, description)
        VALUES
            ('ms365_sync.read', 'ms365_sync', 'read', 'View MS365 sync configurations'),
            ('ms365_sync.create', 'ms365_sync', 'create', 'Create MS365 sync configurations'),
            ('ms365_sync.update', 'ms365_sync', 'update', 'Update MS365 sync configurations'),
            ('ms365_sync.delete', 'ms365_sync', 'delete', 'Delete MS365 sync configurations'),
            ('ms365_sync.execute', 'ms365_sync', 'execute', 'Execute MS365 sync operations')
        ON CONFLICT (name) DO NOTHING;
    """)

    # 5. admin ロールに権限付与
    op.execute("""
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
    """)


def downgrade():
    """Drop Microsoft 365 sync tables and permissions"""

    # 権限削除
    op.execute("DELETE FROM auth.permissions WHERE resource = 'ms365_sync'")

    # テーブル削除（逆順）
    op.drop_table('ms365_file_mapping', schema='public')
    op.drop_table('ms365_sync_history', schema='public')
    op.drop_table('ms365_sync_config', schema='public')
