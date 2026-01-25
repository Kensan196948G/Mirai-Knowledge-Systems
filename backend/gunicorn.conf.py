# Gunicorn設定ファイル
# Mirai Knowledge System - WSGIサーバー設定
#
# ポート番号（固定 - 変更不可）:
#   開発環境: 5100
#   本番環境: 8100

import multiprocessing
import os

# ==============================================================================
# 環境設定
# ==============================================================================

# 環境モード判定
ENV = os.getenv("MKS_ENV", "development").lower()
IS_PRODUCTION = ENV == "production"

# ポート番号（環境変数から取得、デフォルトは環境に応じて設定）
# 開発環境: 5100 (固定)
# 本番環境: 8100 (固定)
DEFAULT_PORT = "8100" if IS_PRODUCTION else "5100"
HTTP_PORT = int(os.getenv("MKS_HTTP_PORT", DEFAULT_PORT))

# ==============================================================================
# サーバーソケット設定
# ==============================================================================

# バインドアドレス（環境変数から動的に取得）
# 外部アクセスを許可する場合: 0.0.0.0:PORT
# Nginxプロキシのみの場合: 127.0.0.1:PORT（推奨）
bind = f"0.0.0.0:{HTTP_PORT}"

# バックログ（保留中の接続数）
backlog = 2048

# ==============================================================================
# ワーカープロセス設定
# ==============================================================================

# ワーカープロセス数（推奨: CPU コア数 * 2 + 1）
workers = multiprocessing.cpu_count() * 2 + 1

# ワーカークラス（同期/非同期）
# - sync: 同期（デフォルト、安定）
# - gevent: 非同期（高スループット、geventライブラリ必要） ← Socket.IO用に変更
# - eventlet: 非同期（高スループット、eventletライブラリ必要）
worker_class = "gevent"

# ワーカーの最大リクエスト処理数（メモリリーク対策）
# この数を処理したらワーカーを再起動
max_requests = 1000
max_requests_jitter = 50  # ランダムに±50で再起動（同時再起動を防ぐ）

# ワーカータイムアウト（秒）
timeout = 30

# Graceful タイムアウト（秒）
graceful_timeout = 30

# Keep-Alive（秒）
keepalive = 2

# ==============================================================================
# プロセス命名
# ==============================================================================

proc_name = "mirai-knowledge-system"

# ==============================================================================
# ログ設定
# ==============================================================================

# ログレベル
# - debug, info, warning, error, critical
loglevel = os.getenv("MKS_LOG_LEVEL", "info")

# アクセスログ
accesslog = os.getenv("MKS_ACCESS_LOG", "/var/log/mirai-knowledge/access.log")

# エラーログ
errorlog = os.getenv("MKS_ERROR_LOG", "/var/log/mirai-knowledge/error.log")

# アクセスログフォーマット
# JSON形式で構造化ログを出力（ログ分析ツールとの統合が容易）
access_log_format = '''{"timestamp":"%(t)s","remote_addr":"%(h)s","method":"%(m)s","path":"%(U)s","query":"%(q)s","protocol":"%(H)s","status":%(s)s,"size":%(b)s,"referer":"%(f)s","user_agent":"%(a)s","response_time_us":%(D)s,"response_time_ms":%(M)s,"process_id":"%(p)s"}'''

# 従来形式（コメントアウト、必要に応じて切り替え可能）
# access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
# %(h)s - リモートホスト
# %(l)s - '-' (未使用)
# %(u)s - ユーザー名
# %(t)s - タイムスタンプ
# %(r)s - リクエストライン
# %(s)s - ステータスコード
# %(b)s - レスポンスサイズ
# %(f)s - Referer
# %(a)s - User-Agent
# %(D)s - 処理時間（マイクロ秒）

# JSON形式のフィールド説明:
# %(t)s - タイムスタンプ（例: [09/Jan/2026:09:30:00 +0900]）
# %(h)s - リモートホスト（IPアドレス）
# %(m)s - HTTPメソッド（GET, POST等）
# %(U)s - URLパス（クエリ文字列除く）
# %(q)s - クエリ文字列
# %(H)s - プロトコル（HTTP/1.1等）
# %(s)s - ステータスコード（200, 404等）
# %(b)s - レスポンスサイズ（バイト）
# %(f)s - Referer
# %(a)s - User-Agent
# %(D)s - レスポンス時間（マイクロ秒）
# %(M)s - レスポンス時間（ミリ秒）
# %(p)s - プロセスID

# ==============================================================================
# セキュリティ設定
# ==============================================================================

# ユーザー/グループ（rootで起動した場合に切り替え）
user = os.getenv("MKS_USER", "kensan")
group = os.getenv("MKS_GROUP", "kensan")

# umask（新規作成ファイルのパーミッション）
umask = 0o007

# ==============================================================================
# サーバーフック
# ==============================================================================

def on_starting(server):
    """サーバー起動時"""
    server.log.info("=" * 60)
    server.log.info("Mirai Knowledge System - Gunicorn Starting")
    server.log.info("=" * 60)
    server.log.info(f"Workers: {workers}")
    server.log.info(f"Bind: {bind}")
    server.log.info(f"Worker class: {worker_class}")
    server.log.info("=" * 60)

def on_reload(server):
    """設定リロード時"""
    server.log.info("Gunicorn configuration reloaded")

def when_ready(server):
    """サーバー準備完了時"""
    server.log.info("Gunicorn is ready to handle requests")

def pre_fork(server, worker):
    """ワーカープロセス fork 前"""
    pass

def post_fork(server, worker):
    """ワーカープロセス fork 後"""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def pre_exec(server):
    """サーバー再起動前"""
    server.log.info("Forked child, re-executing.")

def worker_int(worker):
    """ワーカー割り込み時（SIGINT）"""
    worker.log.info(f"Worker received INT or QUIT signal (pid: {worker.pid})")

def worker_abort(worker):
    """ワーカー強制終了時（SIGABRT）"""
    worker.log.info(f"Worker received SIGABRT signal (pid: {worker.pid})")

# ==============================================================================
# SSL/TLS設定（オプション）
# ==============================================================================

# Gunicorn単体でSSL/TLSを使う場合（通常はNginxで終端するので不要）
# keyfile = "/path/to/server.key"
# certfile = "/path/to/server.crt"
# ca_certs = "/path/to/ca.crt"
# ssl_version = ssl.PROTOCOL_TLSv1_2
# cert_reqs = ssl.CERT_REQUIRED

# ==============================================================================
# 開発環境設定（コメントアウト推奨）
# ==============================================================================

# 開発環境でのみ使用（本番では必ずコメントアウト）
# reload = True  # コード変更時に自動リロード
# reload_extra_files = [
#     "/path/to/templates/",
#     "/path/to/static/",
# ]

# ==============================================================================
# パフォーマンスチューニング（環境に応じて調整）
# ==============================================================================

# スレッド数（worker_class = "sync" の場合のみ有効）
# threads = 2

# ワーカー再起動前の最大接続数
# worker_connections = 1000

# リクエストボディの最大サイズ（バイト）
# limit_request_line = 4096
# limit_request_fields = 100
# limit_request_field_size = 8190

# ==============================================================================
# 環境変数設定
# ==============================================================================

# .envファイルから環境変数を読み込む
raw_env = [
    f"MKS_ENV={os.getenv('MKS_ENV', 'production')}",
    f"DATABASE_URL={os.getenv('DATABASE_URL', '')}",
    f"MKS_JWT_SECRET_KEY={os.getenv('MKS_JWT_SECRET_KEY', '')}",
    f"MKS_SECRET_KEY={os.getenv('MKS_SECRET_KEY', '')}",
    f"MKS_USE_POSTGRESQL={os.getenv('MKS_USE_POSTGRESQL', 'true')}",
    f"MKS_CORS_ORIGINS={os.getenv('MKS_CORS_ORIGINS', '')}",
]
