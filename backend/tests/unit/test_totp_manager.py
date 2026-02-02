"""
Unit tests for TOTP Manager (MFA functionality)
"""

import base64
from io import BytesIO

import pyotp
import pytest
from auth.totp_manager import TOTPManager
from PIL import Image


class TestTOTPManager:
    """Test suite for TOTP Manager"""

    def test_generate_totp_secret(self):
        """Test TOTP secret generation"""
        manager = TOTPManager()
        secret = manager.generate_totp_secret()

        # Check format
        assert secret is not None
        assert len(secret) == 32
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567" for c in secret)

        # Check uniqueness
        secret2 = manager.generate_totp_secret()
        assert secret != secret2

    def test_generate_qr_code(self):
        """Test QR code generation"""
        manager = TOTPManager()
        secret = manager.generate_totp_secret()

        qr_code_base64 = manager.generate_qr_code("test@example.com", secret)

        # Check format
        assert qr_code_base64 is not None
        assert len(qr_code_base64) > 0

        # Verify it's valid base64
        try:
            qr_data = base64.b64decode(qr_code_base64)
            assert len(qr_data) > 0
        except Exception as e:
            pytest.fail(f"Invalid base64: {e}")

        # Verify it's a valid PNG image
        try:
            img = Image.open(BytesIO(qr_data))
            assert img.format == "PNG"
        except Exception as e:
            pytest.fail(f"Invalid PNG image: {e}")

    def test_verify_totp_valid_code(self):
        """Test TOTP verification with valid code"""
        manager = TOTPManager()
        secret = "JBSWY3DPEHPK3PXP"  # Example secret

        # Generate current TOTP code
        totp = pyotp.TOTP(secret)
        current_code = totp.now()

        # Verify
        assert manager.verify_totp(secret, current_code) is True

    def test_verify_totp_invalid_code(self):
        """Test TOTP verification with invalid code"""
        manager = TOTPManager()
        secret = "JBSWY3DPEHPK3PXP"

        # Test invalid codes
        assert manager.verify_totp(secret, "000000") is False
        assert manager.verify_totp(secret, "123456") is False
        assert manager.verify_totp(secret, "999999") is False

    def test_verify_totp_invalid_format(self):
        """Test TOTP verification with invalid format"""
        manager = TOTPManager()
        secret = "JBSWY3DPEHPK3PXP"

        # Test invalid formats
        assert manager.verify_totp(secret, "") is False
        assert manager.verify_totp(secret, "12345") is False  # Too short
        assert manager.verify_totp(secret, "1234567") is False  # Too long
        assert manager.verify_totp(secret, "abcdef") is False  # Not digits
        assert (
            manager.verify_totp(secret, "12-34-56") is False
        )  # Contains dashes (after stripping)

    def test_verify_totp_with_whitespace(self):
        """Test TOTP verification handles whitespace"""
        manager = TOTPManager()
        secret = "JBSWY3DPEHPK3PXP"

        totp = pyotp.TOTP(secret)
        current_code = totp.now()

        # Test with whitespace
        assert manager.verify_totp(secret, f" {current_code} ") is True
        assert (
            manager.verify_totp(secret, f"{current_code[:3]} {current_code[3:]}")
            is True
        )

    def test_generate_backup_codes(self):
        """Test backup code generation"""
        manager = TOTPManager()

        # Generate 10 codes
        codes = manager.generate_backup_codes(count=10)

        assert len(codes) == 10
        assert len(set(codes)) == 10  # All unique

        # Check format (XXXX-XXXX-XXXX)
        for code in codes:
            parts = code.split("-")
            assert len(parts) == 3
            assert all(len(part) == 4 for part in parts)
            assert all(
                c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                for part in parts
                for c in part
            )

    def test_generate_backup_codes_custom_count(self):
        """Test backup code generation with custom count"""
        manager = TOTPManager()

        codes = manager.generate_backup_codes(count=5)
        assert len(codes) == 5

        codes = manager.generate_backup_codes(count=20)
        assert len(codes) == 20

    def test_hash_backup_code(self):
        """Test backup code hashing"""
        manager = TOTPManager()

        code = "ABCD-1234-EFGH"
        hashed = manager.hash_backup_code(code)

        # Check format (bcrypt hash starts with $2b$)
        assert hashed is not None
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
        assert len(hashed) == 60  # Bcrypt hash length

        # Check uniqueness (same code should produce different hashes due to salt)
        hashed2 = manager.hash_backup_code(code)
        assert hashed != hashed2

    def test_verify_backup_code_valid(self):
        """Test backup code verification with valid code"""
        manager = TOTPManager()

        code = "ABCD-1234-EFGH"
        hashed = manager.hash_backup_code(code)

        # Verify with exact code
        assert manager.verify_backup_code(hashed, code) is True

        # Verify with code without dashes
        assert manager.verify_backup_code(hashed, "ABCD1234EFGH") is True

        # Verify with lowercase (should still work after normalization)
        # Note: The hash is case-sensitive, so this might fail
        # Depending on implementation, you might want to normalize case

    def test_verify_backup_code_invalid(self):
        """Test backup code verification with invalid code"""
        manager = TOTPManager()

        code = "ABCD-1234-EFGH"
        hashed = manager.hash_backup_code(code)

        # Test invalid codes
        assert manager.verify_backup_code(hashed, "WXYZ-9876-STUV") is False
        assert manager.verify_backup_code(hashed, "0000-0000-0000") is False
        assert manager.verify_backup_code(hashed, "") is False
        assert manager.verify_backup_code(hashed, "invalid") is False

    def test_verify_backup_code_with_spaces(self):
        """Test backup code verification handles spaces"""
        manager = TOTPManager()

        code = "ABCD-1234-EFGH"
        hashed = manager.hash_backup_code(code)

        # Test with spaces
        assert manager.verify_backup_code(hashed, " ABCD-1234-EFGH ") is True
        assert manager.verify_backup_code(hashed, "ABCD 1234 EFGH") is True

    def test_prepare_backup_codes_for_storage(self):
        """Test backup code preparation for database storage"""
        manager = TOTPManager()

        codes = ["AAAA-1111-BBBB", "CCCC-2222-DDDD", "EEEE-3333-FFFF"]
        prepared = manager.prepare_backup_codes_for_storage(codes)

        assert len(prepared) == 3

        for item in prepared:
            assert "code_hash" in item
            assert "used" in item
            assert "used_at" in item

            assert item["used"] is False
            assert item["used_at"] is None
            assert len(item["code_hash"]) == 60  # Bcrypt hash length

    def test_get_provisioning_uri(self):
        """Test provisioning URI generation"""
        manager = TOTPManager()

        secret = "JBSWY3DPEHPK3PXP"
        uri = manager.get_provisioning_uri("test@example.com", secret)

        assert uri.startswith("otpauth://totp/")
        assert "Mirai%20Knowledge%20Systems" in uri or "Mirai+Knowledge+Systems" in uri
        assert "test@example.com" in uri or "test%40example.com" in uri
        assert secret in uri

    def test_get_provisioning_uri_custom_issuer(self):
        """Test provisioning URI with custom issuer"""
        manager = TOTPManager()

        secret = "JBSWY3DPEHPK3PXP"
        uri = manager.get_provisioning_uri(
            "test@example.com", secret, issuer="Custom Issuer"
        )

        assert uri.startswith("otpauth://totp/")
        assert "Custom" in uri

    def test_totp_time_window(self):
        """Test TOTP verification with time window"""
        manager = TOTPManager()
        secret = "JBSWY3DPEHPK3PXP"

        totp = pyotp.TOTP(secret)

        # Get current code
        current_code = totp.now()
        assert manager.verify_totp(secret, current_code, valid_window=1) is True

        # The valid_window parameter allows for ±30 seconds (1 step before and after)
        # We can't easily test previous/next codes without mocking time,
        # but we can verify the parameter is accepted
        assert manager.verify_totp(secret, current_code, valid_window=2) is True

    def test_backup_code_uniqueness(self):
        """Test that backup codes are unique within a generation"""
        manager = TOTPManager()

        codes = manager.generate_backup_codes(count=100)

        assert len(codes) == 100
        assert len(set(codes)) == 100  # All unique

    def test_empty_secret_verification(self):
        """Test verification with empty secret"""
        manager = TOTPManager()

        assert manager.verify_totp("", "123456") is False
        assert manager.verify_totp(None, "123456") is False

    def test_empty_code_verification(self):
        """Test verification with empty code"""
        manager = TOTPManager()

        secret = "JBSWY3DPEHPK3PXP"

        assert manager.verify_totp(secret, "") is False
        assert manager.verify_totp(secret, None) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
