#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
Mirai Knowledge Systems - 環境変数バリデーター
============================================================

使用方法:
    python scripts/common/env-validator.py [環境]

    環境:
        development  - 開発環境の検証
        production   - 本番環境の検証
        all          - 両方の環境を検証

例:
    python scripts/common/env-validator.py development
    python scripts/common/env-validator.py production
    python scripts/common/env-validator.py all

============================================================
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# カラー出力
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

# 固定ポート番号（変更不可）
FIXED_PORTS = {
    'development': {'http': 5100, 'https': 5443},
    'production': {'http': 8100, 'https': 8443}
}

# 必須環境変数の定義
REQUIRED_VARS = {
    'development': [
        'MKS_ENV',
        'MKS_HTTP_PORT',
        'MKS_HTTPS_PORT',
        'MKS_SECRET_KEY',
        'MKS_JWT_SECRET_KEY',
    ],
    'production': [
        'MKS_ENV',
        'MKS_HTTP_PORT',
        'MKS_HTTPS_PORT',
        'MKS_SECRET_KEY',
        'MKS_JWT_SECRET_KEY',
        'DATABASE_URL',
    ]
}

# 推奨環境変数
RECOMMENDED_VARS = {
    'development': [
        'MKS_DEBUG',
        'MKS_LOAD_SAMPLE_DATA',
        'MKS_CREATE_DEMO_USERS',
        'CORS_ORIGINS',
    ],
    'production': [
        'MKS_FORCE_HTTPS',
        'MKS_HSTS_ENABLED',
        'CORS_ORIGINS',
        'GUNICORN_WORKERS',
        'MKS_LOG_LEVEL',
    ]
}

# セキュリティチェック
INSECURE_VALUES = [
    'CHANGE_THIS',
    'dev-secret',
    'password',
    '12345',
    'secret',
    'changeme',
]


def load_env_file(env_path: Path) -> Dict[str, str]:
    """環境変数ファイルを読み込む"""
    env_vars = {}

    if not env_path.exists():
        return env_vars

    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 空行とコメントをスキップ
            if not line or line.startswith('#'):
                continue

            # KEY=VALUE 形式をパース
            if '=' in line:
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip()
                # クォートを除去
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                env_vars[key] = value

    return env_vars


def validate_port(env_vars: Dict[str, str], env_type: str) -> List[str]:
    """ポート番号の検証"""
    errors = []
    expected = FIXED_PORTS[env_type]

    http_port = env_vars.get('MKS_HTTP_PORT', '')
    https_port = env_vars.get('MKS_HTTPS_PORT', '')

    if http_port and int(http_port) != expected['http']:
        errors.append(
            f"MKS_HTTP_PORT は {expected['http']} である必要があります（現在: {http_port}）"
        )

    if https_port and int(https_port) != expected['https']:
        errors.append(
            f"MKS_HTTPS_PORT は {expected['https']} である必要があります（現在: {https_port}）"
        )

    return errors


def validate_security(env_vars: Dict[str, str], env_type: str) -> List[str]:
    """セキュリティ設定の検証"""
    warnings = []

    # 本番環境のみセキュリティチェック
    if env_type == 'production':
        secret_vars = ['MKS_SECRET_KEY', 'MKS_JWT_SECRET_KEY']

        for var in secret_vars:
            value = env_vars.get(var, '')
            for insecure in INSECURE_VALUES:
                if insecure.lower() in value.lower():
                    warnings.append(
                        f"{var} に安全でない値が含まれています（'{insecure}'）"
                    )
                    break

            # 短すぎる秘密鍵
            if len(value) < 32:
                warnings.append(
                    f"{var} が短すぎます（32文字以上推奨、現在: {len(value)}文字）"
                )

        # HTTPS強制チェック
        if env_vars.get('MKS_FORCE_HTTPS', '').lower() != 'true':
            warnings.append("本番環境では MKS_FORCE_HTTPS=true を推奨")

        # HSTS有効チェック
        if env_vars.get('MKS_HSTS_ENABLED', '').lower() != 'true':
            warnings.append("本番環境では MKS_HSTS_ENABLED=true を推奨")

    return warnings


def validate_env(env_type: str, project_root: Path) -> Tuple[bool, List[str], List[str]]:
    """環境変数を検証"""
    errors = []
    warnings = []

    # 環境ファイルのパス
    env_path = project_root / 'envs' / env_type / f'.env.{env_type}'

    print(f"\n{Colors.CYAN}検証中: {env_path}{Colors.NC}")

    # ファイル存在チェック
    if not env_path.exists():
        errors.append(f"環境ファイルが見つかりません: {env_path}")
        return False, errors, warnings

    # 環境変数を読み込み
    env_vars = load_env_file(env_path)

    # 必須変数チェック
    for var in REQUIRED_VARS[env_type]:
        if var not in env_vars or not env_vars[var]:
            errors.append(f"必須環境変数が未設定: {var}")

    # 推奨変数チェック
    for var in RECOMMENDED_VARS[env_type]:
        if var not in env_vars:
            warnings.append(f"推奨環境変数が未設定: {var}")

    # ポート番号チェック
    port_errors = validate_port(env_vars, env_type)
    errors.extend(port_errors)

    # セキュリティチェック
    security_warnings = validate_security(env_vars, env_type)
    warnings.extend(security_warnings)

    # 環境モードチェック
    if env_vars.get('MKS_ENV') != env_type:
        errors.append(
            f"MKS_ENV が '{env_type}' ではありません（現在: {env_vars.get('MKS_ENV', '未設定')}）"
        )

    return len(errors) == 0, errors, warnings


def print_results(env_type: str, success: bool, errors: List[str], warnings: List[str]):
    """結果を表示"""
    env_label = "開発環境" if env_type == "development" else "本番環境"
    ports = FIXED_PORTS[env_type]

    print(f"\n{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"{Colors.BLUE}  {env_label} 検証結果{Colors.NC}")
    print(f"{Colors.BLUE}  ポート: HTTP={ports['http']}, HTTPS={ports['https']}{Colors.NC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")

    if errors:
        print(f"\n{Colors.RED}❌ エラー ({len(errors)}件):{Colors.NC}")
        for error in errors:
            print(f"   {Colors.RED}• {error}{Colors.NC}")

    if warnings:
        print(f"\n{Colors.YELLOW}⚠️ 警告 ({len(warnings)}件):{Colors.NC}")
        for warning in warnings:
            print(f"   {Colors.YELLOW}• {warning}{Colors.NC}")

    if success:
        print(f"\n{Colors.GREEN}✅ 検証成功: すべての必須チェックに合格しました{Colors.NC}")
    else:
        print(f"\n{Colors.RED}❌ 検証失敗: エラーを修正してください{Colors.NC}")

    return success


def main():
    # 引数解析
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    env_type = sys.argv[1].lower()

    if env_type not in ['development', 'production', 'all']:
        print(f"{Colors.RED}エラー: 無効な環境タイプ: {env_type}{Colors.NC}")
        print("有効なオプション: development, production, all")
        sys.exit(1)

    # プロジェクトルートを取得
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent

    print(f"{Colors.CYAN}============================================================{Colors.NC}")
    print(f"{Colors.CYAN}  Mirai Knowledge Systems - 環境変数バリデーター{Colors.NC}")
    print(f"{Colors.CYAN}============================================================{Colors.NC}")
    print(f"\nプロジェクトルート: {project_root}")

    all_success = True

    if env_type in ['development', 'all']:
        success, errors, warnings = validate_env('development', project_root)
        print_results('development', success, errors, warnings)
        all_success = all_success and success

    if env_type in ['production', 'all']:
        success, errors, warnings = validate_env('production', project_root)
        print_results('production', success, errors, warnings)
        all_success = all_success and success

    print(f"\n{Colors.CYAN}{'='*60}{Colors.NC}")

    if all_success:
        print(f"{Colors.GREEN}✅ すべての検証が完了しました{Colors.NC}")
        sys.exit(0)
    else:
        print(f"{Colors.RED}❌ 一部の検証に失敗しました{Colors.NC}")
        sys.exit(1)


if __name__ == '__main__':
    main()
