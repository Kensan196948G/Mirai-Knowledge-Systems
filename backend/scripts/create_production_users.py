#!/usr/bin/env python3
"""
本番環境用ユーザー作成スクリプト

使用方法:
    python scripts/create_production_users.py

または環境変数でパスワードを指定:
    ADMIN_PASSWORD=セキュアなパスワード python scripts/create_production_users.py
"""

import os
import sys
import json
import secrets
from pathlib import Path

import bcrypt

# バックエンドディレクトリをパスに追加
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# 環境変数から設定を読み込み
DATA_DIR = os.environ.get('MKS_DATA_DIR', str(backend_dir / 'data'))


def hash_password(password: str) -> str:
    """パスワードをbcryptでハッシュ化（app_v2.pyと同じ方式）"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def generate_secure_password(length: int = 16) -> str:
    """セキュアなランダムパスワードを生成"""
    import string
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def load_users() -> list:
    """ユーザーデータを読み込み"""
    users_file = Path(DATA_DIR) / 'users.json'
    if users_file.exists():
        with open(users_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_users(users: list) -> None:
    """ユーザーデータを保存"""
    users_file = Path(DATA_DIR) / 'users.json'
    with open(users_file, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def create_user(username: str, password: str, full_name: str,
                department: str, email: str, roles: list) -> dict:
    """ユーザーを作成"""
    users = load_users()

    # ユーザー名の重複チェック
    for u in users:
        if u['username'] == username:
            print(f"[SKIP] ユーザー '{username}' は既に存在します")
            return None

    # 新しいID
    max_id = max([u.get('id', 0) for u in users], default=0)

    new_user = {
        'id': max_id + 1,
        'username': username,
        'password_hash': hash_password(password),
        'full_name': full_name,
        'department': department,
        'email': email,
        'roles': roles,
        'is_active': True
    }

    users.append(new_user)
    save_users(users)

    return new_user


def main():
    print("=" * 60)
    print("  Mirai Knowledge System - 本番ユーザー作成")
    print("=" * 60)
    print()

    # 既存ユーザーの確認
    users = load_users()
    print(f"現在のユーザー数: {len(users)}")
    for u in users:
        print(f"  - {u['username']} ({u.get('full_name', 'N/A')}) - ロール: {u.get('roles', [])}")
    print()

    # 本番用ユーザーの定義
    # パスワードは環境変数から取得するか、自動生成
    admin_password = os.environ.get('ADMIN_PASSWORD') or generate_secure_password()
    manager_password = os.environ.get('MANAGER_PASSWORD') or generate_secure_password()
    engineer_password = os.environ.get('ENGINEER_PASSWORD') or generate_secure_password()

    production_users = [
        {
            'username': 'system_admin',
            'password': admin_password,
            'full_name': 'システム管理者',
            'department': 'IT部門',
            'email': 'sysadmin@company.local',
            'roles': ['admin']
        },
        {
            'username': 'project_manager',
            'password': manager_password,
            'full_name': 'プロジェクト管理者',
            'department': '建設部門',
            'email': 'pm@company.local',
            'roles': ['manager']
        },
        {
            'username': 'engineer01',
            'password': engineer_password,
            'full_name': '技術者01',
            'department': '技術部門',
            'email': 'engineer01@company.local',
            'roles': ['engineer']
        }
    ]

    print("本番ユーザーを作成中...")
    print()

    created_users = []
    for user_data in production_users:
        result = create_user(
            username=user_data['username'],
            password=user_data['password'],
            full_name=user_data['full_name'],
            department=user_data['department'],
            email=user_data['email'],
            roles=user_data['roles']
        )
        if result:
            created_users.append({
                'username': user_data['username'],
                'password': user_data['password'],
                'roles': user_data['roles']
            })
            print(f"[OK] ユーザー作成: {user_data['username']} ({user_data['full_name']})")

    print()
    print("=" * 60)

    if created_users:
        print("作成されたユーザーの認証情報:")
        print("-" * 60)
        for u in created_users:
            print(f"  ユーザー名: {u['username']}")
            print(f"  パスワード: {u['password']}")
            print(f"  ロール: {', '.join(u['roles'])}")
            print()
        print("-" * 60)
        print("⚠️  これらのパスワードは安全な場所に保管してください！")
        print("⚠️  本番運用前にパスワードを変更することを推奨します。")
    else:
        print("新規ユーザーは作成されませんでした。")

    print()
    print("完了!")


if __name__ == '__main__':
    main()
