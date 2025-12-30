"""
建設土木ナレッジシステム - 認証機能付きFlaskバックエンド
JSONベース + JWT認証 + RBAC
"""
from flask import Flask, jsonify, request, send_from_directory, redirect
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta
from functools import wraps
import json
import os
import hashlib
import bcrypt
from dotenv import load_dotenv
from marshmallow import ValidationError
from werkzeug.exceptions import BadRequest
from schemas import LoginSchema, KnowledgeCreateSchema
import time
import psutil
from collections import defaultdict, Counter
import smtplib
import ssl
from email.message import EmailMessage
import urllib.request
import tempfile

# 環境変数をロード
load_dotenv()


# ============================================================
# HTTPS強制リダイレクトミドルウェア
# ============================================================

class HTTPSRedirectMiddleware:
    """
    HTTP リクエストを HTTPS にリダイレクトするミドルウェア

    リバースプロキシ（Nginx等）経由の場合は X-Forwarded-Proto ヘッダーを使用。
    環境変数 MKS_FORCE_HTTPS=true で有効化。
    環境変数 MKS_TRUST_PROXY_HEADERS=true でプロキシヘッダーを信頼。

    使用例:
        app.wsgi_app = HTTPSRedirectMiddleware(app.wsgi_app)
    """

    def __init__(self, app, force_https=None, trust_proxy=None):
        self.app = app
        self.force_https = force_https if force_https is not None else \
            os.environ.get('MKS_FORCE_HTTPS', 'false').lower() in ('true', '1', 'yes')
        self.trust_proxy = trust_proxy if trust_proxy is not None else \
            os.environ.get('MKS_TRUST_PROXY_HEADERS', 'false').lower() in ('true', '1', 'yes')

    def __call__(self, environ, start_response):
        if not self.force_https:
            return self.app(environ, start_response)

        # プロトコルの判定
        if self.trust_proxy:
            # リバースプロキシからのヘッダーを信頼
            proto = environ.get('HTTP_X_FORWARDED_PROTO', 'http')
        else:
            # 直接接続の場合
            proto = environ.get('wsgi.url_scheme', 'http')

        if proto == 'https':
            # 既にHTTPS
            return self.app(environ, start_response)

        # HTTPからHTTPSへリダイレクト
        host = environ.get('HTTP_HOST', environ.get('SERVER_NAME', 'localhost'))

        # X-Forwarded-Host がある場合はそれを使用
        if self.trust_proxy and 'HTTP_X_FORWARDED_HOST' in environ:
            host = environ['HTTP_X_FORWARDED_HOST']

        path = environ.get('PATH_INFO', '/')
        query = environ.get('QUERY_STRING', '')

        https_url = f"https://{host}{path}"
        if query:
            https_url = f"{https_url}?{query}"

        # 301 Permanent Redirect
        status = '301 Moved Permanently'
        response_headers = [
            ('Location', https_url),
            ('Content-Type', 'text/html'),
            ('Content-Length', '0')
        ]
        start_response(status, response_headers)
        return [b'']

app = Flask(__name__, static_folder='../webui')

# CORS設定（環境変数ベース）
allowed_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:5100').split(',')
CORS(app,
     resources={
         r"/api/*": {
             "origins": allowed_origins,
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "expose_headers": ["Content-Type", "Authorization"],
             "supports_credentials": True,
             "max_age": 3600
         }
     })
print(f'[INIT] CORS configured for origins: {allowed_origins}')

# 設定
DEFAULT_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
app.config['DATA_DIR'] = os.environ.get('MKS_DATA_DIR', DEFAULT_DATA_DIR)

# JWT設定
# 開発環境用の固定秘密鍵（本番環境では環境変数を使用してください）
JWT_SECRET = 'mirai-knowledge-system-jwt-secret-key-2025'
app.config['JWT_SECRET_KEY'] = os.environ.get('MKS_JWT_SECRET_KEY', JWT_SECRET)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
# 完全なCSRF無効化（API専用）
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
app.config['WTF_CSRF_ENABLED'] = False

# セッションタイムアウト設定（本番環境での追加セキュリティ）
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12)
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('MKS_FORCE_HTTPS', 'false').lower() in ('true', '1', 'yes')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

print(f'[INIT] JWT Secret Key configured: {app.config["JWT_SECRET_KEY"][:20]}...')
jwt = JWTManager(app)

# 本番環境判定（レート制限/セキュリティヘッダーで使用）
IS_PRODUCTION = os.environ.get('MKS_ENV', 'development').lower() == 'production'
HSTS_ENABLED = os.environ.get('MKS_HSTS_ENABLED', 'false').lower() in ('true', '1', 'yes')
HSTS_MAX_AGE = int(os.environ.get('MKS_HSTS_MAX_AGE', '31536000'))  # デフォルト1年
HSTS_INCLUDE_SUBDOMAINS = os.environ.get('MKS_HSTS_INCLUDE_SUBDOMAINS', 'true').lower() in ('true', '1', 'yes')

# レート制限設定
# 開発環境では無効化、本番環境では緩和された制限を適用
if IS_PRODUCTION:
    default_limits_config = ["1000 per minute", "10000 per hour", "100000 per day"]
else:
    # 開発環境: レート制限を無効化
    default_limits_config = []

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=default_limits_config,
    storage_uri="memory://",
    strategy="fixed-window",
    in_memory_fallback_enabled=True
)

# 静的ファイルをレート制限から除外
@limiter.request_filter
def exempt_static():
    """静的ファイル（HTML、JS、CSS）をレート制限から除外"""
    return (request.path.startswith('/static/') or
            request.path.startswith('/webui/') or
            request.path.endswith('.html') or
            request.path.endswith('.js') or
            request.path.endswith('.css') or
            request.path == '/')

print('[INIT] Rate limiting configured (memory storage)')

# データストレージディレクトリ
def get_data_dir():
    """データ保存先ディレクトリを取得"""
    data_dir = app.config.get('DATA_DIR', DEFAULT_DATA_DIR)
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

# セキュリティヘッダー
@app.after_request
def add_security_headers(response):
    """セキュリティヘッダーを追加（本番/開発環境で設定を切り替え）"""
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'DENY')
    response.headers.setdefault('X-XSS-Protection', '1; mode=block')
    response.headers.setdefault(
        'Permissions-Policy',
        'geolocation=(), microphone=(), camera=(), payment=()'
    )

    # 本番環境: 強化されたセキュリティ設定
    if IS_PRODUCTION:
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')

        # HSTS (HTTP Strict Transport Security)
        if HSTS_ENABLED:
            hsts_value = f"max-age={HSTS_MAX_AGE}"
            if HSTS_INCLUDE_SUBDOMAINS:
                hsts_value += "; includeSubDomains"
            response.headers.setdefault('Strict-Transport-Security', hsts_value)

        # Content Security Policy（本番用: unsafe-inline を削除）
        csp_policy = "; ".join([
            "default-src 'self'",
            "script-src 'self' https://cdn.jsdelivr.net",  # Chart.js CDN許可
            "style-src 'self' https://fonts.googleapis.com",   # Google Fonts許可
            "img-src 'self' data: https:",
            "font-src 'self' data: https://fonts.gstatic.com",  # Google Fonts許可
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "upgrade-insecure-requests"  # HTTPリクエストを自動的にHTTPSに変換
        ])

        # APIレスポンスはキャッシュしない
        if request.path.startswith('/api/'):
            response.headers.setdefault('Cache-Control', 'no-store, no-cache, must-revalidate')
            response.headers.setdefault('Pragma', 'no-cache')
    else:
        # 開発環境: 緩和されたセキュリティ設定
        response.headers.setdefault('Referrer-Policy', 'no-referrer')

        # Content Security Policy（開発用: unsafe-inline許可）
        csp_policy = "; ".join([
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",  # 開発環境用にunsafe-inline許可 + Chart.js CDN
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",   # インラインスタイル許可 + Google Fonts
            "img-src 'self' data: https:",
            "font-src 'self' data: https://fonts.gstatic.com",  # Google Fonts許可
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ])

    response.headers.setdefault('Content-Security-Policy', csp_policy)

    return response

# ============================================================
# メトリクス収集（Prometheus互換）
# ============================================================

# グローバルメトリクスストレージ
metrics_storage = {
    'http_requests_total': defaultdict(int),
    'http_request_duration_seconds': defaultdict(list),
    'active_users': set(),
    'active_sessions': set(),
    'login_attempts': defaultdict(int),
    'knowledge_operations': defaultdict(int),
    'errors': defaultdict(int),
    'start_time': time.time()
}

@app.before_request
def before_request_metrics():
    """リクエスト前のメトリクス記録"""
    request.start_time = time.time()

@app.after_request
def after_request_metrics(response):
    """リクエスト後のメトリクス記録"""
    # リクエスト処理時間計算
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time

        # エンドポイント特定
        endpoint = request.endpoint or 'unknown'
        method = request.method
        status = response.status_code

        # メトリクス記録
        key = f"{method}_{endpoint}_{status}"
        metrics_storage['http_requests_total'][key] += 1
        metrics_storage['http_request_duration_seconds'][endpoint].append(duration)

        # エラー記録
        if status >= 400:
            error_key = f"{status}"
            metrics_storage['errors'][error_key] += 1

    return response

# ============================================================
# ユーザー・権限管理（JSONベース）
# ============================================================

def load_users():
    """ユーザーデータ読み込み"""
    filepath = os.path.join(get_data_dir(), 'users.json')
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_users(users):
    """ユーザーデータ保存"""
    filepath = os.path.join(get_data_dir(), 'users.json')
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def hash_password(password):
    """
    パスワードをbcryptでハッシュ化

    Args:
        password: 平文パスワード

    Returns:
        str: bcryptハッシュ文字列
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, password_hash):
    """
    パスワードを検証（bcryptとレガシーSHA256の両方をサポート）

    Args:
        password: 平文パスワード
        password_hash: ハッシュ化されたパスワード

    Returns:
        bool: 検証成功時True
    """
    # bcrypt hash detection (starts with $2)
    if password_hash.startswith('$2'):
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception as e:
            print(f'[ERROR] bcrypt verification failed: {e}')
            return False
    else:
        # レガシーSHA256サポート（後方互換性）
        print(f'[WARNING] Using legacy SHA256 verification for password. Please update user password.')
        legacy_hash = hashlib.sha256(password.encode()).hexdigest()
        return legacy_hash == password_hash

def get_user_permissions(user):
    """ユーザーの権限を取得"""
    role_permissions = {
        'admin': ['*'],  # 全権限
        'construction_manager': [
            'knowledge.create', 'knowledge.read', 'knowledge.update',
            'sop.read', 'incident.create', 'incident.read',
            'consultation.create', 'approval.read', 'notification.read'
        ],
        'quality_assurance': [
            'knowledge.read', 'knowledge.approve', 'sop.read', 'sop.update',
            'incident.read', 'approval.execute', 'notification.read'
        ],
        'safety_officer': [
            'knowledge.read', 'sop.read', 'incident.create', 'incident.read',
            'incident.update', 'approval.read', 'notification.read'
        ],
        'partner_company': [
            'knowledge.read', 'sop.read', 'incident.read', 'notification.read'
        ]
    }
    
    roles = user.get('roles', [])
    permissions = set()
    
    for role in roles:
        role_perms = role_permissions.get(role, [])
        if '*' in role_perms:
            return ['*']  # 全権限
        permissions.update(role_perms)
    
    return list(permissions)

def check_permission(required_permission):
    """権限チェックデコレータ"""
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            try:
                current_user_id = get_jwt_identity()
                # IDを整数に変換（JWTでは文字列として保存）
                user_id_int = int(current_user_id) if isinstance(current_user_id, str) else current_user_id
                print(f'[DEBUG] check_permission: user_id={user_id_int}, required={required_permission}')

                users = load_users()
                user = next((u for u in users if u['id'] == user_id_int), None)

                if not user:
                    print(f'[DEBUG] User not found: {current_user_id}')
                    return jsonify({'success': False, 'error': 'User not found'}), 404

                permissions = get_user_permissions(user)
                print(f'[DEBUG] User permissions: {permissions}')

                # 管理者または必要な権限を持っている
                if '*' in permissions or required_permission in permissions:
                    print(f'[DEBUG] Permission granted')
                    return fn(*args, **kwargs)

                print(f'[DEBUG] Permission denied')
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'FORBIDDEN',
                        'message': 'Insufficient permissions'
                    }
                }), 403
            except Exception as e:
                print(f'[DEBUG] Exception in check_permission: {e}')
                import traceback
                traceback.print_exc()
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INTERNAL_ERROR',
                        'message': 'Internal server error'
                    }
                }), 500

        return wrapper
    return decorator

def validate_request(schema_class):
    """
    リクエストデータを検証するデコレータ

    Usage:
        @validate_request(KnowledgeCreateSchema)
        def create_knowledge():
            validated_data = request.validated_data
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                schema = schema_class()
                validated_data = schema.load(request.json or {})
                # 検証済みデータをrequestに追加
                request.validated_data = validated_data
                return fn(*args, **kwargs)
            except BadRequest:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_JSON',
                        'message': 'Invalid JSON payload'
                    }
                }), 400
            except ValidationError as err:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': '入力データが不正です',
                        'details': err.messages
                    }
                }), 400

        return wrapper
    return decorator

# ============================================================
# 監査ログ
# ============================================================

def log_access(user_id, action, resource=None, resource_id=None):
    """アクセスログを記録"""
    logs = load_data('access_logs.json')
    
    log_entry = {
        'id': len(logs) + 1,
        'user_id': user_id,
        'action': action,
        'resource': resource,
        'resource_id': resource_id,
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent'),
        'timestamp': datetime.now().isoformat()
    }
    
    logs.append(log_entry)
    save_data('access_logs.json', logs)

# ============================================================
# データ管理関数
# ============================================================

def load_data(filename):
    """JSONファイルからデータを読み込み"""
    filepath = os.path.join(get_data_dir(), filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    return []
                return [item for item in data if isinstance(item, dict)]
        except (json.JSONDecodeError, ValueError) as e:
            print(f'[WARN] Failed to decode {filepath}: {e}')
            return []
    return []

def save_data(filename, data):
    """JSONファイルにデータを保存"""
    filepath = os.path.join(get_data_dir(), filename)
    dirpath = os.path.dirname(filepath)
    fd, tmp_path = tempfile.mkstemp(prefix=f".{filename}.", suffix=".tmp", dir=dirpath)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, filepath)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

# ============================================================
# 認証API
# ============================================================

@app.route('/api/v1/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
@limiter.limit("20 per hour")
@validate_request(LoginSchema)
def login():
    """ログイン（レート制限: 5回/分、20回/時、入力検証付き）"""
    data = request.validated_data  # 検証済みデータを使用
    username = data['username']
    password = data['password']
    
    if not username or not password:
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Username and password are required'
            }
        }), 400
    
    users = load_users()
    user = next((u for u in users if u['username'] == username), None)
    
    if not user or not verify_password(password, user['password_hash']):
        return jsonify({
            'success': False,
            'error': {
                'code': 'UNAUTHORIZED',
                'message': 'Invalid username or password'
            }
        }), 401
    
    # トークン生成（identityを文字列に変換）
    access_token = create_access_token(
        identity=str(user['id']),
        additional_claims={'roles': user.get('roles', [])}
    )
    refresh_token = create_refresh_token(identity=str(user['id']))
    
    # ログイン記録
    log_access(user['id'], 'login')
    
    # レスポンス
    user_data = {k: v for k, v in user.items() if k != 'password_hash'}
    
    return jsonify({
        'success': True,
        'data': {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': 3600,
            'user': user_data
        }
    })

@app.route('/api/v1/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """トークンリフレッシュ"""
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)
    
    return jsonify({
        'success': True,
        'data': {
            'access_token': access_token,
            'expires_in': 3600
        }
    })

@app.route('/api/v1/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """現在のユーザー情報取得"""
    current_user_id = int(get_jwt_identity())
    users = load_users()
    user = next((u for u in users if u['id'] == current_user_id), None)
    
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    user_data = {k: v for k, v in user.items() if k != 'password_hash'}
    user_data['permissions'] = get_user_permissions(user)
    
    return jsonify({
        'success': True,
        'data': user_data
    })

# ============================================================
# 検索ヘルパー関数
# ============================================================

def search_in_fields(item, query, fields):
    """
    複数フィールドから検索し、マッチ情報とスコアを返す

    Args:
        item: 検索対象アイテム
        query: 検索クエリ
        fields: 検索対象フィールドのリスト

    Returns:
        tuple: (matched_fields, relevance_score)
    """
    query_lower = query.lower()
    matched_fields = []
    relevance_score = 0.0

    for field in fields:
        value = str(item.get(field, '')).lower()
        if query_lower in value:
            matched_fields.append(field)
            # フィールドごとに重み付けスコアリング
            if field == 'title':
                relevance_score += 1.0
            elif field == 'summary':
                relevance_score += 0.7
            elif field == 'content':
                relevance_score += 0.5

    return matched_fields, relevance_score

def highlight_text(text, query):
    """
    検索語をハイライトマークで囲む

    Args:
        text: 対象テキスト
        query: ハイライト対象のクエリ

    Returns:
        str: ハイライト適用後のテキスト
    """
    if not text or not query:
        return text
    import re
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    return pattern.sub(lambda m: f'<mark>{m.group()}</mark>', text)

# ============================================================
# ナレッジ管理API（権限チェック付き）
# ============================================================

@app.route('/api/v1/knowledge', methods=['GET'])
@check_permission('knowledge.read')
def get_knowledge():
    """ナレッジ一覧取得"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, 'knowledge.list', 'knowledge')
    
    knowledge_list = load_data('knowledge.json')
    
    # クエリパラメータでのフィルタリング
    category = request.args.get('category')
    search = request.args.get('search')
    tags = request.args.get('tags')
    
    filtered = knowledge_list
    
    if category:
        filtered = [k for k in filtered if k.get('category') == category]
    
    # 全文検索（title, summary, contentフィールド対応）
    if search:
        highlight = request.args.get('highlight', 'false') == 'true'
        filtered_with_score = []

        for k in filtered:
            # title, summary, contentから検索
            matched_fields, score = search_in_fields(
                k, search, ['title', 'summary', 'content']
            )

            if matched_fields:
                k_copy = k.copy()
                k_copy['matched_fields'] = matched_fields
                k_copy['relevance_score'] = score

                # ハイライト処理（オプション）
                if highlight:
                    for field in ['title', 'summary', 'content']:
                        if field in k_copy and k_copy[field]:
                            k_copy[field] = highlight_text(k_copy[field], search)

                filtered_with_score.append(k_copy)

        # スコア順にソート
        filtered = sorted(filtered_with_score,
                         key=lambda x: x['relevance_score'],
                         reverse=True)

    if tags:
        tag_list = tags.split(',')
        filtered = [k for k in filtered if
                   any(tag in k.get('tags', []) for tag in tag_list)]

    return jsonify({
        'success': True,
        'data': filtered,
        'pagination': {
            'total_items': len(filtered)
        }
    })

@app.route('/api/v1/knowledge/<int:knowledge_id>', methods=['GET'])
@check_permission('knowledge.read')
def get_knowledge_detail(knowledge_id):
    """ナレッジ詳細取得"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, 'knowledge.view', 'knowledge', knowledge_id)
    
    knowledge_list = load_data('knowledge.json')
    knowledge = next((k for k in knowledge_list if k['id'] == knowledge_id), None)
    
    if not knowledge:
        return jsonify({'success': False, 'error': 'Knowledge not found'}), 404
    
    return jsonify({
        'success': True,
        'data': knowledge
    })

@app.route('/api/v1/knowledge', methods=['POST'])
@check_permission('knowledge.create')
@validate_request(KnowledgeCreateSchema)
def create_knowledge():
    """新規ナレッジ登録（入力検証付き）"""
    current_user_id = get_jwt_identity()
    data = request.validated_data  # 検証済みデータを使用
    knowledge_list = load_data('knowledge.json')
    
    # ID自動採番
    new_id = max([k['id'] for k in knowledge_list], default=0) + 1
    
    new_knowledge = {
        'id': new_id,
        'title': data.get('title'),
        'summary': data.get('summary'),
        'content': data.get('content'),
        'category': data.get('category'),
        'tags': data.get('tags', []),
        'status': 'draft',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'owner': data.get('owner', 'unknown'),
        'project': data.get('project'),
        'priority': data.get('priority', 'medium'),
        'created_by_id': current_user_id
    }
    
    knowledge_list.append(new_knowledge)
    save_data('knowledge.json', knowledge_list)

    log_access(current_user_id, 'knowledge.create', 'knowledge', new_id)

    # 通知作成（承認者に通知）
    create_notification(
        title='新規ナレッジが承認待ちです',
        message=f'{new_knowledge["owner"]}さんが「{new_knowledge["title"]}」を登録しました。承認をお願いします。',
        type='approval_required',
        target_roles=['admin', 'quality_assurance'],
        priority='high',
        related_entity_type='knowledge',
        related_entity_id=new_id
    )

    return jsonify({
        'success': True,
        'data': new_knowledge
    }), 201

# ============================================================
# 横断検索API
# ============================================================

@app.route('/api/v1/search/unified', methods=['GET'])
@jwt_required()
def unified_search():
    """
    複数エンティティの横断検索

    クエリパラメータ:
        q: 検索クエリ（必須）
        types: 検索対象タイプ（カンマ区切り）
               knowledge,sop,incidents,consultations,regulations
        highlight: ハイライト有効化（デフォルト: true）
    """
    current_user_id = get_jwt_identity()
    query = request.args.get('q', '')
    types = request.args.get('types', 'knowledge,sop,incidents').split(',')
    highlight = request.args.get('highlight', 'true') == 'true'

    if not query:
        return jsonify({
            'success': False,
            'error': {'code': 'MISSING_QUERY', 'message': 'Query parameter "q" is required'}
        }), 400

    results = {}
    total_count = 0

    # 各エンティティを検索
    if 'knowledge' in types:
        knowledge_list = load_data('knowledge.json')
        matched = []

        for item in knowledge_list:
            matched_fields, score = search_in_fields(
                item, query, ['title', 'summary', 'content']
            )
            if matched_fields:
                item_copy = item.copy()
                item_copy['relevance_score'] = score
                if highlight:
                    for field in ['title', 'summary']:
                        if field in item_copy and item_copy[field]:
                            item_copy[field] = highlight_text(item_copy[field], query)
                matched.append(item_copy)

        matched = sorted(matched, key=lambda x: x['relevance_score'], reverse=True)
        results['knowledge'] = {'items': matched[:10], 'count': len(matched)}
        total_count += len(matched)

    if 'sop' in types:
        sop_list = load_data('sop.json')
        matched = []

        for item in sop_list:
            matched_fields, score = search_in_fields(
                item, query, ['title', 'content']
            )
            if matched_fields:
                item_copy = item.copy()
                item_copy['relevance_score'] = score
                matched.append(item_copy)

        matched = sorted(matched, key=lambda x: x['relevance_score'], reverse=True)
        results['sop'] = {'items': matched[:10], 'count': len(matched)}
        total_count += len(matched)

    if 'incidents' in types:
        incidents_list = load_data('incidents.json')
        matched = []

        for item in incidents_list:
            matched_fields, score = search_in_fields(
                item, query, ['title', 'description']
            )
            if matched_fields:
                item_copy = item.copy()
                item_copy['relevance_score'] = score
                matched.append(item_copy)

        matched = sorted(matched, key=lambda x: x['relevance_score'], reverse=True)
        results['incidents'] = {'items': matched[:10], 'count': len(matched)}
        total_count += len(matched)

    log_access(current_user_id, 'search.unified', 'search', query)

    return jsonify({
        'success': True,
        'data': results,
        'total_results': total_count,
        'query': query
    })

# ============================================================
# 通知機能
# ============================================================

def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in ('1', 'true', 'yes', 'on')


def _external_notifications_disabled():
    return app.config.get('TESTING', False) or _env_bool('MKS_DISABLE_EXTERNAL_NOTIFICATIONS', False)


def _external_notification_types():
    raw_types = os.environ.get('MKS_EXTERNAL_NOTIFICATION_TYPES', '').strip()
    if not raw_types:
        return None
    return {t.strip() for t in raw_types.split(',') if t.strip()}


def _should_send_external(notification_type):
    allowed_types = _external_notification_types()
    if allowed_types is None:
        return True
    return notification_type in allowed_types


def _get_notification_recipients(target_users, target_roles):
    target_users = target_users or []
    target_roles = target_roles or []
    if not target_users and not target_roles:
        return []

    users = load_users()
    recipients = []
    seen = set()

    for user in users:
        if user.get('id') in target_users or any(
            role in target_roles for role in user.get('roles', [])
        ):
            email = user.get('email')
            if email and email not in seen:
                seen.add(email)
                recipients.append(email)

    return recipients


def _build_notification_message(notification, recipient_count=None):
    summary_parts = []
    if notification.get('target_users'):
        summary_parts.append(f"対象ユーザーID: {', '.join(map(str, notification['target_users']))}")
    if notification.get('target_roles'):
        summary_parts.append(f"対象ロール: {', '.join(notification['target_roles'])}")
    if recipient_count is not None:
        summary_parts.append(f"受信者数: {recipient_count}")

    summary = " / ".join(summary_parts)

    subject = f"[{notification.get('type', 'notification')}] {notification.get('title', '')}"
    body_lines = [
        notification.get('message', ''),
        "",
        f"タイプ: {notification.get('type', '')}",
        f"優先度: {notification.get('priority', '')}",
        f"通知ID: {notification.get('id', '')}",
        f"作成日時: {notification.get('created_at', '')}",
    ]
    if summary:
        body_lines.append(summary)

    body = "\n".join(body_lines).strip()
    return subject, body


def _retry_operation(operation, label, max_attempts=5, backoff_seconds=0.5):
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            operation()
            return {'status': 'sent', 'attempts': attempt}
        except Exception as exc:
            last_error = str(exc)
            print(f"[NOTIFY] {label} attempt {attempt} failed: {exc}")
            if attempt < max_attempts:
                time.sleep(backoff_seconds * attempt)
    return {'status': 'failed', 'attempts': max_attempts, 'last_error': last_error}


def _get_retry_count():
    raw = os.environ.get('MKS_NOTIFICATION_RETRY_COUNT', '5').strip()
    return int(raw) if raw.isdigit() else 5


def _send_teams_notification(notification):
    webhook_url = os.environ.get('MKS_TEAMS_WEBHOOK_URL', '').strip()
    if not webhook_url:
        return {'status': 'skipped', 'reason': 'MKS_TEAMS_WEBHOOK_URL not set'}

    subject, body = _build_notification_message(notification)
    payload = {'text': f"{subject}\n{body}"}
    data = json.dumps(payload).encode('utf-8')

    def _post():
        request_obj = urllib.request.Request(
            webhook_url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(request_obj, timeout=10) as response:
            if response.status not in (200, 201, 202):
                raise RuntimeError(f"Teams webhook response: {response.status}")

    return _retry_operation(_post, 'teams', max_attempts=_get_retry_count())


def _send_email_notification(notification):
    smtp_host = os.environ.get('MKS_SMTP_HOST', '').strip()
    smtp_from = os.environ.get('MKS_SMTP_FROM', '').strip()
    if not smtp_host or not smtp_from:
        return {'status': 'skipped', 'reason': 'SMTP config not set'}

    recipients = _get_notification_recipients(
        notification.get('target_users'),
        notification.get('target_roles')
    )
    if not recipients:
        return {'status': 'skipped', 'reason': 'no recipients'}

    smtp_port = int(os.environ.get('MKS_SMTP_PORT', '587'))
    smtp_user = os.environ.get('MKS_SMTP_USER', '').strip()
    smtp_password = os.environ.get('MKS_SMTP_PASSWORD', '').strip()
    use_tls = _env_bool('MKS_SMTP_USE_TLS', True)
    use_ssl = _env_bool('MKS_SMTP_USE_SSL', False)

    subject, body = _build_notification_message(notification, recipient_count=len(recipients))
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = smtp_from
    msg['To'] = ', '.join(recipients)
    msg.set_content(body)

    context = ssl.create_default_context()

    def _send():
        if use_ssl:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10, context=context) as server:
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)
            return

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            if use_tls:
                server.starttls(context=context)
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)

    result = _retry_operation(_send, 'email', max_attempts=_get_retry_count())
    result['recipient_count'] = len(recipients)
    return result


def _send_external_notifications(notification):
    if _external_notifications_disabled():
        return {
            'teams': {'status': 'skipped', 'reason': 'disabled'},
            'email': {'status': 'skipped', 'reason': 'disabled'}
        }

    if not _should_send_external(notification.get('type')):
        return {
            'teams': {'status': 'skipped', 'reason': 'type filtered'},
            'email': {'status': 'skipped', 'reason': 'type filtered'}
        }

    return {
        'teams': _send_teams_notification(notification),
        'email': _send_email_notification(notification)
    }


def create_notification(title, message, type, target_users=None,
                       target_roles=None, priority='medium',
                       related_entity_type=None, related_entity_id=None):
    """
    通知を作成してJSONに保存

    Args:
        title: 通知タイトル
        message: 通知メッセージ
        type: 通知タイプ（approval_required, approval_completed等）
        target_users: ターゲットユーザーIDリスト
        target_roles: ターゲットロールリスト
        priority: 優先度（low, medium, high）
        related_entity_type: 関連エンティティタイプ
        related_entity_id: 関連エンティティID

    Returns:
        dict: 作成された通知オブジェクト
    """
    notifications = load_data('notifications.json')

    new_notification = {
        'id': max([n['id'] for n in notifications], default=0) + 1,
        'title': title,
        'message': message,
        'type': type,
        'target_users': target_users or [],
        'target_roles': target_roles or [],
        'priority': priority,
        'related_entity_type': related_entity_type,
        'related_entity_id': related_entity_id,
        'created_at': datetime.now().isoformat(),
        'status': 'sent',
        'read_by': [],
        'external_delivery': {},
        'external_delivery_failed': False
    }

    notifications.append(new_notification)
    save_data('notifications.json', notifications)

    delivery_results = _send_external_notifications(new_notification)
    if delivery_results:
        new_notification['external_delivery'] = delivery_results
        new_notification['external_delivery_failed'] = any(
            result.get('status') == 'failed'
            for result in delivery_results.values()
        )
        save_data('notifications.json', notifications)

    return new_notification

@app.route('/api/v1/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """ユーザーの通知一覧取得"""
    current_user_id = int(get_jwt_identity())
    users = load_users()
    user = next((u for u in users if u['id'] == current_user_id), None)

    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    notifications = load_data('notifications.json')
    user_notifications = []

    for n in notifications:
        # ターゲットユーザーまたはターゲットロールに該当するか
        if current_user_id in n.get('target_users', []) or \
           any(role in n.get('target_roles', []) for role in user.get('roles', [])):
            n_copy = n.copy()
            n_copy['is_read'] = current_user_id in n.get('read_by', [])
            user_notifications.append(n_copy)

    # 新しい順にソート
    user_notifications = sorted(user_notifications,
                                key=lambda x: x['created_at'],
                                reverse=True)

    # 未読数カウント
    unread_count = sum(1 for n in user_notifications if not n['is_read'])

    return jsonify({
        'success': True,
        'data': user_notifications,
        'pagination': {
            'total_items': len(user_notifications),
            'unread_count': unread_count
        }
    })

@app.route('/api/v1/notifications/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_notification_read(notification_id):
    """通知を既読にする"""
    current_user_id = int(get_jwt_identity())
    notifications = load_data('notifications.json')

    notification = next((n for n in notifications if n['id'] == notification_id), None)
    if not notification:
        return jsonify({'success': False, 'error': 'Notification not found'}), 404

    # 既読リストに追加
    if current_user_id not in notification.get('read_by', []):
        notification.setdefault('read_by', []).append(current_user_id)
        save_data('notifications.json', notifications)

    return jsonify({
        'success': True,
        'data': {'id': notification_id, 'is_read': True}
    })

@app.route('/api/v1/notifications/unread/count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """未読通知数取得"""
    current_user_id = int(get_jwt_identity())
    users = load_users()
    user = next((u for u in users if u['id'] == current_user_id), None)

    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    notifications = load_data('notifications.json')
    unread_count = 0

    for n in notifications:
        if (current_user_id in n.get('target_users', []) or \
            any(role in n.get('target_roles', []) for role in user.get('roles', []))) and \
           current_user_id not in n.get('read_by', []):
            unread_count += 1

    return jsonify({
        'success': True,
        'data': {'unread_count': unread_count}
    })

# 他のエンドポイントも同様に権限チェックを追加...
# （簡潔にするため、主要なものの定義）

@app.route('/api/v1/sop', methods=['GET'])
@check_permission('sop.read')
def get_sop():
    """SOP一覧取得"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, 'sop.list', 'sop')
    
    sop_list = load_data('sop.json')
    return jsonify({
        'success': True,
        'data': sop_list,
        'pagination': {'total_items': len(sop_list)}
    })

@app.route('/api/v1/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """ダッシュボード統計情報取得"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, 'dashboard.view', 'dashboard')
    
    knowledge_list = load_data('knowledge.json')
    sop_list = load_data('sop.json')
    incidents = load_data('incidents.json')
    approvals = load_data('approvals.json')
    
    stats = {
        'kpis': {
            'knowledge_reuse_rate': 71,
            'accident_free_days': 184,
            'active_audits': 6,
            'delayed_corrections': 3
        },
        'counts': {
            'total_knowledge': len(knowledge_list),
            'total_sop': len(sop_list),
            'recent_incidents': len([i for i in incidents if i.get('status') == 'reported']),
            'pending_approvals': len([a for a in approvals if a.get('status') == 'pending'])
        }
    }
    
    return jsonify({
        'success': True,
        'data': stats
    })

@app.route('/api/v1/approvals', methods=['GET'])
@jwt_required()
def get_approvals():
    """承認フロー一覧取得"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, 'approvals.list', 'approvals')

    approvals = load_data('approvals.json')
    return jsonify({
        'success': True,
        'data': approvals,
        'pagination': {'total_items': len(approvals)}
    })


# ============================================================
# メトリクスエンドポイント（Prometheus用）
# ============================================================

@app.route('/api/v1/metrics', methods=['GET'])
def get_metrics():
    """
    Prometheus互換メトリクスエンドポイント

    Returns:
        text/plain: Prometheus形式のメトリクスデータ
    """
    from flask import Response

    # システムメトリクス取得
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # ナレッジデータ統計
    knowledge_list = load_data('knowledge.json')
    sop_list = load_data('sop.json')

    # アクセスログ分析
    access_logs = load_data('access_logs.json')

    # アクティブユーザー計算（過去15分以内にアクセスがあったユーザー）
    now = datetime.now()
    active_users = set()
    active_sessions = set()
    login_success = 0
    login_failure = 0

    for log in access_logs:
        try:
            log_time = datetime.fromisoformat(log.get('timestamp', ''))
            if (now - log_time).total_seconds() < 900:  # 15分以内
                user_id = log.get('user_id')
                if user_id:
                    active_users.add(user_id)
                    active_sessions.add(log.get('session_id', ''))

            # ログイン統計
            if log.get('action') == 'auth.login':
                if log.get('status') == 'success':
                    login_success += 1
                else:
                    login_failure += 1
        except (ValueError, TypeError):
            continue

    # カテゴリ別ナレッジ数
    category_counts = Counter([k.get('category', 'unknown') for k in knowledge_list])

    # HTTPリクエストメトリクス集計
    http_requests_metrics = []
    for key, count in metrics_storage['http_requests_total'].items():
        parts = key.split('_', 2)
        if len(parts) >= 3:
            method, endpoint, status = parts[0], parts[1], parts[2]
            http_requests_metrics.append(
                f'http_requests_total{{method="{method}",endpoint="{endpoint}",status="{status}"}} {count}'
            )

    # 応答時間メトリクス（ヒストグラム風）
    response_time_metrics = []
    for endpoint, durations in metrics_storage['http_request_duration_seconds'].items():
        if durations:
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)

            # パーセンタイル計算
            sorted_durations = sorted(durations)
            p50 = sorted_durations[len(sorted_durations) // 2] if sorted_durations else 0
            p95_idx = int(len(sorted_durations) * 0.95)
            p95 = sorted_durations[p95_idx] if p95_idx < len(sorted_durations) else max_duration
            p99_idx = int(len(sorted_durations) * 0.99)
            p99 = sorted_durations[p99_idx] if p99_idx < len(sorted_durations) else max_duration

            response_time_metrics.extend([
                f'http_request_duration_seconds{{endpoint="{endpoint}",quantile="0.5"}} {p50:.4f}',
                f'http_request_duration_seconds{{endpoint="{endpoint}",quantile="0.95"}} {p95:.4f}',
                f'http_request_duration_seconds{{endpoint="{endpoint}",quantile="0.99"}} {p99:.4f}',
                f'http_request_duration_seconds_sum{{endpoint="{endpoint}"}} {sum(durations):.4f}',
                f'http_request_duration_seconds_count{{endpoint="{endpoint}"}} {len(durations)}'
            ])

    # Prometheus形式のテキスト生成
    metrics_text = f"""# HELP app_info Application information
# TYPE app_info gauge
app_info{{version="2.0",name="mirai-knowledge-system"}} 1

# HELP app_uptime_seconds Application uptime in seconds
# TYPE app_uptime_seconds counter
app_uptime_seconds {time.time() - metrics_storage['start_time']:.2f}

# HELP system_cpu_usage_percent CPU usage percentage
# TYPE system_cpu_usage_percent gauge
system_cpu_usage_percent {cpu_percent:.2f}

# HELP system_memory_usage_percent Memory usage percentage
# TYPE system_memory_usage_percent gauge
system_memory_usage_percent {memory.percent:.2f}

# HELP system_memory_total_bytes Total memory in bytes
# TYPE system_memory_total_bytes gauge
system_memory_total_bytes {memory.total}

# HELP system_memory_available_bytes Available memory in bytes
# TYPE system_memory_available_bytes gauge
system_memory_available_bytes {memory.available}

# HELP system_disk_usage_percent Disk usage percentage
# TYPE system_disk_usage_percent gauge
system_disk_usage_percent {disk.percent:.2f}

# HELP system_disk_total_bytes Total disk space in bytes
# TYPE system_disk_total_bytes gauge
system_disk_total_bytes {disk.total}

# HELP system_disk_free_bytes Free disk space in bytes
# TYPE system_disk_free_bytes gauge
system_disk_free_bytes {disk.free}

# HELP active_users_count Number of active users (last 15 minutes)
# TYPE active_users_count gauge
active_users_count {len(active_users)}

# HELP active_sessions_count Number of active sessions
# TYPE active_sessions_count gauge
active_sessions_count {len(active_sessions)}

# HELP login_attempts_total Total number of login attempts
# TYPE login_attempts_total counter
login_attempts_total{{status="success"}} {login_success}
login_attempts_total{{status="failure"}} {login_failure}

# HELP knowledge_total_count Total number of knowledge items
# TYPE knowledge_total_count gauge
knowledge_total_count {len(knowledge_list)}

# HELP knowledge_by_category Knowledge items by category
# TYPE knowledge_by_category gauge
"""

    # カテゴリ別メトリクス追加
    for category, count in category_counts.items():
        metrics_text += f'knowledge_by_category{{category="{category}"}} {count}\n'

    metrics_text += f"""
# HELP sop_total_count Total number of SOP documents
# TYPE sop_total_count gauge
sop_total_count {len(sop_list)}

# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
"""

    # HTTPリクエストメトリクス追加
    if http_requests_metrics:
        metrics_text += '\n'.join(http_requests_metrics) + '\n'

    metrics_text += """
# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
"""

    # 応答時間メトリクス追加
    if response_time_metrics:
        metrics_text += '\n'.join(response_time_metrics) + '\n'

    # エラーメトリクス
    metrics_text += """
# HELP http_errors_total Total number of HTTP errors
# TYPE http_errors_total counter
"""
    for error_code, count in metrics_storage['errors'].items():
        metrics_text += f'http_errors_total{{code="{error_code}"}} {count}\n'

    # ナレッジ操作メトリクス
    metrics_text += """
# HELP knowledge_created_total Total number of created knowledge items
# TYPE knowledge_created_total counter
knowledge_created_total {0}

# HELP knowledge_searches_total Total number of knowledge searches
# TYPE knowledge_searches_total counter
knowledge_searches_total {0}

# HELP knowledge_views_total Total number of knowledge views
# TYPE knowledge_views_total counter
knowledge_views_total {0}
"""

    return Response(metrics_text, mimetype='text/plain; version=0.0.4; charset=utf-8')


# ============================================================
# 公開エンドポイント（認証不要）
# ============================================================

@app.route('/')
def index():
    """トップページ"""
    response = send_from_directory(app.static_folder, 'index.html')
    # HTMLファイルはキャッシュしない（動的更新対応）
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/<path:path>')
def serve_static(path):
    """静的ファイル配信（キャッシュ最適化）"""
    response = send_from_directory(app.static_folder, path)

    # ファイルタイプに応じたキャッシュ設定
    if path.endswith(('.js', '.css')):
        # JS/CSSは1時間キャッシュ
        response.headers['Cache-Control'] = 'public, max-age=3600'
    elif path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp')):
        # 画像は1日キャッシュ
        response.headers['Cache-Control'] = 'public, max-age=86400'
    elif path.endswith(('.woff', '.woff2', '.ttf', '.eot')):
        # フォントは1週間キャッシュ
        response.headers['Cache-Control'] = 'public, max-age=604800'
    elif path.endswith('.html'):
        # HTMLファイルはキャッシュしない
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

    return response

# ============================================================
# エラーハンドラー
# ============================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': {
            'code': 'NOT_FOUND',
            'message': 'Resource not found'
        }
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': {
            'code': 'INTERNAL_ERROR',
            'message': 'Internal server error'
        }
    }), 500

@app.errorhandler(429)
def ratelimit_handler(error):
    """レート制限エラーハンドラ"""
    return jsonify({
        'success': False,
        'error': {
            'code': 'RATE_LIMIT_EXCEEDED',
            'message': 'リクエストが多すぎます。しばらく待ってから再試行してください。',
            'retry_after': str(error.description) if hasattr(error, 'description') else '60 seconds'
        }
    }), 429

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'success': False,
        'error': {
            'code': 'TOKEN_EXPIRED',
            'message': 'Token has expired'
        }
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'success': False,
        'error': {
            'code': 'INVALID_TOKEN',
            'message': 'Invalid token'
        }
    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        'success': False,
        'error': {
            'code': 'MISSING_TOKEN',
            'message': 'Authorization token is missing'
        }
    }), 401

# ============================================================
# アプリケーション起動
# ============================================================

def init_demo_users():
    """デモユーザー作成"""
    users = load_users()
    if len(users) == 0:
        demo_users = [
            {
                'id': 1,
                'username': 'admin',
                'email': 'admin@example.com',
                'password_hash': hash_password('admin123'),
                'full_name': '管理者',
                'department': 'システム管理部',
                'roles': ['admin'],
                'is_active': True
            },
            {
                'id': 2,
                'username': 'yamada',
                'email': 'yamada@example.com',
                'password_hash': hash_password('yamada123'),
                'full_name': '山田太郎',
                'department': '施工管理',
                'roles': ['construction_manager'],
                'is_active': True
            },
            {
                'id': 3,
                'username': 'partner',
                'email': 'partner@example.com',
                'password_hash': hash_password('partner123'),
                'full_name': '協力会社ユーザー',
                'department': '協力会社',
                'roles': ['partner_company'],
                'is_active': True
            }
        ]
        save_users(demo_users)
        print("[OK] デモユーザーを作成しました")
        print("   - admin / admin123 (管理者)")
        print("   - yamada / yamada123 (施工管理)")
        print("   - partner / partner123 (協力会社)")

# HTTPS強制リダイレクトミドルウェアを適用（本番環境用）
# 環境変数 MKS_FORCE_HTTPS=true で有効化
if os.environ.get('MKS_FORCE_HTTPS', 'false').lower() in ('true', '1', 'yes'):
    app.wsgi_app = HTTPSRedirectMiddleware(app.wsgi_app)
    print('[INIT] HTTPS強制リダイレクトを有効化しました')

if __name__ == '__main__':
    print('=' * 60)
    print('建設土木ナレッジシステム - サーバー起動中')
    print('=' * 60)

    # 環境情報表示
    env_mode = os.environ.get('MKS_ENV', 'development')
    print(f'環境モード: {env_mode}')

    if IS_PRODUCTION:
        print('[PRODUCTION] 本番環境設定が有効です')
        if HSTS_ENABLED:
            print(f'[SECURITY] HSTS有効 (max-age={HSTS_MAX_AGE})')
    else:
        print('[DEVELOPMENT] 開発環境設定が有効です')

    # デモユーザー初期化
    init_demo_users()

    protocol = 'https' if os.environ.get('MKS_FORCE_HTTPS', 'false').lower() in ('true', '1', 'yes') else 'http'
    print(f'アクセスURL: {protocol}://localhost:5100')
    print('=' * 60)

    debug = os.environ.get('MKS_DEBUG', 'false').lower() in ('1', 'true', 'yes')
    app.run(host='0.0.0.0', port=5100, debug=debug)
