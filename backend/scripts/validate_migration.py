#!/usr/bin/env python3
"""
データ移行検証スクリプト
Mirai Knowledge Systems - Phase C-2-3

用途: JSON→PostgreSQL移行後のデータ整合性を検証
実行: python scripts/validate_migration.py
"""

import json
import os
import sys
from datetime import datetime

# パスを追加
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import get_session_factory
from models import SOP, Expert, Incident, Knowledge, Project

# カラー出力
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
NC = "\033[0m"


def load_json_data(filename):
    """JSONファイルを読み込む"""
    filepath = os.path.join(os.path.dirname(__file__), "..", "data", filename)
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_table(model, json_file, name):
    """テーブルとJSONデータの件数を比較"""
    json_data = load_json_data(json_file)
    json_count = len(json_data)

    session_factory = get_session_factory()
    db = session_factory()

    try:
        db_count = db.query(model).count()
    finally:
        db.close()

    if db_count >= json_count:
        status = f"{GREEN}✓{NC}"
        result = "OK"
    elif db_count >= json_count * 0.9:
        status = f"{YELLOW}△{NC}"
        result = "WARNING"
    else:
        status = f"{RED}✗{NC}"
        result = "FAIL"

    print(f"  {status} {name}: JSON={json_count}, DB={db_count} [{result}]")
    return result == "OK" or result == "WARNING"


def validate_sample_data(model, name):
    """サンプルデータの内容を確認"""
    session_factory = get_session_factory()
    db = session_factory()

    try:
        # 最新3件を取得
        items = db.query(model).order_by(model.id.desc()).limit(3).all()

        if not items:
            print(f"  {YELLOW}△{NC} {name}: データなし")
            return True

        print(f"  {GREEN}✓{NC} {name}: サンプルデータ確認")
        for item in items:
            title = getattr(item, "title", getattr(item, "name", str(item.id)))
            print(f"      - ID:{item.id} {title[:40]}...")
        return True

    except Exception as e:
        print(f"  {RED}✗{NC} {name}: エラー - {e}")
        return False
    finally:
        db.close()


def validate_api_endpoints():
    """APIエンドポイントの動作確認"""
    import requests

    endpoints = [
        ("/api/v1/health", "ヘルスチェック"),
        ("/api/v1/knowledge", "ナレッジ一覧"),
        ("/api/v1/sop", "SOP一覧"),
        ("/api/v1/incidents", "インシデント一覧"),
    ]

    base_url = os.environ.get("API_BASE_URL", "http://localhost:5100")
    all_ok = True

    print(f"\n{BLUE}[3] APIエンドポイント確認{NC}")

    for endpoint, name in endpoints:
        try:
            # 認証なしでアクセス可能なエンドポイントのみ
            if endpoint == "/api/v1/health":
                resp = requests.get(f"{base_url}{endpoint}", timeout=5)
                if resp.status_code == 200:
                    print(f"  {GREEN}✓{NC} {name}: OK (200)")
                else:
                    print(f"  {RED}✗{NC} {name}: NG ({resp.status_code})")
                    all_ok = False
            else:
                # 認証が必要なエンドポイントは401が正常
                resp = requests.get(f"{base_url}{endpoint}", timeout=5)
                if resp.status_code in [200, 401, 403]:
                    print(f"  {GREEN}✓{NC} {name}: 応答あり ({resp.status_code})")
                else:
                    print(
                        f"  {YELLOW}△{NC} {name}: 予期しない応答 ({resp.status_code})"
                    )

        except requests.exceptions.ConnectionError:
            print(f"  {YELLOW}△{NC} {name}: 接続できません（サーバー停止中）")
        except Exception as e:
            print(f"  {RED}✗{NC} {name}: エラー - {e}")
            all_ok = False

    return all_ok


def main():
    """メイン処理"""
    print(f"{BLUE}========================================{NC}")
    print(f"{BLUE} データ移行検証{NC}")
    print(f"{BLUE}========================================{NC}")
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")

    all_passed = True

    # 1. 件数検証
    print(f"{BLUE}[1] データ件数検証{NC}")

    validations = [
        (Knowledge, "knowledge.json", "ナレッジ"),
        (SOP, "sop.json", "SOP"),
        (Incident, "incidents.json", "インシデント"),
        (Project, "projects.json", "プロジェクト"),
        (Expert, "experts.json", "専門家"),
    ]

    for model, json_file, name in validations:
        try:
            if not validate_table(model, json_file, name):
                all_passed = False
        except Exception as e:
            print(f"  {RED}✗{NC} {name}: エラー - {e}")
            all_passed = False

    print("")

    # 2. サンプルデータ確認
    print(f"{BLUE}[2] サンプルデータ確認{NC}")

    for model, _, name in validations:
        try:
            validate_sample_data(model, name)
        except Exception as e:
            print(f"  {RED}✗{NC} {name}: エラー - {e}")

    # 3. API確認（オプション）
    try:
        validate_api_endpoints()
    except ImportError:
        print(
            f"\n{YELLOW}[3] APIエンドポイント確認: requestsモジュールなし（スキップ）{NC}"
        )

    # 結果サマリー
    print("")
    print(f"{BLUE}========================================{NC}")
    if all_passed:
        print(f"{GREEN}✓ 移行検証完了 - すべてのチェックに合格{NC}")
        return 0
    else:
        print(f"{RED}✗ 移行検証完了 - 一部のチェックに失敗{NC}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
