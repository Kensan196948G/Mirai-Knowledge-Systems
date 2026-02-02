#!/usr/bin/env python3
"""
詳細データ（knowledge_details.json等）をPostgreSQLに投入するスクリプト
"""

import json
import os
import sys
from datetime import datetime

# パスを追加
sys.path.insert(0, os.path.dirname(__file__))

from database import get_session_factory
from models import SOP, Consultation, Incident, Knowledge


def parse_datetime(date_str):
    """日付文字列をdatetimeオブジェクトに変換"""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except:
        return datetime.utcnow()


def import_knowledge_details():
    """ナレッジ詳細データの投入"""
    json_path = os.path.join("data", "knowledge_details.json")
    if not os.path.exists(json_path):
        print(f"⚠️  {json_path} が見つかりません。スキップします。")
        return 0

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        print(f"⚠️  {json_path} にデータがありません。")
        return 0

    session_factory = get_session_factory()
    db = session_factory()
    count = 0
    updated = 0

    try:
        for item in data:
            # 既存チェック
            existing = db.query(Knowledge).filter_by(id=item["id"]).first()

            if existing:
                # 既存データを更新（contentが長い場合のみ）
                if len(item.get("content", "")) > len(existing.content or ""):
                    existing.content = item["content"]
                    existing.updated_at = datetime.utcnow()
                    updated += 1
                continue

            # 新規作成
            knowledge = Knowledge(
                id=item["id"],
                title=item["title"],
                summary=item.get("summary", item["title"]),
                content=item.get("content", ""),
                category=item["category"],
                tags=item.get("tags", []),
                status=item.get("status", "approved"),
                priority=item.get("priority", "medium"),
                project=item.get("project", "サンプルプロジェクト"),
                owner=item.get("owner", item.get("created_by", "技術部")),
                created_by_id=item.get("created_by_id", 1),
                updated_by_id=item.get("updated_by_id", 1),
                created_at=parse_datetime(item.get("created_at")),
                updated_at=parse_datetime(item.get("updated_at")),
            )
            db.add(knowledge)
            count += 1

        db.commit()
        print(f"✅ ナレッジ: 新規{count}件、更新{updated}件")
        return count + updated

    except Exception as e:
        db.rollback()
        print(f"❌ ナレッジ投入エラー: {e}")
        raise
    finally:
        db.close()


def import_sop_details():
    """SOP詳細データの投入"""
    json_path = os.path.join("data", "sop_details.json")
    if not os.path.exists(json_path):
        print(f"⚠️  {json_path} が見つかりません。スキップします。")
        return 0

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        print(f"⚠️  {json_path} にデータがありません。")
        return 0

    session_factory = get_session_factory()
    db = session_factory()
    count = 0
    updated = 0

    try:
        for item in data:
            # 既存チェック
            existing = db.query(SOP).filter_by(id=item["id"]).first()

            # stepsからcontentを生成
            content_parts = []
            if "purpose" in item:
                content_parts.append(f"【目的】\n{item['purpose']}\n")
            if "scope" in item:
                content_parts.append(f"【適用範囲】\n{item['scope']}\n")
            if "steps" in item:
                content_parts.append("【作業手順】\n")
                for step in item["steps"]:
                    content_parts.append(
                        f"ステップ{step['step_number']}: {step['description']}\n"
                    )

            content = (
                "\n".join(content_parts) if content_parts else item.get("content", "")
            )

            if existing:
                # 既存データを更新
                if len(content) > len(existing.content or ""):
                    existing.content = content
                    existing.updated_at = datetime.utcnow()
                    updated += 1
                continue

            # 新規作成
            sop = SOP(
                id=item["id"],
                title=item["title"],
                category=item["category"],
                version=item.get("version", "1.0"),
                revision_date=parse_datetime(item.get("revision_date"))
                or datetime.utcnow().date(),
                target=item.get("target", item.get("scope", "")),
                tags=item.get("tags", []),
                content=content,
                status=item.get("status", "active"),
                created_by_id=item.get("created_by_id", 1),
                updated_by_id=item.get("updated_by_id", 1),
                created_at=parse_datetime(item.get("created_at")),
                updated_at=parse_datetime(item.get("updated_at")),
            )
            db.add(sop)
            count += 1

        db.commit()
        print(f"✅ SOP: 新規{count}件、更新{updated}件")
        return count + updated

    except Exception as e:
        db.rollback()
        print(f"❌ SOP投入エラー: {e}")
        raise
    finally:
        db.close()


def import_incident_details():
    """事故レポート詳細データの投入"""
    json_path = os.path.join("data", "incidents_details.json")
    if not os.path.exists(json_path):
        print(f"⚠️  {json_path} が見つかりません。スキップします。")
        return 0

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        print(f"⚠️  {json_path} にデータがありません。")
        return 0

    session_factory = get_session_factory()
    db = session_factory()
    count = 0
    updated = 0

    try:
        for item in data:
            # 既存チェック
            existing = db.query(Incident).filter_by(id=item["id"]).first()

            if existing:
                # 既存データを更新
                if item.get("description") and len(item["description"]) > len(
                    existing.description or ""
                ):
                    existing.description = item["description"]
                    existing.updated_at = datetime.utcnow()
                    updated += 1
                continue

            # 新規作成
            incident_date = parse_datetime(
                item.get("occurred_at") or item.get("incident_date")
            )
            if incident_date:
                incident_date = incident_date.date()
            else:
                incident_date = datetime.utcnow().date()

            incident = Incident(
                id=item["id"],
                title=item["title"],
                description=item.get("description", ""),
                project=item.get("project", "サンプルプロジェクト"),
                incident_date=incident_date,
                severity=item.get("severity", "medium"),
                status=item.get("status", "reported"),
                location=item.get("location"),
                reporter_id=item.get("reporter_id", item.get("reported_by_id", 1)),
                created_at=parse_datetime(item.get("created_at")),
                updated_at=parse_datetime(item.get("updated_at")),
            )
            db.add(incident)
            count += 1

        db.commit()
        print(f"✅ 事故レポート: 新規{count}件、更新{updated}件")
        return count + updated

    except Exception as e:
        db.rollback()
        print(f"❌ 事故レポート投入エラー: {e}")
        raise
    finally:
        db.close()


def main():
    """メイン処理"""
    print("=" * 60)
    print("詳細データ → PostgreSQL 投入")
    print("=" * 60)
    print()

    total = 0

    # ナレッジ詳細データ投入
    total += import_knowledge_details()

    # SOP詳細データ投入
    total += import_sop_details()

    # 事故レポート詳細データ投入
    total += import_incident_details()

    print()
    print("=" * 60)
    print(f"✅ 合計 {total}件のデータを投入・更新しました！")
    print("=" * 60)


if __name__ == "__main__":
    main()
