#!/usr/bin/env python3
"""
Phase H-1: app_v2.py Blueprint移行スクリプト

以下の変更を app_v2.py に適用する:
1. app_helpers からの共有ヘルパーインポートを追加
2. 認証APIルートを削除（blueprints/auth.py に移行済み）
3. 検索ヘルパーとナレッジAPIルートを削除（blueprints/knowledge.py に移行済み）
4. 通知ヘルパー（create_notification等）を削除（app_helpers.py に移行済み）
5. check_if_token_revoked を app_helpers._token_blacklist を使うよう更新
6. 重複するヘルパー関数を削除
7. 重複する CacheInvalidator / cache functions を削除
"""

import re
import sys
from pathlib import Path

APP_V2_PATH = Path(__file__).parent / "app_v2.py"
BACKUP_PATH = Path(__file__).parent / "app_v2.py.bak"

def main():
    # バックアップ作成
    content = APP_V2_PATH.read_text(encoding="utf-8")
    BACKUP_PATH.write_text(content, encoding="utf-8")
    print(f"[OK] Backup created: {BACKUP_PATH}")

    lines = content.splitlines(keepends=True)
    print(f"  Original lines: {len(lines)}")

    # ----------------------------------------------------------------
    # 変更 1: _file_lock ローカル定義を削除
    # ----------------------------------------------------------------
    content = content.replace(
        "# スレッドセーフなファイルアクセス用ロック\n_file_lock = threading.RLock()\n",
        "# _file_lock: app_helpers モジュールで管理（Phase H-1）\n",
    )
    print("[OK] Change 1: Removed local _file_lock definition")

    # ----------------------------------------------------------------
    # 変更 2: app_helpers インポートブロックを Blueprint 登録後に追加
    # ----------------------------------------------------------------
    IMPORT_BLOCK = '''
# ============================================================
# Phase H-1: 共有ヘルパーを app_helpers からインポート
# Blueprint (auth.py, knowledge.py) と同一シングルトンを共有するために必要
# ============================================================
from app_helpers import (
    _file_lock,
    _token_blacklist as _ah_token_blacklist,
    get_data_dir,
    get_dal,
    get_cache_key,
    cache_get,
    cache_set,
    CacheInvalidator,
    recommendation_engine,
    load_users,
    save_users,
    hash_password,
    verify_password,
    get_user_permissions,
    check_permission,
    validate_request,
    log_access,
    load_data,
    save_data,
    search_in_fields,
    highlight_text,
    create_notification,
)

'''

    blueprint_log_line = 'logger.info("[INIT] Blueprints registered: auth_bp (prefix=/api/v1/auth), knowledge_bp (prefix=/api/v1)")\n'
    if blueprint_log_line in content:
        content = content.replace(
            blueprint_log_line,
            blueprint_log_line + IMPORT_BLOCK,
        )
        print("[OK] Change 2: Added app_helpers import block after blueprint registration")
    else:
        print("[NG] Change 2: Could not find blueprint log line - skipping")

    # ----------------------------------------------------------------
    # 変更 3: キャッシュ関数と CacheInvalidator のローカル定義を削除
    # ----------------------------------------------------------------

    # get_cache_key の定義を削除
    old_cache_key_def = (
        "def get_cache_key(prefix, *args):\n"
        '    """キャッシュキー生成"""\n'
        '    return f"{prefix}:{\':\'.join(str(arg) for arg in args)}"\n'
    )
    if old_cache_key_def in content:
        content = content.replace(
            old_cache_key_def,
            "# get_cache_key: app_helpers で管理（Phase H-1）\n",
        )
        print("[OK] Change 3a: Removed local get_cache_key")
    else:
        print("[NG] Change 3a: get_cache_key not found - skipping")

    # cache_get の定義を削除
    old_cache_get_def = (
        "def cache_get(key):\n"
        '    """キャッシュ取得"""\n'
        "    if not CACHE_ENABLED or not redis_client:\n"
        "        return None\n"
        "    try:\n"
        "        data = redis_client.get(key)\n"
        "        return json.loads(data) if data else None\n"
        "    except Exception:\n"
        "        return None\n"
    )
    if old_cache_get_def in content:
        content = content.replace(
            old_cache_get_def,
            "# cache_get: app_helpers で管理（Phase H-1）\n",
        )
        print("[OK] Change 3b: Removed local cache_get")
    else:
        print("[NG] Change 3b: cache_get not found - skipping")

    # cache_set の定義を削除
    old_cache_set_def = (
        "def cache_set(key, value, ttl=CACHE_TTL):\n"
        '    """キャッシュ設定"""\n'
        "    if not CACHE_ENABLED or not redis_client:\n"
        "        return\n"
        "    try:\n"
        "        redis_client.setex(key, ttl, json.dumps(value))\n"
        "    except Exception as e:\n"
        '        logger.debug("Redis cache write failed for key: %s - %s", key, str(e))\n'
    )
    if old_cache_set_def in content:
        content = content.replace(
            old_cache_set_def,
            "# cache_set: app_helpers で管理（Phase H-1）\n",
        )
        print("[OK] Change 3c: Removed local cache_set")
    else:
        print("[NG] Change 3c: cache_set not found - skipping")

    # ----------------------------------------------------------------
    # 変更 4: recommendation_engine と get_dal のローカル定義を削除
    # ----------------------------------------------------------------

    # recommendation_engine ローカル定義を削除
    old_reco = "# 推薦エンジンインスタンス\nrecommendation_engine = RecommendationEngine(cache_ttl=300)  # 5分間キャッシュ\n"
    if old_reco in content:
        content = content.replace(
            old_reco,
            "# recommendation_engine: app_helpers で管理（Phase H-1）\n",
        )
        print("[OK] Change 4a: Removed local recommendation_engine")
    else:
        print("[NG] Change 4a: recommendation_engine not found - skipping")

    # get_dal のローカル定義（app.config.get("TESTING") 参照版）を削除
    old_get_dal = (
        "# DataAccessLayerインスタンス（グローバル）\n"
        "_dal = None\n"
        "\n"
        "\n"
        "def get_dal():\n"
        '    """DataAccessLayerインスタンスを取得"""\n'
        "    global _dal\n"
        "    if _dal is None:\n"
        '        use_pg = os.environ.get("MKS_USE_POSTGRESQL", "false").lower() in (\n'
        '            "true",\n'
        '            "1",\n'
        '            "yes",\n'
        "        )\n"
        "        # テスト環境では強制的にJSONモード\n"
        '        if app.config.get("TESTING"):\n'
        "            use_pg = False\n"
        "        _dal = DataAccessLayer(use_postgresql=use_pg)\n"
        "    return _dal\n"
    )
    if old_get_dal in content:
        content = content.replace(
            old_get_dal,
            "# get_dal: app_helpers で管理（PYTEST_CURRENT_TEST 対応、Phase H-1）\n",
        )
        print("[OK] Change 4b: Removed local get_dal (app.config.TESTING → PYTEST_CURRENT_TEST)")
    else:
        print("[NG] Change 4b: local get_dal not found - skipping")

    # ----------------------------------------------------------------
    # 変更 5: ヘルパー関数セクションを削除（app_helpers に移行済み）
    # ----------------------------------------------------------------
    HELPER_SECTION_START = "# ============================================================\n# ユーザー・権限管理（JSONベース）\n# ============================================================\n"
    HELPER_SECTION_END_MARKER = "\n\n# ============================================================\n# 認証API\n# ============================================================\n"

    if HELPER_SECTION_START in content and HELPER_SECTION_END_MARKER in content:
        start_idx = content.index(HELPER_SECTION_START)
        end_idx = content.index(HELPER_SECTION_END_MARKER)
        old_section = content[start_idx:end_idx]
        content = content.replace(
            old_section,
            "# load_users / save_users / check_permission 等: app_helpers で管理（Phase H-1）\n",
        )
        print("[OK] Change 5: Removed local helper function section (ユーザー権限管理)")
    else:
        print("[NG] Change 5: Helper section not found - skipping")

    # ----------------------------------------------------------------
    # 変更 6: 認証APIルートセクションを削除（blueprints/auth.py に移行済み）
    #         check_if_token_revoked のみ残す（app_helpers._token_blacklist を使用）
    # ----------------------------------------------------------------
    AUTH_SECTION_START = "# ============================================================\n# 認証API\n# ============================================================\n"
    # MS365連携セクションが始まるまで
    MS365_SECTION_START = "# ============================================================\n# Microsoft 365 連携 API\n# ============================================================\n"

    CHECK_TOKEN_CALLBACK = '''
# ============================================================
# JWT トークンブラックリストチェック（app_helpers._token_blacklist を参照）
# ============================================================


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    """トークンがブラックリストにあるかチェック（app_helpers._token_blacklist 参照）"""
    jti = jwt_payload["jti"]
    # _ah_token_blacklist は app_helpers からインポートした同一オブジェクト
    return jti in _ah_token_blacklist


'''

    if AUTH_SECTION_START in content and MS365_SECTION_START in content:
        start_idx = content.index(AUTH_SECTION_START)
        end_idx = content.index(MS365_SECTION_START)
        old_auth_section = content[start_idx:end_idx]
        content = content.replace(
            old_auth_section,
            "# 認証APIルート: blueprints/auth.py に移行済み（Phase H-1）\n" + CHECK_TOKEN_CALLBACK,
        )
        print("[OK] Change 6: Removed auth routes; kept check_if_token_revoked with app_helpers")
    else:
        print("[NG] Change 6: Auth API section not found - skipping")

    # ----------------------------------------------------------------
    # 変更 7: 検索ヘルパーとナレッジAPIルートを削除
    #         （blueprints/knowledge.py に移行済み）
    # ----------------------------------------------------------------
    SEARCH_HELPERS_START = "# ============================================================\n# 検索ヘルパー関数\n# ============================================================\n"
    NOTIFICATION_SECTION_START = "# ============================================================\n# 通知機能\n# ============================================================\n"

    if SEARCH_HELPERS_START in content and NOTIFICATION_SECTION_START in content:
        start_idx = content.index(SEARCH_HELPERS_START)
        end_idx = content.index(NOTIFICATION_SECTION_START)
        old_section = content[start_idx:end_idx]
        content = content.replace(
            old_section,
            "# 検索ヘルパー/ナレッジAPIルート: blueprints/knowledge.py に移行済み（Phase H-1）\n\n\n",
        )
        print("[OK] Change 7: Removed search helpers and knowledge API routes")
    else:
        print("[NG] Change 7: Search helpers / knowledge section not found - skipping")

    # ----------------------------------------------------------------
    # 変更 8: 通知ヘルパー関数を削除（app_helpers.py に移行済み）
    #         _get_user_notifications と通知ルートは残す
    # ----------------------------------------------------------------
    NOTIF_HELPERS_START = "\ndef _env_bool(name, default=False):\n"
    NOTIF_ROUTES_START = "\n\ndef _get_user_notifications(current_user_id, user_roles):\n"

    if NOTIF_HELPERS_START in content and NOTIF_ROUTES_START in content:
        start_idx = content.index(NOTIF_HELPERS_START)
        end_idx = content.index(NOTIF_ROUTES_START)
        old_section = content[start_idx:end_idx]
        content = content.replace(
            old_section,
            "\n# _env_bool / create_notification等: app_helpers で管理（Phase H-1）\n\n",
        )
        print("[OK] Change 8: Removed notification helpers (kept _get_user_notifications)")
    else:
        print("[NG] Change 8: Notification helpers section not found - skipping")

    # ----------------------------------------------------------------
    # 変更 9: CacheInvalidator クラス定義を削除（app_helpers に移行済み）
    # ----------------------------------------------------------------
    # CacheInvalidator は長いクラスなので、開始マーカーと終わりを見つけて削除
    CACHE_INV_START = "\nclass CacheInvalidator:\n"
    # 推薦エンジンか別の定義の前まで
    AFTER_CACHE_INV = "\n\n# 推薦エンジンインスタンス\n"
    if CACHE_INV_START in content and AFTER_CACHE_INV not in content:
        # 既に推薦エンジン定義は削除済みなので別マーカーを使用
        AFTER_CACHE_INV2 = "\n\n# recommendation_engine: app_helpers で管理"
        if CACHE_INV_START in content and AFTER_CACHE_INV2 in content:
            start_idx = content.index(CACHE_INV_START)
            end_idx = content.index(AFTER_CACHE_INV2)
            old_section = content[start_idx:end_idx]
            content = content.replace(
                old_section,
                "\n# CacheInvalidator: app_helpers で管理（Phase H-1）\n",
            )
            print("[OK] Change 9: Removed local CacheInvalidator class")
        else:
            print("[NG] Change 9: CacheInvalidator end marker not found - skipping")
    elif CACHE_INV_START in content and AFTER_CACHE_INV in content:
        start_idx = content.index(CACHE_INV_START)
        end_idx = content.index(AFTER_CACHE_INV)
        old_section = content[start_idx:end_idx]
        content = content.replace(
            old_section,
            "\n# CacheInvalidator: app_helpers で管理（Phase H-1）\n",
        )
        print("[OK] Change 9: Removed local CacheInvalidator class")
    else:
        print("[NG] Change 9: CacheInvalidator not found - skipping")

    # ----------------------------------------------------------------
    # 書き込み
    # ----------------------------------------------------------------
    APP_V2_PATH.write_text(content, encoding="utf-8")
    new_lines = content.splitlines()
    print(f"\n[OK] Written to: {APP_V2_PATH}")
    print(f"  New lines: {len(new_lines)}")
    print(f"  Reduction: {len(lines) - len(new_lines)} lines ({(len(lines) - len(new_lines)) / len(lines) * 100:.1f}%)")

if __name__ == "__main__":
    main()
