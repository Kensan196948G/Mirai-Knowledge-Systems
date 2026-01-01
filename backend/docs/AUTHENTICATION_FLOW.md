# 認証・認可フロードキュメント

## 目次

1. [認証フロー概要](#認証フロー概要)
2. [JWT トークン仕様](#jwtトークン仕様)
3. [認証シーケンス](#認証シーケンス)
4. [権限管理（RBAC）](#権限管理rbac)
5. [セキュリティ考慮事項](#セキュリティ考慮事項)

---

## 認証フロー概要

Mirai Knowledge Systemは、JWT（JSON Web Token）ベースの認証を使用しています。

### 基本フロー

```
1. クライアント: ユーザー名・パスワードでログイン
   ↓
2. サーバー: 認証情報を検証
   ↓
3. サーバー: Access Token + Refresh Token を生成
   ↓
4. クライアント: Access Token を保存
   ↓
5. クライアント: 各API呼び出しにAccess Tokenを含める
   ↓
6. サーバー: トークンを検証し、リソースへのアクセスを許可
   ↓
7. Access Token期限切れ時: Refresh Tokenで新しいAccess Tokenを取得
```

---

## JWT トークン仕様

### Access Token

- **有効期限**: 1時間（3600秒）
- **用途**: API呼び出しの認証
- **含まれる情報**:
  - `sub` (subject): ユーザーID
  - `roles`: ユーザーのロールリスト
  - `exp` (expiration): 有効期限（Unixタイムスタンプ）
  - `iat` (issued at): 発行時刻

**ペイロード例:**

```json
{
  "sub": "1",
  "roles": ["admin"],
  "exp": 1704110400,
  "iat": 1704106800
}
```

### Refresh Token

- **有効期限**: 30日
- **用途**: Access Tokenの更新
- **含まれる情報**:
  - `sub` (subject): ユーザーID
  - `exp` (expiration): 有効期限

**ペイロード例:**

```json
{
  "sub": "1",
  "exp": 1706698800,
  "iat": 1704106800
}
```

### トークン形式

```
Authorization: Bearer <token>
```

**例:**

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwicm9sZXMiOlsiYWRtaW4iXSwiZXhwIjoxNzA0MTEwNDAwfQ.abc123...
```

---

## 認証シーケンス

### 1. 初回ログイン

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Auth
    participant Database

    Client->>API: POST /api/v1/auth/login
    Note right of Client: {username, password}

    API->>Database: ユーザー検索
    Database-->>API: ユーザー情報

    API->>Auth: パスワード検証
    Auth-->>API: 検証成功

    API->>Auth: Access Token生成
    Auth-->>API: Access Token

    API->>Auth: Refresh Token生成
    Auth-->>API: Refresh Token

    API->>Database: ログイン記録保存

    API-->>Client: トークン返却
    Note left of API: {access_token, refresh_token, user}
```

**リクエスト例:**

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**レスポンス例:**

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "full_name": "管理者",
      "roles": ["admin"]
    }
  }
}
```

### 2. API呼び出し（認証済み）

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Auth
    participant Database

    Client->>API: GET /api/v1/knowledge
    Note right of Client: Authorization: Bearer <access_token>

    API->>Auth: トークン検証
    Auth-->>API: 検証成功 + ユーザー情報

    API->>Auth: 権限チェック
    Auth-->>API: 権限あり

    API->>Database: ナレッジ取得
    Database-->>API: ナレッジリスト

    API-->>Client: ナレッジ返却
    Note left of API: {success: true, data: [...]}
```

### 3. トークンリフレッシュ

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Auth

    Note over Client: Access Token期限切れ

    Client->>API: POST /api/v1/auth/refresh
    Note right of Client: Authorization: Bearer <refresh_token>

    API->>Auth: Refresh Token検証
    Auth-->>API: 検証成功

    API->>Auth: 新しいAccess Token生成
    Auth-->>API: Access Token

    API-->>Client: 新しいトークン返却
    Note left of API: {access_token, expires_in}

    Note over Client: 新しいAccess Tokenで再試行
    Client->>API: GET /api/v1/knowledge
    Note right of Client: Authorization: Bearer <new_access_token>
```

**リクエスト例:**

```bash
POST /api/v1/auth/refresh
Authorization: Bearer <refresh_token>
```

**レスポンス例:**

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600
  }
}
```

### 4. エラーハンドリング

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Auth

    Client->>API: GET /api/v1/knowledge
    Note right of Client: Authorization: Bearer <expired_token>

    API->>Auth: トークン検証
    Auth-->>API: 期限切れエラー

    API-->>Client: 401 Unauthorized
    Note left of API: {error: "TOKEN_EXPIRED"}

    Client->>API: POST /api/v1/auth/refresh
    Note right of Client: Refresh Tokenで更新

    API->>Auth: Refresh Token検証
    Auth-->>API: 検証成功

    API-->>Client: 新しいAccess Token

    Client->>API: GET /api/v1/knowledge
    Note right of Client: 新しいトークンで再試行

    API-->>Client: 200 OK
```

---

## 権限管理（RBAC）

### ロール定義

| ロール | 権限スコープ | 主な用途 |
|-------|-------------|---------|
| **admin** | 全権限 (`*`) | システム管理者 |
| **construction_manager** | knowledge.*, incident.*, consultation.create | 施工管理者 |
| **quality_assurance** | knowledge.approve, sop.*, approval.execute | 品質管理者 |
| **safety_officer** | knowledge.read, incident.*, sop.read | 安全衛生管理者 |
| **partner_company** | knowledge.read, sop.read, incident.read | 協力会社 |

### 権限マトリクス

| リソース | admin | construction_manager | quality_assurance | safety_officer | partner_company |
|---------|-------|---------------------|-------------------|----------------|-----------------|
| **ナレッジ** |
| - 作成 | ✓ | ✓ | - | - | - |
| - 閲覧 | ✓ | ✓ | ✓ | ✓ | ✓ |
| - 更新 | ✓ | ✓ | - | - | - |
| - 削除 | ✓ | - | - | - | - |
| - 承認 | ✓ | - | ✓ | - | - |
| **SOP** |
| - 作成 | ✓ | - | ✓ | - | - |
| - 閲覧 | ✓ | ✓ | ✓ | ✓ | ✓ |
| - 更新 | ✓ | - | ✓ | - | - |
| **事故レポート** |
| - 作成 | ✓ | ✓ | - | ✓ | - |
| - 閲覧 | ✓ | ✓ | ✓ | ✓ | ✓ |
| - 更新 | ✓ | - | - | ✓ | - |
| **承認フロー** |
| - 申請 | ✓ | ✓ | - | - | - |
| - 承認実行 | ✓ | - | ✓ | - | - |

### 権限チェックフロー

```mermaid
flowchart TD
    A[API リクエスト] --> B{認証済み?}
    B -->|No| C[401 Unauthorized]
    B -->|Yes| D[ユーザー情報取得]
    D --> E[ロール取得]
    E --> F{admin ロール?}
    F -->|Yes| G[アクセス許可]
    F -->|No| H{必要な権限を持つ?}
    H -->|Yes| G
    H -->|No| I[403 Forbidden]
    G --> J[リソースへアクセス]
```

### 権限チェック実装例

**サーバー側（app_v2.py）:**

```python
@app.route('/api/v1/knowledge', methods=['POST'])
@check_permission('knowledge.create')
def create_knowledge():
    """新規ナレッジ作成（knowledge.create権限が必要）"""
    # 実装...
```

**デコレータ内部:**

```python
def check_permission(required_permission):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = get_user_by_id(current_user_id)
            permissions = get_user_permissions(user)

            # 管理者または必要な権限を持っている
            if '*' in permissions or required_permission in permissions:
                return fn(*args, **kwargs)

            return jsonify({
                'success': False,
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'Insufficient permissions'
                }
            }), 403
        return wrapper
    return decorator
```

---

## セキュリティ考慮事項

### 1. トークンの安全な保存

#### ✅ 推奨

**ブラウザアプリケーション:**
- `localStorage`または`sessionStorage`にトークンを保存
- XSS対策として、HTMLエスケープを実施
- HTTPS通信を必須化

**モバイルアプリケーション:**
- Keychain（iOS）またはKeystore（Android）にトークンを保存
- ルート化/脱獄デバイスでの動作を制限

**サーバーサイドアプリケーション:**
- 環境変数または秘密管理サービス（AWS Secrets Manager等）に保存

#### ❌ 非推奨

```javascript
// トークンをURLパラメータに含める（ログに記録される危険性）
fetch('https://api.example.com/data?token=' + accessToken)

// トークンをCookieに保存（CSRF攻撃のリスク）
document.cookie = `token=${accessToken}`

// トークンをコードにハードコーディング
const TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 2. トークンのライフサイクル管理

```javascript
class TokenManager {
  constructor() {
    this.accessToken = null;
    this.refreshToken = null;
    this.expiresAt = null;
  }

  setTokens(accessToken, refreshToken, expiresIn) {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    this.expiresAt = Date.now() + (expiresIn * 1000);

    // セキュアストレージに保存
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    localStorage.setItem('expires_at', this.expiresAt);
  }

  isTokenExpired() {
    return Date.now() >= this.expiresAt - 60000; // 1分前にリフレッシュ
  }

  async getValidToken() {
    if (this.isTokenExpired()) {
      await this.refreshAccessToken();
    }
    return this.accessToken;
  }

  async refreshAccessToken() {
    const response = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.refreshToken}`
      }
    });

    const data = await response.json();
    this.setTokens(data.data.access_token, this.refreshToken, data.data.expires_in);
  }

  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    this.expiresAt = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('expires_at');
  }
}
```

### 3. パスワードセキュリティ

**サーバー側:**
- bcryptによるハッシュ化（コストファクター: 12）
- ソルトの自動生成
- レインボーテーブル攻撃対策

```python
import bcrypt

def hash_password(password):
    """パスワードをbcryptでハッシュ化"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, password_hash):
    """パスワードを検証"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
```

**クライアント側:**
- パスワードの平文送信（HTTPS必須）
- パスワードのローカル保存禁止
- パスワード強度チェック

### 4. レート制限

**ログインエンドポイント:**
- 5リクエスト/分
- 20リクエスト/時

**その他のエンドポイント:**
- 1000リクエスト/分
- 10000リクエスト/時

**レート制限超過時の対応:**

```python
@app.errorhandler(429)
def ratelimit_handler(error):
    return jsonify({
        'success': False,
        'error': {
            'code': 'RATE_LIMIT_EXCEEDED',
            'message': 'リクエストが多すぎます。しばらく待ってから再試行してください。',
            'details': {'retry_after': '60 seconds'}
        }
    }), 429
```

### 5. HTTPS強制

**本番環境:**
- HTTPS通信の強制
- HSTS（HTTP Strict Transport Security）の有効化

```python
# 環境変数設定
MKS_FORCE_HTTPS=true
MKS_HSTS_ENABLED=true
MKS_HSTS_MAX_AGE=31536000  # 1年
```

**レスポンスヘッダー:**

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### 6. 監査ログ

すべての認証イベントを記録：

```python
def log_access(user_id, action, resource=None, resource_id=None):
    """アクセスログを記録"""
    log_entry = {
        'id': len(logs) + 1,
        'user_id': user_id,
        'action': action,  # 'login', 'logout', 'token_refresh'
        'resource': resource,
        'resource_id': resource_id,
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent'),
        'timestamp': datetime.now().isoformat()
    }
    logs.append(log_entry)
    save_data('access_logs.json', logs)
```

**ログ例:**

```json
{
  "id": 123,
  "user_id": 1,
  "action": "login",
  "resource": null,
  "resource_id": null,
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "timestamp": "2024-01-15T10:30:00"
}
```

### 7. セキュリティヘッダー

```python
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response
```

---

## トラブルシューティング

### よくあるエラーと対処法

#### 1. `401 Unauthorized - MISSING_TOKEN`

**原因:** Authorizationヘッダーが含まれていない

**対処法:**

```javascript
// 正しい
fetch('/api/v1/knowledge', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
})

// 誤り
fetch('/api/v1/knowledge')
```

#### 2. `401 Unauthorized - TOKEN_EXPIRED`

**原因:** Access Tokenの有効期限切れ

**対処法:** Refresh Tokenを使用して新しいAccess Tokenを取得

```javascript
async function refreshAndRetry() {
  const refreshResponse = await fetch('/api/v1/auth/refresh', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${refreshToken}`
    }
  });

  const data = await refreshResponse.json();
  accessToken = data.data.access_token;

  // 元のリクエストを再試行
  return fetch('/api/v1/knowledge', {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
}
```

#### 3. `403 Forbidden - FORBIDDEN`

**原因:** 必要な権限がない

**対処法:** 適切なロールを持つユーザーでログイン

#### 4. `429 Too Many Requests`

**原因:** レート制限超過

**対処法:** 指数バックオフで再試行

```javascript
async function retryWithBackoff(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (error.status === 429 && i < maxRetries - 1) {
        const waitTime = Math.pow(2, i) * 1000;
        await new Promise(resolve => setTimeout(resolve, waitTime));
      } else {
        throw error;
      }
    }
  }
}
```

---

## まとめ

Mirai Knowledge Systemの認証・認可システムは、以下の特徴を持ちます：

1. **JWT ベース認証**: 標準的でスケーラブル
2. **役割ベースアクセス制御（RBAC）**: 柔軟な権限管理
3. **トークンリフレッシュ**: シームレスなユーザー体験
4. **セキュリティ強化**: bcrypt、HTTPS、レート制限
5. **監査ログ**: すべての認証イベントを記録

これにより、セキュアで使いやすいAPIを提供しています。
