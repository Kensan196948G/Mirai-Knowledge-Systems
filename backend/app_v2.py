"""
建設土木ナレッジシステム - 認証機能付きFlaskバックエンド
JSONベース + JWT認証 + RBAC
"""
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import datetime, timedelta
from functools import wraps
import json
import os
import hashlib

app = Flask(__name__, static_folder='../webui')
CORS(app)

# 設定
DEFAULT_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
app.config['DATA_DIR'] = os.environ.get('MKS_DATA_DIR', DEFAULT_DATA_DIR)

# JWT設定
app.config['JWT_SECRET_KEY'] = os.environ.get('MKS_JWT_SECRET_KEY', 'change-me')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
jwt = JWTManager(app)

# データストレージディレクトリ
def get_data_dir():
    """データ保存先ディレクトリを取得"""
    data_dir = app.config.get('DATA_DIR', DEFAULT_DATA_DIR)
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

# セキュリティヘッダー
@app.after_request
def add_security_headers(response):
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'DENY')
    response.headers.setdefault('Referrer-Policy', 'no-referrer')
    response.headers.setdefault(
        'Permissions-Policy',
        'geolocation=(), microphone=(), camera=()'
    )
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
    """パスワードをハッシュ化"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """パスワード検証"""
    return hash_password(password) == password_hash

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
            current_user_id = get_jwt_identity()
            users = load_users()
            user = next((u for u in users if u['id'] == current_user_id), None)
            
            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
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
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_data(filename, data):
    """JSONファイルにデータを保存"""
    filepath = os.path.join(get_data_dir(), filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================
# 認証API
# ============================================================

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    """ログイン"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
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
    
    # トークン生成
    access_token = create_access_token(
        identity=user['id'],
        additional_claims={'roles': user.get('roles', [])}
    )
    refresh_token = create_refresh_token(identity=user['id'])
    
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
    current_user_id = get_jwt_identity()
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
# ナレッジ管理API（権限チェック付き）
# ============================================================

@app.route('/api/v1/knowledge', methods=['GET'])
@jwt_required()
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
    
    if search:
        search_lower = search.lower()
        filtered = [k for k in filtered if 
                   search_lower in k.get('title', '').lower() or 
                   search_lower in k.get('summary', '').lower()]
    
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
@jwt_required()
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
@jwt_required()
@check_permission('knowledge.create')
def create_knowledge():
    """新規ナレッジ登録"""
    current_user_id = get_jwt_identity()
    data = request.json
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
    
    return jsonify({
        'success': True,
        'data': new_knowledge
    }), 201

# 他のエンドポイントも同様に権限チェックを追加...
# （簡潔にするため、主要なものの定義）

@app.route('/api/v1/sop', methods=['GET'])
@jwt_required()
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
# 公開エンドポイント（認証不要）
# ============================================================

@app.route('/')
def index():
    """トップページ"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """静的ファイル配信"""
    return send_from_directory(app.static_folder, path)

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

if __name__ == '__main__':
    print('=' * 60)
    print('建設土木ナレッジシステム - サーバー起動中')
    print('=' * 60)
    
    # デモユーザー初期化
    init_demo_users()
    
    print(f'アクセスURL: http://localhost:5000')
    print('=' * 60)
    
    debug = os.environ.get('MKS_DEBUG', 'true').lower() in ('1', 'true', 'yes')
    app.run(host='0.0.0.0', port=5000, debug=debug)
