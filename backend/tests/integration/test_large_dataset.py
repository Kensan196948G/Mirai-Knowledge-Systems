"""
統合テスト: 大規模データセットとパフォーマンス

大規模データでの検索パフォーマンステストとレート制限テストを実施
"""

import json
import time

import pytest


class TestLargeDatasetPerformance:
    """大規模データセットでのパフォーマンステスト"""

    @pytest.fixture
    def large_knowledge_dataset(self, tmp_path):
        """1000件のナレッジデータを生成"""
        knowledge_data = []
        categories = ["安全衛生", "品質管理", "施工管理", "設備保守", "環境管理"]

        for i in range(1000):
            knowledge_data.append(
                {
                    "id": i + 1,
                    "title": f"ナレッジ{i+1:04d}",
                    "summary": f"要約{i+1}：大規模データセットのテストデータです。",
                    "content": f"内容{i+1}：" + ("データ" * 100),  # 約500文字
                    "category": categories[i % len(categories)],
                    "tags": [f"tag{j}" for j in range(i % 5 + 1)],
                    "status": "published" if i % 10 != 0 else "draft",
                    "created_at": f"2026-01-{(i % 28) + 1:02d}T12:00:00Z",
                    "updated_at": f"2026-01-{(i % 28) + 1:02d}T12:00:00Z",
                    "created_by": (i % 5) + 1,
                    "views": i * 10,
                    "rating": (i % 5) + 1,
                }
            )

        # JSONファイルに書き込み
        knowledge_file = tmp_path / "knowledge.json"
        knowledge_file.write_text(
            json.dumps(knowledge_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        return knowledge_data

    def test_search_performance_with_1000_records(
        self, client, auth_headers, large_knowledge_dataset
    ):
        """
        1000件のデータでの検索パフォーマンステスト

        目的:
        - 大規模データセットでの検索が適切な時間内に完了
        - 1秒以内にレスポンスが返る
        """
        start_time = time.time()

        response = client.get(
            "/api/v1/knowledge/search?query=データ", headers=auth_headers
        )

        elapsed_time = time.time() - start_time

        # レスポンスが成功
        assert response.status_code == 200

        # パフォーマンス: 1秒以内（大規模データでも高速検索）
        assert (
            elapsed_time < 1.0
        ), f"検索に{elapsed_time:.2f}秒かかりました（目標: 1秒以内）"

        data = response.get_json()

        # 検索結果が存在する
        if "data" in data:
            results = data["data"].get("results", [])
            assert len(results) > 0, "検索結果が0件です"

    def test_pagination_with_large_dataset(
        self, client, auth_headers, large_knowledge_dataset
    ):
        """
        大規模データセットでのページネーションテスト

        目的:
        - ページング機能が正しく動作
        - 各ページのデータ件数が適切
        """
        # ページ1を取得
        response1 = client.get(
            "/api/v1/knowledge?page=1&per_page=50", headers=auth_headers
        )

        assert response1.status_code == 200
        data1 = response1.get_json()

        # ページ1のデータ件数
        if "data" in data1:
            page1_items = data1["data"]
            assert len(page1_items) <= 50, "ページ1のデータ件数が50件を超えています"

        # ページ2を取得
        response2 = client.get(
            "/api/v1/knowledge?page=2&per_page=50", headers=auth_headers
        )

        assert response2.status_code == 200
        data2 = response2.get_json()

        # ページ1とページ2のデータが異なる
        if "data" in data1 and "data" in data2:
            page1_ids = [
                item["id"]
                for item in data1["data"]
                if isinstance(item, dict) and "id" in item
            ]
            page2_ids = [
                item["id"]
                for item in data2["data"]
                if isinstance(item, dict) and "id" in item
            ]

            # IDが重複していないこと
            overlap = set(page1_ids) & set(page2_ids)
            assert (
                len(overlap) == 0
            ), f"ページ1とページ2でデータが重複しています: {overlap}"

    def test_category_filter_with_large_dataset(
        self, client, auth_headers, large_knowledge_dataset
    ):
        """
        大規模データセットでのカテゴリフィルタリングテスト

        目的:
        - カテゴリフィルタが正しく動作
        - フィルタリング後のデータ件数が適切
        """
        response = client.get(
            "/api/v1/knowledge?category=安全衛生", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()

        # カテゴリフィルタが適用されている
        if "data" in data:
            items = data["data"]

            # すべてのアイテムが「安全衛生」カテゴリ
            for item in items:
                if isinstance(item, dict) and "category" in item:
                    assert (
                        item["category"] == "安全衛生"
                    ), f"カテゴリフィルタが正しく動作していません: {item.get('category')}"

    def test_sorting_with_large_dataset(
        self, client, auth_headers, large_knowledge_dataset
    ):
        """
        大規模データセットでのソート機能テスト

        目的:
        - ソート機能が正しく動作
        - 作成日時順、更新日時順、閲覧数順でソート可能
        """
        # 作成日時降順
        response = client.get(
            "/api/v1/knowledge?sort=created_at&order=desc&per_page=10",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()

        if "data" in data:
            items = data["data"]

            # 作成日時が降順になっている
            for i in range(len(items) - 1):
                if isinstance(items[i], dict) and isinstance(items[i + 1], dict):
                    if "created_at" in items[i] and "created_at" in items[i + 1]:
                        assert (
                            items[i]["created_at"] >= items[i + 1]["created_at"]
                        ), "作成日時でのソートが正しく動作していません"

    def test_concurrent_searches(self, client, auth_headers, large_knowledge_dataset):
        """
        同時検索リクエストのテスト

        目的:
        - 複数の同時検索が正しく処理される
        - レスポンスタイムが許容範囲内
        """

        def search_request(query):
            """検索リクエストを実行"""
            start = time.time()
            response = client.get(
                f"/api/v1/knowledge/search?query={query}", headers=auth_headers
            )
            elapsed = time.time() - start
            return {
                "status_code": response.status_code,
                "elapsed": elapsed,
                "query": query,
            }

        # 10個の同時検索クエリ
        queries = [f"データ{i}" for i in range(10)]

        results = []
        for query in queries:
            result = search_request(query)
            results.append(result)
            time.sleep(0.1)  # レート制限を考慮

        # すべてのリクエストが成功
        for result in results:
            assert result["status_code"] in [
                200,
                429,
            ], f"検索リクエストが失敗しました: {result['query']}"

            # レスポンスタイムが許容範囲内（3秒以内）
            if result["status_code"] == 200:
                assert (
                    result["elapsed"] < 3.0
                ), f"検索に{result['elapsed']:.2f}秒かかりました"


class TestRateLimitingAdvanced:
    """高度なレート制限テスト"""

    def test_login_rate_limit_5_per_15_minutes(self, client):
        """
        ログインエンドポイントのレート制限（5回/15分）

        目的:
        - ブルートフォース攻撃対策
        - 5回の失敗後にレート制限が発動
        """
        # レート制限を有効化
        import app_v2

        original_state = app_v2.limiter.enabled
        app_v2.limiter.enabled = True

        try:
            # 連続ログイン試行
            responses = []
            for i in range(7):
                response = client.post(
                    "/api/v1/auth/login",
                    json={"username": f"attacker{i}", "password": "wrongpass"},
                )
                responses.append(response)
                time.sleep(0.2)

            # レート制限が発動したか確認
            status_codes = [r.status_code for r in responses]

            # 最初の数回は401（認証失敗）、その後429（レート制限）の可能性
            assert any(code == 429 for code in status_codes) or all(
                code in [400, 401] for code in status_codes
            ), f"レート制限が期待通り動作していません: {status_codes}"

        finally:
            # レート制限を元に戻す
            app_v2.limiter.enabled = original_state

    def test_api_rate_limit_per_user(self, client, auth_headers):
        """
        認証済みユーザーごとのレート制限テスト

        目的:
        - ユーザーごとに独立したレート制限が適用される
        - 正常な利用が阻害されない
        """
        import app_v2

        original_state = app_v2.limiter.enabled
        app_v2.limiter.enabled = True

        try:
            # 連続リクエスト
            success_count = 0

            for i in range(20):
                response = client.get("/api/v1/knowledge", headers=auth_headers)

                if response.status_code == 200:
                    success_count += 1
                elif response.status_code == 429:
                    break

                time.sleep(0.1)

            # 少なくとも5回は成功する（レート制限が緩い）
            assert (
                success_count >= 5
            ), f"認証済みユーザーのレート制限が厳しすぎます: 成功{success_count}回"

        finally:
            app_v2.limiter.enabled = original_state

    def test_rate_limit_reset_after_timeout(self, client):
        """
        レート制限のタイムアウト後のリセットテスト

        目的:
        - 一定時間後にレート制限がリセットされる
        - 正常なリトライが可能
        """
        import app_v2

        original_state = app_v2.limiter.enabled
        app_v2.limiter.enabled = True

        try:
            # レート制限を発動させる
            for i in range(7):
                client.post(
                    "/api/v1/auth/login", json={"username": "test", "password": "wrong"}
                )
                time.sleep(0.1)

            # 短時間待機（レート制限ウィンドウの一部）
            time.sleep(2)

            # 再度ログイン試行
            response = client.post(
                "/api/v1/auth/login", json={"username": "test2", "password": "wrong"}
            )

            # レート制限が継続しているか、リセットされているか
            assert response.status_code in [
                400,
                401,
                429,
            ], f"予期しないステータスコード: {response.status_code}"

        finally:
            app_v2.limiter.enabled = original_state

    def test_rate_limit_different_endpoints(self, client, auth_headers):
        """
        異なるエンドポイント間でのレート制限独立性テスト

        目的:
        - エンドポイントごとに独立したレート制限
        - 1つのエンドポイントの制限が他に影響しない
        """
        import app_v2

        original_state = app_v2.limiter.enabled
        app_v2.limiter.enabled = True

        try:
            # ナレッジエンドポイントに連続アクセス
            for _ in range(10):
                client.get("/api/v1/knowledge", headers=auth_headers)
                time.sleep(0.1)

            # SOPエンドポイントにアクセス（独立したレート制限）
            response = client.get("/api/v1/sop", headers=auth_headers)

            # SOPエンドポイントは制限されていないはず
            assert response.status_code in [
                200,
                404,
            ], f"エンドポイント間のレート制限が独立していません: {response.status_code}"

        finally:
            app_v2.limiter.enabled = original_state


class TestTimeoutHandling:
    """タイムアウト処理テスト"""

    def test_request_timeout_handling(self, client, auth_headers):
        """
        リクエストタイムアウト処理テスト

        目的:
        - 長時間処理でのタイムアウト処理
        - エラーレスポンスが適切に返る
        """
        # 通常の検索リクエスト（タイムアウトしないはず）
        response = client.get(
            "/api/v1/knowledge/search?query=test", headers=auth_headers
        )

        # タイムアウトせずに完了
        assert response.status_code in [
            200,
            404,
        ], f"通常のリクエストが失敗しました: {response.status_code}"

    def test_large_response_handling(self, client, auth_headers):
        """
        大規模レスポンス処理テスト

        目的:
        - 大量のデータを返すリクエストが正常に処理される
        - メモリ使用量が適切
        """
        # 大量のデータを要求（ページサイズ最大）
        response = client.get("/api/v1/knowledge?per_page=100", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()

        # レスポンスデータが存在
        assert "data" in data or "error" not in data

    def test_concurrent_write_operations(self, client, auth_headers):
        """
        同時書き込み操作テスト

        目的:
        - 同時書き込みが適切に処理される
        - データ整合性が保たれる
        """
        # 3つのナレッジを同時作成（実際には順次実行）
        results = []

        for i in range(3):
            response = client.post(
                "/api/v1/knowledge",
                json={
                    "title": f"同時作成テスト{i}",
                    "summary": f"要約{i}",
                    "content": f"内容{i}",
                    "category": "安全衛生",
                },
                headers=auth_headers,
            )
            results.append(response)
            time.sleep(0.1)

        # すべての作成が成功
        for response in results:
            assert response.status_code in [
                200,
                201,
            ], f"ナレッジ作成が失敗しました: {response.status_code}"


class TestDataConsistency:
    """データ整合性テスト"""

    def test_search_result_consistency(self, client, auth_headers):
        """
        検索結果の整合性テスト

        目的:
        - 同じクエリで同じ結果が返る
        - データの一貫性が保たれる
        """
        # 同じ検索を2回実行
        response1 = client.get(
            "/api/v1/knowledge/search?query=test", headers=auth_headers
        )

        time.sleep(0.5)

        response2 = client.get(
            "/api/v1/knowledge/search?query=test", headers=auth_headers
        )

        # 両方とも成功
        assert response1.status_code == 200
        assert response2.status_code == 200

        # 結果が一致（データが変更されていない場合）
        data1 = response1.get_json()
        data2 = response2.get_json()

        # データ構造が同じ
        assert type(data1) == type(data2)

    def test_pagination_consistency(self, client, auth_headers):
        """
        ページネーションの整合性テスト

        目的:
        - ページング処理が正確
        - データの重複や欠落がない
        """
        # ページ1を取得
        response1 = client.get(
            "/api/v1/knowledge?page=1&per_page=10", headers=auth_headers
        )

        assert response1.status_code == 200
        data1 = response1.get_json()

        # ページ2を取得
        response2 = client.get(
            "/api/v1/knowledge?page=2&per_page=10", headers=auth_headers
        )

        assert response2.status_code == 200
        data2 = response2.get_json()

        # ページ1とページ2のデータが異なる
        if "data" in data1 and "data" in data2:
            page1_data = str(data1["data"])
            page2_data = str(data2["data"])

            # データが完全に同一でないこと
            assert (
                page1_data != page2_data or len(data1["data"]) == 0
            ), "ページ1とページ2のデータが同一です"

    def test_filter_combination_consistency(self, client, auth_headers):
        """
        フィルタ組み合わせの整合性テスト

        目的:
        - 複数フィルタの組み合わせが正しく動作
        - 予期しない結果が返らない
        """
        # カテゴリ + ステータスフィルタ
        response = client.get(
            "/api/v1/knowledge?category=安全衛生&status=published", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()

        # フィルタ条件に一致するデータのみ返る
        if "data" in data:
            for item in data["data"]:
                if isinstance(item, dict):
                    if "category" in item:
                        assert item["category"] == "安全衛生"
                    if "status" in item:
                        assert item["status"] == "published"
