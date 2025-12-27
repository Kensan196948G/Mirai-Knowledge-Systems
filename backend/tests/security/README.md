# セキュリティテストスイート

## 概要

このディレクトリには、Mirai Knowledge Systemsの包括的なセキュリティテストが含まれています。

参照: `docs/09_品質保証(QA)/03_Final-Acceptance-Test-Plan.md` セクション 5. セキュリティテスト

## テストファイル

### 1. test_authentication.py
**認証セキュリティテスト**

- パスワード認証が正常に機能すること
- JWTトークンの発行・検証が正しく行われること
- トークンの有効期限が適切に管理されること
- ログアウト後はトークンが無効化されること
- 不正なトークンでAPIアクセスが拒否されること

**テストクラス:**
- `TestPasswordAuthentication` - パスワード認証の検証
- `TestJWTTokenValidation` - JWTトークンの検証
- `TestTokenExpiration` - トークン有効期限の管理
- `TestLogoutTokenInvalidation` - ログアウト処理
- `TestInvalidTokenScenarios` - 不正トークンのシナリオ
- `TestBruteForceProtection` - ブルートフォース攻撃対策
- `TestSecureTokenStorage` - トークンの安全な保存

### 2. test_authorization.py
**認可・権限管理セキュリティテスト**

- ロールベースアクセス制御（RBAC）が機能すること
- 権限のない機能へのアクセスが拒否されること
- ロール昇格攻撃が防止されていること

**テストクラス:**
- `TestRoleBasedAccessControl` - RBAC機能の検証
- `TestUnauthorizedAccess` - 権限なしアクセスの拒否
- `TestPrivilegeEscalation` - ロール昇格攻撃の防止
- `TestHorizontalAccessControl` - 横方向アクセス制御
- `TestResourceOwnership` - リソース所有権の検証
- `TestDirectObjectReference` - 直接オブジェクト参照の保護
- `TestAPIEndpointProtection` - APIエンドポイントの保護
- `TestRoleConsistency` - ロール一貫性の検証

### 3. test_input_validation.py
**入力検証セキュリティテスト**

- XSS（クロスサイトスクリプティング）対策
- SQLインジェクション対策
- CSRF（クロスサイトリクエストフォージェリ）対策
- ファイルアップロード検証

**テストクラス:**
- `TestXSSPrevention` - XSS攻撃の防止
- `TestSQLInjectionPrevention` - SQLインジェクション攻撃の防止
- `TestCSRFPrevention` - CSRF攻撃の防止
- `TestFileUploadValidation` - ファイルアップロードの検証
- `TestInputSanitization` - 入力のサニタイズ
- `TestJSONValidation` - JSON入力の検証

### 4. test_https_security.py
**HTTPS・セキュリティヘッダーテスト**

- HTTPS通信が強制されること
- セキュリティヘッダーが適切に設定されていること
- SSL/TLS設定が安全であること

**テストクラス:**
- `TestHTTPSEnforcement` - HTTPS強制の検証
- `TestSecurityHeaders` - セキュリティヘッダーの確認
- `TestContentSecurityPolicy` - CSPの詳細テスト
- `TestHSTS` - HSTS設定の検証
- `TestSSLTLSConfiguration` - SSL/TLS設定の確認
- `TestSecureConfiguration` - セキュアな設定全般
- `TestErrorHandling` - エラーハンドリングと情報漏洩防止
- `TestRateLimiting` - レート制限の確認
- `TestSessionSecurity` - セッションセキュリティ
- `TestDataProtection` - データ保護の検証

### 5. run_security_scan.sh
**セキュリティスキャン実行スクリプト**

統合的なセキュリティスキャンを実行し、レポートを生成します。

**実行内容:**
1. 環境確認（Python仮想環境、必要なツールのインストール）
2. **Bandit** - 静的コード解析による脆弱性スキャン
3. **Safety** - 依存関係の既知の脆弱性チェック
4. **Pytest** - セキュリティテストの実行
5. 総合レポートの生成
6. サマリーの表示

## 実行方法

### 個別テストの実行

```bash
# 認証テストのみ実行
pytest tests/security/test_authentication.py -v

# 認可テストのみ実行
pytest tests/security/test_authorization.py -v

# 入力検証テストのみ実行
pytest tests/security/test_input_validation.py -v

# HTTPS/セキュリティヘッダーテストのみ実行
pytest tests/security/test_https_security.py -v
```

### 全セキュリティテストの実行

```bash
# 全セキュリティテストを実行
pytest tests/security/ -v

# カバレッジ付きで実行
pytest tests/security/ -v --cov=. --cov-report=html
```

### 統合セキュリティスキャンの実行

```bash
# セキュリティスキャンスクリプトを実行
cd backend
./tests/security/run_security_scan.sh
```

このスクリプトは以下を実行します:
- Bandit による静的コード解析
- Safety による依存関係の脆弱性チェック
- Pytest によるセキュリティテスト実行
- 包括的なレポート生成

### 継続的インテグレーション（CI）での実行

```bash
# CI環境での実行例
pytest tests/security/ \
  --junitxml=reports/security-test-results.xml \
  --cov=. \
  --cov-report=xml:reports/coverage.xml \
  --cov-report=html:reports/coverage_html
```

## レポート出力

セキュリティスキャンを実行すると、以下のレポートが生成されます:

```
backend/tests/reports/security/
├── bandit_report_YYYYMMDD_HHMMSS.txt       # Bandit テキストレポート
├── bandit_report_YYYYMMDD_HHMMSS.json      # Bandit JSONレポート
├── safety_report_YYYYMMDD_HHMMSS.txt       # Safety レポート
├── pytest_security_YYYYMMDD_HHMMSS.xml     # Pytest XMLレポート
├── coverage_security_YYYYMMDD_HHMMSS.txt   # カバレッジレポート
├── coverage_html_YYYYMMDD_HHMMSS/          # HTMLカバレッジレポート
└── security_summary_YYYYMMDD_HHMMSS.txt    # 総合レポート
```

## テスト対象

### セキュリティ要件（参照: 受入テスト計画書）

#### 5.1 認証・認可テスト
- [x] パスワード認証が正常に機能すること
- [x] JWTトークンが正しく発行・検証されること
- [x] トークンの有効期限が適切に管理されること
- [x] ログアウト後はトークンが無効化されること
- [x] 不正なトークンでAPIアクセスが拒否されること
- [x] RBAC（ロールベースアクセス制御）が機能すること
- [x] 権限のない機能へのアクセスが拒否されること

#### 5.2 HTTPS強制確認
- [x] HTTPアクセスがHTTPSにリダイレクトされること
- [x] SSL/TLS証明書が有効であること
- [x] 暗号化通信が使用されていること（TLS 1.2以上）
- [x] 安全でない暗号スイートが無効化されていること

#### 5.3 セキュリティヘッダー確認
- [x] `Strict-Transport-Security` (HSTS)
- [x] `X-Content-Type-Options: nosniff`
- [x] `X-Frame-Options: DENY` or `SAMEORIGIN`
- [x] `X-XSS-Protection: 1; mode=block`
- [x] `Content-Security-Policy`
- [x] `Referrer-Policy`

#### 5.4 CSRF対策確認
- [x] CSRFトークンが生成されること（または JWT使用でCSRF不要）
- [x] 状態変更操作が保護されていること

#### 5.5 XSS対策確認
- [x] ユーザー入力がエスケープされること
- [x] スクリプトタグが実行されないこと
- [x] HTML属性内のXSSが防止されていること
- [x] JavaScriptイベントハンドラーのXSSが防止されていること

テストペイロード:
- `<script>alert('XSS')</script>`
- `<img src=x onerror="alert('XSS')">`
- `<svg/onload=alert('XSS')>`
- `javascript:alert('XSS')`
- `<iframe src="javascript:alert('XSS')">`

#### 5.6 SQLインジェクション対策確認
- [x] パラメータ化クエリが使用されていること
- [x] SQLインジェクションペイロードが無効化されること
- [x] エラーメッセージからDB情報が漏洩しないこと

テストペイロード:
- `' OR '1'='1`
- `'; DROP TABLE users; --`
- `' UNION SELECT * FROM users--`
- `admin'--`

## テスト環境

### 前提条件

```bash
# Python 3.11以上
python --version

# 仮想環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate  # Windows

# 依存関係のインストール
pip install -r requirements.txt
pip install pytest pytest-cov bandit safety
```

### テストデータ

テストでは自動的にテストユーザーとテストデータが作成されます（`conftest.py`）:

- **admin_user** - 管理者権限
- **editor_user** - 編集者権限
- **viewer_user** - 閲覧者権限
- **no_role_user** - ロールなし

## トラブルシューティング

### よくある問題

#### 1. モジュールが見つからない

```bash
# 仮想環境を有効化
source venv/bin/activate

# 必要なパッケージをインストール
pip install pytest pytest-cov bandit safety
```

#### 2. テストが失敗する

```bash
# 詳細なエラー情報を表示
pytest tests/security/ -v --tb=long

# 特定のテストのみ実行
pytest tests/security/test_authentication.py::TestPasswordAuthentication::test_successful_login_with_valid_credentials -v
```

#### 3. Banditが実行できない

```bash
# Banditを再インストール
pip uninstall bandit
pip install bandit[toml]
```

#### 4. パーミッションエラー

```bash
# スクリプトに実行権限を付与
chmod +x tests/security/run_security_scan.sh
```

## 継続的改善

### セキュリティテストの追加

新しいセキュリティ要件が発生した場合:

1. 適切なテストファイルにテストケースを追加
2. テストクラスとテストメソッドを作成
3. ドキュメント（このREADME）を更新
4. CIパイプラインに統合

### レビュープロセス

1. セキュリティテストは全て自動化されている
2. CI/CDパイプラインで毎回実行される
3. 重大な脆弱性が検出された場合は即座に修正
4. 定期的にセキュリティスキャンを実施

## 参考資料

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Safety Documentation](https://pyup.io/safety/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

## 連絡先

セキュリティに関する問題や懸念事項がある場合は、速やかにセキュリティチームに報告してください。

---

**最終更新:** 2025-12-27
**バージョン:** 1.0
**担当:** QA/セキュリティチーム
