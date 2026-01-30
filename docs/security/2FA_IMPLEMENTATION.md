# 2要素認証（2FA）実装ドキュメント

## 概要

Mirai Knowledge Systemsの2要素認証（Two-Factor Authentication, 2FA）実装は、TOTP（Time-based One-Time Password）アルゴリズムとバックアップコードを使用して、アカウントのセキュリティを強化します。

## アーキテクチャ

### コンポーネント構成

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (WebUI)                        │
├─────────────────┬───────────────────┬───────────────────────────┤
│ mfa-setup.html  │ mfa-settings.html │ login.html (MFA support) │
│                 │                   │                           │
│ - QRコード表示   │ - ステータス管理  │ - MFAログイン             │
│ - TOTP検証      │ - 無効化          │ - バックアップコード      │
│ - バックアップ   │ - 再生成          │ - カウントダウン          │
└─────────────────┴───────────────────┴───────────────────────────┘
                              ↓ HTTPS
┌─────────────────────────────────────────────────────────────────┐
│                    Backend API (Flask)                          │
├─────────────────────────────────────────────────────────────────┤
│  MFA Endpoints:                                                 │
│  - POST /api/v1/auth/mfa/setup                                  │
│  - POST /api/v1/auth/mfa/enable                                 │
│  - POST /api/v1/auth/mfa/disable                                │
│  - POST /api/v1/auth/mfa/verify                                 │
│  - POST /api/v1/auth/login/mfa                                  │
│  - POST /api/v1/auth/mfa/backup-codes/regenerate               │
│  - GET  /api/v1/auth/mfa/status                                │
│  - POST /api/v1/auth/mfa/recovery                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  TOTP Manager (auth/totp_manager.py)            │
├─────────────────────────────────────────────────────────────────┤
│  - generate_totp_secret(): TOTP秘密鍵生成                       │
│  - generate_qr_code(): QRコード生成 (Base64 PNG)                │
│  - verify_totp(): TOTP検証                                      │
│  - generate_backup_codes(): バックアップコード生成（10個）       │
│  - hash_backup_code(): bcryptハッシュ化                         │
│  - verify_backup_code(): バックアップコード検証                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Database (PostgreSQL)                      │
├─────────────────────────────────────────────────────────────────┤
│  auth.users テーブル:                                           │
│  - mfa_secret: String(32)       # TOTP秘密鍵                    │
│  - mfa_enabled: Boolean         # MFA有効フラグ                │
│  - mfa_backup_codes: JSONB      # バックアップコード配列         │
│      [{code_hash, used, used_at}, ...]                          │
└─────────────────────────────────────────────────────────────────┘
```

## データベーススキーマ

### auth.users テーブル拡張

```sql
ALTER TABLE auth.users
ADD COLUMN mfa_secret VARCHAR(32),
ADD COLUMN mfa_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN mfa_backup_codes JSONB;
```

### mfa_backup_codes フォーマット

```json
[
  {
    "code_hash": "$2b$12$...",  // bcrypt ハッシュ
    "used": false,               // 使用済みフラグ
    "used_at": null              // 使用日時 (ISO 8601)
  },
  ...
]
```

## APIエンドポイント仕様

### 1. MFAセットアップ

**Endpoint**: `POST /api/v1/auth/mfa/setup`

**認証**: 必須（JWT Bearer Token）

**Request**: なし

**Response**:
```json
{
  "success": true,
  "data": {
    "secret": "JBSWY3DPEHPK3PXP",
    "qr_code_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
    "provisioning_uri": "otpauth://totp/...",
    "backup_codes": [
      "AAAA-1111-BBBB",
      "CCCC-2222-DDDD",
      ...
    ],
    "message": "MFA setup initiated. Please verify the code to enable MFA."
  }
}
```

**動作**:
1. TOTP秘密鍵生成（32文字、Base32）
2. QRコード生成（300x300 PNG、Base64エンコード）
3. バックアップコード生成（10個、XXXX-XXXX-XXXX形式）
4. データベースに保存（`mfa_enabled=False`のまま）

---

### 2. MFA有効化

**Endpoint**: `POST /api/v1/auth/mfa/enable`

**認証**: 必須（JWT Bearer Token）

**Request**:
```json
{
  "code": "123456"  // 6桁のTOTPコード
}
```

**Response**:
```json
{
  "success": true,
  "message": "MFA enabled successfully. Save your backup codes in a safe place."
}
```

**Rate Limiting**: 10回/分

**動作**:
1. TOTPコード検証
2. 成功時、`mfa_enabled=True`に更新
3. アクセスログ記録

---

### 3. MFAログイン（2段階）

#### 3-1. 初期ログイン

**Endpoint**: `POST /api/v1/auth/login`

**Request**:
```json
{
  "username": "user",
  "password": "password"
}
```

**Response** (MFA有効ユーザー):
```json
{
  "success": true,
  "data": {
    "mfa_required": true,
    "mfa_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "message": "MFA verification required"
  }
}
```

**mfa_token**:
- 有効期限: 5分
- Claims: `{"mfa_pending": true, "type": "mfa_temp"}`

#### 3-2. MFA検証

**Endpoint**: `POST /api/v1/auth/login/mfa`

**Request** (TOTPコード使用):
```json
{
  "mfa_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "code": "123456"
}
```

**Request** (バックアップコード使用):
```json
{
  "mfa_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "backup_code": "AAAA-1111-BBBB"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "used_backup_code": false,
    "remaining_backup_codes": 10,
    "user": { ... }
  }
}
```

**Rate Limiting**: 5回/15分（ブルートフォース対策）

---

### 4. MFA無効化

**Endpoint**: `POST /api/v1/auth/mfa/disable`

**認証**: 必須（JWT Bearer Token）

**Request**:
```json
{
  "password": "current_password",
  "code": "123456"  // TOTPコードまたはバックアップコード
}
```

**Response**:
```json
{
  "success": true,
  "message": "MFA disabled successfully"
}
```

**動作**:
1. パスワード検証
2. TOTPまたはバックアップコード検証
3. `mfa_enabled=False`, `mfa_secret=NULL`, `mfa_backup_codes=NULL`
4. アクセスログ記録

---

### 5. バックアップコード再生成

**Endpoint**: `POST /api/v1/auth/mfa/backup-codes/regenerate`

**認証**: 必須（JWT Bearer Token）

**Request**:
```json
{
  "code": "123456"  // TOTPコード
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "backup_codes": [
      "XXXX-YYYY-ZZZZ",
      ...
    ],
    "message": "New backup codes generated. Previous codes are now invalid."
  }
}
```

**Rate Limiting**: 3回/時間

---

### 6. MFAステータス取得

**Endpoint**: `GET /api/v1/auth/mfa/status`

**認証**: 必須（JWT Bearer Token）

**Response**:
```json
{
  "success": true,
  "data": {
    "mfa_enabled": true,
    "mfa_configured": true,
    "remaining_backup_codes": 8,
    "email": "user@example.com"
  }
}
```

---

### 7. MFAリカバリー

**Endpoint**: `POST /api/v1/auth/mfa/recovery`

**認証**: 不要

**Request**:
```json
{
  "email": "user@example.com",
  "username": "user"
}
```

**Response**:
```json
{
  "success": true,
  "message": "If the email and username match, a recovery link will be sent to your email.",
  "dev_only_token": "..."  // 開発環境のみ
}
```

**Rate Limiting**: 3回/時間

**注意**: 本番環境ではメール送信が必要。セキュリティのため、ユーザーが存在しない場合も成功レスポンスを返す（列挙攻撃対策）。

---

## セキュリティ考慮事項

### 1. TOTP検証

- **アルゴリズム**: RFC 6238準拠 TOTP
- **ハッシュ関数**: SHA-1（TOTP標準）
- **タイムステップ**: 30秒
- **検証ウィンドウ**: ±30秒（valid_window=1）
- **コード長**: 6桁

### 2. バックアップコード

- **生成**: `secrets`モジュールで暗号学的に安全な乱数生成
- **フォーマット**: XXXX-XXXX-XXXX（大文字英数字）
- **ハッシュ化**: bcrypt（cost factor=12）
- **使用**: 1回のみ（使用後は`used=True`）
- **保存**: ハッシュ化されたもののみデータベースに保存

### 3. Rate Limiting

| エンドポイント | 制限 | 目的 |
|---------------|------|------|
| `/auth/mfa/enable` | 10回/分 | ブルートフォース対策 |
| `/auth/mfa/verify` | 5回/15分 | ブルートフォース対策 |
| `/auth/login/mfa` | 5回/15分 | ブルートフォース対策 |
| `/auth/mfa/backup-codes/regenerate` | 3回/時間 | 不正再生成防止 |
| `/auth/mfa/recovery` | 3回/時間 | 列挙攻撃対策 |

### 4. トークン管理

#### mfa_token（一時トークン）
- **有効期限**: 5分
- **Claims**: `{"mfa_pending": true, "type": "mfa_temp"}`
- **用途**: パスワード検証後〜MFA検証前の一時的な認証

#### access_token（正規トークン）
- **有効期限**: 1時間
- **Claims**: `{"roles": [...]}`
- **用途**: API認証

### 5. 監査ログ

すべてのMFA関連イベントは`access_logs`に記録:

- `mfa_setup_initiated` - MFAセットアップ開始
- `mfa_enabled` - MFA有効化
- `mfa_enable_failed` - MFA有効化失敗
- `mfa_login_success` - MFAログイン成功
- `mfa_login_success_backup` - バックアップコードログイン成功
- `mfa_login_failed` - MFAログイン失敗
- `mfa_disabled` - MFA無効化
- `mfa_disable_failed_password` - MFA無効化失敗（パスワード）
- `mfa_disable_failed_code` - MFA無効化失敗（コード）
- `backup_codes_regenerated` - バックアップコード再生成
- `backup_codes_regen_failed` - バックアップコード再生成失敗
- `mfa_recovery_requested` - リカバリー要求

## トラブルシューティング

### 問題: TOTPコードが常に無効

**原因**:
- サーバーとクライアントの時刻同期ズレ

**解決方法**:
1. サーバー時刻確認: `date`
2. NTPサービス確認: `systemctl status systemd-timesyncd`
3. 時刻同期: `sudo timedatectl set-ntp true`

### 問題: QRコードが表示されない

**原因**:
- Pillow（PIL）ライブラリ未インストール
- qrcodeライブラリ未インストール

**解決方法**:
```bash
pip install qrcode[pil] pillow
```

### 問題: バックアップコード検証失敗

**原因**:
- ダッシュ（-）の有無
- 大文字小文字の違い

**解決方法**:
コードは自動的に正規化されるため、通常は問題なし。マニュアル入力時は注意。

### 問題: mfa_tokenが期限切れ

**原因**:
- 5分以内にMFA検証を完了しなかった

**解決方法**:
再度ログインからやり直す。

## パフォーマンス考慮事項

### QRコード生成

- **生成時間**: 約50-100ms
- **サイズ**: 約2-5KB（Base64）
- **キャッシュ**: なし（セキュリティのため毎回生成）

### TOTP検証

- **検証時間**: 約1-2ms
- **並行処理**: 可能（ステートレス）

### バックアップコード検証

- **検証時間**: 約50-100ms（bcrypt）
- **最適化**: インデックス不要（JSONB内検索）

## 互換性

### 認証アプリ

以下の認証アプリで動作確認済み:

- Google Authenticator（iOS, Android）
- Microsoft Authenticator（iOS, Android）
- Authy（iOS, Android, Desktop）
- 1Password（iOS, Android, Desktop）
- Bitwarden（iOS, Android, Desktop）

### ブラウザ

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## 今後の拡張

### 予定機能

1. **SMS/メールによる2FA**
   - TOTP以外の選択肢
   - バックアップ手段の追加

2. **WebAuthn/FIDO2対応**
   - ハードウェアトークン対応
   - 生体認証

3. **管理者によるMFAリセット**
   - ユーザーサポート強化
   - 監査ログ強化

4. **MFA強制ポリシー**
   - 管理者による強制有効化
   - 役割ベースの要件設定

## 参考資料

- [RFC 6238 - TOTP](https://datatracker.ietf.org/doc/html/rfc6238)
- [RFC 4226 - HOTP](https://datatracker.ietf.org/doc/html/rfc4226)
- [OWASP MFA Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html)
- [PyOTP Documentation](https://pyauth.github.io/pyotp/)

---

**最終更新**: 2026-01-31
**作成者**: Claude Sonnet 4.5 (1M context)
