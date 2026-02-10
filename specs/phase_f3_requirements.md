# Phase F-3: ユーティリティモジュール分割 - 機能要件書

**バージョン**: 1.0.0
**作成日**: 2026-02-10
**作成者**: spec-planner SubAgent
**ステータス**: Draft

---

## 1. 概要

### 1.1 機能名
Phase F-3: ユーティリティモジュール分割（Utility Modules Separation）

### 1.2 目的
- 共通ユーティリティ関数のモジュール化
- `webui/src/utils/` ディレクトリへの統合
- コード重複の排除と再利用性の向上
- 単体テストの容易化

### 1.3 優先度
**Medium** - Phase F-2完了後に実施

### 1.4 担当者
- **実装**: code-implementer SubAgent
- **レビュー**: code-reviewer SubAgent
- **テスト設計**: test-designer SubAgent

### 1.5 前提条件
- Phase F-1完了（Viteビルドシステム、コアモジュール）
- Phase F-2完了（機能モジュール分割）
- 既存の dom-helpers.js の動作確認済み

---

## 2. 機能仕様

### 2.1 対象モジュール

以下の4つのユーティリティモジュールを `webui/src/utils/` に実装します。

#### 2.1.1 dom-helpers.js
- **目的**: DOM操作の共通化とXSS対策
- **元ファイル**: webui/dom-helpers.js（1,085行）
- **想定行数**: 約1,100行（ESモジュール化＋JSDoc）
- **依存**: logger.js

#### 2.1.2 date-formatter.js
- **目的**: 日付フォーマット処理の統一
- **元ファイル**: app.js、detail-pages.js内の日付関連関数
- **想定行数**: 約150行
- **依存**: なし（Pure JavaScript）

#### 2.1.3 validation.js
- **目的**: バリデーション処理の共通化
- **元ファイル**: app.js、detail-pages.js内のバリデーション関数
- **想定行数**: 約200行
- **依存**: なし

#### 2.1.4 file-utils.js
- **目的**: ファイル操作の共通化
- **元ファイル**: webui/file-preview.js（819行）+ app.js内のファイル処理
- **想定行数**: 約900行
- **依存**: logger.js

---

### 2.2 入力仕様

#### 2.2.1 dom-helpers.js

##### モジュールAPI
```javascript
/**
 * テキストノードを安全に作成（XSS対策）
 *
 * @param {string} text - テキスト内容
 * @returns {Text} - テキストノード
 */
export function createTextNode(text)

/**
 * 要素を安全に作成
 *
 * @param {string} tagName - タグ名
 * @param {Object} options - オプション
 * @param {string} options.className - CSSクラス
 * @param {string} options.id - 要素ID
 * @param {Object} options.attributes - 属性オブジェクト
 * @param {string} options.textContent - テキスト内容（XSS安全）
 * @returns {HTMLElement} - 作成された要素
 */
export function createElement(tagName, options = {})

/**
 * 要素を空にする（子要素を全削除）
 *
 * @param {HTMLElement} element - 対象要素
 * @returns {void}
 */
export function clearElement(element)

/**
 * 要素を表示/非表示
 *
 * @param {HTMLElement} element - 対象要素
 * @param {boolean} visible - 表示するかどうか
 * @returns {void}
 */
export function setVisible(element, visible)

/**
 * CSSクラスをトグル
 *
 * @param {HTMLElement} element - 対象要素
 * @param {string} className - クラス名
 * @param {boolean} force - 強制的に追加/削除（オプション）
 * @returns {void}
 */
export function toggleClass(element, className, force = undefined)

/**
 * HTML文字列をサニタイズ（XSS対策）
 *
 * @param {string} html - HTML文字列
 * @returns {string} - サニタイズ済みHTML
 */
export function sanitizeHTML(html)

/**
 * URLをサニタイズ（XSS対策）
 *
 * @param {string} url - URL文字列
 * @returns {string} - サニタイズ済みURL
 */
export function sanitizeURL(url)

/**
 * フォームデータを安全に取得
 *
 * @param {HTMLFormElement} form - フォーム要素
 * @returns {Object} - フォームデータオブジェクト
 */
export function getFormData(form)

/**
 * テーブル行を作成
 *
 * @param {Array<string|HTMLElement>} cells - セルデータ
 * @param {Object} options - オプション
 * @param {string} options.className - 行のクラス名
 * @param {Function} options.onClick - クリックハンドラー
 * @returns {HTMLTableRowElement} - テーブル行
 */
export function createTableRow(cells, options = {})

/**
 * ページネーションUIを作成
 *
 * @param {Object} paginationData - ページネーション情報
 * @param {number} paginationData.page - 現在のページ
 * @param {number} paginationData.total_pages - 総ページ数
 * @param {Function} onPageChange - ページ変更ハンドラー
 * @returns {HTMLElement} - ページネーションUI
 */
export function createPagination(paginationData, onPageChange)

/**
 * モーダルダイアログを表示
 *
 * @param {Object} options - モーダルオプション
 * @param {string} options.title - タイトル
 * @param {string|HTMLElement} options.content - 本文
 * @param {Array<Object>} options.buttons - ボタン配列
 * @returns {Promise<string>} - クリックされたボタンのvalue
 */
export async function showModal(options)

/**
 * トーストメッセージを表示
 *
 * @param {string} message - メッセージ
 * @param {string} type - タイプ (success, error, warning, info)
 * @param {number} duration - 表示時間（ミリ秒、デフォルト: 3000）
 * @returns {void}
 */
export function showToast(message, type = 'info', duration = 3000)
```

---

#### 2.2.2 date-formatter.js

##### モジュールAPI
```javascript
/**
 * 日付を日本語形式にフォーマット
 *
 * @param {Date|string|number} date - 日付オブジェクト、ISO文字列、Unixタイムスタンプ
 * @param {Object} options - フォーマットオプション
 * @param {boolean} options.includeTime - 時刻を含めるか（デフォルト: false）
 * @param {boolean} options.includeSeconds - 秒を含めるか（デフォルト: false）
 * @param {boolean} options.useWareki - 和暦を使用するか（デフォルト: false）
 * @returns {string} - フォーマット済み日付文字列
 *
 * @example
 * formatDate('2026-02-10T12:30:00Z')
 * // '2026年2月10日'
 *
 * formatDate('2026-02-10T12:30:00Z', { includeTime: true })
 * // '2026年2月10日 12時30分'
 *
 * formatDate('2026-02-10T12:30:00Z', { useWareki: true })
 * // '令和8年2月10日'
 */
export function formatDate(date, options = {})

/**
 * 日付を相対表記にフォーマット
 *
 * @param {Date|string|number} date - 日付オブジェクト、ISO文字列、Unixタイムスタンプ
 * @returns {string} - 相対日付文字列
 *
 * @example
 * formatRelativeDate('2026-02-10T12:00:00Z')  // 現在: 2026-02-10T12:05:00Z
 * // '5分前'
 *
 * formatRelativeDate('2026-02-09T12:00:00Z')
 * // '1日前'
 */
export function formatRelativeDate(date)

/**
 * 日付範囲を文字列にフォーマット
 *
 * @param {Date|string|number} startDate - 開始日
 * @param {Date|string|number} endDate - 終了日
 * @returns {string} - フォーマット済み日付範囲
 *
 * @example
 * formatDateRange('2026-02-10', '2026-02-15')
 * // '2026年2月10日 〜 2026年2月15日'
 */
export function formatDateRange(startDate, endDate)

/**
 * ISO 8601文字列をパース
 *
 * @param {string} isoString - ISO 8601文字列
 * @returns {Date} - Dateオブジェクト
 */
export function parseISO(isoString)

/**
 * DateオブジェクトをISO 8601文字列に変換
 *
 * @param {Date} date - Dateオブジェクト
 * @returns {string} - ISO 8601文字列
 */
export function toISO(date)

/**
 * タイムゾーンを変換
 *
 * @param {Date|string|number} date - 日付
 * @param {string} timezone - タイムゾーン（例: 'Asia/Tokyo'）
 * @returns {Date} - 変換後のDateオブジェクト
 */
export function convertTimezone(date, timezone)

/**
 * 営業日を計算（土日祝を除く）
 *
 * @param {Date|string|number} startDate - 開始日
 * @param {number} businessDays - 営業日数
 * @param {Array<Date|string>} holidays - 祝日配列（オプション）
 * @returns {Date} - 計算後の日付
 */
export function addBusinessDays(startDate, businessDays, holidays = [])

/**
 * 年齢を計算
 *
 * @param {Date|string|number} birthDate - 生年月日
 * @returns {number} - 年齢
 */
export function calculateAge(birthDate)
```

---

#### 2.2.3 validation.js

##### モジュールAPI
```javascript
/**
 * メールアドレスを検証
 *
 * @param {string} email - メールアドレス
 * @returns {boolean} - 有効かどうか
 */
export function isValidEmail(email)

/**
 * URLを検証
 *
 * @param {string} url - URL文字列
 * @returns {boolean} - 有効かどうか
 */
export function isValidURL(url)

/**
 * パスワードを検証
 *
 * @param {string} password - パスワード
 * @param {Object} options - 検証オプション
 * @param {number} options.minLength - 最小文字数（デフォルト: 8）
 * @param {boolean} options.requireUppercase - 大文字必須（デフォルト: true）
 * @param {boolean} options.requireLowercase - 小文字必須（デフォルト: true）
 * @param {boolean} options.requireNumber - 数字必須（デフォルト: true）
 * @param {boolean} options.requireSpecial - 特殊文字必須（デフォルト: true）
 * @returns {Object} - { valid: boolean, errors: string[] }
 */
export function validatePassword(password, options = {})

/**
 * 電話番号を検証（日本形式）
 *
 * @param {string} phoneNumber - 電話番号
 * @returns {boolean} - 有効かどうか
 */
export function isValidPhoneNumber(phoneNumber)

/**
 * 郵便番号を検証（日本形式）
 *
 * @param {string} postalCode - 郵便番号
 * @returns {boolean} - 有効かどうか
 */
export function isValidPostalCode(postalCode)

/**
 * 日付を検証
 *
 * @param {string} dateString - 日付文字列
 * @param {string} format - フォーマット（例: 'YYYY-MM-DD'）
 * @returns {boolean} - 有効かどうか
 */
export function isValidDate(dateString, format = 'YYYY-MM-DD')

/**
 * 文字列長を検証
 *
 * @param {string} str - 文字列
 * @param {number} min - 最小文字数
 * @param {number} max - 最大文字数
 * @returns {boolean} - 有効かどうか
 */
export function isValidLength(str, min, max)

/**
 * 数値範囲を検証
 *
 * @param {number} value - 数値
 * @param {number} min - 最小値
 * @param {number} max - 最大値
 * @returns {boolean} - 有効かどうか
 */
export function isInRange(value, min, max)

/**
 * ファイルサイズを検証
 *
 * @param {File} file - ファイルオブジェクト
 * @param {number} maxSizeMB - 最大サイズ（MB）
 * @returns {boolean} - 有効かどうか
 */
export function isValidFileSize(file, maxSizeMB)

/**
 * ファイル拡張子を検証
 *
 * @param {File|string} file - ファイルオブジェクトまたはファイル名
 * @param {Array<string>} allowedExtensions - 許可する拡張子配列（例: ['pdf', 'docx']）
 * @returns {boolean} - 有効かどうか
 */
export function isValidFileExtension(file, allowedExtensions)

/**
 * フォームデータを一括検証
 *
 * @param {Object} formData - フォームデータオブジェクト
 * @param {Object} rules - 検証ルール
 * @returns {Object} - { valid: boolean, errors: Object }
 *
 * @example
 * const formData = { email: 'test@example.com', password: 'Pass123!' };
 * const rules = {
 *   email: { required: true, type: 'email' },
 *   password: { required: true, minLength: 8 }
 * };
 * const result = validateForm(formData, rules);
 * // { valid: true, errors: {} }
 */
export function validateForm(formData, rules)

/**
 * XSS攻撃パターンを検出
 *
 * @param {string} input - ユーザー入力
 * @returns {boolean} - XSSパターンが含まれているか
 */
export function containsXSS(input)

/**
 * SQLインジェクション攻撃パターンを検出
 *
 * @param {string} input - ユーザー入力
 * @returns {boolean} - SQLインジェクションパターンが含まれているか
 */
export function containsSQLInjection(input)
```

---

#### 2.2.4 file-utils.js

##### モジュールAPI
```javascript
/**
 * ファイルサイズを人間が読める形式にフォーマット
 *
 * @param {number} bytes - バイト数
 * @param {number} decimals - 小数点以下桁数（デフォルト: 2）
 * @returns {string} - フォーマット済みサイズ（例: '1.23 MB'）
 */
export function formatFileSize(bytes, decimals = 2)

/**
 * ファイル拡張子を取得
 *
 * @param {File|string} file - ファイルオブジェクトまたはファイル名
 * @returns {string} - 拡張子（小文字、ドットなし）
 */
export function getFileExtension(file)

/**
 * MIMEタイプを取得
 *
 * @param {string} extension - ファイル拡張子
 * @returns {string} - MIMEタイプ
 */
export function getMIMEType(extension)

/**
 * ファイルを読み込み（Base64）
 *
 * @param {File} file - ファイルオブジェクト
 * @returns {Promise<string>} - Base64エンコードされた文字列
 */
export async function readFileAsBase64(file)

/**
 * ファイルを読み込み（テキスト）
 *
 * @param {File} file - ファイルオブジェクト
 * @param {string} encoding - エンコーディング（デフォルト: 'UTF-8'）
 * @returns {Promise<string>} - ファイル内容
 */
export async function readFileAsText(file, encoding = 'UTF-8')

/**
 * ファイルを読み込み（Data URL）
 *
 * @param {File} file - ファイルオブジェクト
 * @returns {Promise<string>} - Data URL
 */
export async function readFileAsDataURL(file)

/**
 * 画像ファイルをリサイズ
 *
 * @param {File} file - 画像ファイル
 * @param {number} maxWidth - 最大幅
 * @param {number} maxHeight - 最大高さ
 * @param {number} quality - 品質（0.0〜1.0、デフォルト: 0.8）
 * @returns {Promise<Blob>} - リサイズ済み画像Blob
 */
export async function resizeImage(file, maxWidth, maxHeight, quality = 0.8)

/**
 * ファイルプレビューを生成
 *
 * @param {File} file - ファイルオブジェクト
 * @returns {Promise<HTMLElement>} - プレビュー要素
 */
export async function generateFilePreview(file)

/**
 * PDFファイルのサムネイルを生成
 *
 * @param {File} file - PDFファイル
 * @param {number} page - ページ番号（デフォルト: 1）
 * @returns {Promise<string>} - サムネイル画像のData URL
 */
export async function generatePDFThumbnail(file, page = 1)

/**
 * ファイルをダウンロード
 *
 * @param {Blob|string} data - Blobオブジェクトまたは Data URL
 * @param {string} filename - ファイル名
 * @returns {void}
 */
export function downloadFile(data, filename)

/**
 * ファイルアップロード進捗を監視
 *
 * @param {File} file - ファイルオブジェクト
 * @param {string} uploadUrl - アップロードURL
 * @param {Function} onProgress - 進捗コールバック（0〜100）
 * @returns {Promise<Object>} - アップロード結果
 */
export async function uploadFileWithProgress(file, uploadUrl, onProgress)

/**
 * ドラッグ&ドロップを有効化
 *
 * @param {HTMLElement} element - ドロップ対象要素
 * @param {Function} onFileDrop - ファイルドロップコールバック
 * @returns {void}
 */
export function enableDragAndDrop(element, onFileDrop)
```

---

### 2.3 処理仕様

#### 2.3.1 モジュール実装パターン

##### パターン1: Pure Function（副作用なし）
```javascript
/**
 * 日付をフォーマット（Pure Function）
 */
export function formatDate(date, options = {}) {
  // 引数を変更しない
  // グローバル状態を変更しない
  // 常に同じ入力で同じ出力を返す
  const dateObj = new Date(date);
  // ...
  return formattedString;
}
```

##### パターン2: Side Effect Function（副作用あり）
```javascript
/**
 * トーストメッセージを表示（Side Effect Function）
 */
export function showToast(message, type = 'info', duration = 3000) {
  // DOM操作を行う（副作用）
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  // 一定時間後に削除
  setTimeout(() => {
    toast.remove();
  }, duration);
}
```

##### パターン3: Async Function（非同期処理）
```javascript
/**
 * ファイルを読み込み（Async Function）
 */
export async function readFileAsText(file, encoding = 'UTF-8') {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target.result);
    reader.onerror = (e) => reject(new Error('ファイル読み込み失敗'));
    reader.readAsText(file, encoding);
  });
}
```

---

#### 2.3.2 エラーハンドリング統一

```javascript
/**
 * パスワード検証（エラー情報を返却）
 */
export function validatePassword(password, options = {}) {
  const errors = [];

  if (password.length < options.minLength) {
    errors.push(`パスワードは${options.minLength}文字以上必要です`);
  }

  if (options.requireUppercase && !/[A-Z]/.test(password)) {
    errors.push('大文字を1文字以上含めてください');
  }

  // ...

  return {
    valid: errors.length === 0,
    errors
  };
}
```

---

#### 2.3.3 XSS対策パターン

```javascript
/**
 * HTML文字列をサニタイズ
 */
export function sanitizeHTML(html) {
  const div = document.createElement('div');
  div.textContent = html; // innerHTMLではなくtextContentを使用
  return div.innerHTML;
}

/**
 * URLをサニタイズ
 */
export function sanitizeURL(url) {
  try {
    const parsedURL = new URL(url);
    // http/httpsのみ許可
    if (parsedURL.protocol !== 'http:' && parsedURL.protocol !== 'https:') {
      return '#';
    }
    return parsedURL.href;
  } catch (error) {
    return '#'; // 不正なURLは#に置換
  }
}
```

---

### 2.4 出力仕様

#### 2.4.1 正常時レスポンス

##### dom-helpers.js
```javascript
// createElement()
<div class="card" id="card-123">
  カード内容
</div>

// showModal()
'ok'  // OKボタンがクリックされた
'cancel'  // キャンセルボタンがクリックされた
```

##### date-formatter.js
```javascript
// formatDate()
'2026年2月10日'
'2026年2月10日 12時30分'
'令和8年2月10日'

// formatRelativeDate()
'たった今'
'3分前'
'2時間前'
'1日前'
'2週間前'
```

##### validation.js
```javascript
// validatePassword()
{
  valid: false,
  errors: [
    'パスワードは8文字以上必要です',
    '大文字を1文字以上含めてください'
  ]
}

// validateForm()
{
  valid: false,
  errors: {
    email: 'メールアドレスの形式が不正です',
    password: 'パスワードは8文字以上必要です'
  }
}
```

##### file-utils.js
```javascript
// formatFileSize()
'1.23 MB'
'456.78 KB'
'12.34 GB'

// readFileAsBase64()
'iVBORw0KGgoAAAANSUhEUgAA...'

// uploadFileWithProgress()
{
  success: true,
  file_id: 123,
  url: 'https://example.com/files/123'
}
```

---

#### 2.4.2 異常時エラー

```javascript
// readFileAsText() - ファイル読み込み失敗
throw new Error('ファイル読み込み失敗');

// resizeImage() - サポートされていないファイル形式
throw new Error('画像ファイル形式がサポートされていません');

// uploadFileWithProgress() - アップロード失敗
throw new Error('ファイルアップロードに失敗しました: ネットワークエラー');

// validateForm() - 必須フィールド未入力
{
  valid: false,
  errors: {
    title: '必須項目です',
    email: 'メールアドレスの形式が不正です'
  }
}
```

---

## 3. ビジネスルール

### 3.1 Pure Functionの優先
- 副作用のない関数を優先的に実装
- テストが容易、デバッグが簡単
- 可読性が高い

### 3.2 エラーメッセージの日本語化
- すべてのエラーメッセージは日本語
- エンドユーザーにわかりやすい表現
- 技術用語は避ける

### 3.3 XSS対策の徹底
- すべてのDOM操作はXSS対策済み
- `innerHTML` は使用禁止（特別な理由がある場合のみ）
- `textContent` または `createTextNode()` を使用

### 3.4 バリデーションの二重チェック
- フロントエンドで基本的なバリデーション
- バックエンドで厳格なバリデーション
- セキュリティはバックエンドで担保

---

## 4. 制約事項

### 4.1 技術的制約
- **ブラウザ対応**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Pure JavaScript**: 外部ライブラリ不使用（軽量化）
- **Date API**: ネイティブDateオブジェクトを使用（moment.js等は不使用）
- **File API**: ネイティブFile API、FileReader APIを使用

### 4.2 パフォーマンス制約
- 各ユーティリティ関数は10ms以内に実行完了
- ファイル読み込みは非同期処理必須
- メモリリークを起こさない（イベントリスナーの適切な削除）

### 4.3 セキュリティ制約
- すべての外部入力はサニタイズ
- XSS攻撃パターンの検出と防止
- SQLインジェクション攻撃パターンの検出と防止

---

## 5. 受け入れ基準

### 5.1 実装完了基準
- [ ] 4つのユーティリティモジュールが `webui/src/utils/` に配置されている
- [ ] すべての関数にJSDocコメントが付与されている
- [ ] ESモジュール構文（import/export）を使用している
- [ ] Pure Function と Side Effect Function が明確に区別されている
- [ ] `window.MKS_Utils_*` 経由でも呼び出し可能（後方互換性）

### 5.2 品質基準
- [ ] ESLintエラーが0件
- [ ] Prettierフォーマット済み
- [ ] すべての関数に単体テストがある（Jest）
- [ ] テストカバレッジが90%以上
- [ ] E2Eテストが成功する（Playwright）

### 5.3 パフォーマンス基準
- [ ] 各関数の実行時間が10ms以内（ファイル読み込みを除く）
- [ ] メモリリークが発生しない
- [ ] 大量のDOM操作でもパフォーマンス劣化なし

### 5.4 セキュリティ基準
- [ ] すべての外部入力がサニタイズされている
- [ ] XSS攻撃パターンが検出される
- [ ] SQLインジェクション攻撃パターンが検出される
- [ ] セキュリティテストが成功する

### 5.5 ドキュメント基準
- [ ] 各モジュールのREADME.mdが存在する
- [ ] API仕様書が更新されている
- [ ] 使用例が記載されている

---

## 6. 非機能要件（参照）

非機能要件の詳細は `phase_f3_non_functional.md` を参照してください。

---

## 7. 運用定義（参照）

運用定義の詳細は `phase_f3_operations.md` を参照してください。

---

## 変更履歴

| バージョン | 日付 | 変更内容 | 作成者 |
|-----------|------|---------|--------|
| 1.0.0 | 2026-02-10 | 初版作成 | spec-planner SubAgent |

---

**このドキュメントは ITSM および ISO 27001/9001 に準拠しています。**
