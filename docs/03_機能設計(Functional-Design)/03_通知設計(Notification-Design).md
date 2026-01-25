# 通知設計

## 通知種別
- 承認待ち通知
- 承認完了通知
- 事故・ヒヤリの緊急通知
- 法令・SOP改訂通知
- 専門家相談の回答通知

## 配信先
- 現場責任者
- 関連現場の施工管理
- 品質保証/安全衛生
- 協力会社 (閲覧対象のみ)

## 通知チャネル
- WebUI内通知
- メール連携 (Microsoft365 / Exchange Online)
- Microsoft Teams (Incoming Webhook)

## 通知ルール
- 重要度「高」は即時配信
- 「中」「低」は日次サマリ
- 既読確認と再通知を記録
- 外部通知は同期送信（失敗時は5回リトライ）
- 外部通知の失敗フラグを通知データに記録

## 外部通知設定（環境変数）
- `MKS_TEAMS_WEBHOOK_URL`: Teams Incoming Webhook URL（1本で全通知）
- `MKS_SMTP_HOST`: SMTPホスト（例: smtp.office365.com）
- `MKS_SMTP_PORT`: SMTPポート（例: 587）
- `MKS_SMTP_USER`: SMTPユーザー
- `MKS_SMTP_PASSWORD`: SMTPパスワード
- `MKS_SMTP_FROM`: 送信元メールアドレス
- `MKS_SMTP_USE_TLS`: TLS使用（true/false）
- `MKS_SMTP_USE_SSL`: SSL使用（true/false）
- `MKS_NOTIFICATION_RETRY_COUNT`: リトライ回数（デフォルト5）
- `MKS_EXTERNAL_NOTIFICATION_TYPES`: 送信対象タイプの絞り込み（任意）

## 変更履歴
| 日付 | バージョン | 変更内容 | 担当 |
| --- | --- | --- | --- |
| 2025-12-26 | 0.1 | 初版作成 | Codex |
