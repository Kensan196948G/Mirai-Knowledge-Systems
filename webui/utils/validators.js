/**
 * Validators - Input validation utilities
 * Mirai Knowledge Systems v1.5.0
 *
 * バリデーション関数集
 * - 入力値検証
 * - エラーメッセージ生成
 * - 汎用バリデーション関数
 */

class Validators {
  /**
   * メールアドレス検証
   * @param {string} email - メールアドレス
   * @returns {boolean} 有効ならtrue
   */
  static isValidEmail(email) {
    if (!email || typeof email !== 'string') return false;

    // RFC 5322準拠の簡易版
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email.trim());
  }

  /**
   * パスワード強度チェック
   * @param {string} password - パスワード
   * @returns {Object} {valid: boolean, strength: string, errors: [], score: number}
   */
  static checkPasswordStrength(password) {
    const errors = [];
    let score = 0;

    if (!password || typeof password !== 'string') {
      return {
        valid: false,
        strength: 'invalid',
        errors: ['パスワードを入力してください'],
        score: 0
      };
    }

    // 最低8文字
    if (password.length < 8) {
      errors.push('パスワードは8文字以上にしてください');
    } else {
      score += 1;
      if (password.length >= 12) score += 1;
      if (password.length >= 16) score += 1;
    }

    // 大文字含む
    if (!/[A-Z]/.test(password)) {
      errors.push('大文字を1文字以上含めてください');
    } else {
      score += 1;
    }

    // 小文字含む
    if (!/[a-z]/.test(password)) {
      errors.push('小文字を1文字以上含めてください');
    } else {
      score += 1;
    }

    // 数字含む
    if (!/[0-9]/.test(password)) {
      errors.push('数字を1文字以上含めてください');
    } else {
      score += 1;
    }

    // 特殊文字含む（オプション、スコアボーナス）
    if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
      score += 2;
    }

    // 強度判定
    let strength = 'weak';
    if (errors.length === 0) {
      if (score >= 7) {
        strength = 'very_strong';
      } else if (score >= 5) {
        strength = 'strong';
      } else {
        strength = 'medium';
      }
    }

    return {
      valid: errors.length === 0,
      strength: strength,
      errors: errors,
      score: score
    };
  }

  /**
   * 必須入力チェック
   * @param {*} value - 値
   * @returns {boolean} 入力ありならtrue
   */
  static isRequired(value) {
    if (value === null || value === undefined) return false;

    if (typeof value === 'string') {
      return value.trim() !== '';
    }

    if (Array.isArray(value)) {
      return value.length > 0;
    }

    return true;
  }

  /**
   * 数値範囲チェック
   * @param {number} value - 値
   * @param {number} min - 最小値（省略可）
   * @param {number} max - 最大値（省略可）
   * @returns {boolean} 範囲内ならtrue
   */
  static isInRange(value, min = -Infinity, max = Infinity) {
    const num = typeof value === 'string' ? parseFloat(value) : value;

    if (isNaN(num)) return false;

    return num >= min && num <= max;
  }

  /**
   * URL検証
   * @param {string} url - URL
   * @returns {boolean} 有効なURLならtrue
   */
  static isValidUrl(url) {
    if (!url || typeof url !== 'string') return false;

    try {
      const urlObj = new URL(url);
      // HTTP/HTTPSのみ許可
      return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
    } catch {
      return false;
    }
  }

  /**
   * 日付検証（YYYY-MM-DD）
   * @param {string} dateStr - 日付文字列
   * @returns {boolean} 有効な日付ならtrue
   */
  static isValidDate(dateStr) {
    if (!dateStr || typeof dateStr !== 'string') return false;

    // YYYY-MM-DD形式チェック
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    if (!dateRegex.test(dateStr)) return false;

    // 実在する日付かチェック
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return false;

    // 文字列との整合性チェック（例: 2024-02-30 は無効）
    const [year, month, day] = dateStr.split('-').map(Number);
    return (
      date.getFullYear() === year &&
      date.getMonth() + 1 === month &&
      date.getDate() === day
    );
  }

  /**
   * 日時検証（YYYY-MM-DD HH:MM:SS）
   * @param {string} datetimeStr - 日時文字列
   * @returns {boolean} 有効な日時ならtrue
   */
  static isValidDateTime(datetimeStr) {
    if (!datetimeStr || typeof datetimeStr !== 'string') return false;

    // YYYY-MM-DD HH:MM:SS形式チェック
    const datetimeRegex = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/;
    if (!datetimeRegex.test(datetimeStr)) return false;

    const date = new Date(datetimeStr.replace(' ', 'T'));
    return !isNaN(date.getTime());
  }

  /**
   * 電話番号検証（日本国内）
   * @param {string} phone - 電話番号
   * @returns {boolean} 有効な電話番号ならtrue
   */
  static isValidPhoneNumber(phone) {
    if (!phone || typeof phone !== 'string') return false;

    // ハイフンを除去
    const cleaned = phone.replace(/[-\s]/g, '');

    // 10桁または11桁の数字
    const phoneRegex = /^(0\d{9,10})$/;
    return phoneRegex.test(cleaned);
  }

  /**
   * 郵便番号検証（日本国内）
   * @param {string} postalCode - 郵便番号
   * @returns {boolean} 有効な郵便番号ならtrue
   */
  static isValidPostalCode(postalCode) {
    if (!postalCode || typeof postalCode !== 'string') return false;

    // NNN-NNNN形式 または NNNNNNN形式
    const postalRegex = /^\d{3}-?\d{4}$/;
    return postalRegex.test(postalCode);
  }

  /**
   * ユーザー名検証（英数字、アンダースコア、ハイフン）
   * @param {string} username - ユーザー名
   * @param {number} minLength - 最小文字数（デフォルト: 3）
   * @param {number} maxLength - 最大文字数（デフォルト: 30）
   * @returns {Object} {valid: boolean, errors: []}
   */
  static validateUsername(username, minLength = 3, maxLength = 30) {
    const errors = [];

    if (!username || typeof username !== 'string') {
      return {
        valid: false,
        errors: ['ユーザー名を入力してください']
      };
    }

    if (username.length < minLength) {
      errors.push(`ユーザー名は${minLength}文字以上にしてください`);
    }

    if (username.length > maxLength) {
      errors.push(`ユーザー名は${maxLength}文字以内にしてください`);
    }

    // 英数字、アンダースコア、ハイフンのみ許可
    if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
      errors.push('ユーザー名は英数字、アンダースコア、ハイフンのみ使用できます');
    }

    // 先頭は英字のみ
    if (!/^[a-zA-Z]/.test(username)) {
      errors.push('ユーザー名は英字で始まる必要があります');
    }

    return {
      valid: errors.length === 0,
      errors: errors
    };
  }

  /**
   * ファイルサイズ検証
   * @param {File} file - ファイルオブジェクト
   * @param {number} maxSizeMB - 最大サイズ（MB）
   * @returns {boolean} サイズが許容範囲内ならtrue
   */
  static isValidFileSize(file, maxSizeMB = 10) {
    if (!file || !(file instanceof File)) return false;

    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    return file.size <= maxSizeBytes;
  }

  /**
   * ファイル拡張子検証
   * @param {File} file - ファイルオブジェクト
   * @param {Array<string>} allowedExtensions - 許可する拡張子の配列（例: ['jpg', 'png', 'pdf']）
   * @returns {boolean} 許可された拡張子ならtrue
   */
  static isValidFileExtension(file, allowedExtensions = []) {
    if (!file || !(file instanceof File)) return false;
    if (allowedExtensions.length === 0) return true;

    const fileName = file.name.toLowerCase();
    const extension = fileName.split('.').pop();

    return allowedExtensions.some(ext => ext.toLowerCase() === extension);
  }

  /**
   * カスタムバリデーション実行
   * @param {*} value - 検証する値
   * @param {Array<Function>} validators - バリデータ関数の配列
   * @returns {Object} {valid: boolean, errors: []}
   */
  static validate(value, validators = []) {
    const errors = [];

    validators.forEach(validator => {
      if (typeof validator !== 'function') return;

      const result = validator(value);

      if (result === false) {
        errors.push('検証に失敗しました');
      } else if (typeof result === 'string') {
        errors.push(result);
      } else if (result && result.errors) {
        errors.push(...result.errors);
      }
    });

    return {
      valid: errors.length === 0,
      errors: errors
    };
  }

  /**
   * フォーム全体のバリデーション
   * @param {HTMLFormElement} form - フォーム要素
   * @param {Object} rules - バリデーションルール {fieldName: [validators]}
   * @returns {Object} {valid: boolean, errors: {fieldName: []}}
   */
  static validateForm(form, rules = {}) {
    if (!(form instanceof HTMLFormElement)) {
      throw new TypeError('Invalid form element');
    }

    const errors = {};
    const formData = new FormData(form);

    Object.keys(rules).forEach(fieldName => {
      const value = formData.get(fieldName);
      const fieldValidators = rules[fieldName];

      const result = Validators.validate(value, fieldValidators);

      if (!result.valid) {
        errors[fieldName] = result.errors;
      }
    });

    return {
      valid: Object.keys(errors).length === 0,
      errors: errors
    };
  }
}

// グローバル公開（既存コード互換性）
if (typeof window !== 'undefined') {
  window.Validators = Validators;
}

// ES6モジュールエクスポート
export { Validators };
export default Validators;
