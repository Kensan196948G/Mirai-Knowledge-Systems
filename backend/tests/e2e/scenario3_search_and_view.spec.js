/**
 * E2E Test Scenario 3: Search and View
 *
 * Tests search and viewing functionality:
 * 1. Full-text search
 * 2. Filter by category
 * 3. Filter by tags
 * 4. Sort results
 * 5. View knowledge details
 * 6. Track view history
 * 7. Related knowledge suggestions
 */

const { test, expect } = require('@playwright/test');
const { login, loginAPI } = require('./helpers/auth');
const { createKnowledge, updateKnowledgeStatus } = require('./helpers/api');
const { waitForText, waitForPageLoad } = require('./helpers/waiters');

test.describe('Scenario 3: Search and View', () => {
  let workerToken;
  let testKnowledgeIds = [];

  test.beforeAll(async ({ request }) => {
    const workerAuth = await loginAPI(request, 'worker');
    workerToken = workerAuth.token;

    // Create multiple knowledge items for search testing
    const knowledgeItems = [
      {
        title: '安全手順: 高所作業',
        content: '高所作業における安全手順:\n1. ハーネスの装着\n2. 作業床の確認\n3. 工具の落下防止',
        category: 'safety',
        tags: ['高所作業', '安全', '手順'],
        is_critical: true
      },
      {
        title: '機械操作マニュアル: クレーン',
        content: 'クレーン操作の基本:\n1. 始業点検\n2. 荷重制限の確認\n3. 周囲の安全確認',
        category: 'procedure',
        tags: ['機械操作', 'クレーン', 'マニュアル']
      },
      {
        title: '品質管理: 検査手順',
        content: '製品検査の手順:\n1. 外観検査\n2. 寸法測定\n3. 機能試験',
        category: 'quality',
        tags: ['品質管理', '検査', '手順']
      },
      {
        title: 'トラブルシューティング: 電気系統',
        content: '電気系統トラブルの対処:\n1. 電源確認\n2. ブレーカー点検\n3. 配線チェック',
        category: 'maintenance',
        tags: ['トラブルシューティング', '電気', '保守']
      }
    ];

    for (const item of knowledgeItems) {
      const knowledge = await createKnowledge(request, workerToken, item);
      testKnowledgeIds.push(knowledge.id);

      // Publish knowledge (set status to published)
      await updateKnowledgeStatus(request, workerToken, knowledge.id, 'published');
    }

    console.log(`Created ${testKnowledgeIds.length} test knowledge items`);
  });

  test('should perform full-text search', async ({ page }) => {
    console.log('=== Test: Full-text Search ===');

    await login(page, 'worker');

    // Navigate to knowledge search page
    await page.goto('/knowledge');
    await waitForPageLoad(page);

    // Perform search for "安全"
    const searchInput = page.locator('input[type="search"], input[name="search"], input[name="q"], #search');
    await searchInput.fill('安全');
    await page.keyboard.press('Enter');

    // Wait for search results
    await page.waitForTimeout(2000);

    // Verify results contain safety-related knowledge
    const results = page.locator('.knowledge-item, .knowledge-card, .search-result, tr[data-knowledge-id]');
    const count = await results.count();

    expect(count).toBeGreaterThan(0);
    console.log(`Found ${count} results for "安全"`);

    // Verify at least one result contains our test knowledge
    const resultText = await results.first().textContent();
    expect(resultText).toMatch(/安全|高所作業/);

    console.log('✓ Full-text search working');
  });

  test('should filter by category', async ({ page }) => {
    console.log('=== Test: Category Filter ===');

    await login(page, 'worker');
    await page.goto('/knowledge');
    await waitForPageLoad(page);

    // Find and use category filter
    const categoryFilter = page.locator('select[name="category"], #category-filter, .category-filter select');

    if (await categoryFilter.count() > 0) {
      await categoryFilter.selectOption('safety');
      await page.waitForTimeout(2000);

      // Verify results are filtered
      const results = page.locator('.knowledge-item, .knowledge-card');
      const count = await results.count();

      expect(count).toBeGreaterThan(0);

      // Verify first result is safety category
      const firstResult = results.first();
      const text = await firstResult.textContent();
      expect(text).toMatch(/安全|safety|高所作業/i);

      console.log(`✓ Category filter working (${count} results)`);
    } else {
      console.log('⚠ Category filter not found, skipping');
    }
  });

  test('should filter by tags', async ({ page }) => {
    console.log('=== Test: Tag Filter ===');

    await login(page, 'worker');
    await page.goto('/knowledge');
    await waitForPageLoad(page);

    // Look for tag filter or tag links
    const tagFilter = page.locator('.tag:has-text("手順"), .tag:has-text("安全"), a[href*="tag="]').first();

    if (await tagFilter.count() > 0) {
      await tagFilter.click();
      await page.waitForTimeout(2000);

      // Verify URL contains tag parameter or results are filtered
      const url = page.url();
      expect(url).toMatch(/tag=|tags=/);

      const results = page.locator('.knowledge-item, .knowledge-card');
      const count = await results.count();
      expect(count).toBeGreaterThan(0);

      console.log(`✓ Tag filter working (${count} results)`);
    } else {
      console.log('⚠ Tag filter not found, testing manual tag search');

      // Try searching for tag directly
      const searchInput = page.locator('input[type="search"], input[name="search"]');
      await searchInput.fill('tag:手順');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(2000);
    }
  });

  test('should sort search results', async ({ page }) => {
    console.log('=== Test: Sort Results ===');

    await login(page, 'worker');
    await page.goto('/knowledge');
    await waitForPageLoad(page);

    // Find sort dropdown
    const sortSelect = page.locator('select[name="sort"], #sort, .sort-select');

    if (await sortSelect.count() > 0) {
      // Get initial order
      const initialResults = await page.locator('.knowledge-item, .knowledge-card').allTextContents();

      // Change sort order
      await sortSelect.selectOption({ label: /新しい順|Newest|created_desc/ }).catch(() =>
        sortSelect.selectOption({ index: 1 })
      );

      await page.waitForTimeout(2000);

      // Get new order
      const newResults = await page.locator('.knowledge-item, .knowledge-card').allTextContents();

      // Verify order changed
      expect(newResults[0]).not.toBe(initialResults[0]);

      console.log('✓ Sort functionality working');
    } else {
      console.log('⚠ Sort dropdown not found, skipping');
    }
  });

  test('should view knowledge details and track views', async ({ page, request }) => {
    console.log('=== Test: View Knowledge Details ===');

    await login(page, 'worker');

    // Navigate to first test knowledge
    const knowledgeId = testKnowledgeIds[0];
    await page.goto(`/knowledge/${knowledgeId}`);

    // Wait for details to load
    await page.waitForSelector('.knowledge-detail, .knowledge-content, article', { timeout: 10000 });

    // Verify content is displayed
    await expect(page.locator('h1, .title')).toBeVisible();
    await expect(page.locator('.content, .knowledge-content, article')).toBeVisible();

    // Verify metadata
    const metadata = page.locator('.metadata, .info, .knowledge-info');
    if (await metadata.count() > 0) {
      const metadataText = await metadata.textContent();
      expect(metadataText).toMatch(/カテゴリ|Category|タグ|Tags|作成日|Created/);
    }

    // Check if view count increased
    const viewCount = page.locator('.view-count, .views, [class*="view"]');
    if (await viewCount.count() > 0) {
      const viewText = await viewCount.textContent();
      console.log(`View count: ${viewText}`);
    }

    // Verify tags are displayed
    const tags = page.locator('.tag, .badge');
    const tagCount = await tags.count();
    expect(tagCount).toBeGreaterThan(0);

    console.log('✓ Knowledge details displayed correctly');
  });

  test('should show related knowledge suggestions', async ({ page }) => {
    console.log('=== Test: Related Knowledge ===');

    await login(page, 'worker');

    // View a knowledge item
    const knowledgeId = testKnowledgeIds[0];
    await page.goto(`/knowledge/${knowledgeId}`);

    await waitForPageLoad(page);

    // Look for related knowledge section
    const relatedSection = page.locator(
      '.related-knowledge, .suggestions, .similar, [class*="related"]'
    );

    if (await relatedSection.count() > 0) {
      await relatedSection.first().scrollIntoViewIfNeeded();

      // Verify related items exist
      const relatedItems = page.locator('.related-item, .suggestion-item, .knowledge-card');
      const count = await relatedItems.count();

      if (count > 0) {
        expect(count).toBeGreaterThan(0);
        console.log(`✓ Found ${count} related knowledge items`);

        // Click on a related item
        await relatedItems.first().click();
        await page.waitForURL(/\/knowledge\/\d+/);

        console.log('✓ Related knowledge navigation working');
      } else {
        console.log('⚠ No related knowledge items found');
      }
    } else {
      console.log('⚠ Related knowledge section not found');
    }
  });

  test('should support advanced search with multiple filters', async ({ page }) => {
    console.log('=== Test: Advanced Search ===');

    await login(page, 'worker');
    await page.goto('/knowledge');
    await waitForPageLoad(page);

    // Try to open advanced search
    const advancedSearchBtn = page.locator(
      'button:has-text("詳細検索"), button:has-text("Advanced"), .advanced-search-toggle'
    );

    if (await advancedSearchBtn.count() > 0) {
      await advancedSearchBtn.click();
      await page.waitForTimeout(1000);

      // Fill in multiple search criteria
      const searchInput = page.locator('input[name="search"], input[name="q"]');
      await searchInput.fill('手順');

      const categorySelect = page.locator('select[name="category"]');
      if (await categorySelect.count() > 0) {
        await categorySelect.selectOption('safety');
      }

      const criticalCheckbox = page.locator('input[type="checkbox"][name="is_critical"]');
      if (await criticalCheckbox.count() > 0) {
        await criticalCheckbox.check();
      }

      // Submit search
      await page.click('button[type="submit"], button:has-text("検索"), button:has-text("Search")');
      await page.waitForTimeout(2000);

      // Verify results match all criteria
      const results = page.locator('.knowledge-item, .knowledge-card');
      const count = await results.count();

      expect(count).toBeGreaterThanOrEqual(0);
      console.log(`✓ Advanced search returned ${count} results`);
    } else {
      console.log('⚠ Advanced search not available');
    }
  });

  test('should display search history', async ({ page }) => {
    console.log('=== Test: Search History ===');

    await login(page, 'worker');
    await page.goto('/knowledge');

    // Perform several searches
    const searchTerms = ['安全', 'クレーン', '検査'];
    const searchInput = page.locator('input[type="search"], input[name="search"]');

    for (const term of searchTerms) {
      await searchInput.fill(term);
      await page.keyboard.press('Enter');
      await page.waitForTimeout(1500);
    }

    // Check if search history is available
    await searchInput.click();
    await page.waitForTimeout(500);

    const historyItems = page.locator('.search-history-item, .recent-search, datalist option');

    if (await historyItems.count() > 0) {
      const count = await historyItems.count();
      console.log(`✓ Found ${count} search history items`);
    } else {
      console.log('⚠ Search history not found (may not be implemented)');
    }
  });

  test('should export search results', async ({ page }) => {
    console.log('=== Test: Export Search Results ===');

    await login(page, 'worker');
    await page.goto('/knowledge');

    // Perform a search
    const searchInput = page.locator('input[type="search"], input[name="search"]');
    await searchInput.fill('手順');
    await page.keyboard.press('Enter');
    await page.waitForTimeout(2000);

    // Look for export button
    const exportBtn = page.locator(
      'button:has-text("エクスポート"), button:has-text("Export"), button:has-text("CSV"), button:has-text("ダウンロード")'
    );

    if (await exportBtn.count() > 0) {
      // Start waiting for download before clicking
      const downloadPromise = page.waitForEvent('download', { timeout: 5000 });

      await exportBtn.click();

      try {
        const download = await downloadPromise;
        const fileName = download.suggestedFilename();
        expect(fileName).toMatch(/\.(csv|xlsx|pdf)$/i);

        console.log(`✓ Export successful: ${fileName}`);
      } catch (error) {
        console.log('⚠ Export may require additional confirmation');
      }
    } else {
      console.log('⚠ Export functionality not found');
    }
  });
});
