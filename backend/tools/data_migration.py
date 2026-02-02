#!/usr/bin/env python3
"""
データ移行ツール
既存データをMirai Knowledge Systemsにインポートするツール

機能:
- CSVファイルからのナレッジインポート
- Excel/CSVファイルからのSOPインポート
- JSONファイルからの一括インポート
- バリデーション機能
- ロールバック機能
- プレビュー機能（ドライラン）
"""

import argparse
import csv
import json
import logging
import os
import shutil
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# プロジェクトルートをPYTHONPATHに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine
from models import SOP, Incident, Knowledge, Regulation, User
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

# ロギング設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DataMigrationError(Exception):
    """データ移行エラー"""

    pass


class ImportResult:
    """インポート結果"""

    def __init__(self):
        self.success_count = 0
        self.error_count = 0
        self.skip_count = 0
        self.errors: List[Dict[str, Any]] = []
        self.backup_id: Optional[str] = None

    def add_success(self):
        self.success_count += 1

    def add_error(self, row_num: int, error: str, data: Dict = None):
        self.error_count += 1
        self.errors.append({"row": row_num, "error": error, "data": data})

    def add_skip(self):
        self.skip_count += 1

    def print_summary(self):
        """結果サマリーを表示"""
        print("\n" + "=" * 60)
        print("インポート結果サマリー")
        print("=" * 60)
        print(f"成功: {self.success_count} 件")
        print(f"エラー: {self.error_count} 件")
        print(f"スキップ: {self.skip_count} 件")
        print(f"合計: {self.success_count + self.error_count + self.skip_count} 件")

        if self.backup_id:
            print(f"\nバックアップID: {self.backup_id}")

        if self.errors:
            print("\nエラー詳細:")
            for err in self.errors[:10]:  # 最初の10件のみ表示
                print(f"  行 {err['row']}: {err['error']}")
            if len(self.errors) > 10:
                print(f"  ... 他 {len(self.errors) - 10} 件のエラー")

        print("=" * 60 + "\n")


class DataValidator:
    """データバリデーター"""

    @staticmethod
    def validate_knowledge(data: Dict) -> tuple[bool, Optional[str]]:
        """ナレッジデータをバリデーション"""
        required_fields = ["title", "summary", "category", "owner"]

        # 必須フィールドチェック
        for field in required_fields:
            if not data.get(field):
                return False, f"必須フィールド '{field}' が未入力です"

        # データ型チェック
        if not isinstance(data.get("title"), str):
            return False, "タイトルは文字列である必要があります"

        # 長さチェック
        if len(data.get("title", "")) > 500:
            return False, "タイトルは500文字以内にしてください"

        if len(data.get("summary", "")) > 2000:
            return False, "概要は2000文字以内にしてください"

        # カテゴリチェック
        valid_categories = [
            "施工計画",
            "品質管理",
            "安全衛生",
            "環境対策",
            "原価管理",
            "出来形管理",
            "その他",
        ]
        if data.get("category") not in valid_categories:
            return False, f"カテゴリは {valid_categories} のいずれかを指定してください"

        return True, None

    @staticmethod
    def validate_sop(data: Dict) -> tuple[bool, Optional[str]]:
        """SOPデータをバリデーション"""
        required_fields = ["title", "category", "version", "revision_date", "content"]

        # 必須フィールドチェック
        for field in required_fields:
            if not data.get(field):
                return False, f"必須フィールド '{field}' が未入力です"

        # 日付チェック
        try:
            if isinstance(data.get("revision_date"), str):
                datetime.strptime(data["revision_date"], "%Y-%m-%d")
        except ValueError:
            return False, "revision_dateは YYYY-MM-DD 形式で指定してください"

        return True, None

    @staticmethod
    def validate_regulation(data: Dict) -> tuple[bool, Optional[str]]:
        """法令データをバリデーション"""
        required_fields = ["title", "issuer", "category", "revision_date", "summary"]

        for field in required_fields:
            if not data.get(field):
                return False, f"必須フィールド '{field}' が未入力です"

        return True, None

    @staticmethod
    def validate_incident(data: Dict) -> tuple[bool, Optional[str]]:
        """事故レポートデータをバリデーション"""
        required_fields = [
            "title",
            "description",
            "project",
            "incident_date",
            "severity",
        ]

        for field in required_fields:
            if not data.get(field):
                return False, f"必須フィールド '{field}' が未入力です"

        # 深刻度チェック
        valid_severities = ["low", "medium", "high", "critical"]
        if data.get("severity") not in valid_severities:
            return False, f"重大度は {valid_severities} のいずれかを指定してください"

        return True, None


class DataMigrationTool:
    """データ移行ツール"""

    def __init__(self, db: Session):
        self.db = db
        self.validator = DataValidator()
        self.backup_dir = Path(__file__).parent / "backups"
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self) -> str:
        """現在のデータをバックアップ"""
        backup_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{backup_id}.json"

        logger.info(f"バックアップを作成中: {backup_path}")

        backup_data = {
            "created_at": datetime.now().isoformat(),
            "knowledge": [],
            "sop": [],
            "regulations": [],
            "incidents": [],
        }

        try:
            # 既存データをバックアップ（効率化：select()使用）
            from sqlalchemy import select

            knowledge_list = self.db.scalars(select(Knowledge)).all()
            for k in knowledge_list:
                backup_data["knowledge"].append(
                    {
                        "id": k.id,
                        "title": k.title,
                        "summary": k.summary,
                        "content": k.content,
                        "category": k.category,
                        "tags": k.tags,
                        "status": k.status,
                        "priority": k.priority,
                        "project": k.project,
                        "owner": k.owner,
                        "created_at": (
                            k.created_at.isoformat() if k.created_at else None
                        ),
                        "updated_at": (
                            k.updated_at.isoformat() if k.updated_at else None
                        ),
                    }
                )

            # SOPなども同様にバックアップ（効率化：select()使用）
            sop_list = self.db.scalars(select(SOP)).all()
            for s in sop_list:
                backup_data["sop"].append(
                    {
                        "id": s.id,
                        "title": s.title,
                        "category": s.category,
                        "version": s.version,
                        "revision_date": (
                            s.revision_date.isoformat() if s.revision_date else None
                        ),
                        "target": s.target,
                        "tags": s.tags,
                        "content": s.content,
                        "status": s.status,
                    }
                )

            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)

            logger.info(f"バックアップ完了: {backup_id}")
            return backup_id

        except Exception as e:
            logger.error(f"バックアップ作成エラー: {e}")
            raise DataMigrationError(f"バックアップ作成に失敗しました: {e}")

    def restore_backup(self, backup_id: str):
        """バックアップから復元"""
        backup_path = self.backup_dir / f"backup_{backup_id}.json"

        if not backup_path.exists():
            raise DataMigrationError(
                f"バックアップファイルが見つかりません: {backup_id}"
            )

        logger.info(f"バックアップから復元中: {backup_id}")

        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                backup_data = json.load(f)

            # 現在のデータを削除
            self.db.query(Knowledge).delete()
            self.db.query(SOP).delete()
            self.db.commit()

            # バックアップデータを復元
            for k_data in backup_data.get("knowledge", []):
                knowledge = Knowledge(
                    id=k_data["id"],
                    title=k_data["title"],
                    summary=k_data["summary"],
                    content=k_data["content"],
                    category=k_data["category"],
                    tags=k_data.get("tags"),
                    status=k_data.get("status", "draft"),
                    priority=k_data.get("priority", "medium"),
                    project=k_data.get("project"),
                    owner=k_data["owner"],
                )
                self.db.add(knowledge)

            self.db.commit()
            logger.info("復元が完了しました")

        except Exception as e:
            self.db.rollback()
            logger.error(f"復元エラー: {e}")
            raise DataMigrationError(f"復元に失敗しました: {e}")

    def import_knowledge_from_csv(
        self, file_path: str, preview: bool = False, create_backup: bool = True
    ) -> ImportResult:
        """CSVファイルからナレッジをインポート"""
        result = ImportResult()

        if not os.path.exists(file_path):
            raise DataMigrationError(f"ファイルが見つかりません: {file_path}")

        # バックアップ作成
        if create_backup and not preview:
            result.backup_id = self.create_backup()

        logger.info(f"CSVファイルを読み込み中: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(
                    reader, start=2
                ):  # ヘッダーを考慮して2から
                    try:
                        # データ準備
                        data = {
                            "title": row.get("title", "").strip(),
                            "summary": row.get("summary", "").strip(),
                            "content": row.get("content", "").strip(),
                            "category": row.get("category", "").strip(),
                            "tags": [
                                t.strip()
                                for t in row.get("tags", "").split(",")
                                if t.strip()
                            ],
                            "status": row.get("status", "draft").strip(),
                            "priority": row.get("priority", "medium").strip(),
                            "project": row.get("project", "").strip() or None,
                            "owner": row.get("owner", "unknown").strip(),
                        }

                        # バリデーション
                        is_valid, error_msg = self.validator.validate_knowledge(data)
                        if not is_valid:
                            result.add_error(row_num, error_msg, data)
                            continue

                        # 重複チェック
                        existing = (
                            self.db.query(Knowledge)
                            .filter_by(title=data["title"], category=data["category"])
                            .first()
                        )

                        if existing:
                            logger.warning(
                                f"行 {row_num}: 重複データをスキップ - {data['title']}"
                            )
                            result.add_skip()
                            continue

                        if preview:
                            logger.info(f"[プレビュー] 行 {row_num}: {data['title']}")
                            result.add_success()
                        else:
                            # データベースに追加
                            knowledge = Knowledge(**data)
                            self.db.add(knowledge)
                            self.db.flush()  # IDを取得するためflush

                            logger.info(
                                f"インポート成功 (ID: {knowledge.id}): {data['title']}"
                            )
                            result.add_success()

                    except Exception as e:
                        logger.error(f"行 {row_num} でエラー: {e}")
                        result.add_error(row_num, str(e), row)
                        continue

            if not preview:
                self.db.commit()
                logger.info("コミット完了")
            else:
                logger.info("プレビューモード - データベースは変更されていません")

        except Exception as e:
            if not preview:
                self.db.rollback()
            logger.error(f"インポートエラー: {e}")
            raise DataMigrationError(f"インポートに失敗しました: {e}")

        return result

    def import_sop_from_csv(
        self, file_path: str, preview: bool = False, create_backup: bool = True
    ) -> ImportResult:
        """CSVファイルからSOPをインポート"""
        result = ImportResult()

        if not os.path.exists(file_path):
            raise DataMigrationError(f"ファイルが見つかりません: {file_path}")

        if create_backup and not preview:
            result.backup_id = self.create_backup()

        logger.info(f"CSVファイルを読み込み中: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, start=2):
                    try:
                        # データ準備
                        revision_date_str = row.get("revision_date", "").strip()
                        revision_date = (
                            datetime.strptime(revision_date_str, "%Y-%m-%d").date()
                            if revision_date_str
                            else date.today()
                        )

                        data = {
                            "title": row.get("title", "").strip(),
                            "category": row.get("category", "").strip(),
                            "version": row.get("version", "1.0").strip(),
                            "revision_date": revision_date,
                            "target": row.get("target", "").strip() or None,
                            "tags": [
                                t.strip()
                                for t in row.get("tags", "").split(",")
                                if t.strip()
                            ],
                            "content": row.get("content", "").strip(),
                            "status": row.get("status", "active").strip(),
                        }

                        # バリデーション
                        is_valid, error_msg = self.validator.validate_sop(data)
                        if not is_valid:
                            result.add_error(row_num, error_msg, data)
                            continue

                        # 重複チェック
                        existing = (
                            self.db.query(SOP)
                            .filter_by(title=data["title"], version=data["version"])
                            .first()
                        )

                        if existing:
                            logger.warning(
                                f"行 {row_num}: 重複データをスキップ - {data['title']} v{data['version']}"
                            )
                            result.add_skip()
                            continue

                        if preview:
                            logger.info(
                                f"[プレビュー] 行 {row_num}: {data['title']} v{data['version']}"
                            )
                            result.add_success()
                        else:
                            sop = SOP(**data)
                            self.db.add(sop)
                            self.db.flush()

                            logger.info(
                                f"インポート成功 (ID: {sop.id}): {data['title']}"
                            )
                            result.add_success()

                    except Exception as e:
                        logger.error(f"行 {row_num} でエラー: {e}")
                        result.add_error(row_num, str(e), row)
                        continue

            if not preview:
                self.db.commit()
                logger.info("コミット完了")
            else:
                logger.info("プレビューモード")

        except Exception as e:
            if not preview:
                self.db.rollback()
            logger.error(f"インポートエラー: {e}")
            raise DataMigrationError(f"インポートに失敗しました: {e}")

        return result

    def import_from_json(
        self, file_path: str, preview: bool = False, create_backup: bool = True
    ) -> ImportResult:
        """JSONファイルから一括インポート"""
        result = ImportResult()

        if not os.path.exists(file_path):
            raise DataMigrationError(f"ファイルが見つかりません: {file_path}")

        if create_backup and not preview:
            result.backup_id = self.create_backup()

        logger.info(f"JSONファイルを読み込み中: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # ナレッジをインポート
            for idx, k_data in enumerate(data.get("knowledge", []), start=1):
                try:
                    is_valid, error_msg = self.validator.validate_knowledge(k_data)
                    if not is_valid:
                        result.add_error(idx, error_msg, k_data)
                        continue

                    if not preview:
                        knowledge = Knowledge(**k_data)
                        self.db.add(knowledge)
                        self.db.flush()

                    result.add_success()

                except Exception as e:
                    result.add_error(idx, str(e), k_data)

            # SOPをインポート
            for idx, s_data in enumerate(data.get("sop", []), start=1):
                try:
                    # 日付を変換
                    if "revision_date" in s_data and isinstance(
                        s_data["revision_date"], str
                    ):
                        s_data["revision_date"] = datetime.strptime(
                            s_data["revision_date"], "%Y-%m-%d"
                        ).date()

                    is_valid, error_msg = self.validator.validate_sop(s_data)
                    if not is_valid:
                        result.add_error(idx, error_msg, s_data)
                        continue

                    if not preview:
                        sop = SOP(**s_data)
                        self.db.add(sop)
                        self.db.flush()

                    result.add_success()

                except Exception as e:
                    result.add_error(idx, str(e), s_data)

            if not preview:
                self.db.commit()
                logger.info("JSONインポート完了")
            else:
                logger.info("プレビューモード")

        except Exception as e:
            if not preview:
                self.db.rollback()
            logger.error(f"JSONインポートエラー: {e}")
            raise DataMigrationError(f"JSONインポートに失敗しました: {e}")

        return result


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="Mirai Knowledge Systems データ移行ツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="サブコマンド")

    # import-knowledge コマンド
    parser_knowledge = subparsers.add_parser(
        "import-knowledge", help="CSVファイルからナレッジをインポート"
    )
    parser_knowledge.add_argument(
        "--file", required=True, help="インポートするCSVファイルのパス"
    )
    parser_knowledge.add_argument(
        "--preview",
        action="store_true",
        help="プレビューモード（実際にはインポートしない）",
    )
    parser_knowledge.add_argument(
        "--no-backup", action="store_true", help="バックアップを作成しない"
    )

    # import-sop コマンド
    parser_sop = subparsers.add_parser(
        "import-sop", help="CSVファイルからSOPをインポート"
    )
    parser_sop.add_argument(
        "--file", required=True, help="インポートするCSVファイルのパス"
    )
    parser_sop.add_argument("--preview", action="store_true", help="プレビューモード")
    parser_sop.add_argument(
        "--no-backup", action="store_true", help="バックアップを作成しない"
    )

    # import-json コマンド
    parser_json = subparsers.add_parser(
        "import-json", help="JSONファイルから一括インポート"
    )
    parser_json.add_argument(
        "--file", required=True, help="インポートするJSONファイルのパス"
    )
    parser_json.add_argument("--preview", action="store_true", help="プレビューモード")
    parser_json.add_argument(
        "--no-backup", action="store_true", help="バックアップを作成しない"
    )

    # rollback コマンド
    parser_rollback = subparsers.add_parser("rollback", help="バックアップから復元")
    parser_rollback.add_argument(
        "--backup-id", required=True, help="バックアップID (例: 20250127_123456)"
    )

    # list-backups コマンド
    parser_list = subparsers.add_parser("list-backups", help="バックアップ一覧を表示")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # データベース接続
    db = SessionLocal()
    tool = DataMigrationTool(db)

    try:
        if args.command == "import-knowledge":
            result = tool.import_knowledge_from_csv(
                args.file, preview=args.preview, create_backup=not args.no_backup
            )
            result.print_summary()

        elif args.command == "import-sop":
            result = tool.import_sop_from_csv(
                args.file, preview=args.preview, create_backup=not args.no_backup
            )
            result.print_summary()

        elif args.command == "import-json":
            result = tool.import_from_json(
                args.file, preview=args.preview, create_backup=not args.no_backup
            )
            result.print_summary()

        elif args.command == "rollback":
            tool.restore_backup(args.backup_id)
            print(f"バックアップ {args.backup_id} から復元しました")

        elif args.command == "list-backups":
            backup_dir = Path(__file__).parent / "backups"
            backups = sorted(backup_dir.glob("backup_*.json"), reverse=True)

            print("\n利用可能なバックアップ:")
            print("=" * 60)
            for backup in backups:
                backup_id = backup.stem.replace("backup_", "")
                size = backup.stat().st_size / 1024  # KB
                mtime = datetime.fromtimestamp(backup.stat().st_mtime)
                print(f"ID: {backup_id}")
                print(f"  作成日時: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"  サイズ: {size:.2f} KB")
                print()
            print("=" * 60 + "\n")

    except DataMigrationError as e:
        logger.error(f"エラー: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"予期しないエラー: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
