"""
ナレッジ管理APIエンドポイント - Blueprint版
Phase H-1: app_v2.py knowledge エンドポイント完全移行

移行エンドポイント一覧（12件）:
  GET    /api/v1/knowledge                       - ナレッジ一覧取得（フィルタ・ページネーション）
  GET    /api/v1/knowledge/popular               - 人気ナレッジTop N
  GET    /api/v1/knowledge/recent                - 最近追加ナレッジ
  GET    /api/v1/knowledge/favorites             - お気に入りナレッジ
  GET    /api/v1/knowledge/tags                  - タグクラウド集計
  GET    /api/v1/knowledge/<id>                  - ナレッジ詳細取得
  GET    /api/v1/knowledge/<id>/related          - 関連ナレッジ（MLアルゴリズム）
  POST   /api/v1/knowledge                       - 新規ナレッジ登録
  PUT    /api/v1/knowledge/<id>                  - ナレッジ更新
  DELETE /api/v1/knowledge/<id>                  - ナレッジ削除
  DELETE /api/v1/favorites/<id>                  - お気に入り削除
  GET    /api/v1/search/unified                  - 横断検索
"""

import logging
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app_helpers import (
    CacheInvalidator,
    cache_get,
    cache_set,
    check_permission,
    get_cache_key,
    get_user_permissions,
    highlight_text,
    load_data,
    load_users,
    log_access,
    recommendation_engine,
    save_data,
    search_in_fields,
    validate_request,
)
from app_helpers import create_notification  # 通知ヘルパー
from schemas import KnowledgeCreateSchema

logger = logging.getLogger(__name__)

knowledge_bp = Blueprint("knowledge", __name__, url_prefix="/api/v1")


# ============================================================
# Phase G-3-3: Blueprint移行デモ用エンドポイント（後方互換）
# ============================================================


@knowledge_bp.route("/ping", methods=["GET"])
def ping():
    """Blueprint稼働確認エンドポイント（後方互換）"""
    return jsonify({
        "status": "ok",
        "source": "knowledge_blueprint",
        "blueprint_name": knowledge_bp.name,
        "timestamp": datetime.now().isoformat(),
        "phase": "H-1",
    }), 200


# ============================================================
# ナレッジ管理API
# NOTE: 静的パス（/popular, /recent 等）を動的パス（/<int:id>）より
#       先に定義することでルーティングの曖昧さを排除する
# ============================================================


@knowledge_bp.route("/knowledge", methods=["GET"])
@check_permission("knowledge.read")
def get_knowledge():
    """ナレッジ一覧取得（フィルタ・ページネーション・全文検索・ハイライト対応）"""
    try:
        current_user_id = get_jwt_identity()
        log_access(current_user_id, "knowledge.list", "knowledge")

        # クエリパラメータ
        category = request.args.get("category")
        search = request.args.get("search")
        tags = request.args.get("tags")
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        highlight_key = request.args.get("highlight", "false")

        # キャッシュキー生成
        cache_key = get_cache_key(
            "knowledge_list",
            category or "",
            search or "",
            tags or "",
            highlight_key,
            page,
            per_page,
        )

        # キャッシュチェック
        cached_result = cache_get(cache_key)
        if cached_result:
            logger.info("Cache hit: knowledge_list - %s", cache_key)
            return jsonify(cached_result)

        knowledge_list = load_data("knowledge.json") or []
        filtered = knowledge_list

        if category:
            filtered = [k for k in filtered if k.get("category") == category]

        # 全文検索（title, summary, content フィールド対応）
        if search:
            highlight = highlight_key == "true"
            filtered_with_score = []

            for k in filtered:
                matched_fields, score = search_in_fields(
                    k, search, ["title", "summary", "content"]
                )
                if matched_fields:
                    k_copy = k.copy()
                    k_copy["matched_fields"] = matched_fields
                    k_copy["relevance_score"] = score

                    if highlight:
                        for field in ["title", "summary", "content"]:
                            if field in k_copy and k_copy[field]:
                                k_copy[field] = highlight_text(k_copy[field], search)

                    filtered_with_score.append(k_copy)

            # スコア順にソート
            filtered = sorted(
                filtered_with_score,
                key=lambda x: x["relevance_score"],
                reverse=True,
            )

        if tags:
            tag_list = tags.split(",")
            filtered = [
                k for k in filtered
                if any(tag in k.get("tags", []) for tag in tag_list)
            ]

        # ページネーション
        total_items = len(filtered)
        per_page = min(per_page, 100)
        total_pages = (total_items + per_page - 1) // per_page if per_page > 0 else 1
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_data = filtered[start_idx:end_idx]

        response_data = {
            "success": True,
            "data": paginated_data,
            "pagination": {
                "total_items": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "per_page": per_page,
            },
        }
        cache_set(cache_key, response_data, ttl=3600)  # 1時間
        logger.info("Cache set: knowledge_list - %s", cache_key)

        return jsonify(response_data)
    except Exception as e:
        logger.error("get_knowledge: %s: %s", type(e).__name__, e)
        raise  # Flask の 500 ハンドラ（internal_error）に委譲


@knowledge_bp.route("/knowledge/popular", methods=["GET"])
@check_permission("knowledge.read")
def get_popular_knowledge():
    """人気ナレッジTop Nを取得（閲覧数順）"""
    try:
        current_user_id = get_jwt_identity()
        log_access(current_user_id, "knowledge.popular", "knowledge")

        limit = request.args.get("limit", 10, type=int)
        limit = min(limit, 50)  # 最大50件

        cache_key = get_cache_key("knowledge_popular", limit)
        cached_result = cache_get(cache_key)
        if cached_result:
            logger.info("Cache hit: knowledge_popular - %s", cache_key)
            return jsonify(cached_result)

        knowledge_list = load_data("knowledge.json") or []

        sorted_knowledge = sorted(
            knowledge_list,
            key=lambda k: k.get("views", 0) if k else 0,
            reverse=True,
        )[:limit]

        response_data = {"success": True, "data": sorted_knowledge}
        cache_set(cache_key, response_data, ttl=3600)  # 1時間
        logger.info("Cache set: knowledge_popular - %s", cache_key)

        return jsonify(response_data)
    except Exception as e:
        logger.error("get_popular_knowledge: %s: %s", type(e).__name__, e)
        return jsonify({"success": True, "data": []})


@knowledge_bp.route("/knowledge/recent", methods=["GET"])
@check_permission("knowledge.read")
def get_recent_knowledge():
    """最近追加されたナレッジを取得（作成日時順、キャッシュ対応）

    NOTE: 日付ソート処理のため、キャッシュ優先度中。
    """
    try:
        current_user_id = get_jwt_identity()
        log_access(current_user_id, "knowledge.recent", "knowledge")

        limit = request.args.get("limit", 10, type=int)
        days = request.args.get("days", 7, type=int)  # デフォルト7日以内
        limit = min(limit, 50)

        cache_key = get_cache_key("knowledge_recent", limit, days)
        cached_result = cache_get(cache_key)
        if cached_result:
            logger.info("Cache hit: knowledge_recent - %s", cache_key)
            return jsonify(cached_result)

        knowledge_list = load_data("knowledge.json") or []
        cutoff_date = datetime.now() - timedelta(days=days)

        recent_knowledge = []
        for k in knowledge_list or []:
            if not k:
                continue
            created_at = k.get("created_at")
            if created_at:
                try:
                    created_date = datetime.fromisoformat(
                        created_at.replace("Z", "+00:00")
                    )
                    if created_date >= cutoff_date:
                        recent_knowledge.append(k)
                except Exception as parse_err:
                    logger.debug(
                        "Failed to parse created_at for knowledge id=%s: %s",
                        k.get("id"),
                        str(parse_err),
                    )

        sorted_knowledge = sorted(
            recent_knowledge,
            key=lambda k: k.get("created_at", "") if k else "",
            reverse=True,
        )[:limit]

        response_data = {"success": True, "data": sorted_knowledge}
        cache_set(cache_key, response_data, ttl=900)  # 15分（時間依存データ）
        logger.info("Cache set: knowledge_recent - %s", cache_key)

        return jsonify(response_data)
    except Exception as e:
        logger.error("get_recent_knowledge: %s: %s", type(e).__name__, e)
        return jsonify({"success": True, "data": []})


@knowledge_bp.route("/knowledge/favorites", methods=["GET"])
@jwt_required()
def get_favorite_knowledge():
    """お気に入りナレッジを取得"""
    try:
        current_user_id = get_jwt_identity()
        log_access(current_user_id, "knowledge.favorites", "knowledge")

        favorites = load_data("users_favorites.json") or []
        user_favs = [
            f for f in favorites
            if str(f.get("user_id")) == str(current_user_id)
        ]
        fav_ids = {str(f.get("knowledge_id")) for f in user_favs}

        if not fav_ids:
            return jsonify({"success": True, "data": []})

        knowledge_list = load_data("knowledge.json") or []
        result = [k for k in knowledge_list if str(k.get("id")) in fav_ids]

        return jsonify({"success": True, "data": result})
    except Exception as e:
        logger.error("get_favorite_knowledge: %s: %s", type(e).__name__, e)
        return jsonify({"success": True, "data": []})


@knowledge_bp.route("/knowledge/tags", methods=["GET"])
@check_permission("knowledge.read")
def get_knowledge_tags():
    """ナレッジのタグ集計を取得（タグクラウド用、キャッシュ対応）

    NOTE: 全スキャン+集計処理（O(n)）のため、キャッシュ優先度高。
    """
    try:
        current_user_id = get_jwt_identity()
        log_access(current_user_id, "knowledge.tags", "knowledge")

        cache_key = get_cache_key("knowledge_tags")
        cached_result = cache_get(cache_key)
        if cached_result:
            logger.info("Cache hit: knowledge_tags - %s", cache_key)
            return jsonify(cached_result)

        knowledge_list = load_data("knowledge.json") or []

        tag_count = {}
        for k in knowledge_list or []:
            if not k:
                continue
            tags = k.get("tags", []) or []
            for tag in tags:
                if tag:
                    tag_count[tag] = tag_count.get(tag, 0) + 1

        sorted_tags = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)
        tag_list = [
            {"name": tag, "count": count, "size": min(count // 5 + 1, 5)}
            for tag, count in sorted_tags
        ]

        response_data = {"success": True, "data": tag_list}
        cache_set(cache_key, response_data, ttl=1800)  # 30分
        logger.info("Cache set: knowledge_tags - %s", cache_key)

        return jsonify(response_data)
    except Exception as e:
        logger.error("get_knowledge_tags: %s: %s", type(e).__name__, e)
        return jsonify({"success": True, "data": []})


@knowledge_bp.route("/knowledge/<int:knowledge_id>", methods=["GET"])
@check_permission("knowledge.read")
def get_knowledge_detail(knowledge_id):
    """ナレッジ詳細取得"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "knowledge.view", "knowledge", knowledge_id)

    knowledge_list = load_data("knowledge.json")
    knowledge = next((k for k in knowledge_list if k["id"] == knowledge_id), None)

    if not knowledge:
        return jsonify({"success": False, "error": "Knowledge not found"}), 404

    return jsonify({"success": True, "data": knowledge})


@knowledge_bp.route("/knowledge/<int:knowledge_id>/related", methods=["GET"])
@check_permission("knowledge.read")
def get_related_knowledge(knowledge_id):
    """
    関連ナレッジを取得（キャッシュ対応）

    クエリパラメータ:
        limit: 取得件数（デフォルト: 5）
        algorithm: アルゴリズム（tag/category/keyword/hybrid、デフォルト: hybrid）
        min_score: 最小スコア閾値（デフォルト: 0.1）

    NOTE: MLアルゴリズム（O(n²)計算量）のため、キャッシュ優先度最高。
    """
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "knowledge.related", "knowledge", knowledge_id)

    limit = int(request.args.get("limit", 5))
    algorithm = request.args.get("algorithm", "hybrid")
    min_score = float(request.args.get("min_score", 0.1))

    # バリデーション
    if limit < 1 or limit > 20:
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_LIMIT",
                "message": "limit must be between 1 and 20",
            },
        }), 400

    if algorithm not in ["tag", "category", "keyword", "hybrid"]:
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_ALGORITHM",
                "message": "algorithm must be tag, category, keyword, or hybrid",
            },
        }), 400

    # キャッシュチェック（min_scoreは小数点2桁で正規化してキー生成）
    min_score_key = f"{min_score:.2f}"
    cache_key = get_cache_key(
        "knowledge_related", knowledge_id, limit, algorithm, min_score_key
    )
    cached_result = cache_get(cache_key)
    if cached_result:
        logger.info("Cache hit: knowledge_related - %s", cache_key)
        return jsonify(cached_result)

    knowledge_list = load_data("knowledge.json")
    target_knowledge = next(
        (k for k in knowledge_list if k["id"] == knowledge_id), None
    )

    if not target_knowledge:
        return jsonify({"success": False, "error": "Knowledge not found"}), 404

    # 関連アイテム取得（高負荷ML処理）
    related = recommendation_engine.get_related_items(
        target_knowledge,
        knowledge_list,
        limit=limit,
        algorithm=algorithm,
        min_score=min_score,
    )

    response_data = {
        "success": True,
        "data": {
            "target_id": knowledge_id,
            "related_items": related,
            "algorithm": algorithm,
            "count": len(related),
        },
    }
    cache_set(cache_key, response_data, ttl=3600)  # 1時間（高コストML計算）
    logger.info("Cache set: knowledge_related - %s", cache_key)

    return jsonify(response_data)


@knowledge_bp.route("/knowledge", methods=["POST"])
@check_permission("knowledge.create")
@validate_request(KnowledgeCreateSchema)
def create_knowledge():
    """新規ナレッジ登録（入力検証付き）"""
    current_user_id = get_jwt_identity()
    data = request.validated_data  # 検証済みデータを使用
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
        "created_by_id": current_user_id,
    }

    knowledge_list.append(new_knowledge)
    save_data("knowledge.json", knowledge_list)

    # キャッシュ無効化（CacheInvalidator使用）
    CacheInvalidator.invalidate_knowledge()

    log_access(current_user_id, "knowledge.create", "knowledge", new_id)

    # 通知作成（承認者に通知）
    create_notification(
        title="新規ナレッジが承認待ちです",
        message=f"{new_knowledge['owner']}さんが「{new_knowledge['title']}」を登録しました。承認をお願いします。",
        type="approval_required",
        target_roles=["admin", "quality_assurance"],
        priority="high",
        related_entity_type="knowledge",
        related_entity_id=new_id,
    )

    return jsonify({"success": True, "data": new_knowledge}), 201


@knowledge_bp.route("/knowledge/<int:knowledge_id>", methods=["PUT"])
@check_permission("knowledge.update")
def update_knowledge(knowledge_id):
    """ナレッジ更新"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": "Request body is required",
            },
        }), 400

    knowledge_list = load_data("knowledge.json")
    knowledge_index = next(
        (i for i, k in enumerate(knowledge_list) if k["id"] == knowledge_id), None
    )

    if knowledge_index is None:
        return jsonify({
            "success": False,
            "error": {"code": "NOT_FOUND", "message": "Knowledge not found"},
        }), 404

    # 更新可能なフィールド
    updatable_fields = [
        "title", "summary", "content", "category",
        "tags", "status", "priority", "project", "owner",
    ]

    for field in updatable_fields:
        if field in data:
            knowledge_list[knowledge_index][field] = data[field]

    knowledge_list[knowledge_index]["updated_at"] = datetime.now().isoformat()
    knowledge_list[knowledge_index]["updated_by_id"] = current_user_id

    save_data("knowledge.json", knowledge_list)

    # キャッシュ無効化（CacheInvalidator使用）
    CacheInvalidator.invalidate_knowledge(knowledge_id)

    log_access(current_user_id, "knowledge.update", "knowledge", knowledge_id)

    return jsonify({"success": True, "data": knowledge_list[knowledge_index]})


@knowledge_bp.route("/knowledge/<int:knowledge_id>", methods=["DELETE"])
@check_permission("knowledge.delete")
def delete_knowledge(knowledge_id):
    """ナレッジ削除（所有権チェック付き）"""
    current_user_id = int(get_jwt_identity())

    knowledge_list = load_data("knowledge.json")
    knowledge_index = next(
        (i for i, k in enumerate(knowledge_list) if k["id"] == knowledge_id), None
    )

    if knowledge_index is None:
        return jsonify({
            "success": False,
            "error": {"code": "NOT_FOUND", "message": "Knowledge not found"},
        }), 404

    knowledge = knowledge_list[knowledge_index]

    # 所有権チェック: 管理者または所有者のみ削除可能
    users = load_users()
    current_user = next((u for u in users if u["id"] == current_user_id), None)
    user_permissions = get_user_permissions(current_user) if current_user else []
    is_admin = "*" in user_permissions
    is_owner = (
        knowledge.get("created_by_id") == current_user_id
        or knowledge.get("owner_id") == current_user_id
    )

    if not is_admin and not is_owner:
        return jsonify({
            "success": False,
            "error": {
                "code": "FORBIDDEN",
                "message": "You can only delete your own knowledge",
            },
        }), 403

    deleted_knowledge = knowledge_list.pop(knowledge_index)
    save_data("knowledge.json", knowledge_list)

    # キャッシュ無効化（CacheInvalidator使用）
    CacheInvalidator.invalidate_knowledge(knowledge_id)

    log_access(current_user_id, "knowledge.delete", "knowledge", knowledge_id)

    return jsonify({
        "success": True,
        "message": f"Knowledge {knowledge_id} deleted successfully",
        "data": deleted_knowledge,
    })


# ============================================================
# お気に入り管理API
# ============================================================


@knowledge_bp.route("/favorites/<int:knowledge_id>", methods=["DELETE"])
@jwt_required()
def remove_favorite(knowledge_id):
    """お気に入りから削除"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "favorites.remove", "favorites", knowledge_id)

    favorites = load_data("users_favorites.json") or []
    updated = [
        f for f in favorites
        if not (
            str(f.get("user_id")) == str(current_user_id)
            and str(f.get("knowledge_id")) == str(knowledge_id)
        )
    ]
    save_data("users_favorites.json", updated)

    return jsonify({
        "success": True,
        "message": "お気に入りから削除しました",
        "knowledge_id": knowledge_id,
    })


# ============================================================
# 横断検索API
# ============================================================


@knowledge_bp.route("/search/unified", methods=["GET"])
@jwt_required()
def unified_search():
    """
    複数エンティティの横断検索

    クエリパラメータ:
        q: 検索クエリ（必須）
        types: 検索対象タイプ（カンマ区切り）
               knowledge,sop,incidents,consultations,regulations
        highlight: ハイライト有効化（デフォルト: true）
        sort_by: ソート基準（relevance_score, updated_at, created_at）（デフォルト: relevance_score）
        order: ソート順（asc, desc）（デフォルト: desc）
        page_size: ページサイズ（デフォルト: 10）
        page: ページ番号（デフォルト: 1）
    """
    current_user_id = get_jwt_identity()
    query = request.args.get("q", "")
    types = request.args.get("types", "knowledge,sop,incidents").split(",")
    highlight = request.args.get("highlight", "true") == "true"
    sort_by = request.args.get("sort_by", "relevance_score")
    order = request.args.get("order", "desc")
    page_size = int(request.args.get("page_size", 10))
    page = int(request.args.get("page", 1))

    if not query:
        return jsonify({
            "success": False,
            "error": {
                "code": "MISSING_QUERY",
                "message": 'Query parameter "q" is required',
            },
        }), 400

    # キャッシュキー生成（クエリ正規化でヒット率向上）
    normalized_query = " ".join(query.strip().lower().split())
    search_types = ",".join(sorted(types))
    highlight_key = "true" if highlight else "false"
    cache_key = get_cache_key(
        "search", normalized_query, search_types, highlight_key, page, page_size, sort_by, order
    )

    cached_result = cache_get(cache_key)
    if cached_result:
        logger.info("Cache hit: unified_search - %s", cache_key)
        return jsonify(cached_result)

    search_query = normalized_query
    results = {}
    total_count = 0

    # 各エンティティを検索
    if "knowledge" in types:
        knowledge_list = load_data("knowledge.json")
        matched = []

        for item in knowledge_list:
            matched_fields, score = search_in_fields(
                item, search_query, ["title", "summary", "content"]
            )
            if matched_fields:
                item_copy = item.copy()
                item_copy["relevance_score"] = score
                if highlight:
                    for field in ["title", "summary"]:
                        if field in item_copy and item_copy[field]:
                            item_copy[field] = highlight_text(item_copy[field], search_query)
                matched.append(item_copy)

        # ソート
        if sort_by == "relevance_score":
            matched = sorted(
                matched,
                key=lambda x: x["relevance_score"],
                reverse=(order == "desc"),
            )
        elif sort_by == "updated_at":
            matched = sorted(
                matched,
                key=lambda x: x.get("updated_at", ""),
                reverse=(order == "desc"),
            )
        elif sort_by == "created_at":
            matched = sorted(
                matched,
                key=lambda x: x.get("created_at", ""),
                reverse=(order == "desc"),
            )

        # ページネーション
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        results["knowledge"] = {
            "items": matched[start_idx:end_idx],
            "count": len(matched),
            "page": page,
            "page_size": page_size,
            "total_pages": (len(matched) + page_size - 1) // page_size,
        }
        total_count += len(matched)

    if "sop" in types:
        sop_list = load_data("sop.json")
        matched = []

        for item in sop_list:
            matched_fields, score = search_in_fields(item, search_query, ["title", "content"])
            if matched_fields:
                item_copy = item.copy()
                item_copy["relevance_score"] = score
                matched.append(item_copy)

        matched = sorted(matched, key=lambda x: x["relevance_score"], reverse=True)
        results["sop"] = {"items": matched[:10], "count": len(matched)}
        total_count += len(matched)

    if "incidents" in types:
        incidents_list = load_data("incidents.json")
        matched = []

        for item in incidents_list:
            matched_fields, score = search_in_fields(
                item, search_query, ["title", "description"]
            )
            if matched_fields:
                item_copy = item.copy()
                item_copy["relevance_score"] = score
                matched.append(item_copy)

        matched = sorted(matched, key=lambda x: x["relevance_score"], reverse=True)
        results["incidents"] = {"items": matched[:10], "count": len(matched)}
        total_count += len(matched)

    log_access(current_user_id, "search.unified", "search", query)

    response_data = {
        "success": True,
        "data": results,
        "total_results": total_count,
        "query": query,
    }
    cache_set(cache_key, response_data, ttl=3600)  # 1時間
    logger.info("Cache set: unified_search - %s", cache_key)

    return jsonify(response_data)
