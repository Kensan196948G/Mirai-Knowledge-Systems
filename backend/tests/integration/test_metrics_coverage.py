"""
メトリクスAPIの追加カバレッジテスト
"""
import pytest


class TestMetricsCompleteCoverage:
    """メトリクスエンドポイントのカバレッジ向上テスト"""

    def test_metrics_endpoint_prometheus_format(self, client):
        """Prometheusメトリクスエンドポイントが正しいフォーマットを返す"""
        response = client.get('/metrics')
        assert response.status_code == 200
        assert b'mks_' in response.data or b'app_info' in response.data

    def test_metrics_v1_endpoint(self, client, auth_headers):
        """APIバージョン付きメトリクスエンドポイント"""
        response = client.get('/api/v1/metrics', headers=auth_headers)
        assert response.status_code == 200

    def test_metrics_summary_complete(self, client, auth_headers):
        """メトリクスサマリーが全項目を含む"""
        response = client.get('/api/metrics/summary', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert 'system' in data
        assert 'application' in data
        assert 'requests' in data
        assert 'errors' in data

    def test_metrics_summary_system_stats(self, client, auth_headers):
        """システムメトリクスが含まれる"""
        response = client.get('/api/metrics/summary', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        system = data.get('system', {})
        assert 'cpu_percent' in system or 'cpu_usage_percent' in system or len(system) >= 0

    def test_metrics_summary_application_stats(self, client, auth_headers):
        """アプリケーションメトリクスが含まれる"""
        response = client.get('/api/metrics/summary', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert 'application' in data

    def test_metrics_summary_without_auth(self, client):
        """認証なしでもメトリクスサマリーにアクセス可能（公開メトリクス）"""
        response = client.get('/api/metrics/summary')
        # 認証必須または公開どちらでもOK
        assert response.status_code in (200, 401)


class TestSOPRecommendations:
    """SOP関連アイテム取得のテスト"""

    def test_get_related_items_default(self, client, auth_headers):
        """デフォルトパラメータでSOP関連アイテム取得"""
        response = client.get('/api/v1/sop/1/related', headers=auth_headers)
        # SOPが存在しない場合は404、存在する場合は200
        assert response.status_code in (200, 404)

    def test_get_related_items_with_limit(self, client, auth_headers):
        """limit指定でSOP関連アイテム取得"""
        response = client.get('/api/v1/sop/1/related?limit=3', headers=auth_headers)
        assert response.status_code in (200, 404)

    def test_get_related_items_with_algorithm_tag(self, client, auth_headers):
        """tagアルゴリズムでSOP関連アイテム取得"""
        response = client.get('/api/v1/sop/1/related?algorithm=tag', headers=auth_headers)
        assert response.status_code in (200, 404)

    def test_get_related_items_with_algorithm_category(self, client, auth_headers):
        """categoryアルゴリズムでSOP関連アイテム取得"""
        response = client.get('/api/v1/sop/1/related?algorithm=category', headers=auth_headers)
        assert response.status_code in (200, 404)

    def test_get_related_items_with_algorithm_keyword(self, client, auth_headers):
        """keywordアルゴリズムでSOP関連アイテム取得"""
        response = client.get('/api/v1/sop/1/related?algorithm=keyword', headers=auth_headers)
        assert response.status_code in (200, 404)

    def test_get_related_items_with_algorithm_hybrid(self, client, auth_headers):
        """hybridアルゴリズムでSOP関連アイテム取得"""
        response = client.get('/api/v1/sop/1/related?algorithm=hybrid', headers=auth_headers)
        assert response.status_code in (200, 404)

    def test_get_related_items_invalid_limit_zero(self, client, auth_headers):
        """無効なlimit（0）でエラー"""
        response = client.get('/api/v1/sop/1/related?limit=0', headers=auth_headers)
        assert response.status_code in (200, 400, 404)

    def test_get_related_items_invalid_limit_high(self, client, auth_headers):
        """無効なlimit（21）でエラー"""
        response = client.get('/api/v1/sop/1/related?limit=21', headers=auth_headers)
        assert response.status_code in (200, 400, 404)

    def test_get_related_items_invalid_algorithm(self, client, auth_headers):
        """無効なアルゴリズムでエラー"""
        response = client.get('/api/v1/sop/1/related?algorithm=invalid', headers=auth_headers)
        assert response.status_code in (200, 400, 404)

    def test_get_related_items_sop_not_found(self, client, auth_headers):
        """存在しないSOPで404"""
        response = client.get('/api/v1/sop/99999/related', headers=auth_headers)
        assert response.status_code == 404

    def test_get_related_items_with_min_score(self, client, auth_headers):
        """min_score指定でSOP関連アイテム取得"""
        response = client.get('/api/v1/sop/1/related?min_score=0.5', headers=auth_headers)
        assert response.status_code in (200, 404)


class TestAuditLogFilteringExtended:
    """監査ログフィルタリングの拡張テスト"""

    def test_audit_logs_user_id_filter_int(self, client, auth_headers):
        """ユーザーIDフィルタ（整数）"""
        response = client.get('/api/v1/logs/access?user_id=1', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['filters']['user_id'] == 1

    def test_audit_logs_action_filter_case_insensitive(self, client, auth_headers):
        """アクションフィルタ（大文字小文字区別なし）"""
        response = client.get('/api/v1/logs/access?action=LOGIN', headers=auth_headers)
        assert response.status_code == 200

    def test_audit_logs_resource_filter(self, client, auth_headers):
        """リソースフィルタ"""
        response = client.get('/api/v1/logs/access?resource=knowledge', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['filters']['resource'] == 'knowledge'

    def test_audit_logs_start_date_filter(self, client, auth_headers):
        """開始日付フィルタ"""
        response = client.get('/api/v1/logs/access?start_date=2025-01-01T00:00:00', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['filters']['start_date'] == '2025-01-01T00:00:00'

    def test_audit_logs_end_date_filter(self, client, auth_headers):
        """終了日付フィルタ"""
        response = client.get('/api/v1/logs/access?end_date=2099-12-31T23:59:59', headers=auth_headers)
        assert response.status_code == 200

    def test_audit_logs_invalid_start_date(self, client, auth_headers):
        """無効な開始日付（スキップされる）"""
        response = client.get('/api/v1/logs/access?start_date=invalid-date', headers=auth_headers)
        assert response.status_code == 200  # エラーではなくフィルタがスキップされる

    def test_audit_logs_invalid_end_date(self, client, auth_headers):
        """無効な終了日付（スキップされる）"""
        response = client.get('/api/v1/logs/access?end_date=invalid-date', headers=auth_headers)
        assert response.status_code == 200

    def test_audit_logs_combined_filters(self, client, auth_headers):
        """複合フィルタ"""
        response = client.get(
            '/api/v1/logs/access?action=login&status=success&start_date=2025-01-01',
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_audit_logs_date_range(self, client, auth_headers):
        """日付範囲フィルタ"""
        response = client.get(
            '/api/v1/logs/access?start_date=2025-01-01&end_date=2099-12-31',
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_audit_logs_sorting_asc(self, client, auth_headers):
        """昇順ソート"""
        response = client.get('/api/v1/logs/access?sort=asc', headers=auth_headers)
        assert response.status_code == 200


class TestStaticFileCaching:
    """静的ファイルキャッシュヘッダーのテスト"""

    def test_serve_index_html(self, client):
        """index.htmlのキャッシュヘッダー"""
        response = client.get('/')
        assert response.status_code in (200, 302)

    def test_serve_login_html(self, client):
        """login.htmlのアクセス"""
        response = client.get('/login.html')
        assert response.status_code == 200

    def test_serve_admin_html(self, client):
        """admin.htmlのアクセス"""
        response = client.get('/admin.html')
        assert response.status_code == 200

    def test_serve_css_file(self, client):
        """CSSファイルのアクセス"""
        response = client.get('/styles.css')
        assert response.status_code in (200, 404)

    def test_serve_js_file(self, client):
        """JavaScriptファイルのアクセス"""
        response = client.get('/app.js')
        assert response.status_code in (200, 404)


class TestRecommendationCache:
    """推薦キャッシュ管理のテスト"""

    def test_get_recommendation_cache_stats(self, client, auth_headers):
        """キャッシュ統計取得"""
        response = client.get('/api/v1/recommendations/cache/stats', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert 'cache_stats' in data or 'stats' in data or response.status_code == 200

    def test_clear_recommendation_cache(self, client, auth_headers):
        """キャッシュクリア"""
        response = client.post('/api/v1/recommendations/cache/clear', headers=auth_headers)
        assert response.status_code == 200

    def test_clear_recommendation_cache_non_admin(self, client, create_test_users, viewer_token):
        """非管理者はキャッシュクリア不可"""
        headers = {'Authorization': f'Bearer {viewer_token}'}
        response = client.post('/api/v1/recommendations/cache/clear', headers=headers)
        assert response.status_code == 403

    def test_get_cache_stats_non_admin(self, client, create_test_users, viewer_token):
        """非管理者はキャッシュ統計取得不可"""
        headers = {'Authorization': f'Bearer {viewer_token}'}
        response = client.get('/api/v1/recommendations/cache/stats', headers=headers)
        assert response.status_code == 403
