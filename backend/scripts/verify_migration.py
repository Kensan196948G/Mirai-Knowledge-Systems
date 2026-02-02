#!/usr/bin/env python3
"""
JSONからPostgreSQLへのマイグレーション結果を検証するスクリプト

使用方法:
    python backend/scripts/verify_migration.py

検証内容:
    1. レコード数の一致確認
    2. データ整合性チェック
    3. インデックスの存在確認
    4. サンプルデータの比較
"""

import json
import os
import sys
from typing import Dict, List, Tuple

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import SessionLocal
from models import (SOP, Approval, Consultation, Incident, Knowledge,
                    Notification, User)
from sqlalchemy import inspect


class MigrationVerifier:
    """マイグレーション検証クラス"""

    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.db = SessionLocal()
        self.errors = []
        self.warnings = []

    def __del__(self):
        """デストラクタでセッションをクローズ"""
        if hasattr(self, "db"):
            self.db.close()

    def load_json(self, filename: str) -> List[Dict]:
        """JSONファイルを読み込み"""
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.exists(filepath):
            self.warnings.append(f"JSONファイルが見つかりません: {filepath}")
            return []

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            self.errors.append(f"JSONファイル読み込みエラー ({filename}): {e}")
            return []

    def verify_record_count(
        self, model, json_filename: str, entity_name: str
    ) -> Tuple[bool, int, int]:
        """
        レコード数を検証

        Args:
            model: SQLAlchemyモデルクラス
            json_filename: JSONファイル名
            entity_name: エンティティ名（表示用）

        Returns:
            (検証成功, JSON件数, DB件数)
        """
        json_data = self.load_json(json_filename)
        json_count = len(json_data)

        try:
            db_count = self.db.query(model).count()
        except Exception as e:
            self.errors.append(f"{entity_name}のDB件数取得エラー: {e}")
            return False, json_count, 0

        if json_count == db_count:
            print(f"✅ {entity_name}: {json_count}件 (JSON) = {db_count}件 (DB)")
            return True, json_count, db_count
        else:
            msg = f"{entity_name}: {json_count}件 (JSON) ≠ {db_count}件 (DB)"
            if db_count == 0:
                self.warnings.append(msg + " - データベースが空です")
                print(f"⚠️  {msg}")
            else:
                self.errors.append(msg)
                print(f"❌ {msg}")
            return False, json_count, db_count

    def verify_data_integrity(
        self, model, json_filename: str, entity_name: str, sample_size: int = 5
    ):
        """
        データ整合性を検証（サンプルデータ比較）

        Args:
            model: SQLAlchemyモデルクラス
            json_filename: JSONファイル名
            entity_name: エンティティ名
            sample_size: サンプルサイズ
        """
        json_data = self.load_json(json_filename)
        if not json_data:
            return

        print(f"\n{entity_name}のデータ整合性チェック（サンプル{sample_size}件）:")
        print("-" * 60)

        sample_data = json_data[:sample_size]
        for item in sample_data:
            item_id = item.get("id")
            if not item_id:
                continue

            try:
                db_record = self.db.query(model).filter(model.id == item_id).first()
                if not db_record:
                    self.errors.append(f"{entity_name} ID={item_id}: DBに存在しません")
                    print(f"❌ ID={item_id}: DBに存在しません")
                    continue

                # 主要フィールドを比較
                if hasattr(db_record, "title"):
                    if item.get("title") == db_record.title:
                        print(f"✅ ID={item_id}: タイトル一致")
                    else:
                        self.warnings.append(
                            f"{entity_name} ID={item_id}: タイトル不一致"
                        )
                        print(f"⚠️  ID={item_id}: タイトル不一致")

            except Exception as e:
                self.errors.append(f"{entity_name} ID={item_id}の検証エラー: {e}")
                print(f"❌ ID={item_id}: 検証エラー - {e}")

    def verify_indexes(self):
        """インデックスの存在を確認"""
        print("\nインデックス検証:")
        print("-" * 60)

        expected_indexes = {
            "knowledge": [
                "idx_knowledge_category",
                "idx_knowledge_status",
                "idx_knowledge_updated",
                "idx_knowledge_title",
                "idx_knowledge_owner",
                "idx_knowledge_project",
            ],
            "sop": [
                "idx_sop_category",
                "idx_sop_status",
                "idx_sop_title",
                "idx_sop_version",
            ],
            "incidents": [
                "idx_incident_project",
                "idx_incident_severity",
                "idx_incident_status",
                "idx_incident_date",
            ],
        }

        inspector = inspect(self.db.bind)

        for table_name, expected_idx_list in expected_indexes.items():
            # publicスキーマのテーブルを指定
            try:
                indexes = inspector.get_indexes(table_name, schema="public")
                index_names = [idx["name"] for idx in indexes]

                for expected_idx in expected_idx_list:
                    if expected_idx in index_names:
                        print(f"✅ {table_name}.{expected_idx}")
                    else:
                        self.warnings.append(
                            f"インデックス未作成: {table_name}.{expected_idx}"
                        )
                        print(f"⚠️  {table_name}.{expected_idx} - 未作成")
            except Exception as e:
                self.warnings.append(
                    f"テーブル {table_name} のインデックス確認エラー: {e}"
                )
                print(f"⚠️  {table_name}: インデックス確認エラー")

    def verify_foreign_keys(self):
        """外部キー制約の確認"""
        print("\n外部キー検証:")
        print("-" * 60)

        inspector = inspect(self.db.bind)

        tables_with_fk = ["knowledge", "sop", "incidents", "consultations", "approvals"]

        for table_name in tables_with_fk:
            try:
                foreign_keys = inspector.get_foreign_keys(table_name, schema="public")
                if foreign_keys:
                    print(f"✅ {table_name}: {len(foreign_keys)}個の外部キー")
                    for fk in foreign_keys:
                        print(
                            f"   - {fk['name']}: {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}"
                        )
                else:
                    print(f"ℹ️  {table_name}: 外部キーなし")
            except Exception as e:
                self.warnings.append(f"テーブル {table_name} の外部キー確認エラー: {e}")

    def run_verification(self):
        """全検証を実行"""
        print("=" * 60)
        print("PostgreSQL マイグレーション検証")
        print("=" * 60)
        print()

        # レコード数検証
        print("レコード数検証:")
        print("-" * 60)
        verifications = [
            (Knowledge, "knowledge.json", "ナレッジ"),
            (SOP, "sop.json", "SOP"),
            (Incident, "incidents.json", "インシデント"),
            (Consultation, "consultations.json", "相談"),
            (Approval, "approvals.json", "承認"),
            (Notification, "notifications.json", "通知"),
            (User, "users.json", "ユーザー"),
        ]

        total_json = 0
        total_db = 0
        for model, json_file, name in verifications:
            success, json_count, db_count = self.verify_record_count(
                model, json_file, name
            )
            total_json += json_count
            total_db += db_count

        print()
        print(f"合計: {total_json}件 (JSON) vs {total_db}件 (DB)")
        print()

        # データ整合性検証（主要エンティティのみ）
        self.verify_data_integrity(
            Knowledge, "knowledge.json", "ナレッジ", sample_size=5
        )
        self.verify_data_integrity(SOP, "sop.json", "SOP", sample_size=3)

        # インデックス検証
        self.verify_indexes()

        # 外部キー検証
        self.verify_foreign_keys()

        # 結果サマリー
        print()
        print("=" * 60)
        print("検証結果サマリー")
        print("=" * 60)

        if self.errors:
            print(f"\n❌ エラー: {len(self.errors)}件")
            for error in self.errors:
                print(f"   - {error}")

        if self.warnings:
            print(f"\n⚠️  警告: {len(self.warnings)}件")
            for warning in self.warnings:
                print(f"   - {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ すべての検証に合格しました")
            return True
        elif not self.errors:
            print("\n✅ 検証完了（警告あり）")
            return True
        else:
            print("\n❌ 検証に失敗しました")
            return False


def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(description="PostgreSQLマイグレーション検証")
    parser.add_argument("--data-dir", default="data", help="JSONデータディレクトリ")
    args = parser.parse_args()

    verifier = MigrationVerifier(data_dir=args.data_dir)
    success = verifier.run_verification()

    print()
    print("=" * 60)
    if success:
        print("検証完了")
    else:
        print("検証失敗 - 上記のエラーを確認してください")
    print("=" * 60)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
