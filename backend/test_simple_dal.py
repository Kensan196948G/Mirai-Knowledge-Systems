#!/usr/bin/env python3
"""
DataAccessLayerの簡易テスト（設定不要版）
"""

import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_json(filename):
    """JSONファイルを読み込み"""
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def test_regulation_data():
    """法令データのテスト"""
    print("\n[1] Regulation データテスト")
    data = load_json("regulations.json")
    if not data:
        print("  ✗ データなし")
        return False

    regulation = next((r for r in data if r["id"] == 1), None)
    if regulation:
        print(f"  ✓ ID: {regulation['id']}")
        print(f"  ✓ Title: {regulation['title']}")
        print(f"  ✓ Issuer: {regulation['issuer']}")
        print(f"  ✓ Category: {regulation['category']}")
        return True
    else:
        print("  ✗ ID=1 が見つからない")
        return False


def test_project_data():
    """プロジェクトデータのテスト"""
    print("\n[2] Project データテスト")
    data = load_json("projects.json")
    if not data:
        print("  ✗ データなし")
        return False

    project = next((p for p in data if p["id"] == 1), None)
    if project:
        print(f"  ✓ ID: {project['id']}")
        print(f"  ✓ Name: {project['name']}")
        print(f"  ✓ Status: {project['status']}")
        print(f"  ✓ Members: {len(project.get('members', []))} 人")
        print(f"  ✓ Milestones: {len(project.get('milestones', []))} 件")
        return True
    else:
        print("  ✗ ID=1 が見つからない")
        return False


def test_expert_data():
    """専門家データのテスト"""
    print("\n[3] Expert データテスト")
    data = load_json("experts.json")
    if not data:
        print("  ✗ データなし")
        return False

    expert = next((e for e in data if e["id"] == 1), None)
    if expert:
        print(f"  ✓ ID: {expert['id']}")
        print(f"  ✓ Name: {expert['name']}")
        print(f"  ✓ Email: {expert['email']}")
        print(f"  ✓ Department: {expert['department']}")
        print(f"  ✓ Specialties: {', '.join(expert.get('specialties', []))}")
        return True
    else:
        print("  ✗ ID=1 が見つからない")
        return False


def main():
    """メインテスト"""
    print("=" * 60)
    print("詳細エンドポイントデータ検証")
    print("=" * 60)

    results = []
    results.append(test_regulation_data())
    results.append(test_project_data())
    results.append(test_expert_data())

    print("\n" + "=" * 60)
    if all(results):
        print("全テスト成功 ✓")
        print("=" * 60)
        return 0
    else:
        print("一部テスト失敗 ✗")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit(main())
