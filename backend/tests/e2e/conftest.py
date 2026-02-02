"""
E2Eテスト用 pytest フィクスチャ設定

このファイルはE2Eテスト専用のフィクスチャを提供します。
Playwrightのpageフィクスチャやbase_url設定を含みます。
"""

import os

import pytest
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="session")
def base_url():
    """
    テスト対象のベースURL

    環境変数 BASE_URL で上書き可能
    デフォルト: http://localhost:5100
    """
    return os.getenv("BASE_URL", "http://localhost:5100")


@pytest.fixture(scope="function")
def browser_context():
    """
    Playwrightブラウザコンテキストを提供

    各テスト関数ごとに新しいコンテキストを作成し、
    テスト終了後に自動的にクリーンアップします。
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True, args=["--disable-dev-shm-usage"]  # CI環境での安定性向上
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            ignore_https_errors=True,  # 自己署名証明書対応
        )
        yield context
        context.close()
        browser.close()


@pytest.fixture(scope="function")
def page(browser_context):
    """
    Playwrightページオブジェクトを提供

    テスト関数で `page` パラメータを指定することで、
    このフィクスチャが自動的に注入されます。

    使用例:
        def test_login(page, base_url):
            page.goto(f"{base_url}/login.html")
            # テストコード...
    """
    page = browser_context.new_page()
    yield page
    page.close()


@pytest.fixture(scope="function")
def authenticated_page(page, base_url):
    """
    認証済みのページオブジェクトを提供

    ログイン処理を自動的に実行した状態のページを返します。
    認証が必要なページのテストで使用します。

    使用例:
        def test_dashboard(authenticated_page, base_url):
            authenticated_page.goto(f"{base_url}/index.html")
            # 既にログイン済みの状態でテスト可能
    """
    # ログインページに移動
    page.goto(f"{base_url}/login.html")

    # テスト用の認証情報でログイン
    page.fill('input[name="username"]', "admin")
    page.fill('input[name="password"]', "admin")
    page.click('button[type="submit"]')

    # ログイン完了を待機
    page.wait_for_url(f"{base_url}/index.html", timeout=5000)

    yield page


@pytest.fixture(scope="function")
def test_data():
    """
    テストデータを提供

    E2Eテストで使用する共通のテストデータを定義します。
    """
    return {
        "admin_user": {"username": "admin", "password": "admin"},
        "test_knowledge": {
            "title": "E2Eテスト用ナレッジ",
            "content": "これはE2Eテスト用のサンプルコンテンツです。",
            "category": "建設",
        },
    }
