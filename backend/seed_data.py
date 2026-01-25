"""
データベース初期データ投入スクリプト
"""
import os
import sys
from datetime import datetime, date

# パスを追加
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, init_db
from models import User, Role, Permission, UserRole, RolePermission

def seed_roles_and_permissions():
    """役割と権限の初期データを投入"""
    db = SessionLocal()
    
    try:
        # 既存データがあればスキップ
        if db.query(Role).count() > 0:
            print("⚠️  既に役割データが存在します。スキップします。")
            return
        
        # 役割の作成
        roles = [
            Role(name='admin', description='システム管理者'),
            Role(name='construction_manager', description='施工管理'),
            Role(name='quality_assurance', description='品質保証'),
            Role(name='safety_officer', description='安全衛生'),
            Role(name='technical_dept', description='技術本部'),
            Role(name='site_manager', description='現場所長'),
            Role(name='partner_company', description='協力会社（閲覧のみ）')
        ]
        
        for role in roles:
            db.add(role)
        
        db.commit()
        print(f"✅ {len(roles)}件の役割を作成しました")
        
        # 権限の作成
        permissions = [
            # ナレッジ
            Permission(name='knowledge.create', resource='knowledge', action='create', description='ナレッジ登録'),
            Permission(name='knowledge.read', resource='knowledge', action='read', description='ナレッジ閲覧'),
            Permission(name='knowledge.update', resource='knowledge', action='update', description='ナレッジ編集'),
            Permission(name='knowledge.delete', resource='knowledge', action='delete', description='ナレッジ削除'),
            Permission(name='knowledge.approve', resource='knowledge', action='approve', description='ナレッジ承認'),
            
            # SOP
            Permission(name='sop.read', resource='sop', action='read', description='SOP閲覧'),
            Permission(name='sop.update', resource='sop', action='update', description='SOP編集'),
            
            # 事故レポート
            Permission(name='incident.create', resource='incident', action='create', description='事故レポート登録'),
            Permission(name='incident.read', resource='incident', action='read', description='事故レポート閲覧'),
            Permission(name='incident.update', resource='incident', action='update', description='事故レポート更新'),
            
            # 専門家相談
            Permission(name='consultation.create', resource='consultation', action='create', description='相談起案'),
            Permission(name='consultation.answer', resource='consultation', action='answer', description='相談回答'),
            
            # 承認
            Permission(name='approval.execute', resource='approval', action='approve', description='承認実行'),
            Permission(name='approval.read', resource='approval', action='read', description='承認フロー閲覧'),
            
           # 通知
            Permission(name='notification.send', resource='notification', action='send', description='通知送信'),
            Permission(name='notification.read', resource='notification', action='read', description='通知閲覧'),
        ]
        
        for perm in permissions:
            db.add(perm)
        
        db.commit()
        print(f"✅ {len(permissions)}件の権限を作成しました")
        
        # 役割-権限の関連付け
        
        # 管理者：全権限（SQLAlchemy 2.0 select使用）
        from sqlalchemy import select
        admin_role = db.scalar(select(Role).filter_by(name='admin'))
        all_permissions = db.scalars(select(Permission)).all()
        for perm in all_permissions:
            db.add(RolePermission(role_id=admin_role.id, permission_id=perm.id))

        # 施工管理：読み取り＋作成（SQLAlchemy 2.0 select使用）
        cm_role = db.scalar(select(Role).filter_by(name='construction_manager'))
        cm_perms = db.scalars(
            select(Permission).filter(
                Permission.name.in_([
                    'knowledge.create', 'knowledge.read', 'knowledge.update',
                    'sop.read',
                    'incident.create', 'incident.read',
                    'consultation.create',
                    'approval.read',
                    'notification.read'
                ])
            )
        ).all()
        for perm in cm_perms:
            db.add(RolePermission(role_id=cm_role.id, permission_id=perm.id))

        # 協力会社：閲覧のみ（SQLAlchemy 2.0 select使用）
        partner_role = db.scalar(select(Role).filter_by(name='partner_company'))
        partner_perms = db.scalars(
            select(Permission).filter(Permission.action == 'read')
        ).all()
        for perm in partner_perms:
            db.add(RolePermission(role_id=partner_role.id, permission_id=perm.id))
        
        db.commit()
        print("✅ 役割-権限の関連付けを完了しました")
        
    except Exception as e:
        db.rollback()
        print(f"❌ エラーが発生しました: {e}")
        raise
    finally:
        db.close()


def seed_demo_users():
    """デモユーザーの作成"""
    db = SessionLocal()
    
    try:
        # 既存データがあればスキップ
        if db.query(User).count() > 0:
            print("⚠️  既にユーザーデータが存在します。スキップします。")
            return
        
        # デモユーザーの作成
        admin_role = db.query(Role).filter_by(name='admin').first()
        cm_role = db.query(Role).filter_by(name='construction_manager').first()
        
        users = [
            {
                'user': User(
                    username='admin',
                    email='admin@example.com',
                    full_name='管理者',
                    department='システム管理部',
                    position='管理者'
                ),
                'password': 'admin123',
                'role': admin_role
            },
            {
                'user': User(
                    username='yamada',
                    email='yamada@example.com',
                    full_name='山田太郎',
                    department='施工管理',
                    position='主任'
                ),
                'password': 'yamada123',
                'role': cm_role
            },
            {
                'user': User(
                    username='suzuki',
                    email='suzuki@example.com',
                    full_name='鈴木花子',
                    department='品質保証',
                    position='課長'
                ),
                'password': 'suzuki123',
                'role': db.query(Role).filter_by(name='quality_assurance').first()
            }
        ]
        
        for user_data in users:
            user = user_data['user']
            user.set_password(user_data['password'])
            db.add(user)
            db.flush()  # IDを取得
            
            # 役割を関連付け
            db.add(UserRole(user_id=user.id, role_id=user_data['role'].id))
        
        db.commit()
        print(f"✅ {len(users)}件のデモユーザーを作成しました")
        print("\n📝 デモユーザー情報:")
        for user_data in users:
            print(f"  - {user_data['user'].username} / {user_data['password']}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ エラーが発生しました: {e}")
        raise
    finally:
        db.close()


def main():
    """メイン処理"""
    print("=" * 60)
    print("データベース初期化とシードデータ投入")
    print("=" * 60)
    
    # データベース初期化
    print("\n1. データベーステーブルを作成中...")
    init_db()
    
    # 役割と権限のシード
    print("\n2. 役割と権限を作成中...")
    seed_roles_and_permissions()
    
    # デモユーザーのシード
    print("\n3. デモユーザーを作成中...")
    seed_demo_users()
    
    print("\n" + "=" * 60)
    print("✅ 初期化が完了しました！")
    print("=" * 60)


if __name__ == '__main__':
    main()
