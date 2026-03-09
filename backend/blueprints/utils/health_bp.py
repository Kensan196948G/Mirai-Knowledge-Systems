"""
blueprints/utils/health_bp.py - ヘルスチェック・メトリクス・ドキュメント・静的ファイル Blueprint

Phase I-4: app_v2.py から以下のルートを移行
  GET /api/v1/metrics        - Prometheus互換カスタムメトリクス
  GET /api/docs              - Swagger UI
  GET /api/openapi.yaml      - OpenAPI仕様
  GET /                      - トップページ
  GET /index.html            - トップページ（エイリアス）
  GET /<path:path>           - 静的ファイル配信
"""

import logging
import os
import time
from collections import Counter

import psutil
from flask import Blueprint, Response, current_app, jsonify, send_from_directory
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

logger = logging.getLogger(__name__)

health_bp = Blueprint("health", __name__)


# ============================================================
# Prometheus互換カスタムメトリクスエンドポイント
# ============================================================


@health_bp.route("/api/v1/metrics", methods=["GET"])
def get_metrics():
    """
    Prometheus互換メトリクスエンドポイント

    Returns:
        text/plain: Prometheus形式のメトリクスデータ
    """
    # metrics_storage は app_v2 モジュールレベルに存在するため遅延インポート
    from app_helpers import load_data
    import app_v2 as _app_v2

    metrics_storage = _app_v2.metrics_storage

    # システムメトリクス取得
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    # ナレッジデータ統計
    knowledge_list = load_data("knowledge.json")
    sop_list = load_data("sop.json")

    # アクセスログ分析
    access_logs = load_data("access_logs.json")

    # アクティブユーザー計算（過去15分以内にアクセスがあったユーザー）
    from datetime import datetime
    now = datetime.now()
    active_users = set()
    active_sessions = set()
    login_success = 0
    login_failure = 0

    for log in access_logs:
        try:
            log_time = datetime.fromisoformat(log.get("timestamp", ""))
            if (now - log_time).total_seconds() < 900:  # 15分以内
                user_id = log.get("user_id")
                if user_id:
                    active_users.add(user_id)
                    active_sessions.add(log.get("session_id", ""))

            # ログイン統計
            if log.get("action") == "auth.login":
                if log.get("status") == "success":
                    login_success += 1
                else:
                    login_failure += 1
        except (ValueError, TypeError):
            continue

    # カテゴリ別ナレッジ数
    category_counts = Counter([k.get("category", "unknown") for k in knowledge_list])

    # HTTPリクエストメトリクス集計
    http_requests_metrics = []
    for key, count in metrics_storage["http_requests_total"].items():
        parts = key.split("_", 2)
        if len(parts) >= 3:
            method, endpoint, status = parts[0], parts[1], parts[2]
            http_requests_metrics.append(
                f'http_requests_total{{method="{method}",endpoint="{endpoint}",status="{status}"}} {count}'
            )

    # 応答時間メトリクス（ヒストグラム風）
    response_time_metrics = []
    for endpoint, durations in metrics_storage["http_request_duration_seconds"].items():
        if durations:
            sum(durations) / len(durations)
            max_duration = max(durations)
            min(durations)

            # パーセンタイル計算
            sorted_durations = sorted(durations)
            p50 = (
                sorted_durations[len(sorted_durations) // 2] if sorted_durations else 0
            )
            p95_idx = int(len(sorted_durations) * 0.95)
            p95 = (
                sorted_durations[p95_idx]
                if p95_idx < len(sorted_durations)
                else max_duration
            )
            p99_idx = int(len(sorted_durations) * 0.99)
            p99 = (
                sorted_durations[p99_idx]
                if p99_idx < len(sorted_durations)
                else max_duration
            )

            response_time_metrics.extend(
                [
                    f'http_request_duration_seconds{{endpoint="{endpoint}",quantile="0.5"}} {p50:.4f}',
                    f'http_request_duration_seconds{{endpoint="{endpoint}",quantile="0.95"}} {p95:.4f}',
                    f'http_request_duration_seconds{{endpoint="{endpoint}",quantile="0.99"}} {p99:.4f}',
                    f'http_request_duration_seconds_sum{{endpoint="{endpoint}"}} {sum(durations):.4f}',
                    f'http_request_duration_seconds_count{{endpoint="{endpoint}"}} {len(durations)}',
                ]
            )

    # Prometheus形式のテキスト生成
    metrics_text = f"""# HELP app_info Application information
# TYPE app_info gauge
app_info{{version="2.0",name="mirai-knowledge-system"}} 1

# HELP app_uptime_seconds Application uptime in seconds
# TYPE app_uptime_seconds counter
app_uptime_seconds {time.time() - metrics_storage["start_time"]:.2f}

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

# HELP active_users Number of active users (last 15 minutes)
# TYPE active_users gauge
active_users {len(active_users)}

# HELP active_sessions Number of active sessions
# TYPE active_sessions gauge
active_sessions {len(active_sessions)}

# HELP login_attempts_total Total number of login attempts
# TYPE login_attempts_total counter
login_attempts_total{{status="success"}} {login_success}
login_attempts_total{{status="failure"}} {login_failure}

# HELP knowledge_total Total number of knowledge items
# TYPE knowledge_total gauge
knowledge_total {len(knowledge_list)}

# HELP knowledge_by_category Knowledge items by category
# TYPE knowledge_by_category gauge
"""

    # カテゴリ別メトリクス追加
    for category, count in category_counts.items():
        metrics_text += f'knowledge_by_category{{category="{category}"}} {count}\n'

    metrics_text += f"""
# HELP sop_total Total number of SOP documents
# TYPE sop_total gauge
sop_total {len(sop_list)}

# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
"""

    # HTTPリクエストメトリクス追加
    if http_requests_metrics:
        metrics_text += "\n".join(http_requests_metrics) + "\n"

    metrics_text += """
# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
"""

    # 応答時間メトリクス追加
    if response_time_metrics:
        metrics_text += "\n".join(response_time_metrics) + "\n"

    # エラーメトリクス
    metrics_text += """
# HELP http_errors_total Total number of HTTP errors
# TYPE http_errors_total counter
"""
    for error_code, count in metrics_storage["errors"].items():
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

    return Response(metrics_text, mimetype="text/plain; version=0.0.4; charset=utf-8")


# ============================================================
# Swagger UI統合（API Documentation）
# ============================================================


@health_bp.route("/api/docs")
def api_docs():
    """Swagger UI for API documentation"""
    return send_from_directory(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "swagger-ui.html")


@health_bp.route("/api/openapi.yaml")
def openapi_spec():
    """OpenAPI仕様ファイルを配信"""
    return send_from_directory(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "openapi.yaml")


# ============================================================
# 公開エンドポイント（認証不要）
# ============================================================


@health_bp.route("/")
@health_bp.route("/index.html")
def index():
    """トップページ"""
    response = send_from_directory(current_app.static_folder, "index.html")
    # HTMLファイルはキャッシュしない（動的更新対応）
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@health_bp.route("/<path:path>")
def serve_static(path):
    """静的ファイル配信（キャッシュ最適化）"""
    response = send_from_directory(current_app.static_folder, path)

    # ファイルタイプに応じたキャッシュ設定
    if path.endswith((".js", ".css")):
        # JS/CSSは1時間キャッシュ
        response.headers["Cache-Control"] = "public, max-age=3600"
    elif path.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp")):
        # 画像は1日キャッシュ
        response.headers["Cache-Control"] = "public, max-age=86400"
    elif path.endswith((".woff", ".woff2", ".ttf", ".eot")):
        # フォントは1週間キャッシュ
        response.headers["Cache-Control"] = "public, max-age=604800"
    elif path.endswith(".html"):
        # HTMLファイルはキャッシュしない
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    return response
