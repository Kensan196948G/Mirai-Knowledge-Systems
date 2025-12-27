/**
 * API Helper for E2E Tests
 * Provides utilities for API interactions during tests
 */

const { expect } = require('@playwright/test');

/**
 * Create headers with authentication
 * @param {string} token - JWT token
 * @returns {Object} Headers object
 */
function createAuthHeaders(token) {
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };
}

/**
 * Create a knowledge item via API
 * @param {import('@playwright/test').APIRequestContext} request - Playwright request context
 * @param {string} token - JWT token
 * @param {Object} data - Knowledge data
 * @returns {Promise<Object>} Created knowledge
 */
async function createKnowledge(request, token, data = {}) {
  const defaultData = {
    title: `テストナレッジ ${Date.now()}`,
    content: 'これはE2Eテスト用のナレッジです。',
    category: 'safety',
    tags: ['test', 'e2e'],
    is_critical: false,
    ...data
  };

  const response = await request.post('/api/v1/knowledge/', {
    headers: createAuthHeaders(token),
    data: defaultData
  });

  expect(response.ok()).toBeTruthy();
  return await response.json();
}

/**
 * Update knowledge status
 * @param {import('@playwright/test').APIRequestContext} request - Playwright request context
 * @param {string} token - JWT token
 * @param {number} knowledgeId - Knowledge ID
 * @param {string} status - New status
 * @returns {Promise<Object>} Updated knowledge
 */
async function updateKnowledgeStatus(request, token, knowledgeId, status) {
  const response = await request.patch(`/api/v1/knowledge/${knowledgeId}/status`, {
    headers: createAuthHeaders(token),
    data: { status }
  });

  expect(response.ok()).toBeTruthy();
  return await response.json();
}

/**
 * Create an approval request
 * @param {import('@playwright/test').APIRequestContext} request - Playwright request context
 * @param {string} token - JWT token
 * @param {number} knowledgeId - Knowledge ID
 * @returns {Promise<Object>} Created approval request
 */
async function createApprovalRequest(request, token, knowledgeId) {
  const response = await request.post('/api/v1/approvals/', {
    headers: createAuthHeaders(token),
    data: {
      knowledge_id: knowledgeId,
      approver_role: 'manager'
    }
  });

  expect(response.ok()).toBeTruthy();
  return await response.json();
}

/**
 * Process an approval (approve/reject/request_changes)
 * @param {import('@playwright/test').APIRequestContext} request - Playwright request context
 * @param {string} token - JWT token
 * @param {number} approvalId - Approval ID
 * @param {string} action - Action to take
 * @param {string} comment - Comment for the action
 * @returns {Promise<Object>} Updated approval
 */
async function processApproval(request, token, approvalId, action, comment = '') {
  const response = await request.post(`/api/v1/approvals/${approvalId}/${action}`, {
    headers: createAuthHeaders(token),
    data: { comment }
  });

  expect(response.ok()).toBeTruthy();
  return await response.json();
}

/**
 * Create an incident report
 * @param {import('@playwright/test').APIRequestContext} request - Playwright request context
 * @param {string} token - JWT token
 * @param {Object} data - Incident data
 * @returns {Promise<Object>} Created incident
 */
async function createIncident(request, token, data = {}) {
  const defaultData = {
    title: `テスト事故レポート ${Date.now()}`,
    description: 'これはE2Eテスト用の事故レポートです。',
    severity: 'medium',
    location: 'テスト現場',
    occurred_at: new Date().toISOString(),
    ...data
  };

  const response = await request.post('/api/v1/incidents/', {
    headers: createAuthHeaders(token),
    data: defaultData
  });

  expect(response.ok()).toBeTruthy();
  return await response.json();
}

/**
 * Create an expert consultation
 * @param {import('@playwright/test').APIRequestContext} request - Playwright request context
 * @param {string} token - JWT token
 * @param {Object} data - Consultation data
 * @returns {Promise<Object>} Created consultation
 */
async function createConsultation(request, token, data = {}) {
  const defaultData = {
    title: `専門家相談 ${Date.now()}`,
    question: 'これはE2Eテスト用の質問です。',
    category: 'technical',
    priority: 'medium',
    ...data
  };

  const response = await request.post('/api/v1/consultations/', {
    headers: createAuthHeaders(token),
    data: defaultData
  });

  expect(response.ok()).toBeTruthy();
  return await response.json();
}

/**
 * Answer a consultation
 * @param {import('@playwright/test').APIRequestContext} request - Playwright request context
 * @param {string} token - JWT token
 * @param {number} consultationId - Consultation ID
 * @param {string} answer - Answer text
 * @returns {Promise<Object>} Updated consultation
 */
async function answerConsultation(request, token, consultationId, answer) {
  const response = await request.post(`/api/v1/consultations/${consultationId}/answer`, {
    headers: createAuthHeaders(token),
    data: { answer }
  });

  expect(response.ok()).toBeTruthy();
  return await response.json();
}

/**
 * Get notifications for current user
 * @param {import('@playwright/test').APIRequestContext} request - Playwright request context
 * @param {string} token - JWT token
 * @returns {Promise<Array>} List of notifications
 */
async function getNotifications(request, token) {
  const response = await request.get('/api/v1/notifications/', {
    headers: createAuthHeaders(token)
  });

  expect(response.ok()).toBeTruthy();
  return await response.json();
}

/**
 * Mark notification as read
 * @param {import('@playwright/test').APIRequestContext} request - Playwright request context
 * @param {string} token - JWT token
 * @param {number} notificationId - Notification ID
 * @returns {Promise<Object>} Updated notification
 */
async function markNotificationRead(request, token, notificationId) {
  const response = await request.patch(`/api/v1/notifications/${notificationId}/read`, {
    headers: createAuthHeaders(token)
  });

  expect(response.ok()).toBeTruthy();
  return await response.json();
}

/**
 * Clean up test data
 * @param {import('@playwright/test').APIRequestContext} request - Playwright request context
 * @param {string} token - JWT token
 * @param {number} knowledgeId - Knowledge ID to delete
 */
async function deleteKnowledge(request, token, knowledgeId) {
  await request.delete(`/api/v1/knowledge/${knowledgeId}`, {
    headers: createAuthHeaders(token)
  });
}

module.exports = {
  createAuthHeaders,
  createKnowledge,
  updateKnowledgeStatus,
  createApprovalRequest,
  processApproval,
  createIncident,
  createConsultation,
  answerConsultation,
  getNotifications,
  markNotificationRead,
  deleteKnowledge
};
