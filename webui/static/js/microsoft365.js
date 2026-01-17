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
                statusDiv.innerHTML = `
                    <span class="status-success">✅ 認証済み</span>
                    <div class="user-info">
                        <strong>${result.user.display_name}</strong><br>
                        ${result.user.email}
                    </div>
                `;

                servicesDiv.innerHTML = result.services.map(service =>
                    `<li class="service-item">${service}</li>`
                ).join('');
            } else {
                statusDiv.innerHTML = `
                    <span class="status-error">❌ 未認証</span>
                    <div class="error-details">${result.error || '認証に失敗しました'}</div>
                `;
                servicesDiv.innerHTML = '<li class="service-error">サービス利用不可</li>';
            }
        } catch (error) {
            console.error('Auth check error:', error);
            document.getElementById('authStatus').innerHTML =
                '<span class="status-error">❌ 接続エラー</span>';
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