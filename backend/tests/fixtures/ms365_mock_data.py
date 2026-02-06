"""
MS365 Sync用のモックデータ
テストで使用するMicrosoft Graph APIのレスポンスデータ
"""


# SharePointサイト一覧のモックデータ
MOCK_SITES = [
    {
        "id": "site-123",
        "displayName": "Test SharePoint Site",
        "webUrl": "https://contoso.sharepoint.com/sites/test",
        "createdDateTime": "2025-01-01T00:00:00Z",
    }
]

# ドライブ（ドキュメントライブラリ）一覧のモックデータ
MOCK_DRIVES = [
    {
        "id": "drive-456",
        "name": "Documents",
        "driveType": "documentLibrary",
        "createdDateTime": "2025-01-01T00:00:00Z",
    }
]

# ファイル一覧のモックデータ
MOCK_FILES = [
    {
        "id": "file-001",
        "name": "安全施工手順書.pdf",
        "size": 1024000,
        "createdDateTime": "2025-01-15T10:00:00Z",
        "lastModifiedDateTime": "2025-01-15T10:00:00Z",
        "file": {
            "mimeType": "application/pdf",
            "hashes": {"quickXorHash": "abc123def456"},
        },
        "webUrl": "https://contoso.sharepoint.com/sites/test/Documents/file-001.pdf",
    },
    {
        "id": "file-002",
        "name": "品質管理マニュアル.docx",
        "size": 512000,
        "createdDateTime": "2025-01-16T11:00:00Z",
        "lastModifiedDateTime": "2025-01-20T14:30:00Z",
        "file": {
            "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "hashes": {"quickXorHash": "xyz789ghi012"},
        },
        "webUrl": "https://contoso.sharepoint.com/sites/test/Documents/file-002.docx",
    },
    {
        "id": "file-003",
        "name": "工程表.xlsx",
        "size": 256000,
        "createdDateTime": "2025-01-17T09:00:00Z",
        "lastModifiedDateTime": "2025-01-17T09:00:00Z",
        "file": {
            "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "hashes": {"quickXorHash": "mnopqr345stu678"},
        },
        "webUrl": "https://contoso.sharepoint.com/sites/test/Documents/file-003.xlsx",
    },
]

# ファイルコンテンツのモック（バイト）
MOCK_FILE_CONTENT = {
    "file-001": b"PDF content here...",
    "file-002": b"Word document content...",
    "file-003": b"Excel spreadsheet content...",
}

# 同期設定のモックデータ
MOCK_SYNC_CONFIG = {
    "id": 1,
    "name": "テスト同期設定",
    "description": "テスト用の同期設定です",
    "site_id": "site-123",
    "drive_id": "drive-456",
    "folder_path": "/",
    "file_extensions": ["pdf", "docx", "xlsx"],
    "sync_schedule": "0 2 * * *",
    "sync_strategy": "incremental",
    "is_enabled": True,
    "metadata_mapping": {"category": "category_field", "tags": "tags_field"},
    "created_at": "2025-01-15T00:00:00Z",
    "updated_at": "2025-01-15T00:00:00Z",
}

# 同期履歴のモックデータ
MOCK_SYNC_HISTORY = [
    {
        "id": 1,
        "sync_config_id": 1,
        "started_at": "2025-01-20T02:00:00Z",
        "completed_at": "2025-01-20T02:05:23Z",
        "status": "success",
        "files_discovered": 15,
        "files_new": 3,
        "files_updated": 2,
        "files_deleted": 0,
        "files_failed": 0,
        "total_size": 5242880,
        "errors": [],
        "summary": "同期が正常に完了しました",
    },
    {
        "id": 2,
        "sync_config_id": 1,
        "started_at": "2025-01-21T02:00:00Z",
        "completed_at": "2025-01-21T02:03:45Z",
        "status": "success",
        "files_discovered": 15,
        "files_new": 0,
        "files_updated": 1,
        "files_deleted": 0,
        "files_failed": 0,
        "total_size": 512000,
        "errors": [],
        "summary": "同期が正常に完了しました",
    },
]

# エラーケース用のモックデータ
MOCK_AUTH_ERROR = {
    "error": {
        "code": "InvalidAuthenticationToken",
        "message": "Access token has expired or is not yet valid.",
    }
}

MOCK_PERMISSION_ERROR = {
    "error": {
        "code": "Forbidden",
        "message": "The caller does not have permission to perform the action.",
    }
}

MOCK_NOT_FOUND_ERROR = {
    "error": {"code": "itemNotFound", "message": "The resource could not be found."}
}
