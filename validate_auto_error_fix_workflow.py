#!/usr/bin/env python3
"""
自動エラー検知・修復システム ワークフロー検証スクリプト

このスクリプトは、auto-error-fix-continuous.yml の設定が正しいことを検証します。
"""

import yaml
import sys
import os
from pathlib import Path

def validate_workflow():
    """ワークフロー設定を検証"""
    print("=" * 60)
    print("自動エラー検知・修復システム ワークフロー検証")
    print("=" * 60)
    print()

    # ワークフローファイルのパス
    workflow_path = Path(__file__).parent / '.github/workflows/auto-error-fix-continuous.yml'

    if not workflow_path.exists():
        print(f"❌ エラー: ワークフローファイルが見つかりません: {workflow_path}")
        return False

    print(f"✓ ワークフローファイル: {workflow_path}")
    print()

    # YAMLを読み込み
    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ エラー: ファイルが見つかりません: {workflow_path}")
        return False
    except yaml.YAMLError as e:
        print(f"❌ エラー: YAML構文エラー: {e}")
        return False
    except IOError as e:
        print(f"❌ エラー: ファイルの読み込みに失敗: {e}")
        return False

    print("✓ YAML構文: 正常")
    print()

    # 基本構造の検証
    checks = []

    # 1. ワークフロー名
    if 'name' in workflow:
        name = workflow['name']
        checks.append(('ワークフロー名', name, name == '🤖 自動エラー検知・修復システム（5分間隔・無限ループ）'))
    else:
        checks.append(('ワークフロー名', 'なし', False))

    # 2. トリガー設定
    # Note: In YAML, 'on' is a reserved word and can be loaded as boolean True
    # by some parsers. We check both 'on' (string key) and True (boolean key) for compatibility.
    on_config = workflow.get('on') or workflow.get(True)

    if on_config:

        # スケジュール
        if 'schedule' in on_config:
            cron = on_config['schedule'][0]['cron']
            checks.append(('スケジュール (cron)', cron, cron == '*/5 * * * *'))
        else:
            checks.append(('スケジュール', 'なし', False))

        # workflow_run
        if 'workflow_run' in on_config:
            workflows = on_config['workflow_run']['workflows']
            expected_workflows = ['E2E Tests', 'Backend CI', 'Backend CI (Improved)', 'Mirai Knowledge Systems CI/CD']
            all_present = all(w in workflows for w in expected_workflows)
            checks.append(('workflow_run トリガー', f"{len(workflows)}個のワークフロー", all_present))

            types = on_config['workflow_run']['types']
            checks.append(('workflow_run types', str(types), 'completed' in types))
        else:
            checks.append(('workflow_run トリガー', 'なし', False))

        # workflow_dispatch
        if 'workflow_dispatch' in on_config:
            checks.append(('手動トリガー (workflow_dispatch)', 'あり', True))
        else:
            checks.append(('手動トリガー', 'なし', False))
    else:
        checks.append(('トリガー設定', 'なし', False))

    # 3. 環境変数
    if 'env' in workflow:
        env = workflow['env']
        checks.append(('MAX_LOOPS', str(env.get('MAX_LOOPS')), str(env.get('MAX_LOOPS')) == '15'))
        checks.append(('PYTHON_VERSION', str(env.get('PYTHON_VERSION')), str(env.get('PYTHON_VERSION')) == '3.12'))
    else:
        checks.append(('環境変数', 'なし', False))

    # 4. ジョブ設定
    if 'jobs' in workflow:
        jobs = workflow['jobs']
        if 'auto-error-detection-and-fix' in jobs:
            job = jobs['auto-error-detection-and-fix']

            # 権限
            if 'permissions' in job:
                perms = job['permissions']
                required_perms = ['contents', 'pull-requests', 'checks', 'statuses', 'issues', 'actions']
                all_perms = all(p in perms for p in required_perms)
                checks.append(('権限設定', f"{len(perms)}個の権限", all_perms))
            else:
                checks.append(('権限設定', 'なし', False))

            # ステップ
            if 'steps' in job:
                steps = job['steps']
                step_names = [step.get('name', '') for step in steps]

                # 重要なステップの存在確認
                important_steps = [
                    'チェックアウト',
                    'トリガー元ワークフロー状態確認',
                    'Python環境セットアップ',
                    'エラー検知・修復ループ（15回）',
                    '結果レポート生成',
                    'GitHub Issueに結果を投稿'
                ]

                for step_name in important_steps:
                    present = any(step_name in name for name in step_names)
                    checks.append((f'ステップ: {step_name}', '存在' if present else '不在', present))

        else:
            checks.append(('ジョブ: auto-error-detection-and-fix', 'なし', False))
    else:
        checks.append(('ジョブ設定', 'なし', False))

    # 結果表示
    print("-" * 60)
    print("検証結果:")
    print("-" * 60)

    all_passed = True
    for check_name, value, passed in checks:
        status = "✓" if passed else "❌"
        print(f"{status} {check_name:40s} {value}")
        if not passed:
            all_passed = False

    print("-" * 60)
    print()

    if all_passed:
        print("✓ すべてのチェックに合格しました！")
        print()
        print("📋 概要:")
        print("  - 5分間隔でスケジュール実行")
        print("  - 4つのワークフローを監視")
        print("  - 手動トリガー対応")
        print("  - 適切な権限設定")
        print("  - 必要なステップすべて実装済み")
        return True
    else:
        print("❌ いくつかのチェックに失敗しました。")
        return False

if __name__ == '__main__':
    try:
        success = validate_workflow()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ 実行が中断されました")
        sys.exit(130)
    except yaml.YAMLError as e:
        print(f"❌ YAML処理エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except (IOError, OSError) as e:
        print(f"❌ ファイルI/Oエラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"❌ 予期しないエラー ({type(e).__name__}): {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
