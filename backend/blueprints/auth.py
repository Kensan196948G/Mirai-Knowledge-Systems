"""
認証Blueprint (Phase H-1 Blueprint移行)

/api/v1/auth/* エンドポイント 12本を管理。
app_v2.py から移行、共有ヘルパーは app_helpers.py から取得。
"""

import os
from datetime import timedelta, timezone, datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

from app_helpers import (
    IS_PRODUCTION,
    _token_blacklist,
    get_dal,
    get_user_permissions,
    load_users,
    log_access,
    save_users,
    validate_request,
    verify_password,
)
from auth.totp_manager import TOTPManager
from blueprints.utils.rate_limit import get_limiter
from schemas import LoginSchema

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")
auth_bp.strict_slashes = False


# ================================================================
# ログイン
# ================================================================


@auth_bp.route("/login", methods=["POST"])
@get_limiter().limit(
    "100 per minute" if os.environ.get("MKS_ENV") == "development" else "5 per minute"
)
@get_limiter().limit(
    "1000 per hour" if os.environ.get("MKS_ENV") == "development" else "20 per hour"
)
@validate_request(LoginSchema)
def login():
    """ログイン（レート制限: 開発環境では緩和、本番環境では5回/分、20回/時）

    MFA有効ユーザーの場合:
    - mfa_required: true と mfa_token を返す
    - /api/v1/auth/login/mfa でMFAコード検証後に正規トークン発行
    """
    data = request.validated_data
    username = data["username"]
    password = data["password"]

    if not username or not password:
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Username and password are required",
                },
            }),
            400,
        )

    users = load_users()
    user = next((u for u in users if u["username"] == username), None)

    if not user or not verify_password(password, user["password_hash"]):
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Invalid username or password",
                },
            }),
            401,
        )

    # MFA有効チェック
    if user.get("mfa_enabled", False):
        mfa_token = create_access_token(
            identity=str(user["id"]),
            additional_claims={"mfa_pending": True, "type": "mfa_temp"},
            expires_delta=timedelta(minutes=5),
        )
        return jsonify({
            "success": True,
            "data": {
                "mfa_required": True,
                "mfa_token": mfa_token,
                "message": "MFA verification required",
            },
        })

    # MFA無効ユーザー: 通常のトークン発行
    access_token = create_access_token(
        identity=str(user["id"]), additional_claims={"roles": user.get("roles", [])}
    )
    refresh_token = create_refresh_token(identity=str(user["id"]))

    log_access(user["id"], "login")

    user_data = {k: v for k, v in user.items() if k != "password_hash"}

    return jsonify({
        "success": True,
        "data": {
            "mfa_required": False,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "user": user_data,
        },
    })


# ================================================================
# MFA ログイン（TOTP / バックアップコード）
# ================================================================


@auth_bp.route("/login/mfa", methods=["POST"])
@get_limiter().limit(
    "100 per minute"
    if os.environ.get("MKS_ENV") == "development"
    else "5 per 15 minutes"
)
def login_mfa():
    """MFAコード検証してログイン完了（TOTPまたはバックアップコード対応）"""
    from datetime import datetime

    data = request.get_json()
    if not data:
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Request body is required",
                },
            }),
            400,
        )

    mfa_token = data.get("mfa_token")
    code = data.get("code") or data.get("totp_code")
    backup_code = data.get("backup_code")

    if not mfa_token:
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "MISSING_MFA_TOKEN",
                    "message": "MFA token is required",
                },
            }),
            400,
        )

    if not code and not backup_code:
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "MISSING_CODE",
                    "message": "Either TOTP code or backup code is required",
                },
            }),
            400,
        )

    # MFA一時トークンを検証
    try:
        from flask_jwt_extended import decode_token

        decoded = decode_token(mfa_token)

        if not decoded.get("mfa_pending") or decoded.get("type") != "mfa_temp":
            return (
                jsonify({
                    "success": False,
                    "error": {
                        "code": "INVALID_MFA_TOKEN",
                        "message": "Invalid MFA token",
                    },
                }),
                401,
            )

        user_id = decoded.get("sub")

    except Exception:
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "MFA_TOKEN_EXPIRED",
                    "message": "MFA token expired or invalid. Please login again.",
                },
            }),
            401,
        )

    # ユーザー取得（JSON mode と PostgreSQL mode の両方に対応）
    dal = get_dal()

    try:
        user_obj = dal.get_user_by_id(user_id)
        if user_obj:
            user = {
                "id": user_obj.id,
                "username": user_obj.username,
                "email": user_obj.email,
                "full_name": user_obj.full_name,
                "is_active": user_obj.is_active,
                "mfa_secret": user_obj.mfa_secret,
                "mfa_enabled": user_obj.mfa_enabled,
                "mfa_backup_codes": user_obj.mfa_backup_codes,
                "roles": [ur.role.name for ur in user_obj.roles] if user_obj.roles else [],
            }
            is_postgres = True
        else:
            user = None
            is_postgres = False
    except Exception:
        users = load_users()
        user = next((u for u in users if str(u["id"]) == str(user_id)), None)
        is_postgres = False

    if not user:
        return (
            jsonify({
                "success": False,
                "error": {"code": "USER_NOT_FOUND", "message": "User not found"},
            }),
            404,
        )

    mfa_secret = user.get("mfa_secret")
    if not mfa_secret or not user.get("mfa_enabled"):
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "MFA_NOT_CONFIGURED",
                    "message": "MFA is not configured for this user",
                },
            }),
            400,
        )

    totp_mgr = TOTPManager()
    verified = False
    used_backup = False

    if code:
        verified = totp_mgr.verify_totp(mfa_secret, code)

    if not verified and backup_code:
        backup_codes_data = user.get("mfa_backup_codes") or []

        for idx, backup_data in enumerate(backup_codes_data):
            if backup_data.get("used"):
                continue

            if totp_mgr.verify_backup_code(backup_data["code_hash"], backup_code):
                backup_codes_data[idx]["used"] = True
                backup_codes_data[idx]["used_at"] = datetime.now(timezone.utc).isoformat()

                if is_postgres:
                    user_obj.mfa_backup_codes = backup_codes_data
                    dal.commit()
                else:
                    users = load_users()
                    for u in users:
                        if str(u["id"]) == str(user_id):
                            u["mfa_backup_codes"] = backup_codes_data
                            break
                    save_users(users)

                verified = True
                used_backup = True
                break

    if not verified:
        log_access(int(user_id), "mfa_login_failed")
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "INVALID_MFA_CODE",
                    "message": "Invalid MFA code or backup code",
                },
            }),
            401,
        )

    access_token = create_access_token(
        identity=str(user["id"]), additional_claims={"roles": user.get("roles", [])}
    )
    refresh_token = create_refresh_token(identity=str(user["id"]))

    log_access(
        int(user_id), "mfa_login_success_backup" if used_backup else "mfa_login_success"
    )

    remaining_backups = sum(
        1 for b in (user.get("mfa_backup_codes") or []) if not b.get("used")
    )

    user_data = {
        k: v
        for k, v in user.items()
        if k not in ["password_hash", "mfa_secret", "mfa_backup_codes"]
    }

    return jsonify({
        "success": True,
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "used_backup_code": used_backup,
            "remaining_backup_codes": remaining_backups,
            "user": user_data,
        },
    })


# ================================================================
# トークンリフレッシュ
# ================================================================


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """トークンリフレッシュ"""
    current_user_id = get_jwt_identity()

    users = load_users()
    user = next((u for u in users if str(u["id"]) == str(current_user_id)), None)
    roles = user.get("roles", []) if user else []

    access_token = create_access_token(
        identity=current_user_id,
        additional_claims={"roles": roles},
    )

    return jsonify({
        "success": True,
        "data": {"access_token": access_token, "expires_in": 3600},
    })


# ================================================================
# ログアウト
# ================================================================


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """ログアウト - 現在のトークンを無効化"""
    current_user_id = get_jwt_identity()
    jti = get_jwt()["jti"]

    # トークンをブラックリストに追加（app_helpers._token_blacklist と共有）
    _token_blacklist.add(jti)

    log_access(int(current_user_id), "logout")

    return jsonify({"success": True, "message": "Logged out successfully"})


# ================================================================
# 現在ユーザー情報取得
# ================================================================


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """現在のユーザー情報取得"""
    current_user_id = int(get_jwt_identity())
    users = load_users()
    user = next((u for u in users if u["id"] == current_user_id), None)

    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    user_data = {k: v for k, v in user.items() if k != "password_hash"}
    user_data["permissions"] = get_user_permissions(user)

    return jsonify({"success": True, "data": user_data})


# ================================================================
# MFA セットアップ
# ================================================================


@auth_bp.route("/mfa/setup", methods=["POST"])
@jwt_required()
def setup_mfa():
    """MFAセットアップ - TOTPシークレット、QRコード、バックアップコード生成"""
    current_user_id = get_jwt_identity()
    dal = get_dal()
    user = dal.get_user_by_id(current_user_id)
    if not user:
        return (
            jsonify({
                "success": False,
                "error": {"code": "USER_NOT_FOUND", "message": "User not found"},
            }),
            404,
        )

    if user.mfa_enabled:
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "MFA_ALREADY_ENABLED",
                    "message": "MFA is already enabled. Disable MFA first to regenerate codes.",
                },
            }),
            400,
        )

    totp_mgr = TOTPManager()
    secret = totp_mgr.generate_totp_secret()
    qr_code_base64 = totp_mgr.generate_qr_code(user.email, secret)
    backup_codes = totp_mgr.generate_backup_codes(count=10)
    backup_codes_data = totp_mgr.prepare_backup_codes_for_storage(backup_codes)

    user.mfa_secret = secret
    user.mfa_backup_codes = backup_codes_data
    dal.commit()

    provisioning_uri = totp_mgr.get_provisioning_uri(user.email, secret)

    log_access(int(current_user_id), "mfa_setup_initiated")

    return jsonify({
        "success": True,
        "data": {
            "secret": secret,
            "qr_code_base64": qr_code_base64,
            "provisioning_uri": provisioning_uri,
            "backup_codes": backup_codes,
            "message": "MFA setup initiated. Please verify the code to enable MFA.",
        },
    })


# ================================================================
# MFA 有効化
# ================================================================


@auth_bp.route("/mfa/enable", methods=["POST"])
@jwt_required()
@get_limiter().limit("10 per minute")
def enable_mfa():
    """MFAコード検証と有効化"""
    current_user_id = get_jwt_identity()
    dal = get_dal()
    user = dal.get_user_by_id(current_user_id)
    if not user:
        return (
            jsonify({
                "success": False,
                "error": {"code": "USER_NOT_FOUND", "message": "User not found"},
            }),
            404,
        )

    data = request.get_json()
    if not data or "code" not in data:
        return (
            jsonify({
                "success": False,
                "error": {"code": "MISSING_CODE", "message": "MFA code is required"},
            }),
            400,
        )

    code = data["code"]
    if not user.mfa_secret:
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "MFA_NOT_SETUP",
                    "message": "MFA not set up. Please run /api/v1/auth/mfa/setup first.",
                },
            }),
            400,
        )

    totp_mgr = TOTPManager()
    if totp_mgr.verify_totp(user.mfa_secret, code):
        user.mfa_enabled = True
        dal.commit()
        log_access(int(current_user_id), "mfa_enabled")
        return jsonify({
            "success": True,
            "message": "MFA enabled successfully. Save your backup codes in a safe place.",
        })
    else:
        log_access(int(current_user_id), "mfa_enable_failed")
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "INVALID_CODE",
                    "message": "Invalid MFA code. Please try again.",
                },
            }),
            400,
        )


# ================================================================
# MFA 検証（/verify + /validate エイリアス）
# ================================================================


@auth_bp.route("/mfa/verify", methods=["POST"])
@auth_bp.route("/mfa/validate", methods=["POST"])  # backward compat
@get_limiter().limit("5 per 15 minutes")
def verify_mfa_login():
    """MFAログイン時のコード検証（TOTPまたはバックアップコード）"""
    from datetime import datetime

    data = request.get_json()
    if not data:
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Request body is required",
                },
            }),
            400,
        )

    mfa_token = data.get("mfa_token")
    code = data.get("code") or data.get("totp_code")
    backup_code = data.get("backup_code")

    if not mfa_token:
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "MISSING_MFA_TOKEN",
                    "message": "MFA token is required",
                },
            }),
            400,
        )

    if not code and not backup_code:
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "MISSING_CODE",
                    "message": "Either TOTP code or backup code is required",
                },
            }),
            400,
        )

    try:
        from flask_jwt_extended import decode_token

        decoded = decode_token(mfa_token)

        if not decoded.get("mfa_pending") or decoded.get("type") != "mfa_temp":
            return (
                jsonify({
                    "success": False,
                    "error": {
                        "code": "INVALID_MFA_TOKEN",
                        "message": "Invalid MFA token",
                    },
                }),
                401,
            )

        user_id = decoded.get("sub")

    except Exception:
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "MFA_TOKEN_EXPIRED",
                    "message": "MFA token expired or invalid. Please login again.",
                },
            }),
            401,
        )

    dal = get_dal()
    user = dal.get_user_by_id(user_id)

    if not user:
        return (
            jsonify({
                "success": False,
                "error": {"code": "USER_NOT_FOUND", "message": "User not found"},
            }),
            404,
        )

    if not user.mfa_secret or not user.mfa_enabled:
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "MFA_NOT_CONFIGURED",
                    "message": "MFA is not configured for this user",
                },
            }),
            400,
        )

    totp_mgr = TOTPManager()
    verified = False
    used_backup = False

    if code:
        verified = totp_mgr.verify_totp(user.mfa_secret, code)

    if not verified and backup_code:
        backup_codes_data = user.mfa_backup_codes or []

        for idx, backup_data in enumerate(backup_codes_data):
            if backup_data.get("used"):
                continue

            if totp_mgr.verify_backup_code(backup_data["code_hash"], backup_code):
                backup_codes_data[idx]["used"] = True
                backup_codes_data[idx]["used_at"] = datetime.now(timezone.utc).isoformat()
                user.mfa_backup_codes = backup_codes_data
                dal.commit()
                verified = True
                used_backup = True
                break

    if not verified:
        log_access(int(user_id), "mfa_login_failed")
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "INVALID_MFA_CODE",
                    "message": "Invalid MFA code or backup code",
                },
            }),
            401,
        )

    user_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "roles": [ur.role.name for ur in user.roles] if user.roles else [],
    }

    access_token = create_access_token(
        identity=str(user.id), additional_claims={"roles": user_dict.get("roles", [])}
    )
    refresh_token = create_refresh_token(identity=str(user.id))

    log_access(
        int(user_id), "mfa_login_success_backup" if used_backup else "mfa_login_success"
    )

    remaining_backups = sum(
        1 for b in (user.mfa_backup_codes or []) if not b.get("used")
    )

    return jsonify({
        "success": True,
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "used_backup_code": used_backup,
            "remaining_backup_codes": remaining_backups,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
            },
        },
    })


# ================================================================
# MFA 無効化
# ================================================================


@auth_bp.route("/mfa/disable", methods=["POST"])
@jwt_required()
@get_limiter().limit("10 per minute")
def disable_mfa():
    """MFA無効化（パスワードとTOTP/バックアップコードで二重確認）"""
    current_user_id = get_jwt_identity()
    dal = get_dal()
    user = dal.get_user_by_id(current_user_id)
    if not user:
        return (
            jsonify({
                "success": False,
                "error": {"code": "USER_NOT_FOUND", "message": "User not found"},
            }),
            404,
        )

    if not user.mfa_enabled:
        return (
            jsonify({
                "success": False,
                "error": {"code": "MFA_NOT_ENABLED", "message": "MFA is not enabled"},
            }),
            400,
        )

    data = request.get_json()
    if not data:
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Request body is required",
                },
            }),
            400,
        )

    password = data.get("password")
    code = data.get("code") or data.get("totp_code")
    backup_code = data.get("backup_code")

    if not password:
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "MISSING_PASSWORD",
                    "message": "Password is required",
                },
            }),
            400,
        )

    if not user.check_password(password):
        log_access(int(current_user_id), "mfa_disable_failed_password")
        return (
            jsonify({
                "success": False,
                "error": {"code": "INVALID_PASSWORD", "message": "Invalid password"},
            }),
            401,
        )

    if not code and not backup_code:
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "MISSING_CODE",
                    "message": "TOTP code or backup code is required",
                },
            }),
            400,
        )

    totp_mgr = TOTPManager()
    verified = False

    if code and user.mfa_secret:
        verified = totp_mgr.verify_totp(user.mfa_secret, code)

    if not verified and backup_code:
        backup_codes_data = user.mfa_backup_codes or []
        for backup_data in backup_codes_data:
            if backup_data.get("used"):
                continue
            if totp_mgr.verify_backup_code(backup_data["code_hash"], backup_code):
                verified = True
                break

    if not verified:
        log_access(int(current_user_id), "mfa_disable_failed_code")
        return (
            jsonify({
                "success": False,
                "error": {"code": "INVALID_CODE", "message": "Invalid MFA code"},
            }),
            401,
        )

    user.mfa_enabled = False
    user.mfa_secret = None
    user.mfa_backup_codes = None
    dal.commit()

    log_access(int(current_user_id), "mfa_disabled")

    return jsonify({"success": True, "message": "MFA disabled successfully"})


# ================================================================
# バックアップコード再生成
# ================================================================


@auth_bp.route("/mfa/backup-codes/regenerate", methods=["POST"])
@jwt_required()
@get_limiter().limit("3 per hour")
def regenerate_backup_codes():
    """バックアップコード再生成（TOTP検証必須）"""
    current_user_id = get_jwt_identity()
    dal = get_dal()
    user = dal.get_user_by_id(current_user_id)

    if not user:
        return (
            jsonify({
                "success": False,
                "error": {"code": "USER_NOT_FOUND", "message": "User not found"},
            }),
            404,
        )

    if not user.mfa_enabled:
        return (
            jsonify({
                "success": False,
                "error": {"code": "MFA_NOT_ENABLED", "message": "MFA is not enabled"},
            }),
            400,
        )

    data = request.get_json()
    code = data.get("code") if data else None

    if not code:
        return (
            jsonify({
                "success": False,
                "error": {"code": "MISSING_CODE", "message": "TOTP code is required"},
            }),
            400,
        )

    totp_mgr = TOTPManager()
    if not totp_mgr.verify_totp(user.mfa_secret, code):
        log_access(int(current_user_id), "backup_codes_regen_failed")
        return (
            jsonify({
                "success": False,
                "error": {"code": "INVALID_CODE", "message": "Invalid TOTP code"},
            }),
            401,
        )

    new_backup_codes = totp_mgr.generate_backup_codes(count=10)
    backup_codes_data = totp_mgr.prepare_backup_codes_for_storage(new_backup_codes)

    user.mfa_backup_codes = backup_codes_data
    dal.commit()

    log_access(int(current_user_id), "backup_codes_regenerated")

    return jsonify({
        "success": True,
        "data": {
            "backup_codes": new_backup_codes,
            "message": "New backup codes generated. Previous codes are now invalid.",
        },
    })


# ================================================================
# MFA ステータス
# ================================================================


@auth_bp.route("/mfa/status", methods=["GET"])
@jwt_required()
def mfa_status():
    """現在のMFA設定状態を取得"""
    current_user_id = get_jwt_identity()
    dal = get_dal()
    user = dal.get_user_by_id(current_user_id)

    if not user:
        return (
            jsonify({
                "success": False,
                "error": {"code": "USER_NOT_FOUND", "message": "User not found"},
            }),
            404,
        )

    remaining_backups = 0
    if user.mfa_backup_codes:
        remaining_backups = sum(1 for b in user.mfa_backup_codes if not b.get("used"))

    return jsonify({
        "success": True,
        "data": {
            "mfa_enabled": user.mfa_enabled,
            "mfa_configured": user.mfa_secret is not None,
            "remaining_backup_codes": remaining_backups,
            "email": user.email,
        },
    })


# ================================================================
# MFA リカバリー
# ================================================================


@auth_bp.route("/mfa/recovery", methods=["POST"])
@get_limiter().limit("3 per hour")
def mfa_recovery():
    """MFAリカバリー - メール経由でリカバリーコード送信"""
    data = request.get_json()
    if not data:
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Request body is required",
                },
            }),
            400,
        )

    email = data.get("email")
    username = data.get("username")

    if not email or not username:
        return (
            jsonify({
                "success": False,
                "error": {
                    "code": "MISSING_FIELDS",
                    "message": "Email and username are required",
                },
            }),
            400,
        )

    dal = get_dal()

    try:
        from models import User

        user = dal.session.query(User).filter_by(username=username, email=email).first()
    except Exception:
        users = load_users()
        user = next(
            (u for u in users if u.get("username") == username and u.get("email") == email),
            None,
        )

    if not user:
        return jsonify({
            "success": True,
            "message": "If the email and username match, a recovery link will be sent to your email.",
        })

    if not user.get("mfa_enabled") if isinstance(user, dict) else not user.mfa_enabled:
        return jsonify({
            "success": True,
            "message": "If the email and username match, a recovery link will be sent to your email.",
        })

    recovery_token = create_access_token(
        identity=str(user.get("id") if isinstance(user, dict) else user.id),
        additional_claims={"type": "mfa_recovery"},
        expires_delta=timedelta(hours=1),
    )

    user_id = user.get("id") if isinstance(user, dict) else user.id
    log_access(int(user_id), "mfa_recovery_requested")

    return jsonify({
        "success": True,
        "message": "If the email and username match, a recovery link will be sent to your email.",
        "dev_only_token": (
            recovery_token if os.getenv("MKS_ENV") == "development" else None
        ),
    })
