// ファイル一覧管理
class FileListManager {
    constructor() {
        this.fileListDiv = document.getElementById('fileList');
        this.init();
    }

    init() {
        this.loadFiles();
    }

    async loadFiles() {
        try {
            const response = await fetch('/api/v1/files', {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });

            const result = await response.json();

            if (result.success) {
                this.renderFileList(result.data);
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
            this.fileListDiv.innerHTML = '<div class="no-files">アップロードされたファイルはありません</div>';
            return;
        }

        const html = files.map(file => `
            <div class="file-item">
                <div class="file-info">
                    <div class="file-name">${this.escapeHtml(file.name)}</div>
                    <div class="file-meta">
                        <span class="file-size">${this.formatFileSize(file.size)}</span>
                        <span class="file-date">${new Date(file.uploaded_at).toLocaleString('ja-JP')}</span>
                        <span class="file-type">${file.mime_type}</span>
                    </div>
                </div>
                <div class="file-actions">
                    <a href="/api/v1/files/${file.id}" class="btn btn-secondary download-link" target="_blank">ダウンロード</a>
                </div>
            </div>
        `).join('');

        this.fileListDiv.innerHTML = html;
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

    showError(message) {
        this.fileListDiv.innerHTML = `<div class="error-message">${message}</div>`;
    }

    getToken() {
        return localStorage.getItem('jwt_token');
    }
}

// 初期化
document.addEventListener('DOMContentLoaded', () => {
    new FileListManager();
});