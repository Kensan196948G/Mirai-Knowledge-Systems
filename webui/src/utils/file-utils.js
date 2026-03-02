/**
 * @fileoverview ファイルユーティリティ ESMモジュール版
 *
 * MS365ファイルプレビュー・サムネイル取得・ダウンロード機能を提供する。
 * webui/file-preview.js のESモジュール変換版。
 *
 * Features:
 * - Office documents preview (Word/Excel/PowerPoint)
 * - PDF preview with iframe embed
 * - Image preview with direct rendering
 * - Thumbnail generation and caching
 * - Offline preview support (PWA integration)
 * - Performance metrics (Performance API)
 *
 * Security:
 * - XSS prevention (DOM API only, no innerHTML)
 * - CSP compliance (frame-src, img-src)
 * - JWT authentication with token refresh
 * - RBAC permission check
 *
 * @module utils/file-utils
 * @version 2.0.0
 * @author Mirai Knowledge Systems
 */

import { logger } from '../core/logger.js';
import { fetchAPI } from '../core/api-client.js';

// ============================================================
// 定数定義
// ============================================================

/** プレビューキャッシュのキャッシュストア名 */
const PREVIEW_CACHE_NAME = 'mks-previews-v1.4.0';

/** サムネイルキャッシュのキャッシュストア名 */
const THUMBNAIL_CACHE_NAME = 'mks-thumbnails-v1.4.0';

/** Office MIMEタイプ一覧 */
const OFFICE_MIME_TYPES = [
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',    // .docx
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',         // .xlsx
  'application/vnd.openxmlformats-officedocument.presentationml.presentation'  // .pptx
];

// ============================================================
// ファイルタイプ判定ユーティリティ
// ============================================================

/**
 * MIMEタイプからOfficeドキュメントかどうかを判定
 *
 * @param {string} mimeType - MIMEタイプ
 * @returns {boolean} Officeドキュメントの場合 true
 *
 * @example
 * isOfficeDocument('application/vnd.openxmlformats-officedocument.wordprocessingml.document'); // true
 * isOfficeDocument('application/pdf'); // false
 */
export function isOfficeDocument(mimeType) {
  if (!mimeType) return false;
  return OFFICE_MIME_TYPES.some(type => mimeType.includes(type));
}

/**
 * MIMEタイプからPDFかどうかを判定
 *
 * @param {string} mimeType - MIMEタイプ
 * @returns {boolean} PDFの場合 true
 *
 * @example
 * isPdf('application/pdf'); // true
 * isPdf('image/jpeg');      // false
 */
export function isPdf(mimeType) {
  if (!mimeType) return false;
  return mimeType.includes('pdf');
}

/**
 * MIMEタイプから画像かどうかを判定
 *
 * @param {string} mimeType - MIMEタイプ
 * @returns {boolean} 画像の場合 true
 *
 * @example
 * isImage('image/jpeg'); // true
 * isImage('image/png');  // true
 * isImage('text/plain'); // false
 */
export function isImage(mimeType) {
  if (!mimeType) return false;
  return mimeType.startsWith('image/');
}

/**
 * ファイル名から拡張子を取得
 *
 * @param {string} fileName - ファイル名
 * @returns {string} 拡張子（ドット含む、小文字）。拡張子なしの場合は空文字
 *
 * @example
 * getFileExtension('document.pdf');   // '.pdf'
 * getFileExtension('image.JPEG');     // '.jpeg'
 * getFileExtension('no-extension');   // ''
 */
export function getFileExtension(fileName) {
  if (!fileName || typeof fileName !== 'string') return '';
  const lastDot = fileName.lastIndexOf('.');
  if (lastDot === -1 || lastDot === fileName.length - 1) return '';
  return fileName.slice(lastDot).toLowerCase();
}

/**
 * ファイル名からファイルタイプアイコンのテキスト絵文字を取得
 *
 * @param {string} mimeType - MIMEタイプ
 * @returns {string} ファイルタイプを表す絵文字
 *
 * @example
 * getFileTypeEmoji('application/pdf');   // '\uD83D\uDCC4' (ページ絵文字)
 * getFileTypeEmoji('image/jpeg');        // '\uD83D\uDDBC\uFE0F' (フレーム絵文字)
 * getFileTypeEmoji('text/plain');        // '\uD83D\uDCDD' (メモ絵文字)
 */
export function getFileTypeEmoji(mimeType) {
  if (!mimeType) return '\uD83D\uDCC4';

  if (mimeType.includes('pdf')) return '\uD83D\uDCC4';
  if (mimeType.startsWith('image/')) return '\uD83D\uDDBC\uFE0F';
  if (mimeType.includes('wordprocessingml') || mimeType.includes('msword')) return '\uD83D\uDCDD';
  if (mimeType.includes('spreadsheetml') || mimeType.includes('excel')) return '\uD83D\uDCCA';
  if (mimeType.includes('presentationml') || mimeType.includes('powerpoint')) return '\uD83D\uDCCA';
  if (mimeType.startsWith('video/')) return '\uD83C\uDFAC';
  if (mimeType.startsWith('audio/')) return '\uD83C\uDFB5';
  if (mimeType.startsWith('text/')) return '\uD83D\uDCDD';
  if (mimeType.includes('zip') || mimeType.includes('archive')) return '\uD83D\uDDC2\uFE0F';

  return '\uD83D\uDCC4';
}

/**
 * ファイルタイプアイコンをSVGデータURLとして取得（フォールバック用）
 *
 * @param {string} [type='unknown'] - ファイルタイプ
 * @returns {string} SVGデータURL
 */
export function getFileTypeIconDataUrl(type = 'unknown') {
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>';
  return `data:image/svg+xml;base64,${btoa(svg)}`;
}

// ============================================================
// ファイルサイズフォーマット
// ============================================================

/**
 * ファイルサイズをバイト数から人間が読める形式に変換
 *
 * @param {number} bytes - バイト数
 * @returns {string} フォーマットされたファイルサイズ
 *
 * @example
 * formatFileSize(0);           // '0 Bytes'
 * formatFileSize(1024);        // '1 KB'
 * formatFileSize(1536);        // '1.5 KB'
 * formatFileSize(1048576);     // '1 MB'
 */
export function formatFileSize(bytes) {
  if (bytes == null || isNaN(bytes) || bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(k)), sizes.length - 1);
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

// ============================================================
// ブロブ・データURL変換ユーティリティ
// ============================================================

/**
 * BlobをData URLに変換
 *
 * @param {Blob} blob - 変換するBlobオブジェクト
 * @returns {Promise<string>} Data URL
 *
 * @example
 * const dataUrl = await blobToDataUrl(blob);
 * // 'data:image/jpeg;base64,...'
 */
export function blobToDataUrl(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

/**
 * BlobをObjectURLに変換して返す。
 * 使用後は必ず URL.revokeObjectURL() を呼び出すこと。
 *
 * @param {Blob} blob - 変換するBlobオブジェクト
 * @returns {string} ObjectURL
 */
export function blobToObjectUrl(blob) {
  return URL.createObjectURL(blob);
}

// ============================================================
// ファイルプレビューキャッシュ（PWA統合）
// ============================================================

/**
 * プレビューデータをCache APIに保存
 *
 * @param {string} driveId - DriveID
 * @param {string} fileId - FileID
 * @param {Object} previewData - プレビューデータ
 * @returns {Promise<void>}
 */
export async function cachePreviewData(driveId, fileId, previewData) {
  try {
    if (!('caches' in window)) return;
    const cacheKey = `preview_${driveId}_${fileId}`;
    const cache = await caches.open(PREVIEW_CACHE_NAME);
    const response = new Response(JSON.stringify(previewData), {
      headers: { 'Content-Type': 'application/json' }
    });
    await cache.put(cacheKey, response);
    logger.info('[FileUtils] Preview cached:', cacheKey);
  } catch (error) {
    logger.warn('[FileUtils] Cache write failed:', error);
  }
}

/**
 * Cache APIからプレビューデータを取得
 *
 * @param {string} driveId - DriveID
 * @param {string} fileId - FileID
 * @returns {Promise<Object|null>} キャッシュされたプレビューデータ、またはnull
 */
export async function getCachedPreviewData(driveId, fileId) {
  try {
    if (!('caches' in window)) return null;
    const cacheKey = `preview_${driveId}_${fileId}`;
    const cache = await caches.open(PREVIEW_CACHE_NAME);
    const response = await cache.match(cacheKey);
    if (response) {
      logger.info('[FileUtils] Cache hit:', cacheKey);
      return await response.json();
    }
  } catch (error) {
    logger.warn('[FileUtils] Cache read failed:', error);
  }
  return null;
}

/**
 * サムネイルをCache APIに保存
 *
 * @param {string} cacheKey - キャッシュキー
 * @param {string} dataUrl - Data URL
 * @returns {Promise<void>}
 */
export async function cacheThumbnail(cacheKey, dataUrl) {
  try {
    if (!('caches' in window)) return;
    const cache = await caches.open(THUMBNAIL_CACHE_NAME);
    const response = new Response(dataUrl, {
      headers: { 'Content-Type': 'text/plain' }
    });
    await cache.put(cacheKey, response);
    logger.info('[FileUtils] Thumbnail cached:', cacheKey);
  } catch (error) {
    logger.warn('[FileUtils] Thumbnail cache write failed:', error);
  }
}

/**
 * Cache APIからサムネイルを取得
 *
 * @param {string} cacheKey - キャッシュキー
 * @returns {Promise<string|null>} Data URL、またはnull
 */
export async function getCachedThumbnail(cacheKey) {
  try {
    if (!('caches' in window)) return null;
    const cache = await caches.open(THUMBNAIL_CACHE_NAME);
    const response = await cache.match(cacheKey);
    if (response) {
      return await response.text();
    }
  } catch (error) {
    logger.warn('[FileUtils] Thumbnail cache read failed:', error);
  }
  return null;
}

// ============================================================
// FilePreviewManager クラス
// ============================================================

/**
 * File Preview Manager
 *
 * MS365ファイルのプレビュー表示、サムネイル生成、
 * オフラインキャッシュ統合を管理するクラス。
 *
 * @class
 */
export class FilePreviewManager {
  /**
   * @constructor
   */
  constructor() {
    /** API Base URL */
    this.apiBaseUrl = this._getApiBaseUrl();

    /** Cache Manager（PWA統合） */
    this.cacheManager = typeof window !== 'undefined' ? (window.cacheManager || null) : null;

    /** モーダル要素（遅延初期化） */
    this.modal = null;

    /** DOM要素参照 */
    this.elements = {};

    /** 現在表示中のFileID */
    this.currentFileId = null;

    /** 現在表示中のDriveID */
    this.currentDriveId = null;

    /** クローズコールバック */
    this.onCloseCallback = null;

    logger.info('[FilePreviewManager] Initialized');
  }

  /**
   * API Base URLを取得
   * @private
   * @returns {string}
   */
  _getApiBaseUrl() {
    if (typeof window === 'undefined') {
      return 'http://localhost:5200/api/v1/integrations/microsoft365/files';
    }
    const hostname = window.location.hostname;
    const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1';
    if (isLocalhost) {
      return 'http://localhost:5200/api/v1/integrations/microsoft365/files';
    }
    return `${window.location.protocol}//${window.location.host}/api/v1/integrations/microsoft365/files`;
  }

  /**
   * ファイルプレビューモーダルを表示
   *
   * @param {string} driveId - Drive ID
   * @param {string} fileId - File ID
   * @param {Object} [options] - オプション
   * @param {string} [options.fileName] - 表示用ファイル名
   * @param {string} [options.mimeType] - MIMEタイプ
   * @param {Function} [options.onClose] - クローズコールバック
   * @returns {Promise<void>}
   */
  async showPreview(driveId, fileId, options = {}) {
    const perfMark = `preview_${fileId}`;
    performance.mark(`${perfMark}_start`);

    try {
      this.currentDriveId = driveId;
      this.currentFileId = fileId;
      this.onCloseCallback = options.onClose || null;

      // モーダル初期化
      this._initializeModal();

      // モーダル表示・ローディング表示
      this.modal.style.display = 'flex';
      this.elements.loading.style.display = 'block';
      this.elements.container.style.display = 'none';
      this.elements.error.style.display = 'none';

      if (options.fileName) {
        this.elements.fileName.textContent = options.fileName;
      }

      logger.info(`[FilePreviewManager] Fetching preview for file: ${fileId}`);

      // オフラインキャッシュ優先（PWA統合）
      const cachedPreview = await getCachedPreviewData(driveId, fileId);
      if (cachedPreview) {
        logger.info('[FilePreviewManager] Using cached preview (offline mode)');
        await this._renderCachedPreview(cachedPreview);
        performance.mark(`${perfMark}_end`);
        performance.measure(`preview_${fileId}`, `${perfMark}_start`, `${perfMark}_end`);
        return;
      }

      // APIからプレビューURL取得
      const previewData = await this._fetchPreviewUrl(driveId, fileId);

      // ローディング非表示
      this.elements.loading.style.display = 'none';
      this.elements.container.style.display = 'block';

      // プレビュー描画
      await this._renderPreview(previewData, options);

      // キャッシュ保存
      await cachePreviewData(driveId, fileId, previewData);

      // パフォーマンス計測終了
      performance.mark(`${perfMark}_end`);
      performance.measure(`preview_${fileId}`, `${perfMark}_start`, `${perfMark}_end`);
      const measure = performance.getEntriesByName(`preview_${fileId}`)[0];
      logger.info(`[FilePreviewManager] Preview rendered in ${measure.duration.toFixed(2)}ms`);

    } catch (error) {
      logger.error('[FilePreviewManager] Preview error:', error);
      this._handleError(error);
      performance.mark(`${perfMark}_error`);
      performance.measure(`preview_${fileId}_error`, `${perfMark}_start`, `${perfMark}_error`);
    }
  }

  /**
   * サムネイルURLを取得
   *
   * @param {string} driveId - Drive ID
   * @param {string} fileId - File ID
   * @param {string} [size='medium'] - サムネイルサイズ（'small'|'medium'|'large'）
   * @returns {Promise<string>} Data URL
   */
  async getThumbnailUrl(driveId, fileId, size = 'medium') {
    const cacheKey = `thumbnail_${driveId}_${fileId}_${size}`;

    try {
      // キャッシュ確認
      const cached = await getCachedThumbnail(cacheKey);
      if (cached) {
        logger.info(`[FilePreviewManager] Thumbnail cache hit: ${cacheKey}`);
        return cached;
      }

      // APIから取得
      const token = localStorage.getItem('access_token');
      const url = `${this.apiBaseUrl}/${fileId}/thumbnail?drive_id=${encodeURIComponent(driveId)}&size=${size}`;

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        logger.warn(`[FilePreviewManager] Thumbnail fetch failed: ${response.status}`);
        return getFileTypeIconDataUrl('unknown');
      }

      const blob = await response.blob();
      const dataUrl = await blobToDataUrl(blob);

      // キャッシュ保存
      await cacheThumbnail(cacheKey, dataUrl);

      // LRUアクセス記録（PWA統合）
      if (this.cacheManager && typeof this.cacheManager.trackAccess === 'function') {
        await this.cacheManager.trackAccess(cacheKey);
      }

      return dataUrl;

    } catch (error) {
      logger.error('[FilePreviewManager] Thumbnail error:', error);
      return getFileTypeIconDataUrl('unknown');
    }
  }

  /**
   * ファイルをダウンロード
   *
   * @param {string} driveId - Drive ID
   * @param {string} fileId - File ID
   * @param {string} fileName - ファイル名
   * @returns {Promise<void>}
   */
  async downloadFile(driveId, fileId, fileName) {
    try {
      logger.info(`[FilePreviewManager] Downloading file: ${fileName}`);

      const token = localStorage.getItem('access_token');
      const url = `${this.apiBaseUrl}/${fileId}/download?drive_id=${encodeURIComponent(driveId)}`;

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Download failed');
      }

      const blob = await response.blob();

      // ブラウザダウンロード
      const downloadUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(downloadUrl);

      logger.info(`[FilePreviewManager] Downloaded: ${fileName}`);

    } catch (error) {
      logger.error('[FilePreviewManager] Download error:', error);
      // alert は将来的に通知UIに置き換え予定
      alert('ダウンロードに失敗しました。');
    }
  }

  /**
   * プレビューモーダルを閉じる
   */
  closePreview() {
    if (this.modal) {
      this.modal.style.display = 'none';
      // コンテナのクリア（textContent で安全に）
      this.elements.container.textContent = '';

      this.currentFileId = null;
      this.currentDriveId = null;

      if (this.onCloseCallback) {
        this.onCloseCallback();
        this.onCloseCallback = null;
      }
    }
  }

  // ============================================================
  // Private: モーダル初期化
  // ============================================================

  /**
   * モーダルを初期化（遅延初期化）
   * @private
   */
  _initializeModal() {
    if (this.modal) return;

    // モーダルルート
    this.modal = document.createElement('div');
    this.modal.id = 'filePreviewModal';
    this.modal.className = 'file-preview-modal';
    this.modal.style.cssText = [
      'display: none',
      'position: fixed',
      'top: 0',
      'left: 0',
      'width: 100%',
      'height: 100%',
      'background-color: rgba(0, 0, 0, 0.8)',
      'z-index: 10000',
      'align-items: center',
      'justify-content: center'
    ].join(';');

    // モーダルコンテンツ
    const modalContent = document.createElement('div');
    modalContent.className = 'file-preview-content';
    modalContent.style.cssText = [
      'background-color: #fff',
      'border-radius: 8px',
      'width: 90%',
      'height: 90%',
      'max-width: 1200px',
      'display: flex',
      'flex-direction: column',
      'overflow: hidden'
    ].join(';');

    // ヘッダー
    const header = document.createElement('div');
    header.className = 'file-preview-header';
    header.style.cssText = 'padding: 16px 24px; border-bottom: 1px solid #ddd; display: flex; justify-content: space-between; align-items: center;';

    const fileName = document.createElement('h3');
    fileName.className = 'file-preview-title';
    fileName.textContent = 'プレビュー';
    fileName.style.cssText = 'margin: 0; font-size: 18px;';
    this.elements.fileName = fileName;

    const closeBtn = document.createElement('button');
    closeBtn.className = 'file-preview-close';
    closeBtn.textContent = '\u00D7';
    closeBtn.style.cssText = 'background: none; border: none; font-size: 32px; cursor: pointer; padding: 0; line-height: 1;';
    closeBtn.setAttribute('aria-label', 'プレビューを閉じる');
    closeBtn.addEventListener('click', () => this.closePreview());

    header.appendChild(fileName);
    header.appendChild(closeBtn);

    // ローディング
    const loading = document.createElement('div');
    loading.className = 'file-preview-loading';
    loading.style.cssText = 'display: none; text-align: center; padding: 48px;';
    const loadingSpinner = document.createElement('div');
    loadingSpinner.textContent = '読み込み中...';
    loadingSpinner.style.cssText = 'font-size: 18px; color: #666;';
    loading.appendChild(loadingSpinner);
    this.elements.loading = loading;

    // コンテナ
    const container = document.createElement('div');
    container.className = 'file-preview-container';
    container.style.cssText = 'flex: 1; overflow: auto; padding: 24px;';
    this.elements.container = container;

    // エラー
    const error = document.createElement('div');
    error.className = 'file-preview-error';
    error.style.cssText = 'display: none; text-align: center; padding: 48px;';
    const errorText = document.createElement('p');
    errorText.textContent = 'プレビューの表示に失敗しました。';
    errorText.style.cssText = 'color: #dc3545; font-size: 16px;';
    error.appendChild(errorText);
    this.elements.error = error;
    this.elements.errorText = errorText;

    // 組み立て
    modalContent.appendChild(header);
    modalContent.appendChild(loading);
    modalContent.appendChild(container);
    modalContent.appendChild(error);
    this.modal.appendChild(modalContent);
    document.body.appendChild(this.modal);

    logger.info('[FilePreviewManager] Modal initialized');
  }

  // ============================================================
  // Private: API通信
  // ============================================================

  /**
   * APIからプレビューURLを取得
   * @private
   * @param {string} driveId - Drive ID
   * @param {string} fileId - File ID
   * @returns {Promise<Object>} プレビューデータ
   */
  async _fetchPreviewUrl(driveId, fileId) {
    const endpoint = `/api/v1/integrations/microsoft365/files/${fileId}/preview?drive_id=${encodeURIComponent(driveId)}`;

    try {
      const data = await fetchAPI(endpoint);
      if (!data.success) {
        throw new Error(data.error?.message || 'Preview API failed');
      }
      return data.data;
    } catch (error) {
      // 401エラーの場合は認証失敗として再スロー
      if (error.message && error.message.includes('401')) {
        throw new Error('AUTHENTICATION_FAILED');
      }
      throw error;
    }
  }

  // ============================================================
  // Private: プレビュー描画
  // ============================================================

  /**
   * ファイルタイプに応じたプレビューを描画
   * @private
   * @param {Object} previewData - プレビューデータ
   * @param {Object} options - オプション
   */
  async _renderPreview(previewData, options) {
    // 安全にコンテナをクリア
    this.elements.container.textContent = '';

    const { preview_url, download_url, mime_type, file_name, file_size } = previewData;

    if (mime_type && isOfficeDocument(mime_type)) {
      await this._renderOfficePreview(preview_url, file_name);
    } else if (mime_type && isPdf(mime_type)) {
      await this._renderPdfPreview(download_url, file_name);
    } else if (mime_type && isImage(mime_type)) {
      await this._renderImagePreview(download_url, file_name);
    } else {
      await this._renderDownloadPreview(previewData);
    }
  }

  /**
   * Officeドキュメントプレビューを描画
   * @private
   * @param {string} previewUrl - Office Online埋め込みURL
   * @param {string} fileName - ファイル名
   */
  async _renderOfficePreview(previewUrl, fileName) {
    const iframe = document.createElement('iframe');
    iframe.src = previewUrl;
    iframe.style.cssText = 'width: 100%; height: 100%; border: none;';
    iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin');
    iframe.setAttribute('title', fileName || 'Office Document Preview');

    this.elements.container.appendChild(iframe);
    logger.info('[FilePreviewManager] Office preview rendered');
  }

  /**
   * PDFプレビューを描画
   * @private
   * @param {string} downloadUrl - PDF ダウンロードURL
   * @param {string} fileName - ファイル名
   */
  async _renderPdfPreview(downloadUrl, fileName) {
    const embed = document.createElement('embed');
    embed.src = downloadUrl;
    embed.type = 'application/pdf';
    embed.style.cssText = 'width: 100%; height: 100%;';
    embed.setAttribute('title', fileName || 'PDF Preview');

    this.elements.container.appendChild(embed);
    logger.info('[FilePreviewManager] PDF preview rendered');
  }

  /**
   * 画像プレビューを描画
   * @private
   * @param {string} downloadUrl - 画像ダウンロードURL
   * @param {string} fileName - ファイル名
   */
  async _renderImagePreview(downloadUrl, fileName) {
    const img = document.createElement('img');
    img.alt = fileName || 'Image Preview';
    img.style.cssText = 'max-width: 100%; max-height: 100%; display: block; margin: 0 auto;';

    // 認証付きフェッチ
    const token = localStorage.getItem('access_token');
    const response = await fetch(downloadUrl, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      throw new Error('Failed to load image');
    }

    const blob = await response.blob();
    const objectUrl = blobToObjectUrl(blob);
    img.src = objectUrl;

    // 読み込み完了後にObjectURLを解放
    img.addEventListener('load', () => {
      URL.revokeObjectURL(objectUrl);
    });

    this.elements.container.appendChild(img);
    logger.info('[FilePreviewManager] Image preview rendered');
  }

  /**
   * ダウンロードのみのプレビューを描画
   * @private
   * @param {Object} previewData - プレビューデータ
   */
  async _renderDownloadPreview(previewData) {
    const wrapper = document.createElement('div');
    wrapper.style.cssText = 'text-align: center; padding: 48px 24px;';

    const icon = document.createElement('div');
    icon.textContent = getFileTypeEmoji(previewData.mime_type);
    icon.style.fontSize = '64px';

    const fileNameEl = document.createElement('p');
    fileNameEl.textContent = previewData.file_name || 'ファイル';
    fileNameEl.style.cssText = 'font-size: 18px; margin-top: 16px;';

    const fileSizeEl = document.createElement('p');
    fileSizeEl.textContent = formatFileSize(previewData.file_size || 0);
    fileSizeEl.style.cssText = 'color: #666; margin-top: 8px;';

    const message = document.createElement('p');
    message.textContent = 'このファイルはプレビュー表示できません。ダウンロードしてご確認ください。';
    message.style.cssText = 'margin-top: 24px; color: #666;';

    const downloadBtn = document.createElement('button');
    downloadBtn.textContent = 'ダウンロード';
    downloadBtn.className = 'action-btn';
    downloadBtn.style.marginTop = '24px';
    downloadBtn.addEventListener('click', () => {
      this.downloadFile(this.currentDriveId, this.currentFileId, previewData.file_name);
    });

    wrapper.appendChild(icon);
    wrapper.appendChild(fileNameEl);
    wrapper.appendChild(fileSizeEl);
    wrapper.appendChild(message);
    wrapper.appendChild(downloadBtn);

    this.elements.container.appendChild(wrapper);
    logger.info('[FilePreviewManager] Download-only preview rendered');
  }

  /**
   * キャッシュされたプレビューを描画
   * @private
   * @param {Object} cachedData - キャッシュ済みプレビューデータ
   */
  async _renderCachedPreview(cachedData) {
    this.elements.loading.style.display = 'none';
    this.elements.container.style.display = 'block';
    await this._renderPreview(cachedData, {});
  }

  // ============================================================
  // Private: エラーハンドリング
  // ============================================================

  /**
   * エラーを処理して適切なメッセージを表示
   * @private
   * @param {Error} error - エラーオブジェクト
   */
  _handleError(error) {
    this.elements.loading.style.display = 'none';
    this.elements.container.style.display = 'none';
    this.elements.error.style.display = 'block';

    let errorMessage = 'プレビューの表示に失敗しました。';

    if (error.message.includes('NOT_CONFIGURED')) {
      errorMessage = 'Microsoft 365が設定されていません。管理者にお問い合わせください。';
    } else if (error.message.includes('PERMISSION_ERROR')) {
      errorMessage = 'ファイルへのアクセス権限がありません。';
    } else if (error.message.includes('AUTHENTICATION_FAILED')) {
      errorMessage = '認証に失敗しました。再度ログインしてください。';
    } else if (error.message.includes('Network') || error.message.includes('fetch')) {
      errorMessage = 'ネットワークエラーが発生しました。接続を確認してください。';
    }

    this.elements.errorText.textContent = errorMessage;
    logger.error('[FilePreviewManager] Error handled:', errorMessage);
  }
}

// ============================================================
// グローバルインスタンス（シングルトン）
// ============================================================

/** デフォルトのFilePreviewManagerインスタンス */
export const filePreviewManager = new FilePreviewManager();

// ============================================================
// 後方互換性レイヤー - window.FileUtils グローバル公開
// ============================================================
if (typeof window !== 'undefined') {
  window.FileUtils = {
    // クラス
    FilePreviewManager,
    filePreviewManager,

    // ファイルタイプ判定
    isOfficeDocument,
    isPdf,
    isImage,
    getFileExtension,
    getFileTypeEmoji,
    getFileTypeIconDataUrl,

    // フォーマット
    formatFileSize,

    // 変換
    blobToDataUrl,
    blobToObjectUrl,

    // キャッシュ
    cachePreviewData,
    getCachedPreviewData,
    cacheThumbnail,
    getCachedThumbnail
  };

  // 既存コードへの後方互換
  window.FilePreviewManager = FilePreviewManager;
  window.filePreviewManager = filePreviewManager;

  logger.info('[FileUtils] ESM module loaded. FilePreviewManager initialized.');
}
