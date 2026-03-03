/**
 * @fileoverview validation.js ユニットテスト
 *
 * webui/src/utils/validation.js の全バリデーション関数をテスト。
 * ESMモジュールをfs.readFileSync + evalで読み込み、
 * window.Validation グローバルを経由して関数を検証する。
 *
 * @version 1.0.0
 */

const fs = require('fs');
const path = require('path');

// ----------------------------------------------------------------
// グローバルモック設定（eval前に設定必須）
// ----------------------------------------------------------------

// loggerモック（ESMモジュール内の import { logger } を置き換え）
global.logger = {
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
  debug: jest.fn()
};

// validation.js を読み込み、import文を除去してeval
const validationPath = path.join(
  __dirname,
  '../../../webui/src/utils/validation.js'
);
let validationCode = fs.readFileSync(validationPath, 'utf8');

// ESM import文を除去
validationCode = validationCode.replace(
  /^import\s+.*?;?\s*$/gm,
  '// [import removed for test]'
);
// export function/const/let/var/async を export なしに変換
validationCode = validationCode.replace(
  /^export\s+(?=function|async\s+function|class|const|let|var)/gm,
  ''
);
// export default を削除
validationCode = validationCode.replace(/^export\s+default\s+/gm, '');
// export { ... } ブロックを削除
validationCode = validationCode.replace(
  /^export\s*\{[^}]*\}\s*;?\s*$/gm,
  '// [export block removed]'
);

// logger参照を global.logger に変換
validationCode = validationCode.replace(
  /\blogger\.info\b/g,
  'global.logger.info'
);

eval(validationCode);

// ----------------------------------------------------------------
// テスト: validateEmail
// ----------------------------------------------------------------

describe('Validation.validateEmail', () => {
  test('有効なメールアドレスで valid:true を返す', () => {
    const result = window.Validation.validateEmail('user@example.com');
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  test('サブドメイン付きメールアドレスで valid:true を返す', () => {
    expect(window.Validation.validateEmail('user@mail.example.co.jp').valid).toBe(true);
  });

  test('+記号付きメールアドレスで valid:true を返す', () => {
    expect(window.Validation.validateEmail('user+tag@example.com').valid).toBe(true);
  });

  test('空文字列で valid:false を返す', () => {
    const result = window.Validation.validateEmail('');
    expect(result.valid).toBe(false);
    expect(result.error).toBe('メールアドレスを入力してください');
  });

  test('nullで valid:false を返す', () => {
    const result = window.Validation.validateEmail(null);
    expect(result.valid).toBe(false);
    expect(result.error).toBe('メールアドレスを入力してください');
  });

  test('undefinedで valid:false を返す', () => {
    const result = window.Validation.validateEmail(undefined);
    expect(result.valid).toBe(false);
  });

  test('@なしで valid:false を返す', () => {
    const result = window.Validation.validateEmail('invalidformat');
    expect(result.valid).toBe(false);
    expect(result.error).toBe('メールアドレスの形式が正しくありません');
  });

  test('ドメインなしで valid:false を返す', () => {
    const result = window.Validation.validateEmail('user@');
    expect(result.valid).toBe(false);
  });

  test('254文字超で valid:false を返す（上限チェック）', () => {
    const longEmail = 'a'.repeat(250) + '@example.com';
    const result = window.Validation.validateEmail(longEmail);
    expect(result.valid).toBe(false);
    expect(result.error).toContain('254文字以内');
  });

  test('空白のみ文字列で valid:false を返す', () => {
    const result = window.Validation.validateEmail('   ');
    expect(result.valid).toBe(false);
    expect(result.error).toBe('メールアドレスを入力してください');
  });
});

// ----------------------------------------------------------------
// テスト: validatePassword
// ----------------------------------------------------------------

describe('Validation.validatePassword', () => {
  test('全条件を満たすパスワードで valid:true を返す', () => {
    const result = window.Validation.validatePassword('Pass1!abcd');
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  test('全条件を満たす場合 strength が very_strong になる', () => {
    const result = window.Validation.validatePassword('Pass1!abcd');
    expect(result.strength).toBe('very_strong');
  });

  test('nullで valid:false を返す', () => {
    const result = window.Validation.validatePassword(null);
    expect(result.valid).toBe(false);
    expect(result.strength).toBe('weak');
  });

  test('7文字のパスワードで valid:false（最小文字数未満）', () => {
    const result = window.Validation.validatePassword('Sh0rt!');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('8文字以上');
  });

  test('129文字のパスワードで valid:false（最大文字数超過）', () => {
    const longPwd = 'A1!a' + 'b'.repeat(125);
    const result = window.Validation.validatePassword(longPwd);
    expect(result.valid).toBe(false);
    expect(result.error).toContain('128文字以下');
  });

  test('大文字なしで valid:false（大文字要件）', () => {
    const result = window.Validation.validatePassword('lowercase1!abc');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('大文字');
  });

  test('小文字なしで valid:false（小文字要件）', () => {
    const result = window.Validation.validatePassword('UPPERCASE1!ABC');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('小文字');
  });

  test('数字なしで valid:false（数字要件）', () => {
    const result = window.Validation.validatePassword('Password!abc');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('数字');
  });

  test('記号なしで valid:false（記号要件）', () => {
    const result = window.Validation.validatePassword('Password1abc');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('記号');
  });

  test('大小文字のみ（2条件）で strength が fair になる', () => {
    // 長さは8文字以上確保
    const result = window.Validation.validatePassword('Abcdefgh');
    expect(result.strength).toBe('fair');
  });

  test('大小文字＋数字（3条件）で strength が strong になる', () => {
    const result = window.Validation.validatePassword('Abcdef12');
    expect(result.strength).toBe('strong');
  });
});

// ----------------------------------------------------------------
// テスト: validateRequired
// ----------------------------------------------------------------

describe('Validation.validateRequired', () => {
  test('通常の文字列で valid:true を返す', () => {
    const result = window.Validation.validateRequired('value', 'タイトル');
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  test('nullで valid:false を返す', () => {
    const result = window.Validation.validateRequired(null, 'タイトル');
    expect(result.valid).toBe(false);
    expect(result.error).toBe('タイトルは必須です');
  });

  test('undefinedで valid:false を返す', () => {
    const result = window.Validation.validateRequired(undefined, 'フィールド');
    expect(result.valid).toBe(false);
  });

  test('空文字列で valid:false を返す', () => {
    const result = window.Validation.validateRequired('', '説明');
    expect(result.valid).toBe(false);
    expect(result.error).toBe('説明は必須です');
  });

  test('空白のみ文字列で valid:false を返す', () => {
    const result = window.Validation.validateRequired('   ', '入力欄');
    expect(result.valid).toBe(false);
  });

  test('空配列で valid:false を返す', () => {
    const result = window.Validation.validateRequired([], 'リスト');
    expect(result.valid).toBe(false);
    expect(result.error).toBe('リストは必須です');
  });

  test('要素のある配列で valid:true を返す', () => {
    const result = window.Validation.validateRequired(['item'], 'リスト');
    expect(result.valid).toBe(true);
  });

  test('0（数値）で valid:true を返す（nullでないため）', () => {
    const result = window.Validation.validateRequired(0, '数値');
    expect(result.valid).toBe(true);
  });

  test('fieldName省略時のデフォルトメッセージ確認', () => {
    const result = window.Validation.validateRequired(null);
    expect(result.error).toBe('このフィールドは必須です');
  });
});

// ----------------------------------------------------------------
// テスト: validateLength
// ----------------------------------------------------------------

describe('Validation.validateLength', () => {
  test('min以上max以下の文字列で valid:true を返す', () => {
    const result = window.Validation.validateLength('Hello', 1, 10, 'タイトル');
    expect(result.valid).toBe(true);
  });

  test('ちょうど最小文字数で valid:true を返す', () => {
    expect(window.Validation.validateLength('a', 1, 10, 'タイトル').valid).toBe(true);
  });

  test('ちょうど最大文字数で valid:true を返す', () => {
    expect(window.Validation.validateLength('1234567890', 1, 10, 'タイトル').valid).toBe(true);
  });

  test('最小文字数未満で valid:false を返す', () => {
    const result = window.Validation.validateLength('', 1, 10, 'タイトル');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('1文字以上');
  });

  test('最大文字数超過で valid:false を返す', () => {
    const result = window.Validation.validateLength('12345678901', 1, 10, 'タイトル');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('10文字以内');
  });

  test('nullかつmin>0で valid:false を返す', () => {
    const result = window.Validation.validateLength(null, 1, 10, 'タイトル');
    expect(result.valid).toBe(false);
  });

  test('nullかつmin=0で valid:true を返す', () => {
    const result = window.Validation.validateLength(null, 0, 10, 'タイトル');
    expect(result.valid).toBe(true);
  });

  test('数値も文字列変換して検証する', () => {
    const result = window.Validation.validateLength(12345, 1, 10, '値');
    expect(result.valid).toBe(true);
  });
});

// ----------------------------------------------------------------
// テスト: validateUrl
// ----------------------------------------------------------------

describe('Validation.validateUrl', () => {
  test('https:// URLで valid:true を返す', () => {
    expect(window.Validation.validateUrl('https://example.com').valid).toBe(true);
  });

  test('http:// URLで valid:true を返す', () => {
    expect(window.Validation.validateUrl('http://example.com').valid).toBe(true);
  });

  test('nullで valid:false を返す', () => {
    const result = window.Validation.validateUrl(null);
    expect(result.valid).toBe(false);
    expect(result.error).toBe('URLを入力してください');
  });

  test('空文字列で valid:false を返す', () => {
    const result = window.Validation.validateUrl('');
    expect(result.valid).toBe(false);
    expect(result.error).toBe('URLを入力してください');
  });

  test('ftp://で始まるURLで valid:false（http/https必須）', () => {
    const result = window.Validation.validateUrl('ftp://example.com');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('http://またはhttps://');
  });

  test('スキームなしURLで valid:false を返す', () => {
    const result = window.Validation.validateUrl('example.com');
    expect(result.valid).toBe(false);
  });
});

// ----------------------------------------------------------------
// テスト: validateTOTPCode
// ----------------------------------------------------------------

describe('Validation.validateTOTPCode', () => {
  test('6桁の数字で valid:true を返す', () => {
    const result = window.Validation.validateTOTPCode('123456');
    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  test('000000でも valid:true を返す（全ゼロ）', () => {
    expect(window.Validation.validateTOTPCode('000000').valid).toBe(true);
  });

  test('999999でも valid:true を返す（全9）', () => {
    expect(window.Validation.validateTOTPCode('999999').valid).toBe(true);
  });

  test('5桁の数字で valid:false を返す', () => {
    const result = window.Validation.validateTOTPCode('12345');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('6桁');
  });

  test('7桁の数字で valid:false を返す', () => {
    const result = window.Validation.validateTOTPCode('1234567');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('6桁');
  });

  test('英字を含む文字列で valid:false を返す（数字のみ）', () => {
    const result = window.Validation.validateTOTPCode('12345a');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('数字のみ');
  });

  test('nullで valid:false を返す', () => {
    const result = window.Validation.validateTOTPCode(null);
    expect(result.valid).toBe(false);
    expect(result.error).toBe('認証コードを入力してください');
  });

  test('undefinedで valid:false を返す', () => {
    expect(window.Validation.validateTOTPCode(undefined).valid).toBe(false);
  });

  test('空文字列で valid:false を返す', () => {
    const result = window.Validation.validateTOTPCode('');
    expect(result.valid).toBe(false);
  });

  test('スペース区切りの6桁数字もtrim後に valid:true を返す', () => {
    const result = window.Validation.validateTOTPCode(' 123456 ');
    expect(result.valid).toBe(true);
  });
});

// ----------------------------------------------------------------
// テスト: validateBackupCode
// ----------------------------------------------------------------

describe('Validation.validateBackupCode', () => {
  test('ABCD1234-EFGH5678 形式で valid:true を返す', () => {
    const result = window.Validation.validateBackupCode('ABCD1234-EFGH5678');
    expect(result.valid).toBe(true);
  });

  test('小文字入力もtoUpperCase後に valid:true を返す', () => {
    const result = window.Validation.validateBackupCode('abcd1234-efgh5678');
    expect(result.valid).toBe(true);
  });

  test('nullで valid:false を返す', () => {
    const result = window.Validation.validateBackupCode(null);
    expect(result.valid).toBe(false);
    expect(result.error).toBe('バックアップコードを入力してください');
  });

  test('不正な形式で valid:false を返す（7桁-8桁）', () => {
    const result = window.Validation.validateBackupCode('ABCD123-EFGH5678');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('形式が正しくありません');
  });

  test('ハイフンなしの16桁で valid:false を返す', () => {
    const result = window.Validation.validateBackupCode('ABCD1234EFGH5678');
    expect(result.valid).toBe(false);
  });
});

// ----------------------------------------------------------------
// テスト: validateForm（統合バリデーション）
// ----------------------------------------------------------------

describe('Validation.validateForm', () => {
  test('全フィールドが有効な場合 valid:true を返す', () => {
    const formData = {
      email: 'user@example.com',
      password: 'Pass1!abcd'
    };
    const rules = {
      email: { required: true, email: true, label: 'メールアドレス' },
      password: { required: true, password: true, label: 'パスワード' }
    };
    const { valid, errors } = window.Validation.validateForm(formData, rules);
    expect(valid).toBe(true);
    expect(Object.keys(errors)).toHaveLength(0);
  });

  test('必須フィールドが空の場合 valid:false を返す', () => {
    const formData = { email: '' };
    const rules = { email: { required: true, label: 'メールアドレス' } };
    const { valid, errors } = window.Validation.validateForm(formData, rules);
    expect(valid).toBe(false);
    expect(errors.email).toBeDefined();
  });

  test('メール形式が不正な場合 errors.email が設定される', () => {
    const formData = { email: 'bad-email' };
    const rules = { email: { email: true, label: 'メールアドレス' } };
    const { valid, errors } = window.Validation.validateForm(formData, rules);
    expect(valid).toBe(false);
    expect(errors.email).toContain('形式が正しくありません');
  });

  test('文字数制限違反（maxLength超過）で errors が設定される', () => {
    const formData = { title: 'a'.repeat(101) }; // 101文字でmaxLength:100を超過
    const rules = { title: { minLength: 1, maxLength: 100, label: 'タイトル' } };
    const { valid, errors } = window.Validation.validateForm(formData, rules);
    expect(valid).toBe(false);
    expect(errors.title).toBeDefined();
  });

  test('カスタムバリデーション関数が機能する', () => {
    const formData = { age: '17' };
    const rules = {
      age: {
        custom: (val) => parseInt(val) >= 18 || '18歳以上である必要があります'
      }
    };
    const { valid, errors } = window.Validation.validateForm(formData, rules);
    expect(valid).toBe(false);
    expect(errors.age).toBe('18歳以上である必要があります');
  });

  test('カスタムバリデーション通過時はエラーなし', () => {
    const formData = { age: '20' };
    const rules = {
      age: {
        custom: (val) => parseInt(val) >= 18 || '18歳以上である必要があります'
      }
    };
    const { valid, errors } = window.Validation.validateForm(formData, rules);
    expect(valid).toBe(true);
    expect(errors.age).toBeUndefined();
  });
});

// ----------------------------------------------------------------
// テスト: window.Validation グローバル公開確認
// ----------------------------------------------------------------

describe('Validation グローバル公開', () => {
  test('window.Validation が定義されている', () => {
    expect(window.Validation).toBeDefined();
  });

  test('validateEmail が関数である', () => {
    expect(typeof window.Validation.validateEmail).toBe('function');
  });

  test('validatePassword が関数である', () => {
    expect(typeof window.Validation.validatePassword).toBe('function');
  });

  test('validateRequired が関数である', () => {
    expect(typeof window.Validation.validateRequired).toBe('function');
  });

  test('validateLength が関数である', () => {
    expect(typeof window.Validation.validateLength).toBe('function');
  });

  test('validateUrl が関数である', () => {
    expect(typeof window.Validation.validateUrl).toBe('function');
  });

  test('validateTOTPCode が関数である', () => {
    expect(typeof window.Validation.validateTOTPCode).toBe('function');
  });

  test('validateBackupCode が関数である', () => {
    expect(typeof window.Validation.validateBackupCode).toBe('function');
  });

  test('validateForm が関数である', () => {
    expect(typeof window.Validation.validateForm).toBe('function');
  });
});
