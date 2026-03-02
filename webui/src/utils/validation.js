/**
 * @fileoverview バリデーションユーティリティ
 *
 * フォーム入力値・ファイル・TOTP等のバリデーション関数を提供するESMモジュール。
 * バックエンドのパスワードポリシー（password_policy.py）と整合した仕様。
 *
 * @module utils/validation
 * @version 2.0.0
 * @author Mirai Knowledge Systems
 */

import { logger } from '../core/logger.js';

// ============================================================
// 定数定義
// ============================================================

/** パスワードの最小文字数 */
const PASSWORD_MIN_LENGTH = 8;

/** パスワードの最大文字数 */
const PASSWORD_MAX_LENGTH = 128;

/** デフォルトのファイルサイズ上限（MB） */
const DEFAULT_MAX_FILE_SIZE_MB = 50;

/** メールアドレス正規表現（RFC 5322 簡易版） */
const EMAIL_REGEX = /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/;

/** URL正規表現（http/https） */
const URL_REGEX = /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_+.~#?&/=]*)$/;

/** TOTP コード正規表現（6桁数字） */
const TOTP_REGEX = /^\d{6}$/;

// ============================================================
// バリデーション結果型
// ============================================================

/**
 * バリデーション結果オブジェクトを生成する内部関数
 * @private
 * @param {boolean} valid - 検証結果
 * @param {string|null} [error=null] - エラーメッセージ
 * @returns {{valid: boolean, error: string|null}}
 */
function result(valid, error = null) {
  return { valid, error };
}

// ============================================================
// 個別バリデーション関数
// ============================================================

/**
 * メールアドレスバリデーション
 *
 * @param {string} email - メールアドレス
 * @returns {{valid: boolean, error: string|null}} バリデーション結果
 *
 * @example
 * validateEmail('user@example.com');      // { valid: true, error: null }
 * validateEmail('invalid-email');         // { valid: false, error: 'メールアドレスの形式が正しくありません' }
 * validateEmail('');                      // { valid: false, error: 'メールアドレスを入力してください' }
 */
export function validateEmail(email) {
  if (!email || typeof email !== 'string') {
    return result(false, 'メールアドレスを入力してください');
  }

  const trimmed = email.trim();
  if (trimmed.length === 0) {
    return result(false, 'メールアドレスを入力してください');
  }

  if (trimmed.length > 254) {
    return result(false, 'メールアドレスが長すぎます（254文字以内）');
  }

  if (!EMAIL_REGEX.test(trimmed)) {
    return result(false, 'メールアドレスの形式が正しくありません');
  }

  return result(true);
}

/**
 * パスワードポリシー検証
 *
 * ポリシー要件:
 * - 8文字以上128文字以下
 * - 大文字（A-Z）を1文字以上含む
 * - 小文字（a-z）を1文字以上含む
 * - 数字（0-9）を1文字以上含む
 * - 記号（!@#$%^&*等）を1文字以上含む
 *
 * @param {string} password - パスワード
 * @returns {{valid: boolean, error: string|null, strength: 'weak'|'fair'|'strong'|'very_strong'}} バリデーション結果
 *
 * @example
 * validatePassword('Pass1!ab');  // { valid: true, error: null, strength: 'strong' }
 * validatePassword('short');     // { valid: false, error: '8文字以上入力してください', strength: 'weak' }
 */
export function validatePassword(password) {
  if (!password || typeof password !== 'string') {
    return { ...result(false, 'パスワードを入力してください'), strength: 'weak' };
  }

  if (password.length < PASSWORD_MIN_LENGTH) {
    return {
      ...result(false, `パスワードは${PASSWORD_MIN_LENGTH}文字以上で入力してください`),
      strength: 'weak'
    };
  }

  if (password.length > PASSWORD_MAX_LENGTH) {
    return {
      ...result(false, `パスワードは${PASSWORD_MAX_LENGTH}文字以下で入力してください`),
      strength: 'weak'
    };
  }

  const hasUpperCase = /[A-Z]/.test(password);
  const hasLowerCase = /[a-z]/.test(password);
  const hasNumbers = /[0-9]/.test(password);
  const hasSymbols = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?~`]/.test(password);

  const criteriaCount = [hasUpperCase, hasLowerCase, hasNumbers, hasSymbols]
    .filter(Boolean).length;

  // 強度計算
  let strength;
  if (criteriaCount <= 1) strength = 'weak';
  else if (criteriaCount === 2) strength = 'fair';
  else if (criteriaCount === 3) strength = 'strong';
  else strength = 'very_strong';

  // 全条件を満たさない場合はエラー
  if (!hasUpperCase) {
    return { ...result(false, 'パスワードに大文字（A-Z）を含めてください'), strength };
  }
  if (!hasLowerCase) {
    return { ...result(false, 'パスワードに小文字（a-z）を含めてください'), strength };
  }
  if (!hasNumbers) {
    return { ...result(false, 'パスワードに数字（0-9）を含めてください'), strength };
  }
  if (!hasSymbols) {
    return { ...result(false, 'パスワードに記号（!@#$%等）を含めてください'), strength };
  }

  return { ...result(true), strength };
}

/**
 * 必須フィールド検証
 *
 * @param {any} value - 検証する値
 * @param {string} [fieldName='このフィールド'] - フィールド名（エラーメッセージ用）
 * @returns {{valid: boolean, error: string|null}} バリデーション結果
 *
 * @example
 * validateRequired('value', 'タイトル');  // { valid: true, error: null }
 * validateRequired('', 'タイトル');       // { valid: false, error: 'タイトルは必須です' }
 * validateRequired(null, 'タイトル');     // { valid: false, error: 'タイトルは必須です' }
 */
export function validateRequired(value, fieldName = 'このフィールド') {
  if (value == null) {
    return result(false, `${fieldName}は必須です`);
  }

  if (typeof value === 'string' && value.trim().length === 0) {
    return result(false, `${fieldName}は必須です`);
  }

  if (Array.isArray(value) && value.length === 0) {
    return result(false, `${fieldName}は必須です`);
  }

  return result(true);
}

/**
 * 文字数制限検証
 *
 * @param {string} value - 検証する文字列
 * @param {number} min - 最小文字数（0以上）
 * @param {number} max - 最大文字数
 * @param {string} [fieldName='このフィールド'] - フィールド名（エラーメッセージ用）
 * @returns {{valid: boolean, error: string|null}} バリデーション結果
 *
 * @example
 * validateLength('Hello', 1, 10, 'タイトル');   // { valid: true, error: null }
 * validateLength('', 1, 10, 'タイトル');         // { valid: false, error: 'タイトルは1文字以上で入力してください' }
 * validateLength('Very long...', 1, 5, 'タイトル'); // { valid: false, error: 'タイトルは5文字以内で入力してください' }
 */
export function validateLength(value, min, max, fieldName = 'このフィールド') {
  if (value == null) {
    return min > 0
      ? result(false, `${fieldName}は${min}文字以上で入力してください`)
      : result(true);
  }

  const str = String(value);
  const len = str.length;

  if (len < min) {
    return result(false, `${fieldName}は${min}文字以上で入力してください`);
  }

  if (len > max) {
    return result(false, `${fieldName}は${max}文字以内で入力してください`);
  }

  return result(true);
}

/**
 * URLフォーマット検証
 *
 * http:// または https:// で始まる有効なURLかどうか検証する。
 *
 * @param {string} url - 検証するURL
 * @returns {{valid: boolean, error: string|null}} バリデーション結果
 *
 * @example
 * validateUrl('https://example.com');    // { valid: true, error: null }
 * validateUrl('http://localhost:3000');  // { valid: true, error: null }
 * validateUrl('not-a-url');              // { valid: false, error: 'URLの形式が正しくありません' }
 * validateUrl('ftp://example.com');      // { valid: false, error: 'URLはhttp://またはhttps://で始めてください' }
 */
export function validateUrl(url) {
  if (!url || typeof url !== 'string') {
    return result(false, 'URLを入力してください');
  }

  const trimmed = url.trim();
  if (trimmed.length === 0) {
    return result(false, 'URLを入力してください');
  }

  if (!trimmed.startsWith('http://') && !trimmed.startsWith('https://')) {
    return result(false, 'URLはhttp://またはhttps://で始めてください');
  }

  if (!URL_REGEX.test(trimmed)) {
    return result(false, 'URLの形式が正しくありません');
  }

  return result(true);
}

/**
 * ファイルサイズ検証
 *
 * @param {File} file - 検証するFileオブジェクト
 * @param {number} [maxSizeMB=50] - 最大ファイルサイズ（MB）
 * @returns {{valid: boolean, error: string|null}} バリデーション結果
 *
 * @example
 * validateFileSize(file, 10);    // { valid: true, error: null } （10MB以下の場合）
 * validateFileSize(file, 1);     // { valid: false, error: 'ファイルサイズは1MB以内にしてください' }
 */
export function validateFileSize(file, maxSizeMB = DEFAULT_MAX_FILE_SIZE_MB) {
  if (!file || !(file instanceof File)) {
    return result(false, 'ファイルを選択してください');
  }

  const maxBytes = maxSizeMB * 1024 * 1024;
  if (file.size > maxBytes) {
    return result(false, `ファイルサイズは${maxSizeMB}MB以内にしてください（現在: ${_formatFileSizeForError(file.size)}）`);
  }

  return result(true);
}

/**
 * ファイル拡張子・MIMEタイプ検証
 *
 * allowedTypesには拡張子（'.pdf'）またはMIMEタイプ（'application/pdf'）を指定できる。
 *
 * @param {File} file - 検証するFileオブジェクト
 * @param {string[]} allowedTypes - 許可する拡張子またはMIMEタイプの配列
 * @returns {{valid: boolean, error: string|null}} バリデーション結果
 *
 * @example
 * validateFileType(file, ['.pdf', '.docx']);          // { valid: true, error: null }
 * validateFileType(file, ['application/pdf']);        // { valid: true, error: null }
 * validateFileType(file, ['.jpg', '.png', '.gif']);  // { valid: false, error: 'このファイル形式は許可されていません...' }
 */
export function validateFileType(file, allowedTypes) {
  if (!file || !(file instanceof File)) {
    return result(false, 'ファイルを選択してください');
  }

  if (!allowedTypes || allowedTypes.length === 0) {
    return result(true);
  }

  const fileName = file.name.toLowerCase();
  const mimeType = file.type.toLowerCase();

  const isAllowed = allowedTypes.some(type => {
    const normalizedType = type.toLowerCase();
    // 拡張子チェック（.pdf 形式）
    if (normalizedType.startsWith('.')) {
      return fileName.endsWith(normalizedType);
    }
    // MIMEタイプチェック（application/pdf 形式）
    return mimeType === normalizedType || mimeType.startsWith(normalizedType.replace('*', ''));
  });

  if (!isAllowed) {
    const allowedDisplay = allowedTypes.join('、');
    return result(false, `このファイル形式は許可されていません。許可形式: ${allowedDisplay}`);
  }

  return result(true);
}

/**
 * フォームデータ一括バリデーション
 *
 * ルール定義に基づいてフォームデータを一括検証する。
 * 全フィールドのエラーを収集して返す。
 *
 * @param {Object} formData - 検証するフォームデータ
 * @param {Object} rules - バリデーションルール定義
 * @param {boolean} [rules[field].required] - 必須かどうか
 * @param {number} [rules[field].minLength] - 最小文字数
 * @param {number} [rules[field].maxLength] - 最大文字数
 * @param {boolean} [rules[field].email] - メールアドレス検証
 * @param {boolean} [rules[field].url] - URL検証
 * @param {boolean} [rules[field].password] - パスワードポリシー検証
 * @param {string} [rules[field].label] - フィールドの表示名
 * @param {Function} [rules[field].custom] - カスタムバリデーション関数
 * @returns {{valid: boolean, errors: Object<string, string>}} バリデーション結果
 *
 * @example
 * const rules = {
 *   email: { required: true, email: true, label: 'メールアドレス' },
 *   password: { required: true, password: true, label: 'パスワード' },
 *   title: { required: true, minLength: 1, maxLength: 100, label: 'タイトル' }
 * };
 * const { valid, errors } = validateForm({ email: 'bad', password: '123' }, rules);
 * // valid: false
 * // errors: { email: 'メールアドレスの形式が正しくありません', password: '...', title: 'タイトルは必須です' }
 */
export function validateForm(formData, rules) {
  const errors = {};
  let valid = true;

  for (const [field, rule] of Object.entries(rules)) {
    const value = formData[field];
    const fieldName = rule.label || field;

    // 必須チェック
    if (rule.required) {
      const { valid: isValid, error } = validateRequired(value, fieldName);
      if (!isValid) {
        errors[field] = error;
        valid = false;
        continue;
      }
    }

    // 値が空の場合は後続チェックをスキップ
    if (value == null || (typeof value === 'string' && value.trim().length === 0)) {
      continue;
    }

    // メールアドレスチェック
    if (rule.email) {
      const { valid: isValid, error } = validateEmail(value);
      if (!isValid) {
        errors[field] = error;
        valid = false;
        continue;
      }
    }

    // パスワードポリシーチェック
    if (rule.password) {
      const { valid: isValid, error } = validatePassword(value);
      if (!isValid) {
        errors[field] = error;
        valid = false;
        continue;
      }
    }

    // URLチェック
    if (rule.url) {
      const { valid: isValid, error } = validateUrl(value);
      if (!isValid) {
        errors[field] = error;
        valid = false;
        continue;
      }
    }

    // 文字数チェック
    if (rule.minLength != null || rule.maxLength != null) {
      const min = rule.minLength ?? 0;
      const max = rule.maxLength ?? Infinity;
      const { valid: isValid, error } = validateLength(value, min, max, fieldName);
      if (!isValid) {
        errors[field] = error;
        valid = false;
        continue;
      }
    }

    // カスタムバリデーション
    if (typeof rule.custom === 'function') {
      const customResult = rule.custom(value, formData);
      if (customResult !== true && customResult !== null && customResult !== undefined) {
        errors[field] = typeof customResult === 'string'
          ? customResult
          : `${fieldName}の値が不正です`;
        valid = false;
      }
    }
  }

  return { valid, errors };
}

/**
 * TOTP コード検証（6桁数字）
 *
 * RFC 6238準拠のTOTPコードの形式を検証する（内容の正当性はバックエンドが検証）。
 *
 * @param {string} code - TOTPコード
 * @returns {{valid: boolean, error: string|null}} バリデーション結果
 *
 * @example
 * validateTOTPCode('123456');   // { valid: true, error: null }
 * validateTOTPCode('12345');    // { valid: false, error: '認証コードは6桁の数字を入力してください' }
 * validateTOTPCode('12345a');   // { valid: false, error: '認証コードは数字のみ入力してください' }
 */
export function validateTOTPCode(code) {
  if (!code || typeof code !== 'string') {
    return result(false, '認証コードを入力してください');
  }

  const trimmed = code.trim().replace(/\s/g, '');

  if (trimmed.length === 0) {
    return result(false, '認証コードを入力してください');
  }

  if (!/^\d+$/.test(trimmed)) {
    return result(false, '認証コードは数字のみ入力してください');
  }

  if (trimmed.length !== 6) {
    return result(false, '認証コードは6桁の数字を入力してください');
  }

  return result(true);
}

/**
 * バックアップコード検証（8桁英数字 x 2ブロック、ハイフン区切り）
 *
 * @param {string} code - バックアップコード（例: 'ABCD1234-EFGH5678'）
 * @returns {{valid: boolean, error: string|null}} バリデーション結果
 *
 * @example
 * validateBackupCode('ABCD1234-EFGH5678');  // { valid: true, error: null }
 * validateBackupCode('invalid');            // { valid: false, error: 'バックアップコードの形式が正しくありません' }
 */
export function validateBackupCode(code) {
  if (!code || typeof code !== 'string') {
    return result(false, 'バックアップコードを入力してください');
  }

  const trimmed = code.trim().toUpperCase();

  if (trimmed.length === 0) {
    return result(false, 'バックアップコードを入力してください');
  }

  // 形式: 英数字8文字-英数字8文字（ハイフン区切り）
  const BACKUP_CODE_REGEX = /^[A-Z0-9]{8}-[A-Z0-9]{8}$/;
  if (!BACKUP_CODE_REGEX.test(trimmed)) {
    return result(false, 'バックアップコードの形式が正しくありません（例: ABCD1234-EFGH5678）');
  }

  return result(true);
}

// ============================================================
// 内部ユーティリティ
// ============================================================

/**
 * エラーメッセージ用ファイルサイズフォーマット
 * @private
 * @param {number} bytes - バイト数
 * @returns {string}
 */
function _formatFileSizeForError(bytes) {
  if (bytes < 1024) return `${bytes} Bytes`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ============================================================
// 後方互換性レイヤー - window.Validation グローバル公開
// ============================================================
if (typeof window !== 'undefined') {
  window.Validation = {
    validateEmail,
    validatePassword,
    validateRequired,
    validateLength,
    validateUrl,
    validateFileSize,
    validateFileType,
    validateForm,
    validateTOTPCode,
    validateBackupCode
  };

  logger.info('[Validation] ESM module loaded.');
}
