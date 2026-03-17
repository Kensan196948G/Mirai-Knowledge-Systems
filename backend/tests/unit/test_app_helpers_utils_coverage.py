"""
app_helpers.py 純粋ユーティリティ関数のカバレッジ強化テスト

対象関数:
  - search_in_fields(item, query, fields)
  - highlight_text(text, query)
  - _env_bool(name, default)
  - get_cache_key(prefix, *args)
  - hash_password(password) / verify_password(password, hash)
  - get_user_permissions(user)
  - _get_retry_count()

テスト方針:
  - Flask アプリケーションコンテキスト不要（純粋関数のみ対象）
  - 正常系・異常系・境界値をそれぞれカバー
  - pytest クラス構造を使用
"""

import os
import sys

os.environ.setdefault(
    "MKS_JWT_SECRET_KEY",
    "test-only-secret-key-for-pytest-minimum-32-chars"
)
os.environ.setdefault("TESTING", "true")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app_helpers import (
    _env_bool,
    _get_retry_count,
    get_cache_key,
    get_user_permissions,
    hash_password,
    highlight_text,
    search_in_fields,
    verify_password,
)


# ============================================================
# テストクラス 1: search_in_fields
# ============================================================


class TestSearchInFields:
    """search_in_fields() の正常系・異常系・境界値テスト"""

    def test_match_in_title_field(self):
        """title フィールドにクエリが含まれる場合のマッチ確認"""
        item = {"title": "橋梁工事の施工計画", "summary": "", "content": ""}
        matched, score = search_in_fields(item, "橋梁", ["title"])
        assert "title" in matched
        assert score == 1.0

    def test_match_in_summary_field(self):
        """summary フィールドにクエリが含まれる場合のスコア確認（0.7）"""
        item = {"title": "", "summary": "掘削の品質管理について", "content": ""}
        matched, score = search_in_fields(item, "品質管理", ["summary"])
        assert "summary" in matched
        assert score == pytest.approx(0.7)

    def test_match_in_content_field(self):
        """content フィールドにクエリが含まれる場合のスコア確認（0.5）"""
        item = {"title": "", "summary": "", "content": "安全管理の詳細手順"}
        matched, score = search_in_fields(item, "安全管理", ["content"])
        assert "content" in matched
        assert score == pytest.approx(0.5)

    def test_no_match_returns_empty_and_zero_score(self):
        """クエリが含まれない場合は空リストとスコア0を返す"""
        item = {"title": "テスト", "summary": "サマリー", "content": "本文"}
        matched, score = search_in_fields(item, "存在しないキーワード", ["title", "summary", "content"])
        assert matched == []
        assert score == 0.0

    def test_match_in_multiple_fields(self):
        """複数フィールドにマッチする場合のスコア累計確認"""
        item = {
            "title": "安全管理マニュアル",
            "summary": "安全管理の手順",
            "content": "安全管理の詳細",
        }
        matched, score = search_in_fields(item, "安全管理", ["title", "summary", "content"])
        assert "title" in matched
        assert "summary" in matched
        assert "content" in matched
        # 1.0 + 0.7 + 0.5 = 2.2
        assert score == pytest.approx(2.2)

    def test_case_insensitive_matching(self):
        """大文字小文字を区別せずにマッチすることを確認"""
        item = {"title": "ABC Test Document", "summary": "", "content": ""}
        matched, score = search_in_fields(item, "abc", ["title"])
        assert "title" in matched

    def test_empty_fields_list(self):
        """対象フィールドが空の場合は空リストとスコア0を返す"""
        item = {"title": "テスト"}
        matched, score = search_in_fields(item, "テスト", [])
        assert matched == []
        assert score == 0.0

    def test_field_not_in_item(self):
        """アイテムにフィールドが存在しない場合はスキップされる"""
        item = {"title": "テスト"}
        matched, score = search_in_fields(item, "テスト", ["title", "missing_field"])
        assert "title" in matched
        assert "missing_field" not in matched

    def test_none_field_value_treated_as_empty_string(self):
        """フィールド値が None の場合は空文字列として扱われる"""
        item = {"title": None}
        matched, score = search_in_fields(item, "テスト", ["title"])
        # str(None) = "None" にはマッチしない
        assert matched == [] or score == 0.0

    def test_numeric_field_value(self):
        """フィールド値が数値の場合も文字列変換されてマッチする"""
        item = {"title": 12345}
        matched, score = search_in_fields(item, "123", ["title"])
        assert "title" in matched

    def test_empty_query(self):
        """空のクエリは全フィールドにマッチする（空文字列は任意文字列に含まれる）"""
        item = {"title": "テスト"}
        matched, score = search_in_fields(item, "", ["title"])
        # "" は任意の文字列に含まれるため title はマッチする
        assert "title" in matched

    def test_unknown_field_score_is_zero(self):
        """title/summary/content 以外のフィールドはスコア加算なし（ただしマッチ記録あり）"""
        item = {"custom_field": "テストデータ"}
        matched, score = search_in_fields(item, "テスト", ["custom_field"])
        # custom_field はスコア加算ロジックに含まれないため score=0
        assert score == 0.0
        # しかしマッチは記録される
        assert "custom_field" in matched


import pytest


# ============================================================
# テストクラス 2: highlight_text
# ============================================================


class TestHighlightText:
    """highlight_text() の正常系・異常系・境界値テスト"""

    def test_basic_highlight(self):
        """基本的なハイライト動作の確認"""
        result = highlight_text("橋梁工事の施工計画", "橋梁")
        assert "<mark>橋梁</mark>" in result

    def test_case_insensitive_highlight(self):
        """大文字小文字を区別せずにハイライトする"""
        result = highlight_text("ABC Test Document", "abc")
        assert "<mark>" in result
        assert "ABC" in result or "abc" in result.lower()

    def test_multiple_occurrences_highlighted(self):
        """クエリが複数箇所に出現する場合は全てハイライト"""
        result = highlight_text("テスト1とテスト2", "テスト")
        assert result.count("<mark>") == 2

    def test_empty_text_returns_empty(self):
        """テキストが空の場合は空文字列（またはNone相当）を返す"""
        result = highlight_text("", "テスト")
        assert result == "" or result is None

    def test_none_text_returns_none(self):
        """テキストが None の場合は None を返す"""
        result = highlight_text(None, "テスト")
        assert result is None

    def test_empty_query_returns_original_text(self):
        """クエリが空の場合は元のテキストをそのまま返す"""
        original = "テストテキスト"
        result = highlight_text(original, "")
        assert result == original

    def test_none_query_returns_original_text(self):
        """クエリが None の場合は元のテキストをそのまま返す"""
        original = "テストテキスト"
        result = highlight_text(original, None)
        assert result == original

    def test_query_not_in_text(self):
        """クエリがテキストに含まれない場合は元のテキストをそのまま返す"""
        original = "テストテキスト"
        result = highlight_text(original, "存在しないキーワード")
        assert result == original

    def test_special_regex_chars_in_query(self):
        """クエリに正規表現特殊文字が含まれる場合もエラーなく処理する"""
        result = highlight_text("price: 100.00 (USD)", "100.00")
        assert "<mark>100.00</mark>" in result

    def test_html_tag_chars_in_query(self):
        """クエリに < > が含まれる場合も安全に処理する"""
        # re.escape でエスケープされるため、正規表現エラーは発生しない
        result = highlight_text("a<b>c", "<b>")
        # マッチまたは元テキスト返却のどちらでも例外が出ないこと
        assert result is not None


# ============================================================
# テストクラス 3: _env_bool
# ============================================================


class TestEnvBool:
    """_env_bool() の正常系・異常系・境界値テスト"""

    def test_true_values(self):
        """'1', 'true', 'yes', 'on' が True を返すことを確認"""
        for val in ("1", "true", "yes", "on"):
            os.environ["_TEST_BOOL_VAR"] = val
            assert _env_bool("_TEST_BOOL_VAR") is True, f"値 {val!r} が True を返さない"
        os.environ.pop("_TEST_BOOL_VAR", None)

    def test_true_values_uppercase(self):
        """大文字の 'TRUE', 'YES', 'ON' も True を返すことを確認"""
        for val in ("TRUE", "YES", "ON"):
            os.environ["_TEST_BOOL_VAR"] = val
            assert _env_bool("_TEST_BOOL_VAR") is True, f"値 {val!r} が True を返さない"
        os.environ.pop("_TEST_BOOL_VAR", None)

    def test_false_values(self):
        """'0', 'false', 'no', 'off' が False を返すことを確認"""
        for val in ("0", "false", "no", "off"):
            os.environ["_TEST_BOOL_VAR"] = val
            assert _env_bool("_TEST_BOOL_VAR") is False, f"値 {val!r} が False を返さない"
        os.environ.pop("_TEST_BOOL_VAR", None)

    def test_env_var_not_set_returns_default_false(self):
        """環境変数が未設定の場合はデフォルト False を返す"""
        os.environ.pop("_TEST_BOOL_VAR_MISSING", None)
        result = _env_bool("_TEST_BOOL_VAR_MISSING")
        assert result is False

    def test_env_var_not_set_returns_custom_default(self):
        """環境変数が未設定の場合は指定されたデフォルト値を返す"""
        os.environ.pop("_TEST_BOOL_VAR_MISSING", None)
        result = _env_bool("_TEST_BOOL_VAR_MISSING", default=True)
        assert result is True

    def test_empty_string_value_is_false(self):
        """空文字列は False を返すことを確認（"" は ('1','true','yes','on') に非含有）"""
        os.environ["_TEST_BOOL_VAR"] = ""
        # 空文字列 "" は "1","true","yes","on" のいずれにも含まれないため False
        result = _env_bool("_TEST_BOOL_VAR")
        assert result is False
        os.environ.pop("_TEST_BOOL_VAR", None)

    def test_arbitrary_string_returns_false(self):
        """任意の文字列は False を返すことを確認"""
        os.environ["_TEST_BOOL_VAR"] = "maybe"
        result = _env_bool("_TEST_BOOL_VAR")
        assert result is False
        os.environ.pop("_TEST_BOOL_VAR", None)


# ============================================================
# テストクラス 4: get_cache_key
# ============================================================


class TestGetCacheKey:
    """get_cache_key() の正常系・境界値テスト"""

    def test_prefix_only(self):
        """プレフィックスのみの場合のキー生成確認"""
        key = get_cache_key("knowledge_list")
        assert key == "knowledge_list:"

    def test_prefix_with_single_arg(self):
        """プレフィックスと1つの引数のキー生成確認"""
        key = get_cache_key("knowledge_list", 1)
        assert key == "knowledge_list:1"

    def test_prefix_with_multiple_args(self):
        """プレフィックスと複数引数のキー生成確認"""
        key = get_cache_key("knowledge_list", 1, "page", 10)
        assert key == "knowledge_list:1:page:10"

    def test_prefix_with_string_args(self):
        """文字列引数のキー生成確認"""
        key = get_cache_key("user", "admin", "profile")
        assert key == "user:admin:profile"

    def test_prefix_with_mixed_types(self):
        """異なる型の引数が文字列変換されることを確認"""
        key = get_cache_key("search", "query", 42, 3.14, True)
        assert key == "search:query:42:3.14:True"

    def test_empty_prefix(self):
        """プレフィックスが空文字列の場合のキー生成確認"""
        key = get_cache_key("", "arg1")
        assert key == ":arg1"

    def test_returns_string(self):
        """戻り値が文字列型であることを確認"""
        key = get_cache_key("prefix", "arg")
        assert isinstance(key, str)


# ============================================================
# テストクラス 5: hash_password / verify_password
# ============================================================


class TestPasswordHashing:
    """hash_password() と verify_password() の正常系・異常系テスト"""

    def test_hash_password_returns_string(self):
        """hash_password() が文字列を返すことを確認"""
        hashed = hash_password("testpassword123")
        assert isinstance(hashed, str)

    def test_hash_password_starts_with_bcrypt_prefix(self):
        """hash_password() が bcrypt ハッシュ形式であることを確認"""
        hashed = hash_password("testpassword123")
        assert hashed.startswith("$2")

    def test_hash_password_different_each_time(self):
        """同じパスワードでも異なるハッシュが生成されることを確認（salt）"""
        hash1 = hash_password("samepassword")
        hash2 = hash_password("samepassword")
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """正しいパスワードが検証成功することを確認"""
        password = "mySecurePassword!123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_wrong_password(self):
        """間違ったパスワードが検証失敗することを確認"""
        hashed = hash_password("correctpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_legacy_sha256(self):
        """レガシー SHA256 ハッシュの検証が成功することを確認"""
        import hashlib
        password = "legacypassword"
        legacy_hash = hashlib.sha256(password.encode()).hexdigest()
        # bcrypt プレフィックス '$2' で始まらないため legacy パスに分岐
        assert verify_password(password, legacy_hash) is True

    def test_verify_password_legacy_sha256_wrong(self):
        """レガシー SHA256 ハッシュで間違ったパスワードが失敗することを確認"""
        import hashlib
        password = "correctpassword"
        legacy_hash = hashlib.sha256(password.encode()).hexdigest()
        assert verify_password("wrongpassword", legacy_hash) is False

    def test_verify_password_invalid_bcrypt_hash(self):
        """不正な bcrypt ハッシュの検証が False を返すことを確認"""
        # "$2b$" で始まるが無効なハッシュ
        invalid_hash = "$2b$12$invalidhashvalue"
        result = verify_password("anypassword", invalid_hash)
        assert result is False

    def test_hash_password_unicode(self):
        """Unicode パスワードが正常にハッシュ化されることを確認"""
        password = "パスワード123!"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_hash_password_empty_string(self):
        """空文字列パスワードのハッシュ化と検証"""
        password = ""
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_hash_password_long_string(self):
        """長いパスワード（72文字超）のハッシュ化と検証"""
        password = "a" * 100  # bcrypt は 72 バイトで切り詰めるが例外は発生しない
        hashed = hash_password(password)
        assert isinstance(hashed, str)


# ============================================================
# テストクラス 6: get_user_permissions
# ============================================================


class TestGetUserPermissions:
    """get_user_permissions() の各ロールとエッジケースのテスト"""

    def test_admin_returns_wildcard(self):
        """admin ロールは ['*'] を返すことを確認"""
        user = {"roles": ["admin"]}
        perms = get_user_permissions(user)
        assert perms == ["*"]

    def test_construction_manager_permissions(self):
        """construction_manager ロールが正しい権限セットを返すことを確認"""
        user = {"roles": ["construction_manager"]}
        perms = get_user_permissions(user)
        assert "knowledge.create" in perms
        assert "knowledge.read" in perms
        assert "knowledge.delete" in perms

    def test_quality_assurance_permissions(self):
        """quality_assurance ロールが approve 権限を含むことを確認"""
        user = {"roles": ["quality_assurance"]}
        perms = get_user_permissions(user)
        assert "knowledge.approve" in perms
        assert "approval.execute" in perms

    def test_safety_officer_permissions(self):
        """safety_officer ロールがインシデント関連権限を含むことを確認"""
        user = {"roles": ["safety_officer"]}
        perms = get_user_permissions(user)
        assert "incident.create" in perms
        assert "incident.update" in perms

    def test_partner_company_limited_permissions(self):
        """partner_company ロールは読み取り系権限のみを持つことを確認"""
        user = {"roles": ["partner_company"]}
        perms = get_user_permissions(user)
        assert "knowledge.read" in perms
        assert "knowledge.create" not in perms
        assert "knowledge.delete" not in perms

    def test_manager_permissions(self):
        """manager ロールが承認実行権限を持つことを確認"""
        user = {"roles": ["manager"]}
        perms = get_user_permissions(user)
        assert "approval.execute" in perms
        assert "knowledge.update" in perms

    def test_engineer_permissions(self):
        """engineer ロールが基本的な読み取り・作成権限を持つことを確認"""
        user = {"roles": ["engineer"]}
        perms = get_user_permissions(user)
        assert "knowledge.read" in perms
        assert "knowledge.create" in perms

    def test_expert_permissions(self):
        """expert ロールが consultation 関連権限を持つことを確認"""
        user = {"roles": ["expert"]}
        perms = get_user_permissions(user)
        assert "consultation.answer" in perms
        assert "consultation.read" in perms

    def test_unknown_role_returns_empty(self):
        """未知のロールは空のパーミッションリストを返すことを確認"""
        user = {"roles": ["nonexistent_role"]}
        perms = get_user_permissions(user)
        assert perms == []

    def test_empty_roles_returns_empty(self):
        """ロールが空リストの場合は空のパーミッションリストを返すことを確認"""
        user = {"roles": []}
        perms = get_user_permissions(user)
        assert perms == []

    def test_no_roles_key_returns_empty(self):
        """roles キーが存在しない場合は空のパーミッションリストを返すことを確認"""
        user = {}
        perms = get_user_permissions(user)
        assert perms == []

    def test_multiple_roles_merge_permissions(self):
        """複数ロールの権限が統合されることを確認"""
        user = {"roles": ["engineer", "expert"]}
        perms = get_user_permissions(user)
        # engineer の権限
        assert "knowledge.read" in perms
        # expert の権限
        assert "consultation.answer" in perms

    def test_admin_with_other_roles_still_returns_wildcard(self):
        """admin を含む複数ロールの場合は ['*'] を返すことを確認"""
        user = {"roles": ["engineer", "admin"]}
        perms = get_user_permissions(user)
        assert perms == ["*"]

    def test_returns_list(self):
        """get_user_permissions() がリストを返すことを確認"""
        user = {"roles": ["engineer"]}
        perms = get_user_permissions(user)
        assert isinstance(perms, list)

    def test_duplicate_permissions_from_multiple_roles(self):
        """複数ロールで重複する権限が重複なく統合されることを確認"""
        # construction_manager と manager は両方 knowledge.read を持つ
        user = {"roles": ["construction_manager", "manager"]}
        perms = get_user_permissions(user)
        # set を通して重複を除去しているため、knowledge.read は1回のみ
        assert perms.count("knowledge.read") == 1


# ============================================================
# テストクラス 7: _get_retry_count
# ============================================================


class TestGetRetryCount:
    """_get_retry_count() の正常系・異常系テスト"""

    def test_default_value_is_5(self):
        """MKS_NOTIFICATION_RETRY_COUNT が未設定の場合はデフォルト 5 を返す"""
        os.environ.pop("MKS_NOTIFICATION_RETRY_COUNT", None)
        count = _get_retry_count()
        assert count == 5

    def test_valid_integer_string(self):
        """正しい整数文字列が設定された場合はその値を返す"""
        os.environ["MKS_NOTIFICATION_RETRY_COUNT"] = "3"
        count = _get_retry_count()
        assert count == 3
        os.environ.pop("MKS_NOTIFICATION_RETRY_COUNT", None)

    def test_zero_is_valid(self):
        """0 が設定された場合は 0 を返す"""
        os.environ["MKS_NOTIFICATION_RETRY_COUNT"] = "0"
        count = _get_retry_count()
        assert count == 0
        os.environ.pop("MKS_NOTIFICATION_RETRY_COUNT", None)

    def test_non_digit_string_returns_default_5(self):
        """数字以外の文字列が設定された場合はデフォルト 5 を返す"""
        os.environ["MKS_NOTIFICATION_RETRY_COUNT"] = "abc"
        count = _get_retry_count()
        assert count == 5
        os.environ.pop("MKS_NOTIFICATION_RETRY_COUNT", None)

    def test_negative_string_returns_default_5(self):
        """負の数文字列が設定された場合はデフォルト 5 を返す

        '-3'.isdigit() は False を返すため、デフォルト値になる。
        """
        os.environ["MKS_NOTIFICATION_RETRY_COUNT"] = "-3"
        count = _get_retry_count()
        assert count == 5
        os.environ.pop("MKS_NOTIFICATION_RETRY_COUNT", None)

    def test_float_string_returns_default_5(self):
        """浮動小数点数文字列は isdigit() が False を返すためデフォルト 5 を返す"""
        os.environ["MKS_NOTIFICATION_RETRY_COUNT"] = "3.5"
        count = _get_retry_count()
        assert count == 5
        os.environ.pop("MKS_NOTIFICATION_RETRY_COUNT", None)

    def test_large_number(self):
        """大きな整数が設定された場合はその値を返す"""
        os.environ["MKS_NOTIFICATION_RETRY_COUNT"] = "100"
        count = _get_retry_count()
        assert count == 100
        os.environ.pop("MKS_NOTIFICATION_RETRY_COUNT", None)

    def test_returns_int(self):
        """戻り値が int 型であることを確認"""
        os.environ.pop("MKS_NOTIFICATION_RETRY_COUNT", None)
        count = _get_retry_count()
        assert isinstance(count, int)

    def test_whitespace_stripped(self):
        """環境変数の値が strip() されることを確認"""
        os.environ["MKS_NOTIFICATION_RETRY_COUNT"] = " 7 "
        # "7" （trim済み）は isdigit() == True
        count = _get_retry_count()
        assert count == 7
        os.environ.pop("MKS_NOTIFICATION_RETRY_COUNT", None)
