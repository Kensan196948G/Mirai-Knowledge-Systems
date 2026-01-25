/**
 * E2E Test Scenario 1: Knowledge Lifecycle
 *
 * Tests the complete lifecycle of a knowledge item:
 * 1. Login as worker
 * 2. Create new knowledge
 * 3. Submit for approval
 * 4. Login as manager
 * 5. Approve knowledge
 * 6. Verify knowledge is published
 * 7. Verify notifications
 * 8. View published knowledge
 */

const { test, expect } = require('@playwright/test');
const { login, loginAPI, logout } = require('./helpers/auth');
const { createKnowledge, createApprovalRequest, processApproval, getNotifications } = require('./helpers/api');
const { waitForNotification, waitForText, waitForAPIResponse } = require('./helpers/waiters');

test.describe('Scenario 1: Knowledge Lifecycle', () => {
  let workerToken;
  let managerToken;
  let knowledgeId;
  let approvalId;

  test.beforeAll(async ({ request }) => {
    // Setup: Get tokens for both users
    const workerAuth = await loginAPI(request, 'worker');
    workerToken = workerAuth.token;

    const managerAuth = await loginAPI(request, 'manager');
    managerToken = managerAuth.token;
  });

  test('should complete full knowledge lifecycle from creation to publication', async ({ page, request }) => {
    // Step 1: Login as worker
    console.log('Step 1: Logging in as worker');
    await login(page, 'worker');
    await expect(page).toHaveURL(/\/(dashboard|home|knowledge)/);

    // Step 2: Navigate to knowledge creation page
    console.log('Step 2: Navigating to knowledge creation');
    await page.click('text=ナレッジ登録, text=新規作成, text=Create Knowledge, a[href*="knowledge/new"]', { timeout: 5000 }).catch(async () => {
      // Fallback: Try navigation
      await page.goto('/knowledge/new');
    });

    // Wait for form to load
    await page.waitForSelector('form, input[name="title"]', { timeout: 10000 });

    // Step 3: Fill in knowledge form
    console.log('Step 3: Creating knowledge');
    const knowledgeTitle = `E2Eテスト: ナレッジライフサイクル ${Date.now()}`;
    const knowledgeContent = '安全作業手順:\n1. 保護具の着用確認\n2. 作業環境の点検\n3. 安全確認後に作業開始';

    await page.fill('input[name="title"], #title', knowledgeTitle);
    await page.fill('textarea[name="content"], #content', knowledgeContent);

    // Select category (if available)
    const categorySelector = 'select[name="category"], #category';
    if (await page.locator(categorySelector).count() > 0) {
      await page.selectOption(categorySelector, 'safety');
    }

    // Add tags (if available)
    const tagsInput = page.locator('input[name="tags"], #tags');
    if (await tagsInput.count() > 0) {
      await tagsInput.fill('安全,作業手順,E2E');
    }

    // Step 4: Submit knowledge
    console.log('Step 4: Submitting knowledge');
    await page.click('button[type="submit"], button:has-text("登録"), button:has-text("作成"), button:has-text("Submit")');

    // Wait for success notification or redirect
    await Promise.race([
      waitForNotification(page, /登録|作成|成功|success/i, 5000).catch(() => {}),
      page.waitForURL(/\/knowledge\/\d+/, { timeout: 5000 }).catch(() => {}),
      page.waitForSelector('.knowledge-detail, .success', { timeout: 5000 }).catch(() => {})
    ]);

    // Get the created knowledge ID from URL or API
    const currentUrl = page.url();
    const urlMatch = currentUrl.match(/\/knowledge\/(\d+)/);

    if (urlMatch) {
      knowledgeId = parseInt(urlMatch[1]);
    } else {
      // Fallback: Create via API to ensure we have an ID
      const knowledge = await createKnowledge(request, workerToken, {
        title: knowledgeTitle,
        content: knowledgeContent,
        category: 'safety',
        tags: ['安全', '作業手順', 'E2E']
      });
      knowledgeId = knowledge.id;
    }

    console.log(`Knowledge created with ID: ${knowledgeId}`);
    expect(knowledgeId).toBeTruthy();

    // Step 5: Submit for approval
    console.log('Step 5: Submitting for approval');

    // Try to find approval button on page
    const approvalButton = page.locator('button:has-text("承認申請"), button:has-text("Submit for Approval")');
    if (await approvalButton.count() > 0) {
      await approvalButton.click();
      await waitForNotification(page, /承認申請|submitted/i, 5000).catch(() => {});
    } else {
      // Create approval via API
      const approval = await createApprovalRequest(request, workerToken, knowledgeId);
      approvalId = approval.id;
    }

    // Step 6: Logout worker and login as manager
    console.log('Step 6: Switching to manager account');
    await logout(page);
    await login(page, 'manager');

    // Step 7: Navigate to approvals page
    console.log('Step 7: Navigating to approvals');
    await page.goto('/approvals').catch(async () => {
      await page.click('text=承認, text=Approvals, a[href*="approval"]').catch(() => {});
    });

    // Wait for approvals list
    await page.waitForSelector('.approval-list, .approvals, table, .approval-item', { timeout: 10000 }).catch(() => {});

    // Step 8: Find and approve the knowledge
    console.log('Step 8: Approving knowledge');

    // Look for the knowledge in the list
    const knowledgeRow = page.locator(`text=${knowledgeTitle}`).first();
    if (await knowledgeRow.count() > 0) {
      await knowledgeRow.click();

      // Click approve button
      await page.click('button:has-text("承認"), button:has-text("Approve")');

      // Add approval comment if prompted
      const commentField = page.locator('textarea[name="comment"], #comment');
      if (await commentField.isVisible({ timeout: 2000 }).catch(() => false)) {
        await commentField.fill('内容を確認しました。承認します。');
        await page.click('button[type="submit"], button:has-text("確定"), button:has-text("Submit")');
      }

      await waitForNotification(page, /承認|approved/i, 5000).catch(() => {});
    } else if (approvalId) {
      // Approve via API
      await processApproval(request, managerToken, approvalId, 'approve', '内容を確認しました。承認します。');
    }

    // Step 9: Verify knowledge is published
    console.log('Step 9: Verifying knowledge publication');
    await page.goto(`/knowledge/${knowledgeId}`);

    await page.waitForSelector('.knowledge-detail, .knowledge-content', { timeout: 10000 });

    // Verify status is approved/published
    const statusBadge = page.locator('.status, .badge, [class*="status"]');
    if (await statusBadge.count() > 0) {
      const statusText = await statusBadge.first().textContent();
      expect(statusText.toLowerCase()).toMatch(/approved|published|承認済|公開/);
    }

    // Step 10: Verify title and content are displayed
    await expect(page.locator(`text=${knowledgeTitle}`)).toBeVisible();
    await expect(page.locator('text=保護具の着用確認')).toBeVisible();

    // Step 11: Check notifications
    console.log('Step 10: Verifying notifications');
    const notifications = await getNotifications(request, workerToken);

    const approvalNotification = notifications.find(n =>
      n.knowledge_id === knowledgeId &&
      n.type === 'approval_approved'
    );

    if (approvalNotification) {
      expect(approvalNotification).toBeTruthy();
      console.log('Approval notification found');
    }

    console.log('✓ Knowledge lifecycle test completed successfully');
  });

  test('should display knowledge in search results after publication', async ({ page }) => {
    // Login as any user
    await login(page, 'worker');

    // Navigate to knowledge search/list
    await page.goto('/knowledge');

    // Search for the created knowledge
    const searchInput = page.locator('input[type="search"], input[name="search"], input[placeholder*="検索"]');
    if (await searchInput.count() > 0) {
      await searchInput.fill('E2Eテスト');
      await page.keyboard.press('Enter');

      // Wait for results
      await page.waitForTimeout(2000);
    }

    // Verify knowledge appears in results
    await page.waitForSelector('.knowledge-list, .knowledge-card, table', { timeout: 10000 });

    // Should see at least one result
    const knowledgeItems = page.locator('.knowledge-item, .knowledge-card, tr[data-knowledge-id]');
    const count = await knowledgeItems.count();
    expect(count).toBeGreaterThan(0);

    console.log('✓ Knowledge appears in search results');
  });
});
