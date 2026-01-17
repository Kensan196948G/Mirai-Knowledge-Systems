#!/usr/bin/env python3
"""
adminユーザーのパスワードをリセットするスクリプト
"""
import os
import sys
from bcrypt import hashpw, gensalt

sys.path.insert(0, os.path.dirname(__file__))

from database import get_session_factory
from models import User

def reset_admin_password(password='admin123'):
    """adminユーザーのパスワードをリセット"""
    session_factory = get_session_factory()
    db = session_factory()

    try:
        # adminユーザーを取得
        admin = db.query(User).filter_by(username='admin').first()

        if not admin:
            print("❌ adminユーザーが見つかりません")
            return False

        # パスワードハッシュ生成
        password_hash = hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')

        # パスワード更新
        admin.password_hash = password_hash
        db.commit()

        print(f"✅ adminユーザーのパスワードを '{password}' に設定しました")
        print(f"   ユーザー名: {admin.username}")
        print(f"   フルネーム: {admin.full_name}")
        return True

    except Exception as e:
        db.rollback()
        print(f"❌ エラー: {e}")
        return False
    finally:
        db.close()

if __name__ == '__main__':
    reset_admin_password()
