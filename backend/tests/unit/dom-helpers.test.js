/**
 * Unit Tests for dom-helpers.js
 * DOM操作ヘルパー関数のテスト
 */

// テスト対象のファイルを読み込み
const fs = require('fs');
const path = require('path');
const domHelpersCode = fs.readFileSync(
  path.join(__dirname, '../../../webui/dom-helpers.js'),
  'utf8'
);

// グローバルスコープで評価
eval(domHelpersCode);

describe('DOM Helpers - Security Functions', () => {
  describe('escapeHtml', () => {
    test('should escape HTML special characters', () => {
      const input = '<script>alert("XSS")</script>';
      const expected = '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;';
      expect(escapeHtml(input)).toBe(expected);
    });

    test('should escape all dangerous characters', () => {
      expect(escapeHtml('&')).toBe('&amp;');
      expect(escapeHtml('<')).toBe('&lt;');
      expect(escapeHtml('>')).toBe('&gt;');
      expect(escapeHtml('"')).toBe('&quot;');
      expect(escapeHtml("'")).toBe('&#039;');
    });

    test('should handle null and undefined', () => {
      expect(escapeHtml(null)).toBe('');
      expect(escapeHtml(undefined)).toBe('');
    });

    test('should handle numbers and convert to string', () => {
      expect(escapeHtml(123)).toBe('123');
      expect(escapeHtml(0)).toBe('0');
    });

    test('should handle mixed content', () => {
      const input = 'Hello <b>World</b> & "Friends"';
      const expected = 'Hello &lt;b&gt;World&lt;/b&gt; &amp; &quot;Friends&quot;';
      expect(escapeHtml(input)).toBe(expected);
    });
  });

  describe('createSecureElement', () => {
    test('should create element with className', () => {
      const element = createSecureElement('div', { className: 'test-class' });
      expect(element.tagName).toBe('DIV');
      expect(element.className).toBe('test-class');
    });

    test('should create element with textContent', () => {
      const element = createSecureElement('span', { textContent: 'Hello World' });
      expect(element.tagName).toBe('SPAN');
      expect(element.textContent).toBe('Hello World');
    });

    test('should create element with attributes', () => {
      const element = createSecureElement('a', {
        attributes: {
          href: 'https://example.com',
          target: '_blank'
        }
      });
      expect(element.getAttribute('href')).toBe('https://example.com');
      expect(element.getAttribute('target')).toBe('_blank');
    });

    test('should create element with inline styles', () => {
      const element = createSecureElement('div', {
        style: {
          color: 'red',
          fontSize: '16px'
        }
      });
      expect(element.style.color).toBe('red');
      expect(element.style.fontSize).toBe('16px');
    });

    test('should create element with children', () => {
      const child1 = document.createElement('span');
      child1.textContent = 'Child 1';
      const child2 = document.createElement('span');
      child2.textContent = 'Child 2';

      const parent = createSecureElement('div', {
        children: [child1, child2]
      });

      expect(parent.children.length).toBe(2);
      expect(parent.children[0].textContent).toBe('Child 1');
      expect(parent.children[1].textContent).toBe('Child 2');
    });

    test('should prevent XSS through textContent', () => {
      const element = createSecureElement('div', {
        textContent: '<script>alert("XSS")</script>'
      });
      expect(element.innerHTML).toBe('&lt;script&gt;alert("XSS")&lt;/script&gt;');
    });
  });

  describe('setSecureChildren', () => {
    test('should clear and append single child', () => {
      const parent = document.createElement('div');
      parent.innerHTML = '<span>Old</span>';

      const newChild = document.createElement('p');
      newChild.textContent = 'New';

      setSecureChildren(parent, newChild);

      expect(parent.children.length).toBe(1);
      expect(parent.children[0].tagName).toBe('P');
      expect(parent.children[0].textContent).toBe('New');
    });

    test('should clear and append multiple children', () => {
      const parent = document.createElement('div');
      parent.innerHTML = '<span>Old</span>';

      const child1 = document.createElement('p');
      child1.textContent = 'First';
      const child2 = document.createElement('span');
      child2.textContent = 'Second';

      setSecureChildren(parent, [child1, child2]);

      expect(parent.children.length).toBe(2);
      expect(parent.children[0].textContent).toBe('First');
      expect(parent.children[1].textContent).toBe('Second');
    });

    test('should handle null parent gracefully', () => {
      expect(() => setSecureChildren(null, document.createElement('div'))).not.toThrow();
    });

    test('should ignore non-element children', () => {
      const parent = document.createElement('div');
      const validChild = document.createElement('span');

      setSecureChildren(parent, [validChild, 'string', null, undefined]);

      expect(parent.children.length).toBe(1);
      expect(parent.children[0].tagName).toBe('SPAN');
    });
  });

  describe('createTagElement', () => {
    test('should create tag element with text', () => {
      const tag = createTagElement('JavaScript');
      expect(tag.tagName).toBe('SPAN');
      expect(tag.className).toBe('tag');
      expect(tag.textContent).toBe('JavaScript');
    });

    test('should escape malicious tag text', () => {
      const tag = createTagElement('<script>alert("XSS")</script>');
      expect(tag.innerHTML).toBe('&lt;script&gt;alert("XSS")&lt;/script&gt;');
    });
  });
});

describe('DOM Helpers - Utility Functions', () => {
  describe('formatDate', () => {
    test('should format date string correctly', () => {
      const dateStr = '2024-01-15T10:30:00Z';
      const formatted = formatDate(dateStr);
      expect(formatted).toMatch(/2024\/01\/15/);
    });

    test('should handle invalid date gracefully', () => {
      expect(formatDate('invalid-date')).toBe('Invalid Date');
    });

    test('should handle null/undefined', () => {
      expect(formatDate(null)).toBe('Invalid Date');
      expect(formatDate(undefined)).toBe('Invalid Date');
    });
  });

  describe('truncateText', () => {
    test('should truncate long text', () => {
      const longText = 'This is a very long text that should be truncated';
      const result = truncateText(longText, 20);
      expect(result).toBe('This is a very long...');
      expect(result.length).toBe(23); // 20 + '...'
    });

    test('should not truncate short text', () => {
      const shortText = 'Short';
      expect(truncateText(shortText, 20)).toBe('Short');
    });

    test('should handle edge cases', () => {
      expect(truncateText('', 10)).toBe('');
      expect(truncateText(null, 10)).toBe('');
      expect(truncateText(undefined, 10)).toBe('');
    });

    test('should handle exact length', () => {
      const text = 'Exactly20Characters!';
      expect(truncateText(text, 20)).toBe(text);
    });
  });
});
