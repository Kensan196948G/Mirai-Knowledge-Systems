# Microsoft 365 連携ガイド

## 更新日: 2026-01-07
## バージョン: 1.0

---

## 1. 概要

Mirai Knowledge SystemsとMicrosoft 365（SharePoint/OneDrive）を連携し、
ファイルの一覧取得やドキュメントのインポートを実現するためのガイドです。

## 2. 技術アーキテクチャ

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Flask App     │────>│   Azure AD      │────>│  Microsoft      │
│   (MKS)         │<────│   (OAuth 2.0)   │<────│  Graph API      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                                               │
        │                                               ▼
        │                                       ┌─────────────────┐
        └──────────────────────────────────────>│  SharePoint/    │
                    Access Token                │  OneDrive       │
                                                └─────────────────┘
```

## 3. 必要なライブラリ

```bash
pip install msal azure-identity msgraph-sdk requests
```

| ライブラリ | 用途 |
|-----------|------|
| msal | Microsoft認証ライブラリ |
| azure-identity | Azure認証情報管理 |
| msgraph-sdk | Microsoft Graph SDK（公式） |
| requests | API直接呼び出し |

## 4. Azure ADアプリ登録手順

### 4.1 アプリ登録

1. Azure Portal（https://portal.azure.com）にサインイン
2. Azure Active Directory → アプリの登録 → 新規登録
3. 設定:
   - 名前: `MKS-SharePoint-Integration`
   - サポートされているアカウントの種類: 「この組織ディレクトリのみ」
   - リダイレクトURI: `http://localhost:5100/auth/callback`

### 4.2 取得する情報

| 情報 | 取得場所 |
|------|----------|
| Client ID | 概要ページ → アプリケーション（クライアント）ID |
| Tenant ID | 概要ページ → ディレクトリ（テナント）ID |
| Client Secret | 証明書とシークレット → 新しいクライアントシークレット |

### 4.3 API権限設定

**必要な権限**:

| 権限 | 種類 | 用途 |
|------|------|------|
| Files.Read.All | Delegated | ファイル読み取り |
| Sites.Read.All | Delegated | SharePointサイト読み取り |
| User.Read | Delegated | ユーザー情報取得 |

**設定手順**:
1. APIのアクセス許可 → アクセス許可の追加
2. Microsoft Graph → 委任されたアクセス許可
3. 上記権限を追加
4. 管理者の同意を付与

## 5. 実装例

### 5.1 認証設定

```python
# config/m365_config.py
import os

M365_CONFIG = {
    "client_id": os.getenv("M365_CLIENT_ID"),
    "client_secret": os.getenv("M365_CLIENT_SECRET"),
    "tenant_id": os.getenv("M365_TENANT_ID"),
    "authority": f"https://login.microsoftonline.com/{os.getenv('M365_TENANT_ID')}",
    "scope": ["Files.Read.All", "Sites.Read.All", "User.Read"],
    "redirect_uri": "http://localhost:5100/auth/m365/callback"
}
```

### 5.2 認証フロー

```python
from msal import ConfidentialClientApplication
from flask import redirect, url_for, session, request

def get_msal_app():
    """MSALアプリケーションインスタンス"""
    return ConfidentialClientApplication(
        M365_CONFIG["client_id"],
        authority=M365_CONFIG["authority"],
        client_credential=M365_CONFIG["client_secret"]
    )

@app.route("/auth/m365/login")
def m365_login():
    """Microsoft 365認証開始"""
    msal_app = get_msal_app()
    auth_url = msal_app.get_authorization_request_url(
        M365_CONFIG["scope"],
        redirect_uri=M365_CONFIG["redirect_uri"]
    )
    return redirect(auth_url)

@app.route("/auth/m365/callback")
def m365_callback():
    """認証コールバック"""
    if request.args.get('code'):
        msal_app = get_msal_app()
        result = msal_app.acquire_token_by_authorization_code(
            request.args['code'],
            scopes=M365_CONFIG["scope"],
            redirect_uri=M365_CONFIG["redirect_uri"]
        )
        if "access_token" in result:
            session["m365_token"] = result["access_token"]
            return redirect(url_for("m365_files"))
    return "認証エラー", 400
```

### 5.3 ファイル一覧取得

```python
import requests

def get_onedrive_files(access_token, folder_path="root"):
    """OneDriveからファイル一覧を取得"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    url = f"https://graph.microsoft.com/v1.0/me/drive/{folder_path}/children"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json().get("value", [])
    else:
        raise Exception(f"API Error: {response.status_code}")

def get_sharepoint_files(access_token, site_id, drive_id):
    """SharePointサイトからファイル一覧を取得"""
    headers = {"Authorization": f"Bearer {access_token}"}

    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root/children"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json().get("value", [])
    else:
        raise Exception(f"API Error: {response.status_code}")
```

### 5.4 ファイルダウンロード

```python
def download_file(access_token, item_id):
    """ファイルをダウンロード"""
    headers = {"Authorization": f"Bearer {access_token}"}

    url = f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}/content"
    response = requests.get(url, headers=headers, allow_redirects=True)

    return response.content
```

## 6. 環境変数設定

`.env`ファイルに以下を追加:

```bash
# Microsoft 365連携
M365_CLIENT_ID=your-client-id
M365_CLIENT_SECRET=your-client-secret
M365_TENANT_ID=your-tenant-id
```

## 7. セキュリティ考慮事項

1. **最小権限の原則**: `Sites.Selected`権限を使用して特定サイトのみアクセス
2. **証明書認証**: 本番環境ではクライアントシークレットより証明書認証を推奨
3. **トークン管理**: アクセストークンは安全に保存し、リフレッシュ処理を実装

## 8. 次のステップ

1. Azure ADアプリ登録
2. 環境変数設定
3. 認証エンドポイント実装
4. ファイル一覧API実装
5. インポート機能統合

---

## 参考リンク

- [Microsoft Graph API ドキュメント](https://learn.microsoft.com/ja-jp/graph/)
- [MSAL Python ドキュメント](https://github.com/AzureAD/microsoft-authentication-library-for-python)
- [SharePoint REST API](https://learn.microsoft.com/ja-jp/sharepoint/dev/sp-add-ins/get-to-know-the-sharepoint-rest-service)
