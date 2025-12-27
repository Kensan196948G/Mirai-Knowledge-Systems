# 障害対応手順書

建設土木ナレッジシステムにおける障害発生時の対応手順を定義します。

## 目次

1. [障害レベル定義](#障害レベル定義)
2. [エスカレーションフロー](#エスカレーションフロー)
3. [よくある障害パターンと対処法](#よくある障害パターンと対処法)
4. [復旧手順](#復旧手順)
5. [障害報告テンプレート](#障害報告テンプレート)

---

## 障害レベル定義

### Critical（重大）

**定義:**
- システム全体が停止している
- データ損失のリスクがある
- セキュリティ侵害が発生している
- 全ユーザーがサービスを利用できない

**対応時間:**
- 初動: 15分以内
- 一次報告: 30分以内
- 暫定対策: 1時間以内
- 完全復旧目標: 4時間以内

**通知対象:**
- システム管理者（即座）
- 経営層（30分以内）
- 全ユーザー（30分以内）

**例:**
- Gunicornプロセスの完全停止
- データベースファイルの破損
- 認証機能の全面障害
- SSL証明書期限切れによるアクセス不可

### High（高）

**定義:**
- 主要機能が利用できない
- 多数のユーザーに影響がある
- パフォーマンスが著しく劣化している
- データ不整合が発生している

**対応時間:**
- 初動: 30分以内
- 一次報告: 1時間以内
- 暫定対策: 4時間以内
- 完全復旧目標: 1営業日以内

**通知対象:**
- システム管理者（即座）
- 関連部門管理者（1時間以内）
- 影響ユーザー（1時間以内）

**例:**
- 検索機能の障害
- ナレッジ投稿・編集機能の障害
- 通知配信の遅延・停止
- ディスク使用率90%超過

### Medium（中）

**定義:**
- 一部機能が利用できない
- 特定ユーザーグループに影響がある
- ワークアラウンドが存在する
- パフォーマンス軽度劣化

**対応時間:**
- 初動: 2時間以内
- 一次報告: 4時間以内
- 暫定対策: 2営業日以内
- 完全復旧目標: 1週間以内

**通知対象:**
- システム管理者（2時間以内）
- 影響ユーザー（4時間以内）

**例:**
- 特定ロールでのアクセスエラー
- 画像アップロード失敗
- メール通知の遅延
- ログファイルの肥大化

### Low（低）

**定義:**
- UIの軽微な不具合
- 機能への影響が限定的
- 利用者の業務に支障がない
- 代替手段が容易に利用可能

**対応時間:**
- 初動: 1営業日以内
- 一次報告: 2営業日以内
- 完全復旧目標: 次回定期メンテナンス

**通知対象:**
- システム管理者（1営業日以内）

**例:**
- 表示レイアウトの崩れ
- 日本語表示の一部誤り
- ログ出力の異常（機能影響なし）
- アクセスログの記録漏れ

---

## エスカレーションフロー

```
[障害検知]
    ↓
[レベル判定] → Low: 担当者対応
    ↓
  Medium
    ↓
[システム管理者へ通知]
    ↓
[影響範囲調査]
    ↓
High/Critical → [経営層へエスカレーション]
    ↓              ↓
[初動対応]    [外部ベンダー連絡]
    ↓
[暫定対策実施]
    ↓
[ユーザー通知]
    ↓
[恒久対策検討]
    ↓
[復旧完了報告]
```

### エスカレーション基準

**即座にエスカレーション:**
- Critical レベルの障害
- セキュリティインシデント
- データ損失の可能性
- 30分以内に原因特定できない場合

**1時間以内にエスカレーション:**
- High レベルの障害
- 影響範囲が拡大している場合
- 複数システムに影響がある場合

**連絡先リスト（例）:**

| 役割 | 連絡先 | 対応時間 |
|------|--------|----------|
| システム管理者 | admin@example.com | 24/7 |
| 技術リーダー | tech-lead@example.com | 平日 9:00-18:00 |
| 経営層 | management@example.com | Critical時のみ |
| 外部ベンダー | vendor-support@example.com | 平日 9:00-17:00 |

---

## よくある障害パターンと対処法

### 1. サーバーダウン

#### 症状
- APIエンドポイントへのアクセスが全て失敗
- ブラウザで "Connection refused" エラー
- ヘルスチェックが失敗

#### 確認手順

```bash
# プロセス確認
cd /path/to/backend
./run_production.sh status

# ログ確認
tail -n 100 /var/log/mirai-knowledge-system/app.log
tail -n 100 logs/error.log
tail -n 100 logs/access.log

# ポート確認
sudo netstat -tlnp | grep 8000
# または
sudo lsof -i :8000
```

#### 対処法

**1. プロセス再起動:**

```bash
cd /path/to/backend
./run_production.sh restart
```

**2. それでも起動しない場合:**

```bash
# 環境変数確認
./run_production.sh check

# エラーログ詳細確認
tail -n 200 logs/error.log

# 手動起動でエラー確認
source venv/bin/activate
export MKS_ENV=production
source .env.production
python3 -c "from app_v2 import app; print('OK')"
```

**3. ディスク容量確認:**

```bash
df -h
# ログファイル削除（必要に応じて）
find logs/ -name "*.log" -mtime +30 -delete
```

#### 暫定対策
- Nginx経由の場合、静的なメンテナンスページを表示
- ロードバランサー使用時は別サーバーに切り替え

#### 恒久対策
- 自動再起動設定（systemd, supervisord）
- ヘルスチェック監視の導入
- ログローテーション設定

---

### 2. データベース障害

#### 症状
- "Database file is locked" エラー
- "Integrity constraint violation" エラー
- データ取得・更新が異常に遅い
- データ不整合（検索結果と実データの相違）

#### 確認手順

```bash
# データベースファイル確認
cd /path/to/backend/data
ls -lh *.json

# ファイルパーミッション確認
ls -la users.json knowledges.json

# ファイルサイズ確認（肥大化チェック）
du -h *.json

# バックアップ存在確認
ls -lht backups/ | head -20
```

#### 対処法

**1. JSON整合性チェック:**

```bash
# JSON構文チェック
python3 << 'EOF'
import json
files = ['users.json', 'knowledges.json', 'access_logs.json']
for f in files:
    try:
        with open(f'data/{f}', 'r', encoding='utf-8') as file:
            json.load(file)
        print(f"{f}: OK")
    except Exception as e:
        print(f"{f}: ERROR - {e}")
EOF
```

**2. パーミッション修正:**

```bash
cd /path/to/backend/data
sudo chown -R www-data:www-data .
chmod 644 *.json
chmod 755 .
```

**3. バックアップからリストア:**

```bash
# 最新バックアップ確認
ls -lt data/backups/ | head -5

# リストア（障害ファイルを指定）
cp data/knowledges.json data/knowledges.json.broken
cp data/backups/knowledges_YYYYMMDD_HHMMSS.json data/knowledges.json
```

**4. PostgreSQL移行（推奨）:**

```bash
# 移行スクリプト実行
python3 migrate_json_to_postgres.py
```

#### 暫定対策
- 読み取り専用モードで運用
- 影響のない機能のみ提供

#### 恒久対策
- PostgreSQLへの移行
- レプリケーション構成
- 定期バックアップの自動化

---

### 3. 認証エラー

#### 症状
- "Invalid token" エラー
- "Token has expired" エラー
- ログイン後すぐにセッション切れ
- 全ユーザーがログインできない

#### 確認手順

```bash
# 環境変数確認
echo $MKS_JWT_SECRET_KEY
echo $MKS_SECRET_KEY

# 設定ファイル確認
grep -E "JWT_|SECRET_" .env.production

# タイムゾーン確認
date
timedatectl
```

#### 対処法

**1. JWT秘密鍵の不一致:**

```bash
# 環境変数が正しく設定されているか確認
./run_production.sh check

# 再起動（環境変数再読み込み）
./run_production.sh restart
```

**2. トークン有効期限の調整:**

```bash
# .env.production編集
export MKS_JWT_ACCESS_TOKEN_HOURS=24  # 1時間→24時間に延長
export MKS_JWT_REFRESH_TOKEN_DAYS=30  # 7日→30日に延長

# 再起動
./run_production.sh restart
```

**3. 時刻同期の問題:**

```bash
# NTP同期確認
sudo timedatectl status

# NTP再同期
sudo timedatectl set-ntp true
sudo systemctl restart systemd-timesyncd
```

**4. CORS設定の問題:**

```bash
# CORS許可オリジン確認
grep CORS_ORIGINS .env.production

# 必要に応じて追加
export MKS_CORS_ORIGINS="https://app.example.com,https://admin.example.com"
```

#### 暫定対策
- トークン有効期限を一時的に延長
- 特定ユーザーのみ手動でトークン発行

#### 恒久対策
- Redis等のセッションストア導入
- リフレッシュトークンの適切な実装
- 多要素認証の導入

---

### 4. パフォーマンス劣化

#### 症状
- APIレスポンスタイムが5秒以上
- 検索が異常に遅い
- CPU使用率が常時80%以上
- メモリ使用率が90%以上

#### 確認手順

```bash
# リソース使用状況確認
top -b -n 1 | head -20
free -h
df -h

# プロセス別リソース確認
ps aux | grep gunicorn | head -10

# ワーカー数確認
./run_production.sh status

# 接続数確認
sudo netstat -an | grep :8000 | wc -l

# ログサイズ確認
du -h logs/*.log
```

#### 対処法

**1. ワーカー数の調整:**

```bash
# 推奨: CPUコア数 × 2 + 1
export MKS_GUNICORN_WORKERS=9  # 4コアの場合

# 再起動
./run_production.sh restart
```

**2. メモリ解放:**

```bash
# キャッシュクリア
sync && echo 3 | sudo tee /proc/sys/vm/drop_caches

# ログローテーション
sudo logrotate -f /etc/logrotate.d/mirai-knowledge-system

# 古いログ削除
find logs/ -name "*.log" -mtime +7 -exec truncate -s 0 {} \;
```

**3. データベース最適化:**

```bash
# JSONファイルの圧縮（PostgreSQL移行推奨）
cd data
for f in *.json; do
    python3 -c "import json; d=json.load(open('$f')); json.dump(d, open('${f}.tmp', 'w'), separators=(',',':'))"
    mv ${f}.tmp $f
done
```

**4. 検索インデックス再構築:**

```bash
# アプリケーション内で実装が必要
# 現在JSONベースの場合、PostgreSQL移行を推奨
```

**5. Nginx接続制限:**

```nginx
# /etc/nginx/sites-available/mirai-knowledge-system
limit_conn_zone $binary_remote_addr zone=conn_limit:10m;
limit_conn conn_limit 10;
```

#### 暫定対策
- 非必須な定期処理の一時停止
- レート制限の強化
- 重い処理のバッチ化

#### 恒久対策
- PostgreSQL + インデックス最適化
- キャッシュレイヤー導入（Redis）
- CDN導入（静的ファイル）
- スケールアウト（複数サーバー）

---

### 5. SSL証明書期限切れ

#### 症状
- ブラウザで "Your connection is not private" エラー
- curl実行時 "SSL certificate problem" エラー
- HTTPS接続が全て失敗

#### 確認手順

```bash
# 証明書有効期限確認
openssl x509 -in /etc/letsencrypt/live/api.example.com/fullchain.pem -noout -dates

# certbot証明書リスト
sudo certbot certificates

# Nginx設定確認
sudo nginx -t
sudo grep -r ssl_certificate /etc/nginx/sites-enabled/
```

#### 対処法

**1. Let's Encrypt証明書の更新:**

```bash
# 証明書更新
sudo certbot renew

# 特定ドメインのみ更新
sudo certbot renew --cert-name api.example.com

# Nginx設定リロード
sudo systemctl reload nginx
```

**2. 自動更新の確認:**

```bash
# certbot タイマー確認
sudo systemctl status certbot.timer

# 有効化されていない場合
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

**3. 証明書取得に失敗する場合:**

```bash
# ドライラン（テスト）
sudo certbot renew --dry-run

# ログ確認
sudo tail -100 /var/log/letsencrypt/letsencrypt.log

# ポート80が開いているか確認
sudo netstat -tlnp | grep :80
```

**4. 緊急時の自己署名証明書:**

```bash
# 一時的な自己署名証明書作成（本番非推奨）
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/temp-selfsigned.key \
  -out /etc/ssl/certs/temp-selfsigned.crt

# Nginx設定を一時変更
sudo nano /etc/nginx/sites-available/mirai-knowledge-system
# ssl_certificate /etc/ssl/certs/temp-selfsigned.crt;
# ssl_certificate_key /etc/ssl/private/temp-selfsigned.key;

sudo systemctl reload nginx
```

#### 暫定対策
- 自己署名証明書での一時運用（ユーザーに警告通知）
- HTTP接続の一時許可（セキュリティリスクあり）

#### 恒久対策
- certbot自動更新の有効化
- 証明書期限監視アラート（30日前、7日前）
- 複数認証局での冗長化検討

---

## 復旧手順

### フェーズ1: 初動対応（15分以内）

1. **障害検知・確認**
   - アラート内容の確認
   - 障害レベルの判定
   - 影響範囲の初期調査

2. **一次報告**
   - システム管理者への連絡
   - 障害発生時刻、症状、影響範囲を報告

3. **初期調査**
   - ログ確認（直近100行）
   - プロセス状態確認
   - リソース使用状況確認

### フェーズ2: 暫定対策（1時間以内）

1. **影響範囲の特定**
   - 影響ユーザー数の算出
   - 影響機能の特定
   - データ損失リスクの評価

2. **暫定対策の実施**
   - サービス再起動
   - バックアップからのリストア
   - 代替機能への切り替え

3. **ユーザー通知**
   - 影響ユーザーへの障害通知
   - 復旧見込み時刻の通知
   - ワークアラウンドの案内

### フェーズ3: 恒久対策（4時間〜1営業日）

1. **根本原因の特定**
   - ログの詳細分析
   - 再現試験の実施
   - 原因の文書化

2. **恒久対策の実装**
   - コード修正
   - 設定変更
   - インフラ改善

3. **復旧確認**
   - 機能テスト
   - パフォーマンステスト
   - セキュリティチェック

### フェーズ4: 事後対応（1週間以内）

1. **完全復旧報告**
   - 障害原因の説明
   - 実施した対策の報告
   - 再発防止策の提示

2. **再発防止策の実施**
   - 監視強化
   - テストケース追加
   - ドキュメント更新

3. **振り返り**
   - 対応時間の評価
   - 手順の改善点抽出
   - 知見の共有

---

## 障害報告テンプレート

### 一次報告（障害発生時）

```
件名: [障害レベル] システム障害発生 - [障害概要]

発生日時: YYYY/MM/DD HH:MM
障害レベル: Critical / High / Medium / Low
影響範囲: 全ユーザー / 特定機能 / 特定ユーザー
復旧見込み: YYYY/MM/DD HH:MM

【症状】
- 具体的な症状を記載

【影響】
- 影響ユーザー数: XX名
- 影響機能: 検索機能、ナレッジ投稿等

【現在の状況】
- 調査中 / 対応中 / 復旧済み

【暫定対策】
- 実施中の対策を記載

【次回報告予定】
- YYYY/MM/DD HH:MM

報告者: 氏名
```

### 復旧報告（復旧完了時）

```
件名: [復旧完了] システム障害復旧 - [障害概要]

発生日時: YYYY/MM/DD HH:MM
復旧日時: YYYY/MM/DD HH:MM
所要時間: X時間Y分

【障害概要】
- 発生した障害の概要

【原因】
- 根本原因の詳細
  - 直接原因: XXX
  - 間接原因: YYY

【影響】
- 影響ユーザー数: XX名
- 影響時間: X時間Y分
- データ損失: あり/なし

【実施した対策】
1. 暫定対策: XXX
2. 恒久対策: YYY

【再発防止策】
1. 監視強化: XXX
2. プロセス改善: YYY
3. 技術改善: ZZZ

【タイムライン】
- HH:MM 障害検知
- HH:MM 初動対応開始
- HH:MM 暫定対策実施
- HH:MM 復旧完了

報告者: 氏名
承認者: 氏名
```

### 定期報告（障害対応中）

```
件名: [経過報告] システム障害対応状況 - [障害概要]

前回報告: YYYY/MM/DD HH:MM
現在時刻: YYYY/MM/DD HH:MM

【現在の状況】
- 進捗状況の詳細

【完了した作業】
- 作業1
- 作業2

【実施中の作業】
- 作業3

【課題・障壁】
- 特になし / 課題の詳細

【復旧見込み】
- 変更なし / 変更後の見込み時刻

【次回報告予定】
- YYYY/MM/DD HH:MM

報告者: 氏名
```

---

## チェックリスト

### 障害発生時の初動チェックリスト

- [ ] 障害発生時刻の記録
- [ ] 障害レベルの判定
- [ ] 関係者への第一報
- [ ] ログファイルの取得
- [ ] プロセス状態の確認
- [ ] リソース使用状況の確認
- [ ] 影響範囲の特定
- [ ] ユーザー通知の実施

### 復旧作業チェックリスト

- [ ] バックアップの取得（作業前）
- [ ] 復旧手順の確認
- [ ] 暫定対策の実施
- [ ] 機能動作確認
- [ ] パフォーマンス確認
- [ ] セキュリティチェック
- [ ] ユーザー通知（復旧完了）
- [ ] 報告書の作成

### 事後対応チェックリスト

- [ ] 根本原因の文書化
- [ ] 再発防止策の策定
- [ ] 監視設定の見直し
- [ ] 手順書の更新
- [ ] 関係者への共有
- [ ] 振り返りミーティング実施

---

## 参考資料

- [監視設定ガイド](./07_Monitoring-Setup-Guide.md)
- [バックアップ・リストア詳細手順](./08_Backup-Restore-Procedures.md)
- [運用手順(Operations-Guide)](./01_運用手順(Operations-Guide).md)
- [SLA・SLO](./03_SLA・SLO(SLA-SLO).md)

---

## 変更履歴

| 日付 | バージョン | 変更内容 | 担当 |
| --- | --- | --- | --- |
| 2025-12-27 | 1.0 | 初版作成 - 詳細な障害対応手順を追加 | Codex |
| 2025-12-26 | 0.1 | 基本骨子作成 | Codex |
