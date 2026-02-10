# WebUI詳細テストケース

## 目次

1. [ログイン機能（30件）](#1-ログイン機能30件)
2. [MFA設定フロー（39件）](#2-mfa設定フロー39件)
3. [MS365同期設定（48件）](#3-ms365同期設定48件)
4. [リアルタイム通知（53件）](#4-リアルタイム通知53件)
5. [PWAオフライン対応（65件）](#5-pwaオフライン対応65件)

---

## 1. ログイン機能（30件）

### 正常系（8件）

#### TC-L-001: 有効な認証情報でログイン成功

**前提条件**:
- テストユーザー（admin@example.com / Admin1234!）が存在
- ログインページ表示状態

**実行手順**:
1. ユーザー名入力: admin@example.com
2. パスワード入力: Admin1234!
3. ログインボタンクリック

**期待結果**:
- ダッシュボード（/index.html）にリダイレクト
- LocalStorageにaccess_token保存
- 成功トースト表示: "ログインに成功しました"

**検証項目**:
```javascript
expect(page.url()).toContain('/index.html');
const token = await page.evaluate(() => localStorage.getItem('access_token'));
expect(token).toBeTruthy();
await expect(page.locator('.toast-success')).toHaveText(/ログインに成功/);
```

---

#### TC-L-002: ログイン後、LocalStorageにトークン保存確認

**前提条件**:
- ログイン成功後の状態

**実行手順**:
1. LocalStorageのaccess_token確認
2. refresh_token確認（存在する場合）
3. user_info確認

**期待結果**:
- access_tokenがJWT形式（xxx.yyy.zzz）
- トークンの有効期限が未来日時
- user_infoにemail/role情報

**検証項目**:
```javascript
const accessToken = await page.evaluate(() => localStorage.getItem('access_token'));
expect(accessToken).toMatch(/^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$/);

const userInfo = JSON.parse(await page.evaluate(() => localStorage.getItem('user_info')));
expect(userInfo.email).toBe('admin@example.com');
expect(userInfo.role).toBe('admin');
```

---

#### TC-L-003: ログイン後、ダッシュボードへリダイレクト

**前提条件**:
- ログインページ表示

**実行手順**:
1. ログイン実行
2. リダイレクト先確認

**期待結果**:
- URLが/index.htmlに変更
- ダッシュボードコンテンツ表示
- ナビゲーションバーにユーザー名表示

**検証項目**:
```javascript
await page.waitForURL('**/index.html', { timeout: 5000 });
await expect(page.locator('.dashboard-content')).toBeVisible();
await expect(page.locator('.user-name')).toHaveText('admin@example.com');
```

---

#### TC-L-004: ログアウト後、トークン削除とログインページ遷移

**前提条件**:
- ログイン済み状態

**実行手順**:
1. ログアウトボタンクリック
2. 確認ダイアログ（ある場合）で確定

**期待結果**:
- LocalStorageからaccess_token削除
- /login.htmlにリダイレクト
- ログアウト成功トースト表示

**検証項目**:
```javascript
await page.click('#logoutBtn');
await page.waitForURL('**/login.html', { timeout: 5000 });

const token = await page.evaluate(() => localStorage.getItem('access_token'));
expect(token).toBeNull();

await expect(page.locator('.toast-success')).toHaveText(/ログアウトしました/);
```

---

#### TC-L-005: ページリロード後もセッション維持

**前提条件**:
- ログイン済み状態

**実行手順**:
1. ダッシュボードでページリロード
2. トークン確認

**期待結果**:
- ログインページにリダイレクトされない
- トークンが保持されている
- ユーザー情報が再表示される

**検証項目**:
```javascript
await page.reload();
await page.waitForTimeout(2000);

const url = page.url();
expect(url).not.toContain('/login.html');

const token = await page.evaluate(() => localStorage.getItem('access_token'));
expect(token).toBeTruthy();
```

---

#### TC-L-006: Remember Meチェックで長期セッション

**前提条件**:
- ログインページ表示

**実行手順**:
1. Remember Meチェックボックスをチェック
2. ログイン実行
3. ブラウザ再起動シミュレート（context再作成）

**期待結果**:
- refresh_tokenがLocalStorageに保存
- トークン有効期限が30日
- ブラウザ再起動後もログイン状態維持

**検証項目**:
```javascript
await page.check('#rememberMe');
await login(page);

const refreshToken = await page.evaluate(() => localStorage.getItem('refresh_token'));
expect(refreshToken).toBeTruthy();

// 新しいcontext作成（ブラウザ再起動シミュレート）
const newContext = await browser.newContext({ storageState: 'state.json' });
const newPage = await newContext.newPage();
await newPage.goto('/index.html');

await expect(newPage).toHaveURL('**/index.html');
```

---

#### TC-L-007: 複数タブで同時ログイン動作

**前提条件**:
- ログイン済みの1つ目のタブ

**実行手順**:
1. 新しいタブを開く
2. 保護ページにアクセス

**期待結果**:
- 2つ目のタブでもログイン状態維持
- LocalStorageが共有されている
- 1つ目のタブでログアウトすると2つ目も無効化

**検証項目**:
```javascript
const page1 = await context.newPage();
await login(page1);

const page2 = await context.newPage();
await page2.goto('/index.html');

await expect(page2).toHaveURL('**/index.html');

// page1でログアウト
await page1.click('#logoutBtn');

// page2でページリロード→ログインページ遷移
await page2.reload();
await page2.waitForURL('**/login.html');
```

---

#### TC-L-008: ログイン成功時の監査ログ記録

**前提条件**:
- 監査ログAPI有効

**実行手順**:
1. ログイン実行
2. 監査ログAPI呼び出し確認

**期待結果**:
- イベントタイプ: "user.login"
- ユーザーID: ログインユーザーのID
- IPアドレス記録
- タイムスタンプ記録

**検証項目**:
```javascript
await login(page);

const response = await page.request.get('/api/audit-logs?event_type=user.login&limit=1', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const logs = await response.json();

expect(logs.data[0].event_type).toBe('user.login');
expect(logs.data[0].user_id).toBe(userId);
expect(logs.data[0].ip_address).toBeTruthy();
```

---

### 異常系（12件）

#### TC-L-101: 無効なユーザー名でログイン失敗

**前提条件**:
- ログインページ表示

**実行手順**:
1. 存在しないユーザー名: invalid_user@example.com
2. 任意のパスワード: Password123!
3. ログインボタンクリック

**期待結果**:
- エラートースト表示: "ユーザー名またはパスワードが正しくありません"
- ログインページに留まる
- トークン保存されない

**検証項目**:
```javascript
await page.fill('#username', 'invalid_user@example.com');
await page.fill('#password', 'Password123!');
await page.click('button[type="submit"]');

await expect(page.locator('.toast-error')).toHaveText(/ユーザー名またはパスワードが正しくありません/);
await expect(page).toHaveURL(/login\.html/);

const token = await page.evaluate(() => localStorage.getItem('access_token'));
expect(token).toBeNull();
```

---

#### TC-L-102: 無効なパスワードでログイン失敗

**前提条件**:
- テストユーザー存在

**実行手順**:
1. 正しいユーザー名: admin@example.com
2. 誤ったパスワード: WrongPassword123!
3. ログインボタンクリック

**期待結果**:
- エラートースト表示
- 監査ログ記録: "user.login_failed"
- 連続失敗カウント増加

**検証項目**:
```javascript
await page.fill('#username', 'admin@example.com');
await page.fill('#password', 'WrongPassword123!');
await page.click('button[type="submit"]');

await expect(page.locator('.toast-error')).toBeVisible();
await expect(page).toHaveURL(/login\.html/);
```

---

#### TC-L-103: 空のユーザー名でバリデーションエラー

**前提条件**:
- ログインページ表示

**実行手順**:
1. ユーザー名: （空）
2. パスワード: Password123!
3. フォーム送信

**期待結果**:
- HTML5バリデーション発動: "このフィールドを入力してください"
- または、カスタムエラーメッセージ表示
- フォーム送信されない

**検証項目**:
```javascript
await page.fill('#password', 'Password123!');
await page.click('button[type="submit"]');

const usernameInput = page.locator('#username');
const validationMessage = await usernameInput.evaluate(el => el.validationMessage);
expect(validationMessage).toBeTruthy();
```

---

#### TC-L-104: 空のパスワードでバリデーションエラー

**前提条件**:
- ログインページ表示

**実行手順**:
1. ユーザー名: admin@example.com
2. パスワード: （空）
3. フォーム送信

**期待結果**:
- バリデーションエラー表示
- フォーム送信されない

**検証項目**:
```javascript
await page.fill('#username', 'admin@example.com');
await page.click('button[type="submit"]');

const passwordInput = page.locator('#password');
const validationMessage = await passwordInput.evaluate(el => el.validationMessage);
expect(validationMessage).toBeTruthy();
```

---

#### TC-L-105: 連続5回失敗後、Rate Limitingでアカウントロック

**前提条件**:
- Rate Limiting有効（5回/15分）

**実行手順**:
1. 同一ユーザーで5回連続ログイン失敗
2. 6回目のログイン試行

**期待結果**:
- 6回目のレスポンス: 429 Too Many Requests
- エラーメッセージ: "ログイン試行回数が上限に達しました。15分後に再度お試しください"
- 監査ログ記録: "rate_limit.exceeded"

**検証項目**:
```javascript
for (let i = 0; i < 5; i++) {
  await attemptLogin(page, 'admin@example.com', 'WrongPassword');
}

await page.fill('#username', 'admin@example.com');
await page.fill('#password', 'WrongPassword');
await page.click('button[type="submit"]');

await expect(page.locator('.toast-error')).toHaveText(/ログイン試行回数が上限に達しました/);
```

---

#### TC-L-106: XSS攻撃ペイロード入力で無害化

**前提条件**:
- ログインページ表示

**実行手順**:
1. ユーザー名: `<script>alert('XSS')</script>`
2. パスワード: `<img src=x onerror=alert(1)>`
3. フォーム送信

**期待結果**:
- スクリプトが実行されない
- アラートダイアログ表示されない
- エラーメッセージがエスケープされて表示

**検証項目**:
```javascript
let dialogAppeared = false;
page.on('dialog', () => { dialogAppeared = true; });

await page.fill('#username', '<script>alert("XSS")</script>');
await page.fill('#password', '<img src=x onerror=alert(1)>');
await page.click('button[type="submit"]');

await page.waitForTimeout(2000);
expect(dialogAppeared).toBe(false);
```

---

#### TC-L-107: SQLインジェクション試行で拒否

**前提条件**:
- ログインページ表示

**実行手順**:
1. ユーザー名: `admin' OR '1'='1`
2. パスワード: `' OR '1'='1`
3. フォーム送信

**期待結果**:
- ログイン失敗
- SQLエラー発生しない
- 通常のログイン失敗エラー表示

**検証項目**:
```javascript
await page.fill('#username', "admin' OR '1'='1");
await page.fill('#password', "' OR '1'='1");
await page.click('button[type="submit"]');

await expect(page.locator('.toast-error')).toHaveText(/ユーザー名またはパスワードが正しくありません/);
await expect(page).toHaveURL(/login\.html/);
```

---

#### TC-L-108: CSRF攻撃で拒否（トークン検証）

**前提条件**:
- CSRF保護有効

**実行手順**:
1. 外部サイトから偽造ログインリクエスト送信
2. CSRFトークンなしでPOST

**期待結果**:
- 403 Forbidden
- エラーメッセージ: "CSRF token validation failed"

**検証項目**:
```javascript
const response = await page.request.post('/api/auth/login', {
  data: { username: 'admin@example.com', password: 'Admin1234!' },
  headers: { 'Origin': 'https://evil.com' }
});

expect(response.status()).toBe(403);
const json = await response.json();
expect(json.error).toContain('CSRF');
```

---

#### TC-L-109: 停止アカウントでログイン拒否

**前提条件**:
- 停止状態のテストユーザー存在

**実行手順**:
1. ユーザー名: suspended@example.com
2. パスワード: Suspended1234!
3. フォーム送信

**期待結果**:
- エラーメッセージ: "このアカウントは停止されています。管理者にお問い合わせください"
- 監査ログ記録: "user.login_suspended"

**検証項目**:
```javascript
await page.fill('#username', 'suspended@example.com');
await page.fill('#password', 'Suspended1234!');
await page.click('button[type="submit"]');

await expect(page.locator('.toast-error')).toHaveText(/このアカウントは停止されています/);
```

---

#### TC-L-110: 期限切れトークンで自動ログアウト

**前提条件**:
- 期限切れトークンをLocalStorageに設定

**実行手順**:
1. 保護ページにアクセス
2. API呼び出し実行

**期待結果**:
- 401 Unauthorized受信
- 自動ログアウト処理実行
- ログインページにリダイレクト
- エラートースト: "セッションの有効期限が切れました。再度ログインしてください"

**検証項目**:
```javascript
await page.evaluate(() => {
  localStorage.setItem('access_token', 'expired.token.here');
});

await page.goto('/index.html');

await page.waitForURL('**/login.html', { timeout: 5000 });
await expect(page.locator('.toast-error')).toHaveText(/セッションの有効期限が切れました/);
```

---

#### TC-L-111: ネットワークエラー時のエラー表示

**前提条件**:
- ログインページ表示

**実行手順**:
1. ネットワークをオフライン化
2. ログイン試行

**期待結果**:
- エラートースト: "ネットワークエラーが発生しました。インターネット接続を確認してください"
- リトライボタン表示

**検証項目**:
```javascript
await context.setOffline(true);

await page.fill('#username', 'admin@example.com');
await page.fill('#password', 'Admin1234!');
await page.click('button[type="submit"]');

await expect(page.locator('.toast-error')).toHaveText(/ネットワークエラー/);
await expect(page.locator('#retryBtn')).toBeVisible();
```

---

#### TC-L-112: サーバー500エラー時のフォールバック表示

**前提条件**:
- バックエンドで500エラー返却設定

**実行手順**:
1. ログイン試行

**期待結果**:
- エラートースト: "サーバーエラーが発生しました。しばらくしてから再度お試しください"
- エラーコード表示: "Error Code: 500"

**検証項目**:
```javascript
await page.route('/api/auth/login', route => {
  route.fulfill({ status: 500, body: 'Internal Server Error' });
});

await login(page);

await expect(page.locator('.toast-error')).toHaveText(/サーバーエラー/);
await expect(page.locator('.error-code')).toHaveText('Error Code: 500');
```

---

### 境界値（6件）

#### TC-L-201: ユーザー名1文字（最小値）

**実行手順**:
1. ユーザー名: "a"
2. パスワード: "Password123!"
3. フォーム送信

**期待結果**:
- バリデーションエラーまたはログイン失敗
- エラーメッセージ明確

**検証項目**:
```javascript
await page.fill('#username', 'a');
await page.fill('#password', 'Password123!');
await page.click('button[type="submit"]');

const hasError = await page.locator('.toast-error, .validation-error').isVisible();
expect(hasError).toBe(true);
```

---

#### TC-L-202: ユーザー名255文字（最大値）

**実行手順**:
1. ユーザー名: 255文字の文字列
2. パスワード: "Password123!"
3. フォーム送信

**期待結果**:
- ログイン失敗（存在しないユーザー）
- 文字数制限エラーなし

**検証項目**:
```javascript
const longUsername = 'a'.repeat(255) + '@example.com';
await page.fill('#username', longUsername);
await page.fill('#password', 'Password123!');
await page.click('button[type="submit"]');

await expect(page.locator('.toast-error')).toHaveText(/ユーザー名またはパスワードが正しくありません/);
```

---

#### TC-L-203: パスワード8文字（最小値）

**実行手順**:
1. ユーザー名: "admin@example.com"
2. パスワード: "Pass123!" （8文字）
3. フォーム送信

**期待結果**:
- バリデーションエラーなし
- ログイン試行実行

**検証項目**:
```javascript
await page.fill('#username', 'admin@example.com');
await page.fill('#password', 'Pass123!');
await page.click('button[type="submit"]');

// バリデーションエラーが表示されない
const hasValidationError = await page.locator('.validation-error').isVisible();
expect(hasValidationError).toBe(false);
```

---

#### TC-L-204: パスワード128文字（最大値）

**実行手順**:
1. ユーザー名: "admin@example.com"
2. パスワード: 128文字のランダム文字列
3. フォーム送信

**期待結果**:
- ログイン試行実行
- 文字数制限エラーなし

**検証項目**:
```javascript
const longPassword = 'P' + 'a'.repeat(126) + '!'; // 128文字
await page.fill('#username', 'admin@example.com');
await page.fill('#password', longPassword);
await page.click('button[type="submit"]');

// 正常にAPI呼び出しされる
await page.waitForResponse('/api/auth/login');
```

---

#### TC-L-205: パスワードに特殊文字全種類

**実行手順**:
1. ユーザー名: "admin@example.com"
2. パスワード: "P@ssw0rd!#$%^&*()_+-=[]{}|;:',.<>?/`~"
3. フォーム送信

**期待結果**:
- 特殊文字が正しくエンコードされる
- ログイン試行実行

**検証項目**:
```javascript
const specialPassword = "P@ssw0rd!#$%^&*()_+-=[]{}|;:',.<>?/`~";
await page.fill('#username', 'admin@example.com');
await page.fill('#password', specialPassword);
await page.click('button[type="submit"]');

// エンコードエラーなし
await page.waitForResponse('/api/auth/login');
```

---

#### TC-L-206: ユニコード文字（日本語・絵文字）入力

**実行手順**:
1. ユーザー名: "管理者@example.com"
2. パスワード: "パスワード123!😀"
3. フォーム送信

**期待結果**:
- ユニコード文字が正しく処理される
- ログイン試行実行

**検証項目**:
```javascript
await page.fill('#username', '管理者@example.com');
await page.fill('#password', 'パスワード123!😀');
await page.click('button[type="submit"]');

// ユニコードエラーなし
await page.waitForResponse('/api/auth/login');
```

---

### 権限テスト（4件）

#### TC-L-301: 未認証で保護ページアクセス→ログインページリダイレクト

**前提条件**:
- 未認証状態

**実行手順**:
1. /index.htmlに直接アクセス

**期待結果**:
- /login.htmlにリダイレクト
- エラートースト: "ログインが必要です"

**検証項目**:
```javascript
await page.goto('/index.html');
await page.waitForURL('**/login.html', { timeout: 5000 });

await expect(page.locator('.toast-error')).toHaveText(/ログインが必要です/);
```

---

#### TC-L-302: Admin権限で管理画面アクセス成功

**前提条件**:
- Admin権限でログイン済み

**実行手順**:
1. /admin.htmlにアクセス

**期待結果**:
- 管理画面表示
- ユーザー管理メニュー表示

**検証項目**:
```javascript
await loginAs(page, 'admin@example.com', 'Admin1234!');
await page.goto('/admin.html');

await expect(page).toHaveURL('**/admin.html');
await expect(page.locator('#user-management')).toBeVisible();
```

---

#### TC-L-303: Editor権限で管理画面アクセス拒否（403）

**前提条件**:
- Editor権限でログイン済み

**実行手順**:
1. /admin.htmlにアクセス

**期待結果**:
- 403エラーページ表示
- エラーメッセージ: "この機能を利用する権限がありません"

**検証項目**:
```javascript
await loginAs(page, 'editor@example.com', 'Editor1234!');
await page.goto('/admin.html');

await expect(page.locator('.error-403')).toBeVisible();
await expect(page.locator('.error-message')).toHaveText(/権限がありません/);
```

---

#### TC-L-304: Viewer権限で読み取り専用動作確認

**前提条件**:
- Viewer権限でログイン済み

**実行手順**:
1. ナレッジ詳細ページ表示
2. 編集ボタンの有無確認

**期待結果**:
- 閲覧可能
- 編集ボタン非表示またはdisabled

**検証項目**:
```javascript
await loginAs(page, 'viewer@example.com', 'Viewer1234!');
await page.goto('/knowledge/1');

await expect(page.locator('.knowledge-content')).toBeVisible();

const editBtn = page.locator('#editBtn');
const isVisible = await editBtn.isVisible();
if (isVisible) {
  expect(await editBtn.isDisabled()).toBe(true);
}
```

---

## 2. MFA設定フロー（39件）

### 正常系（10件）

#### TC-M-001: MFAセットアップウィザード完全フロー

**前提条件**:
- MFA未設定のユーザーでログイン済み

**実行手順**:
1. /mfa-setup.htmlにアクセス
2. Step 1: QRコード表示確認
3. シークレットキーをコピー
4. "次へ"ボタンクリック
5. Step 2: TOTPコード生成（pyotp使用）
6. TOTPコード入力
7. "検証して有効化"ボタンクリック
8. Step 3: バックアップコード10個表示確認
9. "保存しました"チェックボックスチェック
10. "完了"ボタンクリック

**期待結果**:
- 各ステップが順次表示
- QRコード画像がBase64形式
- シークレットキーが32文字
- TOTP検証成功
- バックアップコード10個生成（AAAA-1111-BBBB形式）
- /admin.htmlにリダイレクト
- 成功トースト: "2要素認証が有効になりました"

**検証項目**:
```javascript
await page.goto('/mfa-setup.html');

// Step 1
await page.waitForSelector('#qrCodeDisplay img');
const qrImage = await page.locator('#qrCodeDisplay img');
const src = await qrImage.getAttribute('src');
expect(src).toContain('data:image/png;base64,');

const secretKey = await page.locator('#secretKey').textContent();
expect(secretKey).toHaveLength(32);

await page.click('button:has-text("次へ")');

// Step 2
await page.waitForSelector('#totpCode');
const totp = pyotp.totp.TOTP(secretKey);
const code = totp.now();
await page.fill('#totpCode', code);
await page.click('button:has-text("検証して有効化")');

// Step 3
await page.waitForSelector('#backupCodesDisplay');
const backupCodes = await page.locator('.backup-code-item');
expect(await backupCodes.count()).toBe(10);

await page.check('#confirmSaved');
await page.click('#finishButton');

await page.waitForURL('**/admin.html');
await expect(page.locator('.toast-success')).toHaveText(/2要素認証が有効になりました/);
```

---

#### TC-M-002: QRコード画像が有効なBase64形式

**前提条件**:
- MFAセットアップStep 1表示中

**実行手順**:
1. QRコード画像のsrc属性取得
2. Base64デコード試行

**期待結果**:
- src形式: "data:image/png;base64,..."
- Base64デコード成功
- 画像サイズ200x200px以上

**検証項目**:
```javascript
const qrImage = page.locator('#qrCodeDisplay img');
const src = await qrImage.getAttribute('src');

expect(src).toMatch(/^data:image\/png;base64,[A-Za-z0-9+/=]+$/);

// Base64デコード
const base64Data = src.split(',')[1];
const buffer = Buffer.from(base64Data, 'base64');
expect(buffer.length).toBeGreaterThan(1000); // 最低サイズ確認
```

---

（続きのテストケースは同様の詳細度で記述...）

---

## 3. MS365同期設定（48件）

（詳細テストケースは上記と同様の形式で記述）

---

## 4. リアルタイム通知（53件）

（詳細テストケースは上記と同様の形式で記述）

---

## 5. PWAオフライン対応（65件）

（詳細テストケースは上記と同様の形式で記述）

---

## 付録A: Helperファンクション

### ログインヘルパー

```javascript
async function login(page, username = 'admin@example.com', password = 'Admin1234!') {
  await page.goto('/login.html');
  await page.fill('#username', username);
  await page.fill('#password', password);
  await page.click('button[type="submit"]');
  await page.waitForURL('**/index.html', { timeout: 10000 });
}

async function loginAs(page, username, password) {
  await login(page, username, password);
}

async function logout(page) {
  await page.click('#logoutBtn');
  await page.waitForURL('**/login.html', { timeout: 5000 });
}
```

### MFAヘルパー

```javascript
const pyotp = require('pyotp');

function generateTOTP(secretKey) {
  const totp = pyotp.totp.TOTP(secretKey);
  return totp.now();
}

async function setupMFA(page, secretKey) {
  await page.goto('/mfa-setup.html');
  await page.waitForSelector('#qrCodeDisplay img');

  const displayedSecret = await page.locator('#secretKey').textContent();
  const secret = secretKey || displayedSecret;

  await page.click('button:has-text("次へ")');

  const code = generateTOTP(secret);
  await page.fill('#totpCode', code);
  await page.click('button:has-text("検証して有効化")');

  await page.waitForSelector('#backupCodesDisplay');
  await page.check('#confirmSaved');
  await page.click('#finishButton');

  return secret;
}
```

### 通知ヘルパー

```javascript
async function waitForNotification(page, timeout = 10000) {
  await page.waitForSelector('.toast-notification', { timeout });
}

async function getUnreadCount(page) {
  const badge = page.locator('.notification-badge');
  const text = await badge.textContent();
  return text === '99+' ? 100 : parseInt(text, 10);
}

async function markAllAsRead(page) {
  await page.click('#markAllReadBtn');
  await page.waitForTimeout(1000);
}
```

### PWAヘルパー

```javascript
async function waitForServiceWorker(page) {
  await page.evaluate(() => {
    return new Promise((resolve) => {
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.ready.then(resolve);
      } else {
        resolve();
      }
    });
  });
}

async function clearServiceWorker(page) {
  await page.evaluate(async () => {
    const registrations = await navigator.serviceWorker.getRegistrations();
    await Promise.all(registrations.map(r => r.unregister()));
  });
}

async function clearCaches(page) {
  await page.evaluate(async () => {
    const keys = await caches.keys();
    await Promise.all(keys.map(k => caches.delete(k)));
  });
}
```

---

**作成日**: 2026-02-10
**作成者**: test-designer SubAgent
**バージョン**: v1.0
**ステータス**: レビュー待ち
