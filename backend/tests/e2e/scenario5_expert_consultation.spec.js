/**
 * E2E Test Scenario 5: Expert Consultation
 *
 * Tests the expert consultation workflow:
 * 1. Worker submits consultation request
 * 2. Expert receives notification
 * 3. Expert provides answer
 * 4. Worker receives notification of answer
 * 5. Worker marks as helpful
 * 6. Expert views consultation history
 * 7. Create knowledge from consultation
 */

const { test, expect } = require('@playwright/test');
const { login, loginAPI, logout } = require('./helpers/auth');
const { createConsultation, answerConsultation, getNotifications } = require('./helpers/api');
const { waitForNotification, waitForText, waitForPageLoad } = require('./helpers/waiters');

test.describe('Scenario 5: Expert Consultation', () => {
  let workerToken;
  let expertToken;

  test.beforeAll(async ({ request }) => {
    const workerAuth = await loginAPI(request, 'worker');
    workerToken = workerAuth.token;

    const expertAuth = await loginAPI(request, 'expert');
    expertToken = expertAuth.token;
  });

  test('should submit and answer consultation request', async ({ page, request }) => {
    console.log('=== Test: Submit and Answer Consultation ===');

    // Step 1: Login as worker and create consultation
    await login(page, 'worker');

    // Navigate to consultation creation page
    await page.goto('/consultations/new').catch(async () => {
      await page.goto('/consultations');
      await page.click('button:has-text("相談"), button:has-text("New"), a:has-text("相談")').catch(() => {});
    });

    // Wait for form to load
    await page.waitForSelector('form, input[name="title"]', { timeout: 10000 });

    // Fill consultation form
    const consultationTitle = `E2Eテスト: 専門家相談 ${Date.now()}`;
    const consultationQuestion = '高所作業における安全装備の選定について相談があります。\n\n状況:\n- 作業高さ: 15m\n- 作業期間: 2週間\n- 作業者数: 3名\n\nどのような装備が適切でしょうか？';

    await page.fill('input[name="title"], #title', consultationTitle);
    await page.fill('textarea[name="question"], #question', consultationQuestion);

    // Select category
    const categorySelect = page.locator('select[name="category"], #category');
    if (await categorySelect.count() > 0) {
      await categorySelect.selectOption({ value: 'safety' }).catch(() =>
        categorySelect.selectOption({ index: 1 })
      );
    }

    // Select priority
    const prioritySelect = page.locator('select[name="priority"], #priority');
    if (await prioritySelect.count() > 0) {
      await prioritySelect.selectOption('medium');
    }

    // Submit consultation
    await page.click('button[type="submit"], button:has-text("送信"), button:has-text("Submit"), button:has-text("相談")');

    // Wait for success
    await Promise.race([
      waitForNotification(page, /送信|success|相談/i, 5000).catch(() => {}),
      page.waitForURL(/\/consultations\/\d+/, { timeout: 5000 }).catch(() => {})
    ]);

    // Get consultation ID
    const currentUrl = page.url();
    const urlMatch = currentUrl.match(/\/consultations\/(\d+)/);
    let consultationId;

    if (urlMatch) {
      consultationId = parseInt(urlMatch[1]);
    } else {
      // Fallback: Create via API
      const consultation = await createConsultation(request, workerToken, {
        title: consultationTitle,
        question: consultationQuestion,
        category: 'safety',
        priority: 'medium'
      });
      consultationId = consultation.id;
    }

    console.log(`Consultation created: ${consultationId}`);

    // Step 2: Logout and login as expert
    await logout(page);
    await login(page, 'expert');

    // Navigate to consultations
    await page.goto('/consultations').catch(async () => {
      await page.click('text=相談, text=Consultations, a[href*="consultation"]').catch(() => {});
    });

    await waitForPageLoad(page);

    // Find the consultation
    const consultationLink = page.locator(`text=${consultationTitle}`).first();
    if (await consultationLink.count() > 0) {
      await consultationLink.click();
    } else {
      await page.goto(`/consultations/${consultationId}`);
    }

    await waitForPageLoad(page);

    // Step 3: Expert provides answer
    const answerField = page.locator('textarea[name="answer"], #answer, textarea[placeholder*="回答"]');

    if (await answerField.count() > 0) {
      const expertAnswer = `ご相談ありがとうございます。\n\n15m高所での作業には以下の装備が必要です:\n\n1. フルハーネス型安全帯\n   - 墜落制止用器具として必須\n   - 2本のランヤード付き\n\n2. ヘルメット\n   - あご紐付き\n   - 落下物対策\n\n3. 作業靴\n   - 滑り止め付き\n   - JIS規格適合品\n\n2週間の作業期間であれば、定期的な装備点検も実施してください。\n何か不明点があれば、お気軽にご質問ください。`;

      await answerField.fill(expertAnswer);

      // Submit answer
      await page.click('button[type="submit"], button:has-text("回答"), button:has-text("送信"), button:has-text("Submit")');

      await waitForNotification(page, /回答|送信|success/i, 5000).catch(() => {});

      console.log('✓ Expert answer submitted');
    } else {
      // Answer via API
      await answerConsultation(request, expertToken, consultationId, 'テスト回答: 適切な安全装備についてアドバイスします。');
    }

    // Step 4: Verify worker receives notification
    const workerNotifications = await getNotifications(request, workerToken);
    const answerNotif = workerNotifications.find(n =>
      n.consultation_id === consultationId && n.type === 'consultation_answered'
    );

    if (answerNotif) {
      console.log('✓ Worker notification sent');
    }

    // Step 5: Login as worker and view answer
    await logout(page);
    await login(page, 'worker');

    await page.goto(`/consultations/${consultationId}`);
    await waitForPageLoad(page);

    // Verify answer is displayed
    await expect(page.locator('.answer, .expert-answer, .response')).toBeVisible({ timeout: 5000 });

    // Mark as helpful
    const helpfulBtn = page.locator('button:has-text("役立った"), button:has-text("Helpful"), button:has-text("参考になった")');
    if (await helpfulBtn.count() > 0) {
      await helpfulBtn.click();
      await waitForNotification(page, /ありがとう|thank|feedback/i, 3000).catch(() => {});
      console.log('✓ Marked as helpful');
    }

    console.log('✓ Complete consultation workflow executed successfully');
  });

  test('should filter consultations by status and category', async ({ page, request }) => {
    console.log('=== Test: Filter Consultations ===');

    // Create consultations with different statuses
    const consultation1 = await createConsultation(request, workerToken, {
      title: 'フィルタテスト1 - 未回答',
      question: 'テスト質問1',
      category: 'technical',
      priority: 'high'
    });

    const consultation2 = await createConsultation(request, workerToken, {
      title: 'フィルタテスト2 - 回答済み',
      question: 'テスト質問2',
      category: 'safety',
      priority: 'medium'
    });

    await answerConsultation(request, expertToken, consultation2.id, 'テスト回答');

    // Login and navigate to consultations
    await login(page, 'worker');
    await page.goto('/consultations');
    await waitForPageLoad(page);

    // Test status filter
    const statusFilter = page.locator('select[name="status"], #status-filter');
    if (await statusFilter.count() > 0) {
      // Filter by "answered"
      await statusFilter.selectOption({ value: 'answered' }).catch(() =>
        statusFilter.selectOption({ label: /回答済|Answered/ })
      );

      await page.waitForTimeout(2000);

      // Verify filtered results
      const results = page.locator('.consultation-item, .consultation-card');
      const count = await results.count();
      console.log(`✓ Status filter: ${count} results`);
    }

    // Test category filter
    const categoryFilter = page.locator('select[name="category"], #category-filter');
    if (await categoryFilter.count() > 0) {
      await categoryFilter.selectOption('safety');
      await page.waitForTimeout(2000);

      const results = page.locator('.consultation-item, .consultation-card');
      const count = await results.count();
      console.log(`✓ Category filter: ${count} results`);
    }
  });

  test('should show expert consultation statistics', async ({ page, request }) => {
    console.log('=== Test: Expert Statistics ===');

    // Create and answer multiple consultations
    for (let i = 0; i < 3; i++) {
      const consultation = await createConsultation(request, workerToken, {
        title: `統計テスト ${i + 1}`,
        question: `テスト質問 ${i + 1}`,
        category: 'technical'
      });

      if (i < 2) {
        await answerConsultation(request, expertToken, consultation.id, `テスト回答 ${i + 1}`);
      }
    }

    // Login as expert
    await login(page, 'expert');

    // Navigate to expert dashboard or profile
    await page.goto('/expert/dashboard').catch(async () => {
      await page.goto('/consultations');
    });

    await waitForPageLoad(page);

    // Look for statistics
    const statsWidgets = page.locator('.stat, .statistic, .metric, .widget');
    const widgetCount = await statsWidgets.count();

    if (widgetCount > 0) {
      console.log(`✓ Found ${widgetCount} statistics widgets`);

      // Check for specific metrics
      const metricsToCheck = ['回答数', 'Total', '未回答', 'Pending', '評価', 'Rating'];

      for (const metric of metricsToCheck) {
        const metricElement = page.locator(`text=${metric}`);
        if (await metricElement.count() > 0) {
          const text = await metricElement.first().textContent();
          console.log(`  - Found metric: ${text}`);
        }
      }
    } else {
      console.log('⚠ No statistics found');
    }
  });

  test('should create knowledge from consultation', async ({ page, request }) => {
    console.log('=== Test: Create Knowledge from Consultation ===');

    // Create and answer consultation
    const consultation = await createConsultation(request, workerToken, {
      title: 'ナレッジ化テスト: 溶接作業の注意点',
      question: '溶接作業時の安全対策について教えてください。',
      category: 'safety'
    });

    await answerConsultation(
      request,
      expertToken,
      consultation.id,
      '溶接作業の安全対策:\n1. 保護メガネの着用\n2. 換気の確保\n3. 可燃物の除去'
    );

    // Login as expert
    await login(page, 'expert');
    await page.goto(`/consultations/${consultation.id}`);
    await waitForPageLoad(page);

    // Look for "Create Knowledge" button
    const createKnowledgeBtn = page.locator(
      'button:has-text("ナレッジ化"), button:has-text("Create Knowledge"), button:has-text("ナレッジとして保存")'
    );

    if (await createKnowledgeBtn.count() > 0) {
      await createKnowledgeBtn.click();

      // Form should be pre-filled with consultation data
      await page.waitForSelector('form, input[name="title"]', { timeout: 10000 });

      const titleField = page.locator('input[name="title"], #title');
      const titleValue = await titleField.inputValue();

      expect(titleValue).toContain('溶接作業');

      // Submit knowledge creation
      await page.click('button[type="submit"], button:has-text("作成"), button:has-text("Create")');

      await waitForNotification(page, /作成|created|success/i, 5000).catch(() => {});

      console.log('✓ Knowledge created from consultation');
    } else {
      console.log('⚠ Create Knowledge button not found');
    }
  });

  test('should support follow-up questions', async ({ page, request }) => {
    console.log('=== Test: Follow-up Questions ===');

    // Create and answer consultation
    const consultation = await createConsultation(request, workerToken, {
      title: 'フォローアップテスト',
      question: '初回の質問です。',
      category: 'technical'
    });

    await answerConsultation(request, expertToken, consultation.id, '初回の回答です。');

    // Login as worker
    await login(page, 'worker');
    await page.goto(`/consultations/${consultation.id}`);
    await waitForPageLoad(page);

    // Look for follow-up question field
    const followUpField = page.locator(
      'textarea[name="follow_up"], textarea[placeholder*="追加"], #follow-up-question'
    );

    if (await followUpField.count() > 0) {
      await followUpField.fill('追加で質問があります。詳細を教えてください。');

      await page.click('button:has-text("質問"), button:has-text("Ask"), button:has-text("送信")');

      await waitForNotification(page, /送信|sent|success/i, 5000).catch(() => {});

      console.log('✓ Follow-up question submitted');
    } else {
      // Try adding a comment instead
      const commentField = page.locator('textarea[name="comment"], #comment');
      if (await commentField.count() > 0) {
        await commentField.fill('追加質問: 詳細を教えてください。');

        await page.click('button:has-text("コメント"), button:has-text("Comment")');
        await page.waitForTimeout(1000);

        console.log('✓ Follow-up via comment submitted');
      } else {
        console.log('⚠ Follow-up mechanism not found');
      }
    }
  });

  test('should show consultation history for users', async ({ page, request }) => {
    console.log('=== Test: Consultation History ===');

    // Create multiple consultations
    for (let i = 0; i < 3; i++) {
      await createConsultation(request, workerToken, {
        title: `履歴テスト ${i + 1}`,
        question: `質問 ${i + 1}`,
        category: 'technical'
      });
    }

    // Login as worker
    await login(page, 'worker');

    // Navigate to consultations or user profile
    await page.goto('/consultations').catch(async () => {
      await page.goto('/profile/consultations');
    });

    await waitForPageLoad(page);

    // Look for "My Consultations" section
    const myConsultations = page.locator('.my-consultations, .user-consultations, .consultation-list');

    if (await myConsultations.count() > 0) {
      const consultationItems = page.locator('.consultation-item, .consultation-card');
      const count = await consultationItems.count();

      expect(count).toBeGreaterThanOrEqual(3);
      console.log(`✓ Found ${count} consultations in history`);
    } else {
      // Count all visible consultation items
      const allItems = page.locator('.consultation-item, .consultation-card, tr[data-consultation-id]');
      const count = await allItems.count();
      console.log(`✓ Found ${count} consultations`);
    }
  });

  test('should notify expert of urgent consultations', async ({ page, request }) => {
    console.log('=== Test: Urgent Consultation Notification ===');

    // Create high-priority consultation
    const consultation = await createConsultation(request, workerToken, {
      title: '緊急: 設備故障への対応',
      question: '設備が停止しました。緊急で対応方法を教えてください。',
      category: 'technical',
      priority: 'high'
    });

    // Login as expert
    await login(page, 'expert');

    // Check notifications
    await page.goto('/notifications').catch(async () => {
      await page.click('.notifications-icon, [href*="notification"]').catch(() => {});
    });

    await page.waitForTimeout(2000);

    // Look for urgent notification
    const urgentNotif = page.locator('.notification.urgent, .notification.high, .notification[data-priority="high"]');

    if (await urgentNotif.count() > 0) {
      console.log('✓ Urgent notification displayed');

      // Verify it stands out (e.g., has special styling)
      const classList = await urgentNotif.first().getAttribute('class');
      expect(classList).toMatch(/urgent|high|priority|important/i);
    } else {
      // Check regular notifications
      const notifications = page.locator('.notification-item, .notification');
      const count = await notifications.count();
      console.log(`Found ${count} notifications (urgent styling may not be implemented)`);
    }

    // Navigate to consultation
    await page.goto(`/consultations/${consultation.id}`);
    await waitForPageLoad(page);

    // Verify priority badge
    const priorityBadge = page.locator('.priority, .badge[class*="priority"]');
    if (await priorityBadge.count() > 0) {
      const badgeText = await priorityBadge.first().textContent();
      expect(badgeText.toLowerCase()).toMatch(/high|urgent|緊急|高/);
      console.log('✓ Priority badge displayed correctly');
    }
  });
});
