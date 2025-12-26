"""
JSONデータをPostgreSQLに移行するスクリプト
"""
import os
import sys
import json
from datetime import datetime

# パスを追加
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal
from models import Knowledge, SOP, Regulation, Incident, Consultation, Approval

def parse_datetime(date_str):
    """日付文字列をdatetimeオブジェクトに変換"""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        return datetime.utcnow()

def migrate_knowledge():
    """ナレッジデータの移行"""
    json_path = os.path.join('data', 'knowledge.json')
    if not os.path.exists(json_path):
        print(f"⚠️  {json_path} が見つかりません。スキップします。")
        return 0
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    db = SessionLocal()
    count = 0
    
    try:
        for item in data:
            # 既存チェック
            existing = db.query(Knowledge).filter_by(id=item['id']).first()
            if existing:
                continue
            
            knowledge = Knowledge(
                id=item['id'],
                title=item['title'],
                summary=item['summary'],
                content=item.get('content', item['summary']),
                category=item['category'],
                tags=item.get('tags', []),
                status=item.get('status', 'approved'),
                priority=item.get('priority', 'medium'),
                project=item.get('project'),
                owner=item['owner'],
                created_at=parse_datetime(item.get('created_at')),
                updated_at=parse_datetime(item.get('updated_at'))
            )
            db.add(knowledge)
            count += 1
        
        db.commit()
        print(f"✅ ナレッジ: {count}件を移行しました")
        return count
        
    except Exception as e:
        db.rollback()
        print(f"❌ ナレッジ移行エラー: {e}")
        raise
    finally:
        db.close()

def migrate_sop():
    """SOPデータの移行"""
    json_path = os.path.join('data', 'sop.json')
    if not os.path.exists(json_path):
        print(f"⚠️  {json_path} が見つかりません。スキップします。")
        return 0
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    db = SessionLocal()
    count = 0
    
    try:
        for item in data:
            existing = db.query(SOP).filter_by(id=item['id']).first()
            if existing:
                continue
            
            sop = SOP(
                id=item['id'],
                title=item['title'],
                category=item['category'],
                version=item['version'],
                revision_date=datetime.strptime(item['revision_date'], '%Y-%m-%d').date(),
                target=item.get('target'),
                tags=item.get('tags', []),
                content=item['content'],
                status=item.get('status', 'active'),
                created_at=parse_datetime(item.get('created_at')),
                updated_at=parse_datetime(item.get('updated_at'))
            )
            db.add(sop)
            count += 1
        
        db.commit()
        print(f"✅ SOP: {count}件を移行しました")
        return count
        
    except Exception as e:
        db.rollback()
        print(f"❌ SOP移行エラー: {e}")
        raise
    finally:
        db.close()

def migrate_regulations():
    """法令データの移行"""
    json_path = os.path.join('data', 'regulations.json')
    if not os.path.exists(json_path):
        print(f"⚠️  {json_path} が見つかりません。スキップします。")
        return 0
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    db = SessionLocal()
    count = 0
    
    try:
        for item in data:
            existing = db.query(Regulation).filter_by(id=item['id']).first()
            if existing:
                continue
            
            regulation = Regulation(
                id=item['id'],
                title=item['title'],
                issuer=item['issuer'],
                category=item['category'],
                revision_date=datetime.strptime(item['revision_date'], '%Y-%m-%d').date(),
                applicable_scope=item.get('applicable_scope', []),
                summary=item['summary'],
                content=item.get('content'),
                status=item.get('status', 'active'),
                url=item.get('url'),
                created_at=parse_datetime(item.get('created_at')),
                updated_at=parse_datetime(item.get('updated_at'))
            )
            db.add(regulation)
            count += 1
        
        db.commit()
        print(f"✅ 法令: {count}件を移行しました")
        return count
        
    except Exception as e:
        db.rollback()
        print(f"❌ 法令移行エラー: {e}")
        raise
    finally:
        db.close()

def migrate_incidents():
    """事故レポートデータの移行"""
    json_path = os.path.join('data', 'incidents.json')
    if not os.path.exists(json_path):
        print(f"⚠️  {json_path} が見つかりません。スキップします。")
        return 0
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    db = SessionLocal()
    count = 0
    
    try:
        for item in data:
            existing = db.query(Incident).filter_by(id=item['id']).first()
            if existing:
                continue
            
            incident = Incident(
                id=item['id'],
                title=item['title'],
                description=item['description'],
                project=item['project'],
                incident_date=datetime.strptime(item['date'], '%Y-%m-%d').date(),
                severity=item['severity'],
                status=item.get('status', 'reported'),
                corrective_actions=item.get('corrective_actions'),
                tags=item.get('tags', []),
                created_at=parse_datetime(item.get('created_at'))
            )
            db.add(incident)
            count += 1
        
        db.commit()
        print(f"✅ 事故レポート: {count}件を移行しました")
        return count
        
    except Exception as e:
        db.rollback()
        print(f"❌ 事故レポート移行エラー: {e}")
        raise
    finally:
        db.close()

def migrate_consultations():
    """専門家相談データの移行"""
    json_path = os.path.join('data', 'consultations.json')
    if not os.path.exists(json_path):
        print(f"⚠️  {json_path} が見つかりません。スキップします。")
        return 0
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    db = SessionLocal()
    count = 0
    
    try:
        for item in data:
            existing = db.query(Consultation).filter_by(id=item['id']).first()
            if existing:
                continue
            
            consultation = Consultation(
                id=item['id'],
                title=item['title'],
                question=item['question'],
                category=item['category'],
                priority=item.get('priority', 'medium'),
                status=item.get('status', 'pending'),
                answer=item.get('answer'),
                answered_at=parse_datetime(item.get('updated_at')) if item.get('status') == 'answered' else None,
                created_at=parse_datetime(item.get('created_at')),
                updated_at=parse_datetime(item.get('updated_at'))
            )
            db.add(consultation)
            count += 1
        
        db.commit()
        print(f"✅ 専門家相談: {count}件を移行しました")
        return count
        
    except Exception as e:
        db.rollback()
        print(f"❌ 専門家相談移行エラー: {e}")
        raise
    finally:
        db.close()

def migrate_approvals():
    """承認フローデータの移行"""
    json_path = os.path.join('data', 'approvals.json')
    if not os.path.exists(json_path):
        print(f"⚠️  {json_path} が見つかりません。スキップします。")
        return 0
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    db = SessionLocal()
    count = 0
    
    try:
        for item in data:
            existing = db.query(Approval).filter_by(id=item['id']).first()
            if existing:
                continue
            
            approval = Approval(
                id=item['id'],
                title=item['title'],
                type=item['type'],
                description=item.get('description'),
                status=item.get('status', 'pending'),
                priority=item.get('priority', 'medium'),
                created_at=parse_datetime(item.get('created_at')),
                updated_at=parse_datetime(item.get('updated_at'))
            )
            db.add(approval)
            count += 1
        
        db.commit()
        print(f"✅ 承認フロー: {count}件を移行しました")
        return count
        
    except Exception as e:
        db.rollback()
        print(f"❌ 承認フロー移行エラー: {e}")
        raise
    finally:
        db.close()

def main():
    """メイン処理"""
    print("=" * 60)
    print("JSONデータ → PostgreSQL 移行")
    print("=" * 60)
    
    total = 0
    total += migrate_knowledge()
    total += migrate_sop()
    total += migrate_regulations()
    total += migrate_incidents()
    total += migrate_consultations()
    total += migrate_approvals()
    
    print("\n" + "=" * 60)
    print(f"✅ 合計 {total}件のデータを移行しました！")
    print("=" * 60)

if __name__ == '__main__':
    main()
