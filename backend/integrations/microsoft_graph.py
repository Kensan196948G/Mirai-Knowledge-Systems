# -*- coding: utf-8 -*-
"""
Microsoft Graph API 連携モジュール

非対話型認証（デーモンアプリ）によるMicrosoft 365データアクセス機能を提供
- SharePoint/OneDriveからのファイル取得
- ユーザー情報取得
- Teams通知送信

使用方法:
    1. Azure ADでアプリ登録
    2. 環境変数を設定:
       - AZURE_TENANT_ID
       - AZURE_CLIENT_ID
       - AZURE_CLIENT_SECRET または AZURE_CLIENT_CERTIFICATE_PATH
    3. MicrosoftGraphClient を初期化して使用

参考: https://learn.microsoft.com/en-us/graph/auth-v2-service
"""

import os
import json
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# オプションの依存関係を遅延インポート
try:
    from azure.identity import ClientSecretCredential, CertificateCredential
    AZURE_IDENTITY_AVAILABLE = True
except ImportError:
    AZURE_IDENTITY_AVAILABLE = False
    logger.warning("azure-identity ライブラリが未インストールです。pip install azure-identity でインストールしてください。")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class MicrosoftGraphClient:
    """
    Microsoft Graph API クライアント

    非対話型認証（Client Credentials Flow）を使用してMicrosoft 365にアクセス
    """

    GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
    GRAPH_API_BETA = "https://graph.microsoft.com/beta"

    def __init__(
        self,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        certificate_path: Optional[str] = None,
        certificate_key_path: Optional[str] = None
    ):
        """
        Microsoft Graph クライアントを初期化

        Args:
            tenant_id: Azure ADテナントID（環境変数AZURE_TENANT_IDからも取得可）
            client_id: アプリケーションID（環境変数AZURE_CLIENT_IDからも取得可）
            client_secret: クライアントシークレット（環境変数AZURE_CLIENT_SECRETからも取得可）
            certificate_path: 証明書ファイルパス（環境変数AZURE_CLIENT_CERTIFICATE_PATHからも取得可）
            certificate_key_path: 秘密鍵ファイルパス（環境変数AZURE_CLIENT_CERTIFICATE_KEY_PATHからも取得可）
        """
        self.tenant_id = tenant_id or os.environ.get('AZURE_TENANT_ID')
        self.client_id = client_id or os.environ.get('AZURE_CLIENT_ID')
        self.client_secret = client_secret or os.environ.get('AZURE_CLIENT_SECRET')
        self.certificate_path = certificate_path or os.environ.get('AZURE_CLIENT_CERTIFICATE_PATH')
        self.certificate_key_path = certificate_key_path or os.environ.get('AZURE_CLIENT_CERTIFICATE_KEY_PATH')

        self._credential = None
        self._access_token = None
        self._token_expiry = None

        # 設定の検証
        self._validate_config()

    def _validate_config(self) -> bool:
        """設定を検証"""
        if not self.tenant_id:
            logger.warning("AZURE_TENANT_ID が設定されていません")
            return False
        if not self.client_id:
            logger.warning("AZURE_CLIENT_ID が設定されていません")
            return False
        if not self.client_secret and not self.certificate_path:
            logger.warning("AZURE_CLIENT_SECRET または AZURE_CLIENT_CERTIFICATE_PATH が必要です")
            return False
        return True

    def is_configured(self) -> bool:
        """Graph APIが設定されているかどうか"""
        return bool(self.tenant_id and self.client_id and (self.client_secret or self.certificate_path))

    def _get_credential(self):
        """認証情報を取得"""
        if not AZURE_IDENTITY_AVAILABLE:
            raise ImportError("azure-identity ライブラリがインストールされていません")

        if self._credential is None:
            if self.certificate_path:
                # 証明書認証（推奨）
                self._credential = CertificateCredential(
                    tenant_id=self.tenant_id,
                    client_id=self.client_id,
                    certificate_path=self.certificate_path
                )
                logger.info("証明書認証を使用します")
            else:
                # クライアントシークレット認証
                self._credential = ClientSecretCredential(
                    tenant_id=self.tenant_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
                logger.info("クライアントシークレット認証を使用します")

        return self._credential

    def get_access_token(self) -> str:
        """アクセストークンを取得"""
        credential = self._get_credential()
        token = credential.get_token("https://graph.microsoft.com/.default")
        self._access_token = token.token
        return self._access_token

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        use_beta: bool = False
    ) -> Dict:
        """Graph APIリクエストを実行"""
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests ライブラリがインストールされていません")

        token = self.get_access_token()
        base_url = self.GRAPH_API_BETA if use_beta else self.GRAPH_API_BASE
        url = f"{base_url}{endpoint}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=data,
            timeout=30
        )

        if response.status_code == 401:
            logger.error("認証エラー: トークンが無効または期限切れです")
            raise PermissionError("Graph API認証エラー")

        if response.status_code == 403:
            logger.error("権限エラー: 必要なAPI権限がありません")
            raise PermissionError("Graph API権限エラー")

        response.raise_for_status()

        if response.content:
            return response.json()
        return {}

    # =========================================================================
    # ユーザー関連
    # =========================================================================

    def get_users(self, select: Optional[List[str]] = None, top: int = 100) -> List[Dict]:
        """
        組織内のユーザー一覧を取得

        必要な権限: User.Read.All

        Args:
            select: 取得するフィールド
            top: 取得件数

        Returns:
            ユーザー情報のリスト
        """
        params = {"$top": top}
        if select:
            params["$select"] = ",".join(select)

        result = self._make_request("GET", "/users", params=params)
        return result.get("value", [])

    def get_user(self, user_id: str) -> Dict:
        """
        特定のユーザー情報を取得

        必要な権限: User.Read.All
        """
        return self._make_request("GET", f"/users/{user_id}")

    # =========================================================================
    # SharePoint / OneDrive
    # =========================================================================

    def get_sites(self, search: Optional[str] = None) -> List[Dict]:
        """
        SharePointサイト一覧を取得

        必要な権限: Sites.Read.All

        Args:
            search: 検索クエリ
        """
        if search:
            result = self._make_request("GET", f"/sites?search={search}")
        else:
            result = self._make_request("GET", "/sites")
        return result.get("value", [])

    def get_site_drives(self, site_id: str) -> List[Dict]:
        """
        サイト内のドライブ（ドキュメントライブラリ）一覧を取得

        必要な権限: Sites.Read.All
        """
        result = self._make_request("GET", f"/sites/{site_id}/drives")
        return result.get("value", [])

    def get_drive_items(self, drive_id: str, path: str = "/") -> List[Dict]:
        """
        ドライブ内のアイテム（ファイル/フォルダ）一覧を取得

        必要な権限: Files.Read.All
        """
        if path == "/":
            endpoint = f"/drives/{drive_id}/root/children"
        else:
            endpoint = f"/drives/{drive_id}/root:/{path}:/children"

        result = self._make_request("GET", endpoint)
        return result.get("value", [])

    def download_file(self, drive_id: str, item_id: str) -> bytes:
        """
        ファイルをダウンロード

        必要な権限: Files.Read.All
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests ライブラリがインストールされていません")

        token = self.get_access_token()
        url = f"{self.GRAPH_API_BASE}/drives/{drive_id}/items/{item_id}/content"

        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()

        return response.content

    def get_file_metadata(self, drive_id: str, item_id: str) -> Dict:
        """
        ファイルメタデータを取得

        必要な権限: Files.Read.All
        """
        return self._make_request("GET", f"/drives/{drive_id}/items/{item_id}")

    # =========================================================================
    # データ取得ヘルパー
    # =========================================================================

    def fetch_sharepoint_files(
        self,
        site_name: str,
        library_name: str = "Documents",
        folder_path: str = "/",
        file_extensions: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        SharePointライブラリからファイル情報を取得

        Args:
            site_name: サイト名
            library_name: ドキュメントライブラリ名
            folder_path: フォルダパス
            file_extensions: フィルタする拡張子（例: ['.xlsx', '.csv']）

        Returns:
            ファイル情報のリスト
        """
        # サイトを検索
        sites = self.get_sites(search=site_name)
        if not sites:
            raise ValueError(f"サイト '{site_name}' が見つかりません")

        site = sites[0]
        site_id = site["id"]

        # ドライブを取得
        drives = self.get_site_drives(site_id)
        drive = next((d for d in drives if d.get("name") == library_name), None)
        if not drive:
            raise ValueError(f"ドキュメントライブラリ '{library_name}' が見つかりません")

        drive_id = drive["id"]

        # ファイル一覧を取得
        items = self.get_drive_items(drive_id, folder_path)

        # 拡張子でフィルタ
        if file_extensions:
            items = [
                item for item in items
                if item.get("file") and any(
                    item["name"].lower().endswith(ext.lower())
                    for ext in file_extensions
                )
            ]

        return items

    # =========================================================================
    # テスト・診断
    # =========================================================================

    def test_connection(self) -> Dict[str, Any]:
        """
        Graph API接続をテスト

        Returns:
            テスト結果
        """
        result = {
            "configured": self.is_configured(),
            "connected": False,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "auth_type": "certificate" if self.certificate_path else "secret",
            "errors": []
        }

        if not result["configured"]:
            result["errors"].append("必要な環境変数が設定されていません")
            return result

        if not AZURE_IDENTITY_AVAILABLE:
            result["errors"].append("azure-identity ライブラリがインストールされていません")
            return result

        try:
            # トークン取得テスト
            token = self.get_access_token()
            result["token_acquired"] = bool(token)

            # API呼び出しテスト
            org = self._make_request("GET", "/organization")
            result["connected"] = True
            result["organization"] = org.get("value", [{}])[0].get("displayName", "Unknown")

        except Exception as e:
            result["errors"].append(str(e))

        return result


# =============================================================================
# CLIインターフェース
# =============================================================================

def main():
    """コマンドライン実行"""
    import argparse

    parser = argparse.ArgumentParser(description="Microsoft Graph API 連携テスト")
    parser.add_argument("--test", action="store_true", help="接続テストを実行")
    parser.add_argument("--users", action="store_true", help="ユーザー一覧を取得")
    parser.add_argument("--sites", action="store_true", help="SharePointサイト一覧を取得")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    client = MicrosoftGraphClient()

    if args.test:
        print("Graph API接続テスト...")
        result = client.test_connection()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.users:
        print("ユーザー一覧取得...")
        users = client.get_users(select=["displayName", "mail", "department"])
        for user in users:
            print(f"  - {user.get('displayName')} ({user.get('mail')})")

    elif args.sites:
        print("SharePointサイト一覧取得...")
        sites = client.get_sites()
        for site in sites:
            print(f"  - {site.get('displayName')} ({site.get('webUrl')})")

    else:
        # 設定状況を表示
        print("Microsoft Graph API 設定状況:")
        print(f"  AZURE_TENANT_ID: {'設定済み' if client.tenant_id else '未設定'}")
        print(f"  AZURE_CLIENT_ID: {'設定済み' if client.client_id else '未設定'}")
        print(f"  AZURE_CLIENT_SECRET: {'設定済み' if client.client_secret else '未設定'}")
        print(f"  証明書認証: {'設定済み' if client.certificate_path else '未設定'}")
        print()
        print("使用方法:")
        print("  python -m backend.integrations.microsoft_graph --test")
        print("  python -m backend.integrations.microsoft_graph --users")
        print("  python -m backend.integrations.microsoft_graph --sites")


if __name__ == "__main__":
    main()
