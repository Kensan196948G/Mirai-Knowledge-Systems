/**
 * Playwright Global Setup
 * E2Eテスト実行前の初期化処理
 */

module.exports = async () => {
  console.log('Starting E2E tests global setup...');

  // 環境変数の検証
  const requiredEnvVars = ['BASE_URL'];
  const missingEnvVars = requiredEnvVars.filter(envVar => !process.env[envVar]);

  if (missingEnvVars.length > 0) {
    console.warn(`Warning: Missing environment variables: ${missingEnvVars.join(', ')}`);
    console.log('Using default BASE_URL: http://localhost:8000');
  }

  // テスト用データのセットアップ（必要に応じて）
  console.log('Environment:', {
    BASE_URL: process.env.BASE_URL || 'http://localhost:8000',
    CI: process.env.CI || 'false',
    NODE_ENV: process.env.NODE_ENV || 'test'
  });

  console.log('Global setup completed successfully');
};
