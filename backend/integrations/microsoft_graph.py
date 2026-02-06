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

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# オプションの依存関係を遅延インポート
try:
    from azure.identity import CertificateCredential, ClientSecretCredential

    AZURE_IDENTITY_AVAILABLE = True
except ImportError:
    AZURE_IDENTITY_AVAILABLE = False
    logger.warning(
        "azure-identity ライブラリが未インストールです。pip install azure-identity でインストールしてください。"
    )

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
        certificate_key_path: Optional[str] = None,
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
        self.tenant_id = tenant_id or os.environ.get("AZURE_TENANT_ID")
        self.client_id = client_id or os.environ.get("AZURE_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("AZURE_CLIENT_SECRET")
        self.certificate_path = certificate_path or os.environ.get(
            "AZURE_CLIENT_CERTIFICATE_PATH"
        )
        self.certificate_key_path = certificate_key_path or os.environ.get(
            "AZURE_CLIENT_CERTIFICATE_KEY_PATH"
        )

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
            logger.warning(
                "AZURE_CLIENT_SECRET または AZURE_CLIENT_CERTIFICATE_PATH が必要です"
            )
            return False
        return True

    def is_configured(self) -> bool:
        """Graph APIが設定されているかどうか"""
        return bool(
            self.tenant_id
            and self.client_id
            and (self.client_secret or self.certificate_path)
        )

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
                    certificate_path=self.certificate_path,
                )
                logger.info("証明書認証を使用します")
            else:
                # クライアントシークレット認証
                self._credential = ClientSecretCredential(
                    tenant_id=self.tenant_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
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
        use_beta: bool = False,
    ) -> Dict:
        """Graph APIリクエストを実行"""
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests ライブラリがインストールされていません")

        token = self.get_access_token()
        base_url = self.GRAPH_API_BETA if use_beta else self.GRAPH_API_BASE
        url = f"{base_url}{endpoint}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=data,
            timeout=30,
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

    def get_users(
        self, select: Optional[List[str]] = None, top: int = 100
    ) -> List[Dict]:
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

    def get_file_mime_type(self, drive_id: str, item_id: str) -> str:
        """
        ファイルMIMEタイプを取得

        必要な権限: Files.Read.All

        Args:
            drive_id: ドライブID
            item_id: ファイルID

        Returns:
            MIMEタイプ（例: "application/pdf"）
        """
        try:
            metadata = self.get_file_metadata(drive_id, item_id)
            mime_type = metadata.get("file", {}).get(
                "mimeType", "application/octet-stream"
            )
            return mime_type
        except Exception as e:
            logger.error(
                f"MIMEタイプ取得エラー (drive_id={drive_id}, item_id={item_id}): {e}"
            )
            return "application/octet-stream"

    def get_file_preview_url(self, drive_id: str, item_id: str) -> Dict[str, str]:
        """
        ファイルプレビューURLを取得

        Office形式ファイル: Microsoft Graph Embed URL
        画像ファイル: ダウンロードURL（preview_type="image"）
        その他: ダウンロードURL（preview_type="download"）

        必要な権限: Files.Read.All

        Args:
            drive_id: ドライブID
            item_id: ファイルID

        Returns:
            {
                "preview_url": "https://...",
                "preview_type": "office_embed | download | image",
                "mime_type": "application/pdf"
            }
        """
        try:
            # ファイルメタデータを取得
            metadata = self.get_file_metadata(drive_id, item_id)
            mime_type = metadata.get("file", {}).get(
                "mimeType", "application/octet-stream"
            )
            file_name = metadata.get("name", "")
            web_url = metadata.get("webUrl", "")

            # Office形式ファイルの判定（拡張子ベース）
            office_extensions = [".xlsx", ".docx", ".pptx", ".xlsm", ".docm", ".pptm"]
            is_office = any(
                file_name.lower().endswith(ext) for ext in office_extensions
            )

            # プレビュータイプとURLの決定
            if is_office and web_url:
                # Office形式: Microsoft Office Online Embedビューアー使用
                preview_url = (
                    f"https://view.officeapps.live.com/op/embed.aspx?src={web_url}"
                )
                preview_type = "office_embed"
            elif mime_type.startswith("image/"):
                # 画像ファイル: ダウンロードURL使用
                preview_url = (
                    f"{self.GRAPH_API_BASE}/drives/{drive_id}/items/{item_id}/content"
                )
                preview_type = "image"
            else:
                # その他: ダウンロードURL
                preview_url = (
                    f"{self.GRAPH_API_BASE}/drives/{drive_id}/items/{item_id}/content"
                )
                preview_type = "download"

            return {
                "preview_url": preview_url,
                "preview_type": preview_type,
                "mime_type": mime_type,
            }

        except Exception as e:
            logger.error(
                f"プレビューURL取得エラー (drive_id={drive_id}, item_id={item_id}): {e}"
            )
            # エラー時はダウンロードURLを返す
            return {
                "preview_url": f"{self.GRAPH_API_BASE}/drives/{drive_id}/items/{item_id}/content",
                "preview_type": "download",
                "mime_type": "application/octet-stream",
            }

    def get_file_thumbnail(
        self, drive_id: str, item_id: str, size: str = "large"
    ) -> Optional[bytes]:
        """
        ファイルサムネイルを取得

        必要な権限: Files.Read.All

        Args:
            drive_id: ドライブID
            item_id: ファイルID
            size: サムネイルサイズ ("small" | "medium" | "large" | "c200x150")
                  - small: 小サイズ（96x96）
                  - medium: 中サイズ（176x176）
                  - large: 大サイズ（800x800）
                  - c{width}x{height}: カスタムサイズ（例: c200x150）

        Returns:
            サムネイル画像データ（bytes）またはNone（サムネイルが利用不可の場合）
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests ライブラリがインストールされていません")

        try:
            token = self.get_access_token()
            url = f"{self.GRAPH_API_BASE}/drives/{drive_id}/items/{item_id}/thumbnails/0/{size}/content"

            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers, timeout=30)

            # 404エラー（サムネイル利用不可）の場合はNoneを返す
            if response.status_code == 404:
                logger.info(
                    f"サムネイル利用不可 (drive_id={drive_id}, item_id={item_id})"
                )
                return None

            response.raise_for_status()
            return response.content

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.info(
                    f"サムネイル利用不可 (drive_id={drive_id}, item_id={item_id})"
                )
                return None
            else:
                logger.error(
                    f"サムネイル取得エラー (drive_id={drive_id}, item_id={item_id}): {e}"
                )
                return None
        except Exception as e:
            logger.error(
                f"サムネイル取得エラー (drive_id={drive_id}, item_id={item_id}): {e}"
            )
            return None

    # =========================================================================
    # データ取得ヘルパー
    # =========================================================================

    def fetch_sharepoint_files(
        self,
        site_name: str,
        library_name: str = "Documents",
        folder_path: str = "/",
        file_extensions: Optional[List[str]] = None,
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
            raise ValueError(
                f"ドキュメントライブラリ '{library_name}' が見つかりません"
            )

        drive_id = drive["id"]

        # ファイル一覧を取得
        items = self.get_drive_items(drive_id, folder_path)

        # 拡張子でフィルタ
        if file_extensions:
            items = [
                item
                for item in items
                if item.get("file")
                and any(
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
            "errors": [],
        }

        if not result["configured"]:
            result["errors"].append("必要な環境変数が設定されていません")
            return result

        if not AZURE_IDENTITY_AVAILABLE:
            result["errors"].append(
                "azure-identity ライブラリがインストールされていません"
            )
            return result

        try:
            # トークン取得テスト
            token = self.get_access_token()
            result["token_acquired"] = bool(token)

            # API呼び出しテスト
            org = self._make_request("GET", "/organization")
            result["connected"] = True
            result["organization"] = org.get("value", [{}])[0].get(
                "displayName", "Unknown"
            )

        except Exception as e:
            result["errors"].append(str(e))

        return result

    # =========================================================================
    # Microsoft Teams
    # =========================================================================

    def get_teams(self) -> List[Dict]:
        """
        参加しているチーム一覧を取得

        必要な権限: Team.ReadBasic.All

        Returns:
            チーム情報のリスト
        """
        result = self._make_request(
            "GET", "/groups?$filter=resourceProvisioningOptions/Any(x:x eq 'Team')"
        )
        return result.get("value", [])

    def get_team_channels(self, team_id: str) -> List[Dict]:
        """
        チームのチャネル一覧を取得

        必要な権限: Channel.ReadBasic.All

        Args:
            team_id: チームID

        Returns:
            チャネル情報のリスト
        """
        result = self._make_request("GET", f"/teams/{team_id}/channels")
        return result.get("value", [])

    def send_teams_channel_message(
        self, team_id: str, channel_id: str, content: str, content_type: str = "text"
    ) -> Dict:
        """
        Teamsチャネルにメッセージを送信

        必要な権限: ChannelMessage.Send（委任権限）
        注意: アプリケーション権限では現在サポートされていません

        Args:
            team_id: チームID
            channel_id: チャネルID
            content: メッセージ内容
            content_type: コンテンツタイプ ("text" or "html")

        Returns:
            送信結果
        """
        data = {"body": {"contentType": content_type, "content": content}}
        return self._make_request(
            "POST", f"/teams/{team_id}/channels/{channel_id}/messages", data=data
        )

    def send_teams_webhook_message(
        self,
        webhook_url: str,
        title: str,
        message: str,
        theme_color: str = "0076D7",
        facts: Optional[List[Dict[str, str]]] = None,
    ) -> bool:
        """
        Teams Incoming WebhookでAdaptive Card形式のメッセージを送信

        Args:
            webhook_url: Webhook URL
            title: メッセージタイトル
            message: メッセージ本文
            theme_color: テーマカラー（16進数）
            facts: 追加のファクト情報 [{"name": "キー", "value": "値"}, ...]

        Returns:
            送信成功かどうか
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests ライブラリがインストールされていません")

        # Adaptive Card形式のペイロード
        card = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": theme_color,
            "summary": title,
            "sections": [
                {
                    "activityTitle": title,
                    "facts": facts or [],
                    "text": message,
                    "markdown": True,
                }
            ],
        }

        try:
            response = requests.post(
                webhook_url,
                json=card,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Teams Webhook送信エラー: {e}")
            return False

    def send_notification_to_teams(
        self,
        webhook_url: str,
        notification_type: str,
        title: str,
        details: Dict[str, str],
        link_url: Optional[str] = None,
    ) -> bool:
        """
        システム通知をTeamsに送信（テンプレート使用）

        Args:
            webhook_url: Webhook URL
            notification_type: 通知タイプ（"knowledge", "incident", "approval"等）
            title: 通知タイトル
            details: 詳細情報の辞書
            link_url: 詳細リンクURL

        Returns:
            送信成功かどうか
        """
        # 通知タイプ別の色
        type_colors = {
            "knowledge": "0076D7",  # 青
            "incident": "FF4444",  # 赤
            "approval": "FFB300",  # オレンジ
            "info": "00C853",  # 緑
        }
        theme_color = type_colors.get(notification_type, "0076D7")

        # 詳細情報をファクト形式に変換
        facts = [{"name": k, "value": v} for k, v in details.items()]

        # リンクを追加
        if link_url:
            facts.append({"name": "詳細", "value": f"[開く]({link_url})"})

        return self.send_teams_webhook_message(
            webhook_url=webhook_url,
            title=f"[{notification_type.upper()}] {title}",
            message="",
            theme_color=theme_color,
            facts=facts,
        )


# =============================================================================
# CLIインターフェース
# =============================================================================


def main():
    """コマンドライン実行"""
    import argparse

    parser = argparse.ArgumentParser(description="Microsoft Graph API 連携テスト")
    parser.add_argument("--test", action="store_true", help="接続テストを実行")
    parser.add_argument("--users", action="store_true", help="ユーザー一覧を取得")
    parser.add_argument(
        "--sites", action="store_true", help="SharePointサイト一覧を取得"
    )

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
        print(
            f"  AZURE_CLIENT_SECRET: {'設定済み' if client.client_secret else '未設定'}"
        )
        print(f"  証明書認証: {'設定済み' if client.certificate_path else '未設定'}")
        print()
        print("使用方法:")
        print("  python -m backend.integrations.microsoft_graph --test")
        print("  python -m backend.integrations.microsoft_graph --users")
        print("  python -m backend.integrations.microsoft_graph --sites")


if __name__ == "__main__":
    main()
