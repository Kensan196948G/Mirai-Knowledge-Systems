"""
パスワードハッシュ化機能のユニットテスト
"""

import os
import sys

import pytest

# backend ディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app_v2 import hash_password, verify_password


class TestPasswordHashing:
    """パスワードハッシュ化のテストクラス"""

    def test_hash_password_returns_valid_bcrypt_hash(self):
        """bcryptハッシュが正しく生成される"""
        password = "test123"
        hashed = hash_password(password)

        # bcryptハッシュは$2で始まる
        assert hashed.startswith("$2")
        assert isinstance(hashed, str)
        assert len(hashed) == 60  # bcryptハッシュは60文字

    def test_different_passwords_produce_different_hashes(self):
        """異なるパスワードは異なるハッシュを生成"""
        password1 = "test123"
        password2 = "test456"

        hash1 = hash_password(password1)
        hash2 = hash_password(password2)

        assert hash1 != hash2

    def test_same_password_produces_different_hashes_due_to_salt(self):
        """bcryptはソルトを使うため、同じパスワードでも異なるハッシュ"""
        password = "test123"

        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # ハッシュは異なるが、両方とも検証可能
        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_verify_password_with_correct_password_returns_true(self):
        """正しいパスワードで検証するとTrueを返す"""
        password = "test123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_with_wrong_password_returns_false(self):
        """誤ったパスワードで検証するとFalseを返す"""
        password = "test123"
        hashed = hash_password(password)

        assert verify_password("wrong", hashed) is False

    def test_verify_password_handles_empty_password(self):
        """空パスワードを適切に処理"""
        hashed = hash_password("test123")
        assert verify_password("", hashed) is False

    def test_verify_password_supports_legacy_sha256(self):
        """レガシーSHA256ハッシュもサポート"""
        import hashlib

        password = "test123"
        legacy_hash = hashlib.sha256(password.encode()).hexdigest()

        # SHA256ハッシュでも検証可能
        assert verify_password(password, legacy_hash) is True
        assert verify_password("wrong", legacy_hash) is False
