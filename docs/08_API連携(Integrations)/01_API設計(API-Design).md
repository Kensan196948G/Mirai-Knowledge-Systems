# API設計

## APIカテゴリ
- ナレッジ検索
- ナレッジ詳細取得
- 承認ステータス更新
- 配信履歴登録
- 相談起案/回答

## 主要エンドポイント (例)
- GET /api/knowledge?query=
- GET /api/knowledge/{id}
- POST /api/approval/{id}
- POST /api/notification
- POST /api/consultation

## レスポンス方針
- エラーコードの標準化
- 権限不足は403

## 変更履歴
| 日付 | バージョン | 変更内容 | 担当 |
| --- | --- | --- | --- |
| 2025-12-26 | 0.1 | 初版作成 | Codex |
