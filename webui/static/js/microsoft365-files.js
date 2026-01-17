// Microsoft 365ファイル一覧管理
class MS365FileManager {
    constructor() {
        this.currentService = 'onedrive';
        this.currentPath = '/';
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadFiles();
    }

    bindEvents() {
        document.querySelectorAll('.service-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchService(e.target.dataset.service);
            });
        });
    }

    switchService(service) {
        this.currentService = service;
        this.currentPath = '/';
        document.querySelectorAll('.service-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.service === service);
        });
        this.loadFiles();
    }

    async loadFiles() {
        try {
            this.showLoading();

            const response = await fetch(`/api/v1/microsoft365/files?service=${this.currentService}&path=${encodeURIComponent(this.currentPath)}`, {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });

            const result = await response.json();

            if (result.success) {
                this.renderFileList(result.data);
                this.updateBreadcrumb(result.path);
            } else {
                this.showError(result.message);
            }
        } catch (error) {
            console.error('Load files error:', error);
            this.showError('ファイル一覧の取得に失敗しました');
        }
    }

    renderFileList(files) {
        if (files.length === 0) {
            this.fileListDiv.innerHTML = '<div class="no-files">ファイルがありません</div>';
            return;
        }

        const html = files.map(file => `
            <div class="file-item ${file.type}" data-id="${file.id}" data-type="${file.type}">
                <div class="file-icon">
                    ${file.type === 'folder' ? '📁' : '📄'}
                </div>
                <div class="file-info">
                    <div class="file-name">${this.escapeHtml(file.name)}</div>
                    <div class="file-meta">
                        ${file.type === 'file' ? `<span class="file-size">${this.formatFileSize(file.size)}</span>` : ''}
                        <span class="file-date">${new Date(file.last_modified).toLocaleString('ja-JP')}</span>
                    </div>
                </div>
                <div class="file-actions">
                    ${file.type === 'file' ? `<a href="${file.download_url}" class="btn btn-secondary" target="_blank">ダウンロード</a>` : ''}
                    ${file.web_url ? `<a href="${file.web_url}" class="btn btn-secondary" target="_blank">Webで開く</a>` : ''}
                </div>
            </div>
        `).join('');

        this.fileListDiv.innerHTML = html;

        // フォルダクリックイベント
        document.querySelectorAll('.file-item.folder').forEach(item => {
            item.addEventListener('click', () => {
                const folderName = item.querySelector('.file-name').textContent;
                this.navigateToFolder(folderName);
            });
        });
    }

    navigateToFolder(folderName) {
        this.currentPath = this.currentPath === '/' ? `/${folderName}` : `${this.currentPath}/${folderName}`;
        this.loadFiles();
    }

    updateBreadcrumb(path) {
        document.getElementById('currentPath').textContent = path;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showLoading() {
        this.fileListDiv.innerHTML = '<div class="loading">読み込み中...</div>';
    }

    showError(message) {
        this.fileListDiv.innerHTML = `<div class="error-message">${message}</div>`;
    }

    getToken() {
        return localStorage.getItem('jwt_token');
    }
}

// 初期化
document.addEventListener('DOMContentLoaded', () => {
    new MS365FileManager();
});