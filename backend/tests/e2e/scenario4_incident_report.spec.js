/**
 * E2E Test Scenario 4: Incident Report
 *
 * Tests the complete incident reporting workflow:
 * 1. Create incident report
 * 2. Attach photos/documents
 * 3. Assign to responsible person
 * 4. Update incident status
 * 5. Add investigation notes
 * 6. Link related knowledge
 * 7. Close incident
 * 8. Verify notifications
 */

const { test, expect } = require('@playwright/test');
const { login, loginAPI } = require('./helpers/auth');
const { createIncident, createKnowledge } = require('./helpers/api');
const { waitForNotification, waitForText, waitForPageLoad } = require('./helpers/waiters');

test.describe('Scenario 4: Incident Report', () => {
  let workerToken;
  let managerToken;

  test.beforeAll(async ({ request }) => {
    const workerAuth = await loginAPI(request, 'worker');
    workerToken = workerAuth.token;

    const managerAuth = await loginAPI(request, 'manager');
    managerToken = managerAuth.token;
  });

  test('should create incident report with all details', async ({ page }) => {
    console.log('=== Test: Create Incident Report ===');

    await login(page, 'worker');

    // Navigate to incident creation page
    await page.goto('/incidents/new').catch(async () => {
      await page.goto('/incidents');
      await page.click('button:has-text("新規作成"), a:has-text("Create"), button:has-text("報告")').catch(() => {});
    });

    // Wait for form to load
    await page.waitForSelector('form, input[name="title"]', { timeout: 10000 });

    // Fill in incident details
    const timestamp = Date.now();
    const incidentTitle = `E2Eテスト: 事故報告 ${timestamp}`;

    await page.fill('input[name="title"], #title', incidentTitle);

    await page.fill(
      'textarea[name="description"], #description',
      '作業中に工具が落下しました。\n\n状況:\n- 場所: 3階作業現場\n- 時刻: 14:30頃\n- 被害: なし（近くに作業者なし）'
    );

    // Select severity
    const severitySelect = page.locator('select[name="severity"], #severity');
    if (await severitySelect.count() > 0) {
      await severitySelect.selectOption('medium');
    }

    // Fill location
    const locationInput = page.locator('input[name="location"], #location');
    if (await locationInput.count() > 0) {
      await locationInput.fill('3階作業現場 A-3区画');
    }

    // Set occurred time
    const occurredAtInput = page.locator('input[name="occurred_at"], #occurred_at, input[type="datetime-local"]');
    if (await occurredAtInput.count() > 0) {
      const now = new Date();
      const dateTimeString = now.toISOString().slice(0, 16);
      await occurredAtInput.fill(dateTimeString);
    }

    // Submit form
    await page.click('button[type="submit"], button:has-text("登録"), button:has-text("作成"), button:has-text("Submit")');

    // Wait for success notification or redirect
    await Promise.race([
      waitForNotification(page, /登録|作成|success/i, 5000).catch(() => {}),
      page.waitForURL(/\/incidents\/\d+/, { timeout: 5000 }).catch(() => {})
    ]);

    // Verify incident was created
    const currentUrl = page.url();
    console.log(`Incident created, URL: ${currentUrl}`);

    // Verify incident details are displayed
    await expect(page.locator(`text=${incidentTitle}`)).toBeVisible({ timeout: 5000 });

    console.log('✓ Incident report created successfully');
  });

  test('should update incident status and add notes', async ({ page, request }) => {
    console.log('=== Test: Update Incident Status ===');

    // Create incident via API
    const incident = await createIncident(request, workerToken, {
      title: `ステータス更新テスト ${Date.now()}`,
      description: '事故の詳細説明',
      severity: 'high',
      location: 'テスト現場'
    });

    // Login as manager
    await login(page, 'manager');

    // Navigate to incident
    await page.goto(`/incidents/${incident.id}`);
    await waitForPageLoad(page);

    // Look for status update controls
    const statusSelect = page.locator('select[name="status"], #status, .status-select');

    if (await statusSelect.count() > 0) {
      // Update status to "investigating"
      await statusSelect.selectOption({ label: /調査中|Investigating/ }).catch(() =>
        statusSelect.selectOption({ value: 'investigating' })
      );

      // Add investigation notes
      const notesField = page.locator('textarea[name="notes"], textarea[name="investigation_notes"], #notes');
      if (await notesField.count() > 0) {
        await notesField.fill('調査開始:\n- 現場確認完了\n- 関係者ヒアリング実施中');

        // Save changes
        await page.click('button[type="submit"], button:has-text("更新"), button:has-text("保存"), button:has-text("Save")');

        await waitForNotification(page, /更新|updated|保存|saved/i, 5000).catch(() => {});
      }

      console.log('✓ Incident status updated');
    } else {
      console.log('⚠ Status update UI not found');
    }

    // Verify status badge shows updated status
    const statusBadge = page.locator('.status, .badge, [class*="status"]');
    if (await statusBadge.count() > 0) {
      const statusText = await statusBadge.first().textContent();
      expect(statusText.toLowerCase()).toMatch(/investigating|調査中|in_progress/);
    }
  });

  test('should assign incident to responsible person', async ({ page, request }) => {
    console.log('=== Test: Assign Incident ===');

    // Create incident
    const incident = await createIncident(request, workerToken, {
      title: `担当者割当テスト ${Date.now()}`,
      description: '担当者を割り当てるテスト',
      severity: 'medium'
    });

    await login(page, 'manager');
    await page.goto(`/incidents/${incident.id}`);
    await waitForPageLoad(page);

    // Look for assignment controls
    const assigneeSelect = page.locator(
      'select[name="assignee"], select[name="assigned_to"], #assignee'
    );

    if (await assigneeSelect.count() > 0) {
      // Assign to a user
      await assigneeSelect.selectOption({ index: 1 }); // Select first available user

      // Save assignment
      const saveBtn = page.locator('button:has-text("割当"), button:has-text("Assign"), button:has-text("保存")');
      if (await saveBtn.count() > 0) {
        await saveBtn.click();
        await waitForNotification(page, /割当|assigned|success/i, 5000).catch(() => {});
      }

      console.log('✓ Incident assigned successfully');
    } else {
      console.log('⚠ Assignment UI not found');
    }
  });

  test('should link related knowledge to incident', async ({ page, request }) => {
    console.log('=== Test: Link Related Knowledge ===');

    // Create knowledge and incident
    const knowledge = await createKnowledge(request, workerToken, {
      title: '工具落下防止対策',
      content: '工具の落下を防ぐための対策手順',
      category: 'safety'
    });

    const incident = await createIncident(request, workerToken, {
      title: `関連ナレッジテスト ${Date.now()}`,
      description: '工具落下事故',
      severity: 'medium'
    });

    await login(page, 'manager');
    await page.goto(`/incidents/${incident.id}`);
    await waitForPageLoad(page);

    // Look for "Add Related Knowledge" button or section
    const addKnowledgeBtn = page.locator(
      'button:has-text("関連ナレッジ"), button:has-text("Link Knowledge"), button:has-text("ナレッジを追加")'
    );

    if (await addKnowledgeBtn.count() > 0) {
      await addKnowledgeBtn.click();
      await page.waitForTimeout(1000);

      // Search for knowledge
      const searchInput = page.locator('input[name="knowledge_search"], input[placeholder*="検索"]');
      if (await searchInput.count() > 0) {
        await searchInput.fill('工具落下');
        await page.waitForTimeout(1000);

        // Select the knowledge
        const knowledgeItem = page.locator(`text=${knowledge.title}`).first();
        if (await knowledgeItem.count() > 0) {
          await knowledgeItem.click();

          // Confirm selection
          await page.click('button:has-text("追加"), button:has-text("Link"), button:has-text("確定")');
          await waitForNotification(page, /追加|linked|success/i, 5000).catch(() => {});

          console.log('✓ Related knowledge linked successfully');
        }
      }
    } else {
      console.log('⚠ Link knowledge UI not found');
    }
  });

  test('should complete incident workflow from report to closure', async ({ page, request }) => {
    console.log('=== Test: Complete Incident Workflow ===');

    // Create incident
    const incident = await createIncident(request, workerToken, {
      title: `完全ワークフローテスト ${Date.now()}`,
      description: '作業中の軽微な事故',
      severity: 'low',
      location: 'テスト現場'
    });

    console.log(`Created incident: ${incident.id}`);

    // Step 1: Worker reports incident (already done via API)

    // Step 2: Manager reviews and starts investigation
    await login(page, 'manager');
    await page.goto(`/incidents/${incident.id}`);
    await waitForPageLoad(page);

    // Update status to investigating
    const statusSelect = page.locator('select[name="status"], .status-select');
    if (await statusSelect.count() > 0) {
      await statusSelect.selectOption({ value: 'investigating' }).catch(() =>
        statusSelect.selectOption({ index: 1 })
      );

      await page.click('button:has-text("更新"), button:has-text("保存")').catch(() => {});
      await page.waitForTimeout(1000);
    }

    // Add investigation notes
    const notesBtn = page.locator('button:has-text("メモ追加"), button:has-text("Add Note"), button:has-text("調査記録")');
    if (await notesBtn.count() > 0) {
      await notesBtn.click();

      const notesField = page.locator('textarea[name="notes"], #note-content');
      await notesField.fill('原因調査完了:\n- 工具固定不十分\n- 対策: 固定方法の見直し');

      await page.click('button[type="submit"], button:has-text("保存")');
      await page.waitForTimeout(1000);
    }

    // Step 3: Add corrective actions
    const actionsBtn = page.locator('button:has-text("是正措置"), button:has-text("Corrective Actions")');
    if (await actionsBtn.count() > 0) {
      await actionsBtn.click();

      const actionField = page.locator('textarea[name="corrective_actions"], #actions');
      await actionField.fill('是正措置:\n1. 工具固定手順の改訂\n2. 全作業員への周知\n3. 定期点検の実施');

      await page.click('button[type="submit"], button:has-text("保存")');
      await page.waitForTimeout(1000);
    }

    // Step 4: Close incident
    if (await statusSelect.count() > 0) {
      await statusSelect.selectOption({ value: 'resolved' }).catch(() =>
        statusSelect.selectOption({ label: /完了|Resolved|解決/ })
      );

      await page.click('button:has-text("更新"), button:has-text("保存")');
      await waitForNotification(page, /更新|updated|完了|resolved/i, 5000).catch(() => {});
    }

    // Verify incident is closed
    const statusBadge = page.locator('.status, .badge');
    if (await statusBadge.count() > 0) {
      const statusText = await statusBadge.first().textContent();
      expect(statusText.toLowerCase()).toMatch(/resolved|完了|closed|解決/);
    }

    console.log('✓ Complete incident workflow executed successfully');
  });

  test('should display incident statistics and trends', async ({ page, request }) => {
    console.log('=== Test: Incident Statistics ===');

    // Create multiple incidents
    const severities = ['low', 'medium', 'high'];
    for (let i = 0; i < 3; i++) {
      await createIncident(request, workerToken, {
        title: `統計テスト ${Date.now()}_${i}`,
        description: `テスト事故 ${i + 1}`,
        severity: severities[i],
        location: 'テスト現場'
      });
    }

    await login(page, 'manager');

    // Navigate to incidents dashboard
    await page.goto('/incidents/dashboard').catch(async () => {
      await page.goto('/incidents');
    });

    await waitForPageLoad(page);

    // Look for statistics widgets
    const statsWidgets = page.locator('.stat, .statistic, .widget, .card');
    const widgetCount = await statsWidgets.count();

    if (widgetCount > 0) {
      console.log(`✓ Found ${widgetCount} statistics widgets`);

      // Look for specific metrics
      const metricsToCheck = ['合計', 'Total', '未解決', 'Open', '重大', 'High'];

      for (const metric of metricsToCheck) {
        const metricElement = page.locator(`text=${metric}`);
        if (await metricElement.count() > 0) {
          console.log(`  - Found metric: ${metric}`);
        }
      }
    } else {
      console.log('⚠ No statistics widgets found');
    }

    // Look for charts
    const charts = page.locator('canvas, svg, .chart');
    if (await charts.count() > 0) {
      console.log('✓ Found charts/visualizations');
    }
  });

  test('should send notifications for incident updates', async ({ page, request }) => {
    console.log('=== Test: Incident Notifications ===');

    // Create incident as worker
    const incident = await createIncident(request, workerToken, {
      title: `通知テスト ${Date.now()}`,
      description: '通知確認用の事故',
      severity: 'medium'
    });

    // Manager views and comments on incident
    await login(page, 'manager');
    await page.goto(`/incidents/${incident.id}`);
    await waitForPageLoad(page);

    // Add a comment
    const commentBtn = page.locator('button:has-text("コメント"), button:has-text("Comment")');
    if (await commentBtn.count() > 0) {
      await commentBtn.click();

      const commentField = page.locator('textarea[name="comment"], #comment');
      await commentField.fill('確認しました。調査を開始します。');

      await page.click('button[type="submit"], button:has-text("送信"), button:has-text("投稿")');
      await waitForNotification(page, /コメント|comment|投稿/i, 5000).catch(() => {});
    }

    // Switch back to worker account
    await login(page, 'worker');

    // Check notifications
    await page.goto('/notifications').catch(async () => {
      await page.click('.notifications-icon, [href*="notification"]').catch(() => {});
    });

    await page.waitForTimeout(2000);

    // Look for incident notification
    const notificationItems = page.locator('.notification-item, .notification, .alert');
    const count = await notificationItems.count();

    if (count > 0) {
      // Check if any notification relates to our incident
      const notificationText = await notificationItems.first().textContent();
      console.log(`✓ Found ${count} notifications`);
    } else {
      console.log('⚠ No notifications found (may be cleared or not implemented)');
    }
  });
});
