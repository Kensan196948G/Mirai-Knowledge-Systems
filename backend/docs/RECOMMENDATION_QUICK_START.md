# 推薦システム クイックスタートガイド

## 5分で始める推薦システム

### 1. バックエンド - 基本的な使い方

```python
from recommendation_engine import RecommendationEngine

# エンジンのインスタンス化
engine = RecommendationEngine(cache_ttl=300)

# データ読み込み
knowledge_list = load_data('knowledge.json')

# 関連ナレッジを取得
target = knowledge_list[0]
related = engine.get_related_items(
    target_item=target,
    candidate_items=knowledge_list,
    limit=5,
    algorithm='hybrid'  # tag/category/keyword/hybridから選択
)

# 結果を表示
for item in related:
    print(f"ID: {item['id']}, Title: {item['title']}")
    print(f"Score: {item['recommendation_score']}")
    print(f"Reasons: {item['recommendation_reasons']}")
    print("---")
```

### 2. API - cURLでテスト

```bash
# ログイン
TOKEN=$(curl -X POST http://localhost:5100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.data.access_token')

# 関連ナレッジ取得
curl -X GET "http://localhost:5100/api/v1/knowledge/1/related?limit=5&algorithm=hybrid" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'

# パーソナライズ推薦取得
curl -X GET "http://localhost:5100/api/v1/recommendations/personalized?type=all&limit=5" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'
```

### 3. フロントエンド - HTMLに追加

```html
<!-- recommendations.jsを読み込む -->
<script src="detail-pages.js"></script>
<script src="recommendations.js"></script>

<!-- 推薦表示エリア -->
<div id="relatedKnowledgeList"></div>

<!-- JavaScriptで呼び出し -->
<script>
// ナレッジ詳細ページで関連ナレッジを表示
const knowledgeId = 1;
loadRelatedKnowledgeFromAPI(knowledgeId, 'hybrid', 5);

// ダッシュボードでパーソナライズ推薦を表示
loadPersonalizedRecommendations('all', 5, 30);
</script>
```

## アルゴリズム選択ガイド

| アルゴリズム | 用途 | 精度 | 速度 |
|------------|------|------|------|
| **hybrid** | 一般的な推薦（推奨） | ★★★★★ | ★★★★☆ |
| **tag** | タグが明確な場合 | ★★★★☆ | ★★★★★ |
| **category** | カテゴリ重視 | ★★★☆☆ | ★★★★★ |
| **keyword** | コンテンツ類似重視 | ★★★★☆ | ★★★☆☆ |

## パラメータ早見表

### GET /api/v1/knowledge/{id}/related

| パラメータ | 型 | デフォルト | 範囲 | 説明 |
|-----------|------|-----------|------|------|
| limit | int | 5 | 1-20 | 取得件数 |
| algorithm | string | hybrid | tag/category/keyword/hybrid | アルゴリズム |
| min_score | float | 0.1 | 0.0-1.0 | 最小スコア閾値 |

### GET /api/v1/recommendations/personalized

| パラメータ | 型 | デフォルト | 範囲 | 説明 |
|-----------|------|-----------|------|------|
| limit | int | 5 | 1-20 | 取得件数 |
| days | int | 30 | 1-365 | 対象期間（日数） |
| type | string | all | knowledge/sop/all | 推薦タイプ |

## トラブルシューティング

### 問題: 推薦結果が返されない

**解決策:**
```python
# 最小スコアを下げる
related = engine.get_related_items(
    target, candidates,
    min_score=0.0  # 0.1 → 0.0
)
```

### 問題: パフォーマンスが遅い

**解決策:**
```python
# limit数を減らす
related = engine.get_related_items(
    target, candidates,
    limit=3  # 5 → 3
)

# キャッシュTTLを長くする
engine = RecommendationEngine(cache_ttl=600)  # 300 → 600
```

### 問題: APIが401エラーを返す

**解決策:**
```bash
# トークンの有効期限を確認
# 再ログインして新しいトークンを取得
TOKEN=$(curl -X POST http://localhost:5100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.data.access_token')
```

## ベストプラクティス

### 1. キャッシュを活用

```python
# 同じデータに対する複数回の呼び出しは自動的にキャッシュされる
engine = RecommendationEngine(cache_ttl=300)  # 5分キャッシュ

# 初回: 250ms
related1 = engine.get_related_items(target, candidates)

# 2回目以降: 5ms（キャッシュから取得）
related2 = engine.get_related_items(target, candidates)
```

### 2. 適切なアルゴリズムを選択

```python
# タグが明確な場合はtagアルゴリズムが高速
if target['tags'] and len(target['tags']) > 0:
    related = engine.get_related_items(target, candidates, algorithm='tag')
else:
    # タグがない場合はhybridを使用
    related = engine.get_related_items(target, candidates, algorithm='hybrid')
```

### 3. エラーハンドリング

```javascript
// フロントエンドでのエラーハンドリング例
try {
  await loadRelatedKnowledgeFromAPI(knowledgeId, 'hybrid', 5);
} catch (error) {
  console.error('Failed to load recommendations:', error);
  // フォールバック処理
  showErrorMessage('推薦の読み込みに失敗しました');
}
```

## サンプルコード集

### Python: カスタム推薦ロジック

```python
def get_smart_recommendations(user_id, knowledge_list, access_logs):
    """ユーザーの状況に応じた推薦を生成"""
    engine = RecommendationEngine()

    # ユーザーの閲覧履歴を確認
    user_logs = [log for log in access_logs if log['user_id'] == user_id]

    if len(user_logs) < 5:
        # 新規ユーザーには人気アイテムを推薦
        return engine._get_popular_items(knowledge_list, access_logs, limit=5)
    else:
        # アクティブユーザーにはパーソナライズ推薦
        return engine.get_personalized_recommendations(
            user_id, access_logs, knowledge_list, limit=5, days=30
        )
```

### JavaScript: アルゴリズム切り替えUI

```javascript
// アルゴリズム選択ドロップダウンを追加
addAlgorithmSelector('recommendationContainer', (algorithm) => {
  // アルゴリズム変更時に再読み込み
  const knowledgeId = getCurrentKnowledgeId();
  loadRelatedKnowledgeFromAPI(knowledgeId, algorithm, 5);
});
```

### JavaScript: ローディング表示

```javascript
// ローディング表示付きの推薦取得
async function loadRecommendationsWithLoading() {
  const container = document.getElementById('recommendations');
  showLoadingInContainer(container);

  try {
    await loadPersonalizedRecommendations('all', 5, 30);
  } catch (error) {
    container.innerHTML = '<p class="error">読み込みに失敗しました</p>';
  }
}
```

## 次のステップ

1. **詳細ドキュメントを読む**
   - `RECOMMENDATION_ENGINE.md` - 完全なドキュメント
   - アルゴリズムの詳細、カスタマイズ方法など

2. **テストを実行**
   ```bash
   python3 tests/test_recommendation_engine.py
   python3 tests/test_recommendation_api.py
   ```

3. **カスタマイズを試す**
   - アルゴリズムの重み調整
   - UIスタイルの変更
   - カスタムトークナイザーの実装

## 参考リンク

- [完全ドキュメント](RECOMMENDATION_ENGINE.md)
- [実装サマリー](RECOMMENDATION_IMPLEMENTATION_SUMMARY.md)
- [APIリファレンス](../openapi.yaml)

## サポート

質問や問題がある場合は、GitHubリポジトリでIssueを作成してください。

---

最終更新: 2026-01-01
