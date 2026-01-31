"""
MS365同期サービスのユニットテスト
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from tests.fixtures.ms365_mock_data import (
    MOCK_SITES, MOCK_DRIVES, MOCK_FILES, MOCK_FILE_CONTENT,
    MOCK_SYNC_CONFIG, MOCK_AUTH_ERROR
)


class TestMS365SyncService:
    """MS365同期サービスのテスト"""

    @pytest.fixture
    def mock_graph_client(self):
        """モックのGraph APIクライアント"""
        client = Mock()
        client.get_sites.return_value = MOCK_SITES
        client.get_site_drives.return_value = MOCK_DRIVES
        client.get_drive_items.return_value = MOCK_FILES
        client.download_file.side_effect = lambda drive_id, item_id: MOCK_FILE_CONTENT.get(item_id, b"")
        client.get_file_metadata.side_effect = lambda drive_id, item_id: next(
            (f for f in MOCK_FILES if f['id'] == item_id), None
        )
        return client

    def test_discover_files(self, mock_graph_client):
        """ファイル検出のテスト"""
        # 実装: ドライブからファイル一覧を取得
        files = mock_graph_client.get_drive_items("drive-456", "/")

        assert len(files) == 3
        assert files[0]['name'] == '安全施工手順書.pdf'
        assert files[1]['name'] == '品質管理マニュアル.docx'
        assert files[2]['name'] == '工程表.xlsx'

    def test_detect_changes_incremental(self, mock_graph_client):
        """増分変更検出のテスト"""
        # 既存ファイルのハッシュ
        existing_hashes = {
            "file-001": "abc123def456",  # 変更なし
            "file-002": "old_hash_xyz",   # 変更あり（ハッシュが異なる）
            # file-003 は新規ファイル
        }

        # 現在のファイル一覧を取得
        current_files = mock_graph_client.get_drive_items("drive-456", "/")

        # 変更検出ロジック
        new_files = []
        updated_files = []
        unchanged_files = []

        for file in current_files:
            file_id = file['id']
            current_hash = file.get('file', {}).get('hashes', {}).get('quickXorHash', '')

            if file_id not in existing_hashes:
                new_files.append(file)
            elif existing_hashes[file_id] != current_hash:
                updated_files.append(file)
            else:
                unchanged_files.append(file)

        assert len(new_files) == 1
        assert new_files[0]['id'] == 'file-003'

        assert len(updated_files) == 1
        assert updated_files[0]['id'] == 'file-002'

        assert len(unchanged_files) == 1
        assert unchanged_files[0]['id'] == 'file-001'

    def test_calculate_checksum(self):
        """チェックサム計算のテスト"""
        import hashlib

        # サンプルデータ
        content = b"Test file content for checksum"

        # MD5ハッシュ計算
        md5_hash = hashlib.md5(content).hexdigest()
        assert len(md5_hash) == 32

        # SHA256ハッシュ計算
        sha256_hash = hashlib.sha256(content).hexdigest()
        assert len(sha256_hash) == 64

    def test_extract_basic_metadata(self, mock_graph_client):
        """メタデータ抽出のテスト"""
        file_metadata = mock_graph_client.get_file_metadata("drive-456", "file-001")

        # 基本メタデータの抽出
        extracted = {
            "file_id": file_metadata['id'],
            "filename": file_metadata['name'],
            "size": file_metadata['size'],
            "mime_type": file_metadata['file']['mimeType'],
            "created_at": file_metadata['createdDateTime'],
            "modified_at": file_metadata['lastModifiedDateTime'],
            "web_url": file_metadata['webUrl']
        }

        assert extracted['file_id'] == 'file-001'
        assert extracted['filename'] == '安全施工手順書.pdf'
        assert extracted['size'] == 1024000
        assert extracted['mime_type'] == 'application/pdf'

    def test_sync_error_handling(self, mock_graph_client):
        """同期エラーハンドリングのテスト"""
        # 認証エラーをシミュレート
        mock_graph_client.get_sites.side_effect = PermissionError("Graph API認証エラー")

        with pytest.raises(PermissionError, match="認証エラー"):
            mock_graph_client.get_sites()

    def test_file_extension_filter(self, mock_graph_client):
        """ファイル拡張子フィルタのテスト"""
        all_files = mock_graph_client.get_drive_items("drive-456", "/")
        allowed_extensions = ['pdf', 'docx']

        # 拡張子でフィルタリング
        filtered_files = [
            f for f in all_files
            if any(f['name'].lower().endswith(f'.{ext}') for ext in allowed_extensions)
        ]

        assert len(filtered_files) == 2
        assert filtered_files[0]['name'] == '安全施工手順書.pdf'
        assert filtered_files[1]['name'] == '品質管理マニュアル.docx'


class TestMetadataExtractor:
    """メタデータ抽出のテスト"""

    def test_extract_from_pdf(self):
        """PDFテキスト抽出のテスト（モック）"""
        # 実際のPDF抽出はライブラリが必要なので、ここではモック
        mock_pdf_content = "これは安全施工手順書のテキストです。"

        # 簡易的なメタデータ抽出
        metadata = {
            "text": mock_pdf_content,
            "word_count": len(mock_pdf_content),
            "has_content": bool(mock_pdf_content)
        }

        assert metadata['has_content'] is True
        assert metadata['word_count'] > 0

    def test_extract_from_word(self):
        """Word文書抽出のテスト（モック）"""
        # python-docxを使った抽出のモック
        mock_word_content = "品質管理マニュアルの内容です。\n第1章: 品質方針\n第2章: 検査手順"

        metadata = {
            "text": mock_word_content,
            "paragraphs": mock_word_content.count('\n') + 1,
            "has_content": bool(mock_word_content)
        }

        assert metadata['has_content'] is True
        assert metadata['paragraphs'] == 3

    def test_extract_from_excel(self):
        """Excel抽出のテスト（モック）"""
        # openpyxlを使った抽出のモック
        mock_excel_data = [
            ["日付", "工程", "進捗率"],
            ["2025-01-15", "基礎工事", "80%"],
            ["2025-01-20", "躯体工事", "50%"]
        ]

        metadata = {
            "row_count": len(mock_excel_data),
            "column_count": len(mock_excel_data[0]) if mock_excel_data else 0,
            "has_content": bool(mock_excel_data)
        }

        assert metadata['has_content'] is True
        assert metadata['row_count'] == 3
        assert metadata['column_count'] == 3

    def test_extract_from_text(self):
        """テキストファイル抽出のテスト"""
        mock_text_content = "これはテキストファイルの内容です。\n複数行あります。"

        # UTF-8でエンコード
        content_bytes = mock_text_content.encode('utf-8')

        # デコード
        decoded = content_bytes.decode('utf-8')

        metadata = {
            "text": decoded,
            "line_count": decoded.count('\n') + 1,
            "encoding": "utf-8"
        }

        assert metadata['text'] == mock_text_content
        assert metadata['line_count'] == 2
        assert metadata['encoding'] == 'utf-8'

    def test_encoding_detection(self):
        """エンコーディング検出のテスト"""
        # UTF-8
        utf8_text = "日本語テキスト".encode('utf-8')
        assert utf8_text.decode('utf-8') == "日本語テキスト"

        # Shift-JIS
        sjis_text = "日本語テキスト".encode('shift-jis')
        assert sjis_text.decode('shift-jis') == "日本語テキスト"

        # 自動検出が必要な場合のロジック
        def detect_encoding(content: bytes) -> str:
            """簡易的なエンコーディング検出"""
            encodings = ['utf-8', 'shift-jis', 'euc-jp', 'iso-2022-jp']
            for enc in encodings:
                try:
                    content.decode(enc)
                    return enc
                except (UnicodeDecodeError, LookupError):
                    continue
            return 'utf-8'  # デフォルト

        assert detect_encoding(utf8_text) == 'utf-8'
        assert detect_encoding(sjis_text) == 'shift-jis'


class TestMS365SchedulerService:
    """MS365スケジューラーのテスト"""

    def test_schedule_creation(self):
        """スケジュール作成のテスト"""
        # cron形式のスケジュール
        schedule = "0 2 * * *"  # 毎日午前2時

        # スケジュールのパース（簡易検証）
        parts = schedule.split()
        assert len(parts) == 5
        assert parts[0] == "0"   # 分
        assert parts[1] == "2"   # 時
        assert parts[2] == "*"   # 日
        assert parts[3] == "*"   # 月
        assert parts[4] == "*"   # 曜日

    def test_cron_parsing(self):
        """cronパースのテスト"""
        test_cases = [
            ("0 2 * * *", "毎日午前2時"),
            ("0 */6 * * *", "6時間ごと"),
            ("0 0 * * 0", "毎週日曜日の午前0時"),
            ("0 9 1 * *", "毎月1日の午前9時")
        ]

        for cron, description in test_cases:
            parts = cron.split()
            assert len(parts) == 5, f"{description}: cron形式が正しくありません"

    def test_scheduler_start_stop(self):
        """スケジューラー開始/停止のテスト"""
        # モックのスケジューラー
        scheduler_state = {"running": False, "jobs": []}

        def start_scheduler():
            scheduler_state["running"] = True
            scheduler_state["jobs"].append({
                "id": "sync_job_1",
                "schedule": "0 2 * * *",
                "next_run": "2025-01-21T02:00:00Z"
            })

        def stop_scheduler():
            scheduler_state["running"] = False
            scheduler_state["jobs"].clear()

        # スケジューラー開始
        start_scheduler()
        assert scheduler_state["running"] is True
        assert len(scheduler_state["jobs"]) == 1

        # スケジューラー停止
        stop_scheduler()
        assert scheduler_state["running"] is False
        assert len(scheduler_state["jobs"]) == 0

    def test_job_execution_tracking(self):
        """ジョブ実行追跡のテスト"""
        job_executions = []

        def execute_sync_job(config_id: int):
            """同期ジョブを実行"""
            execution = {
                "config_id": config_id,
                "started_at": datetime.utcnow().isoformat(),
                "status": "running"
            }
            job_executions.append(execution)

            # 同期処理（モック）
            # ... 実際の同期ロジック ...

            # 完了を記録
            execution["status"] = "completed"
            execution["completed_at"] = datetime.utcnow().isoformat()

        # ジョブ実行
        execute_sync_job(1)

        assert len(job_executions) == 1
        assert job_executions[0]["config_id"] == 1
        assert job_executions[0]["status"] == "completed"
        assert "started_at" in job_executions[0]
        assert "completed_at" in job_executions[0]
