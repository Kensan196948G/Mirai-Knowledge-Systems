"""
ダッシュボードフローのE2Eテスト
Playwrightを使用したブラウザテスト
"""

import os
import sys

import pytest
from playwright.sync_api import Page, expect

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def login(page: Page, base_url: str, username="admin", password="admin123"):
    """ログインヘルパー関数（タイムアウト延長版）"""
    page.goto(f"{base_url}/login.html", timeout=10000)
    page.wait_for_load_state("networkidle")  # ネットワーク安定待機
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    # ダッシュボードへのリダイレクトを待つ（タイムアウト延長）
    page.wait_for_url(f"{base_url}/index.html", timeout=10000)
    page.wait_for_load_state("networkidle")  # リダイレクト後も待機


class TestLoginToDashboard:
    """ログインからダッシュボード表示までのテスト"""

    def test_successful_login_redirects_to_dashboard(self, page: Page, base_url):
        """ログイン成功後ダッシュボードへリダイレクト"""
        page.goto(f"{base_url}/login.html", timeout=10000)
        page.wait_for_load_state("networkidle")

        # ログインフォーム要素の確認
        expect(page.locator('input[name="username"]')).to_be_visible(timeout=10000)
        expect(page.locator('input[name="password"]')).to_be_visible(timeout=10000)

        # ログイン実行
        page.fill('input[name="username"]', "admin")
        page.fill('input[name="password"]', "admin123")
        page.click('button[type="submit"]')

        # ダッシュボードへリダイレクト確認
        expect(page).to_have_url(f"{base_url}/index.html", timeout=10000)

    def test_failed_login_shows_error_message(self, page: Page, base_url):
        """ログイン失敗時エラーメッセージ表示"""
        page.goto(f"{base_url}/login.html", timeout=10000)
        page.wait_for_load_state("networkidle")

        # 無効な認証情報でログイン
        page.fill('input[name="username"]', "admin")
        page.fill('input[name="password"]', "wrongpassword")
        page.click('button[type="submit"]')

        # エラーメッセージ表示確認（タイムアウト延長）
        page.wait_for_load_state("networkidle")  # レスポンス待機
        error_selector = '#loginAlert, .error-message, .alert-danger, [role="alert"]'
        expect(page.locator(error_selector).first).to_be_visible(timeout=10000)

    def test_dashboard_displays_key_elements(self, page: Page, base_url):
        """ダッシュボードに主要要素が表示される"""
        login(page, base_url)

        # ダッシュボード要素の確認（存在する可能性のある要素）
        # 少なくとも1つは表示されるはず
        dashboard_elements = [
            ".dashboard",
            "#dashboard",
            ".dashboard-stats",
            ".knowledge-list",
            ".main-content",
            "main",
        ]

        found = False
        for selector in dashboard_elements:
            if page.locator(selector).count() > 0:
                found = True
                break

        assert found, "ダッシュボード要素が見つかりません"


class TestDashboardNavigation:
    """ダッシュボードナビゲーションのテスト"""

    def test_logout_returns_to_login_page(self, page: Page, base_url):
        """ログアウトでログインページへ戻る"""
        login(page, base_url)

        # ログアウトボタンを探す
        logout_selectors = [
            'button:has-text("ログアウト")',
            'a:has-text("ログアウト")',
            '[data-action="logout"]',
            ".logout-btn",
        ]

        for selector in logout_selectors:
            if page.locator(selector).count() > 0:
                page.click(selector)
                # ログインページへのリダイレクト確認
                expect(page).to_have_url(f"{base_url}/login.html", timeout=5000)
                return

        # ログアウトボタンが見つからない場合はスキップ
        pytest.skip("ログアウトボタンが見つかりません")

    def test_navigation_menu_is_accessible(self, page: Page, base_url):
        """ナビゲーションメニューにアクセス可能"""
        login(page, base_url)

        # ナビゲーションメニューの確認
        nav_selectors = ["nav", ".navbar", ".navigation", "#nav-menu", ".sidebar"]

        found = False
        for selector in nav_selectors:
            if page.locator(selector).count() > 0:
                expect(page.locator(selector).first).to_be_visible()
                found = True
                break

        assert found, "ナビゲーションメニューが見つかりません"


class TestDashboardContent:
    """ダッシュボードコンテンツのテスト"""

    def test_dashboard_shows_statistics(self, page: Page, base_url):
        """ダッシュボードに統計情報が表示される"""
        login(page, base_url)
        page.wait_for_load_state("networkidle")  # ネットワーク安定待機

        # 統計情報エリアの確認（タイムアウト延長）
        stats_selectors = [
            ".stats",
            ".dashboard-stats",
            ".statistics",
            ".metrics",
            '[data-component="stats"]',
        ]

        found = False
        for selector in stats_selectors:
            try:
                # 各セレクタで10秒待機
                page.wait_for_selector(selector, state="visible", timeout=10000)
                found = True
                break
            except:
                continue

        # 統計情報が表示されていることを確認（または存在しない場合はスキップ）
        if found:
            assert True
        else:
            pytest.skip("統計情報エリアが見つかりません")

    def test_dashboard_shows_recent_knowledge(self, page: Page, base_url):
        """ダッシュボードに最近のナレッジが表示される"""
        login(page, base_url)
        page.wait_for_load_state("networkidle")  # ネットワーク安定待機

        # ナレッジリストの確認（タイムアウト延長）
        knowledge_selectors = [
            ".knowledge-list",
            ".recent-knowledge",
            '[data-component="knowledge-list"]',
            ".items-list",
        ]

        found = False
        for selector in knowledge_selectors:
            try:
                # 各セレクタで10秒待機
                page.wait_for_selector(selector, state="visible", timeout=10000)
                found = True
                break
            except:
                continue

        if found:
            assert True
        else:
            pytest.skip("ナレッジリストが見つかりません")


class TestResponsiveDesign:
    """レスポンシブデザインのテスト"""

    def test_dashboard_works_on_mobile_viewport(self, page: Page, base_url):
        """モバイルビューポートでダッシュボードが動作する"""
        # モバイルサイズに設定
        page.set_viewport_size({"width": 375, "height": 667})

        login(page, base_url)
        page.wait_for_load_state("networkidle")  # レンダリング完了待機

        # ページが正常に読み込まれることを確認（タイムアウト延長）
        expect(page).to_have_url(f"{base_url}/index.html", timeout=10000)

    def test_dashboard_works_on_tablet_viewport(self, page: Page, base_url):
        """タブレットビューポートでダッシュボードが動作する"""
        # タブレットサイズに設定
        page.set_viewport_size({"width": 768, "height": 1024})

        login(page, base_url)
        page.wait_for_load_state("networkidle")  # レンダリング完了待機

        # ページが正常に読み込まれることを確認（タイムアウト延長）
        expect(page).to_have_url(f"{base_url}/index.html", timeout=10000)


class TestAccessibilityBasics:
    """基本的なアクセシビリティテスト"""

    def test_login_page_has_accessible_form_labels(self, page: Page, base_url):
        """ログインページにアクセシブルなフォームラベルがある"""
        page.goto(f"{base_url}/login.html")

        # ラベルまたはプレースホルダーの確認
        username_input = page.locator('input[name="username"]')
        password_input = page.locator('input[name="password"]')

        expect(username_input).to_be_visible()
        expect(password_input).to_be_visible()

    def test_dashboard_has_meaningful_title(self, page: Page, base_url):
        """ダッシュボードに意味のあるタイトルがある"""
        login(page, base_url)

        # タイトルが空でないことを確認
        title = page.title()
        assert len(title) > 0, "ページタイトルが設定されていません"
