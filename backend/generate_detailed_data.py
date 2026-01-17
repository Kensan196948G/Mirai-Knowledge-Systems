#!/usr/bin/env python3
"""
詳細ページ表示用の大量ダミーデータ生成スクリプト
"""
import json
import random
from datetime import datetime, timedelta
import hashlib

# 共通データ
CATEGORIES = ['施工計画', '品質管理', '安全衛生', '環境対策', '原価管理', '出来形管理', '設計変更', '工程管理']
PROJECTS = [
    '東北橋梁補修 (B-03)', '首都高速更新 (K-12)', '河川護岸整備 (R-07)',
    '砂防堰堤工事 (S-15)', '道路舗装 (D-09)', 'トンネル補修 (T-21)',
    '擁壁設置 (Y-18)', '防波堤建設 (H-06)', '上下水道更新 (W-14)',
    '橋梁耐震補強 (E-11)'
]
USERS = [
    '田中太郎', '山田花子', '鈴木一郎', '佐藤次郎', '高橋三郎',
    '伊藤美咲', '渡辺健', '中村愛', '小林誠', '加藤優子',
    '吉田直樹', '山本さくら', '松本大輔', '井上麗子', '木村拓也',
    '林真由美', '斎藤隆', '清水恵', '森川将太', '池田香織'
]
TAGS_POOL = [
    'コンクリート', '鉄筋', '型枠', '足場', '測量', '安全管理', '品質管理',
    '環境対策', '施工計画', 'クレーン', 'バックホウ', '塗装', 'ブラスト',
    '地盤改良', '土留め', '掘削', '盛土', '舗装', '橋梁', '護岸',
    '砂防', 'トンネル', '擁壁', '防波堤', '上下水道', '耐震', '補修',
    '維持管理', '点検', 'ICT', 'BIM/CIM', 'ドローン', '3D測量'
]

def generate_long_content(base_text, min_length=2000):
    """長文コンテンツ生成"""
    paragraphs = [
        "工事概要: 本工事は、老朽化した構造物の補修・補強を目的とした大規模改修工事である。施工期間は12ヶ月を予定しており、供用中の施設であることから、交通規制を最小限に抑えた施工計画が求められる。",
        "施工方法: 既設構造物の撤去は、周辺環境への影響を考慮し、低騒音・低振動工法を採用する。また、産業廃棄物の適切な分別・処理を徹底し、リサイクル率90%以上を目標とする。",
        "品質管理: コンクリートの配合設計は、所要の強度・耐久性を確保するため、事前に配合試験を実施する。打設時は温度管理を徹底し、気象条件に応じた養生方法を選定する。",
        "安全管理: 高所作業における墜落・転落災害防止のため、作業床の設置、安全帯の使用を徹底する。また、重機との接触災害防止のため、誘導員の配置、作業区域の明確化を図る。",
        "環境対策: 粉塵飛散防止のため、散水設備を設置し、適宜散水を実施する。騒音・振動については、定期的な測定を行い、基準値超過が認められた場合は、速やかに対策を講じる。",
        "工程管理: クリティカルパスを明確にし、重点管理項目について進捗管理を徹底する。天候不良等による工程遅延リスクに対しては、予備日を確保し、柔軟な工程調整を行う。",
        "原価管理: 予算管理を徹底し、月次で実行予算との差異分析を実施する。コスト削減については、VE提案を積極的に推進し、品質を維持しつつ経済性の向上を図る。",
        "出来形管理: 出来形測定は、基準点測量による精度管理を徹底し、許容範囲内に収まるよう施工する。測定結果は速やかに記録し、トレーサビリティを確保する。",
        "技術的検討事項: 施工条件の制約から、従来工法の適用が困難な箇所については、新技術の導入を検討する。適用にあたっては、事前に試験施工を実施し、品質・安全性を確認する。",
        "協議事項: 設計図書と現地条件の相違が確認された場合は、速やかに発注者と協議を行い、適切な対応方針を決定する。協議内容は記録を残し、関係者間で情報共有を図る。",
        "教訓・改善点: 過去の類似工事における課題を分析し、本工事に活かす改善策を立案する。特に、施工手順の最適化、資材調達の効率化、品質管理の強化に重点を置く。",
        "まとめ: 本工事の成功には、計画段階での十分な検討、施工段階での確実な管理、そして全ての関係者の協力が不可欠である。安全第一を基本理念とし、高品質な施工を実現する。"
    ]

    content = base_text + "\n\n"
    while len(content) < min_length:
        content += random.choice(paragraphs) + "\n\n"

    return content

def generate_knowledge_details(count=100):
    """ナレッジ詳細データ生成（100件）"""
    knowledge_list = []

    templates = [
        {
            'title': 'コンクリート打設の温度管理手順 No.{}',
            'summary': '寒冷地におけるコンクリート打設時の温度管理フロー',
            'base_content': '【目的】\n寒冷期におけるコンクリート打設において、所要の強度発現を確保するための温度管理手順を定める。\n\n【適用範囲】\n日平均気温が4℃以下となる期間の全てのコンクリート打設作業に適用する。'
        },
        {
            'title': '砂防堰堤 基礎掘削の安全対策 No.{}',
            'summary': '急傾斜地における掘削作業の安全管理手順',
            'base_content': '【目的】\n急傾斜地での基礎掘削作業における安全を確保し、崩壊・転落災害を防止する。\n\n【適用範囲】\n傾斜角30度以上の斜面における掘削作業に適用する。'
        },
        {
            'title': '鋼橋塗装 塗膜剥離の品質確認 No.{}',
            'summary': '塗装前の塗膜剥離作業における品質管理',
            'base_content': '【目的】\n既設鋼橋の塗装塗替工事において、適切な塗膜剥離を行い、新設塗膜の密着性を確保する。\n\n【適用範囲】\n全ての鋼橋塗装工事に適用する。'
        },
        {
            'title': 'ICT活用工事の施工管理 No.{}',
            'summary': 'ドローン・3D測量を活用した施工管理手法',
            'base_content': '【目的】\nICT技術を活用し、施工管理の効率化・高度化を図る。\n\n【適用範囲】\n土工事・舗装工事等のICT活用工事に適用する。'
        },
        {
            'title': 'BIM/CIM適用工事のデータ管理 No.{}',
            'summary': '3次元モデルを活用した施工計画と維持管理',
            'base_content': '【目的】\nBIM/CIMモデルを活用し、設計から施工、維持管理まで一貫したデータ連携を実現する。\n\n【適用範囲】\n橋梁・トンネル等の構造物工事に適用する。'
        }
    ]

    for i in range(1, count + 1):
        template = random.choice(templates)
        created_date = datetime.now() - timedelta(days=random.randint(1, 365))
        updated_date = created_date + timedelta(days=random.randint(1, 60))

        # コメント生成
        comments = []
        for c in range(random.randint(3, 5)):
            comment_date = created_date + timedelta(days=random.randint(1, 30))
            comments.append({
                'id': c + 1,
                'user': random.choice(USERS),
                'content': random.choice([
                    '非常に参考になりました。次回の工事で活用させていただきます。',
                    '類似の事例を経験したことがあります。この手順は有効だと思います。',
                    '写真や図面があるとより分かりやすいと思います。',
                    '他の現場でも同様の課題がありました。展開していきたいです。',
                    '具体的な数値基準が示されており、実務に活かせそうです。'
                ]),
                'created_at': comment_date.isoformat(),
                'likes': random.randint(0, 15)
            })

        # 編集履歴
        edit_history = []
        for e in range(random.randint(2, 3)):
            edit_date = created_date + timedelta(days=e * 10)
            edit_history.append({
                'version': e + 1,
                'edited_by': random.choice(USERS),
                'edited_at': edit_date.isoformat(),
                'changes': random.choice([
                    '本文の追記・修正',
                    '図表の追加',
                    '参考資料の更新',
                    '誤字脱字の修正',
                    'タグの追加'
                ])
            })

        # 関連ナレッジID
        related_ids = random.sample(range(1, count + 1), min(random.randint(5, 10), count - 1))
        related_ids = [rid for rid in related_ids if rid != i]

        tags = random.sample(TAGS_POOL, random.randint(5, 10))

        knowledge_list.append({
            'id': i,
            'title': template['title'].format(i),
            'summary': template['summary'],
            'content': generate_long_content(template['base_content'], 2000),
            'category': random.choice(CATEGORIES),
            'tags': tags,
            'created_by': random.choice(USERS),
            'created_at': created_date.isoformat(),
            'updated_at': updated_date.isoformat(),
            'views': random.randint(10, 500),
            'likes': random.randint(0, 50),
            'related_knowledge_ids': related_ids[:random.randint(5, 10)],
            'comments': comments,
            'edit_history': edit_history,
            'project': random.choice(PROJECTS),
            'status': random.choice(['published', 'published', 'published', 'draft'])
        })

    return knowledge_list

def generate_sop_details(count=50):
    """SOP詳細データ生成（50件）"""
    sop_list = []

    templates = [
        {
            'title': 'コンクリート打設作業標準 SOP-{}',
            'category': '施工',
            'purpose': 'コンクリート打設作業における品質確保と安全性の向上'
        },
        {
            'title': '足場組立・解体作業標準 SOP-{}',
            'category': '安全',
            'purpose': '足場の組立・解体作業における墜落災害の防止'
        },
        {
            'title': '測量作業標準 SOP-{}',
            'category': '出来形',
            'purpose': '正確な出来形管理のための測量作業手順の標準化'
        }
    ]

    for i in range(1, count + 1):
        template = random.choice(templates)
        revision_date = datetime.now() - timedelta(days=random.randint(0, 180))

        # 手順生成（10-20ステップ）
        steps = []
        step_count = random.randint(10, 20)
        step_templates = [
            '作業準備: 必要な資機材を確認し、作業エリアを設定する',
            '安全確認: 作業環境の安全性を確認し、危険箇所にバリケードを設置する',
            '測定・計測: 基準点から測量を実施し、施工位置を確定する',
            '材料確認: 使用材料の品質を確認し、不適合品は使用しない',
            '施工実施: 承認された施工計画に基づき、作業を実施する',
            '品質検査: 施工後、品質基準に適合しているか検査を実施する',
            '記録作成: 施工記録、写真、測定データを整理し保管する',
            '後片付け: 使用した資機材を整理し、作業エリアを清掃する'
        ]

        for s in range(1, step_count + 1):
            steps.append({
                'step_number': s,
                'title': f'ステップ {s}',
                'description': random.choice(step_templates),
                'responsible': random.choice(['作業員', '主任技術者', '監理技術者', '安全担当者']),
                'estimated_time': f'{random.randint(10, 120)}分'
            })

        # チェックリスト
        checklist = []
        checklist_items = [
            '作業計画書の承認を受けたか',
            '作業員への作業内容説明を実施したか',
            '安全保護具の着用を確認したか',
            '使用機械の始業前点検を実施したか',
            '作業エリアの立入禁止措置を講じたか',
            '気象条件を確認し、作業可否を判断したか',
            '緊急連絡体制を確認したか',
            '産業廃棄物の分別方法を確認したか'
        ]

        for idx, item in enumerate(random.sample(checklist_items, random.randint(5, 8)), 1):
            checklist.append({
                'id': idx,
                'item': item,
                'required': random.choice([True, True, False])
            })

        # 注意事項
        precautions = [
            '悪天候時（降雨、強風、雷）は作業を中止する',
            '作業半径内への第三者の立入を禁止する',
            '異常を発見した場合は直ちに監督者に報告する',
            '定められた保護具を必ず着用する',
            '作業終了後は使用資機材の点検・整備を実施する'
        ]

        # 改訂履歴
        revision_history = []
        for r in range(random.randint(2, 5)):
            rev_date = revision_date - timedelta(days=r * 60)
            revision_history.append({
                'version': f'v{random.randint(1, 3)}.{r}',
                'date': rev_date.strftime('%Y-%m-%d'),
                'author': random.choice(USERS),
                'changes': random.choice([
                    '手順の追加・修正',
                    '安全対策の強化',
                    'チェックリストの更新',
                    '参考資料の追加',
                    '様式の変更'
                ])
            })

        # 関連SOP
        related_sops = random.sample(range(1, count + 1), min(random.randint(3, 6), count - 1))
        related_sops = [rid for rid in related_sops if rid != i]

        # 参考資料
        references = [
            {'title': '建設工事公衆災害防止対策要綱', 'url': 'https://example.com/ref1'},
            {'title': '労働安全衛生規則', 'url': 'https://example.com/ref2'},
            {'title': 'コンクリート標準示方書', 'url': 'https://example.com/ref3'},
            {'title': '土木工事安全施工技術指針', 'url': 'https://example.com/ref4'}
        ]

        sop_list.append({
            'id': i,
            'title': template['title'].format(str(i).zfill(3)),
            'category': template['category'],
            'purpose': template['purpose'],
            'scope': '本SOPは全ての関連工事に適用する',
            'steps': steps,
            'checklist': checklist,
            'precautions': random.sample(precautions, random.randint(3, 5)),
            'revision_date': revision_date.isoformat(),
            'version': f'v{random.randint(1, 5)}.{random.randint(0, 9)}',
            'revision_history': revision_history,
            'related_sops': related_sops,
            'references': random.sample(references, random.randint(2, 4)),
            'tags': random.sample(TAGS_POOL, random.randint(3, 6))
        })

    return sop_list

def generate_incidents_details(count=30):
    """事故レポート詳細データ生成（30件）"""
    incidents_list = []

    templates = [
        {
            'title': '資材落下ヒヤリハット No.{}',
            'type': 'near_miss',
            'description': 'クレーン作業中に吊り荷が揺れ、作業員の近くに落下しそうになった',
            'severity': 'medium'
        },
        {
            'title': '転落事故 No.{}',
            'type': 'accident',
            'description': '足場端部から作業員が転落。安全帯未使用',
            'severity': 'high'
        },
        {
            'title': '設備損傷 No.{}',
            'type': 'damage',
            'description': 'バックホウが既設配管に接触し損傷',
            'severity': 'medium'
        }
    ]

    for i in range(1, count + 1):
        template = random.choice(templates)
        incident_date = datetime.now() - timedelta(days=random.randint(1, 90))

        # タイムライン（5-10イベント）
        timeline = []
        event_templates = [
            '作業開始',
            '異常発生',
            '作業中止',
            '現場確認',
            '応急処置',
            '関係者への報告',
            '原因調査開始',
            '対策検討会議',
            '是正措置実施',
            '完了確認'
        ]

        for t in range(random.randint(5, 10)):
            event_time = incident_date + timedelta(hours=t)
            timeline.append({
                'time': event_time.isoformat(),
                'event': random.choice(event_templates),
                'details': f'イベント詳細 {t + 1}'
            })

        # 原因分析
        root_causes = random.sample([
            '安全教育の不足',
            '作業手順の不遵守',
            '設備・資材の不具合',
            '環境条件の変化',
            'コミュニケーション不足',
            '確認不足',
            '経験・技術不足'
        ], random.randint(2, 3))

        # 是正措置（3-5項目）
        corrective_actions = []
        action_templates = [
            '作業手順の見直しと周知徹底',
            '安全教育の実施（対象: 全作業員）',
            '設備・資材の点検強化',
            '作業環境の改善',
            'KY活動の実施',
            '類似事例の水平展開',
            '管理体制の強化'
        ]

        for idx, action in enumerate(random.sample(action_templates, random.randint(3, 5)), 1):
            corrective_actions.append({
                'id': idx,
                'action': action,
                'responsible': random.choice(USERS),
                'deadline': (incident_date + timedelta(days=random.randint(7, 30))).strftime('%Y-%m-%d'),
                'status': random.choice(['completed', 'in_progress', 'pending'])
            })

        # ステータス履歴
        status_history = [
            {'status': 'reported', 'date': incident_date.isoformat(), 'user': random.choice(USERS)},
            {'status': 'investigating', 'date': (incident_date + timedelta(hours=2)).isoformat(), 'user': random.choice(USERS)},
        ]

        if random.random() > 0.3:
            status_history.append({
                'status': 'action_plan',
                'date': (incident_date + timedelta(days=3)).isoformat(),
                'user': random.choice(USERS)
            })

        if random.random() > 0.5:
            status_history.append({
                'status': 'resolved',
                'date': (incident_date + timedelta(days=14)).isoformat(),
                'user': random.choice(USERS)
            })

        # 関連写真
        photos = []
        for p in range(random.randint(2, 5)):
            photos.append({
                'id': p + 1,
                'url': f'https://placehold.co/800x600/png?text=Incident+Photo+{p+1}',
                'caption': f'現場写真 {p + 1}',
                'taken_at': (incident_date + timedelta(minutes=p * 10)).isoformat()
            })

        incidents_list.append({
            'id': i,
            'title': template['title'].format(i),
            'type': template['type'],
            'description': generate_long_content(template['description'], 1000),
            'occurred_at': incident_date.isoformat(),
            'location': f'{random.choice(PROJECTS)} - {random.choice(["A工区", "B工区", "C工区"])}',
            'severity': template['severity'],
            'status': status_history[-1]['status'],
            'reporter': random.choice(USERS),
            'timeline': timeline,
            'root_causes': root_causes,
            'corrective_actions': corrective_actions,
            'status_history': status_history,
            'photos': photos,
            'involved_parties': random.sample(USERS, random.randint(2, 4)),
            'tags': random.sample(TAGS_POOL, random.randint(3, 6))
        })

    return incidents_list

def generate_consultations_details(count=40):
    """専門家相談詳細データ生成（40件）"""
    consultations_list = []

    question_templates = [
        {
            'title': '鉄筋配筋の施工方法について',
            'content': 'D29鉄筋の配筋間隔が狭く、コンクリート充填が困難です。推奨する施工方法をご教示ください。',
            'category': '施工計画'
        },
        {
            'title': '地盤改良の工法選定',
            'content': '軟弱地盤（N値2-3）における最適な地盤改良工法を相談したいです。',
            'category': '品質管理'
        },
        {
            'title': '環境基準値の解釈',
            'content': '騒音規制法の基準値について、測定方法を確認したいです。',
            'category': '環境対策'
        },
        {
            'title': 'ICT建機の活用方法',
            'content': '3D測量データを建機に取り込む手順について教えてください。',
            'category': '施工計画'
        }
    ]

    for i in range(1, count + 1):
        template = random.choice(question_templates)
        created_date = datetime.now() - timedelta(days=random.randint(1, 60))

        # 回答生成（2-5件）
        answers = []
        for a in range(random.randint(2, 5)):
            answer_date = created_date + timedelta(hours=random.randint(2, 48))
            is_best = (a == 0 and random.random() > 0.3)

            answer_content = generate_long_content(
                f'ご質問ありがとうございます。{template["category"]}の専門家として回答いたします。',
                random.randint(500, 1500)
            )

            answers.append({
                'id': a + 1,
                'expert': random.choice(USERS),
                'expert_title': random.choice(['技術本部 構造設計', '技術本部 地盤工学', '安全衛生室', 'ICT推進室']),
                'content': answer_content,
                'created_at': answer_date.isoformat(),
                'helpful_count': random.randint(0, 25),
                'is_best_answer': is_best,
                'attachments': [
                    {'name': f'参考資料_{a+1}.pdf', 'url': f'https://example.com/file{a+1}.pdf'}
                ] if random.random() > 0.7 else []
            })

        # ベストアンサーがない場合は最初の回答をベストアンサーに
        if not any(a['is_best_answer'] for a in answers):
            if answers:
                answers[0]['is_best_answer'] = True

        consultations_list.append({
            'id': i,
            'title': f'{template["title"]} (相談{i})',
            'content': template['content'],
            'category': template['category'],
            'tags': random.sample(TAGS_POOL, random.randint(3, 6)),
            'requester': random.choice(USERS),
            'project': random.choice(PROJECTS),
            'created_at': created_date.isoformat(),
            'status': 'answered' if len(answers) > 0 else 'pending',
            'priority': random.choice(['low', 'medium', 'high']),
            'views': random.randint(5, 200),
            'helpful_count': random.randint(0, 30),
            'answers': answers
        })

    return consultations_list

def generate_projects(count=20):
    """プロジェクトデータ生成（20件）"""
    projects_list = []

    work_sections = ['1工区', '2工区', '3工区', 'A工区', 'B工区', 'C工区']
    work_types = ['土工', '基礎工', 'コンクリート工', '鋼構造物工', '舗装工', '付属施設工']

    for i in range(1, count + 1):
        start_date = datetime.now() - timedelta(days=random.randint(30, 365))
        duration_days = random.randint(90, 730)
        end_date = start_date + timedelta(days=duration_days)

        # 担当者（3-5名）
        members = []
        roles = ['監理技術者', '主任技術者', '安全管理者', '品質管理者', '施工管理者']
        for m in range(random.randint(3, 5)):
            members.append({
                'name': random.choice(USERS),
                'role': roles[m] if m < len(roles) else '技術者',
                'email': f'user{m}@example.com'
            })

        # マイルストーン（5-10個）
        milestones = []
        milestone_templates = [
            '施工計画書承認',
            '仮設工完了',
            '基礎工完了',
            '主体工完了',
            '仕上げ工完了',
            '検査実施',
            '是正完了',
            '竣工',
            '引き渡し',
            '供用開始'
        ]

        for m in range(random.randint(5, 10)):
            milestone_date = start_date + timedelta(days=int(duration_days * (m + 1) / 10))
            milestones.append({
                'id': m + 1,
                'title': milestone_templates[m] if m < len(milestone_templates) else f'マイルストーン{m+1}',
                'target_date': milestone_date.strftime('%Y-%m-%d'),
                'status': random.choice(['completed', 'in_progress', 'pending']),
                'completion_date': milestone_date.strftime('%Y-%m-%d') if random.random() > 0.5 else None
            })

        progress = random.randint(10, 100)

        projects_list.append({
            'id': i,
            'name': PROJECTS[i % len(PROJECTS)],
            'description': f'本工事は、{random.choice(["老朽化", "機能向上", "耐震補強", "更新"])}を目的とした{random.choice(work_types)}である。',
            'work_section': random.choice(work_sections),
            'work_type': random.choice(work_types),
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'progress': progress,
            'budget': random.randint(50000, 500000) * 1000,
            'members': members,
            'milestones': milestones,
            'status': random.choice(['planning', 'in_progress', 'in_progress', 'completed']),
            'tags': random.sample(TAGS_POOL, random.randint(3, 5))
        })

    return projects_list

def generate_experts(count=20):
    """専門家データ生成（20人）"""
    experts_list = []

    specialties = [
        '構造設計', '地盤工学', '環境工学', 'コンクリート工学', '鋼構造',
        '施工計画', '品質管理', '安全管理', '測量', 'ICT/BIM',
        '維持管理', '橋梁工学', 'トンネル工学', '舗装工学', '水理学'
    ]

    departments = [
        '技術本部', '設計部', '施工管理部', '品質保証部', '安全衛生室',
        'ICT推進室', '環境対策室', '研究開発部'
    ]

    for i in range(1, count + 1):
        expert_specialties = random.sample(specialties, random.randint(2, 4))

        experts_list.append({
            'id': i,
            'name': USERS[i % len(USERS)],
            'email': f'expert{i}@example.com',
            'department': random.choice(departments),
            'specialties': expert_specialties,
            'online': random.choice([True, False]),
            'answer_count': random.randint(5, 150),
            'best_answer_count': random.randint(1, 50),
            'rating': round(random.uniform(3.5, 5.0), 1),
            'expert_categories': random.sample(CATEGORIES, random.randint(2, 4)),
            'bio': f'{", ".join(expert_specialties)}の専門家として、{random.randint(5, 20)}年の実務経験があります。',
            'certifications': random.sample([
                '技術士（建設部門）',
                '一級土木施工管理技士',
                'コンクリート診断士',
                'RCCM',
                '労働安全コンサルタント'
            ], random.randint(1, 3))
        })

    return experts_list

def main():
    """メイン処理"""
    import os

    data_dir = '/mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/data'

    print('=== 詳細ページ表示用ダミーデータ生成開始 ===\n')

    # 1. ナレッジ詳細データ（100件）
    print('ナレッジ詳細データ生成中...')
    knowledge_data = generate_knowledge_details(100)
    with open(os.path.join(data_dir, 'knowledge_details.json'), 'w', encoding='utf-8') as f:
        json.dump(knowledge_data, f, ensure_ascii=False, indent=2)
    print(f'✅ ナレッジ詳細データ: {len(knowledge_data)}件\n')

    # 2. SOP詳細データ（50件）
    print('SOP詳細データ生成中...')
    sop_data = generate_sop_details(50)
    with open(os.path.join(data_dir, 'sop_details.json'), 'w', encoding='utf-8') as f:
        json.dump(sop_data, f, ensure_ascii=False, indent=2)
    print(f'✅ SOP詳細データ: {len(sop_data)}件\n')

    # 3. 事故レポート詳細データ（30件）
    print('事故レポート詳細データ生成中...')
    incidents_data = generate_incidents_details(30)
    with open(os.path.join(data_dir, 'incidents_details.json'), 'w', encoding='utf-8') as f:
        json.dump(incidents_data, f, ensure_ascii=False, indent=2)
    print(f'✅ 事故レポート詳細データ: {len(incidents_data)}件\n')

    # 4. 専門家相談詳細データ（40件）
    print('専門家相談詳細データ生成中...')
    consultations_data = generate_consultations_details(40)
    with open(os.path.join(data_dir, 'consultations_details.json'), 'w', encoding='utf-8') as f:
        json.dump(consultations_data, f, ensure_ascii=False, indent=2)
    print(f'✅ 専門家相談詳細データ: {len(consultations_data)}件\n')

    # 5. プロジェクトデータ（20件）
    print('プロジェクトデータ生成中...')
    projects_data = generate_projects(20)
    with open(os.path.join(data_dir, 'projects.json'), 'w', encoding='utf-8') as f:
        json.dump(projects_data, f, ensure_ascii=False, indent=2)
    print(f'✅ プロジェクトデータ: {len(projects_data)}件\n')

    # 6. 専門家データ（20人）
    print('専門家データ生成中...')
    experts_data = generate_experts(20)
    with open(os.path.join(data_dir, 'experts.json'), 'w', encoding='utf-8') as f:
        json.dump(experts_data, f, ensure_ascii=False, indent=2)
    print(f'✅ 専門家データ: {len(experts_data)}件\n')

    print('=== すべてのデータ生成完了 ===')
    print(f'\n生成されたファイル:')
    print(f'  - {data_dir}/knowledge_details.json')
    print(f'  - {data_dir}/sop_details.json')
    print(f'  - {data_dir}/incidents_details.json')
    print(f'  - {data_dir}/consultations_details.json')
    print(f'  - {data_dir}/projects.json')
    print(f'  - {data_dir}/experts.json')

if __name__ == '__main__':
    main()
