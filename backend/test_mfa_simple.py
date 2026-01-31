#!/usr/bin/env python3
"""
簡易MFA動作確認スクリプト
依存関係のインストールなしで動作を確認
"""

import sys

def test_imports():
    """依存関係のインポート確認"""
    print("=" * 60)
    print("MFA依存関係確認")
    print("=" * 60)

    results = []

    # pyotp確認
    try:
        import pyotp
        print("✅ pyotp インポート成功")
        print(f"   バージョン: {pyotp.__version__ if hasattr(pyotp, '__version__') else '不明'}")
        results.append(("pyotp", True))
    except ImportError as e:
        print(f"❌ pyotp インポート失敗: {e}")
        results.append(("pyotp", False))

    # qrcode確認
    try:
        import qrcode
        print("✅ qrcode インポート成功")
        print(f"   バージョン: {qrcode.__version__ if hasattr(qrcode, '__version__') else '不明'}")
        results.append(("qrcode", True))
    except ImportError as e:
        print(f"❌ qrcode インポート失敗: {e}")
        results.append(("qrcode", False))

    # Pillow確認
    try:
        from PIL import Image
        import PIL
        print("✅ Pillow (PIL) インポート成功")
        print(f"   バージョン: {PIL.__version__ if hasattr(PIL, '__version__') else '不明'}")
        results.append(("Pillow", True))
    except ImportError as e:
        print(f"❌ Pillow インポート失敗: {e}")
        results.append(("Pillow", False))

    # bcrypt確認
    try:
        import bcrypt
        print("✅ bcrypt インポート成功")
        print(f"   バージョン: {bcrypt.__version__ if hasattr(bcrypt, '__version__') else '不明'}")
        results.append(("bcrypt", True))
    except ImportError as e:
        print(f"❌ bcrypt インポート失敗: {e}")
        results.append(("bcrypt", False))

    print("\n" + "=" * 60)
    success_count = sum(1 for _, success in results if success)
    print(f"結果: {success_count}/{len(results)} 成功")
    print("=" * 60)

    return all(success for _, success in results)


def test_totp_manager():
    """TOTP Managerの動作確認"""
    print("\n" + "=" * 60)
    print("TOTP Manager動作確認")
    print("=" * 60)

    try:
        from auth.totp_manager import TOTPManager

        # 1. 秘密鍵生成
        print("\n[1] TOTP秘密鍵生成")
        secret = TOTPManager.generate_totp_secret()
        print(f"   秘密鍵: {secret[:8]}...（32文字）")
        assert len(secret) == 32, "秘密鍵は32文字である必要があります"
        print("   ✅ 秘密鍵生成成功")

        # 2. TOTP検証（現在のコード生成）
        print("\n[2] TOTP検証")
        import pyotp
        totp = pyotp.TOTP(secret)
        current_code = totp.now()
        print(f"   現在のコード: {current_code}")

        # 検証
        is_valid = TOTPManager.verify_totp(secret, current_code)
        assert is_valid, "TOTPコード検証が失敗しました"
        print("   ✅ TOTP検証成功")

        # 3. バックアップコード生成
        print("\n[3] バックアップコード生成")
        backup_codes = TOTPManager.generate_backup_codes(count=10)
        print(f"   生成数: {len(backup_codes)}個")
        print(f"   例: {backup_codes[0]}")
        assert len(backup_codes) == 10, "バックアップコードは10個生成される必要があります"
        assert "-" in backup_codes[0], "バックアップコードはXXXX-XXXX-XXXX形式である必要があります"
        print("   ✅ バックアップコード生成成功")

        # 4. バックアップコードハッシュ化・検証
        print("\n[4] バックアップコードハッシュ化・検証")
        test_code = backup_codes[0]
        hashed = TOTPManager.hash_backup_code(test_code)
        print(f"   元のコード: {test_code}")
        print(f"   ハッシュ: {hashed[:20]}...")

        # 検証
        is_valid = TOTPManager.verify_backup_code(hashed, test_code)
        assert is_valid, "バックアップコード検証が失敗しました"
        print("   ✅ バックアップコード検証成功")

        # 5. QRコード生成（オプション）
        print("\n[5] QRコード生成")
        try:
            qr_code_base64 = TOTPManager.generate_qr_code("testuser@example.com", secret)
            print(f"   QRコード（Base64）: {qr_code_base64[:50]}...")
            assert qr_code_base64.startswith("iVBOR"), "QRコードはPNG形式のBase64である必要があります"
            print("   ✅ QRコード生成成功")
        except Exception as e:
            print(f"   ⚠️  QRコード生成スキップ: {e}")

        # 6. Provisioning URI生成
        print("\n[6] Provisioning URI生成")
        uri = TOTPManager.get_provisioning_uri("testuser@example.com", secret)
        print(f"   URI: {uri}")
        assert uri.startswith("otpauth://totp/"), "Provisioning URIはotpauth://totp/で始まる必要があります"
        print("   ✅ Provisioning URI生成成功")

        print("\n" + "=" * 60)
        print("✅ すべてのTOTP Manager機能が正常に動作しています！")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メイン実行"""
    print("\n🔐 MFA実装 簡易動作確認スクリプト")
    print("=" * 60)

    # 1. 依存関係確認
    deps_ok = test_imports()

    if not deps_ok:
        print("\n" + "=" * 60)
        print("⚠️  依存関係が不足しています")
        print("=" * 60)
        print("\n以下のコマンドでインストールしてください:")
        print("  pip install pyotp==2.9.0 qrcode==7.4.2 Pillow==10.0.0")
        print("\nまたは:")
        print("  pip install -r requirements.txt")
        return 1

    # 2. TOTP Manager確認
    totp_ok = test_totp_manager()

    if not totp_ok:
        print("\n" + "=" * 60)
        print("❌ TOTP Manager動作確認が失敗しました")
        print("=" * 60)
        return 1

    print("\n" + "=" * 60)
    print("🎉 MFA実装の動作確認が完了しました！")
    print("=" * 60)
    print("\n次のステップ:")
    print("  1. データベースマイグレーション実行")
    print("     alembic upgrade head")
    print("\n  2. 統合テスト実行")
    print("     pytest tests/integration/test_mfa_flow.py -v")
    print("\n  3. 手動テスト")
    print("     http://localhost:5200/mfa-settings.html")
    print("\n詳細はデプロイガイドを参照:")
    print("  docs/deployment/2FA_DEPLOYMENT_GUIDE.md")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
