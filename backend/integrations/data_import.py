# -*- coding: utf-8 -*-
"""
データインポートモジュール

外部ソースからのデータ取り込み機能を提供:
- CSV/Excelファイルインポート
- Microsoft Graph経由のデータ取得
- サーバー直接接続
- データ変換・正規化
"""

import os
import json
import csv
import logging
from typing import Optional, Dict, List, Any, Union
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# オプションの依存関係
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class DataImporter:
    """
    データインポーター

    様々なソースからナレッジシステムにデータを取り込む
    """

    # サポートするエンティティタイプ
    ENTITY_TYPES = ['knowledge', 'sop', 'incidents', 'regulations', 'consultations']

    def __init__(self, data_dir: Optional[str] = None):
        """
        初期化

        Args:
            data_dir: データ保存先ディレクトリ
        """
        self.data_dir = data_dir or os.environ.get(
            'MKS_DATA_DIR',
            os.path.join(os.path.dirname(__file__), '..', 'data')
        )
        self.data_dir = os.path.abspath(self.data_dir)

    # =========================================================================
    # CSVインポート
    # =========================================================================

    def import_from_csv(
        self,
        file_path: str,
        entity_type: str,
        column_mapping: Optional[Dict[str, str]] = None,
        skip_rows: int = 0
    ) -> Dict[str, Any]:
        """
        CSVファイルからデータをインポート

        Args:
            file_path: CSVファイルパス
            entity_type: エンティティタイプ（knowledge, sop等）
            column_mapping: カラムマッピング {csv_column: entity_field}
            skip_rows: スキップする行数

        Returns:
            インポート結果
        """
        if entity_type not in self.ENTITY_TYPES:
            raise ValueError(f"不明なエンティティタイプ: {entity_type}")

        result = {
            "success": True,
            "entity_type": entity_type,
            "imported": 0,
            "skipped": 0,
            "errors": []
        }

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                # 行をスキップ
                for _ in range(skip_rows):
                    next(reader, None)

                records = []
                for row_num, row in enumerate(reader, start=1):
                    try:
                        record = self._transform_csv_row(row, entity_type, column_mapping)
                        if record:
                            records.append(record)
                            result["imported"] += 1
                        else:
                            result["skipped"] += 1
                    except Exception as e:
                        result["errors"].append(f"行 {row_num}: {str(e)}")
                        result["skipped"] += 1

                # 既存データとマージ
                self._merge_records(entity_type, records)

        except Exception as e:
            result["success"] = False
            result["errors"].append(str(e))

        return result

    def _transform_csv_row(
        self,
        row: Dict[str, str],
        entity_type: str,
        column_mapping: Optional[Dict[str, str]] = None
    ) -> Optional[Dict]:
        """CSVの行をエンティティに変換"""
        # カラムマッピングを適用
        if column_mapping:
            mapped_row = {}
            for csv_col, entity_field in column_mapping.items():
                if csv_col in row:
                    mapped_row[entity_field] = row[csv_col]
            row = mapped_row

        # エンティティタイプごとの変換
        if entity_type == 'knowledge':
            return self._transform_knowledge(row)
        elif entity_type == 'sop':
            return self._transform_sop(row)
        elif entity_type == 'incidents':
            return self._transform_incident(row)
        elif entity_type == 'regulations':
            return self._transform_regulation(row)
        elif entity_type == 'consultations':
            return self._transform_consultation(row)

        return None

    def _transform_knowledge(self, row: Dict) -> Optional[Dict]:
        """ナレッジデータに変換"""
        title = row.get('title', '').strip()
        if not title:
            return None

        return {
            "id": self._generate_id('knowledge'),
            "title": title,
            "summary": row.get('summary', ''),
            "category": row.get('category', '一般'),
            "tags": self._parse_tags(row.get('tags', '')),
            "content": row.get('content', ''),
            "status": row.get('status', 'draft'),
            "priority": row.get('priority', 'medium'),
            "project": row.get('project', ''),
            "owner": row.get('owner', 'システム'),
            "created_at": self._parse_datetime(row.get('created_at')),
            "updated_at": datetime.now().isoformat()
        }

    def _transform_sop(self, row: Dict) -> Optional[Dict]:
        """SOP（標準施工手順）データに変換"""
        title = row.get('title', '').strip()
        if not title:
            return None

        return {
            "id": self._generate_id('sop'),
            "title": title,
            "category": row.get('category', '一般'),
            "version": row.get('version', '1.0'),
            "revision_date": self._parse_date(row.get('revision_date')),
            "target": row.get('target', ''),
            "tags": self._parse_tags(row.get('tags', '')),
            "content": row.get('content', ''),
            "status": row.get('status', 'active'),
            "created_at": datetime.now().isoformat()
        }

    def _transform_incident(self, row: Dict) -> Optional[Dict]:
        """事故・ヒヤリレポートデータに変換"""
        title = row.get('title', '').strip()
        if not title:
            return None

        return {
            "id": self._generate_id('incidents'),
            "title": title,
            "description": row.get('description', ''),
            "project": row.get('project', ''),
            "incident_date": self._parse_date(row.get('incident_date')),
            "severity": row.get('severity', 'medium'),
            "status": row.get('status', 'reported'),
            "root_cause": row.get('root_cause', ''),
            "corrective_actions": row.get('corrective_actions', ''),
            "location": row.get('location', ''),
            "tags": self._parse_tags(row.get('tags', '')),
            "created_at": datetime.now().isoformat()
        }

    def _transform_regulation(self, row: Dict) -> Optional[Dict]:
        """法令・規格データに変換"""
        title = row.get('title', '').strip()
        if not title:
            return None

        return {
            "id": self._generate_id('regulations'),
            "title": title,
            "issuer": row.get('issuer', ''),
            "category": row.get('category', '法令'),
            "revision_date": self._parse_date(row.get('revision_date')),
            "summary": row.get('summary', ''),
            "content": row.get('content', ''),
            "status": row.get('status', 'active'),
            "url": row.get('url', ''),
            "created_at": datetime.now().isoformat()
        }

    def _transform_consultation(self, row: Dict) -> Optional[Dict]:
        """専門家相談データに変換"""
        title = row.get('title', '').strip()
        if not title:
            return None

        return {
            "id": self._generate_id('consultations'),
            "title": title,
            "question": row.get('question', ''),
            "category": row.get('category', '技術相談'),
            "priority": row.get('priority', 'medium'),
            "status": row.get('status', 'pending'),
            "answer": row.get('answer', ''),
            "created_at": datetime.now().isoformat()
        }

    # =========================================================================
    # Excelインポート
    # =========================================================================

    def import_from_excel(
        self,
        file_path: str,
        entity_type: str,
        sheet_name: Union[str, int] = 0,
        column_mapping: Optional[Dict[str, str]] = None,
        skip_rows: int = 0
    ) -> Dict[str, Any]:
        """
        Excelファイルからデータをインポート

        Args:
            file_path: Excelファイルパス
            entity_type: エンティティタイプ
            sheet_name: シート名またはインデックス
            column_mapping: カラムマッピング
            skip_rows: スキップする行数

        Returns:
            インポート結果
        """
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas ライブラリがインストールされていません。pip install pandas openpyxl")

        if entity_type not in self.ENTITY_TYPES:
            raise ValueError(f"不明なエンティティタイプ: {entity_type}")

        result = {
            "success": True,
            "entity_type": entity_type,
            "imported": 0,
            "skipped": 0,
            "errors": []
        }

        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=skip_rows)

            # カラムマッピングを適用
            if column_mapping:
                df = df.rename(columns=column_mapping)

            records = []
            for idx, row in df.iterrows():
                try:
                    row_dict = row.to_dict()
                    # NaN値を空文字に変換
                    row_dict = {k: ('' if pd.isna(v) else v) for k, v in row_dict.items()}

                    record = self._transform_csv_row(row_dict, entity_type, None)
                    if record:
                        records.append(record)
                        result["imported"] += 1
                    else:
                        result["skipped"] += 1
                except Exception as e:
                    result["errors"].append(f"行 {idx}: {str(e)}")
                    result["skipped"] += 1

            # 既存データとマージ
            self._merge_records(entity_type, records)

        except Exception as e:
            result["success"] = False
            result["errors"].append(str(e))

        return result

    # =========================================================================
    # Microsoft Graph連携
    # =========================================================================

    def import_from_sharepoint(
        self,
        site_name: str,
        library_name: str = "Documents",
        folder_path: str = "/",
        entity_type: str = "knowledge"
    ) -> Dict[str, Any]:
        """
        SharePointからデータをインポート

        Args:
            site_name: SharePointサイト名
            library_name: ドキュメントライブラリ名
            folder_path: フォルダパス
            entity_type: インポート先エンティティタイプ

        Returns:
            インポート結果
        """
        from .microsoft_graph import MicrosoftGraphClient

        result = {
            "success": True,
            "entity_type": entity_type,
            "imported": 0,
            "skipped": 0,
            "errors": []
        }

        try:
            client = MicrosoftGraphClient()

            if not client.is_configured():
                raise ValueError("Microsoft Graph APIが設定されていません")

            # ファイル一覧を取得
            files = client.fetch_sharepoint_files(
                site_name=site_name,
                library_name=library_name,
                folder_path=folder_path,
                file_extensions=['.xlsx', '.csv', '.json']
            )

            for file_info in files:
                try:
                    file_name = file_info.get('name', '')
                    drive_id = file_info.get('parentReference', {}).get('driveId')
                    item_id = file_info.get('id')

                    if not drive_id or not item_id:
                        continue

                    # ファイルをダウンロード
                    content = client.download_file(drive_id, item_id)

                    # 一時ファイルに保存してインポート
                    temp_path = f"/tmp/{file_name}"
                    with open(temp_path, 'wb') as f:
                        f.write(content)

                    # ファイル形式に応じてインポート
                    if file_name.endswith('.csv'):
                        sub_result = self.import_from_csv(temp_path, entity_type)
                    elif file_name.endswith('.xlsx'):
                        sub_result = self.import_from_excel(temp_path, entity_type)
                    elif file_name.endswith('.json'):
                        sub_result = self.import_from_json(temp_path, entity_type)
                    else:
                        continue

                    result["imported"] += sub_result.get("imported", 0)
                    result["skipped"] += sub_result.get("skipped", 0)
                    result["errors"].extend(sub_result.get("errors", []))

                    # 一時ファイルを削除
                    os.remove(temp_path)

                except Exception as e:
                    result["errors"].append(f"ファイル {file_info.get('name')}: {str(e)}")

        except Exception as e:
            result["success"] = False
            result["errors"].append(str(e))

        return result

    # =========================================================================
    # JSONインポート
    # =========================================================================

    def import_from_json(
        self,
        file_path: str,
        entity_type: str
    ) -> Dict[str, Any]:
        """
        JSONファイルからデータをインポート

        Args:
            file_path: JSONファイルパス
            entity_type: エンティティタイプ

        Returns:
            インポート結果
        """
        if entity_type not in self.ENTITY_TYPES:
            raise ValueError(f"不明なエンティティタイプ: {entity_type}")

        result = {
            "success": True,
            "entity_type": entity_type,
            "imported": 0,
            "skipped": 0,
            "errors": []
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, list):
                records = data
            elif isinstance(data, dict) and 'items' in data:
                records = data['items']
            elif isinstance(data, dict) and 'data' in data:
                records = data['data']
            else:
                records = [data]

            valid_records = []
            for record in records:
                if isinstance(record, dict):
                    # IDがなければ生成
                    if 'id' not in record:
                        record['id'] = self._generate_id(entity_type)
                    valid_records.append(record)
                    result["imported"] += 1
                else:
                    result["skipped"] += 1

            self._merge_records(entity_type, valid_records)

        except Exception as e:
            result["success"] = False
            result["errors"].append(str(e))

        return result

    # =========================================================================
    # ヘルパー関数
    # =========================================================================

    def _generate_id(self, entity_type: str) -> int:
        """新しいIDを生成"""
        # 既存データを読み込んでmax IDを取得
        file_path = os.path.join(self.data_dir, f"{entity_type}.json")
        max_id = 0

        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and 'id' in item:
                                max_id = max(max_id, int(item['id']))
            except Exception:
                pass

        return max_id + 1

    def _parse_tags(self, tags_str: str) -> List[str]:
        """タグ文字列をリストに変換"""
        if not tags_str:
            return []
        # カンマ、セミコロン、スペースで分割
        import re
        tags = re.split(r'[,;、\s]+', str(tags_str))
        return [t.strip() for t in tags if t.strip()]

    def _parse_datetime(self, dt_str: Optional[str]) -> str:
        """日時文字列をISO形式に変換"""
        if not dt_str:
            return datetime.now().isoformat()

        try:
            # 様々な形式を試す
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d']:
                try:
                    dt = datetime.strptime(str(dt_str), fmt)
                    return dt.isoformat()
                except ValueError:
                    continue
            return datetime.now().isoformat()
        except Exception:
            return datetime.now().isoformat()

    def _parse_date(self, date_str: Optional[str]) -> str:
        """日付文字列を正規化"""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')

        try:
            for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y年%m月%d日']:
                try:
                    dt = datetime.strptime(str(date_str), fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            return datetime.now().strftime('%Y-%m-%d')
        except Exception:
            return datetime.now().strftime('%Y-%m-%d')

    def _merge_records(self, entity_type: str, new_records: List[Dict]):
        """既存データに新しいレコードをマージ"""
        file_path = os.path.join(self.data_dir, f"{entity_type}.json")

        existing = []
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            except Exception:
                pass

        # 既存IDのセット
        existing_ids = {item.get('id') for item in existing if isinstance(item, dict)}

        # 重複を除いて追加
        for record in new_records:
            if record.get('id') not in existing_ids:
                existing.append(record)
                existing_ids.add(record.get('id'))

        # 保存
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

    # =========================================================================
    # エクスポート機能
    # =========================================================================

    def export_to_csv(self, entity_type: str, output_path: str) -> Dict[str, Any]:
        """
        データをCSVにエクスポート

        Args:
            entity_type: エンティティタイプ
            output_path: 出力ファイルパス

        Returns:
            エクスポート結果
        """
        file_path = os.path.join(self.data_dir, f"{entity_type}.json")

        if not os.path.exists(file_path):
            return {"success": False, "error": f"データファイルが見つかりません: {file_path}"}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not data:
                return {"success": False, "error": "データが空です"}

            # CSVに書き出し
            with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
                if isinstance(data, list) and data:
                    fieldnames = data[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)

            return {"success": True, "exported": len(data), "path": output_path}

        except Exception as e:
            return {"success": False, "error": str(e)}


# =============================================================================
# CLIインターフェース
# =============================================================================

def main():
    """コマンドライン実行"""
    import argparse

    parser = argparse.ArgumentParser(description="データインポートツール")
    parser.add_argument("--csv", type=str, help="CSVファイルパス")
    parser.add_argument("--excel", type=str, help="Excelファイルパス")
    parser.add_argument("--json", type=str, help="JSONファイルパス")
    parser.add_argument("--type", type=str, required=True,
                        choices=DataImporter.ENTITY_TYPES,
                        help="エンティティタイプ")
    parser.add_argument("--export", type=str, help="CSVエクスポート先パス")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    importer = DataImporter()

    if args.export:
        result = importer.export_to_csv(args.type, args.export)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.csv:
        result = importer.import_from_csv(args.csv, args.type)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.excel:
        result = importer.import_from_excel(args.excel, args.type)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.json:
        result = importer.import_from_json(args.json, args.type)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
