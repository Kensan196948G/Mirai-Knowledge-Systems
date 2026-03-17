"""
blueprints/utils/health_bp.py カバレッジ強化テスト (v2)

残り未カバー4行を狙い撃ち:
  1. lines 81-82: get_metrics() の except (ValueError, TypeError): continue
  2. line 291:    serve_static() フォントファイルキャッシュヘッダー
  3. line 294:    serve_static() HTMLファイルキャッシュヘッダー
"""

import json
import os
import shutil
import sys
import tempfile
import time

import pytest

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, BACKEND_DIR)


# ---------------------------------------------------------------------------
# serve_static テスト用フィクスチャ
# app_v2.app の static_folder を一時ディレクトリに差し替えてテストする
# ---------------------------------------------------------------------------


@pytest.fixture()
def static_app_client(monkeypatch):
    """serve_static() のファイルタイプ別キャッシュをテストするための
    専用クライアント。一時ディレクトリに各種ファイルを配置して
    app.static_folder を差し替える。"""
    import app_v2

    static_dir = tempfile.mkdtemp(prefix="health_bp_test_static_")

    # フォントファイル
    for fname in ("test.woff", "test.woff2", "test.ttf", "test.eot"):
        with open(os.path.join(static_dir, fname), "wb") as f:
            f.write(b"\x00\x01\x02\x03")

    # 画像ファイル (line 288 カバー用)
    for fname in ("test.png", "test.jpg", "test.svg"):
        with open(os.path.join(static_dir, fname), "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n")

    # HTMLファイル (serve_static ルート経由: /some.html)
    with open(os.path.join(static_dir, "about.html"), "w", encoding="utf-8") as f:
        f.write("<html><body>About</body></html>")

    # index.html (index() ルートで使用)
    with open(os.path.join(static_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write("<html><body>Index</body></html>")

    app = app_v2.app
    original_static = app.static_folder
    app.static_folder = static_dir
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client

    # teardown: 元に戻してから一時ディレクトリを削除
    app.static_folder = original_static
    shutil.rmtree(static_dir, ignore_errors=True)


# ===========================================================================
# 1) get_metrics — 無効タイムスタンプによる except (ValueError, TypeError)
# ===========================================================================


class TestGetMetricsInvalidTimestamp:
    """get_metrics() 内のアクセスログ解析で無効なタイムスタンプが
    ValueError / TypeError を発生させ、except ブロック (lines 81-82) を通過する。"""

    def test_invalid_timestamp_string_is_skipped(self, client, tmp_path):
        """timestamp が不正な文字列 → ValueError → continue"""
        logs = [
            {
                "user_id": 1,
                "action": "page.view",
                "status": "success",
                "timestamp": "not-a-valid-date",
                "session_id": "sess-bad-1",
            },
        ]
        (tmp_path / "access_logs.json").write_text(
            json.dumps(logs, ensure_ascii=False), encoding="utf-8"
        )

        resp = client.get("/api/v1/metrics")
        assert resp.status_code == 200
        # 不正ログはスキップされるため active_users は 0 のまま
        assert b"active_users 0" in resp.data

    def test_none_timestamp_is_skipped(self, client, tmp_path):
        """timestamp が None → TypeError → continue"""
        logs = [
            {
                "user_id": 2,
                "action": "auth.login",
                "status": "success",
                "timestamp": None,
                "session_id": "sess-bad-2",
            },
        ]
        (tmp_path / "access_logs.json").write_text(
            json.dumps(logs, ensure_ascii=False), encoding="utf-8"
        )

        resp = client.get("/api/v1/metrics")
        assert resp.status_code == 200
        # None タイムスタンプのログインもスキップ → success カウント 0
        assert b"active_users 0" in resp.data

    def test_missing_timestamp_key_is_skipped(self, client, tmp_path):
        """timestamp キーが存在しない → get() は "" を返し fromisoformat で ValueError"""
        logs = [
            {
                "user_id": 3,
                "action": "auth.login",
                "status": "failure",
                "session_id": "sess-bad-3",
            },
        ]
        (tmp_path / "access_logs.json").write_text(
            json.dumps(logs, ensure_ascii=False), encoding="utf-8"
        )

        resp = client.get("/api/v1/metrics")
        assert resp.status_code == 200

    def test_mix_valid_and_invalid_timestamps(self, client, tmp_path):
        """有効・無効なタイムスタンプが混在 → 無効分のみスキップ"""
        from datetime import datetime

        now_iso = datetime.now().isoformat()
        logs = [
            # 有効: カウントされる
            {
                "user_id": 10,
                "action": "auth.login",
                "status": "success",
                "timestamp": now_iso,
                "session_id": "sess-ok-1",
            },
            # 無効: スキップ (ValueError)
            {
                "user_id": 20,
                "action": "auth.login",
                "status": "success",
                "timestamp": "INVALID",
                "session_id": "sess-bad-4",
            },
            # 無効: スキップ (TypeError)
            {
                "user_id": 30,
                "action": "auth.login",
                "status": "failure",
                "timestamp": None,
                "session_id": "sess-bad-5",
            },
        ]
        (tmp_path / "access_logs.json").write_text(
            json.dumps(logs, ensure_ascii=False), encoding="utf-8"
        )

        resp = client.get("/api/v1/metrics")
        assert resp.status_code == 200
        text = resp.data.decode("utf-8")
        # 有効な1件のみカウント
        assert "active_users 1" in text
        # login success は有効な1件のみ (無効な2件はスキップ)
        assert 'login_attempts_total{status="success"} 1' in text


# ===========================================================================
# 2a) serve_static — 画像ファイルのキャッシュヘッダー (line 288)
# ===========================================================================


class TestServeStaticImageCache:
    """serve_static() で画像ファイル (.png, .jpg, .svg) を
    リクエストしたときに Cache-Control: public, max-age=86400 が設定される。"""

    def test_png_file_cache_header(self, static_app_client):
        resp = static_app_client.get("/test.png")
        assert resp.status_code == 200
        assert resp.headers.get("Cache-Control") == "public, max-age=86400"

    def test_jpg_file_cache_header(self, static_app_client):
        resp = static_app_client.get("/test.jpg")
        assert resp.status_code == 200
        assert resp.headers.get("Cache-Control") == "public, max-age=86400"

    def test_svg_file_cache_header(self, static_app_client):
        resp = static_app_client.get("/test.svg")
        assert resp.status_code == 200
        assert resp.headers.get("Cache-Control") == "public, max-age=86400"


# ===========================================================================
# 2b) serve_static — フォントファイルのキャッシュヘッダー (line 291)
# ===========================================================================


class TestServeStaticFontCache:
    """serve_static() でフォントファイル (.woff, .woff2, .ttf, .eot) を
    リクエストしたときに Cache-Control: public, max-age=604800 が設定される。"""

    def test_woff_file_cache_header(self, static_app_client):
        resp = static_app_client.get("/test.woff")
        assert resp.status_code == 200
        assert resp.headers.get("Cache-Control") == "public, max-age=604800"

    def test_woff2_file_cache_header(self, static_app_client):
        resp = static_app_client.get("/test.woff2")
        assert resp.status_code == 200
        assert resp.headers.get("Cache-Control") == "public, max-age=604800"

    def test_ttf_file_cache_header(self, static_app_client):
        resp = static_app_client.get("/test.ttf")
        assert resp.status_code == 200
        assert resp.headers.get("Cache-Control") == "public, max-age=604800"

    def test_eot_file_cache_header(self, static_app_client):
        resp = static_app_client.get("/test.eot")
        assert resp.status_code == 200
        assert resp.headers.get("Cache-Control") == "public, max-age=604800"


# ===========================================================================
# 3) serve_static — HTMLファイルのキャッシュヘッダー (line 294)
# ===========================================================================


class TestServeStaticHtmlCache:
    """serve_static() で .html ファイル (index.html 以外) をリクエストしたときに
    Cache-Control: no-cache, no-store, must-revalidate が設定される。"""

    def test_html_file_no_cache_header(self, static_app_client):
        resp = static_app_client.get("/about.html")
        assert resp.status_code == 200
        cache_control = resp.headers.get("Cache-Control", "")
        assert "no-cache" in cache_control
        assert "no-store" in cache_control
        assert "must-revalidate" in cache_control

    def test_html_file_pragma_header(self, static_app_client):
        resp = static_app_client.get("/about.html")
        assert resp.status_code == 200
        assert resp.headers.get("Pragma") == "no-cache"

    def test_html_file_expires_header(self, static_app_client):
        resp = static_app_client.get("/about.html")
        assert resp.status_code == 200
        assert resp.headers.get("Expires") == "0"
