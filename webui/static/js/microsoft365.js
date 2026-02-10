// Microsoft 365連携管理
class MS365Manager {
    constructor() {
        this.init();
    }

    async init() {
        await this.checkAuthStatus();
    }

    async checkAuthStatus() {
        try {
            const response = await fetch('/api/v1/microsoft365/auth/status', {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });

            const result = await response.json();

            const statusDiv = document.getElementById('authStatus');
            const servicesDiv = document.getElementById('services');

            if (result.success && result.authenticated) {
                statusDiv.textContent = '';

                const statusSuccess = document.createElement('span');
                statusSuccess.className = 'status-success';
                statusSuccess.textContent = '✅ 認証済み';

                const userInfo = document.createElement('div');
                userInfo.className = 'user-info';

                const displayName = document.createElement('strong');
                displayName.textContent = result.user.display_name;

                const br = document.createElement('br');

                const email = document.createTextNode(result.user.email);

                userInfo.appendChild(displayName);
                userInfo.appendChild(br);
                userInfo.appendChild(email);

                statusDiv.appendChild(statusSuccess);
                statusDiv.appendChild(userInfo);

                servicesDiv.textContent = '';
                result.services.forEach(service => {
                    const li = document.createElement('li');
                    li.className = 'service-item';
                    li.textContent = service;
                    servicesDiv.appendChild(li);
                });
            } else {
                statusDiv.textContent = '';

                const statusError = document.createElement('span');
                statusError.className = 'status-error';
                statusError.textContent = '❌ 未認証';

                const errorDetails = document.createElement('div');
                errorDetails.className = 'error-details';
                errorDetails.textContent = result.error || '認証に失敗しました';

                statusDiv.appendChild(statusError);
                statusDiv.appendChild(errorDetails);

                servicesDiv.textContent = '';
                const li = document.createElement('li');
                li.className = 'service-error';
                li.textContent = 'サービス利用不可';
                servicesDiv.appendChild(li);
            }
        } catch (error) {
            console.error('Auth check error:', error);
            const statusDiv = document.getElementById('authStatus');
            statusDiv.textContent = '';
            const statusError = document.createElement('span');
            statusError.className = 'status-error';
            statusError.textContent = '❌ 接続エラー';
            statusDiv.appendChild(statusError);
        }
    }

    getToken() {
        return localStorage.getItem('jwt_token');
    }
}

// 初期化
document.addEventListener('DOMContentLoaded', () => {
    new MS365Manager();
});