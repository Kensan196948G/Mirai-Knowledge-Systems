/**
 * Wait Helpers for E2E Tests
 * Provides utilities for waiting on various conditions
 */

const { expect } = require('@playwright/test');

/**
 * Wait for notification to appear
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} messagePattern - Pattern to match in notification
 * @param {number} timeout - Timeout in milliseconds
 * @returns {Promise<boolean>} True if notification appeared
 */
async function waitForNotification(page, messagePattern, timeout = 10000) {
  try {
    const notificationSelector = [
      '.notification',
      '.toast',
      '.alert',
      '[role="alert"]',
      '.message'
    ].join(', ');

    await page.waitForSelector(notificationSelector, { timeout });

    const notification = page.locator(notificationSelector).first();
    const text = await notification.textContent();

    if (typeof messagePattern === 'string') {
      expect(text).toContain(messagePattern);
    } else {
      expect(text).toMatch(messagePattern);
    }

    return true;
  } catch (error) {
    console.warn(`Notification not found: ${messagePattern}`);
    return false;
  }
}

/**
 * Wait for element to appear with text
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} text - Text to find
 * @param {number} timeout - Timeout in milliseconds
 * @returns {Promise<import('@playwright/test').Locator>} Element locator
 */
async function waitForText(page, text, timeout = 10000) {
  const locator = page.getByText(text, { exact: false }).first();
  await locator.waitFor({ state: 'visible', timeout });
  return locator;
}

/**
 * Wait for API response
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} urlPattern - URL pattern to match
 * @param {number} timeout - Timeout in milliseconds
 * @returns {Promise<import('@playwright/test').Response>} Response object
 */
async function waitForAPIResponse(page, urlPattern, timeout = 15000) {
  const response = await page.waitForResponse(
    (resp) => {
      const url = resp.url();
      return url.includes(urlPattern) || new RegExp(urlPattern).test(url);
    },
    { timeout }
  );

  return response;
}

/**
 * Wait for page to be fully loaded
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {number} timeout - Timeout in milliseconds
 */
async function waitForPageLoad(page, timeout = 30000) {
  await page.waitForLoadState('networkidle', { timeout });
}

/**
 * Wait for element count to change
 * @param {import('@playwright/test').Locator} locator - Element locator
 * @param {number} expectedCount - Expected element count
 * @param {number} timeout - Timeout in milliseconds
 */
async function waitForCount(locator, expectedCount, timeout = 10000) {
  await expect(locator).toHaveCount(expectedCount, { timeout });
}

/**
 * Retry an action until it succeeds or timeout
 * @param {Function} action - Async function to retry
 * @param {Object} options - Options
 * @returns {Promise<any>} Result of the action
 */
async function retry(action, options = {}) {
  const {
    retries = 3,
    delay = 1000,
    timeout = 30000
  } = options;

  const startTime = Date.now();

  for (let i = 0; i < retries; i++) {
    try {
      if (Date.now() - startTime > timeout) {
        throw new Error('Retry timeout exceeded');
      }

      return await action();
    } catch (error) {
      if (i === retries - 1) {
        throw error;
      }
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}

module.exports = {
  waitForNotification,
  waitForText,
  waitForAPIResponse,
  waitForPageLoad,
  waitForCount,
  retry
};
