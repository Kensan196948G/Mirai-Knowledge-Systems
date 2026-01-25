// ファイルアップロード機能
class FileUploadManager {
    constructor() {
        this.uploadForm = document.getElementById('uploadForm');
        this.fileInput = document.getElementById('file');
        this.statusDiv = document.getElementById('uploadStatus');
        this.init();
    }

    init() {
        this.uploadForm.addEventListener('submit', this.handleUpload.bind(this));
        this.fileInput.addEventListener('change', this.validateFile.bind(this));
    }

    validateFile(event) {
        const file = event.target.files[0];
        if (!file) return;

        // ファイルサイズチェック
        if (file.size > 10 * 1024 * 1024) { // 10MB
            this.showError('ファイルサイズが10MBを超えています');
            event.target.value = '';
            return;
        }

        // ファイルタイプチェック
        const allowedTypes = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'text/plain',
            'image/jpeg',
            'image/png',
            'image/gif'
        ];

        if (!allowedTypes.includes(file.type)) {
            this.showError('許可されていないファイルタイプです');
            event.target.value = '';
            return;
        }

        this.showSuccess('ファイルが選択されました');
    }

    async handleUpload(event) {
        event.preventDefault();

        const formData = new FormData(this.uploadForm);
        const file = formData.get('file');

        if (!file) {
            this.showError('ファイルを選択してください');
            return;
        }

        try {
            this.showInfo('アップロード中...');

            const response = await fetch('/api/v1/files/upload', {
                method: 'POST',
                body: formData,
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess(result.message);
                this.uploadForm.reset();
                // ファイル一覧を更新
                this.refreshFileList();
            } else {
                this.showError(result.message);
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showError('アップロードに失敗しました');
        }
    }

    showSuccess(message) {
        this.statusDiv.className = 'status-message success';
        this.statusDiv.textContent = message;
        this.statusDiv.style.display = 'block';
    }

    showError(message) {
        this.statusDiv.className = 'status-message error';
        this.statusDiv.textContent = message;
        this.statusDiv.style.display = 'block';
    }

    showInfo(message) {
        this.statusDiv.className = 'status-message info';
        this.statusDiv.textContent = message;
        this.statusDiv.style.display = 'block';
    }

    getToken() {
        return localStorage.getItem('jwt_token');
    }

    async refreshFileList() {
        // ファイル一覧ページにリダイレクトするか、リストを更新
        setTimeout(() => {
            window.location.href = '/files.html';
        }, 2000);
    }
}

// 初期化
document.addEventListener('DOMContentLoaded', () => {
    new FileUploadManager();
});