# データモデル

## 主要エンティティ
- Knowledge: ナレッジ本体
- SOP: 標準施工手順
- Regulation: 法令・規格
- Incident: 事故・ヒヤリ
- Consultation: 専門家相談
- Approval: 承認履歴
- Notification: 配信履歴

## 関連
- Knowledge 1 - n Approval
- Knowledge 1 - n Notification
- Incident 1 - n CorrectiveAction

## 属性例 (Knowledge)
- id, title, summary, category, tags, status, updated_at, owner

## 変更履歴
| 日付 | バージョン | 変更内容 | 担当 |
| --- | --- | --- | --- |
| 2025-12-26 | 0.1 | 初版作成 | Codex |
