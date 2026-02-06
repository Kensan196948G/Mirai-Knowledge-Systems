/**
 * File Preview Manager - MS365 File Preview
 * Mirai Knowledge Systems - Phase E-4
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
 * @version 1.0.0
 * @author Claude AI (code-implementer)
 */

// Logger
const logger = window.logger || console;

/**
 * File Preview Manager
 *
 * Manages MS365 file preview display, thumbnail generation,
 * and offline caching integration with PWA infrastructure.
 */
class FilePreviewManager {
  /**
   * Constructor
   */
  constructor() {
    // API Base URL
    this.apiBaseUrl = this._getApiBaseUrl();

    // Cache Manager (PWA integration)
    this.cacheManager = window.cacheManager || null;

    // Modal elements (lazy initialization)
    this.modal = null;
    this.elements = {};

    // State
    this.currentFileId = null;
    this.currentDriveId = null;
    this.onCloseCallback = null;

    // Performance metrics
    this.performanceMarks = {};

    logger.log('[FilePreviewManager] Initialized');
  }

  /**
   * Get API Base URL
   * @private
   * @returns {string}
   */
  _getApiBaseUrl() {
    const hostname = window.location.hostname;
    const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1';

    if (isLocalhost) {
      return 'http://localhost:5200/api/v1/integrations/microsoft365/files';
    }

    return `${window.location.protocol}//${window.location.host}/api/v1/integrations/microsoft365/files`;
  }

  /**
   * Show file preview modal
   *
   * @param {string} driveId - Drive ID
   * @param {string} fileId - File ID
   * @param {Object} options - Options
   * @param {string} options.fileName - File name for display
   * @param {string} options.mimeType - MIME type
   * @param {Function} options.onClose - Close callback
   * @returns {Promise<void>}
   */
  async showPreview(driveId, fileId, options = {}) {
    // Performance tracking start
    const perfMark = `preview_${fileId}`;
    performance.mark(`${perfMark}_start`);

    try {
      this.currentDriveId = driveId;
      this.currentFileId = fileId;
      this.onCloseCallback = options.onClose;

      // Initialize modal
      this._initializeModal();

      // Show modal
      this.modal.style.display = 'flex';

      // Show loading
      this.elements.loading.style.display = 'block';
      this.elements.container.style.display = 'none';
      this.elements.error.style.display = 'none';

      // Set file name
      if (options.fileName) {
        this.elements.fileName.textContent = options.fileName;
      }

      logger.log(`[FilePreviewManager] Fetching preview for file: ${fileId}`);

      // Try offline cache first (PWA integration - Concern #4)
      const cachedPreview = await this._getFromCache(driveId, fileId);
      if (cachedPreview) {
        logger.log('[FilePreviewManager] Using cached preview (offline mode)');
        await this._renderCachedPreview(cachedPreview);
        performance.mark(`${perfMark}_end`);
        performance.measure(`preview_${fileId}`, `${perfMark}_start`, `${perfMark}_end`);
        return;
      }

      // Fetch preview URL from API
      const previewData = await this._fetchPreviewUrl(driveId, fileId);

      // Hide loading
      this.elements.loading.style.display = 'none';
      this.elements.container.style.display = 'block';

      // Render preview based on file type
      await this._renderPreview(previewData, options);

      // Cache preview for offline use
      await this._cachePreview(driveId, fileId, previewData);

      // Performance tracking end (Concern #5)
      performance.mark(`${perfMark}_end`);
      performance.measure(`preview_${fileId}`, `${perfMark}_start`, `${perfMark}_end`);

      const measure = performance.getEntriesByName(`preview_${fileId}`)[0];
      logger.log(`[FilePreviewManager] Preview rendered in ${measure.duration.toFixed(2)}ms`);

    } catch (error) {
      logger.error('[FilePreviewManager] Preview error:', error);
      this._handleError(error);

      performance.mark(`${perfMark}_error`);
      performance.measure(`preview_${fileId}_error`, `${perfMark}_start`, `${perfMark}_error`);
    }
  }

  /**
   * Get thumbnail URL
   *
   * @param {string} driveId - Drive ID
   * @param {string} fileId - File ID
   * @param {string} size - Thumbnail size ("small" | "medium" | "large")
   * @returns {Promise<string>} - Data URL
   */
  async getThumbnailUrl(driveId, fileId, size = 'medium') {
    const cacheKey = `thumbnail_${driveId}_${fileId}_${size}`;

    try {
      // Check cache
      const cached = await this._getCachedThumbnail(cacheKey);
      if (cached) {
        logger.log(`[FilePreviewManager] Thumbnail cache hit: ${cacheKey}`);
        return cached;
      }

      // Fetch from API
      const url = `${this.apiBaseUrl}/${fileId}/thumbnail?drive_id=${encodeURIComponent(driveId)}&size=${size}`;

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (!response.ok) {
        logger.warn(`[FilePreviewManager] Thumbnail fetch failed: ${response.status}`);
        return this._getFileTypeIcon('unknown');
      }

      const blob = await response.blob();
      const dataUrl = await this._blobToDataUrl(blob);

      // Cache thumbnail
      await this._cacheThumbnail(cacheKey, dataUrl);

      // Track cache access (LRU - PWA integration)
      if (this.cacheManager) {
        await this.cacheManager.trackAccess(cacheKey);
      }

      return dataUrl;

    } catch (error) {
      logger.error('[FilePreviewManager] Thumbnail error:', error);
      return this._getFileTypeIcon('unknown');
    }
  }

  /**
   * Download file
   *
   * @param {string} driveId - Drive ID
   * @param {string} fileId - File ID
   * @param {string} fileName - File name
   * @returns {Promise<void>}
   */
  async downloadFile(driveId, fileId, fileName) {
    try {
      logger.log(`[FilePreviewManager] Downloading file: ${fileName}`);

      const url = `${this.apiBaseUrl}/${fileId}/download?drive_id=${encodeURIComponent(driveId)}`;

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Download failed');
      }

      const blob = await response.blob();

      // Browser download
      const downloadUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(downloadUrl);

      logger.log(`[FilePreviewManager] Downloaded: ${fileName}`);

    } catch (error) {
      logger.error('[FilePreviewManager] Download error:', error);
      alert('ダウンロードに失敗しました。');
    }
  }

  /**
   * Close preview modal
   */
  closePreview() {
    if (this.modal) {
      this.modal.style.display = 'none';
      this.elements.container.textContent = '';

      // Reset state
      this.currentFileId = null;
      this.currentDriveId = null;

      // Execute callback
      if (this.onCloseCallback) {
        this.onCloseCallback();
        this.onCloseCallback = null;
      }
    }
  }

  // ============================================================
  // Private Methods: Modal Initialization
  // ============================================================

  /**
   * Initialize modal (lazy initialization)
   * @private
   */
  _initializeModal() {
    if (this.modal) return;

    // Create modal structure
    this.modal = document.createElement('div');
    this.modal.id = 'filePreviewModal';
    this.modal.className = 'file-preview-modal';
    this.modal.style.display = 'none';
    this.modal.style.position = 'fixed';
    this.modal.style.top = '0';
    this.modal.style.left = '0';
    this.modal.style.width = '100%';
    this.modal.style.height = '100%';
    this.modal.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
    this.modal.style.zIndex = '10000';
    this.modal.style.display = 'flex';
    this.modal.style.alignItems = 'center';
    this.modal.style.justifyContent = 'center';

    // Modal content
    const modalContent = document.createElement('div');
    modalContent.className = 'file-preview-content';
    modalContent.style.backgroundColor = '#fff';
    modalContent.style.borderRadius = '8px';
    modalContent.style.width = '90%';
    modalContent.style.height = '90%';
    modalContent.style.maxWidth = '1200px';
    modalContent.style.display = 'flex';
    modalContent.style.flexDirection = 'column';
    modalContent.style.overflow = 'hidden';

    // Header
    const header = document.createElement('div');
    header.className = 'file-preview-header';
    header.style.padding = '16px 24px';
    header.style.borderBottom = '1px solid #ddd';
    header.style.display = 'flex';
    header.style.justifyContent = 'space-between';
    header.style.alignItems = 'center';

    const fileName = document.createElement('h3');
    fileName.className = 'file-preview-title';
    fileName.textContent = 'プレビュー';
    fileName.style.margin = '0';
    fileName.style.fontSize = '18px';
    this.elements.fileName = fileName;

    const closeBtn = document.createElement('button');
    closeBtn.className = 'file-preview-close';
    closeBtn.textContent = '×';
    closeBtn.style.background = 'none';
    closeBtn.style.border = 'none';
    closeBtn.style.fontSize = '32px';
    closeBtn.style.cursor = 'pointer';
    closeBtn.style.padding = '0';
    closeBtn.style.lineHeight = '1';
    closeBtn.addEventListener('click', () => this.closePreview());

    header.appendChild(fileName);
    header.appendChild(closeBtn);

    // Loading indicator
    const loading = document.createElement('div');
    loading.className = 'file-preview-loading';
    loading.style.display = 'none';
    loading.style.textAlign = 'center';
    loading.style.padding = '48px';

    const loadingSpinner = document.createElement('div');
    loadingSpinner.textContent = '読み込み中...';
    loadingSpinner.style.fontSize = '18px';
    loadingSpinner.style.color = '#666';
    loading.appendChild(loadingSpinner);
    this.elements.loading = loading;

    // Container
    const container = document.createElement('div');
    container.className = 'file-preview-container';
    container.style.flex = '1';
    container.style.overflow = 'auto';
    container.style.padding = '24px';
    this.elements.container = container;

    // Error
    const error = document.createElement('div');
    error.className = 'file-preview-error';
    error.style.display = 'none';
    error.style.textAlign = 'center';
    error.style.padding = '48px';

    const errorText = document.createElement('p');
    errorText.textContent = 'プレビューの表示に失敗しました。';
    errorText.style.color = '#dc3545';
    errorText.style.fontSize = '16px';
    error.appendChild(errorText);
    this.elements.error = error;
    this.elements.errorText = errorText;

    // Assemble modal
    modalContent.appendChild(header);
    modalContent.appendChild(loading);
    modalContent.appendChild(container);
    modalContent.appendChild(error);
    this.modal.appendChild(modalContent);

    // Append to body
    document.body.appendChild(this.modal);

    logger.log('[FilePreviewManager] Modal initialized');
  }

  // ============================================================
  // Private Methods: API Communication
  // ============================================================

  /**
   * Fetch preview URL from API
   * @private
   * @param {string} driveId - Drive ID
   * @param {string} fileId - File ID
   * @returns {Promise<Object>} - Preview data
   */
  async _fetchPreviewUrl(driveId, fileId) {
    const url = `${this.apiBaseUrl}/${fileId}/preview?drive_id=${encodeURIComponent(driveId)}`;

    let response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json'
      }
    });

    // Token refresh (Concern #1: app.js integration)
    if (response.status === 401) {
      logger.log('[FilePreviewManager] 401 Unauthorized, attempting token refresh...');

      // Use app.js refreshAccessToken function
      if (typeof window.refreshAccessToken === 'function') {
        const refreshed = await window.refreshAccessToken();

        if (refreshed) {
          logger.log('[FilePreviewManager] Token refreshed, retrying request...');
          const newToken = localStorage.getItem('access_token');

          response = await fetch(url, {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${newToken}`,
              'Content-Type': 'application/json'
            }
          });
        } else {
          throw new Error('AUTHENTICATION_FAILED');
        }
      } else {
        logger.warn('[FilePreviewManager] refreshAccessToken not found in window');
        throw new Error('AUTHENTICATION_FAILED');
      }
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error?.message || `HTTP ${response.status}`);
    }

    const data = await response.json();

    if (!data.success) {
      throw new Error(data.error?.message || 'Preview API failed');
    }

    return data.data;
  }

  // ============================================================
  // Private Methods: Rendering
  // ============================================================

  /**
   * Render preview based on file type
   * @private
   * @param {Object} previewData - Preview data from API
   * @param {Object} options - Options
   */
  async _renderPreview(previewData, options) {
    this.elements.container.textContent = '';

    const { preview_url, download_url, mime_type, file_name, file_size } = previewData;

    // Office documents (Word/Excel/PowerPoint)
    if (mime_type && this._isOfficeDocument(mime_type)) {
      await this._renderOfficePreview(preview_url, file_name);
    }
    // PDF
    else if (mime_type && mime_type.includes('pdf')) {
      await this._renderPdfPreview(download_url, file_name);
    }
    // Images
    else if (mime_type && mime_type.startsWith('image/')) {
      await this._renderImagePreview(download_url, file_name);
    }
    // Download-only
    else {
      await this._renderDownloadPreview(previewData);
    }
  }

  /**
   * Check if file is Office document
   * @private
   * @param {string} mimeType - MIME type
   * @returns {boolean}
   */
  _isOfficeDocument(mimeType) {
    const officeTypes = [
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',      // .xlsx
      'application/vnd.openxmlformats-officedocument.presentationml.presentation' // .pptx
    ];
    return officeTypes.some(type => mimeType.includes(type));
  }

  /**
   * Render Office document preview
   * @private
   * @param {string} previewUrl - Office Online embed URL
   * @param {string} fileName - File name
   */
  async _renderOfficePreview(previewUrl, fileName) {
    const iframe = document.createElement('iframe');
    iframe.src = previewUrl;
    iframe.style.width = '100%';
    iframe.style.height = '100%';
    iframe.style.border = 'none';
    iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin');
    iframe.setAttribute('title', fileName || 'Office Document Preview');

    this.elements.container.appendChild(iframe);

    logger.log('[FilePreviewManager] Office preview rendered');
  }

  /**
   * Render PDF preview
   * @private
   * @param {string} downloadUrl - PDF download URL
   * @param {string} fileName - File name
   */
  async _renderPdfPreview(downloadUrl, fileName) {
    const embed = document.createElement('embed');
    embed.src = downloadUrl;
    embed.type = 'application/pdf';
    embed.style.width = '100%';
    embed.style.height = '100%';
    embed.setAttribute('title', fileName || 'PDF Preview');

    this.elements.container.appendChild(embed);

    logger.log('[FilePreviewManager] PDF preview rendered');
  }

  /**
   * Render image preview
   * @private
   * @param {string} downloadUrl - Image download URL
   * @param {string} fileName - File name
   */
  async _renderImagePreview(downloadUrl, fileName) {
    const img = document.createElement('img');
    img.alt = fileName || 'Image Preview';
    img.style.maxWidth = '100%';
    img.style.maxHeight = '100%';
    img.style.display = 'block';
    img.style.margin = '0 auto';

    // Fetch image with authentication
    const response = await fetch(downloadUrl, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });

    if (!response.ok) {
      throw new Error('Failed to load image');
    }

    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    img.src = objectUrl;

    // Cleanup
    img.addEventListener('load', () => {
      URL.revokeObjectURL(objectUrl);
    });

    this.elements.container.appendChild(img);

    logger.log('[FilePreviewManager] Image preview rendered');
  }

  /**
   * Render download-only preview
   * @private
   * @param {Object} previewData - Preview data
   */
  async _renderDownloadPreview(previewData) {
    const wrapper = document.createElement('div');
    wrapper.style.textAlign = 'center';
    wrapper.style.padding = '48px 24px';

    const icon = document.createElement('div');
    icon.textContent = '📄';
    icon.style.fontSize = '64px';

    const fileNameEl = document.createElement('p');
    fileNameEl.textContent = previewData.file_name || 'ファイル';
    fileNameEl.style.fontSize = '18px';
    fileNameEl.style.marginTop = '16px';

    const fileSizeEl = document.createElement('p');
    fileSizeEl.textContent = this._formatFileSize(previewData.file_size || 0);
    fileSizeEl.style.color = '#666';
    fileSizeEl.style.marginTop = '8px';

    const message = document.createElement('p');
    message.textContent = 'このファイルはプレビュー表示できません。ダウンロードしてご確認ください。';
    message.style.marginTop = '24px';
    message.style.color = '#666';

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

    logger.log('[FilePreviewManager] Download-only preview rendered');
  }

  // ============================================================
  // Private Methods: Offline Support (PWA Integration - Concern #4)
  // ============================================================

  /**
   * Get preview from cache (offline support)
   * @private
   * @param {string} driveId - Drive ID
   * @param {string} fileId - File ID
   * @returns {Promise<Object|null>}
   */
  async _getFromCache(driveId, fileId) {
    try {
      const cacheKey = `preview_${driveId}_${fileId}`;
      const cache = await caches.open('mks-previews-v1.4.0');
      const response = await cache.match(cacheKey);

      if (response) {
        const data = await response.json();
        logger.log('[FilePreviewManager] Cache hit:', cacheKey);
        return data;
      }
    } catch (error) {
      logger.warn('[FilePreviewManager] Cache read failed:', error);
    }
    return null;
  }

  /**
   * Render cached preview
   * @private
   * @param {Object} cachedData - Cached preview data
   */
  async _renderCachedPreview(cachedData) {
    this.elements.loading.style.display = 'none';
    this.elements.container.style.display = 'block';

    await this._renderPreview(cachedData, {});
  }

  /**
   * Cache preview for offline use
   * @private
   * @param {string} driveId - Drive ID
   * @param {string} fileId - File ID
   * @param {Object} previewData - Preview data
   */
  async _cachePreview(driveId, fileId, previewData) {
    try {
      const cacheKey = `preview_${driveId}_${fileId}`;
      const cache = await caches.open('mks-previews-v1.4.0');
      const response = new Response(JSON.stringify(previewData), {
        headers: { 'Content-Type': 'application/json' }
      });
      await cache.put(cacheKey, response);

      logger.log('[FilePreviewManager] Preview cached:', cacheKey);
    } catch (error) {
      logger.warn('[FilePreviewManager] Cache write failed:', error);
    }
  }

  /**
   * Get cached thumbnail
   * @private
   * @param {string} cacheKey - Cache key
   * @returns {Promise<string|null>}
   */
  async _getCachedThumbnail(cacheKey) {
    try {
      const cache = await caches.open('mks-thumbnails-v1.4.0');
      const response = await cache.match(cacheKey);
      if (response) {
        return await response.text();
      }
    } catch (error) {
      logger.warn('[FilePreviewManager] Thumbnail cache read failed:', error);
    }
    return null;
  }

  /**
   * Cache thumbnail
   * @private
   * @param {string} cacheKey - Cache key
   * @param {string} dataUrl - Data URL
   */
  async _cacheThumbnail(cacheKey, dataUrl) {
    try {
      const cache = await caches.open('mks-thumbnails-v1.4.0');
      const response = new Response(dataUrl, {
        headers: { 'Content-Type': 'text/plain' }
      });
      await cache.put(cacheKey, response);

      logger.log('[FilePreviewManager] Thumbnail cached:', cacheKey);
    } catch (error) {
      logger.warn('[FilePreviewManager] Thumbnail cache write failed:', error);
    }
  }

  // ============================================================
  // Private Methods: Error Handling
  // ============================================================

  /**
   * Handle error
   * @private
   * @param {Error} error - Error object
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

  // ============================================================
  // Private Methods: Utilities
  // ============================================================

  /**
   * Blob to Data URL
   * @private
   * @param {Blob} blob - Blob object
   * @returns {Promise<string>}
   */
  async _blobToDataUrl(blob) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  /**
   * Format file size
   * @private
   * @param {number} bytes - File size in bytes
   * @returns {string}
   */
  _formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }

  /**
   * Get file type icon (Data URL fallback)
   * @private
   * @param {string} type - File type
   * @returns {string} - Data URL
   */
  _getFileTypeIcon(type) {
    // Simple SVG icon as Data URL
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>`;
    return `data:image/svg+xml;base64,${btoa(svg)}`;
  }
}

// Global instance
const filePreviewManager = new FilePreviewManager();

// Export (ES Module support)
if (typeof window !== 'undefined') {
  window.FilePreviewManager = FilePreviewManager;
  window.filePreviewManager = filePreviewManager;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { FilePreviewManager, filePreviewManager };
}

logger.log('[FilePreviewManager] Module loaded');
