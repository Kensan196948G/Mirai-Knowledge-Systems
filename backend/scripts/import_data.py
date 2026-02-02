#!/usr/bin/env python3
"""
データインポートスクリプト

各種データソースからMirai Knowledge Systemsへデータをインポートします。

サポート形式:
- CSV (カンマ区切り)
- Excel (.xlsx, .xls)
- JSON

使用方法:
    python scripts/import_data.py --source file.csv --target knowledge
    python scripts/import_data.py --source file.xlsx --target sop --sheet "Sheet1"
    python scripts/import_data.py --source data.json --target incidents

対象テーブル:
    knowledge, sop, regulations, incidents, consultations
"""

import argparse
import csv
import json
import os
import sys
from datetime import date, datetime
from typing import Any, Dict, List, Optional

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
except ImportError:
    print("Error: SQLAlchemy required. Install: pip install sqlalchemy")
    sys.exit(1)


class DataImporter:
    """データインポートクラス"""

    # テーブルごとの必須カラムと型定義
    TABLE_SCHEMAS = {
        "knowledge": {
            "required": ["title", "summary", "category", "owner"],
            "optional": ["content", "tags", "status", "priority", "project"],
            "defaults": {"status": "draft", "priority": "medium"},
        },
        "sop": {
            "required": ["title", "category", "version", "revision_date", "content"],
            "optional": ["target", "tags", "status", "attachments"],
            "defaults": {"status": "active"},
        },
        "regulations": {
            "required": ["title", "issuer", "category", "revision_date", "summary"],
            "optional": [
                "content",
                "applicable_scope",
                "status",
                "effective_date",
                "url",
            ],
            "defaults": {"status": "active"},
        },
        "incidents": {
            "required": [
                "title",
                "description",
                "project",
                "incident_date",
                "severity",
            ],
            "optional": [
                "status",
                "corrective_actions",
                "root_cause",
                "tags",
                "location",
                "involved_parties",
            ],
            "defaults": {"status": "reported"},
        },
        "consultations": {
            "required": ["title", "question", "category"],
            "optional": ["priority", "status", "answer", "answered_at"],
            "defaults": {"status": "pending", "priority": "medium"},
        },
    }

    def __init__(self, database_url: str, dry_run: bool = False, verbose: bool = False):
        self.database_url = database_url
        self.dry_run = dry_run
        self.verbose = verbose
        self.engine = create_engine(database_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.imported_count = 0
        self.error_count = 0
        self.errors: List[Dict] = []

    def log(self, message: str, level: str = "INFO"):
        """ログ出力"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = "[DRY-RUN] " if self.dry_run else ""
        print(f"[{timestamp}] [{level}] {prefix}{message}")

    def log_verbose(self, message: str):
        """詳細ログ"""
        if self.verbose:
            self.log(message, "DEBUG")

    def read_csv(self, filepath: str, encoding: str = "utf-8") -> List[Dict]:
        """CSVファイルを読み込む"""
        self.log(f"CSVファイルを読み込み中: {filepath}")
        records = []

        # エンコーディング自動検出
        encodings = [encoding, "utf-8-sig", "shift_jis", "cp932", "euc-jp"]

        for enc in encodings:
            try:
                with open(filepath, "r", encoding=enc, newline="") as f:
                    reader = csv.DictReader(f)
                    records = list(reader)
                self.log_verbose(f"エンコーディング: {enc}")
                break
            except UnicodeDecodeError:
                continue

        if not records:
            raise ValueError(f"ファイルを読み込めませんでした: {filepath}")

        self.log(f"読み込み件数: {len(records)}")
        return records

    def read_excel(self, filepath: str, sheet_name: Optional[str] = None) -> List[Dict]:
        """Excelファイルを読み込む"""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas and openpyxl required. Install: pip install pandas openpyxl"
            )

        self.log(f"Excelファイルを読み込み中: {filepath}")

        if sheet_name:
            df = pd.read_excel(filepath, sheet_name=sheet_name)
        else:
            df = pd.read_excel(filepath)

        # NaN を None に変換
        df = df.where(pd.notnull(df), None)

        records = df.to_dict("records")
        self.log(f"読み込み件数: {len(records)}")
        return records

    def read_json(self, filepath: str) -> List[Dict]:
        """JSONファイルを読み込む"""
        self.log(f"JSONファイルを読み込み中: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            records = data
        elif isinstance(data, dict) and "data" in data:
            records = data["data"]
        else:
            records = [data]

        self.log(f"読み込み件数: {len(records)}")
        return records

    def validate_record(self, record: Dict, target: str) -> tuple[bool, List[str]]:
        """レコードのバリデーション"""
        errors = []
        schema = self.TABLE_SCHEMAS.get(target)

        if not schema:
            errors.append(f"不明なテーブル: {target}")
            return False, errors

        # 必須フィールドチェック
        for field in schema["required"]:
            if (
                field not in record
                or record[field] is None
                or str(record[field]).strip() == ""
            ):
                errors.append(f"必須フィールドがありません: {field}")

        return len(errors) == 0, errors

    def transform_record(self, record: Dict, target: str) -> Dict:
        """レコードの変換"""
        schema = self.TABLE_SCHEMAS.get(target, {})
        defaults = schema.get("defaults", {})

        # デフォルト値適用
        for key, default_value in defaults.items():
            if key not in record or record[key] is None:
                record[key] = default_value

        # 日付フィールドの変換
        date_fields = [
            "revision_date",
            "incident_date",
            "effective_date",
            "answered_at",
        ]
        for field in date_fields:
            if field in record and record[field]:
                record[field] = self.parse_date(record[field])

        # 配列フィールドの変換
        array_fields = ["tags", "applicable_scope", "involved_parties"]
        for field in array_fields:
            if field in record and record[field]:
                if isinstance(record[field], str):
                    record[field] = [s.strip() for s in record[field].split(",")]

        # JSONフィールドの変換
        json_fields = ["corrective_actions", "attachments"]
        for field in json_fields:
            if field in record and record[field]:
                if isinstance(record[field], str):
                    try:
                        record[field] = json.loads(record[field])
                    except json.JSONDecodeError:
                        record[field] = {"text": record[field]}

        return record

    def parse_date(self, value: Any) -> Optional[date]:
        """日付のパース"""
        if value is None:
            return None

        if isinstance(value, date):
            return value

        if isinstance(value, datetime):
            return value.date()

        str_value = str(value).strip()
        if not str_value:
            return None

        # 複数のフォーマットを試行
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y年%m月%d日",
            "%d/%m/%Y",
            "%m/%d/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(str_value, fmt).date()
            except ValueError:
                continue

        self.log_verbose(f"日付パース失敗: {value}")
        return None

    def insert_record(self, record: Dict, target: str) -> bool:
        """レコードをDBに挿入"""
        schema = self.TABLE_SCHEMAS.get(target, {})
        all_fields = schema.get("required", []) + schema.get("optional", [])

        # 有効なフィールドのみ抽出
        insert_data = {
            k: v for k, v in record.items() if k in all_fields and v is not None
        }

        # タイムスタンプ追加
        insert_data["created_at"] = datetime.now()
        insert_data["updated_at"] = datetime.now()

        # SQL生成
        columns = ", ".join(insert_data.keys())
        placeholders = ", ".join([f":{k}" for k in insert_data.keys()])
        sql = f"INSERT INTO public.{target} ({columns}) VALUES ({placeholders})"

        try:
            if not self.dry_run:
                self.session.execute(text(sql), insert_data)
            return True
        except Exception as e:
            self.log(f"挿入エラー: {e}", "ERROR")
            return False

    def import_file(
        self, source: str, target: str, sheet_name: Optional[str] = None
    ) -> Dict:
        """ファイルをインポート"""
        self.log("=" * 60)
        self.log(f"インポート開始: {source} → {target}")
        self.log("=" * 60)

        # ファイル読み込み
        ext = os.path.splitext(source)[1].lower()

        if ext == ".csv":
            records = self.read_csv(source)
        elif ext in [".xlsx", ".xls"]:
            records = self.read_excel(source, sheet_name)
        elif ext == ".json":
            records = self.read_json(source)
        else:
            raise ValueError(f"サポートされていないファイル形式: {ext}")

        # 各レコードを処理
        for i, record in enumerate(records, 1):
            # バリデーション
            is_valid, errors = self.validate_record(record, target)

            if not is_valid:
                self.error_count += 1
                self.errors.append({"row": i, "errors": errors, "data": record})
                self.log(f"行 {i}: バリデーションエラー - {errors}", "WARN")
                continue

            # 変換
            transformed = self.transform_record(record, target)

            # 挿入
            if self.insert_record(transformed, target):
                self.imported_count += 1
                self.log_verbose(f"行 {i}: インポート成功")
            else:
                self.error_count += 1

        # コミット
        if not self.dry_run:
            self.session.commit()
            self.log("トランザクションコミット完了")
        else:
            self.session.rollback()
            self.log("ドライランのためロールバック")

        # 結果サマリー
        self.log("=" * 60)
        self.log("インポート結果:")
        self.log(f"  成功: {self.imported_count}件")
        self.log(f"  失敗: {self.error_count}件")
        self.log("=" * 60)

        return {
            "imported": self.imported_count,
            "errors": self.error_count,
            "error_details": self.errors,
        }

    def close(self):
        """セッションクローズ"""
        self.session.close()


def main():
    parser = argparse.ArgumentParser(
        description="データインポートスクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
    # CSV インポート
    python scripts/import_data.py --source data/knowledge.csv --target knowledge

    # Excel インポート（シート指定）
    python scripts/import_data.py --source data/sop.xlsx --target sop --sheet "Sheet1"

    # JSON インポート
    python scripts/import_data.py --source data/incidents.json --target incidents

    # ドライラン（実際にはインポートしない）
    python scripts/import_data.py --source data/test.csv --target knowledge --dry-run
        """,
    )

    parser.add_argument(
        "--source", required=True, help="インポート元ファイルパス（CSV, Excel, JSON）"
    )
    parser.add_argument(
        "--target",
        required=True,
        choices=["knowledge", "sop", "regulations", "incidents", "consultations"],
        help="インポート先テーブル",
    )
    parser.add_argument("--sheet", help="Excelシート名（省略時は最初のシート）")
    parser.add_argument(
        "--dry-run", action="store_true", help="ドライラン（実際にはインポートしない）"
    )
    parser.add_argument("--verbose", action="store_true", help="詳細ログ出力")

    args = parser.parse_args()

    # ファイル存在確認
    if not os.path.exists(args.source):
        print(f"Error: ファイルが見つかりません: {args.source}")
        sys.exit(1)

    # データベースURL取得
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:ELzion1969@localhost:5432/mirai_knowledge_db",
    )

    # インポート実行
    importer = DataImporter(
        database_url=database_url, dry_run=args.dry_run, verbose=args.verbose
    )

    try:
        result = importer.import_file(
            source=args.source, target=args.target, sheet_name=args.sheet
        )

        # エラー詳細出力
        if result["errors"] > 0 and args.verbose:
            print("\nエラー詳細:")
            for error in result["error_details"]:
                print(f"  行 {error['row']}: {error['errors']}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        importer.close()


if __name__ == "__main__":
    main()
