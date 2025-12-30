# セキュリティ修正レポート

日付: 2025-12-30
優先度: Priority 1（緊急）

## 実施したセキュリティ修正

### 1. JWT秘密鍵の環境変数必須化

**問題点:**
- デフォルトの固定JWT秘密鍵がハードコーディングされていた
- 本番環境で固定鍵が使用されるリスクがあった

**修正内容:**
- `backend/app_v2.py`: JWT秘密鍵のデフォルト値を削除
- 環境変数 `MKS_JWT_SECRET_KEY` が未設定の場合はエラーで起動を停止
- 明確なエラーメッセージで設定方法を案内

**修正箇所:**
```python
# backend/app_v2.py (行120-129)
JWT_SECRET_KEY = os.environ.get('MKS_JWT_SECRET_KEY')
if not JWT_SECRET_KEY:
    raise ValueError(
        'MKS_JWT_SECRET_KEY environment variable is required. '
        'Please set a secure random key (minimum 32 characters). '
        'Example: export MKS_JWT_SECRET_KEY="your-secure-random-key-here"'
    )
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
```

### 2. HTTPS強制設定の本番環境デフォルト化

**問題点:**
- 本番環境でHTTPS強制がデフォルトで無効だった
- セキュアな接続が保証されていなかった

**修正内容:**
- `MKS_ENV=production` の場合、HTTPS強制をデフォルトで有効化
- 環境変数で明示的に無効化しない限り、HTTPSを強制

**修正箇所:**
```python
# backend/app_v2.py (行52-61)
def __init__(self, app, force_https=None, trust_proxy=None):
    self.app = app
    # 本番環境ではHTTPS強制をデフォルト有効化
    is_production = os.environ.get('MKS_ENV', 'development').lower() == 'production'
    default_force_https = 'true' if is_production else 'false'
    
    self.force_https = force_https if force_https is not None else \
        os.environ.get('MKS_FORCE_HTTPS', default_force_https).lower() in ('true', '1', 'yes')
```

### 3. .env.exampleファイルの作成

**問題点:**
- 環境変数の設定例が不明確だった
- 新規セットアップ時の設定が困難だった

**修正内容:**
- `backend/.env.example` ファイルを新規作成
- 全ての環境変数の説明とサンプル値を記載
- セキュリティ設定、HTTPS設定、外部通知設定などを網羅

**ファイル:** `backend/.env.example`

### 4. XSS脆弱性の修正

**問題点:**
- `innerHTML` を使用してユーザー入力を直接HTMLに埋め込んでいた
- XSS攻撃のリスクがあった

**修正内容:**
- `webui/actions.js`: トースト通知の `innerHTML` を DOM API に置き換え
- `webui/notifications.js`: 通知一覧表示の `innerHTML` を DOM API に置き換え

**修正例（actions.js）:**
```javascript
// 修正前
toast.innerHTML = `
  <div class="toast-icon">${iconMap[type] || 'ℹ'}</div>
  <div class="toast-message">${message}</div>
`;

// 修正後
const iconDiv = document.createElement('div');
iconDiv.className = 'toast-icon';
iconDiv.textContent = iconMap[type] || 'ℹ';

const messageDiv = document.createElement('div');
messageDiv.className = 'toast-message';
messageDiv.textContent = message;

toast.appendChild(iconDiv);
toast.appendChild(messageDiv);
```

**修正ファイル:**
- `webui/actions.js`
- `webui/notifications.js`

### 5. README.mdのセキュリティドキュメント更新

**修正内容:**
- 環境変数の設定手順を追加
- セキュリティセクションを更新し、実施済みの対策を明記
- インストール手順に環境変数設定ステップを追加

## 残存するXSS脆弱性（今後の対応が必要）

以下のファイルには多数の `innerHTML` 使用箇所が残っています:

### 優先度: 高

1. **detail-pages.js** (70+ 箇所)
   - ナレッジ詳細、SOP詳細、事故レポート詳細、専門家相談詳細の表示
   - 影響範囲: 全ての詳細ページ

2. **detail-loader.js** (10+ 箇所)
   - 詳細データのロード処理
   - 影響範囲: 詳細ページの初期表示

3. **expert-consult-actions.js** (5+ 箇所)
   - 専門家相談のアクション処理
   - 影響範囲: 専門家相談機能

4. **sop-detail-functions.js** (3+ 箇所)
   - SOP詳細の機能
   - 影響範囲: SOP詳細ページ

### 推奨される対応

1. **app.js の createElement ヘルパー関数を活用**
   - 既に `createElement` 関数が実装済み（app.js 行180-202）
   - この関数を使用してDOM要素を安全に作成

2. **段階的な修正アプローチ**
   - Phase 1: ユーザー入力を含む箇所を優先的に修正
   - Phase 2: 静的コンテンツの箇所を修正
   - Phase 3: 完全なinnerHTML削除

3. **テスト計画**
   - 各修正後に表示確認
   - XSSペイロード（`<script>alert('XSS')</script>`等）でテスト
   - 機能回帰テストの実施

## セキュリティテスト推奨事項

### 1. JWT秘密鍵のテスト

```bash
# 環境変数なしで起動してエラーを確認
python backend/app_v2.py
# 期待される結果: ValueError with helpful message

# 環境変数を設定して起動
export MKS_JWT_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
python backend/app_v2.py
# 期待される結果: 正常起動
```

### 2. XSS攻撃のテスト

以下のペイロードで通知機能をテスト:

```javascript
// テスト用XSSペイロード
<script>alert('XSS')</script>
<img src=x onerror=alert('XSS')>
<svg onload=alert('XSS')>
```

通知作成時にこれらのペイロードを含むメッセージを送信し、
エスケープされて表示されることを確認。

### 3. HTTPS強制のテスト

```bash
# 本番環境モードで起動
export MKS_ENV=production
export MKS_JWT_SECRET_KEY="your-secret-key"
python backend/app_v2.py

# HTTPアクセスがHTTPSにリダイレクトされることを確認
curl -I http://localhost:5100
# 期待される結果: 301 Moved Permanently, Location: https://...
```

## 本番環境へのデプロイ前チェックリスト

- [ ] MKS_JWT_SECRET_KEY に安全なランダム鍵を設定（最低32文字）
- [ ] MKS_ENV=production を設定
- [ ] SSL証明書を設定（Let's Encrypt等）
- [ ] MKS_FORCE_HTTPS は自動的に有効化されることを確認
- [ ] MKS_HSTS_ENABLED=true を設定
- [ ] CORS_ORIGINS を本番ドメインに設定
- [ ] 全てのXSS脆弱性を修正（detail-pages.js等）
- [ ] セキュリティヘッダーが適切に設定されていることを確認
- [ ] レート制限が有効化されていることを確認
- [ ] 監査ログが正常に記録されていることを確認

## 変更ファイル一覧

### バックエンド
- `backend/app_v2.py` (JWT秘密鍵必須化、HTTPS強制デフォルト化)
- `backend/.env.example` (新規作成)

### フロントエンド
- `webui/actions.js` (XSS修正)
- `webui/notifications.js` (XSS修正)

### ドキュメント
- `README.md` (セキュリティセクション更新、環境変数設定手順追加)
- `SECURITY_FIXES.md` (このファイル、新規作成)

## 次のステップ

1. **優先度1: 残存XSS脆弱性の完全修正**
   - detail-pages.js の全 innerHTML を修正
   - その他のファイルの innerHTML を修正

2. **優先度2: セキュリティテストの実施**
   - 自動化されたXSSスキャン
   - ペネトレーションテスト
   - セキュリティ監査

3. **優先度3: 継続的セキュリティ改善**
   - CSRF対策の強化
   - Content Security Policy の厳格化
   - セキュリティヘッダーの定期レビュー

