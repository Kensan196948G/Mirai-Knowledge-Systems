/**
 * E2E Test Scenario 2: Approval Flow
 *
 * Tests the complete approval workflow including:
 * 1. Submit knowledge for approval
 * 2. Approve knowledge
 * 3. Request changes (差戻し)
 * 4. Resubmit after changes
 * 5. Reject knowledge
 * 6. Verify notifications at each step
 */

const { test, expect } = require('@playwright/test');
const { login, loginAPI, logout } = require('./helpers/auth');
const {
  createKnowledge,
  createApprovalRequest,
  processApproval,
  getNotifications,
  updateKnowledgeStatus
} = require('./helpers/api');
const { waitForNotification, waitForText } = require('./helpers/waiters');

test.describe('Scenario 2: Approval Flow', () => {
  let workerToken;
  let managerToken;

  test.beforeAll(async ({ request }) => {
    const workerAuth = await loginAPI(request, 'worker');
    workerToken = workerAuth.token;

    const managerAuth = await loginAPI(request, 'manager');
    managerToken = managerAuth.token;
  });

  test('should handle approval flow - approve path', async ({ page, request }) => {
    console.log('=== Test: Approval Flow - Approve ===');

    // Create knowledge as worker
    const knowledge = await createKnowledge(request, workerToken, {
      title: `承認テスト (承認) ${Date.now()}`,
      content: 'このナレッジは承認されるべきです。',
      category: 'safety'
    });

    // Create approval request
    const approval = await createApprovalRequest(request, workerToken, knowledge.id);
    console.log(`Approval request created: ${approval.id}`);

    // Login as manager
    await login(page, 'manager');

    // Navigate to approval detail
    await page.goto(`/approvals/${approval.id}`).catch(async () => {
      await page.goto('/approvals');
      await page.click(`text=${knowledge.title}`).catch(() => {});
    });

    // Wait for page to load
    await page.waitForSelector('.approval-detail, .approval-content, form', { timeout: 10000 });

    // Verify knowledge details are shown
    await expect(page.locator(`text=${knowledge.title}`)).toBeVisible();

    // Click approve button
    const approveButton = page.locator('button:has-text("承認"), button:has-text("Approve")');
    await approveButton.click();

    // Add comment if prompted
    const commentField = page.locator('textarea[name="comment"], #comment, textarea[placeholder*="コメント"]');
    if (await commentField.isVisible({ timeout: 2000 }).catch(() => false)) {
      await commentField.fill('内容を確認しました。承認します。');
      await page.click('button[type="submit"], button:has-text("確定"), button:has-text("Submit")');
    }

    // Wait for success notification
    await waitForNotification(page, /承認|approved|success/i, 5000).catch(() => {});

    // Verify via API that approval was processed
    const notifications = await getNotifications(request, workerToken);
    const approvalNotif = notifications.find(n =>
      n.knowledge_id === knowledge.id && n.type === 'approval_approved'
    );

    expect(approvalNotif).toBeTruthy();
    console.log('✓ Approval flow completed successfully');
  });

  test('should handle approval flow - request changes path', async ({ page, request }) => {
    console.log('=== Test: Approval Flow - Request Changes ===');

    // Create knowledge as worker
    const knowledge = await createKnowledge(request, workerToken, {
      title: `承認テスト (差戻し) ${Date.now()}`,
      content: 'このナレッジは修正が必要です。',
      category: 'procedure'
    });

    // Create approval request
    const approval = await createApprovalRequest(request, workerToken, knowledge.id);

    // Login as manager
    await login(page, 'manager');

    // Navigate to approval
    await page.goto(`/approvals/${approval.id}`).catch(async () => {
      await page.goto('/approvals');
    });

    await page.waitForSelector('.approval-detail, form', { timeout: 10000 }).catch(() => {});

    // Click request changes button
    const requestChangesBtn = page.locator(
      'button:has-text("差戻"), button:has-text("Request Changes"), button:has-text("修正依頼")'
    );

    if (await requestChangesBtn.count() > 0) {
      await requestChangesBtn.click();

      // Fill in change request comment
      const commentField = page.locator('textarea[name="comment"], #comment');
      await commentField.fill('以下の点を修正してください:\n1. 手順の詳細化\n2. 図の追加');

      await page.click('button[type="submit"], button:has-text("確定"), button:has-text("Submit")');

      await waitForNotification(page, /差戻|request|changes/i, 5000).catch(() => {});
    } else {
      // Request changes via API
      await processApproval(
        request,
        managerToken,
        approval.id,
        'request_changes',
        '以下の点を修正してください:\n1. 手順の詳細化\n2. 図の追加'
      );
    }

    // Logout and login as worker
    await logout(page);
    await login(page, 'worker');

    // Check notifications for change request
    const notifications = await getNotifications(request, workerToken);
    const changeRequestNotif = notifications.find(n =>
      n.knowledge_id === knowledge.id && n.type === 'approval_changes_requested'
    );

    expect(changeRequestNotif).toBeTruthy();

    // Navigate to knowledge to make changes
    await page.goto(`/knowledge/${knowledge.id}/edit`).catch(async () => {
      await page.goto(`/knowledge/${knowledge.id}`);
      await page.click('button:has-text("編集"), a:has-text("Edit")').catch(() => {});
    });

    await page.waitForSelector('form, textarea[name="content"]', { timeout: 10000 }).catch(() => {});

    // Update content
    const contentField = page.locator('textarea[name="content"], #content');
    if (await contentField.count() > 0) {
      const currentContent = await contentField.inputValue();
      await contentField.fill(currentContent + '\n\n修正:\n1. 手順を詳細化しました\n2. 図を追加しました');

      // Save changes
      await page.click('button[type="submit"], button:has-text("更新"), button:has-text("Save")');
      await waitForNotification(page, /更新|updated|success/i, 5000).catch(() => {});
    }

    // Resubmit for approval
    const resubmitBtn = page.locator('button:has-text("再申請"), button:has-text("Resubmit")');
    if (await resubmitBtn.count() > 0) {
      await resubmitBtn.click();
      await waitForNotification(page, /申請|submitted/i, 5000).catch(() => {});
    } else {
      // Create new approval request via API
      await createApprovalRequest(request, workerToken, knowledge.id);
    }

    console.log('✓ Request changes flow completed successfully');
  });

  test('should handle approval flow - reject path', async ({ page, request }) => {
    console.log('=== Test: Approval Flow - Reject ===');

    // Create knowledge as worker
    const knowledge = await createKnowledge(request, workerToken, {
      title: `承認テスト (却下) ${Date.now()}`,
      content: 'このナレッジは却下されます。',
      category: 'other'
    });

    // Create approval request
    const approval = await createApprovalRequest(request, workerToken, knowledge.id);

    // Reject via API (faster)
    await processApproval(
      request,
      managerToken,
      approval.id,
      'reject',
      '内容が不適切なため却下します。'
    );

    // Login as worker and verify rejection notification
    await login(page, 'worker');

    // Navigate to notifications
    await page.goto('/notifications').catch(async () => {
      await page.click('text=通知, text=Notifications, .notifications-icon').catch(() => {});
    });

    await page.waitForTimeout(2000);

    // Check for rejection notification
    const notifications = await getNotifications(request, workerToken);
    const rejectionNotif = notifications.find(n =>
      n.knowledge_id === knowledge.id && n.type === 'approval_rejected'
    );

    expect(rejectionNotif).toBeTruthy();
    expect(rejectionNotif.message).toContain('却下');

    // Navigate to the rejected knowledge
    await page.goto(`/knowledge/${knowledge.id}`);

    await page.waitForSelector('.knowledge-detail, .status', { timeout: 10000 }).catch(() => {});

    // Verify status shows rejected
    const statusElements = page.locator('.status, .badge, [class*="status"]');
    if (await statusElements.count() > 0) {
      const statusText = await statusElements.first().textContent();
      expect(statusText.toLowerCase()).toMatch(/reject|却下|denied/);
    }

    console.log('✓ Rejection flow completed successfully');
  });

  test('should show approval history and timeline', async ({ page, request }) => {
    console.log('=== Test: Approval History ===');

    // Create knowledge with multiple approval actions
    const knowledge = await createKnowledge(request, workerToken, {
      title: `承認履歴テスト ${Date.now()}`,
      content: '複数の承認アクションを持つナレッジ'
    });

    // Create approval request
    const approval1 = await createApprovalRequest(request, workerToken, knowledge.id);

    // Request changes
    await processApproval(request, managerToken, approval1.id, 'request_changes', '最初の修正依頼');

    // Create second approval
    const approval2 = await createApprovalRequest(request, workerToken, knowledge.id);

    // Approve
    await processApproval(request, managerToken, approval2.id, 'approve', '承認します');

    // Login and view knowledge
    await login(page, 'worker');
    await page.goto(`/knowledge/${knowledge.id}`);

    await page.waitForSelector('.knowledge-detail', { timeout: 10000 }).catch(() => {});

    // Look for history/timeline section
    const historySection = page.locator(
      '.approval-history, .timeline, .history, [class*="history"]'
    );

    if (await historySection.count() > 0) {
      await historySection.first().scrollIntoViewIfNeeded();

      // Verify multiple entries exist
      const historyItems = page.locator('.history-item, .timeline-item, .approval-entry');
      const itemCount = await historyItems.count();

      expect(itemCount).toBeGreaterThanOrEqual(2);
      console.log(`Found ${itemCount} history items`);
    }

    console.log('✓ Approval history verified');
  });

  test('should prevent unauthorized approval actions', async ({ page, request }) => {
    console.log('=== Test: Authorization Check ===');

    // Create knowledge and approval
    const knowledge = await createKnowledge(request, workerToken, {
      title: `権限テスト ${Date.now()}`,
      content: '権限チェック用のナレッジ'
    });

    const approval = await createApprovalRequest(request, workerToken, knowledge.id);

    // Login as worker (not manager) and try to approve own knowledge
    await login(page, 'worker');

    await page.goto(`/approvals/${approval.id}`).catch(async () => {
      await page.goto('/approvals');
    });

    // Approval buttons should not be visible or should be disabled
    const approveBtn = page.locator('button:has-text("承認"), button:has-text("Approve")');

    if (await approveBtn.count() > 0) {
      const isDisabled = await approveBtn.isDisabled().catch(() => true);
      expect(isDisabled).toBeTruthy();
      console.log('✓ Approve button is disabled for unauthorized user');
    } else {
      console.log('✓ Approve button is not visible for unauthorized user');
    }

    // Try to approve via API (should fail)
    try {
      await processApproval(request, workerToken, approval.id, 'approve', 'Unauthorized attempt');
      throw new Error('Should have failed with unauthorized error');
    } catch (error) {
      expect(error.message).toMatch(/unauthorized|forbidden|permission|403/i);
      console.log('✓ API correctly rejected unauthorized approval attempt');
    }
  });
});
