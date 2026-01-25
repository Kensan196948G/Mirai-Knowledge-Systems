#!/usr/bin/env python3
"""
サンプルデータ大量生成スクリプト
"""
import json
import random
from datetime import datetime, timedelta

def generate_knowledge_data(count=50):
    """ナレッジデータ生成"""
    categories = ['施工計画', '品質管理', '安全衛生', '環境対策', '原価管理', '出来形管理']
    projects = ['東北橋梁補修 (B-03)', '首都高速更新 (K-12)', '河川護岸整備 (R-07)',
                '砂防堰堤工事 (S-15)', '道路舗装 (D-09)']
    owners = ['田中太郎', '山田花子', '鈴木一郎', '佐藤次郎', '高橋三郎']

    knowledge_list = []

    templates = [
        {'title': 'コンクリート打設の温度管理手順 No.{}', 'summary': '寒冷地におけるコンクリート打設時の温度管理フロー',
         'content': '打設量180m3 / 連続8時間想定。外気温が5℃以下の場合は保温養生を実施。温度記録は2時間ごと。',
         'tags': ['コンクリート', '温度管理', '寒冷地', '品質確保']},
        {'title': '砂防堰堤 基礎掘削の安全対策 No.{}', 'summary': '急傾斜地における掘削作業の安全管理手順',
         'content': '掘削深さ3m以上の場合は土留め工を設置。法面勾配1:1.5以下を維持。毎日の点検を義務化。',
         'tags': ['砂防', '掘削', '安全管理', '土留め']},
        {'title': '鋼橋塗装 塗膜剥離の品質確認 No.{}', 'summary': '塗装前の塗膜剥離作業における品質管理',
         'content': 'ブラスト処理後の表面粗さ測定。ISO規格Sa2.5相当。塗装は剥離後4時間以内。',
         'tags': ['鋼橋', '塗装', '品質管理', 'ブラスト']},
        {'title': '施工計画書の承認手順 No.{}', 'summary': '施工計画書作成から承認までのワークフロー',
         'content': '作成→部門確認→品質保証確認→監理技術者承認→発注者提出の5段階。各段階3営業日以内。',
         'tags': ['施工計画', '承認フロー', 'ワークフロー']},
        {'title': '河川護岸 環境配慮事項 No.{}', 'summary': '護岸工事における環境保全措置',
         'content': '生息魚類の産卵期（4-6月）は工事を避ける。濁水処理装置の設置。水質測定を週1回実施。',
         'tags': ['河川', '護岸', '環境対策', '生態系保全']}
    ]

    for i in range(1, count + 1):
        template = random.choice(templates)
        created_date = datetime.now() - timedelta(days=random.randint(0, 365))

        knowledge_list.append({
            'id': i,
            'title': template['title'].format(i),
            'summary': template['summary'],
            'content': template['content'],
            'category': random.choice(categories),
            'tags': template['tags'],
            'status': random.choice(['draft', 'approved', 'approved', 'approved']),  # 75%承認済み
            'created_at': created_date.isoformat(),
            'updated_at': (created_date + timedelta(days=random.randint(0, 30))).isoformat(),
            'owner': random.choice(owners),
            'project': random.choice(projects),
            'priority': random.choice(['low', 'medium', 'medium', 'high']),
            'created_by_id': random.randint(1, 5)
        })

    return knowledge_list

def generate_sop_data(count=30):
    """SOPデータ生成"""
    sop_list = []

    templates = [
        {'title': 'コンクリート打設作業標準 SOP-{}', 'category': '施工', 'target': '全現場',
         'content': '1. 材料確認 2. 配合確認 3. スランプ試験 4. 打設 5. 養生 6. 強度試験',
         'tags': ['コンクリート', '打設', '品質管理']},
        {'title': '足場組立安全手順 SOP-{}', 'category': '安全', 'target': '高所作業',
         'content': '1. 地盤確認 2. 材料点検 3. 組立 4. 点検（日常・定期） 5. 解体',
         'tags': ['足場', '安全', '高所作業']},
        {'title': '測量管理標準 SOP-{}', 'category': '出来形', 'target': '全工種',
         'content': '1. 基準点確認 2. 測量実施 3. 精度確認 4. 記録保管',
         'tags': ['測量', '出来形', '精度管理']}
    ]

    for i in range(1, count + 1):
        template = random.choice(templates)
        revision_date = datetime.now() - timedelta(days=random.randint(0, 180))

        sop_list.append({
            'id': i,
            'title': template['title'].format(str(i).zfill(3)),
            'category': template['category'],
            'target': template['target'],
            'content': template['content'],
            'tags': template['tags'],
            'revision_date': revision_date.isoformat(),
            'version': f'v{random.randint(1, 5)}.{random.randint(0, 9)}'
        })

    return sop_list

def generate_incidents_data(count=20):
    """事故・ヒヤリデータ生成"""
    incidents_list = []

    templates = [
        {'title': '資材落下ヒヤリハット No.{}', 'description': 'クレーン作業中に吊り荷が揺れ、作業員の近くに落下しそうになった',
         'severity': 'medium', 'corrective_actions': ['玉掛けワイヤー点検強化', '作業半径内立入禁止徹底'],
         'tags': ['クレーン', 'ヒヤリハット', '資材']},
        {'title': '転落事故 No.{}', 'description': '足場端部から作業員が転落。安全帯未使用',
         'severity': 'high', 'corrective_actions': ['安全帯着用の徹底指導', '足場端部の手すり増設', '朝礼で注意喚起'],
         'tags': ['転落', '足場', '安全帯']},
        {'title': '設備損傷 No.{}', 'description': 'バックホウが既設配管に接触し損傷',
         'severity': 'medium', 'corrective_actions': ['埋設物確認の徹底', '試掘実施', '作業手順見直し'],
         'tags': ['設備損傷', '埋設物', 'バックホウ']}
    ]

    projects = ['東北橋梁補修 (B-03)', '首都高速更新 (K-12)', '河川護岸整備 (R-07)']
    reporters = ['田中太郎', '山田花子', '鈴木一郎']

    for i in range(1, count + 1):
        template = random.choice(templates)
        incident_date = datetime.now() - timedelta(days=random.randint(0, 90))

        incidents_list.append({
            'id': i,
            'title': template['title'].format(i),
            'description': template['description'],
            'project': random.choice(projects),
            'date': incident_date.strftime('%Y-%m-%d'),
            'severity': template['severity'],
            'status': random.choice(['investigating', 'resolved', 'resolved']),
            'corrective_actions': template['corrective_actions'],
            'tags': template['tags'],
            'created_at': incident_date.isoformat(),
            'reporter': random.choice(reporters)
        })

    return incidents_list

def generate_consultations_data(count=15):
    """専門家相談データ生成"""
    consultations_list = []

    templates = [
        {'title': '鉄筋配筋の施工方法について', 'content': 'D29鉄筋の配筋間隔が狭く、コンクリート充填が困難です。推奨する施工方法をご教示ください。',
         'expert': '技術本部 構造設計', 'status': 'answered'},
        {'title': '地盤改良の工法選定', 'content': '軟弱地盤（N値2-3）における最適な地盤改良工法を相談したいです。',
         'expert': '技術本部 地盤工学', 'status': 'pending'},
        {'title': '環境基準値の解釈', 'content': '騒音規制法の基準値について、測定方法を確認したいです。',
         'expert': '安全衛生室', 'status': 'answered'}
    ]

    for i in range(1, count + 1):
        template = random.choice(templates)
        created_date = datetime.now() - timedelta(days=random.randint(0, 60))

        consultations_list.append({
            'id': i,
            'title': template['title'] + f' (相談{i})',
            'content': template['content'],
            'project': random.choice(['東北橋梁補修 (B-03)', '河川護岸整備 (R-07)']),
            'expert': template['expert'],
            'status': template['status'],
            'priority': random.choice(['medium', 'high']),
            'created_at': created_date.isoformat(),
            'requester': random.choice(['田中太郎', '山田花子'])
        })

    return consultations_list

if __name__ == '__main__':
    import os

    data_dir = 'data'

    # ナレッジデータ生成（50件）
    knowledge_data = generate_knowledge_data(50)
    with open(os.path.join(data_dir, 'knowledge.json'), 'w', encoding='utf-8') as f:
        json.dump(knowledge_data, f, ensure_ascii=False, indent=2)
    print(f'✅ ナレッジデータ生成: {len(knowledge_data)}件')

    # SOPデータ生成（30件）
    sop_data = generate_sop_data(30)
    with open(os.path.join(data_dir, 'sop.json'), 'w', encoding='utf-8') as f:
        json.dump(sop_data, f, ensure_ascii=False, indent=2)
    print(f'✅ SOPデータ生成: {len(sop_data)}件')

    # 事故・ヒヤリデータ生成（20件）
    incidents_data = generate_incidents_data(20)
    with open(os.path.join(data_dir, 'incidents.json'), 'w', encoding='utf-8') as f:
        json.dump(incidents_data, f, ensure_ascii=False, indent=2)
    print(f'✅ 事故・ヒヤリデータ生成: {len(incidents_data)}件')

    # 専門家相談データ生成（15件）
    consultations_data = generate_consultations_data(15)
    with open(os.path.join(data_dir, 'consultations.json'), 'w', encoding='utf-8') as f:
        json.dump(consultations_data, f, ensure_ascii=False, indent=2)
    print(f'✅ 専門家相談データ生成: {len(consultations_data)}件')

    print('\n=== サンプルデータ生成完了 ===')
