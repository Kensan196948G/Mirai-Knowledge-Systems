#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mirai Knowledge Systems - Node.js モジュールOS別セットアップスクリプト

このスクリプトは、Windows/Linux間で共有フォルダを使用する際の
Node.jsモジュール互換性問題を解決します。

使用方法:
    python scripts/common/setup-node-modules.py [--install] [--clean]

オプション:
    --install    OSに応じたnode_modulesをセットアップ
    --clean      全てのOS別node_modulesディレクトリを削除
    --help       ヘルプ表示

仕組み:
    1. OSを判定（Windows/Linux）
    2. node_modules.{os} ディレクトリを作成
    3. シンボリックリンク node_modules -> node_modules.{os} を作成
    4. npm install を実行

ポート番号:
    開発環境: HTTP 5100, HTTPS 5443
    本番環境: HTTP 8100, HTTPS 8443
"""

import argparse
import platform
import shutil
import subprocess
from pathlib import Path


def get_os_name():
    """現在のOSを判定して返す"""
    system = platform.system().lower()
    if system == 'windows':
        return 'windows'
    elif system == 'linux':
        return 'linux'
    elif system == 'darwin':
        return 'macos'
    else:
        return system


def get_project_root():
    """プロジェクトルートディレクトリを取得"""
    script_dir = Path(__file__).parent.absolute()
    return script_dir.parent.parent


def setup_node_modules(target_dir: Path, os_name: str):
    """
    OS別のnode_modulesをセットアップ

    Args:
        target_dir: package.jsonがあるディレクトリ
        os_name: 'windows' or 'linux'
    """
    if not (target_dir / 'package.json').exists():
        print(f"[SKIP] package.json が見つかりません: {target_dir}")
        return False

    node_modules = target_dir / 'node_modules'
    node_modules_os = target_dir / f'node_modules.{os_name}'

    print(f"\n{'='*60}")
    print(f"セットアップ: {target_dir.name}")
    print(f"OS: {os_name}")
    print(f"{'='*60}")

    # 既存のnode_modulesがシンボリックリンクでない場合
    if node_modules.exists() and not node_modules.is_symlink():
        # 現在のOSのディレクトリとしてリネーム
        current_os = get_os_name()
        backup_dir = target_dir / f'node_modules.{current_os}'
        if not backup_dir.exists():
            print(f"[INFO] 既存のnode_modulesを移動: node_modules -> node_modules.{current_os}")
            node_modules.rename(backup_dir)
        else:
            print(f"[WARN] node_modules.{current_os} が既に存在。node_modulesを削除します。")
            shutil.rmtree(node_modules)

    # シンボリックリンクを削除
    if node_modules.is_symlink():
        node_modules.unlink()
        print("[INFO] 既存のシンボリックリンクを削除")

    # OS別ディレクトリを作成
    if not node_modules_os.exists():
        print(f"[INFO] ディレクトリ作成: node_modules.{os_name}")
        node_modules_os.mkdir()

    # シンボリックリンク作成
    try:
        if os_name == 'windows':
            # Windows: ジャンクション（管理者権限不要）
            subprocess.run(
                ['cmd', '/c', 'mklink', '/J', str(node_modules), str(node_modules_os)],
                check=True,
                capture_output=True
            )
        else:
            # Linux/macOS: シンボリックリンク
            node_modules.symlink_to(node_modules_os.name)

        print(f"[OK] シンボリックリンク作成: node_modules -> node_modules.{os_name}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] シンボリックリンク作成失敗: {e}")
        # フォールバック: 直接ディレクトリ名を変更
        if node_modules_os.exists():
            node_modules_os.rename(node_modules)
            print(f"[INFO] フォールバック: node_modules.{os_name} を node_modules にリネーム")
        return False
    except OSError as e:
        print(f"[ERROR] シンボリックリンク作成失敗: {e}")
        return False

    # npm install 実行
    print("[INFO] npm install を実行中...")
    try:
        result = subprocess.run(
            ['npm', 'install'],
            cwd=target_dir,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("[OK] npm install 完了")
        else:
            print("[WARN] npm install に警告があります:")
            if result.stderr:
                print(result.stderr[:500])
    except FileNotFoundError:
        print("[WARN] npm が見つかりません。手動で npm install を実行してください。")

    return True


def clean_node_modules(target_dir: Path):
    """全てのOS別node_modulesディレクトリを削除"""
    node_modules = target_dir / 'node_modules'

    # シンボリックリンクを削除
    if node_modules.is_symlink():
        node_modules.unlink()
        print(f"[INFO] シンボリックリンク削除: {node_modules}")
    elif node_modules.exists():
        shutil.rmtree(node_modules)
        print(f"[INFO] ディレクトリ削除: {node_modules}")

    # OS別ディレクトリを削除
    for os_suffix in ['windows', 'linux', 'macos']:
        os_dir = target_dir / f'node_modules.{os_suffix}'
        if os_dir.exists():
            shutil.rmtree(os_dir)
            print(f"[INFO] ディレクトリ削除: {os_dir}")


def main():
    parser = argparse.ArgumentParser(
        description='Node.js モジュールをOS別にセットアップ'
    )
    parser.add_argument(
        '--install',
        action='store_true',
        help='OSに応じたnode_modulesをセットアップ'
    )
    parser.add_argument(
        '--clean',
        action='store_true',
        help='全てのOS別node_modulesディレクトリを削除'
    )

    args = parser.parse_args()

    if not args.install and not args.clean:
        parser.print_help()
        return

    project_root = get_project_root()
    os_name = get_os_name()

    print(f"プロジェクトルート: {project_root}")
    print(f"検出されたOS: {os_name}")

    # package.jsonを持つディレクトリを検索
    target_dirs = [
        project_root / 'backend',
        project_root / 'webui',
        project_root,
    ]

    for target_dir in target_dirs:
        if (target_dir / 'package.json').exists():
            if args.clean:
                clean_node_modules(target_dir)
            if args.install:
                setup_node_modules(target_dir, os_name)

    print(f"\n{'='*60}")
    print("完了")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
