# 2要素認証（2FA）デプロイガイド

**作成日**: 2026-01-31
**対象**: Mirai Knowledge Systems Phase D-3
**実装者**: Claude Code (Sonnet 4.5)

---

## 📋 デプロイ前提条件

### システム要件
- Python 3.10以上
- PostgreSQL 15以上（本番環境）
- Nginx + Gunicorn（本番環境）

### Python依存関係
```txt
pyotp==2.9.0          # TOTP生成・検証
qrcode==7.4.2         # QRコード生成
Pillow==10.0.0        # QRコード画像処理（qrcodeの依存）
bcrypt==4.0.1         # バックアップコードハッシュ化（既存）
```

---

## 🚀 デプロイ手順

### ステップ1: 依存関係のインストール

#### 開発環境（Linux）
```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems

# 仮想環境を使用する場合
python3 -m venv venv_mfa
source venv_mfa/bin/activate

# 依存関係インストール
pip install pyotp==2.9.0 qrcode==7.4.2 Pillow==10.0.0

# 確認
python -c "import pyotp; import qrcode; print('✅ 依存関係OK')"
```

#### 本番環境（systemdサービス）
```bash
# サービス停止
sudo systemctl stop mirai-knowledge-prod

# 仮想環境に依存関係追加
source /opt/mirai-knowledge/venv/bin/activate
pip install pyotp==2.9.0 qrcode==7.4.2 Pillow==10.0.0

# 確認
python -c "import pyotp; import qrcode; print('✅ 依存関係OK')"
```

---

### ステップ2: データベースマイグレーション

#### A. Alembic使用（推奨）

```bash
cd backend

# マイグレーション実行
alembic upgrade head

# 確認
alembic current
# 出力例: add_mfa_backup_codes (head)
```

#### B. 手動SQLスクリプト実行

```bash
# PostgreSQL接続
psql -U mks_user -d mirai_knowledge

# マイグレーション実行
\i backend/migrations/sql/add_mfa_backup_codes.sql

# 確認
\d auth.users
# mfa_backup_codes列が追加されていることを確認
```

---

### ステップ3: app_v2.py にMFAエンドポイント追加確認

#### 確認コマンド
```bash
grep -n "mfa" backend/app_v2.py | head -10
```

#### 期待される出力
```
1415:@app.route('/api/v1/auth/mfa/setup', methods=['POST'])
1440:@app.route('/api/v1/auth/mfa/enable', methods=['POST'])
1465:@app.route('/api/v1/auth/mfa/disable', methods=['POST'])
1490:@app.route('/api/v1/auth/mfa/verify', methods=['POST'])
...
```

---

### ステップ4: テスト実行

#### A. ユニットテスト
```bash
cd backend

# TOTP Managerテスト
pytest tests/unit/test_totp_manager.py -v

# 期待結果: 21 passed
```

#### B. 統合テスト
```bash
# MFAフローテスト
pytest tests/integration/test_mfa_flow.py -v

# 期待結果: 15+ passed
```

#### C. E2Eテスト（Playwright）
```bash
cd backend/tests/e2e

# MFA E2Eテスト
npx playwright test mfa-flow.spec.js

# 期待結果: 10+ passed
```

---

### ステップ5: 動作確認（手動テスト）

#### A. MFAセットアップ
1. ログイン: http://localhost:5200/login.html
   - ユーザー名: admin
   - パスワード: admin123

2. 設定画面へ: http://localhost:5200/mfa-settings.html

3. 「2要素認証を有効化」ボタンクリック

4. QRコードが表示される
   - Google Authenticatorで読み取り
   - 6桁コード入力

5. バックアップコード10個が表示される
   - 「ダウンロード」ボタンでTXTファイル保存
   - チェックボックス確認

6. 「完了」ボタンクリック

#### B. MFAログイン確認
1. ログアウト

2. 再ログイン
   - ユーザー名: admin
   - パスワード: admin123

3. TOTP入力画面が表示される
   - Google Authenticatorから6桁コード入力

4. ログイン成功
   - ダッシュボードが表示される

#### C. バックアップコード確認
1. ログアウト

2. 再ログイン（パスワードまで入力）

3. 「バックアップコードを使用」リンクをクリック

4. バックアップコード1つを入力
   - 形式: XXXX-XXXX-XXXX

5. ログイン成功
   - 使用したバックアップコードは再利用不可

---

### ステップ6: 本番環境デプロイ

#### A. 環境変数確認
```bash
cat backend/.env

# 以下が設定されていることを確認
MKS_USE_POSTGRESQL=true
SECRET_KEY=<your-secret-key>
JWT_SECRET_KEY=<your-jwt-secret>
DATABASE_URL=postgresql://mks_user:password@localhost/mirai_knowledge
```

#### B. サービス再起動
```bash
# 本番サービス再起動
sudo systemctl restart mirai-knowledge-prod

# ステータス確認
sudo systemctl status mirai-knowledge-prod

# ログ確認
sudo journalctl -u mirai-knowledge-prod -f
```

#### C. ヘルスチェック
```bash
# APIヘルスチェック
curl -s https://192.168.0.187:9443/api/v1/health | python3 -m json.tool

# 期待される出力
{
  "status": "healthy",
  "database": "postgresql",
  "version": "1.1.0",
  "features": {
    "mfa": true
  }
}
```

---

## 🧪 テストケース一覧

### ユニットテスト（21件）
- ✅ TOTP秘密鍵生成
- ✅ QRコード生成（Base64 PNG）
- ✅ TOTP検証（正常/異常）
- ✅ バックアップコード生成（10個）
- ✅ バックアップコードハッシュ化
- ✅ バックアップコード検証
- ✅ Provisioning URI生成

### 統合テスト（15+件）
- ✅ MFAセットアップフロー（end-to-end）
- ✅ MFA有効化（TOTP検証成功）
- ✅ MFA有効化（TOTP検証失敗）
- ✅ MFAログインフロー（正常）
- ✅ MFAログインフロー（異常）
- ✅ バックアップコード使用（1回限り）
- ✅ Rate limiting（5回/15分）
- ✅ MFA無効化
- ✅ バックアップコード再生成

### E2Eテスト（10+件）
- ✅ MFAセットアップウィザード全ステップ
- ✅ QRコード表示確認
- ✅ TOTP入力・検証
- ✅ バックアップコードダウンロード
- ✅ MFAログインフロー（ブラウザ自動化）

---

## 🔒 セキュリティチェックリスト

### 実装済みセキュリティ機能
- ✅ TOTP（RFC 6238準拠）
- ✅ ±30秒ウィンドウ（時刻ずれ対応）
- ✅ バックアップコードbcryptハッシュ化
- ✅ Rate limiting（5回/15分）
- ✅ mfa_token有効期限（5分）
- ✅ 監査ログ記録（11種類のMFAイベント）
- ✅ バックアップコード1回限り使用
- ✅ ブルートフォース対策

### デプロイ前確認事項
- [ ] 依存関係インストール完了
- [ ] データベースマイグレーション完了
- [ ] ユニットテスト全件PASS
- [ ] 統合テスト全件PASS
- [ ] 手動テスト完了（セットアップ→ログイン）
- [ ] バックアップコード動作確認
- [ ] Rate limiting動作確認
- [ ] 監査ログ記録確認
- [ ] 本番環境ヘルスチェックOK

---

## 🚨 トラブルシューティング

### 問題1: 依存関係インストールエラー
```
ModuleNotFoundError: No module named 'pyotp'
```

**解決策**:
```bash
pip install pyotp==2.9.0 qrcode==7.4.2 Pillow==10.0.0
```

### 問題2: QRコード生成エラー
```
ModuleNotFoundError: No module named 'PIL'
```

**解決策**:
```bash
pip install Pillow==10.0.0
```

### 問題3: マイグレーションエラー
```
relation "auth.users" does not exist
```

**解決策**:
```bash
# スキーマ作成
psql -U mks_user -d mirai_knowledge -c "CREATE SCHEMA IF NOT EXISTS auth;"

# 再度マイグレーション実行
alembic upgrade head
```

### 問題4: TOTP検証が常に失敗
```
TOTP verification failed even with correct code
```

**原因**: サーバーとクライアントの時刻ずれ

**解決策**:
```bash
# サーバー時刻同期
sudo ntpdate -s time.nist.gov

# または
sudo systemctl restart systemd-timesyncd
```

### 問題5: Rate limiting誤検知
```
Too many MFA verification attempts
```

**解決策**:
```bash
# AccessLog確認
psql -U mks_user -d mirai_knowledge -c "SELECT * FROM audit.access_logs WHERE action LIKE '%mfa%' ORDER BY created_at DESC LIMIT 10;"

# Rate limitリセット（15分待つ、または手動削除）
# 注意: 本番環境では慎重に実施
```

---

## 📊 監視・メトリクス

### 監視項目
- MFAセットアップ成功率
- MFAログイン成功/失敗率
- バックアップコード使用頻度
- Rate limitヒット回数
- TOTP検証失敗回数（ブルートフォース検知）

### Prometheusメトリクス
```python
# app_v2.py に追加推奨
mfa_setup_total = Counter('mfa_setup_total', 'Total MFA setups')
mfa_login_success = Counter('mfa_login_success', 'MFA login successes')
mfa_login_failure = Counter('mfa_login_failure', 'MFA login failures')
mfa_rate_limit_hit = Counter('mfa_rate_limit_hit', 'Rate limit hits')
```

### ログ監視
```bash
# MFA関連ログ
sudo journalctl -u mirai-knowledge-prod | grep -i mfa

# エラーログ
sudo journalctl -u mirai-knowledge-prod -p err
```

---

## 🔄 ロールバック手順

### 緊急ロールバック（MFA無効化）

#### A. 環境変数で無効化
```bash
# backend/.env に追加
MKS_MFA_ENABLED=false

# サービス再起動
sudo systemctl restart mirai-knowledge-prod
```

#### B. データベースロールバック
```bash
# Alembic使用
alembic downgrade -1

# または手動SQL
psql -U mks_user -d mirai_knowledge -c "ALTER TABLE auth.users DROP COLUMN IF EXISTS mfa_backup_codes;"
```

#### C. コードロールバック
```bash
# Gitコミット前の状態に戻す
git stash

# または特定のコミットに戻す
git revert <commit-hash>
```

---

## 📚 関連ドキュメント

- **技術ドキュメント**: `docs/security/2FA_IMPLEMENTATION.md`
- **ユーザーガイド**: `docs/user-guide/MFA_SETUP_GUIDE.md`
- **完了サマリー**: `docs/2FA_COMPLETION_SUMMARY.md`
- **API仕様**: `backend/openapi.yaml` (MFAエンドポイント)

---

## ✅ デプロイ完了チェックリスト

### 事前準備
- [ ] requirements.txtに依存関係追加確認
- [ ] マイグレーションスクリプト確認
- [ ] テスト環境で動作確認

### デプロイ作業
- [ ] 依存関係インストール
- [ ] データベースマイグレーション実行
- [ ] テスト実行（46+ケース全てPASS）
- [ ] サービス再起動
- [ ] ヘルスチェックOK

### 事後確認
- [ ] MFAセットアップ動作確認
- [ ] MFAログイン動作確認
- [ ] バックアップコード動作確認
- [ ] Rate limiting動作確認
- [ ] 監査ログ記録確認
- [ ] Prometheusメトリクス確認

---

**デプロイ担当者**: ________________
**デプロイ日時**: ________________
**承認者**: ________________

---

**作成者**: Claude Code (Sonnet 4.5)
**最終更新**: 2026-01-31
