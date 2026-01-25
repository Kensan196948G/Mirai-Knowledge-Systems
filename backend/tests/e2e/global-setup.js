/**
 * Playwright E2Eテスト グローバルセットアップ
 */

const fs = require('fs');
const path = require('path');

module.exports = async config => {
  console.log('Starting E2E tests global setup...');

  const baseURL = process.env.BASE_URL || config.use.baseURL || 'http://localhost:5100';
  console.log(`Environment: { BASE_URL: '${baseURL}', CI: '${process.env.CI || 'false'}', NODE_ENV: '${process.env.NODE_ENV || 'test'}' }`);

  console.log('Global setup completed successfully');
  console.log('');
};
