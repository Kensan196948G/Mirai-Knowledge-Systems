# 建設土木ナレッジシステム - ドキュメント

## 概要

このディレクトリには、建設土木ナレッジシステムの包括的なドキュメントが含まれています。本番環境への移行、API仕様、運用手順など、システムの構築・運用に必要なすべての情報が網羅されています。

## ドキュメント構成

### 08_API連携 (Integrations)

APIに関する技術仕様とリファレンス

- **[03_API-Reference-Complete.md](./08_API連携(Integrations)/03_API-Reference-Complete.md)** (29KB)
  - 全エンドポイントの詳細仕様
  - リクエスト/レスポンス形式
  - 認証・認可の仕組み
  - エラーコード一覧
  - レート制限
  - セキュリティ設定
  - ベストプラクティス

### 10_移行・展開 (Deployment)

本番環境へのデプロイと移行に関するガイド

- **[04_Production-Migration-Checklist.md](./10_移行・展開(Deployment)/04_Production-Migration-Checklist.md)** (19KB)
  - 本番環境移行の包括的チェックリスト
  - サーバー環境のセットアップ
  - SSL証明書の取得
  - Nginx設定
  - データベース移行
  - セキュリティ設定
  - 動作確認項目
  - トラブルシューティング

- **[05_HTTPS-Migration-Guide.md](./10_移行・展開(Deployment)/05_HTTPS-Migration-Guide.md)** (24KB)
  - HTTP→HTTPS移行の詳細手順
  - Let's Encrypt証明書取得
  - Nginx HTTPS設定
  - セキュリティ強化
  - 証明書の自動更新
  - SSL Labsでの評価方法
  - トラブルシューティング

### 11_運用 (Operations)

日常的な運用とメンテナンスの手順

- **[01_Operations-Manual.md](./11_運用(Operations)/01_Operations-Manual.md)** (28KB)
  - 日常運用手順
  - 起動・停止・再起動
  - ログの確認と分析
  - 監視とアラート設定
  - バックアップとリストア詳細手順
  - 障害対応フローチャート
  - よくある障害と対処法
  - メンテナンス作業
  - セキュリティ運用
  - パフォーマンス最適化

### 13_開発計画 (Development-Plan)

開発とテストに関する情報

- **[24_Debug-Performance-Report.md](./13_開発計画(Development-Plan)/24_Debug-Performance-Report.md)** (18KB)
  - テスト結果レポート
  - パフォーマンス測定結果
  - デバッグ情報

## 対象読者

### システム管理者向け
- [本番環境移行チェックリスト](./10_移行・展開(Deployment)/04_Production-Migration-Checklist.md)
- [HTTPS移行ガイド](./10_移行・展開(Deployment)/05_HTTPS-Migration-Guide.md)
- [運用マニュアル](./11_運用(Operations)/01_Operations-Manual.md)

### 開発者向け
- [API仕様書](./08_API連携(Integrations)/03_API-Reference-Complete.md)
- [デバッグ・パフォーマンスレポート](./13_開発計画(Development-Plan)/24_Debug-Performance-Report.md)

### プロジェクトマネージャー向け
- [本番環境移行チェックリスト](./10_移行・展開(Deployment)/04_Production-Migration-Checklist.md)
- [運用マニュアル](./11_運用(Operations)/01_Operations-Manual.md)

## クイックスタート

### 新規構築の場合

1. **[本番環境移行チェックリスト](./10_移行・展開(Deployment)/04_Production-Migration-Checklist.md)** を最初から最後まで実施
2. **[HTTPS移行ガイド](./10_移行・展開(Deployment)/05_HTTPS-Migration-Guide.md)** でSSL証明書を設定
3. **[運用マニュアル](./11_運用(Operations)/01_Operations-Manual.md)** で日常運用の準備

### 既存環境のHTTPS化

1. **[HTTPS移行ガイド](./10_移行・展開(Deployment)/05_HTTPS-Migration-Guide.md)** の手順に従う
2. **[本番環境移行チェックリスト](./10_移行・展開(Deployment)/04_Production-Migration-Checklist.md)** のセキュリティ項目を再確認

### API開発・連携

1. **[API仕様書](./08_API連携(Integrations)/03_API-Reference-Complete.md)** でエンドポイント仕様を確認
2. 認証方法、レート制限、エラーハンドリングを理解
3. ベストプラクティスに従って実装

### 運用開始後

1. **[運用マニュアル](./11_運用(Operations)/01_Operations-Manual.md)** の「日常運用」セクションを実施
2. 監視スクリプトの設定
3. バックアップの自動化を確認
4. 定期メンテナンススケジュールを設定

## 主要な機能と対応ドキュメント

| 機能 | ドキュメント | 説明 |
|------|------------|------|
| **本番環境構築** | [移行チェックリスト](./10_移行・展開(Deployment)/04_Production-Migration-Checklist.md) | ゼロから本番環境を構築する手順 |
| **HTTPS化** | [HTTPS移行ガイド](./10_移行・展開(Deployment)/05_HTTPS-Migration-Guide.md) | SSL証明書の取得と設定 |
| **API仕様** | [API仕様書](./08_API連携(Integrations)/03_API-Reference-Complete.md) | 全エンドポイントの詳細 |
| **日常運用** | [運用マニュアル](./11_運用(Operations)/01_Operations-Manual.md) | 起動・停止・ログ確認 |
| **バックアップ** | [運用マニュアル](./11_運用(Operations)/01_Operations-Manual.md#バックアップとリストア) | バックアップとリストア手順 |
| **障害対応** | [運用マニュアル](./11_運用(Operations)/01_Operations-Manual.md#障害対応) | トラブルシューティング |
| **監視設定** | [運用マニュアル](./11_運用(Operations)/01_Operations-Manual.md#監視とアラート) | ヘルスチェックとアラート |
| **セキュリティ** | [移行チェックリスト](./10_移行・展開(Deployment)/04_Production-Migration-Checklist.md#セキュリティ確認)、[HTTPS移行ガイド](./10_移行・展開(Deployment)/05_HTTPS-Migration-Guide.md#セキュリティ強化) | セキュリティ設定と運用 |

## よくある質問 (FAQ)

### Q1: 本番環境へのデプロイ手順は？

**A**: [本番環境移行チェックリスト](./10_移行・展開(Deployment)/04_Production-Migration-Checklist.md)を上から順に実施してください。各項目にチェックボックスがあり、進捗を管理できます。

### Q2: SSL証明書の取得方法は？

**A**: [HTTPS移行ガイド](./10_移行・展開(Deployment)/05_HTTPS-Migration-Guide.md)に詳細な手順があります。Let's Encryptを使用した無料証明書の取得から、自動更新の設定まで網羅されています。

### Q3: APIの認証方法は？

**A**: JWT（JSON Web Token）ベースの認証を使用しています。詳細は[API仕様書](./08_API連携(Integrations)/03_API-Reference-Complete.md#認証)を参照してください。

### Q4: バックアップはどのように取得する？

**A**: [運用マニュアル](./11_運用(Operations)/01_Operations-Manual.md#バックアップとリストア)に、自動バックアップスクリプトとリストア手順が記載されています。

### Q5: サービスが起動しない場合は？

**A**: [運用マニュアル](./11_運用(Operations)/01_Operations-Manual.md#障害対応)の「よくある障害とその対処法」を参照してください。

### Q6: 502 Bad Gateway エラーが出る

**A**: [運用マニュアル](./11_運用(Operations)/01_Operations-Manual.md#2-502-bad-gateway)に詳細な対処法が記載されています。

### Q7: レート制限の設定は？

**A**: [API仕様書](./08_API連携(Integrations)/03_API-Reference-Complete.md#レート制限)で、各エンドポイントのレート制限が説明されています。

### Q8: セキュリティヘッダーの設定方法は？

**A**: [HTTPS移行ガイド](./10_移行・展開(Deployment)/05_HTTPS-Migration-Guide.md#セキュリティ強化)と[本番環境移行チェックリスト](./10_移行・展開(Deployment)/04_Production-Migration-Checklist.md#nginx設定テンプレート)に、推奨されるNginx設定が含まれています。

## トラブルシューティング早見表

| 症状 | 確認事項 | 対処ドキュメント |
|------|---------|----------------|
| サービスが起動しない | ポート使用状況、環境変数 | [運用マニュアル - 障害対応](./11_運用(Operations)/01_Operations-Manual.md#1-サービスが起動しない) |
| 502 Bad Gateway | Gunicorn起動状態、Nginx設定 | [運用マニュアル - 障害対応](./11_運用(Operations)/01_Operations-Manual.md#2-502-bad-gateway) |
| SSL証明書エラー | 証明書有効期限、DNS設定 | [HTTPS移行ガイド - トラブルシューティング](./10_移行・展開(Deployment)/05_HTTPS-Migration-Guide.md#トラブルシューティング) |
| メモリ不足 | プロセス使用量、ワーカー数 | [運用マニュアル - 障害対応](./11_運用(Operations)/01_Operations-Manual.md#4-メモリ不足) |
| 認証エラー | JWT設定、システム時刻 | [運用マニュアル - 障害対応](./11_運用(Operations)/01_Operations-Manual.md#6-認証エラー401-unauthorized) |

## システム要件

### 最小要件
- OS: Ubuntu 20.04 LTS以上、Debian 11以上
- CPU: 2コア
- メモリ: 4GB
- ディスク: 20GB

### 推奨要件
- OS: Ubuntu 22.04 LTS
- CPU: 4コア以上
- メモリ: 8GB以上
- ディスク: 50GB以上

詳細は[本番環境移行チェックリスト](./10_移行・展開(Deployment)/04_Production-Migration-Checklist.md#推奨されるサーバースペック)を参照。

## 技術スタック

- **バックエンドフレームワーク**: Flask
- **WSGIサーバー**: Gunicorn
- **リバースプロキシ**: Nginx
- **認証**: JWT (JSON Web Token)
- **データストレージ**: JSON / PostgreSQL（オプション）
- **SSL/TLS**: Let's Encrypt

## メンテナンススケジュール

### 日次
- サービス稼働確認
- エラーログチェック
- ディスク使用率確認

### 週次
- バックアップ動作確認
- SSL証明書有効期限確認
- セキュリティアップデート適用

### 月次
- システムリソースレビュー
- パフォーマンスメトリクス分析
- バックアップリストアテスト

詳細は[運用マニュアル - 定期メンテナンス](./11_運用(Operations)/01_Operations-Manual.md#定期メンテナンス)を参照。

## セキュリティ

### 主要なセキュリティ機能

- JWT認証
- HTTPS強制（本番環境）
- HSTS (HTTP Strict Transport Security)
- セキュリティヘッダー（X-Frame-Options、X-Content-Type-Options等）
- レート制限
- CORS設定
- 入力検証（Marshmallow）

詳細は[HTTPS移行ガイド - セキュリティ強化](./10_移行・展開(Deployment)/05_HTTPS-Migration-Guide.md#セキュリティ強化)を参照。

## サポート

### 問題が解決しない場合

1. [運用マニュアル - 障害対応](./11_運用(Operations)/01_Operations-Manual.md#障害対応)のフローチャートに従う
2. ログを収集（アプリケーション、Nginx、システム）
3. 再現手順を記録
4. 開発チームまたはシステム管理者にエスカレーション

### ドキュメントの改善提案

ドキュメントに不明瞭な点や改善提案がある場合は、開発チームまでフィードバックをお願いします。

## バージョン情報

- **ドキュメントバージョン**: 1.0.0
- **最終更新日**: 2024年12月27日
- **対応システムバージョン**: v2.0

## 変更履歴

| 日付 | バージョン | 変更内容 |
|------|----------|---------|
| 2024-12-27 | 1.0.0 | 初版リリース（本番環境移行チェックリスト、HTTPS移行ガイド、API仕様書、運用マニュアル） |

---

**注意**: このドキュメントは常に最新の状態に保つよう努めていますが、システムの更新に伴い内容が変更される場合があります。最新情報は必ずリポジトリを確認してください。

**ライセンス**: このドキュメントは建設土木ナレッジシステムプロジェクトの一部であり、プロジェクトのライセンスに従います。
