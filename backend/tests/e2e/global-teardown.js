/**
 * Playwright E2Eテスト グローバルティアダウン
 *
 * テスト終了後のクリーンアップ処理
 */

module.exports = async config => {
  console.log('');
  console.log('E2E tests global teardown...');

  // テストデータのクリーンアップ（必要な場合）
  // 本番環境では実行しない
  if (process.env.CI === 'true') {
    console.log('✓ CI environment - no cleanup needed');
  }

  console.log('Global teardown completed');
};
