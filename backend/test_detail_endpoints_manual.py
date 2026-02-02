#!/usr/bin/env python3
"""
詳細エンドポイントの手動テストスクリプト
"""

import json
import os
import sys

# 環境変数を設定（テスト用）
os.environ["MKS_ENV"] = "development"
os.environ["MKS_SECRET_KEY"] = "test-secret-key-for-manual-testing"
os.environ["MKS_USE_POSTGRESQL"] = "false"

# パスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_access import DataAccessLayer


def test_data_access_layer():
    """DataAccessLayerのメソッドをテスト"""
    print("=" * 60)
    print("DataAccessLayer メソッドテスト")
    print("=" * 60)

    # JSONベースでテスト
    dal = DataAccessLayer(use_postgresql=False)

    # 1. Regulation詳細取得
    print("\n[1] Regulation詳細取得 (ID=1)")
    regulation = dal.get_regulation_by_id(1)
    if regulation:
        print(f"  ✓ ID: {regulation['id']}")
        print(f"  ✓ Title: {regulation['title']}")
        print(f"  ✓ Issuer: {regulation['issuer']}")
        print(f"  ✓ Category: {regulation['category']}")
    else:
        print("  ✗ Not found")
        return False

    # 2. Project詳細取得
    print("\n[2] Project詳細取得 (ID=1)")
    project = dal.get_project_by_id(1)
    if project:
        print(f"  ✓ ID: {project['id']}")
        print(f"  ✓ Name: {project['name']}")
        print(f"  ✓ Description: {project['description'][:50]}...")
        print(f"  ✓ Status: {project['status']}")
        print(f"  ✓ Members: {len(project.get('members', []))} 人")
        print(f"  ✓ Milestones: {len(project.get('milestones', []))} 件")
    else:
        print("  ✗ Not found")
        return False

    # 3. Expert詳細取得
    print("\n[3] Expert詳細取得 (ID=1)")
    expert = dal.get_expert_by_id(1)
    if expert:
        print(f"  ✓ ID: {expert['id']}")
        print(f"  ✓ Name: {expert['name']}")
        print(f"  ✓ Email: {expert['email']}")
        print(f"  ✓ Department: {expert['department']}")
        print(f"  ✓ Specialties: {', '.join(expert.get('specialties', []))}")
        print(f"  ✓ Online: {'はい' if expert.get('online') else 'いいえ'}")
        print(f"  ✓ Rating: {expert.get('rating', 0):.1f}")
    else:
        print("  ✗ Not found")
        return False

    # 4. 存在しないIDのテスト
    print("\n[4] 存在しないID (ID=99999) のテスト")
    regulation_none = dal.get_regulation_by_id(99999)
    project_none = dal.get_project_by_id(99999)
    expert_none = dal.get_expert_by_id(99999)

    if regulation_none is None and project_none is None and expert_none is None:
        print("  ✓ 全てNoneを返す（正常）")
    else:
        print("  ✗ 想定外の戻り値")
        return False

    # 5. 複数IDの取得テスト
    print("\n[5] 複数IDの取得テスト")
    for i in range(1, 4):
        reg = dal.get_regulation_by_id(i)
        proj = dal.get_project_by_id(i)
        exp = dal.get_expert_by_id(i)

        if reg and proj and exp:
            print(f"  ✓ ID={i}: Regulation, Project, Expert 全て取得成功")
        else:
            print(f"  - ID={i}: 一部データなし")

    print("\n" + "=" * 60)
    print("全テスト完了 ✓")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_data_access_layer()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ エラー発生: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
