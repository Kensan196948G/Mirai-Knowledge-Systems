/**
 * Authentication Helper for E2E Tests
 * Provides login and user management utilities
 */

const { expect } = require('@playwright/test');

/**
 * Test user credentials
 */
const TEST_USERS = {
  admin: {
    email: 'admin@example.com',
    password: 'Admin123!',
    role: 'admin',
    name: '管理者ユーザー'
  },
  manager: {
    email: 'manager@example.com',
    password: 'Manager123!',
    role: 'manager',
    name: 'マネージャー'
  },
  worker: {
    email: 'worker@example.com',
    password: 'Worker123!',
    role: 'worker',
    name: '作業者'
  },
  expert: {
    email: 'expert@example.com',
    password: 'Expert123!',
    role: 'expert',
    name: '専門家'
  }
};

/**
 * Login to the application
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} userType - Type of user (admin, manager, worker, expert)
 * @returns {Promise<Object>} User credentials and token
 */
async function login(page, userType = 'worker') {
  const user = TEST_USERS[userType];
  if (!user) {
    throw new Error(`Unknown user type: ${userType}`);
  }

  // Navigate to login page
  await page.goto('/login');

  // Fill in credentials
  await page.fill('input[name="email"], input[type="email"]', user.email);
  await page.fill('input[name="password"], input[type="password"]', user.password);

  // Submit form
  await page.click('button[type="submit"]');

  // Wait for successful login (redirect or token storage)
  await page.waitForURL(/\/(dashboard|home|knowledge)/, { timeout: 15000 });

  // Get token from localStorage if available
  const token = await page.evaluate(() => {
    return localStorage.getItem('access_token') || localStorage.getItem('token');
  });

  return {
    user,
    token
  };
}

/**
 * Login via API (faster for setup)
 * @param {import('@playwright/test').APIRequestContext} request - Playwright request context
 * @param {string} userType - Type of user
 * @returns {Promise<Object>} Authentication response
 */
async function loginAPI(request, userType = 'worker') {
  const user = TEST_USERS[userType];
  if (!user) {
    throw new Error(`Unknown user type: ${userType}`);
  }

  const response = await request.post('/api/v1/auth/login', {
    data: {
      email: user.email,
      password: user.password
    }
  });

  expect(response.ok()).toBeTruthy();
  const data = await response.json();

  return {
    user,
    token: data.access_token,
    response: data
  };
}

/**
 * Set authentication token in page context
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} token - JWT token
 */
async function setAuthToken(page, token) {
  await page.evaluate((tokenValue) => {
    localStorage.setItem('access_token', tokenValue);
    localStorage.setItem('token', tokenValue);
  }, token);
}

/**
 * Logout from the application
 * @param {import('@playwright/test').Page} page - Playwright page object
 */
async function logout(page) {
  // Try to find and click logout button
  const logoutButton = page.locator('button:has-text("ログアウト"), button:has-text("Logout"), a:has-text("ログアウト")').first();

  if (await logoutButton.isVisible({ timeout: 2000 }).catch(() => false)) {
    await logoutButton.click();
  }

  // Clear storage
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  // Navigate to login page
  await page.goto('/login');
}

/**
 * Check if user is logged in
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @returns {Promise<boolean>} True if logged in
 */
async function isLoggedIn(page) {
  const token = await page.evaluate(() => {
    return localStorage.getItem('access_token') || localStorage.getItem('token');
  });

  return !!token && token.length > 0;
}

module.exports = {
  TEST_USERS,
  login,
  loginAPI,
  setAuthToken,
  logout,
  isLoggedIn
};
