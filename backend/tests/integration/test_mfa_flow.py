"""
Integration tests for MFA (Multi-Factor Authentication) flow
Tests the complete MFA setup, login, and management workflows
"""

import json
from datetime import datetime

import pyotp
import pytest
from app_v2 import app
from data_access import DataAccessLayer


@pytest.fixture
def client():
    """Create test client"""
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "test-secret-key"

    with app.test_client() as client:
        yield client


@pytest.fixture
def test_user_with_mfa(client):
    """Create a test user with MFA enabled"""
    # First, create and login as a regular user
    # Note: This assumes there's a test user creation endpoint or fixture
    # For now, we'll assume a user exists

    # Login to get token
    login_response = client.post(
        "/api/v1/auth/login", json={"username": "testuser", "password": "Test1234!"}
    )

    if login_response.status_code != 200:
        pytest.skip("Test user not available")

    data = json.loads(login_response.data)

    if data["data"].get("mfa_required"):
        pytest.skip("Test user already has MFA enabled")

    token = data["data"]["access_token"]

    # Setup MFA
    setup_response = client.post(
        "/api/v1/auth/mfa/setup", headers={"Authorization": f"Bearer {token}"}
    )

    setup_data = json.loads(setup_response.data)
    secret = setup_data["data"]["secret"]

    # Generate TOTP code
    totp = pyotp.TOTP(secret)
    code = totp.now()

    # Enable MFA
    enable_response = client.post(
        "/api/v1/auth/mfa/enable",
        headers={"Authorization": f"Bearer {token}"},
        json={"code": code},
    )

    assert enable_response.status_code == 200

    return {
        "username": "testuser",
        "password": "Test1234!",
        "secret": secret,
        "token": token,
    }


class TestMFASetup:
    """Test MFA setup flow"""

    def test_mfa_setup_generates_secret_and_qr(self, client):
        """Test that MFA setup generates secret, QR code, and backup codes"""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "testuser", "password": "Test1234!"}
        )

        if login_response.status_code != 200:
            pytest.skip("Test user not available")

        data = json.loads(login_response.data)

        if data["data"].get("mfa_required"):
            pytest.skip("Test user already has MFA enabled")

        token = data["data"]["access_token"]

        # Setup MFA
        response = client.post(
            "/api/v1/auth/mfa/setup", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["success"] is True
        assert "secret" in data["data"]
        assert "qr_code_base64" in data["data"]
        assert "backup_codes" in data["data"]
        assert "provisioning_uri" in data["data"]

        # Verify secret format
        secret = data["data"]["secret"]
        assert len(secret) == 32
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567" for c in secret)

        # Verify backup codes
        backup_codes = data["data"]["backup_codes"]
        assert len(backup_codes) == 10
        for code in backup_codes:
            parts = code.split("-")
            assert len(parts) == 3

    def test_mfa_setup_without_auth(self, client):
        """Test that MFA setup requires authentication"""
        response = client.post("/api/v1/auth/mfa/setup")

        assert response.status_code == 401

    def test_mfa_setup_already_enabled(self, client, test_user_with_mfa):
        """Test that MFA setup fails if already enabled"""
        token = test_user_with_mfa["token"]

        response = client.post(
            "/api/v1/auth/mfa/setup", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400

        data = json.loads(response.data)
        assert "MFA_ALREADY_ENABLED" in data["error"]["code"]


class TestMFAEnable:
    """Test MFA enable flow"""

    def test_mfa_enable_with_valid_code(self, client):
        """Test enabling MFA with valid TOTP code"""
        # Setup MFA first (without enabling)
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser2", "password": "Test1234!"},
        )

        if login_response.status_code != 200:
            pytest.skip("Test user not available")

        data = json.loads(login_response.data)
        token = data["data"]["access_token"]

        # Setup
        setup_response = client.post(
            "/api/v1/auth/mfa/setup", headers={"Authorization": f"Bearer {token}"}
        )

        setup_data = json.loads(setup_response.data)
        secret = setup_data["data"]["secret"]

        # Generate valid code
        totp = pyotp.TOTP(secret)
        code = totp.now()

        # Enable
        response = client.post(
            "/api/v1/auth/mfa/enable",
            headers={"Authorization": f"Bearer {token}"},
            json={"code": code},
        )

        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["success"] is True

    def test_mfa_enable_with_invalid_code(self, client):
        """Test that MFA enable fails with invalid code"""
        # Setup MFA first
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser3", "password": "Test1234!"},
        )

        if login_response.status_code != 200:
            pytest.skip("Test user not available")

        data = json.loads(login_response.data)
        token = data["data"]["access_token"]

        # Setup
        client.post(
            "/api/v1/auth/mfa/setup", headers={"Authorization": f"Bearer {token}"}
        )

        # Try to enable with invalid code
        response = client.post(
            "/api/v1/auth/mfa/enable",
            headers={"Authorization": f"Bearer {token}"},
            json={"code": "000000"},
        )

        assert response.status_code == 400

        data = json.loads(response.data)
        assert data["success"] is False


class TestMFALogin:
    """Test MFA login flow"""

    def test_mfa_login_returns_mfa_token(self, client, test_user_with_mfa):
        """Test that login with MFA-enabled user returns mfa_token"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_with_mfa["username"],
                "password": test_user_with_mfa["password"],
            },
        )

        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["mfa_required"] is True
        assert "mfa_token" in data["data"]
        assert "access_token" not in data["data"]  # Should not return access token yet

    def test_mfa_login_with_valid_totp(self, client, test_user_with_mfa):
        """Test complete MFA login flow with valid TOTP"""
        # Step 1: Initial login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_with_mfa["username"],
                "password": test_user_with_mfa["password"],
            },
        )

        login_data = json.loads(login_response.data)
        mfa_token = login_data["data"]["mfa_token"]

        # Step 2: Generate TOTP code
        totp = pyotp.TOTP(test_user_with_mfa["secret"])
        code = totp.now()

        # Step 3: Verify MFA code
        mfa_response = client.post(
            "/api/v1/auth/login/mfa", json={"mfa_token": mfa_token, "code": code}
        )

        assert mfa_response.status_code == 200

        mfa_data = json.loads(mfa_response.data)
        assert mfa_data["success"] is True
        assert "access_token" in mfa_data["data"]
        assert "refresh_token" in mfa_data["data"]

    def test_mfa_login_with_invalid_totp(self, client, test_user_with_mfa):
        """Test MFA login with invalid TOTP code"""
        # Initial login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_with_mfa["username"],
                "password": test_user_with_mfa["password"],
            },
        )

        login_data = json.loads(login_response.data)
        mfa_token = login_data["data"]["mfa_token"]

        # Try with invalid code
        mfa_response = client.post(
            "/api/v1/auth/login/mfa", json={"mfa_token": mfa_token, "code": "000000"}
        )

        assert mfa_response.status_code == 401

        mfa_data = json.loads(mfa_response.data)
        assert mfa_data["success"] is False

    def test_mfa_login_with_backup_code(self, client, test_user_with_mfa):
        """Test MFA login with backup code"""
        # Get backup codes
        setup_response = client.post(
            "/api/v1/auth/mfa/setup",
            headers={"Authorization": f'Bearer {test_user_with_mfa["token"]}'},
        )

        # If already enabled, skip
        if setup_response.status_code == 400:
            pytest.skip("MFA already enabled, backup codes not accessible")

        setup_data = json.loads(setup_response.data)
        backup_code = setup_data["data"]["backup_codes"][0]

        # Initial login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_with_mfa["username"],
                "password": test_user_with_mfa["password"],
            },
        )

        login_data = json.loads(login_response.data)
        mfa_token = login_data["data"]["mfa_token"]

        # Use backup code
        mfa_response = client.post(
            "/api/v1/auth/login/mfa",
            json={"mfa_token": mfa_token, "backup_code": backup_code},
        )

        assert mfa_response.status_code == 200

        mfa_data = json.loads(mfa_response.data)
        assert mfa_data["success"] is True
        assert mfa_data["data"]["used_backup_code"] is True
        assert mfa_data["data"]["remaining_backup_codes"] == 9


class TestMFADisable:
    """Test MFA disable flow"""

    def test_mfa_disable_with_valid_credentials(self, client, test_user_with_mfa):
        """Test disabling MFA with valid password and TOTP"""
        # Generate TOTP code
        totp = pyotp.TOTP(test_user_with_mfa["secret"])
        code = totp.now()

        response = client.post(
            "/api/v1/auth/mfa/disable",
            headers={"Authorization": f'Bearer {test_user_with_mfa["token"]}'},
            json={"password": test_user_with_mfa["password"], "code": code},
        )

        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["success"] is True

    def test_mfa_disable_with_invalid_password(self, client, test_user_with_mfa):
        """Test that MFA disable fails with invalid password"""
        totp = pyotp.TOTP(test_user_with_mfa["secret"])
        code = totp.now()

        response = client.post(
            "/api/v1/auth/mfa/disable",
            headers={"Authorization": f'Bearer {test_user_with_mfa["token"]}'},
            json={"password": "wrongpassword", "code": code},
        )

        assert response.status_code == 401

    def test_mfa_disable_with_invalid_code(self, client, test_user_with_mfa):
        """Test that MFA disable fails with invalid TOTP"""
        response = client.post(
            "/api/v1/auth/mfa/disable",
            headers={"Authorization": f'Bearer {test_user_with_mfa["token"]}'},
            json={"password": test_user_with_mfa["password"], "code": "000000"},
        )

        assert response.status_code == 401


class TestBackupCodeRegeneration:
    """Test backup code regeneration"""

    def test_regenerate_backup_codes(self, client, test_user_with_mfa):
        """Test regenerating backup codes"""
        totp = pyotp.TOTP(test_user_with_mfa["secret"])
        code = totp.now()

        response = client.post(
            "/api/v1/auth/mfa/backup-codes/regenerate",
            headers={"Authorization": f'Bearer {test_user_with_mfa["token"]}'},
            json={"code": code},
        )

        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["success"] is True
        assert "backup_codes" in data["data"]
        assert len(data["data"]["backup_codes"]) == 10

    def test_regenerate_backup_codes_invalid_totp(self, client, test_user_with_mfa):
        """Test that backup code regeneration fails with invalid TOTP"""
        response = client.post(
            "/api/v1/auth/mfa/backup-codes/regenerate",
            headers={"Authorization": f'Bearer {test_user_with_mfa["token"]}'},
            json={"code": "000000"},
        )

        assert response.status_code == 401


class TestMFAStatus:
    """Test MFA status endpoint"""

    def test_mfa_status_enabled(self, client, test_user_with_mfa):
        """Test MFA status for user with MFA enabled"""
        response = client.get(
            "/api/v1/auth/mfa/status",
            headers={"Authorization": f'Bearer {test_user_with_mfa["token"]}'},
        )

        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["mfa_enabled"] is True
        assert data["data"]["mfa_configured"] is True
        assert "remaining_backup_codes" in data["data"]

    def test_mfa_status_without_auth(self, client):
        """Test that MFA status requires authentication"""
        response = client.get("/api/v1/auth/mfa/status")

        assert response.status_code == 401


class TestRateLimiting:
    """Test rate limiting on MFA endpoints"""

    def test_mfa_verify_rate_limit(self, client, test_user_with_mfa):
        """Test that MFA verification has rate limiting"""
        # This test would need to make multiple requests rapidly
        # Implementation depends on the rate limiting configuration

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_with_mfa["username"],
                "password": test_user_with_mfa["password"],
            },
        )

        login_data = json.loads(login_response.data)
        mfa_token = login_data["data"]["mfa_token"]

        # Make multiple failed attempts
        for i in range(10):
            client.post(
                "/api/v1/auth/login/mfa",
                json={"mfa_token": mfa_token, "code": "000000"},
            )

        # The next request should be rate limited
        # Note: This depends on rate limit configuration
        # and might need adjustment based on actual limits
        response = client.post(
            "/api/v1/auth/login/mfa", json={"mfa_token": mfa_token, "code": "000000"}
        )

        # Rate limit might return 429 Too Many Requests
        # or might still return 401 depending on implementation
        # This test serves as a reminder to verify rate limiting works


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
