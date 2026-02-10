/**
 * Logger - セキュアロガー（統一ログ管理）
 *
 * 機能:
 * - 開発環境: console.log出力（デバッグ情報）
 * - 本番環境: console.logを抑制（セキュリティ向上）
 * - warn/errorは常に出力（運用監視用）
 * - ログレベル: debug, info, warn, error
 *
 * @module core/logger
 * @version 1.0.0
 */

/**
 * 環境判定
 * - 開発環境: window.MKS_ENV === 'development' または localhost
 * - 本番環境: 上記以外
 */
const isDevelopment =
  window.MKS_ENV === 'development' ||
  window.location.hostname === 'localhost' ||
  window.location.hostname === '127.0.0.1' ||
  window.location.hostname === '192.168.0.187' ||
  window.location.hostname === '192.168.0.145';

/**
 * セキュアロガーオブジェクト
 */
export const logger = {
  /**
   * デバッグログ（開発環境のみ出力）
   *
   * @param {...any} args - ログ出力する引数
   *
   * @example
   * logger.debug('User data:', userData);
   */
  debug: (...args) => {
    if (isDevelopment) {
      console.log('[DEBUG]', ...args);
    }
  },

  /**
   * 情報ログ（開発環境のみ出力）
   *
   * @param {...any} args - ログ出力する引数
   *
   * @example
   * logger.info('API request completed:', response);
   */
  info: (...args) => {
    if (isDevelopment) {
      console.info('[INFO]', ...args);
    }
  },

  /**
   * 警告ログ（常に出力）
   *
   * @param {...any} args - ログ出力する引数
   *
   * @example
   * logger.warn('Token expiring soon:', expiresAt);
   */
  warn: (...args) => {
    console.warn('[WARN]', ...args);
  },

  /**
   * エラーログ（常に出力）
   *
   * @param {...any} args - ログ出力する引数
   *
   * @example
   * logger.error('API request failed:', error);
   */
  error: (...args) => {
    console.error('[ERROR]', ...args);
  },

  /**
   * グループログ開始（開発環境のみ）
   *
   * @param {string} label - グループラベル
   *
   * @example
   * logger.group('API Request');
   * logger.debug('Endpoint:', endpoint);
   * logger.debug('Options:', options);
   * logger.groupEnd();
   */
  group: (label) => {
    if (isDevelopment) {
      console.group(`[GROUP] ${label}`);
    }
  },

  /**
   * グループログ終了（開発環境のみ）
   */
  groupEnd: () => {
    if (isDevelopment) {
      console.groupEnd();
    }
  },

  /**
   * テーブル形式ログ（開発環境のみ）
   *
   * @param {Object|Array} data - テーブル表示するデータ
   *
   * @example
   * logger.table([
   *   { id: 1, name: 'Alice' },
   *   { id: 2, name: 'Bob' }
   * ]);
   */
  table: (data) => {
    if (isDevelopment) {
      console.table(data);
    }
  },

  /**
   * パフォーマンス計測開始（開発環境のみ）
   *
   * @param {string} label - 計測ラベル
   *
   * @example
   * logger.time('API Request');
   * await fetchAPI('/api/v1/knowledge');
   * logger.timeEnd('API Request');
   */
  time: (label) => {
    if (isDevelopment) {
      console.time(`[TIME] ${label}`);
    }
  },

  /**
   * パフォーマンス計測終了（開発環境のみ）
   *
   * @param {string} label - 計測ラベル
   */
  timeEnd: (label) => {
    if (isDevelopment) {
      console.timeEnd(`[TIME] ${label}`);
    }
  },
};

/**
 * グローバル互換性レイヤー（段階的移行のため）
 * 既存コードが window.logger を期待している場合に対応
 */
if (typeof window !== 'undefined') {
  window.logger = logger;
}

/**
 * 開発環境フラグもエクスポート（他のモジュールで使用可能）
 */
export { isDevelopment };
