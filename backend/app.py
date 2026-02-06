"""
建設土木ナレッジシステム - Flaskバックエンド
"""

import json
import logging
import os
import time
from datetime import datetime

import psutil
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# ログ設定
LOG_LEVEL = os.environ.get("MKS_LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO), format=LOG_FORMAT)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="../webui")
CORS(app)

# 環境設定
IS_PRODUCTION = os.environ.get("MKS_ENV", "development").lower() == "production"

# データストレージディレクトリ
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# アプリケーション起動時刻
APP_START_TIME = datetime.now()

# リクエストカウンター（Prometheus用）
REQUEST_METRICS = {
    "total_requests": 0,
    "success_requests": 0,
    "error_requests": 0,
    "response_times": [],
}

# ============================================================
# ヘルスチェック・監視エンドポイント
# ============================================================


@app.route("/api/health", methods=["GET"])
def health_check():
    """
    ヘルスチェックエンドポイント
    システムの健全性を確認するための基本的なエンドポイント
    """
    try:
        # データディレクトリのアクセス確認
        data_accessible = os.path.isdir(DATA_DIR) and os.access(
            DATA_DIR, os.R_OK | os.W_OK
        )

        # メモリ使用率
        memory = psutil.virtual_memory()
        memory_ok = memory.percent < 90

        # ディスク使用率
        disk = psutil.disk_usage("/")
        disk_ok = disk.percent < 95

        overall_healthy = data_accessible and memory_ok and disk_ok

        return jsonify(
            {
                "status": "healthy" if overall_healthy else "degraded",
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": (datetime.now() - APP_START_TIME).total_seconds(),
                "environment": "production" if IS_PRODUCTION else "development",
                "checks": {
                    "data_directory": "ok" if data_accessible else "error",
                    "memory": "ok" if memory_ok else "warning",
                    "disk": "ok" if disk_ok else "warning",
                },
            }
        ), (200 if overall_healthy else 503)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                }
            ),
            503,
        )


@app.route("/api/health/liveness", methods=["GET"])
def liveness_probe():
    """
    Liveness Probe（生存確認）
    アプリケーションが生存しているかを確認
    """
    return jsonify({"status": "alive", "timestamp": datetime.now().isoformat()}), 200


@app.route("/api/health/readiness", methods=["GET"])
def readiness_probe():
    """
    Readiness Probe（準備状態確認）
    アプリケーションがリクエストを受け付ける準備ができているかを確認
    """
    try:
        # データファイルのアクセス確認
        test_file = os.path.join(DATA_DIR, "knowledge.json")
        if os.path.exists(test_file):
            with open(test_file, "r", encoding="utf-8") as f:
                json.load(f)  # JSONパース可能か確認

        return (
            jsonify({"status": "ready", "timestamp": datetime.now().isoformat()}),
            200,
        )
    except Exception as e:
        logger.warning(f"Readiness check failed: {e}")
        return (
            jsonify(
                {
                    "status": "not_ready",
                    "timestamp": datetime.now().isoformat(),
                    "reason": str(e),
                }
            ),
            503,
        )


@app.route("/api/metrics", methods=["GET"])
def metrics():
    """
    メトリクスエンドポイント（Prometheus互換形式）
    """
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # Prometheus形式のメトリクス
        metrics_output = []

        # アプリケーションメトリクス
        uptime = (datetime.now() - APP_START_TIME).total_seconds()
        metrics_output.append(
            "# HELP mks_uptime_seconds Application uptime in seconds"
        )
        metrics_output.append("# TYPE mks_uptime_seconds gauge")
        metrics_output.append(f"mks_uptime_seconds {uptime:.2f}")

        # リクエストメトリクス
        metrics_output.append("# HELP mks_requests_total Total number of requests")
        metrics_output.append("# TYPE mks_requests_total counter")
        metrics_output.append(f'mks_requests_total {REQUEST_METRICS["total_requests"]}')

        # システムメトリクス
        metrics_output.append(
            "# HELP mks_memory_usage_percent Memory usage percentage"
        )
        metrics_output.append("# TYPE mks_memory_usage_percent gauge")
        metrics_output.append(f"mks_memory_usage_percent {memory.percent}")

        metrics_output.append("# HELP mks_disk_usage_percent Disk usage percentage")
        metrics_output.append("# TYPE mks_disk_usage_percent gauge")
        metrics_output.append(f"mks_disk_usage_percent {disk.percent}")

        metrics_output.append("# HELP mks_cpu_usage_percent CPU usage percentage")
        metrics_output.append("# TYPE mks_cpu_usage_percent gauge")
        metrics_output.append(f"mks_cpu_usage_percent {cpu_percent}")

        return (
            "\n".join(metrics_output),
            200,
            {"Content-Type": "text/plain; charset=utf-8"},
        )
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return (
            f"# Error collecting metrics: {e}",
            500,
            {"Content-Type": "text/plain; charset=utf-8"},
        )


@app.route("/api/status", methods=["GET"])
def system_status():
    """
    詳細なシステムステータス（管理者向け）
    """
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # 各データファイルの状態を確認
        data_files = {}
        for filename in [
            "knowledge.json",
            "sop.json",
            "incidents.json",
            "consultations.json",
            "regulations.json",
        ]:
            filepath = os.path.join(DATA_DIR, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        data_files[filename] = {
                            "exists": True,
                            "record_count": (
                                len(data) if isinstance(data, list) else "N/A"
                            ),
                            "size_kb": round(os.path.getsize(filepath) / 1024, 2),
                        }
                except Exception as e:
                    data_files[filename] = {"exists": True, "error": str(e)}
            else:
                data_files[filename] = {"exists": False}

        return (
            jsonify(
                {
                    "status": "operational",
                    "timestamp": datetime.now().isoformat(),
                    "environment": "production" if IS_PRODUCTION else "development",
                    "uptime_seconds": (datetime.now() - APP_START_TIME).total_seconds(),
                    "system": {
                        "memory": {
                            "total_gb": round(memory.total / (1024**3), 2),
                            "available_gb": round(memory.available / (1024**3), 2),
                            "usage_percent": memory.percent,
                        },
                        "disk": {
                            "total_gb": round(disk.total / (1024**3), 2),
                            "free_gb": round(disk.free / (1024**3), 2),
                            "usage_percent": disk.percent,
                        },
                        "cpu_percent": psutil.cpu_percent(interval=0.1),
                        "process_count": len(psutil.pids()),
                    },
                    "data_files": data_files,
                    "request_stats": {
                        "total_requests": REQUEST_METRICS["total_requests"],
                        "success_requests": REQUEST_METRICS["success_requests"],
                        "error_requests": REQUEST_METRICS["error_requests"],
                    },
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500


# リクエストカウントミドルウェア
@app.before_request
def before_request():
    """リクエスト開始時刻を記録"""
    request.start_time = time.time()
    REQUEST_METRICS["total_requests"] += 1


@app.after_request
def after_request(response):
    """レスポンス後にメトリクスを更新"""
    if hasattr(request, "start_time"):
        response_time = (time.time() - request.start_time) * 1000  # ms
        REQUEST_METRICS["response_times"].append(response_time)
        # 最新1000件のみ保持
        if len(REQUEST_METRICS["response_times"]) > 1000:
            REQUEST_METRICS["response_times"] = REQUEST_METRICS["response_times"][
                -1000:
            ]

    if response.status_code >= 400:
        REQUEST_METRICS["error_requests"] += 1
    else:
        REQUEST_METRICS["success_requests"] += 1

    return response


# ============================================================
# データモデル初期化
# ============================================================


def load_data(filename):
    """
    JSONファイルを安全に読み込む

    Args:
        filename: 読み込むJSONファイル名

    Returns:
        list: 読み込んだデータ（失敗時は空リスト）
    """
    filepath = os.path.join(DATA_DIR, filename)

    try:
        if not os.path.exists(filepath):
            print(f"[INFO] File not found: {filename} (returning empty list)")
            return []

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

            # データ型検証
            if not isinstance(data, list):
                print(
                    f"[WARN] {filename}: Expected list, got {type(data).__name__}. Returning empty list."
                )
                return []

            return data

    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON decode error in {filename}: {e}")
        return []
    except PermissionError as e:
        print(f"[ERROR] Permission denied reading {filename}: {e}")
        return []
    except UnicodeDecodeError as e:
        print(f"[ERROR] Encoding error reading {filename}: {e}")
        return []
    except Exception as e:
        print(f"[ERROR] Unexpected error reading {filename}: {type(e).__name__}: {e}")
        return []


def save_data(filename, data):
    """
    JSONファイルに安全にデータを保存

    Args:
        filename: 保存するJSONファイル名
        data: 保存するデータ

    Raises:
        Exception: 保存に失敗した場合
    """
    filepath = os.path.join(DATA_DIR, filename)

    try:
        # ディレクトリの存在確認
        os.makedirs(DATA_DIR, exist_ok=True)

        # データを書き込み
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(
            f'[INFO] Successfully saved {filename} ({len(data) if isinstance(data, list) else "N/A"} items)'
        )

    except PermissionError as e:
        print(f"[ERROR] Permission denied writing {filename}: {e}")
        raise
    except OSError as e:
        print(f"[ERROR] OS error writing {filename}: {e}")
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error writing {filename}: {type(e).__name__}: {e}")
        raise


# ============================================================
# API エンドポイント - ナレッジ管理
# ============================================================


@app.route("/api/knowledge", methods=["GET"])
def get_knowledge():
    """ナレッジ一覧取得"""
    knowledge_list = load_data("knowledge.json")

    # クエリパラメータでのフィルタリング
    category = request.args.get("category")
    search = request.args.get("search")
    tags = request.args.get("tags")

    filtered = knowledge_list

    if category:
        filtered = [k for k in filtered if k.get("category") == category]

    if search:
        search_lower = search.lower()
        filtered = [
            k
            for k in filtered
            if search_lower in k.get("title", "").lower()
            or search_lower in k.get("summary", "").lower()
        ]

    if tags:
        tag_list = tags.split(",")
        filtered = [
            k for k in filtered if any(tag in k.get("tags", []) for tag in tag_list)
        ]

    return jsonify({"success": True, "data": filtered, "total": len(filtered)})


@app.route("/api/knowledge/<int:knowledge_id>", methods=["GET"])
def get_knowledge_detail(knowledge_id):
    """ナレッジ詳細取得"""
    knowledge_list = load_data("knowledge.json")
    knowledge = next((k for k in knowledge_list if k["id"] == knowledge_id), None)

    if not knowledge:
        return jsonify({"success": False, "error": "Knowledge not found"}), 404

    return jsonify({"success": True, "data": knowledge})


@app.route("/api/knowledge", methods=["POST"])
def create_knowledge():
    """新規ナレッジ登録"""
    data = request.json
    knowledge_list = load_data("knowledge.json")

    # ID自動採番
    new_id = max([k["id"] for k in knowledge_list], default=0) + 1

    new_knowledge = {
        "id": new_id,
        "title": data.get("title"),
        "summary": data.get("summary"),
        "content": data.get("content"),
        "category": data.get("category"),
        "tags": data.get("tags", []),
        "status": "draft",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "owner": data.get("owner", "unknown"),
        "project": data.get("project"),
        "priority": data.get("priority", "medium"),
    }

    knowledge_list.append(new_knowledge)
    save_data("knowledge.json", knowledge_list)

    return jsonify({"success": True, "data": new_knowledge}), 201


@app.route("/api/knowledge/<int:knowledge_id>", methods=["PUT"])
def update_knowledge(knowledge_id):
    """ナレッジ更新"""
    data = request.json
    knowledge_list = load_data("knowledge.json")

    knowledge = next((k for k in knowledge_list if k["id"] == knowledge_id), None)
    if not knowledge:
        return jsonify({"success": False, "error": "Knowledge not found"}), 404

    # 更新
    knowledge.update(
        {
            "title": data.get("title", knowledge["title"]),
            "summary": data.get("summary", knowledge["summary"]),
            "content": data.get("content", knowledge["content"]),
            "category": data.get("category", knowledge["category"]),
            "tags": data.get("tags", knowledge["tags"]),
            "status": data.get("status", knowledge["status"]),
            "updated_at": datetime.now().isoformat(),
        }
    )

    save_data("knowledge.json", knowledge_list)

    return jsonify({"success": True, "data": knowledge})


# ============================================================
# API エンドポイント - SOP管理
# ============================================================


@app.route("/api/sop", methods=["GET"])
def get_sop():
    """SOP一覧取得"""
    sop_list = load_data("sop.json")
    return jsonify({"success": True, "data": sop_list, "total": len(sop_list)})


@app.route("/api/sop/<int:sop_id>", methods=["GET"])
def get_sop_detail(sop_id):
    """SOP詳細取得"""
    sop_list = load_data("sop.json")
    sop = next((s for s in sop_list if s["id"] == sop_id), None)

    if not sop:
        return jsonify({"success": False, "error": "SOP not found"}), 404

    return jsonify({"success": True, "data": sop})


# ============================================================
# API エンドポイント - 法令管理
# ============================================================


@app.route("/api/regulations", methods=["GET"])
def get_regulations():
    """法令一覧取得"""
    regulations = load_data("regulations.json")
    return jsonify({"success": True, "data": regulations, "total": len(regulations)})


@app.route("/api/regulations/<int:reg_id>", methods=["GET"])
def get_regulation_detail(reg_id):
    """法令詳細取得"""
    regulations = load_data("regulations.json")
    regulation = next((r for r in regulations if r["id"] == reg_id), None)

    if not regulation:
        return jsonify({"success": False, "error": "Regulation not found"}), 404

    return jsonify({"success": True, "data": regulation})


# ============================================================
# API エンドポイント - 事故・ヒヤリレポート
# ============================================================


@app.route("/api/incidents", methods=["GET"])
def get_incidents():
    """事故レポート一覧取得"""
    incidents = load_data("incidents.json")
    return jsonify({"success": True, "data": incidents, "total": len(incidents)})


@app.route("/api/incidents/<int:incident_id>", methods=["GET"])
def get_incident_detail(incident_id):
    """事故レポート詳細取得"""
    incidents = load_data("incidents.json")
    incident = next((i for i in incidents if i["id"] == incident_id), None)

    if not incident:
        return jsonify({"success": False, "error": "Incident not found"}), 404

    return jsonify({"success": True, "data": incident})


@app.route("/api/incidents", methods=["POST"])
def create_incident():
    """事故レポート登録"""
    data = request.json
    incidents = load_data("incidents.json")

    new_id = max([i["id"] for i in incidents], default=0) + 1

    new_incident = {
        "id": new_id,
        "title": data.get("title"),
        "description": data.get("description"),
        "project": data.get("project"),
        "date": data.get("date"),
        "severity": data.get("severity", "medium"),
        "status": "reported",
        "corrective_actions": data.get("corrective_actions", []),
        "created_at": datetime.now().isoformat(),
        "reporter": data.get("reporter"),
    }

    incidents.append(new_incident)
    save_data("incidents.json", incidents)

    return jsonify({"success": True, "data": new_incident}), 201


# ============================================================
# API エンドポイント - 専門家相談
# ============================================================


@app.route("/api/consultations", methods=["GET"])
def get_consultations():
    """専門家相談一覧取得"""
    consultations = load_data("consultations.json")
    return jsonify(
        {"success": True, "data": consultations, "total": len(consultations)}
    )


@app.route("/api/consultations/<int:consult_id>", methods=["GET"])
def get_consultation_detail(consult_id):
    """専門家相談詳細取得"""
    consultations = load_data("consultations.json")
    consultation = next((c for c in consultations if c["id"] == consult_id), None)

    if not consultation:
        return jsonify({"success": False, "error": "Consultation not found"}), 404

    return jsonify({"success": True, "data": consultation})


@app.route("/api/consultations", methods=["POST"])
def create_consultation():
    """専門家相談登録"""
    data = request.json
    consultations = load_data("consultations.json")

    new_id = max([c["id"] for c in consultations], default=0) + 1

    new_consultation = {
        "id": new_id,
        "title": data.get("title"),
        "question": data.get("question"),
        "category": data.get("category"),
        "priority": data.get("priority", "medium"),
        "status": "pending",
        "requester": data.get("requester"),
        "expert": None,
        "answer": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    consultations.append(new_consultation)
    save_data("consultations.json", consultations)

    return jsonify({"success": True, "data": new_consultation}), 201


# ============================================================
# API エンドポイント - 承認フロー
# ============================================================


@app.route("/api/approvals", methods=["GET"])
def get_approvals():
    """承認フロー一覧取得"""
    approvals = load_data("approvals.json")

    # ステータスフィルタ
    status = request.args.get("status")
    if status:
        approvals = [a for a in approvals if a.get("status") == status]

    return jsonify({"success": True, "data": approvals, "total": len(approvals)})


@app.route("/api/approvals/<int:approval_id>/approve", methods=["POST"])
def approve(approval_id):
    """承認実行"""
    data = request.json
    approvals = load_data("approvals.json")

    approval = next((a for a in approvals if a["id"] == approval_id), None)
    if not approval:
        return jsonify({"success": False, "error": "Approval not found"}), 404

    approval["status"] = "approved"
    approval["approved_at"] = datetime.now().isoformat()
    approval["approver"] = data.get("approver")
    approval["comment"] = data.get("comment", "")

    save_data("approvals.json", approvals)

    return jsonify({"success": True, "data": approval})


@app.route("/api/approvals/<int:approval_id>/reject", methods=["POST"])
def reject(approval_id):
    """承認却下"""
    data = request.json
    approvals = load_data("approvals.json")

    approval = next((a for a in approvals if a["id"] == approval_id), None)
    if not approval:
        return jsonify({"success": False, "error": "Approval not found"}), 404

    approval["status"] = "rejected"
    approval["rejected_at"] = datetime.now().isoformat()
    approval["approver"] = data.get("approver")
    approval["reason"] = data.get("reason", "")

    save_data("approvals.json", approvals)

    return jsonify({"success": True, "data": approval})


# ============================================================
# API エンドポイント - ダッシュボード統計
# ============================================================


@app.route("/api/dashboard/stats", methods=["GET"])
def get_dashboard_stats():
    """ダッシュボード統計情報取得"""
    knowledge_list = load_data("knowledge.json")
    sop_list = load_data("sop.json")
    incidents = load_data("incidents.json")
    approvals = load_data("approvals.json")

    stats = {
        "knowledge_reuse_rate": 71,  # 再利用率
        "accident_free_days": 184,  # 事故ゼロ継続日数
        "active_audits": 6,  # 実施中監査
        "delayed_corrections": 3,  # 是正遅延
        "total_knowledge": len(knowledge_list),
        "total_sop": len(sop_list),
        "recent_incidents": len(
            [i for i in incidents if i.get("status") == "reported"]
        ),
        "pending_approvals": len(
            [a for a in approvals if a.get("status") == "pending"]
        ),
    }

    return jsonify({"success": True, "data": stats})


# ============================================================
# 静的ファイル配信
# ============================================================


@app.route("/")
def index():
    """トップページ"""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def serve_static(path):
    """静的ファイル配信"""
    return send_from_directory(app.static_folder, path)


# ============================================================
# アプリケーション起動
# ============================================================

if __name__ == "__main__":
    import os

    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() in ("true", "1", "yes")

    print("=" * 60)
    print("建設土木ナレッジシステム - サーバー起動中")
    print("=" * 60)
    print("アクセスURL: http://localhost:5000")
    if debug_mode:
        print(
            "[WARNING] Debug mode is ENABLED. This should NEVER be used in production!"
        )
    else:
        print("[INFO] Debug mode is disabled (production mode)")
    print("=" * 60)

    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
