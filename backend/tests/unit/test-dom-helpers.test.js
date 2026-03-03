/**
 * @fileoverview dom-helpers.js（ESM版）ユニットテスト
 *
 * webui/src/utils/dom-helpers.js の主要DOM操作関数をテスト。
 * ESMモジュールをfs.readFileSync + evalで読み込み、
 * window.DOMHelpers / window.MKSApp.DOM グローバルを経由して関数を検証する。
 * jsdom環境（Jest標準）での動作を確認。
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

// dom-helpers.js を読み込み、import文を除去してeval
const domHelpersPath = path.join(
  __dirname,
  '../../../webui/src/utils/dom-helpers.js'
);
let domHelpersCode = fs.readFileSync(domHelpersPath, 'utf8');

// ESM import文を除去
domHelpersCode = domHelpersCode.replace(
  /^import\s+.*?;?\s*$/gm,
  '// [import removed for test]'
);

// export function/const/let/var/async を export なしに変換
domHelpersCode = domHelpersCode.replace(
  /^export\s+(?=function|async\s+function|class|const|let|var)/gm,
  ''
);
// export default を削除
domHelpersCode = domHelpersCode.replace(/^export\s+default\s+/gm, '');
// export { ... } ブロックを削除
domHelpersCode = domHelpersCode.replace(
  /^export\s*\{[^}]*\}\s*;?\s*$/gm,
  '// [export block removed]'
);

// logger参照を global.logger に変換
domHelpersCode = domHelpersCode.replace(
  /\blogger\.info\b/g,
  'global.logger.info'
);

eval(domHelpersCode);

// ----------------------------------------------------------------
// テスト: escapeHtml
// ----------------------------------------------------------------

describe('escapeHtml', () => {
  test('< を &lt; にエスケープする', () => {
    expect(escapeHtml('<')).toBe('&lt;');
  });

  test('> を &gt; にエスケープする', () => {
    expect(escapeHtml('>')).toBe('&gt;');
  });

  test('& を &amp; にエスケープする', () => {
    expect(escapeHtml('&')).toBe('&amp;');
  });

  test('" を &quot; にエスケープする', () => {
    expect(escapeHtml('"')).toBe('&quot;');
  });

  test("' を &#039; にエスケープする", () => {
    expect(escapeHtml("'")).toBe('&#039;');
  });

  test('XSS攻撃文字列を完全にエスケープする', () => {
    const input = '<script>alert("XSS")</script>';
    const result = escapeHtml(input);
    expect(result).toBe('&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;');
    expect(result).not.toContain('<script>');
  });

  test('nullを渡すと空文字列を返す', () => {
    expect(escapeHtml(null)).toBe('');
  });

  test('undefinedを渡すと空文字列を返す', () => {
    expect(escapeHtml(undefined)).toBe('');
  });

  test('数値を渡すと文字列変換してエスケープする', () => {
    expect(escapeHtml(123)).toBe('123');
    expect(escapeHtml(0)).toBe('0');
  });

  test('通常テキストはそのまま返す', () => {
    expect(escapeHtml('Hello World')).toBe('Hello World');
  });

  test('混在コンテンツを正しくエスケープする', () => {
    const input = 'Hello <b>World</b> & "Friends"';
    const expected = 'Hello &lt;b&gt;World&lt;/b&gt; &amp; &quot;Friends&quot;';
    expect(escapeHtml(input)).toBe(expected);
  });
});

// ----------------------------------------------------------------
// テスト: createSecureElement
// ----------------------------------------------------------------

describe('createSecureElement', () => {
  test('指定したタグ名で要素を作成する', () => {
    const el = createSecureElement('div');
    expect(el.tagName).toBe('DIV');
  });

  test('className を設定する', () => {
    const el = createSecureElement('span', { className: 'test-class' });
    expect(el.className).toBe('test-class');
  });

  test('textContent を安全に設定する（XSS不可）', () => {
    const el = createSecureElement('div', {
      textContent: '<script>alert("XSS")</script>'
    });
    // textContentはHTMLとして解釈されないため、innerHTML はエスケープ済みになる
    expect(el.innerHTML).toContain('&lt;script&gt;');
    expect(el.textContent).toBe('<script>alert("XSS")</script>');
  });

  test('attributes を setAttribute で設定する', () => {
    const el = createSecureElement('a', {
      attributes: {
        href: 'https://example.com',
        target: '_blank'
      }
    });
    expect(el.getAttribute('href')).toBe('https://example.com');
    expect(el.getAttribute('target')).toBe('_blank');
  });

  test('style オブジェクトを設定する', () => {
    const el = createSecureElement('div', {
      style: {
        color: 'red',
        fontSize: '16px'
      }
    });
    expect(el.style.color).toBe('red');
    expect(el.style.fontSize).toBe('16px');
  });

  test('children 配列を子要素として追加する', () => {
    const child1 = document.createElement('span');
    child1.textContent = 'Child1';
    const child2 = document.createElement('p');
    child2.textContent = 'Child2';

    const el = createSecureElement('div', {
      children: [child1, child2]
    });
    expect(el.children.length).toBe(2);
    expect(el.children[0].textContent).toBe('Child1');
    expect(el.children[1].textContent).toBe('Child2');
  });

  test('children に非HTMLElement が含まれていても無視される', () => {
    const child = document.createElement('span');
    const el = createSecureElement('div', {
      children: [child, 'string', null, 42]
    });
    expect(el.children.length).toBe(1);
  });

  test('オプションなしでも要素を作成できる', () => {
    const el = createSecureElement('p');
    expect(el.tagName).toBe('P');
    expect(el.textContent).toBe('');
  });
});

// ----------------------------------------------------------------
// テスト: setSecureChildren
// ----------------------------------------------------------------

describe('setSecureChildren', () => {
  test('既存の子要素をクリアして新しい単一子要素を追加する', () => {
    const parent = document.createElement('div');
    parent.innerHTML = '<span>Old</span>';

    const newChild = document.createElement('p');
    newChild.textContent = 'New';

    setSecureChildren(parent, newChild);
    expect(parent.children.length).toBe(1);
    expect(parent.children[0].tagName).toBe('P');
    expect(parent.children[0].textContent).toBe('New');
  });

  test('配列の子要素を順番に追加する', () => {
    const parent = document.createElement('div');
    const c1 = document.createElement('span');
    c1.textContent = 'A';
    const c2 = document.createElement('span');
    c2.textContent = 'B';

    setSecureChildren(parent, [c1, c2]);
    expect(parent.children.length).toBe(2);
    expect(parent.children[0].textContent).toBe('A');
    expect(parent.children[1].textContent).toBe('B');
  });

  test('nullの親要素でクラッシュしない', () => {
    expect(() => setSecureChildren(null, document.createElement('div'))).not.toThrow();
  });

  test('配列中の非HTMLElement は無視される', () => {
    const parent = document.createElement('div');
    const valid = document.createElement('span');

    setSecureChildren(parent, [valid, 'text-node', null, undefined]);
    expect(parent.children.length).toBe(1);
  });
});

// ----------------------------------------------------------------
// テスト: createTableRow
// ----------------------------------------------------------------

describe('createTableRow', () => {
  test('デフォルトはtd要素のtr行を生成する', () => {
    const row = createTableRow(['A', 'B', 'C']);
    expect(row.tagName).toBe('TR');
    expect(row.children.length).toBe(3);
    expect(row.children[0].tagName).toBe('TD');
    expect(row.children[0].textContent).toBe('A');
  });

  test('isHeader=true でth要素のtr行を生成する', () => {
    const row = createTableRow(['Name', 'Age'], true);
    expect(row.children[0].tagName).toBe('TH');
    expect(row.children[1].tagName).toBe('TH');
  });

  test('セルの文字列コンテンツが正しく設定される', () => {
    const row = createTableRow(['Hello', 'World']);
    expect(row.children[0].textContent).toBe('Hello');
    expect(row.children[1].textContent).toBe('World');
  });

  test('空の配列で空のtr行を生成する', () => {
    const row = createTableRow([]);
    expect(row.tagName).toBe('TR');
    expect(row.children.length).toBe(0);
  });

  test('セルのテキストはXSSエスケープされる（textContent使用）', () => {
    const row = createTableRow(['<b>bold</b>']);
    expect(row.children[0].innerHTML).toContain('&lt;b&gt;');
  });
});

// ----------------------------------------------------------------
// テスト: createTableRowWithHTML
// ----------------------------------------------------------------

describe('createTableRowWithHTML', () => {
  test('文字列セルをtextContentで設定する', () => {
    const row = createTableRowWithHTML(['Cell1', 'Cell2']);
    expect(row.children[0].textContent).toBe('Cell1');
    expect(row.children[1].textContent).toBe('Cell2');
  });

  test('HTMLElement をappendChildで追加する', () => {
    const span = document.createElement('span');
    span.textContent = 'InnerSpan';
    const row = createTableRowWithHTML([span]);
    expect(row.children[0].querySelector('span')).not.toBeNull();
    expect(row.children[0].querySelector('span').textContent).toBe('InnerSpan');
  });

  test('文字列とHTMLElementの混在セルを正しく処理する', () => {
    const el = document.createElement('strong');
    el.textContent = 'Strong';
    const row = createTableRowWithHTML(['PlainText', el]);
    expect(row.children[0].textContent).toBe('PlainText');
    expect(row.children[1].querySelector('strong').textContent).toBe('Strong');
  });

  test('isHeader=true でth要素を使用する', () => {
    const row = createTableRowWithHTML(['Header'], true);
    expect(row.children[0].tagName).toBe('TH');
  });

  test('nullや未定義のセルはテキストなしのtdを生成する', () => {
    const row = createTableRowWithHTML([null]);
    expect(row.children[0].textContent).toBe('');
  });
});

// ----------------------------------------------------------------
// テスト: createTagElement
// ----------------------------------------------------------------

describe('createTagElement', () => {
  test('span.tag 要素を生成する', () => {
    const tag = createTagElement('JavaScript');
    expect(tag.tagName).toBe('SPAN');
    expect(tag.className).toBe('tag');
    expect(tag.textContent).toBe('JavaScript');
  });

  test('XSSインジェクションが不可能（textContent使用）', () => {
    const tag = createTagElement('<script>alert(1)</script>');
    expect(tag.innerHTML).toContain('&lt;script&gt;');
  });
});

// ----------------------------------------------------------------
// テスト: createPillElement
// ----------------------------------------------------------------

describe('createPillElement', () => {
  test('div.pill 要素を生成する', () => {
    const pill = createPillElement('アクティブ');
    expect(pill.tagName).toBe('DIV');
    expect(pill.className).toBe('pill');
    expect(pill.textContent).toBe('アクティブ');
  });
});

// ----------------------------------------------------------------
// テスト: createStatusElement
// ----------------------------------------------------------------

describe('createStatusElement', () => {
  test('div.status-item 要素を生成する', () => {
    const el = createStatusElement('正常', 'active');
    expect(el.tagName).toBe('DIV');
    expect(el.className).toBe('status-item');
  });

  test('ステータスドットと テキストの2つの子要素を持つ', () => {
    const el = createStatusElement('正常', 'is-ok');
    expect(el.children.length).toBe(2);
    expect(el.children[0].className).toContain('status-dot');
    expect(el.children[0].className).toContain('is-ok');
    expect(el.children[1].textContent).toBe('正常');
  });

  test('デフォルトのステータスクラスは active', () => {
    const el = createStatusElement('テスト');
    expect(el.children[0].className).toContain('active');
  });
});

// ----------------------------------------------------------------
// テスト: truncateText
// ----------------------------------------------------------------

describe('truncateText', () => {
  test('最大文字数以下はそのまま返す', () => {
    expect(truncateText('短い', 10)).toBe('短い');
  });

  test('最大文字数を超えると...を付加して切り詰める', () => {
    const result = truncateText('This is a very long text', 10);
    expect(result).toContain('...');
    expect(result.length).toBeLessThanOrEqual(13); // 10 + '...' = 13
  });

  test('ちょうど最大文字数は切り詰めない', () => {
    expect(truncateText('1234567890', 10)).toBe('1234567890');
  });

  test('nullを渡すと空文字列を返す', () => {
    expect(truncateText(null, 10)).toBe('');
  });

  test('undefinedを渡すと空文字列を返す', () => {
    expect(truncateText(undefined, 10)).toBe('');
  });

  test('空文字列を渡すと空文字列を返す', () => {
    expect(truncateText('', 10)).toBe('');
  });
});

// ----------------------------------------------------------------
// テスト: createEmptyMessage / createErrorMessage
// ----------------------------------------------------------------

describe('createEmptyMessage', () => {
  test('メッセージテキストを持つ p 要素を返す', () => {
    const el = createEmptyMessage('データがありません');
    expect(el.tagName).toBe('P');
    expect(el.textContent).toBe('データがありません');
  });
});

describe('createErrorMessage', () => {
  test('エラーメッセージを持つ p 要素を返す', () => {
    const el = createErrorMessage('読み込みに失敗しました');
    expect(el.tagName).toBe('P');
    expect(el.textContent).toBe('読み込みに失敗しました');
  });

  test('エラー色スタイルが設定される', () => {
    const el = createErrorMessage('エラー');
    expect(el.style.color).toBe('var(--danger)');
  });
});

// ----------------------------------------------------------------
// テスト: createLinkElement
// ----------------------------------------------------------------

describe('createLinkElement', () => {
  test('href と テキストを持つ a 要素を返す', () => {
    const el = createLinkElement('https://example.com', 'リンクテキスト');
    expect(el.tagName).toBe('A');
    expect(el.getAttribute('href')).toBe('https://example.com');
    expect(el.textContent).toBe('リンクテキスト');
  });

  test('オプションのクラス名が設定される', () => {
    const el = createLinkElement('/path', 'クリック', { className: 'nav-link' });
    expect(el.className).toBe('nav-link');
  });

  test('追加属性が setAttribute で設定される', () => {
    const el = createLinkElement('https://example.com', 'Open', {
      attributes: { target: '_blank', rel: 'noopener' }
    });
    expect(el.getAttribute('target')).toBe('_blank');
    expect(el.getAttribute('rel')).toBe('noopener');
  });
});

// ----------------------------------------------------------------
// テスト: window.DOMHelpers / window.MKSApp.DOM グローバル公開確認
// ----------------------------------------------------------------

describe('DOMHelpers グローバル公開', () => {
  test('window.DOMHelpers が定義されている', () => {
    expect(window.DOMHelpers).toBeDefined();
  });

  test('window.MKSApp.DOM が定義されている', () => {
    expect(window.MKSApp).toBeDefined();
    expect(window.MKSApp.DOM).toBeDefined();
  });

  test('window.escapeHtml が関数である', () => {
    expect(typeof window.escapeHtml).toBe('function');
  });

  test('window.createSecureElement が関数である', () => {
    expect(typeof window.createSecureElement).toBe('function');
  });

  test('window.setSecureChildren が関数である', () => {
    expect(typeof window.setSecureChildren).toBe('function');
  });

  test('window.truncateText が関数である', () => {
    expect(typeof window.truncateText).toBe('function');
  });

  test('window.createTableRow が関数である', () => {
    expect(typeof window.createTableRow).toBe('function');
  });

  test('window.createTableRowWithHTML が関数である', () => {
    expect(typeof window.createTableRowWithHTML).toBe('function');
  });

  test('window.DOMHelpers.Components が定義されている', () => {
    expect(window.DOMHelpers.Components).toBeDefined();
  });

  test('window.DOMHelpers.Messages が定義されている', () => {
    expect(window.DOMHelpers.Messages).toBeDefined();
  });
});
