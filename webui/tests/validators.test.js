/**
 * Validators Unit Tests
 * Mirai Knowledge Systems v1.5.0
 *
 * Jest unit tests for utils/validators.js
 */

import { Validators } from '../utils/validators.js';

describe('Validators', () => {
  describe('isValidEmail', () => {
    test('should validate correct email addresses', () => {
      expect(Validators.isValidEmail('test@example.com')).toBe(true);
      expect(Validators.isValidEmail('user.name@domain.co.jp')).toBe(true);
      expect(Validators.isValidEmail('user+tag@example.com')).toBe(true);
    });

    test('should reject invalid email addresses', () => {
      expect(Validators.isValidEmail('invalid')).toBe(false);
      expect(Validators.isValidEmail('invalid@')).toBe(false);
      expect(Validators.isValidEmail('@example.com')).toBe(false);
      expect(Validators.isValidEmail('invalid@example')).toBe(false);
    });

    test('should handle null and undefined', () => {
      expect(Validators.isValidEmail(null)).toBe(false);
      expect(Validators.isValidEmail(undefined)).toBe(false);
    });

    test('should trim whitespace', () => {
      expect(Validators.isValidEmail('  test@example.com  ')).toBe(true);
    });
  });

  describe('checkPasswordStrength', () => {
    test('should validate strong password', () => {
      const result = Validators.checkPasswordStrength('SecurePass123!');
      expect(result.valid).toBe(true);
      expect(result.strength).toBe('very_strong');
      expect(result.errors).toHaveLength(0);
    });

    test('should detect weak password', () => {
      const result = Validators.checkPasswordStrength('weak');
      expect(result.valid).toBe(false);
      expect(result.strength).toBe('weak');
      expect(result.errors.length).toBeGreaterThan(0);
    });

    test('should check minimum length', () => {
      const result = Validators.checkPasswordStrength('Short1');
      expect(result.errors).toContain('パスワードは8文字以上にしてください');
    });

    test('should check for uppercase letters', () => {
      const result = Validators.checkPasswordStrength('lowercase123');
      expect(result.errors).toContain('大文字を1文字以上含めてください');
    });

    test('should check for lowercase letters', () => {
      const result = Validators.checkPasswordStrength('UPPERCASE123');
      expect(result.errors).toContain('小文字を1文字以上含めてください');
    });

    test('should check for numbers', () => {
      const result = Validators.checkPasswordStrength('NoNumbers');
      expect(result.errors).toContain('数字を1文字以上含めてください');
    });

    test('should give bonus for special characters', () => {
      const withSpecial = Validators.checkPasswordStrength('SecurePass123!');
      const withoutSpecial = Validators.checkPasswordStrength('SecurePass123');
      expect(withSpecial.score).toBeGreaterThan(withoutSpecial.score);
    });

    test('should handle null and undefined', () => {
      expect(Validators.checkPasswordStrength(null).valid).toBe(false);
      expect(Validators.checkPasswordStrength(undefined).valid).toBe(false);
    });
  });

  describe('isRequired', () => {
    test('should validate non-empty values', () => {
      expect(Validators.isRequired('value')).toBe(true);
      expect(Validators.isRequired(123)).toBe(true);
      expect(Validators.isRequired([1, 2, 3])).toBe(true);
    });

    test('should reject empty values', () => {
      expect(Validators.isRequired('')).toBe(false);
      expect(Validators.isRequired('   ')).toBe(false);
      expect(Validators.isRequired(null)).toBe(false);
      expect(Validators.isRequired(undefined)).toBe(false);
      expect(Validators.isRequired([])).toBe(false);
    });
  });

  describe('isInRange', () => {
    test('should validate values in range', () => {
      expect(Validators.isInRange(5, 1, 10)).toBe(true);
      expect(Validators.isInRange(1, 1, 10)).toBe(true);
      expect(Validators.isInRange(10, 1, 10)).toBe(true);
    });

    test('should reject values out of range', () => {
      expect(Validators.isInRange(0, 1, 10)).toBe(false);
      expect(Validators.isInRange(11, 1, 10)).toBe(false);
    });

    test('should handle string numbers', () => {
      expect(Validators.isInRange('5', 1, 10)).toBe(true);
    });

    test('should handle infinity defaults', () => {
      expect(Validators.isInRange(1000000)).toBe(true);
    });

    test('should reject NaN', () => {
      expect(Validators.isInRange('not a number', 1, 10)).toBe(false);
    });
  });

  describe('isValidUrl', () => {
    test('should validate correct URLs', () => {
      expect(Validators.isValidUrl('http://example.com')).toBe(true);
      expect(Validators.isValidUrl('https://example.com/path')).toBe(true);
      expect(Validators.isValidUrl('https://example.com:8080/path?query=1')).toBe(true);
    });

    test('should reject invalid URLs', () => {
      expect(Validators.isValidUrl('not a url')).toBe(false);
      expect(Validators.isValidUrl('ftp://example.com')).toBe(false);
    });

    test('should handle null and undefined', () => {
      expect(Validators.isValidUrl(null)).toBe(false);
      expect(Validators.isValidUrl(undefined)).toBe(false);
    });
  });

  describe('isValidDate', () => {
    test('should validate correct dates', () => {
      expect(Validators.isValidDate('2024-01-15')).toBe(true);
      expect(Validators.isValidDate('2024-12-31')).toBe(true);
    });

    test('should reject invalid dates', () => {
      expect(Validators.isValidDate('2024-02-30')).toBe(false);
      expect(Validators.isValidDate('2024-13-01')).toBe(false);
      expect(Validators.isValidDate('invalid')).toBe(false);
      expect(Validators.isValidDate('01/15/2024')).toBe(false);
    });

    test('should handle null and undefined', () => {
      expect(Validators.isValidDate(null)).toBe(false);
      expect(Validators.isValidDate(undefined)).toBe(false);
    });
  });

  describe('isValidDateTime', () => {
    test('should validate correct datetime strings', () => {
      expect(Validators.isValidDateTime('2024-01-15 14:30:00')).toBe(true);
      expect(Validators.isValidDateTime('2024-12-31 23:59:59')).toBe(true);
    });

    test('should reject invalid datetime strings', () => {
      expect(Validators.isValidDateTime('2024-01-15')).toBe(false);
      expect(Validators.isValidDateTime('invalid')).toBe(false);
    });
  });

  describe('isValidPhoneNumber', () => {
    test('should validate Japanese phone numbers', () => {
      expect(Validators.isValidPhoneNumber('090-1234-5678')).toBe(true);
      expect(Validators.isValidPhoneNumber('03-1234-5678')).toBe(true);
      expect(Validators.isValidPhoneNumber('09012345678')).toBe(true);
    });

    test('should reject invalid phone numbers', () => {
      expect(Validators.isValidPhoneNumber('123')).toBe(false);
      expect(Validators.isValidPhoneNumber('invalid')).toBe(false);
    });
  });

  describe('isValidPostalCode', () => {
    test('should validate Japanese postal codes', () => {
      expect(Validators.isValidPostalCode('123-4567')).toBe(true);
      expect(Validators.isValidPostalCode('1234567')).toBe(true);
    });

    test('should reject invalid postal codes', () => {
      expect(Validators.isValidPostalCode('12-345')).toBe(false);
      expect(Validators.isValidPostalCode('invalid')).toBe(false);
    });
  });

  describe('validateUsername', () => {
    test('should validate correct usernames', () => {
      const result = Validators.validateUsername('john_doe');
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    test('should enforce minimum length', () => {
      const result = Validators.validateUsername('ab');
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('ユーザー名は3文字以上にしてください');
    });

    test('should enforce maximum length', () => {
      const result = Validators.validateUsername('a'.repeat(31));
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('ユーザー名は30文字以内にしてください');
    });

    test('should only allow alphanumeric, underscore, and hyphen', () => {
      const result = Validators.validateUsername('user@name');
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('ユーザー名は英数字、アンダースコア、ハイフンのみ使用できます');
    });

    test('should require username to start with a letter', () => {
      const result = Validators.validateUsername('123user');
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('ユーザー名は英字で始まる必要があります');
    });
  });

  describe('isValidFileSize', () => {
    test('should validate file within size limit', () => {
      const file = new File(['content'], 'test.txt', { type: 'text/plain' });
      expect(Validators.isValidFileSize(file, 10)).toBe(true);
    });

    test('should reject file exceeding size limit', () => {
      const largeContent = 'a'.repeat(11 * 1024 * 1024);
      const file = new File([largeContent], 'large.txt', { type: 'text/plain' });
      expect(Validators.isValidFileSize(file, 10)).toBe(false);
    });

    test('should handle null file', () => {
      expect(Validators.isValidFileSize(null, 10)).toBe(false);
    });
  });

  describe('isValidFileExtension', () => {
    test('should validate allowed extensions', () => {
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      expect(Validators.isValidFileExtension(file, ['pdf', 'doc'])).toBe(true);
    });

    test('should reject disallowed extensions', () => {
      const file = new File(['content'], 'test.exe', { type: 'application/x-msdownload' });
      expect(Validators.isValidFileExtension(file, ['pdf', 'doc'])).toBe(false);
    });

    test('should be case-insensitive', () => {
      const file = new File(['content'], 'test.PDF', { type: 'application/pdf' });
      expect(Validators.isValidFileExtension(file, ['pdf'])).toBe(true);
    });

    test('should allow any extension when list is empty', () => {
      const file = new File(['content'], 'test.xyz', { type: 'application/octet-stream' });
      expect(Validators.isValidFileExtension(file, [])).toBe(true);
    });
  });

  describe('validate (custom validators)', () => {
    test('should run multiple validators', () => {
      const validators = [
        (value) => value.length >= 5 || '最低5文字必要です',
        (value) => /\d/.test(value) || '数字を含めてください'
      ];

      const result = Validators.validate('abc', validators);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('最低5文字必要です');
    });

    test('should pass when all validators succeed', () => {
      const validators = [
        (value) => value.length >= 5,
        (value) => /\d/.test(value)
      ];

      const result = Validators.validate('abc123', validators);
      expect(result.valid).toBe(true);
    });
  });

  describe('validateForm', () => {
    test('should validate entire form', () => {
      const form = document.createElement('form');
      const input1 = document.createElement('input');
      input1.name = 'username';
      input1.value = 'ab';
      form.appendChild(input1);

      const rules = {
        username: [(value) => value.length >= 3 || '3文字以上必要です']
      };

      const result = Validators.validateForm(form, rules);
      expect(result.valid).toBe(false);
      expect(result.errors.username).toBeDefined();
    });

    test('should pass valid form', () => {
      const form = document.createElement('form');
      const input1 = document.createElement('input');
      input1.name = 'username';
      input1.value = 'john';
      form.appendChild(input1);

      const rules = {
        username: [(value) => value.length >= 3]
      };

      const result = Validators.validateForm(form, rules);
      expect(result.valid).toBe(true);
      expect(Object.keys(result.errors)).toHaveLength(0);
    });

    test('should throw error for invalid form element', () => {
      expect(() => {
        Validators.validateForm(null, {});
      }).toThrow(TypeError);
    });
  });
});

describe('Global Validators', () => {
  test('should be available on window object', () => {
    expect(window.Validators).toBeDefined();
  });
});
