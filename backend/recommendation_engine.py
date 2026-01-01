"""
推薦エンジンモジュール

このモジュールは、ナレッジとSOPの推薦機能を提供します。
以下のアルゴリズムを実装しています：
- コンテンツベースフィルタリング（タグ類似度、カテゴリマッチング）
- キーワードマッチング（TF-IDF）
- 協調フィルタリング（閲覧履歴ベース）
"""

import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import re
from typing import List, Dict, Any, Optional, Tuple


class RecommendationEngine:
    """推薦エンジンクラス"""

    def __init__(self, cache_ttl: int = 300):
        """
        初期化

        Args:
            cache_ttl: キャッシュの有効期限（秒）、デフォルト5分
        """
        self.cache = {}
        self.cache_ttl = cache_ttl
        self.cache_timestamps = {}

    def calculate_tag_similarity(self, tags1: List[str], tags2: List[str]) -> float:
        """
        Jaccard係数を使用してタグの類似度を計算

        Args:
            tags1: 1つ目のタグリスト
            tags2: 2つ目のタグリスト

        Returns:
            float: 類似度スコア（0.0～1.0）
        """
        if not tags1 or not tags2:
            return 0.0

        set1 = set(tag.lower() for tag in tags1)
        set2 = set(tag.lower() for tag in tags2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        return intersection / union

    def calculate_category_similarity(self, cat1: str, cat2: str) -> float:
        """
        カテゴリの類似度を計算

        Args:
            cat1: 1つ目のカテゴリ
            cat2: 2つ目のカテゴリ

        Returns:
            float: 類似度スコア（完全一致:1.0、不一致:0.0）
        """
        if not cat1 or not cat2:
            return 0.0

        return 1.0 if cat1.lower() == cat2.lower() else 0.0

    def _tokenize(self, text: str) -> List[str]:
        """
        テキストをトークンに分割（Bi-gram方式）

        Args:
            text: 対象テキスト

        Returns:
            List[str]: トークンリスト
        """
        if not text:
            return []

        tokens = []

        # まず全ての日本語文字列を抽出
        jp_parts = re.findall(r'[ぁ-んァ-ヶー一-龥]+', text)
        for part in jp_parts:
            # Bi-gram（2文字ずつ）で分割
            for i in range(len(part) - 1):
                bigram = part[i:i+2]
                tokens.append(bigram)
            # 3文字以上の場合は元の単語も追加
            if len(part) >= 2:
                tokens.append(part)

        # 英数字トークン（2文字以上）
        en_tokens = re.findall(r'[a-zA-Z0-9]{2,}', text.lower())
        tokens.extend(en_tokens)

        return tokens

    def _calculate_tf(self, tokens: List[str]) -> Dict[str, float]:
        """
        TF（Term Frequency）を計算

        Args:
            tokens: トークンリスト

        Returns:
            Dict[str, float]: 単語ごとのTF値
        """
        if not tokens:
            return {}

        counter = Counter(tokens)
        total = len(tokens)

        return {word: count / total for word, count in counter.items()}

    def _calculate_idf(self, all_documents: List[List[str]]) -> Dict[str, float]:
        """
        IDF（Inverse Document Frequency）を計算

        Args:
            all_documents: 全ドキュメントのトークンリスト

        Returns:
            Dict[str, float]: 単語ごとのIDF値
        """
        if not all_documents:
            return {}

        doc_count = len(all_documents)
        word_doc_count = defaultdict(int)

        for tokens in all_documents:
            unique_words = set(tokens)
            for word in unique_words:
                word_doc_count[word] += 1

        idf = {}
        for word, count in word_doc_count.items():
            idf[word] = math.log((doc_count + 1) / (count + 1)) + 1

        return idf

    def calculate_content_similarity(
        self,
        item1: Dict[str, Any],
        item2: Dict[str, Any],
        all_items: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """
        TF-IDFを使用してコンテンツの類似度を計算

        Args:
            item1: 1つ目のアイテム
            item2: 2つ目のアイテム
            all_items: 全アイテムリスト（IDF計算用、オプション）

        Returns:
            Tuple[float, Dict[str, Any]]:
                - 類似度スコア（0.0～1.0）
                - 詳細情報（共通キーワードなど）
        """
        # テキスト抽出
        text1 = ' '.join([
            item1.get('title', ''),
            item1.get('summary', ''),
            item1.get('content', '')
        ])
        text2 = ' '.join([
            item2.get('title', ''),
            item2.get('summary', ''),
            item2.get('content', '')
        ])

        # トークン化
        tokens1 = self._tokenize(text1)
        tokens2 = self._tokenize(text2)

        if not tokens1 or not tokens2:
            return 0.0, {'common_keywords': []}

        # TF計算
        tf1 = self._calculate_tf(tokens1)
        tf2 = self._calculate_tf(tokens2)

        # IDF計算（全アイテムがある場合）
        if all_items:
            all_tokens = []
            for item in all_items:
                text = ' '.join([
                    item.get('title', ''),
                    item.get('summary', ''),
                    item.get('content', '')
                ])
                all_tokens.append(self._tokenize(text))
            idf = self._calculate_idf(all_tokens)
        else:
            # IDFなしの場合はTFのみ使用
            idf = {word: 1.0 for word in set(tokens1 + tokens2)}

        # TF-IDFベクトル作成
        all_words = set(tf1.keys()) | set(tf2.keys())
        vec1 = [tf1.get(word, 0) * idf.get(word, 1.0) for word in all_words]
        vec2 = [tf2.get(word, 0) * idf.get(word, 1.0) for word in all_words]

        # コサイン類似度計算
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            similarity = 0.0
        else:
            similarity = dot_product / (magnitude1 * magnitude2)

        # 共通キーワード抽出（TF-IDFスコアが高いもの）
        common_words = set(tf1.keys()) & set(tf2.keys())
        common_keywords = sorted(
            common_words,
            key=lambda w: (tf1[w] + tf2[w]) * idf.get(w, 1.0),
            reverse=True
        )[:5]

        details = {
            'common_keywords': common_keywords,
            'keyword_count': len(common_keywords)
        }

        return similarity, details

    def get_related_items(
        self,
        target_item: Dict[str, Any],
        candidate_items: List[Dict[str, Any]],
        limit: int = 5,
        algorithm: str = 'hybrid',
        min_score: float = 0.1
    ) -> List[Dict[str, Any]]:
        """
        関連アイテムを取得

        Args:
            target_item: 対象アイテム
            candidate_items: 候補アイテムリスト
            limit: 取得数上限
            algorithm: アルゴリズム（'tag', 'category', 'keyword', 'hybrid'）
            min_score: 最小スコア閾値

        Returns:
            List[Dict[str, Any]]: 関連アイテムリスト（スコア順）
        """
        # 自分自身を除外
        target_id = target_item.get('id')
        candidates = [item for item in candidate_items if item.get('id') != target_id]

        if not candidates:
            return []

        # キャッシュキー生成
        cache_key = f"related_{target_id}_{algorithm}_{limit}"

        # キャッシュチェック
        if cache_key in self.cache:
            timestamp = self.cache_timestamps.get(cache_key, 0)
            if datetime.now().timestamp() - timestamp < self.cache_ttl:
                return self.cache[cache_key]

        # スコア計算
        scored_items = []

        for item in candidates:
            score = 0.0
            reasons = []
            details = {}

            if algorithm in ['tag', 'hybrid']:
                # タグ類似度
                tag_sim = self.calculate_tag_similarity(
                    target_item.get('tags', []),
                    item.get('tags', [])
                )
                if tag_sim > 0:
                    score += tag_sim * 0.4  # 重み: 40%
                    reasons.append(f'同じタグ（類似度: {tag_sim:.2f}）')
                    details['tag_similarity'] = tag_sim

            if algorithm in ['category', 'hybrid']:
                # カテゴリ類似度
                cat_sim = self.calculate_category_similarity(
                    target_item.get('category', ''),
                    item.get('category', '')
                )
                if cat_sim > 0:
                    score += cat_sim * 0.3  # 重み: 30%
                    reasons.append('同じカテゴリ')
                    details['category_match'] = True

            if algorithm in ['keyword', 'hybrid']:
                # コンテンツ類似度
                content_sim, content_details = self.calculate_content_similarity(
                    target_item,
                    item,
                    candidate_items
                )
                if content_sim > 0:
                    score += content_sim * 0.3  # 重み: 30%
                    if content_details['common_keywords']:
                        reasons.append(
                            f"共通キーワード: {', '.join(content_details['common_keywords'][:3])}"
                        )
                    details['content_similarity'] = content_sim
                    details['common_keywords'] = content_details['common_keywords']

            # 最小スコア閾値でフィルタ
            if score >= min_score:
                item_copy = item.copy()
                item_copy['recommendation_score'] = round(score, 3)
                item_copy['recommendation_reasons'] = reasons
                item_copy['recommendation_details'] = details
                scored_items.append(item_copy)

        # スコア順にソート
        scored_items.sort(key=lambda x: x['recommendation_score'], reverse=True)

        # 上限数まで取得
        result = scored_items[:limit]

        # キャッシュに保存
        self.cache[cache_key] = result
        self.cache_timestamps[cache_key] = datetime.now().timestamp()

        return result

    def get_personalized_recommendations(
        self,
        user_id: int,
        access_logs: List[Dict[str, Any]],
        all_items: List[Dict[str, Any]],
        limit: int = 5,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        パーソナライズ推薦を取得（協調フィルタリング）

        Args:
            user_id: ユーザーID
            access_logs: アクセスログリスト
            all_items: 全アイテムリスト
            limit: 取得数上限
            days: 対象期間（日数）

        Returns:
            List[Dict[str, Any]]: 推薦アイテムリスト
        """
        # キャッシュキー
        cache_key = f"personalized_{user_id}_{limit}_{days}"

        # キャッシュチェック
        if cache_key in self.cache:
            timestamp = self.cache_timestamps.get(cache_key, 0)
            if datetime.now().timestamp() - timestamp < self.cache_ttl:
                return self.cache[cache_key]

        # 対象期間のログをフィルタ
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_logs = []

        for log in access_logs:
            try:
                log_time = datetime.fromisoformat(log.get('timestamp', ''))
                if log_time >= cutoff_date:
                    recent_logs.append(log)
            except (ValueError, TypeError):
                continue

        # ユーザーの閲覧履歴を抽出
        user_viewed = set()
        user_categories = Counter()
        user_tags = Counter()

        for log in recent_logs:
            if log.get('user_id') == user_id and log.get('action') in ['knowledge.view', 'sop.view']:
                resource_id = log.get('resource_id')
                if resource_id:
                    user_viewed.add(resource_id)

                    # アイテム情報を取得
                    item = next((i for i in all_items if i.get('id') == resource_id), None)
                    if item:
                        if item.get('category'):
                            user_categories[item['category']] += 1
                        for tag in item.get('tags', []):
                            user_tags[tag] += 1

        if not user_viewed:
            # 閲覧履歴がない場合は人気アイテムを返す
            return self._get_popular_items(all_items, access_logs, limit)

        # 類似ユーザーを見つける（協調フィルタリング）
        similar_users = self._find_similar_users(
            user_id,
            user_viewed,
            recent_logs,
            all_items
        )

        # 類似ユーザーが閲覧したアイテムをスコアリング
        candidate_scores = defaultdict(float)

        for similar_user_id, similarity_score in similar_users[:10]:  # 上位10名
            for log in recent_logs:
                if log.get('user_id') == similar_user_id and \
                   log.get('action') in ['knowledge.view', 'sop.view']:
                    resource_id = log.get('resource_id')
                    if resource_id and resource_id not in user_viewed:
                        candidate_scores[resource_id] += similarity_score

        # コンテンツベースのスコアを追加
        for item in all_items:
            item_id = item.get('id')
            if item_id in user_viewed:
                continue

            content_score = 0.0

            # カテゴリマッチ
            if item.get('category') in user_categories:
                content_score += 0.5

            # タグマッチ
            tag_matches = sum(1 for tag in item.get('tags', []) if tag in user_tags)
            if tag_matches > 0:
                content_score += tag_matches * 0.3

            candidate_scores[item_id] += content_score

        # スコア順にソート
        sorted_candidates = sorted(
            candidate_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # アイテム情報を付与
        result = []
        for item_id, score in sorted_candidates[:limit]:
            item = next((i for i in all_items if i.get('id') == item_id), None)
            if item:
                item_copy = item.copy()
                item_copy['recommendation_score'] = round(score, 3)
                item_copy['recommendation_reasons'] = ['あなたの閲覧履歴に基づく推薦']
                result.append(item_copy)

        # キャッシュに保存
        self.cache[cache_key] = result
        self.cache_timestamps[cache_key] = datetime.now().timestamp()

        return result

    def _find_similar_users(
        self,
        user_id: int,
        user_viewed: set,
        access_logs: List[Dict[str, Any]],
        all_items: List[Dict[str, Any]]
    ) -> List[Tuple[int, float]]:
        """
        類似ユーザーを検索

        Args:
            user_id: 対象ユーザーID
            user_viewed: 対象ユーザーの閲覧アイテムID集合
            access_logs: アクセスログ
            all_items: 全アイテム

        Returns:
            List[Tuple[int, float]]: (ユーザーID, 類似度スコア)のリスト
        """
        # 他のユーザーの閲覧履歴を集計
        other_users_viewed = defaultdict(set)

        for log in access_logs:
            log_user_id = log.get('user_id')
            if log_user_id and log_user_id != user_id and \
               log.get('action') in ['knowledge.view', 'sop.view']:
                resource_id = log.get('resource_id')
                if resource_id:
                    other_users_viewed[log_user_id].add(resource_id)

        # Jaccard係数で類似度計算
        similarities = []

        for other_user_id, other_viewed in other_users_viewed.items():
            intersection = len(user_viewed & other_viewed)
            union = len(user_viewed | other_viewed)

            if union > 0:
                similarity = intersection / union
                if similarity > 0.1:  # 閾値
                    similarities.append((other_user_id, similarity))

        # スコア順にソート
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities

    def _get_popular_items(
        self,
        all_items: List[Dict[str, Any]],
        access_logs: List[Dict[str, Any]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        人気アイテムを取得

        Args:
            all_items: 全アイテム
            access_logs: アクセスログ
            limit: 取得数上限

        Returns:
            List[Dict[str, Any]]: 人気アイテムリスト
        """
        # 閲覧数をカウント
        view_counts = Counter()

        for log in access_logs:
            if log.get('action') in ['knowledge.view', 'sop.view']:
                resource_id = log.get('resource_id')
                if resource_id:
                    view_counts[resource_id] += 1

        # 上位アイテムを取得
        popular_ids = [item_id for item_id, _ in view_counts.most_common(limit)]

        result = []
        for item_id in popular_ids:
            item = next((i for i in all_items if i.get('id') == item_id), None)
            if item:
                item_copy = item.copy()
                item_copy['recommendation_score'] = view_counts[item_id]
                item_copy['recommendation_reasons'] = ['人気のアイテム']
                result.append(item_copy)

        return result

    def clear_cache(self):
        """キャッシュをクリア"""
        self.cache.clear()
        self.cache_timestamps.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        キャッシュ統計を取得

        Returns:
            Dict[str, Any]: キャッシュ統計情報
        """
        now = datetime.now().timestamp()
        valid_count = sum(
            1 for key, timestamp in self.cache_timestamps.items()
            if now - timestamp < self.cache_ttl
        )

        return {
            'total_entries': len(self.cache),
            'valid_entries': valid_count,
            'expired_entries': len(self.cache) - valid_count,
            'cache_ttl': self.cache_ttl
        }
