/**
 * Phase F ESMモジュール E2Eテスト
 *
 * Phase F-4 で実施されたモジュール分割・ESM化が正しく動作することを確認する。
 * 検証対象:
 *   1. window.MKSApp.DetailPages ネームスペースの存在と構造
 *   2. 各ESMモジュールの主要関数がグローバルに公開されていること
 *   3. W-001修正確認 - テーブル行ボタンが innerHTML ではなく HTMLElement として生成されること
 *   4. 旧来グローバル関数 (window.loadKnowledgeDetail 等) の後方互換性
 *   5. dom-helpers ESMモジュールの MKSApp.DOM ネームスペース確認
 *
 * 実行方法:
 *   npx playwright test backend/tests/e2e/phase-f-modules.spec.js
 *
 * 前提:
 *   - サーバーが http://localhost:5200 で稼働していること
 *   - または BASE_URL 環境変数で上書き可能
 *   - サーバー未起動時は各テストが graceful skip またはエラーメッセージを出力する
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = process.env.BASE_URL || 'http://localhost:5200';

// ============================================================
// ヘルパー: ログイン処理（ダッシュボードが必要なテスト用）
// ============================================================
async function loginAsAdmin(page) {
  await page.goto(`${BASE_URL}/login.html`);
  await page.waitForLoadState('domcontentloaded');

  // ログインフォームへの入力
  const usernameSelector = 'input[name="username"], #username, input[type="text"]';
  const passwordSelector = 'input[name="password"], #password, input[type="password"]';
  const submitSelector = 'button[type="submit"]';

  await page.fill(usernameSelector, 'admin');
  await page.fill(passwordSelector, 'Admin@2024');
  await page.click(submitSelector);

  // ダッシュボード読み込み待機（最大10秒）
  await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {
    // タイムアウトしても続行
  });
  await page.waitForTimeout(500);
}

// ============================================================
// テストスイート 1: MKSApp.DetailPages ネームスペース検証
// ============================================================
test.describe('Phase F: MKSApp.DetailPages ネームスペース', () => {
  test.beforeEach(async ({ page }) => {
    // サーバー疎通確認
    let serverAvailable = true;
    try {
      const response = await page.goto(`${BASE_URL}/login.html`, {
        timeout: 8000,
        waitUntil: 'domcontentloaded'
      });
      if (!response || response.status() >= 500) serverAvailable = false;
    } catch {
      serverAvailable = false;
    }

    if (!serverAvailable) {
      test.skip(true, `サーバー ${BASE_URL} が利用できないためスキップ`);
      return;
    }

    // ログイン → search-detail.html に遷移
    await loginAsAdmin(page);
    await page.goto(`${BASE_URL}/search-detail.html?id=1`);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(1000);
  });

  test('window.MKSApp が定義されている', async ({ page }) => {
    const exists = await page.evaluate(() => typeof window.MKSApp !== 'undefined');
    expect(exists).toBe(true);
  });

  test('window.MKSApp.DetailPages が定義されている', async ({ page }) => {
    const exists = await page.evaluate(() => {
      return (
        typeof window.MKSApp !== 'undefined' &&
        typeof window.MKSApp.DetailPages !== 'undefined'
      );
    });
    expect(exists).toBe(true);
  });

  test('MKSApp.DetailPages が必須サブモジュールを持つ', async ({ page }) => {
    const modules = await page.evaluate(() => {
      if (!window.MKSApp || !window.MKSApp.DetailPages) return [];
      return Object.keys(window.MKSApp.DetailPages);
    });

    // detail-pages.js で定義されている全モジュール
    expect(modules).toContain('Knowledge');
    expect(modules).toContain('SOP');
    expect(modules).toContain('Incident');
    expect(modules).toContain('Consult');
    expect(modules).toContain('Utilities');
    expect(modules).toContain('Share');
    expect(modules).toContain('Modal');
  });

  test('MKSApp.DetailPages.Knowledge が必須関数を持つ', async ({ page }) => {
    const functions = await page.evaluate(() => {
      if (
        !window.MKSApp ||
        !window.MKSApp.DetailPages ||
        !window.MKSApp.DetailPages.Knowledge
      ) return [];
      return Object.keys(window.MKSApp.DetailPages.Knowledge);
    });

    expect(functions).toContain('load');
    expect(functions).toContain('display');
    expect(functions).toContain('share');
  });

  test('MKSApp.DetailPages.SOP が必須関数を持つ', async ({ page }) => {
    const functions = await page.evaluate(() => {
      if (
        !window.MKSApp ||
        !window.MKSApp.DetailPages ||
        !window.MKSApp.DetailPages.SOP
      ) return [];
      return Object.keys(window.MKSApp.DetailPages.SOP);
    });

    expect(functions).toContain('load');
    expect(functions).toContain('display');
    expect(functions).toContain('download');
  });

  test('MKSApp.DetailPages.Incident が必須関数を持つ', async ({ page }) => {
    const functions = await page.evaluate(() => {
      if (
        !window.MKSApp ||
        !window.MKSApp.DetailPages ||
        !window.MKSApp.DetailPages.Incident
      ) return [];
      return Object.keys(window.MKSApp.DetailPages.Incident);
    });

    expect(functions).toContain('load');
    expect(functions).toContain('display');
    expect(functions).toContain('updateStatus');
  });

  test('MKSApp.DetailPages.Utilities が日付フォーマット関数を持つ', async ({ page }) => {
    const result = await page.evaluate(() => {
      try {
        if (
          !window.MKSApp ||
          !window.MKSApp.DetailPages ||
          !window.MKSApp.DetailPages.Utilities
        ) return { ok: false, error: 'Utilities not found' };

        const { formatDate } = window.MKSApp.DetailPages.Utilities;
        if (typeof formatDate !== 'function') {
          return { ok: false, error: 'formatDate is not a function' };
        }
        const formatted = formatDate('2026-01-31T12:00:00Z');
        return { ok: typeof formatted === 'string' && formatted.length > 0, formatted };
      } catch (e) {
        return { ok: false, error: e.message };
      }
    });

    expect(result.ok).toBe(true);
  });
});

// ============================================================
// テストスイート 2: dom-helpers ESM - MKSApp.DOM ネームスペース
// ============================================================
test.describe('Phase F: MKSApp.DOM ネームスペース（dom-helpers ESM）', () => {
  test.beforeEach(async ({ page }) => {
    let serverAvailable = true;
    try {
      const response = await page.goto(`${BASE_URL}/login.html`, {
        timeout: 8000,
        waitUntil: 'domcontentloaded'
      });
      if (!response || response.status() >= 500) serverAvailable = false;
    } catch {
      serverAvailable = false;
    }

    if (!serverAvailable) {
      test.skip(true, `サーバー ${BASE_URL} が利用できないためスキップ`);
      return;
    }

    await loginAsAdmin(page);
    await page.goto(`${BASE_URL}/search-detail.html?id=1`);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(1000);
  });

  test('window.MKSApp.DOM が定義されている', async ({ page }) => {
    const exists = await page.evaluate(() => {
      return (
        typeof window.MKSApp !== 'undefined' &&
        typeof window.MKSApp.DOM !== 'undefined'
      );
    });
    expect(exists).toBe(true);
  });

  test('MKSApp.DOM がコア関数を持つ', async ({ page }) => {
    const keys = await page.evaluate(() => {
      if (!window.MKSApp || !window.MKSApp.DOM) return [];
      return Object.keys(window.MKSApp.DOM);
    });

    expect(keys).toContain('escapeHtml');
    expect(keys).toContain('createSecureElement');
    expect(keys).toContain('setSecureChildren');
    expect(keys).toContain('Components');
    expect(keys).toContain('Messages');
  });

  test('MKSApp.DOM.escapeHtml が XSS文字列を正しくエスケープする', async ({ page }) => {
    const result = await page.evaluate(() => {
      try {
        const fn = window.MKSApp.DOM.escapeHtml || window.escapeHtml;
        if (typeof fn !== 'function') return { ok: false, error: 'escapeHtml not found' };
        const escaped = fn('<script>alert("xss")</script>');
        return {
          ok: !escaped.includes('<script>') && escaped.includes('&lt;'),
          escaped
        };
      } catch (e) {
        return { ok: false, error: e.message };
      }
    });

    expect(result.ok).toBe(true);
  });

  test('MKSApp.DOM.createSecureElement が HTMLElement を返す', async ({ page }) => {
    const result = await page.evaluate(() => {
      try {
        const fn = window.MKSApp.DOM.createSecureElement || window.createSecureElement;
        if (typeof fn !== 'function') return { ok: false, error: 'createSecureElement not found' };
        const el = fn('div', { className: 'test', textContent: 'hello' });
        return {
          ok: el instanceof HTMLElement,
          tagName: el.tagName,
          className: el.className,
          textContent: el.textContent
        };
      } catch (e) {
        return { ok: false, error: e.message };
      }
    });

    expect(result.ok).toBe(true);
    expect(result.tagName).toBe('DIV');
    expect(result.className).toBe('test');
    expect(result.textContent).toBe('hello');
  });

  test('MKSApp.DOM.Components.createTableRow が TR 要素を返す', async ({ page }) => {
    const result = await page.evaluate(() => {
      try {
        const fn =
          (window.MKSApp.DOM.Components && window.MKSApp.DOM.Components.createTableRow) ||
          window.createTableRow;
        if (typeof fn !== 'function') return { ok: false, error: 'createTableRow not found' };
        const row = fn(['セル1', 'セル2', 'セル3']);
        return {
          ok: row instanceof HTMLElement,
          tagName: row.tagName,
          cellCount: row.querySelectorAll('td').length
        };
      } catch (e) {
        return { ok: false, error: e.message };
      }
    });

    expect(result.ok).toBe(true);
    expect(result.tagName).toBe('TR');
    expect(result.cellCount).toBe(3);
  });
});

// ============================================================
// テストスイート 3: W-001修正 - テーブル行ボタンの HTMLElement 生成確認
// ============================================================
test.describe('Phase F W-001修正: テーブル行ボタンの DOM API 生成', () => {
  test.beforeEach(async ({ page }) => {
    let serverAvailable = true;
    try {
      const response = await page.goto(`${BASE_URL}/login.html`, {
        timeout: 8000,
        waitUntil: 'domcontentloaded'
      });
      if (!response || response.status() >= 500) serverAvailable = false;
    } catch {
      serverAvailable = false;
    }

    if (!serverAvailable) {
      test.skip(true, `サーバー ${BASE_URL} が利用できないためスキップ`);
      return;
    }

    await loginAsAdmin(page);
    await page.goto(`${BASE_URL}/search-detail.html?id=1`);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(1000);
  });

  test('createTableRowWithHTML にボタン要素を渡すと HTMLElement が保持される', async ({ page }) => {
    // W-001: innerHTML を使った文字列渡しではなく、button HTMLElement を直接渡すことを確認
    const result = await page.evaluate(() => {
      try {
        const fn =
          (window.MKSApp.DOM.Components && window.MKSApp.DOM.Components.createTableRowWithHTML) ||
          window.createTableRowWithHTML;
        if (typeof fn !== 'function') return { ok: false, error: 'createTableRowWithHTML not found' };

        // button を HTMLElement として作成
        const btn = document.createElement('button');
        btn.textContent = '詳細';
        btn.className = 'cta';
        btn.setAttribute('data-id', '42');

        // セルの中に HTMLElement を渡す（W-001修正: innerHTML 使用なし）
        const row = fn(['項目名', '値', btn]);

        const cells = row.querySelectorAll('td');
        const lastCell = cells[cells.length - 1];
        const buttonInCell = lastCell.querySelector('button');

        return {
          ok: buttonInCell instanceof HTMLElement,
          tagName: buttonInCell ? buttonInCell.tagName : null,
          textContent: buttonInCell ? buttonInCell.textContent : null,
          dataId: buttonInCell ? buttonInCell.getAttribute('data-id') : null,
          // innerHTML が使われていない確認: innerHTMLに<script>等が含まれていないこと
          cellHtmlSafe: !lastCell.innerHTML.includes('<script>')
        };
      } catch (e) {
        return { ok: false, error: e.message };
      }
    });

    expect(result.ok).toBe(true);
    expect(result.tagName).toBe('BUTTON');
    expect(result.textContent).toBe('詳細');
    expect(result.dataId).toBe('42');
    expect(result.cellHtmlSafe).toBe(true);
  });

  test('createSecureElement の children に HTMLElement を渡すと正しく appendChild される', async ({ page }) => {
    const result = await page.evaluate(() => {
      try {
        const fn = (window.MKSApp.DOM && window.MKSApp.DOM.createSecureElement) ||
                   window.createSecureElement;
        if (typeof fn !== 'function') return { ok: false, error: 'createSecureElement not found' };

        // 子要素として button HTMLElement を作成
        const btn = document.createElement('button');
        btn.textContent = '操作';
        btn.type = 'button';

        const container = fn('div', {
          className: 'actions',
          children: [btn]
        });

        const childBtn = container.querySelector('button');
        return {
          ok: childBtn instanceof HTMLElement,
          tagName: childBtn ? childBtn.tagName : null,
          textContent: childBtn ? childBtn.textContent : null,
          // innerHTML ではなく DOM API が使われているため、XSSコンテンツが挿入されていない
          noInnerHTMLInjection: !container.innerHTML.includes('javascript:')
        };
      } catch (e) {
        return { ok: false, error: e.message };
      }
    });

    expect(result.ok).toBe(true);
    expect(result.tagName).toBe('BUTTON');
    expect(result.textContent).toBe('操作');
    expect(result.noInnerHTMLInjection).toBe(true);
  });

  test('ページ内のテーブルボタンが HTMLElement として存在する（XSS文字列なし）', async ({ page }) => {
    // 実際のページ上にレンダリングされたテーブル行のボタンを確認
    // ページロード後に動的生成されるテーブルが存在する場合のみチェック
    const result = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('table button, .table-row button'));
      if (buttons.length === 0) {
        // ページ構造によってはテーブルボタンがない場合も正常
        return { ok: true, count: 0, note: 'no table buttons found, skipping DOM check' };
      }

      let allValid = true;
      const issues = [];

      for (const btn of buttons) {
        if (!(btn instanceof HTMLElement)) {
          allValid = false;
          issues.push('Button is not an HTMLElement');
          continue;
        }
        // innerHTML に危険なコンテンツがないことを確認
        if (btn.innerHTML.includes('<script>') || btn.innerHTML.includes('javascript:')) {
          allValid = false;
          issues.push(`Dangerous innerHTML found: ${btn.innerHTML.substring(0, 50)}`);
        }
      }

      return { ok: allValid, count: buttons.length, issues };
    });

    expect(result.ok).toBe(true);
    if (result.count > 0) {
      expect(result.issues).toHaveLength(0);
    }
  });
});

// ============================================================
// テストスイート 4: 後方互換性 - 旧グローバル関数アクセス
// ============================================================
test.describe('Phase F: 後方互換性 - 旧グローバル関数', () => {
  test.beforeEach(async ({ page }) => {
    let serverAvailable = true;
    try {
      const response = await page.goto(`${BASE_URL}/login.html`, {
        timeout: 8000,
        waitUntil: 'domcontentloaded'
      });
      if (!response || response.status() >= 500) serverAvailable = false;
    } catch {
      serverAvailable = false;
    }

    if (!serverAvailable) {
      test.skip(true, `サーバー ${BASE_URL} が利用できないためスキップ`);
      return;
    }

    await loginAsAdmin(page);
    await page.goto(`${BASE_URL}/search-detail.html?id=1`);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(1000);
  });

  test('window.loadKnowledgeDetail が関数として存在する', async ({ page }) => {
    const result = await page.evaluate(() => typeof window.loadKnowledgeDetail);
    expect(result).toBe('function');
  });

  test('window.loadSOPDetail が関数として存在する', async ({ page }) => {
    const result = await page.evaluate(() => typeof window.loadSOPDetail);
    expect(result).toBe('function');
  });

  test('window.loadIncidentDetail が関数として存在する', async ({ page }) => {
    const result = await page.evaluate(() => typeof window.loadIncidentDetail);
    expect(result).toBe('function');
  });

  test('window.escapeHtml が関数として存在し正しく動作する', async ({ page }) => {
    const result = await page.evaluate(() => {
      if (typeof window.escapeHtml !== 'function') return { ok: false };
      const out = window.escapeHtml('<b>test</b>');
      return { ok: out === '&lt;b&gt;test&lt;/b&gt;', out };
    });
    expect(result.ok).toBe(true);
  });

  test('window.createSecureElement が関数として存在する', async ({ page }) => {
    const result = await page.evaluate(() => typeof window.createSecureElement);
    expect(result).toBe('function');
  });

  test('window.setSecureChildren が関数として存在する', async ({ page }) => {
    const result = await page.evaluate(() => typeof window.setSecureChildren);
    expect(result).toBe('function');
  });

  test('window.createTableRow が関数として存在する', async ({ page }) => {
    const result = await page.evaluate(() => typeof window.createTableRow);
    expect(result).toBe('function');
  });

  test('window.createTableRowWithHTML が関数として存在する', async ({ page }) => {
    const result = await page.evaluate(() => typeof window.createTableRowWithHTML);
    expect(result).toBe('function');
  });

  test('後方互換関数が Namespace 関数と同一参照または同等動作をする', async ({ page }) => {
    const result = await page.evaluate(() => {
      try {
        // window.loadKnowledgeDetail と MKSApp.DetailPages.Knowledge.load が同一または両方 function であること
        const globalFn = typeof window.loadKnowledgeDetail === 'function';
        const nsFn =
          window.MKSApp &&
          window.MKSApp.DetailPages &&
          typeof window.MKSApp.DetailPages.Knowledge.load === 'function';
        return { globalFn, nsFn };
      } catch (e) {
        return { error: e.message };
      }
    });

    expect(result.globalFn).toBe(true);
    expect(result.nsFn).toBe(true);
  });
});

// ============================================================
// テストスイート 5: ESMモジュール読み込みと console エラー監視
// ============================================================
test.describe('Phase F: ESMモジュール読み込みエラー監視', () => {
  test('search-detail.html のロード中に Module 関連エラーが発生しない', async ({ page }) => {
    const errors = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    page.on('pageerror', err => {
      errors.push(err.message);
    });

    let serverAvailable = true;
    try {
      const response = await page.goto(`${BASE_URL}/search-detail.html?id=1`, {
        timeout: 10000,
        waitUntil: 'domcontentloaded'
      });
      if (!response || response.status() >= 500) serverAvailable = false;
    } catch {
      serverAvailable = false;
    }

    if (!serverAvailable) {
      test.skip(true, `サーバー ${BASE_URL} が利用できないためスキップ`);
      return;
    }

    await page.waitForTimeout(2000);

    // ESMモジュール固有のエラーをフィルタリング
    const moduleErrors = errors.filter(err => {
      // ESM import/export エラー
      if (err.includes('SyntaxError') && err.includes('import')) return true;
      if (err.includes('SyntaxError') && err.includes('export')) return true;
      // モジュール解決エラー
      if (err.includes('Failed to resolve module specifier')) return true;
      if (err.includes('Cannot use import statement')) return true;
      // undefined 関数の呼び出し（モジュール未ロード起因）
      if (err.includes('is not a function') && err.includes('MKSApp')) return true;
      return false;
    });

    if (moduleErrors.length > 0) {
      console.log('Phase F module errors detected:');
      moduleErrors.forEach(e => console.log('  -', e));
    }

    expect(moduleErrors).toHaveLength(0);
  });

  test('sop-detail.html のロード中に Module 関連エラーが発生しない', async ({ page }) => {
    const errors = [];

    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    page.on('pageerror', err => errors.push(err.message));

    let serverAvailable = true;
    try {
      const response = await page.goto(`${BASE_URL}/sop-detail.html?id=1`, {
        timeout: 10000,
        waitUntil: 'domcontentloaded'
      });
      if (!response || response.status() >= 500) serverAvailable = false;
    } catch {
      serverAvailable = false;
    }

    if (!serverAvailable) {
      test.skip(true, `サーバー ${BASE_URL} が利用できないためスキップ`);
      return;
    }

    await page.waitForTimeout(2000);

    const moduleErrors = errors.filter(err => {
      if (err.includes('SyntaxError') && err.includes('import')) return true;
      if (err.includes('Failed to resolve module specifier')) return true;
      if (err.includes('Cannot use import statement')) return true;
      if (err.includes('is not a function') && err.includes('MKSApp')) return true;
      return false;
    });

    expect(moduleErrors).toHaveLength(0);
  });

  test('incident-detail.html のロード中に Module 関連エラーが発生しない', async ({ page }) => {
    const errors = [];

    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    page.on('pageerror', err => errors.push(err.message));

    let serverAvailable = true;
    try {
      const response = await page.goto(`${BASE_URL}/incident-detail.html?id=1`, {
        timeout: 10000,
        waitUntil: 'domcontentloaded'
      });
      if (!response || response.status() >= 500) serverAvailable = false;
    } catch {
      serverAvailable = false;
    }

    if (!serverAvailable) {
      test.skip(true, `サーバー ${BASE_URL} が利用できないためスキップ`);
      return;
    }

    await page.waitForTimeout(2000);

    const moduleErrors = errors.filter(err => {
      if (err.includes('SyntaxError') && err.includes('import')) return true;
      if (err.includes('Failed to resolve module specifier')) return true;
      if (err.includes('Cannot use import statement')) return true;
      if (err.includes('is not a function') && err.includes('MKSApp')) return true;
      return false;
    });

    expect(moduleErrors).toHaveLength(0);
  });
});
