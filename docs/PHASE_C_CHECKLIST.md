# Phase C: 本番運用開始チェックリスト

**作成日**: 2026-01-25
**プロジェクト**: Mirai Knowledge Systems
**対象フェーズ**: Phase C - 本番運用開始

---

## 1. インフラ準備状況

### 1.1 サーバー環境
- [x] Linux本番サーバー構築済み
- [x] PostgreSQL 16.11 稼働中
- [x] Nginx + Gunicorn 設定済み
- [x] systemdサービス登録済み（mirai-knowledge-app.service）
- [x] SSL/HTTPS対応（自己署名証明書）

### 1.2 ポート設定
| 環境 | HTTP | HTTPS | 状態 |
|------|------|-------|------|
| 開発 | 5100 | 5443 | 稼働中 |
| 本番 | 8100 | 8443 | 準備完了 |

### 1.3 環境変数
- [x] MKS_JWT_SECRET_KEY 設定済み
- [x] DATABASE_URL 設定済み
- [x] MKS_ENV=production 設定済み
- [ ] MKS_BRAVE_SEARCH_API_KEY 設定（オプション）

---

## 2. データ移行

### 2.1 移行対象データ
- [ ] ユーザーデータ（users）
- [ ] ナレッジデータ（knowledge）
- [ ] SOPデータ（sop）
- [ ] プロジェクトデータ（projects）
- [ ] 専門家データ（experts）
- [ ] インシデントデータ（incidents）
- [ ] 承認フローデータ（approvals）
- [ ] 通知データ（notifications）

### 2.2 移行手順
1. 開発環境JSONデータのエクスポート
2. PostgreSQLへのインポート
3. データ整合性確認
4. 動作検証

### 2.3 バックアップ設定
- [x] PostgreSQLバックアップスクリプト作成済み
- [ ] バックアップスケジュール設定（cron）
- [ ] バックアップ保存先確保

---

## 3. セキュリティ確認

### 3.1 認証・認可
- [x] JWT認証実装済み
- [x] RBAC（ロールベースアクセス制御）実装済み
- [x] パスワードポリシー適用済み
- [x] CSRF対策実装済み

### 3.2 通信セキュリティ
- [x] HTTPS強制リダイレクト
- [x] HSTS設定
- [x] CORS設定

### 3.3 脆弱性対策
- [x] XSS対策（DOM API使用）
- [x] SQLインジェクション対策（SQLAlchemy ORM）
- [x] console.log削除（セキュアロガー導入）

---

## 4. 監視体制

### 4.1 ヘルスチェック
- [x] /api/v1/health エンドポイント
- [ ] 外部監視サービス連携
- [ ] アラート設定

### 4.2 ログ管理
- [x] アプリケーションログ出力
- [ ] ログローテーション設定
- [ ] ログ集約設定

### 4.3 パフォーマンス監視
- [ ] Prometheus設定
- [ ] Grafanaダッシュボード構築

---

## 5. 運用手順

### 5.1 起動・停止
```bash
# サービス起動
sudo systemctl start mirai-knowledge-app.service

# サービス停止
sudo systemctl stop mirai-knowledge-app.service

# サービス再起動
sudo systemctl restart mirai-knowledge-app.service

# ステータス確認
sudo systemctl status mirai-knowledge-app.service
```

### 5.2 ログ確認
```bash
# リアルタイムログ
journalctl -u mirai-knowledge-app.service -f

# 過去ログ
journalctl -u mirai-knowledge-app.service --since "1 hour ago"
```

### 5.3 バックアップ
```bash
# 手動バックアップ
./scripts/backup-postgresql.sh

# リストア
./scripts/restore-postgresql.sh <backup_file>
```

---

## 6. ユーザートレーニング

### 6.1 管理者向け
- [ ] システム管理手順書
- [ ] ユーザー管理手順書
- [ ] バックアップ・リストア手順書

### 6.2 一般ユーザー向け
- [ ] 操作マニュアル
- [ ] FAQ作成

---

## 7. 本番切替手順

### 7.1 事前準備（D-7）
- [ ] 本番環境最終テスト
- [ ] データ移行リハーサル
- [ ] 切替手順確認

### 7.2 切替当日（D-Day）
1. [ ] 開発環境からの最終データエクスポート
2. [ ] 本番環境へのデータインポート
3. [ ] 動作確認テスト
4. [ ] DNS/ネットワーク切替（該当する場合）
5. [ ] ユーザーへの通知

### 7.3 切替後（D+1〜）
- [ ] 本番環境監視
- [ ] 問題対応
- [ ] フィードバック収集

---

## 8. 緊急時対応

### 8.1 障害対応フロー
1. 障害検知
2. 影響範囲確認
3. 一次対応（再起動等）
4. 原因調査
5. 恒久対応
6. 報告・振り返り

### 8.2 連絡先
| 役割 | 担当者 | 連絡先 |
|------|--------|--------|
| システム管理者 | - | - |
| 開発担当 | - | - |

### 8.3 ロールバック手順
1. サービス停止
2. 前バージョンへの切替
3. データリストア（必要な場合）
4. サービス再起動
5. 動作確認

---

## 9. 完了基準

Phase C完了の基準：
- [ ] 本番環境で全機能が正常動作
- [ ] データ移行完了
- [ ] 監視体制稼働
- [ ] 運用手順書完備
- [ ] ユーザートレーニング完了
- [ ] 1週間の安定稼働確認

---

## 10. 次フェーズ（Phase D）への移行

Phase D（機能拡張）の候補：
- Microsoft 365連携（SharePoint/OneDrive）
- 2要素認証
- モバイルアプリ対応
- AI検索機能強化

---

**最終更新**: 2026-01-25
**ステータス**: Phase C準備中
