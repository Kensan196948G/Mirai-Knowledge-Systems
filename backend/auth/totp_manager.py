"""
TOTP (Time-based One-Time Password) Manager for MFA
Handles TOTP secret generation, QR code generation, verification, and backup codes
"""

import base64
import io
import secrets
import string
from typing import Dict, List

import pyotp
import qrcode
from bcrypt import checkpw, gensalt, hashpw


class TOTPManager:
    """Manages TOTP operations for Multi-Factor Authentication"""

    @staticmethod
    def generate_totp_secret() -> str:
        """
        Generate a random TOTP secret key

        Returns:
            str: Base32-encoded secret (32 characters)
        """
        return pyotp.random_base32()

    @staticmethod
    def generate_qr_code(
        username: str, secret: str, issuer: str = "Mirai Knowledge Systems"
    ) -> str:
        """
        Generate QR code for TOTP setup

        Args:
            username: User's email or username
            secret: TOTP secret key
            issuer: Application name (default: "Mirai Knowledge Systems")

        Returns:
            str: Base64-encoded PNG image of QR code
        """
        # Create TOTP instance
        totp = pyotp.TOTP(secret)

        # Generate provisioning URI
        provisioning_uri = totp.provisioning_uri(name=username, issuer_name=issuer)

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return qr_code_base64

    @staticmethod
    def verify_totp(secret: str, code: str, valid_window: int = 1) -> bool:
        """
        Verify TOTP code

        Args:
            secret: TOTP secret key
            code: 6-digit TOTP code from authenticator app
            valid_window: Number of time steps to check before/after current time (default: 1)
                         valid_window=1 allows codes from 30s before to 30s after

        Returns:
            bool: True if code is valid, False otherwise
        """
        if not code or not secret:
            return False

        # Remove any whitespace or dashes
        code = code.strip().replace("-", "").replace(" ", "")

        # Validate code format (6 digits)
        if not code.isdigit() or len(code) != 6:
            return False

        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=valid_window)

    @staticmethod
    def generate_backup_codes(count: int = 10) -> List[str]:
        """
        Generate backup codes for MFA recovery

        Args:
            count: Number of backup codes to generate (default: 10)

        Returns:
            List[str]: List of backup codes in format XXXX-XXXX-XXXX
        """
        backup_codes = []

        for _ in range(count):
            # Generate 12 random alphanumeric characters
            code = "".join(
                secrets.choice(string.ascii_uppercase + string.digits)
                for _ in range(12)
            )

            # Format as XXXX-XXXX-XXXX
            formatted_code = f"{code[0:4]}-{code[4:8]}-{code[8:12]}"
            backup_codes.append(formatted_code)

        return backup_codes

    @staticmethod
    def hash_backup_code(code: str) -> str:
        """
        Hash a backup code using bcrypt

        Args:
            code: Plain text backup code

        Returns:
            str: Bcrypt hashed code
        """
        # Remove dashes for consistent hashing
        clean_code = code.replace("-", "")

        # Hash with bcrypt
        hashed = hashpw(clean_code.encode("utf-8"), gensalt())
        return hashed.decode("utf-8")

    @staticmethod
    def verify_backup_code(hashed_code: str, input_code: str) -> bool:
        """
        Verify a backup code against its hash

        Args:
            hashed_code: Bcrypt hashed backup code
            input_code: User-provided backup code

        Returns:
            bool: True if code matches, False otherwise
        """
        if not hashed_code or not input_code:
            return False

        # Remove dashes from input for comparison
        clean_input = input_code.replace("-", "").replace(" ", "")

        try:
            return checkpw(clean_input.encode("utf-8"), hashed_code.encode("utf-8"))
        except Exception:
            return False

    @staticmethod
    def prepare_backup_codes_for_storage(codes: List[str]) -> List[Dict[str, any]]:
        """
        Prepare backup codes for database storage

        Args:
            codes: List of plain text backup codes

        Returns:
            List[Dict]: List of dictionaries with hashed codes and metadata
                       Format: [{"code_hash": "...", "used": False, "used_at": None}, ...]
        """
        return [
            {
                "code_hash": TOTPManager.hash_backup_code(code),
                "used": False,
                "used_at": None,
            }
            for code in codes
        ]

    @staticmethod
    def get_provisioning_uri(
        username: str, secret: str, issuer: str = "Mirai Knowledge Systems"
    ) -> str:
        """
        Get the provisioning URI for manual entry

        Args:
            username: User's email or username
            secret: TOTP secret key
            issuer: Application name

        Returns:
            str: Provisioning URI (otpauth://totp/...)
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=username, issuer_name=issuer)


# Singleton instance for convenience
totp_manager = TOTPManager()
