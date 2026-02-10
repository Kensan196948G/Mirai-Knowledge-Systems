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
            this.fileListDiv.textContent = '';
            const noFilesDiv = document.createElement('div');
            noFilesDiv.className = 'no-files';
            noFilesDiv.textContent = 'ファイルがありません';
            this.fileListDiv.appendChild(noFilesDiv);
            return;
        }

        this.fileListDiv.textContent = '';

        files.forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = `file-item ${file.type}`;
            fileItem.dataset.id = file.id;
            fileItem.dataset.type = file.type;

            const fileIcon = document.createElement('div');
            fileIcon.className = 'file-icon';
            fileIcon.textContent = file.type === 'folder' ? '📁' : '📄';

            const fileInfo = document.createElement('div');
            fileInfo.className = 'file-info';

            const fileName = document.createElement('div');
            fileName.className = 'file-name';
            fileName.textContent = file.name;

            const fileMeta = document.createElement('div');
            fileMeta.className = 'file-meta';

            if (file.type === 'file') {
                const fileSize = document.createElement('span');
                fileSize.className = 'file-size';
                fileSize.textContent = this.formatFileSize(file.size);
                fileMeta.appendChild(fileSize);
            }

            const fileDate = document.createElement('span');
            fileDate.className = 'file-date';
            fileDate.textContent = new Date(file.last_modified).toLocaleString('ja-JP');
            fileMeta.appendChild(fileDate);

            fileInfo.appendChild(fileName);
            fileInfo.appendChild(fileMeta);

            const fileActions = document.createElement('div');
            fileActions.className = 'file-actions';

            if (file.type === 'file') {
                const downloadLink = document.createElement('a');
                downloadLink.href = file.download_url;
                downloadLink.className = 'btn btn-secondary';
                downloadLink.target = '_blank';
                downloadLink.textContent = 'ダウンロード';
                fileActions.appendChild(downloadLink);
            }

            if (file.web_url) {
                const webLink = document.createElement('a');
                webLink.href = file.web_url;
                webLink.className = 'btn btn-secondary';
                webLink.target = '_blank';
                webLink.textContent = 'Webで開く';
                fileActions.appendChild(webLink);
            }

            fileItem.appendChild(fileIcon);
            fileItem.appendChild(fileInfo);
            fileItem.appendChild(fileActions);

            this.fileListDiv.appendChild(fileItem);

            // フォルダクリックイベント
            if (file.type === 'folder') {
                fileItem.addEventListener('click', () => {
                    this.navigateToFolder(file.name);
                });
            }
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
        this.fileListDiv.textContent = '';
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading';
        loadingDiv.textContent = '読み込み中...';
        this.fileListDiv.appendChild(loadingDiv);
    }

    showError(message) {
        this.fileListDiv.textContent = '';
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        this.fileListDiv.appendChild(errorDiv);
    }

    getToken() {
        return localStorage.getItem('jwt_token');
    }
}

// 初期化
document.addEventListener('DOMContentLoaded', () => {
    new MS365FileManager();
});