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
            this.fileListDiv.textContent = '';
            const noFilesDiv = document.createElement('div');
            noFilesDiv.className = 'no-files';
            noFilesDiv.textContent = 'アップロードされたファイルはありません';
            this.fileListDiv.appendChild(noFilesDiv);
            return;
        }

        this.fileListDiv.textContent = '';

        files.forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';

            const fileInfo = document.createElement('div');
            fileInfo.className = 'file-info';

            const fileName = document.createElement('div');
            fileName.className = 'file-name';
            fileName.textContent = file.name;

            const fileMeta = document.createElement('div');
            fileMeta.className = 'file-meta';

            const fileSize = document.createElement('span');
            fileSize.className = 'file-size';
            fileSize.textContent = this.formatFileSize(file.size);

            const fileDate = document.createElement('span');
            fileDate.className = 'file-date';
            fileDate.textContent = new Date(file.uploaded_at).toLocaleString('ja-JP');

            const fileType = document.createElement('span');
            fileType.className = 'file-type';
            fileType.textContent = file.mime_type;

            fileMeta.appendChild(fileSize);
            fileMeta.appendChild(fileDate);
            fileMeta.appendChild(fileType);

            fileInfo.appendChild(fileName);
            fileInfo.appendChild(fileMeta);

            const fileActions = document.createElement('div');
            fileActions.className = 'file-actions';

            const downloadLink = document.createElement('a');
            downloadLink.href = `/api/v1/files/${file.id}`;
            downloadLink.className = 'btn btn-secondary download-link';
            downloadLink.target = '_blank';
            downloadLink.textContent = 'ダウンロード';

            fileActions.appendChild(downloadLink);

            fileItem.appendChild(fileInfo);
            fileItem.appendChild(fileActions);

            this.fileListDiv.appendChild(fileItem);
        });
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
    new FileListManager();
});