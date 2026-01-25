#!/usr/bin/env python3
"""
JSON to PostgreSQL データ移行スクリプト
Mirai Knowledge Systems - Phase B-10

Usage:
    python migrate_json_to_postgres.py [--dry-run] [--verbose]
"""

import json
import os
import sys
import argparse
from datetime import datetime, date
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

# データディレクトリ
DATA_DIR = Path(__file__).parent.parent / 'data'


def load_json(filename: str) -> list:
    """JSONファイルを読み込む"""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        print(f"[WARN] File not found: {filepath}")
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_date(date_str: str) -> date | None:
    """日付文字列をパース"""
    if not date_str:
        return None
    try:
        if 'T' in date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def parse_datetime(dt_str: str) -> datetime | None:
    """日時文字列をパース"""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return None


def migrate_users(session, dry_run: bool, verbose: bool) -> dict:
    """ユーザーデータを移行"""
    users = load_json('users.json')
    user_id_map = {}

    print(f"\n[INFO] Migrating {len(users)} users...")

    for user in users:
        old_id = user.get('id')

        # パスワードハッシュの処理
        password_hash = user.get('password_hash') or user.get('password')
        if password_hash and not password_hash.startswith('pbkdf2:') and not password_hash.startswith('scrypt:'):
            password_hash = generate_password_hash(password_hash)

        if not dry_run:
            result = session.execute(text("""
                INSERT INTO auth.users (username, email, password_hash, full_name, department, position, is_active, created_at, updated_at)
                VALUES (:username, :email, :password_hash, :full_name, :department, :position, :is_active, :created_at, :updated_at)
                ON CONFLICT (username) DO UPDATE SET
                    email = EXCLUDED.email,
                    full_name = EXCLUDED.full_name,
                    department = EXCLUDED.department,
                    position = EXCLUDED.position
                RETURNING id
            """), {
                'username': user.get('username'),
                'email': user.get('email') or f"{user.get('username')}@example.com",
                'password_hash': password_hash or generate_password_hash('password'),
                'full_name': user.get('full_name') or user.get('name'),
                'department': user.get('department'),
                'position': user.get('position') or user.get('role'),
                'is_active': user.get('is_active', True),
                'created_at': parse_datetime(user.get('created_at')) or datetime.now(),
                'updated_at': parse_datetime(user.get('updated_at')) or datetime.now()
            })
            new_id = result.fetchone()[0]
            user_id_map[old_id] = new_id

            # 役割の割り当て
            role = user.get('role', 'viewer').lower()
            session.execute(text("""
                INSERT INTO auth.user_roles (user_id, role_id)
                SELECT :user_id, id FROM auth.roles WHERE name = :role
                ON CONFLICT DO NOTHING
            """), {'user_id': new_id, 'role': role})

        if verbose:
            print(f"  - User: {user.get('username')} (old_id={old_id})")

    if not dry_run:
        session.commit()

    print(f"[OK] Migrated {len(users)} users")
    return user_id_map


def migrate_knowledge(session, user_id_map: dict, dry_run: bool, verbose: bool):
    """ナレッジデータを移行"""
    items = load_json('knowledge.json')
    details = {d['id']: d for d in load_json('knowledge_details.json')}

    print(f"\n[INFO] Migrating {len(items)} knowledge items...")

    for item in items:
        detail = details.get(item['id'], {})
        content = detail.get('content', '')

        tags = item.get('tags', [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',')]

        created_by_id = user_id_map.get(item.get('created_by_id'))

        if not dry_run:
            session.execute(text("""
                INSERT INTO public.knowledge (id, title, summary, content, category, tags, status, priority, project, owner, created_at, updated_at, created_by_id)
                VALUES (:id, :title, :summary, :content, :category, :tags, :status, :priority, :project, :owner, :created_at, :updated_at, :created_by_id)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    summary = EXCLUDED.summary,
                    content = EXCLUDED.content,
                    category = EXCLUDED.category,
                    tags = EXCLUDED.tags,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at
            """), {
                'id': item['id'],
                'title': item.get('title', ''),
                'summary': item.get('summary', item.get('content', '')[:200]),
                'content': content,
                'category': item.get('category', 'その他'),
                'tags': tags,
                'status': item.get('status', 'draft'),
                'priority': item.get('priority', 'medium'),
                'project': item.get('project'),
                'owner': item.get('owner', 'システム'),
                'created_at': parse_datetime(item.get('created_at')) or datetime.now(),
                'updated_at': parse_datetime(item.get('updated_at')) or datetime.now(),
                'created_by_id': created_by_id
            })

        if verbose:
            print(f"  - Knowledge: {item.get('title', '')[:50]}")

    if not dry_run:
        # シーケンスをリセット
        session.execute(text("SELECT setval('public.knowledge_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.knowledge))"))
        session.commit()

    print(f"[OK] Migrated {len(items)} knowledge items")


def migrate_sop(session, user_id_map: dict, dry_run: bool, verbose: bool):
    """SOPデータを移行"""
    items = load_json('sop.json')
    details = {d['id']: d for d in load_json('sop_details.json')}

    print(f"\n[INFO] Migrating {len(items)} SOP items...")

    for item in items:
        detail = details.get(item['id'], {})
        content = detail.get('content', item.get('content', ''))

        tags = item.get('tags', [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',')]

        revision_date = parse_date(item.get('revision_date') or item.get('updated_at'))
        if not revision_date:
            revision_date = date.today()

        if not dry_run:
            session.execute(text("""
                INSERT INTO public.sop (id, title, category, version, revision_date, target, tags, content, status, attachments, created_at, updated_at)
                VALUES (:id, :title, :category, :version, :revision_date, :target, :tags, :content, :status, :attachments, :created_at, :updated_at)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    category = EXCLUDED.category,
                    version = EXCLUDED.version,
                    content = EXCLUDED.content,
                    updated_at = EXCLUDED.updated_at
            """), {
                'id': item['id'],
                'title': item.get('title', ''),
                'category': item.get('category', 'その他'),
                'version': item.get('version', '1.0'),
                'revision_date': revision_date,
                'target': item.get('target'),
                'tags': tags,
                'content': content,
                'status': item.get('status', 'active'),
                'attachments': json.dumps(item.get('attachments', [])),
                'created_at': parse_datetime(item.get('created_at')) or datetime.now(),
                'updated_at': parse_datetime(item.get('updated_at')) or datetime.now()
            })

        if verbose:
            print(f"  - SOP: {item.get('title', '')[:50]}")

    if not dry_run:
        session.execute(text("SELECT setval('public.sop_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.sop))"))
        session.commit()

    print(f"[OK] Migrated {len(items)} SOP items")


def migrate_regulations(session, dry_run: bool, verbose: bool):
    """法令・規格データを移行"""
    items = load_json('regulations.json')

    print(f"\n[INFO] Migrating {len(items)} regulations...")

    for item in items:
        revision_date = parse_date(item.get('revision_date') or item.get('updated_at'))
        if not revision_date:
            revision_date = date.today()

        applicable_scope = item.get('applicable_scope', [])
        if isinstance(applicable_scope, str):
            applicable_scope = [s.strip() for s in applicable_scope.split(',')]

        if not dry_run:
            session.execute(text("""
                INSERT INTO public.regulations (id, title, issuer, category, revision_date, applicable_scope, summary, content, status, effective_date, url, created_at, updated_at)
                VALUES (:id, :title, :issuer, :category, :revision_date, :applicable_scope, :summary, :content, :status, :effective_date, :url, :created_at, :updated_at)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    summary = EXCLUDED.summary,
                    updated_at = EXCLUDED.updated_at
            """), {
                'id': item['id'],
                'title': item.get('title', ''),
                'issuer': item.get('issuer', '不明'),
                'category': item.get('category', 'その他'),
                'revision_date': revision_date,
                'applicable_scope': applicable_scope,
                'summary': item.get('summary', ''),
                'content': item.get('content'),
                'status': item.get('status', 'active'),
                'effective_date': parse_date(item.get('effective_date')),
                'url': item.get('url'),
                'created_at': parse_datetime(item.get('created_at')) or datetime.now(),
                'updated_at': parse_datetime(item.get('updated_at')) or datetime.now()
            })

        if verbose:
            print(f"  - Regulation: {item.get('title', '')[:50]}")

    if not dry_run:
        session.execute(text("SELECT setval('public.regulations_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.regulations))"))
        session.commit()

    print(f"[OK] Migrated {len(items)} regulations")


def migrate_incidents(session, user_id_map: dict, dry_run: bool, verbose: bool):
    """インシデントデータを移行"""
    items = load_json('incidents.json')
    details = {d['id']: d for d in load_json('incidents_details.json')}

    print(f"\n[INFO] Migrating {len(items)} incidents...")

    for item in items:
        detail = details.get(item['id'], {})

        incident_date = parse_date(item.get('incident_date') or item.get('date'))
        if not incident_date:
            incident_date = date.today()

        tags = item.get('tags', [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',')]

        involved_parties = item.get('involved_parties', [])
        if isinstance(involved_parties, str):
            involved_parties = [p.strip() for p in involved_parties.split(',')]

        reporter_id = user_id_map.get(item.get('reporter_id'))

        if not dry_run:
            session.execute(text("""
                INSERT INTO public.incidents (id, title, description, project, incident_date, severity, status, corrective_actions, root_cause, tags, location, involved_parties, created_at, updated_at, reporter_id)
                VALUES (:id, :title, :description, :project, :incident_date, :severity, :status, :corrective_actions, :root_cause, :tags, :location, :involved_parties, :created_at, :updated_at, :reporter_id)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at
            """), {
                'id': item['id'],
                'title': item.get('title', ''),
                'description': detail.get('description', item.get('description', '')),
                'project': item.get('project', '不明'),
                'incident_date': incident_date,
                'severity': item.get('severity', 'medium'),
                'status': item.get('status', 'reported'),
                'corrective_actions': json.dumps(detail.get('corrective_actions', item.get('corrective_actions', []))),
                'root_cause': detail.get('root_cause', item.get('root_cause')),
                'tags': tags,
                'location': item.get('location'),
                'involved_parties': involved_parties,
                'created_at': parse_datetime(item.get('created_at')) or datetime.now(),
                'updated_at': parse_datetime(item.get('updated_at')) or datetime.now(),
                'reporter_id': reporter_id
            })

        if verbose:
            print(f"  - Incident: {item.get('title', '')[:50]}")

    if not dry_run:
        session.execute(text("SELECT setval('public.incidents_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.incidents))"))
        session.commit()

    print(f"[OK] Migrated {len(items)} incidents")


def migrate_consultations(session, user_id_map: dict, dry_run: bool, verbose: bool):
    """相談データを移行"""
    items = load_json('consultations.json')
    details = {d['id']: d for d in load_json('consultations_details.json')}

    print(f"\n[INFO] Migrating {len(items)} consultations...")

    for item in items:
        detail = details.get(item['id'], {})

        requester_id = user_id_map.get(item.get('requester_id'))
        expert_id = user_id_map.get(item.get('expert_id'))

        if not dry_run:
            session.execute(text("""
                INSERT INTO public.consultations (id, title, question, category, priority, status, requester_id, expert_id, answer, answered_at, created_at, updated_at)
                VALUES (:id, :title, :question, :category, :priority, :status, :requester_id, :expert_id, :answer, :answered_at, :created_at, :updated_at)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    question = EXCLUDED.question,
                    status = EXCLUDED.status,
                    answer = EXCLUDED.answer,
                    updated_at = EXCLUDED.updated_at
            """), {
                'id': item['id'],
                'title': item.get('title', ''),
                'question': detail.get('question', item.get('question', '')),
                'category': item.get('category', 'その他'),
                'priority': item.get('priority', 'medium'),
                'status': item.get('status', 'pending'),
                'requester_id': requester_id,
                'expert_id': expert_id,
                'answer': detail.get('answer', item.get('answer')),
                'answered_at': parse_datetime(item.get('answered_at')),
                'created_at': parse_datetime(item.get('created_at')) or datetime.now(),
                'updated_at': parse_datetime(item.get('updated_at')) or datetime.now()
            })

        if verbose:
            print(f"  - Consultation: {item.get('title', '')[:50]}")

    if not dry_run:
        session.execute(text("SELECT setval('public.consultations_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.consultations))"))
        session.commit()

    print(f"[OK] Migrated {len(items)} consultations")


def migrate_approvals(session, user_id_map: dict, dry_run: bool, verbose: bool):
    """承認データを移行"""
    items = load_json('approvals.json')

    print(f"\n[INFO] Migrating {len(items)} approvals...")

    for item in items:
        requester_id = user_id_map.get(item.get('requester_id'))
        approver_id = user_id_map.get(item.get('approver_id'))

        if not dry_run:
            session.execute(text("""
                INSERT INTO public.approvals (id, title, type, description, requester_id, status, priority, related_entity_type, related_entity_id, approval_flow, created_at, updated_at, approved_at, approver_id)
                VALUES (:id, :title, :type, :description, :requester_id, :status, :priority, :related_entity_type, :related_entity_id, :approval_flow, :created_at, :updated_at, :approved_at, :approver_id)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at
            """), {
                'id': item['id'],
                'title': item.get('title', ''),
                'type': item.get('type', 'general'),
                'description': item.get('description'),
                'requester_id': requester_id,
                'status': item.get('status', 'pending'),
                'priority': item.get('priority', 'medium'),
                'related_entity_type': item.get('related_entity_type'),
                'related_entity_id': item.get('related_entity_id'),
                'approval_flow': json.dumps(item.get('approval_flow', {})),
                'created_at': parse_datetime(item.get('created_at')) or datetime.now(),
                'updated_at': parse_datetime(item.get('updated_at')) or datetime.now(),
                'approved_at': parse_datetime(item.get('approved_at')),
                'approver_id': approver_id
            })

        if verbose:
            print(f"  - Approval: {item.get('title', '')[:50]}")

    if not dry_run:
        session.execute(text("SELECT setval('public.approvals_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.approvals))"))
        session.commit()

    print(f"[OK] Migrated {len(items)} approvals")


def migrate_notifications(session, dry_run: bool, verbose: bool):
    """通知データを移行"""
    items = load_json('notifications.json')

    print(f"\n[INFO] Migrating {len(items)} notifications...")

    for item in items:
        target_users = item.get('target_users', [])
        if isinstance(target_users, str):
            target_users = [int(u) for u in target_users.split(',') if u.strip().isdigit()]

        target_roles = item.get('target_roles', [])
        if isinstance(target_roles, str):
            target_roles = [r.strip() for r in target_roles.split(',')]

        delivery_channels = item.get('delivery_channels', ['in_app'])
        if isinstance(delivery_channels, str):
            delivery_channels = [c.strip() for c in delivery_channels.split(',')]

        if not dry_run:
            session.execute(text("""
                INSERT INTO public.notifications (id, title, message, type, target_users, target_roles, delivery_channels, related_entity_type, related_entity_id, created_at, sent_at, status)
                VALUES (:id, :title, :message, :type, :target_users, :target_roles, :delivery_channels, :related_entity_type, :related_entity_id, :created_at, :sent_at, :status)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    status = EXCLUDED.status
            """), {
                'id': item['id'],
                'title': item.get('title', ''),
                'message': item.get('message', ''),
                'type': item.get('type', 'info'),
                'target_users': target_users,
                'target_roles': target_roles,
                'delivery_channels': delivery_channels,
                'related_entity_type': item.get('related_entity_type'),
                'related_entity_id': item.get('related_entity_id'),
                'created_at': parse_datetime(item.get('created_at')) or datetime.now(),
                'sent_at': parse_datetime(item.get('sent_at')),
                'status': item.get('status', 'pending')
            })

        if verbose:
            print(f"  - Notification: {item.get('title', '')[:50]}")

    if not dry_run:
        session.execute(text("SELECT setval('public.notifications_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.notifications))"))
        session.commit()

    print(f"[OK] Migrated {len(items)} notifications")


def migrate_access_logs(session, user_id_map: dict, dry_run: bool, verbose: bool):
    """アクセスログを移行（最新1000件のみ）"""
    items = load_json('access_logs.json')

    # 最新1000件のみ移行
    items = sorted(items, key=lambda x: x.get('timestamp', ''), reverse=True)[:1000]

    print(f"\n[INFO] Migrating {len(items)} access logs (latest 1000)...")

    for item in items:
        user_id = user_id_map.get(item.get('user_id'))

        # resource_idを整数に変換（文字列の場合はNone）
        resource_id = item.get('resource_id')
        if resource_id is not None:
            try:
                resource_id = int(resource_id)
            except (ValueError, TypeError):
                resource_id = None

        if not dry_run:
            session.execute(text("""
                INSERT INTO audit.access_logs (user_id, username, action, resource, resource_id, ip_address, user_agent, request_method, request_path, session_id, status, details, changes, created_at)
                VALUES (:user_id, :username, :action, :resource, :resource_id, :ip_address, :user_agent, :request_method, :request_path, :session_id, :status, :details, :changes, :created_at)
            """), {
                'user_id': user_id,
                'username': item.get('username'),
                'action': item.get('action', 'unknown'),
                'resource': item.get('resource'),
                'resource_id': resource_id,
                'ip_address': item.get('ip_address'),
                'user_agent': item.get('user_agent'),
                'request_method': item.get('request_method'),
                'request_path': item.get('request_path'),
                'session_id': item.get('session_id'),
                'status': item.get('status', 'success'),
                'details': json.dumps(item.get('details')) if item.get('details') else None,
                'changes': json.dumps(item.get('changes')) if item.get('changes') else None,
                'created_at': parse_datetime(item.get('timestamp')) or datetime.now()
            })

    if not dry_run:
        session.commit()

    print(f"[OK] Migrated {len(items)} access logs")


def main():
    parser = argparse.ArgumentParser(description='Migrate JSON data to PostgreSQL')
    parser.add_argument('--dry-run', action='store_true', help='Dry run without actual migration')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--database-url', default=None, help='Database URL')
    args = parser.parse_args()

    # データベース接続URL
    database_url = args.database_url or os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:password@localhost:5432/mirai_knowledge_db'
    )

    print("=" * 60)
    print("Mirai Knowledge Systems - JSON to PostgreSQL Migration")
    print("=" * 60)
    print(f"Database: {database_url.split('@')[1] if '@' in database_url else database_url}")
    print(f"Dry Run: {args.dry_run}")
    print(f"Data Directory: {DATA_DIR}")
    print("=" * 60)

    if args.dry_run:
        print("\n[DRY RUN MODE] No actual changes will be made\n")

    # データベース接続
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 接続テスト
        session.execute(text("SELECT 1"))
        print("[OK] Database connection successful")

        # 移行実行
        user_id_map = migrate_users(session, args.dry_run, args.verbose)
        migrate_knowledge(session, user_id_map, args.dry_run, args.verbose)
        migrate_sop(session, user_id_map, args.dry_run, args.verbose)
        migrate_regulations(session, args.dry_run, args.verbose)
        migrate_incidents(session, user_id_map, args.dry_run, args.verbose)
        migrate_consultations(session, user_id_map, args.dry_run, args.verbose)
        migrate_approvals(session, user_id_map, args.dry_run, args.verbose)
        migrate_notifications(session, args.dry_run, args.verbose)
        migrate_access_logs(session, user_id_map, args.dry_run, args.verbose)

        print("\n" + "=" * 60)
        print("[SUCCESS] Migration completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == '__main__':
    main()
