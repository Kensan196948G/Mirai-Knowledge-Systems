# 変更履歴

## 2026-01-07
- **Phase B-11（本番準備）開始**
  - 本番開発フェーズ現状評価と計画書作成（Phase-B10-Production-Status.md）
  - DB構造設計書作成（論理/物理データモデル完備）
  - 自己署名SSL証明書セットアップスクリプト作成（setup_ssl_selfsigned.sh）
  - Claude Code用プロンプトテンプレート整備（6種類）
  - データインポートスクリプト作成（CSV/Excel/JSON対応）
  - インポート用CSVテンプレート作成

- **Phase B-10（PostgreSQL移行）完了**
  - データベーススキーマ完全定義（init-db.sql: 375行）
  - JSON→PostgreSQLデータ移行スクリプト作成（migrate_json_to_postgres.py）
  - database.pyをJSON/PostgreSQLデュアルモード対応に拡張
  - ヘルスチェックAPI追加（/api/v1/health、/api/v1/health/db）
  - PostgreSQLセットアップスクリプト作成（setup_postgres.sh）
  - PostgreSQL 16.11 本番稼働中
  - Alembic設定済み

- **Phase B-9（品質保証）進捗: 95%完了**
  - 監査ログ機能の詳細化（session_id、status、changes記録対応）
  - 監査ログAPIエンドポイント追加（/api/v1/logs/access、/api/v1/logs/access/stats）
  - 管理画面に監査ログビューア追加（フィルタ・ページネーション・統計表示）
  - セキュリティスキャン自動化（Bandit + Safety）
  - クロスブラウザE2Eテスト実装（Playwright）
  - カバレッジ向上テスト追加（メトリクス、SOP推薦、監査ログフィルタ等）
  - 全テスト538件PASS、カバレッジ91.07%達成

## 2026-01-06
- **Phase B-8（セキュリティ強化）完了**
  - XSS脆弱性の完全修正（recommendations.js、admin.html等）
  - セキュアロガー導入（本番環境でのログ出力抑制）
  - CSRF対策ドキュメント追加
  - セキュリティテスト111件全PASS

## 2026-01-01
- systemd自動起動設定
- セキュリティヘッダー設定（CSP、HSTS等）
- HTTPS強制リダイレクト機能

## 2025-12-30
- XSS脆弱性修正（dom-helpers.js作成）
- JWT秘密鍵の環境変数必須化
- SECURITY_FIXES.md作成

## 2025-12-26
- 初版のドキュメントセット作成
- UIプロトタイプへの参照を追加

## 変更履歴 (詳細)
| 日付 | バージョン | 変更内容 | 担当 |
| --- | --- | --- | --- |
| 2026-01-07 | 0.8 | Phase B-11開始、本番準備（SSL、プロンプト、インポート） | Claude Code |
| 2026-01-07 | 0.7 | Phase B-10完了、PostgreSQL本番稼働 | Claude Code |
| 2026-01-07 | 0.6 | Phase B-9進捗、監査ログ機能完成 | Claude Code |
| 2026-01-06 | 0.5 | Phase B-8完了、セキュリティ強化 | Claude Code |
| 2026-01-01 | 0.4 | systemd設定、セキュリティヘッダー | Claude Code |
| 2025-12-30 | 0.3 | XSS修正、JWT秘密鍵必須化 | Claude Code |
| 2025-12-26 | 0.1 | 初版作成 | Codex |
