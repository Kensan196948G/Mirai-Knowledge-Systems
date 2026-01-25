# 管理者ガイド (Administrator Guide)

## 目次
1. [システム概要](#1-システム概要)
2. [管理者の役割と責任](#2-管理者の役割と責任)
3. [ユーザー管理](#3-ユーザー管理)
4. [ナレッジ管理](#4-ナレッジ管理)
5. [監査ログの確認](#5-監査ログの確認)
6. [バックアップとリストア](#6-バックアップとリストア)
7. [トラブルシューティング](#7-トラブルシューティング)
8. [セキュリティ管理](#8-セキュリティ管理)
9. [パフォーマンス監視](#9-パフォーマンス監視)

---

## 1. システム概要

### 1.1 Mirai Knowledge Systemsとは

Mirai Knowledge Systemsは、建設土木業界における現場判断を支援するナレッジマネジメントシステムです。SOP（標準施工手順）、法令・規格、事故レポート、専門家相談などを一元管理し、承認フローと配信プロセスを標準化します。

### 1.2 システム構成

```
┌─────────────────────────────────────────┐
│         Webブラウザ (UI)                 │
└────────────────┬────────────────────────┘
                 │
┌────────────────┴────────────────────────┐
│      Flask Backend (API Server)         │
│  - 認証・認可 (JWT)                      │
│  - ビジネスロジック                      │
│  - データ検証                           │
└────────────────┬────────────────────────┘
                 │
┌────────────────┴────────────────────────┐
│      PostgreSQL Database                │
│  - public schema (ナレッジ)             │
│  - auth schema (認証)                   │
│  - audit schema (監査)                  │
└─────────────────────────────────────────┘
```

### 1.3 主要機能

- **ナレッジ管理**: SOP、法令、事故レポート、専門家相談の統合管理
- **承認フロー**: 段階的な承認プロセスの可視化と管理
- **通知配信**: 役割ベースの自動通知配信
- **検索機能**: カテゴリ、タグ、キーワードによる高度な検索
- **監査ログ**: 全操作の記録と追跡
- **役割ベースアクセス制御**: きめ細やかな権限管理

![システム構成図](images/admin/system-architecture.png)

---

## 2. 管理者の役割と責任

### 2.1 システム管理者の役割

システム管理者（administrator）は、以下の責任を持ちます：

| 役割 | 責任範囲 | 頻度 |
|------|---------|------|
| **ユーザー管理** | 新規ユーザー追加、無効化、ロール変更 | 随時 |
| **権限管理** | ロールと権限の設定、定期的な棚卸し | 月次 |
| **ナレッジ管理** | 承認待ちコンテンツの確認、削除・アーカイブ | 日次 |
| **監査** | アクセスログ、変更ログの確認 | 週次 |
| **セキュリティ** | 異常なアクセスパターンの検出、対応 | 日次 |
| **バックアップ** | データベースバックアップの実施と確認 | 日次 |
| **パフォーマンス監視** | システムリソースの監視、最適化 | 日次 |

### 2.2 役割の種類と権限

システムには以下の役割が定義されています：

| ロール | 説明 | 主な権限 |
|--------|------|---------|
| `administrator` | システム管理者 | 全機能へのアクセス、ユーザー管理 |
| `approver` | 承認者（所長、品質保証） | ナレッジ承認・却下、通知配信 |
| `construction_manager` | 施工管理 | ナレッジ作成、相談投稿、検索・閲覧 |
| `safety_officer` | 安全衛生担当 | 事故レポート作成、承認、配信 |
| `technical_expert` | 技術専門家 | 相談回答、ナレッジ作成 |
| `viewer` | 閲覧者（協力会社等） | 公開ナレッジの閲覧のみ |

![ロール権限マトリクス](images/admin/role-permission-matrix.png)

---

## 3. ユーザー管理

### 3.1 新規ユーザーの追加

#### 手順

1. 管理画面にログイン
2. 左側メニューから **「ユーザー管理」** を選択
3. 右上の **「新規ユーザー追加」** ボタンをクリック
4. ユーザー情報を入力：

```
必須項目:
- ユーザー名 (username): システム内で一意
- メールアドレス (email): 通知送信先
- 氏名 (full_name): 表示名
- 初期パスワード: 8文字以上、英数字記号混在

任意項目:
- 部署 (department): 例) 技術本部、品質保証室
- 役職 (position): 例) 所長、主任
- ロール: 上記2.2の役割から選択（複数選択可）
```

5. **「登録」** ボタンをクリック
6. 初期パスワードをユーザーに通知（セキュアな方法で）

![ユーザー追加画面](images/admin/user-add-form.png)

#### API経由での追加（高度な管理者向け）

```bash
# ユーザー作成API
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -d '{
    "username": "yamada_taro",
    "email": "yamada@example.com",
    "password": "SecurePass123!",
    "full_name": "山田太郎",
    "department": "技術本部",
    "position": "主任",
    "roles": ["construction_manager"]
  }'
```

### 3.2 ユーザーの無効化

#### いつ無効化するか
- 退職時
- 長期休暇時
- セキュリティインシデント発生時

#### 手順

1. **「ユーザー管理」** 画面でユーザーを検索
2. 対象ユーザーの行をクリック
3. **「無効化」** ボタンをクリック
4. 確認ダイアログで **「OK」** をクリック

**注意**: 無効化されたユーザーはログインできなくなりますが、データは保持されます。

![ユーザー無効化](images/admin/user-deactivate.png)

### 3.3 ロールの変更

#### 手順

1. **「ユーザー管理」** 画面で対象ユーザーを選択
2. **「ロール編集」** ボタンをクリック
3. 追加または削除するロールをチェックボックスで選択
4. **「保存」** ボタンをクリック

#### ベストプラクティス

- **最小権限の原則**: 必要最小限のロールのみを付与
- **定期的な棚卸し**: 月次で不要なロールが付与されていないか確認
- **変更ログ**: ロール変更は自動的に監査ログに記録される

![ロール変更画面](images/admin/user-role-edit.png)

### 3.4 パスワードリセット

#### ユーザーからリセット依頼があった場合

1. **「ユーザー管理」** で対象ユーザーを選択
2. **「パスワードリセット」** ボタンをクリック
3. 一時パスワードが生成される
4. セキュアな方法でユーザーに通知
5. ユーザーは初回ログイン時にパスワード変更を求められる

![パスワードリセット](images/admin/password-reset.png)

---

## 4. ナレッジ管理

### 4.1 承認待ちナレッジの確認

#### 日次チェック手順

1. ダッシュボードの **「承認待ち」** セクションを確認
2. 優先度の高いものから順に確認
3. 各ナレッジの内容を精査

![承認待ちダッシュボード](images/admin/approval-pending-dashboard.png)

#### 承認基準

以下の観点でチェック：

- **内容の正確性**: 技術的に正しいか
- **完全性**: 必要な情報が含まれているか
- **適切性**: カテゴリ、タグが適切か
- **コンプライアンス**: 法令・規格に準拠しているか
- **重複**: 既存ナレッジと重複していないか

### 4.2 ナレッジの承認

#### 手順

1. **「承認管理」** 画面で対象ナレッジを選択
2. 詳細内容を確認
3. 問題なければ **「承認」** ボタンをクリック
4. 承認コメントを入力（任意）
5. **「確定」** ボタンをクリック

承認後、自動的に：
- ステータスが `approved` に変更
- 関連ユーザーに通知が配信
- 監査ログに記録

![ナレッジ承認画面](images/admin/knowledge-approve.png)

### 4.3 ナレッジの却下

#### 手順

1. **「承認管理」** 画面で対象ナレッジを選択
2. **「却下」** ボタンをクリック
3. **必須**: 却下理由を詳細に記入
4. **「確定」** ボタンをクリック

却下理由の例：
```
- 内容が不正確である（具体的な箇所を指摘）
- 必要な情報が不足している（何が不足しているか明記）
- カテゴリが不適切である
- 既存のナレッジと重複している（ID: XXX と重複）
- 法令・規格に準拠していない（具体的な条項を指摘）
```

![ナレッジ却下画面](images/admin/knowledge-reject.png)

### 4.4 ナレッジの削除とアーカイブ

#### 削除とアーカイブの違い

| 操作 | 用途 | データ保持 | 復元可能性 |
|------|------|-----------|-----------|
| **アーカイブ** | 古い情報だが参照の可能性あり | 保持（非表示） | 可能 |
| **削除** | 誤った情報、重複 | 監査ログのみ | 不可 |

#### アーカイブ手順

1. 対象ナレッジを選択
2. **「アーカイブ」** ボタンをクリック
3. アーカイブ理由を入力
4. **「確定」** ボタンをクリック

#### 削除手順（慎重に実施）

1. 対象ナレッジを選択
2. **「削除」** ボタンをクリック
3. **警告ダイアログ** を確認
4. 削除理由を入力
5. 確認文字列 `DELETE` を入力
6. **「完全削除」** ボタンをクリック

**注意**: 削除は取り消せません。監査ログには記録されますが、データ本体は復元できません。

![ナレッジ削除確認](images/admin/knowledge-delete-confirm.png)

---

## 5. 監査ログの確認

### 5.1 監査ログの種類

システムには3種類の監査ログがあります：

| ログ種別 | 記録内容 | 保持期間 |
|---------|---------|---------|
| **アクセスログ** | ログイン、ログアウト、画面アクセス | 7年 |
| **変更ログ** | データの作成、更新、削除 | 7年 |
| **配信ログ** | 通知の送信、閲覧 | 7年 |

### 5.2 アクセスログの確認

#### 確認手順

1. 左側メニューから **「監査ログ」** → **「アクセスログ」** を選択
2. フィルタ条件を設定：
   - 期間: 開始日〜終了日
   - ユーザー: 特定ユーザーまたは全員
   - アクション: login, logout, view, etc.
   - リソース: knowledge, sop, incident, etc.
3. **「検索」** ボタンをクリック

![アクセスログ画面](images/admin/access-log-view.png)

#### 異常パターンの検出

以下のパターンに注意：

- **深夜の大量アクセス**: 通常業務時間外の異常なアクセス
- **短時間の大量ダウンロード**: データの一括取得の可能性
- **失敗したログイン試行の連続**: ブルートフォース攻撃の可能性
- **無効化されたユーザーのアクセス試行**: 不正アクセスの可能性

```sql
-- 深夜アクセスの抽出例（PostgreSQL）
SELECT user_id, username, action, resource, created_at, ip_address
FROM audit.access_logs
WHERE EXTRACT(HOUR FROM created_at) BETWEEN 22 AND 5
  AND created_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY created_at DESC;
```

### 5.3 変更ログの確認

#### 確認手順

1. **「監査ログ」** → **「変更ログ」** を選択
2. フィルタ条件を設定：
   - テーブル名: knowledge, sop, users, etc.
   - アクション: CREATE, UPDATE, DELETE
   - 期間
3. **「検索」** ボタンをクリック

#### 変更内容の詳細確認

各ログエントリには以下の情報が記録されます：

- **old_values**: 変更前の値（JSON形式）
- **new_values**: 変更後の値（JSON形式）
- **user**: 変更を実施したユーザー
- **timestamp**: 変更日時

![変更ログ詳細](images/admin/change-log-detail.png)

### 5.4 配信ログの確認

#### 確認手順

1. **「監査ログ」** → **「配信ログ」** を選択
2. 通知IDまたは期間で検索
3. 配信状況を確認：
   - **sent**: 送信済み
   - **delivered**: 配信完了
   - **read**: 既読
   - **failed**: 配信失敗

#### 配信失敗の対処

配信失敗の原因と対処法：

| 失敗原因 | 対処法 |
|---------|-------|
| メールアドレス無効 | ユーザー情報を更新 |
| サーバーエラー | システムログを確認、再送信 |
| ユーザー無効化済み | 意図的な場合は対処不要 |

![配信ログ画面](images/admin/distribution-log-view.png)

---

## 6. バックアップとリストア

### 6.1 バックアップの種類

| バックアップ種別 | 頻度 | 保持期間 | 対象 |
|---------------|------|---------|------|
| **フルバックアップ** | 日次（深夜2:00） | 30日 | データベース全体 |
| **増分バックアップ** | 6時間毎 | 7日 | 変更分のみ |
| **スナップショット** | 週次（日曜深夜） | 12週 | システム全体 |

### 6.2 バックアップの実施

#### 手動バックアップ（緊急時）

```bash
# PostgreSQLデータベースのバックアップ
cd /path/to/Mirai-Knowledge-Systems/backend

# 全データベースをダンプ
pg_dump -h localhost -U mirai_user -d mirai_knowledge_db \
  -F c -f backup/mirai_knowledge_$(date +%Y%m%d_%H%M%S).dump

# または、SQLファイルとして出力
pg_dump -h localhost -U mirai_user -d mirai_knowledge_db \
  -f backup/mirai_knowledge_$(date +%Y%m%d_%H%M%S).sql
```

#### 自動バックアップの設定

crontabの設定例：

```bash
# バックアップスクリプトの編集
sudo crontab -e

# 以下を追加
# 毎日午前2時にフルバックアップ
0 2 * * * /opt/mirai-knowledge/scripts/backup_full.sh

# 6時間毎に増分バックアップ
0 */6 * * * /opt/mirai-knowledge/scripts/backup_incremental.sh
```

### 6.3 バックアップの確認

#### 定期確認（週次）

1. バックアップディレクトリの確認：

```bash
ls -lh /opt/mirai-knowledge/backup/
```

2. バックアップファイルのサイズチェック（異常な増減がないか）
3. 最新バックアップの整合性チェック：

```bash
# ダンプファイルの整合性確認
pg_restore --list backup/mirai_knowledge_20251227.dump
```

![バックアップ状況ダッシュボード](images/admin/backup-status.png)

### 6.4 リストア手順

#### 事前準備

**警告**: リストアは既存データを上書きします。慎重に実施してください。

1. 現在のデータベースをバックアップ（念のため）
2. メンテナンスモードに移行（ユーザーアクセスを遮断）
3. リストア対象のバックアップファイルを確認

#### リストア実施

```bash
# 1. データベースへの接続を切断
sudo systemctl stop mirai-knowledge-backend

# 2. データベースをドロップして再作成
psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS mirai_knowledge_db;"
psql -h localhost -U postgres -c "CREATE DATABASE mirai_knowledge_db OWNER mirai_user;"

# 3. バックアップからリストア
pg_restore -h localhost -U mirai_user -d mirai_knowledge_db \
  backup/mirai_knowledge_20251227.dump

# 4. サービス再起動
sudo systemctl start mirai-knowledge-backend

# 5. 動作確認
curl http://localhost:5000/api/health
```

#### リストア後の確認

- [ ] ログイン可能か
- [ ] ダッシュボードが表示されるか
- [ ] 検索機能が動作するか
- [ ] ナレッジの作成・更新が可能か
- [ ] 監査ログが記録されているか

---

## 7. トラブルシューティング

### 7.1 よくある問題と解決策

#### 問題1: ユーザーがログインできない

**症状**: ログイン画面で「認証に失敗しました」と表示される

**考えられる原因と対処法**:

| 原因 | 確認方法 | 対処法 |
|------|---------|-------|
| パスワード間違い | ユーザーに確認 | パスワードリセット |
| ユーザーが無効化されている | データベース確認 | ユーザーを有効化 |
| アカウントロック | 監査ログ確認 | ロック解除 |
| システムエラー | サーバーログ確認 | サービス再起動 |

```bash
# ユーザーの状態確認
psql -h localhost -U mirai_user -d mirai_knowledge_db -c \
  "SELECT id, username, email, is_active FROM auth.users WHERE username='yamada_taro';"

# アクセスログで失敗試行を確認
psql -h localhost -U mirai_user -d mirai_knowledge_db -c \
  "SELECT * FROM audit.access_logs WHERE username='yamada_taro'
   AND action='login_failed' ORDER BY created_at DESC LIMIT 10;"
```

#### 問題2: ナレッジが検索結果に表示されない

**症状**: 特定のナレッジが検索で見つからない

**考えられる原因と対処法**:

1. **ステータスが draft または rejected**
   - 管理画面でステータスを確認
   - 必要に応じて承認

2. **権限不足**
   - ユーザーのロールを確認
   - 必要なロールを付与

3. **インデックスの不整合**
   ```bash
   # インデックスの再構築
   psql -h localhost -U mirai_user -d mirai_knowledge_db -c \
     "REINDEX TABLE public.knowledge;"
   ```

#### 問題3: 通知が配信されない

**症状**: 承認後の通知がユーザーに届かない

**チェックリスト**:

- [ ] 配信ログで送信ステータスを確認
- [ ] ユーザーのメールアドレスが正しいか確認
- [ ] 通知設定が有効か確認
- [ ] メールサーバーの接続を確認

```bash
# 配信ログの確認
psql -h localhost -U mirai_user -d mirai_knowledge_db -c \
  "SELECT * FROM audit.distribution_logs
   WHERE notification_id=123 ORDER BY created_at DESC;"

# 通知設定の確認
psql -h localhost -U mirai_user -d mirai_knowledge_db -c \
  "SELECT * FROM public.notifications WHERE id=123;"
```

#### 問題4: システムが遅い

**症状**: 画面遷移やデータ読み込みに時間がかかる

**診断手順**:

1. **サーバーリソースの確認**
   ```bash
   # CPU・メモリ使用率
   top

   # ディスク使用量
   df -h

   # PostgreSQL接続数
   psql -h localhost -U mirai_user -d mirai_knowledge_db -c \
     "SELECT count(*) FROM pg_stat_activity;"
   ```

2. **スロークエリの確認**
   ```bash
   # スロークエリログを有効化（postgresql.conf）
   log_min_duration_statement = 1000  # 1秒以上のクエリをログ

   # ログファイルを確認
   tail -f /var/log/postgresql/postgresql-*.log
   ```

3. **データベース最適化**
   ```bash
   # VACUUM実行
   psql -h localhost -U mirai_user -d mirai_knowledge_db -c "VACUUM ANALYZE;"

   # 統計情報の更新
   psql -h localhost -U mirai_user -d mirai_knowledge_db -c \
     "ANALYZE public.knowledge;"
   ```

### 7.2 ログの確認場所

| ログ種類 | ファイルパス | 確認コマンド |
|---------|------------|-------------|
| アプリケーションログ | `/var/log/mirai-knowledge/app.log` | `tail -f /var/log/mirai-knowledge/app.log` |
| PostgreSQLログ | `/var/log/postgresql/postgresql-*.log` | `tail -f /var/log/postgresql/postgresql-*.log` |
| Nginxアクセスログ | `/var/log/nginx/access.log` | `tail -f /var/log/nginx/access.log` |
| Nginxエラーログ | `/var/log/nginx/error.log` | `tail -f /var/log/nginx/error.log` |
| システムログ | `/var/log/syslog` | `tail -f /var/log/syslog` |

### 7.3 緊急時の対応

#### システムダウン時

1. **サービスの再起動**
   ```bash
   sudo systemctl restart mirai-knowledge-backend
   sudo systemctl restart postgresql
   sudo systemctl restart nginx
   ```

2. **ステータス確認**
   ```bash
   sudo systemctl status mirai-knowledge-backend
   sudo systemctl status postgresql
   sudo systemctl status nginx
   ```

3. **ヘルスチェック**
   ```bash
   curl http://localhost:5000/api/health
   ```

#### セキュリティインシデント発生時

1. **該当ユーザーの即時無効化**
2. **アクセスログの保全**
3. **変更ログの確認**
4. **必要に応じてデータベースのロールバック**
5. **インシデントレポート作成**

![インシデント対応フロー](images/admin/incident-response-flow.png)

---

## 8. セキュリティ管理

### 8.1 セキュリティポリシー

#### パスワードポリシー

- **最小文字数**: 8文字
- **複雑性**: 英大文字・小文字・数字・記号を各1文字以上
- **有効期限**: 90日（推奨）
- **再利用制限**: 過去5回分のパスワードは使用不可
- **ロックアウト**: 5回連続失敗で30分間ロック

#### セッション管理

- **セッションタイムアウト**: 30分（無操作時）
- **トークン有効期限**: 24時間
- **同時セッション**: 1ユーザー最大3セッション

### 8.2 アクセス制御の監視

#### 定期チェック項目（日次）

```bash
# 1. 失敗したログイン試行
psql -h localhost -U mirai_user -d mirai_knowledge_db -c \
  "SELECT username, ip_address, count(*) as failed_attempts
   FROM audit.access_logs
   WHERE action='login_failed'
     AND created_at >= CURRENT_DATE
   GROUP BY username, ip_address
   HAVING count(*) >= 3
   ORDER BY failed_attempts DESC;"

# 2. 管理者権限での操作
psql -h localhost -U mirai_user -d mirai_knowledge_db -c \
  "SELECT u.username, al.action, al.resource, al.created_at
   FROM audit.access_logs al
   JOIN auth.users u ON al.user_id = u.id
   JOIN auth.user_roles ur ON u.id = ur.user_id
   JOIN auth.roles r ON ur.role_id = r.id
   WHERE r.name = 'administrator'
     AND al.created_at >= CURRENT_DATE
   ORDER BY al.created_at DESC
   LIMIT 50;"

# 3. 深夜アクセス
psql -h localhost -U mirai_user -d mirai_knowledge_db -c \
  "SELECT username, action, resource, created_at, ip_address
   FROM audit.access_logs
   WHERE EXTRACT(HOUR FROM created_at) BETWEEN 22 AND 5
     AND created_at >= CURRENT_DATE - INTERVAL '7 days'
   ORDER BY created_at DESC;"
```

### 8.3 脆弱性管理

#### 定期アップデート（月次）

1. **依存パッケージの更新**
   ```bash
   cd /path/to/Mirai-Knowledge-Systems/backend
   pip list --outdated
   pip install --upgrade -r requirements.txt
   ```

2. **セキュリティパッチ適用**
   ```bash
   sudo apt update
   sudo apt upgrade
   sudo apt autoremove
   ```

3. **脆弱性スキャン**
   ```bash
   # pip-audit で依存関係の脆弱性チェック
   pip install pip-audit
   pip-audit
   ```

### 8.4 データ保護

#### 暗号化

- **通信**: TLS 1.2以上（HTTPS）
- **パスワード**: bcrypt（ワークファクター12）
- **機密データ**: AES-256（データベース列レベル暗号化）

#### アクセス制限

```bash
# データベース接続の制限（pg_hba.conf）
# ローカルホストからのみ接続許可
host    mirai_knowledge_db    mirai_user    127.0.0.1/32    scram-sha-256
```

![セキュリティ設定画面](images/admin/security-settings.png)

---

## 9. パフォーマンス監視

### 9.1 監視指標

#### システムリソース

| 指標 | 正常範囲 | 警告閾値 | アクション |
|------|---------|---------|-----------|
| CPU使用率 | < 70% | 70-90% | プロセス確認 |
| メモリ使用率 | < 80% | 80-95% | メモリリーク調査 |
| ディスク使用率 | < 80% | 80-90% | ログローテーション、古いバックアップ削除 |
| ディスクI/O待機 | < 5% | 5-15% | クエリ最適化 |

#### アプリケーション

| 指標 | 正常範囲 | 警告閾値 | アクション |
|------|---------|---------|-----------|
| レスポンスタイム | < 1秒 | 1-3秒 | クエリ最適化 |
| 同時接続数 | < 100 | 100-200 | スケールアウト検討 |
| エラー率 | < 0.1% | 0.1-1% | エラーログ確認 |

### 9.2 監視コマンド

#### システムリソース確認

```bash
# CPU・メモリ使用率（リアルタイム）
top

# ディスク使用量
df -h

# ディスクI/O統計
iostat -x 1

# ネットワーク統計
netstat -an | grep :5000
```

#### データベース監視

```bash
# 接続数
psql -h localhost -U mirai_user -d mirai_knowledge_db -c \
  "SELECT count(*) as connections FROM pg_stat_activity;"

# 実行中のクエリ
psql -h localhost -U mirai_user -d mirai_knowledge_db -c \
  "SELECT pid, usename, application_name, state, query, query_start
   FROM pg_stat_activity
   WHERE state != 'idle'
   ORDER BY query_start;"

# テーブルサイズ
psql -h localhost -U mirai_user -d mirai_knowledge_db -c \
  "SELECT schemaname, tablename,
          pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
   FROM pg_tables
   WHERE schemaname IN ('public', 'auth', 'audit')
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
   LIMIT 10;"

# インデックス使用率
psql -h localhost -U mirai_user -d mirai_knowledge_db -c \
  "SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
   FROM pg_stat_user_indexes
   ORDER BY idx_scan DESC
   LIMIT 10;"
```

### 9.3 最適化

#### クエリ最適化

```sql
-- スロークエリの特定
SELECT query, calls, total_exec_time, mean_exec_time, max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- クエリプランの確認
EXPLAIN ANALYZE
SELECT * FROM public.knowledge
WHERE category = 'SOP'
  AND status = 'approved'
ORDER BY updated_at DESC
LIMIT 10;
```

#### インデックス追加

```sql
-- 頻繁に検索されるカラムにインデックス追加
CREATE INDEX idx_knowledge_category_status
ON public.knowledge(category, status);

CREATE INDEX idx_access_logs_created_at
ON audit.access_logs(created_at DESC);
```

#### データベースメンテナンス

```bash
# 定期的なVACUUM（週次）
psql -h localhost -U mirai_user -d mirai_knowledge_db -c "VACUUM VERBOSE ANALYZE;"

# テーブルの統計情報更新（日次）
psql -h localhost -U mirai_user -d mirai_knowledge_db -c "ANALYZE;"
```

![パフォーマンスダッシュボード](images/admin/performance-dashboard.png)

### 9.4 容量計画

#### データ増加予測

```bash
# 月別データ増加量
psql -h localhost -U mirai_user -d mirai_knowledge_db -c \
  "SELECT DATE_TRUNC('month', created_at) as month,
          count(*) as records,
          pg_size_pretty(sum(length(content::text))::bigint) as content_size
   FROM public.knowledge
   GROUP BY DATE_TRUNC('month', created_at)
   ORDER BY month DESC;"
```

#### ディスク容量監視

```bash
# データベースサイズ
psql -h localhost -U mirai_user -d mirai_knowledge_db -c \
  "SELECT pg_database.datname,
          pg_size_pretty(pg_database_size(pg_database.datname)) AS size
   FROM pg_database
   WHERE datname = 'mirai_knowledge_db';"

# スキーマ別サイズ
psql -h localhost -U mirai_user -d mirai_knowledge_db -c \
  "SELECT schemaname,
          pg_size_pretty(sum(pg_total_relation_size(schemaname||'.'||tablename))::bigint) AS size
   FROM pg_tables
   WHERE schemaname IN ('public', 'auth', 'audit')
   GROUP BY schemaname
   ORDER BY sum(pg_total_relation_size(schemaname||'.'||tablename)) DESC;"
```

---

## 付録

### A. エラーコード一覧

| コード | 説明 | 対処法 |
|-------|------|-------|
| AUTH-001 | 認証失敗 | パスワード確認、ユーザー有効化確認 |
| AUTH-002 | トークン期限切れ | 再ログイン |
| AUTH-003 | 権限不足 | ロール確認、権限付与 |
| DB-001 | データベース接続エラー | PostgreSQL状態確認、再起動 |
| DB-002 | クエリタイムアウト | クエリ最適化、インデックス追加 |
| APP-001 | 内部サーバーエラー | アプリケーションログ確認 |

### B. 管理者用チートシート

```bash
# ====================================
# よく使うコマンド
# ====================================

# サービス再起動
sudo systemctl restart mirai-knowledge-backend

# ログ確認（リアルタイム）
tail -f /var/log/mirai-knowledge/app.log

# データベース接続
psql -h localhost -U mirai_user -d mirai_knowledge_db

# バックアップ作成
pg_dump -h localhost -U mirai_user -d mirai_knowledge_db \
  -F c -f backup/mirai_$(date +%Y%m%d).dump

# ユーザー一覧
psql -h localhost -U mirai_user -d mirai_knowledge_db -c \
  "SELECT id, username, email, is_active FROM auth.users;"

# 承認待ちナレッジ数
psql -h localhost -U mirai_user -d mirai_knowledge_db -c \
  "SELECT count(*) FROM public.approvals WHERE status='pending';"

# 今日のアクセス数
psql -h localhost -U mirai_user -d mirai_knowledge_db -c \
  "SELECT count(*) FROM audit.access_logs WHERE created_at >= CURRENT_DATE;"
```

### C. 問い合わせ先

| 区分 | 連絡先 | 対応時間 |
|------|-------|---------|
| システム障害 | system-admin@example.com | 24時間 |
| ユーザーサポート | support@example.com | 平日9:00-18:00 |
| セキュリティインシデント | security@example.com | 24時間 |

---

## 変更履歴

| 日付 | バージョン | 変更内容 | 担当 |
| --- | --- | --- | --- |
| 2025-12-27 | 1.0 | 初版作成 | System Administrator |

---

**本ドキュメントの最新版は常に `/docs/11_運用保守(Operations)/` ディレクトリで確認してください。**
