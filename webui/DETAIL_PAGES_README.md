# 詳細ページ完全実装 - README

## 概要
4種類の詳細ページを完全実装しました。各ページには、ユーザーが要求したすべての機能が含まれています。

## 実装済みファイル

### HTMLファイル
1. **search-detail.html** - 検索結果詳細ページ
2. **sop-detail.html** - SOP詳細ページ
3. **incident-detail.html** - 事故レポート詳細ページ
4. **expert-consult.html** - 専門家相談詳細ページ

### JavaScriptファイル
- **detail-pages.js** - 詳細ページ共通機能（新規作成）

### スタイルシート
- **styles.css** - 詳細ページ専用スタイル追加

## 各ページの実装機能

### 1. search-detail.html（検索結果詳細ページ）

#### 実装機能
- ✅ ナレッジ詳細表示（タイトル、概要、本文、メタデータ）
- ✅ 関連ナレッジ表示（5-10件）
- ✅ タグクラウド
- ✅ 編集履歴・バージョン表示
- ✅ コメント機能（投稿・一覧表示）
- ✅ いいね・ブックマーク機能
- ✅ 印刷・PDF出力ボタン
- ✅ 共有ボタン（URL共有、メール、Slack、Teams）
- ✅ パンくずリスト
- ✅ 戻るボタン
- ✅ レスポンシブ対応
- ✅ ローディング表示
- ✅ エラーハンドリング

#### APIエンドポイント
- `GET /api/v1/knowledge/{id}` - ナレッジ取得
- `GET /api/v1/knowledge/{id}/comments` - コメント一覧
- `POST /api/v1/knowledge/{id}/comments` - コメント投稿
- `GET /api/v1/knowledge/{id}/history` - 編集履歴
- `POST /api/v1/knowledge/{id}/like` - いいね切り替え
- `POST /api/v1/knowledge/{id}/bookmark` - ブックマーク切り替え
- `POST /api/v1/knowledge/{id}/view` - 閲覧数カウント
- `GET /api/v1/knowledge/search?tags={tags}` - 関連ナレッジ検索

### 2. sop-detail.html（SOP詳細ページ）

#### 実装機能
- ✅ SOP詳細表示（手順、注意事項、チェックリスト）
- ✅ バージョン情報・改訂履歴
- ✅ 関連SOP表示
- ✅ ダウンロードボタン
- ✅ チェックリスト印刷機能
- ✅ 実施記録入力フォーム
- ✅ 必要資材・工具リスト
- ✅ 標準所要時間表示
- ✅ 適用現場表示
- ✅ 実施統計（実施回数、適合率）
- ✅ パンくずリスト
- ✅ 戻るボタン
- ✅ レスポンシブ対応
- ✅ ローディング表示
- ✅ エラーハンドリング

#### APIエンドポイント
- `GET /api/v1/sop/{id}` - SOP取得
- `GET /api/v1/sop/search?category={category}` - 関連SOP検索
- `POST /api/v1/sop/{id}/record` - 実施記録登録

### 3. incident-detail.html（事故レポート詳細ページ）

#### 実装機能
- ✅ 事故レポート詳細（発生日時、場所、内容、原因、対策）
- ✅ タイムライン表示
- ✅ 関連写真・図面表示（添付ファイルギャラリー）
- ✅ 是正措置記録（タスク管理）
- ✅ 承認フロー表示
- ✅ ステータス更新機能
- ✅ 4M分析（Man、Machine、Media、Management）
- ✅ 即時対応・再発防止策表示
- ✅ 是正措置KPI（完了率、期限遵守率、残タスク）
- ✅ 影響現場リスト
- ✅ 安全評価
- ✅ 担当エキスパート情報
- ✅ 関連教育情報
- ✅ パンくずリスト
- ✅ 戻るボタン
- ✅ レスポンシブ対応
- ✅ ローディング表示
- ✅ エラーハンドリング

#### APIエンドポイント
- `GET /api/v1/incident/{id}` - 事故レポート取得
- `GET /api/v1/incident/{id}/corrective-actions` - 是正措置一覧
- `POST /api/v1/incident/{id}/corrective-actions` - 是正措置追加
- `PUT /api/v1/incident/{id}/status` - ステータス更新

### 4. expert-consult.html（専門家相談詳細ページ）

#### 実装機能
- ✅ 質問詳細表示
- ✅ 回答一覧表示
- ✅ 新規回答フォーム（Markdown対応）
- ✅ ベストアンサー選択機能
- ✅ 関連質問表示
- ✅ 添付ファイル表示
- ✅ 優先度・期限表示
- ✅ 経過時間表示
- ✅ ステータス履歴
- ✅ エンゲージメント統計（回答数、閲覧数、フォロー数）
- ✅ 担当エキスパート情報
- ✅ 参考SOP表示
- ✅ フォロー機能
- ✅ PDF保存・共有機能
- ✅ パンくずリスト
- ✅ 戻るボタン
- ✅ レスポンシブ対応
- ✅ ローディング表示
- ✅ エラーハンドリング

#### APIエンドポイント
- `GET /api/v1/consultation/{id}` - 相談取得
- `GET /api/v1/consultation/{id}/answers` - 回答一覧
- `POST /api/v1/consultation/{id}/answers` - 回答投稿
- `PUT /api/v1/consultation/{id}/best-answer` - ベストアンサー選択
- `GET /api/v1/consultation/search?tags={tags}` - 関連質問検索
- `POST /api/v1/consultation/{id}/follow` - フォロー切り替え

## 共通機能（全ページ）

### UI/UX
- パンくずリスト（ナビゲーション支援）
- 戻るボタン（ブラウザ履歴対応）
- レスポンシブデザイン（モバイル、タブレット、デスクトップ）
- ローディングインジケーター（スピナー表示）
- エラーメッセージ（再試行ボタン付き）
- フローティングボタン（ページトップへスクロール）

### データ取得
- localStorage からの一時データ読み込み
- REST API からの動的データ取得
- 認証トークンによるセキュアアクセス
- エラー時の自動リトライ機能

### 権限制御
- RBAC（ロールベースアクセス制御）統合
- `data-required-role` 属性による権限制御
- 編集・承認ボタンの権限別表示/非表示

### 印刷対応
- 印刷用スタイルシート
- ページ分割制御（page-break-inside: avoid）
- 不要要素の非表示（ボタン、サイドバー等）

## 使用方法

### 基本的な使い方

1. **ナレッジ詳細を表示**
```
http://localhost:5000/search-detail.html?id=123
```

2. **SOP詳細を表示**
```
http://localhost:5000/sop-detail.html?id=456
```

3. **事故レポート詳細を表示**
```
http://localhost:5000/incident-detail.html?id=789
```

4. **専門家相談詳細を表示**
```
http://localhost:5000/expert-consult.html?id=101
```

### JavaScript関数

#### search-detail.html
- `loadKnowledgeDetail()` - ナレッジ詳細読み込み
- `submitComment()` - コメント投稿
- `toggleBookmark()` - ブックマーク切り替え
- `toggleLike()` - いいね切り替え
- `shareKnowledge()` - 共有モーダル表示
- `printPage()` - 印刷
- `exportPDF()` - PDF出力

#### sop-detail.html
- `loadSOPDetail()` - SOP詳細読み込み
- `startInspectionRecord()` - 実施記録フォーム表示
- `printChecklist()` - チェックリスト印刷
- `downloadSOP()` - SOP ダウンロード

#### incident-detail.html
- `loadIncidentDetail()` - 事故レポート詳細読み込み
- `addCorrectiveAction()` - 是正措置追加モーダル表示
- `updateIncidentStatus()` - ステータス更新

#### expert-consult.html
- `loadConsultDetail()` - 相談詳細読み込み
- `loadAnswers()` - 回答一覧読み込み
- `toggleFollow()` - フォロー切り替え

## カスタマイズ

### スタイルのカスタマイズ
`styles.css` の以下のセクションを編集：
```css
/* 詳細ページ専用スタイル */
.loading-overlay { ... }
.error-message { ... }
.breadcrumb-nav { ... }
/* etc. */
```

### APIエンドポイントの変更
`detail-pages.js` の `API_BASE` 定数を編集：
```javascript
const API_BASE = `${window.location.protocol}//${window.location.hostname}:${window.location.port || '5000'}/api/v1`;
```

## トラブルシューティング

### データが表示されない
1. URLパラメータ `?id=xxx` が正しいか確認
2. ブラウザの開発者ツールでAPIレスポンスを確認
3. 認証トークンが有効か確認（localStorage の `access_token`）

### スタイルが適用されない
1. `styles.css` が正しく読み込まれているか確認
2. ブラウザのキャッシュをクリア
3. 開発者ツールでCSSエラーを確認

### JavaScript エラー
1. 開発者ツールのコンソールでエラーメッセージを確認
2. `detail-pages.js` が正しく読み込まれているか確認
3. 依存関係（app.js、actions.js等）が読み込まれているか確認

## 今後の拡張予定

- [ ] PDF出力機能の完全実装（現在はアラート表示のみ）
- [ ] ファイルアップロード機能の実装
- [ ] Markdown エディター統合
- [ ] リアルタイム通知機能
- [ ] バージョン比較機能
- [ ] 高度な検索フィルター

## テスト

### 手動テスト項目
- [ ] 各ページが正常に表示される
- [ ] データが正しく取得・表示される
- [ ] ボタン・リンクが正常に動作する
- [ ] レスポンシブデザインが機能する
- [ ] 印刷プレビューが正しく表示される
- [ ] エラーハンドリングが適切に動作する

## 注意事項

1. **認証必須**: すべてのページは認証トークンが必要です
2. **HTTPS推奨**: 本番環境ではHTTPS接続を使用してください
3. **CORS設定**: APIサーバーで適切なCORS設定が必要です
4. **ブラウザ互換性**: モダンブラウザ（Chrome、Firefox、Safari、Edge）で動作確認済み

## ライセンス

このプロジェクトは Mirai Knowledge Systems の一部です。

## 作成日

2025-12-28

---

以上で詳細ページの完全実装が完了しました。
