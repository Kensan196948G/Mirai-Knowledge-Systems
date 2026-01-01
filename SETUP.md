# セットアップガイド

建設土木ナレッジシステムのセットアップ手順を説明します。

## 📋 目次

1. [システム要件](#システム要件)
2. [インストール手順](#インストール手順)
3. [起動方法](#起動方法)
4. [動作確認](#動作確認)
5. [トラブルシューティング](#トラブルシューティング)

## システム要件

### 必須環境
- **OS**: Windows 10/11, macOS, Linux
- **Python**: 3.8以上
- **ブラウザ**: Chrome 90+, Firefox 88+, Edge 90+

### 推奨環境
- **メモリ**: 4GB以上
- **ディスク空間**: 500MB以上

## インストール手順

### ステップ1: Pythonのインストール確認

コマンドプロンプト（またはターミナル）を開いて、以下のコマンドを実行します：

```bash
python --version
```

Python 3.8以上がインストールされていることを確認してください。

**Pythonがインストールされていない場合:**
- [Python公式サイト](https://www.python.org/downloads/)からダウンロードしてインストールしてください
- インストール時に「Add Python to PATH」にチェックを入れてください

### ステップ2: プロジェクトディレクトリへ移動

```bash
cd Z:\Mirai-Knowledge-Systems
```

### ステップ3: 依存パッケージのインストール

```bash
cd backend
pip install -r requirements.txt
```

**エラーが発生した場合:**
- `pip`を最新版にアップグレード: `python -m pip install --upgrade pip`
- 再度インストールを試してください

### ステップ4: データディレクトリの確認

`backend/data/` ディレクトリに以下のファイルが存在することを確認します：
- `knowledge.json`
- `sop.json`
- `regulations.json`
- `incidents.json`
- `consultations.json`
- `approvals.json`

これらのファイルは初期データとして既に配置されています。

## 起動方法

### 環境変数の設定（重要）

セキュリティのため、JWT秘密鍵の設定が必須です：

```bash
# .envファイルを作成（まだ存在しない場合）
cd backend
cp .env.example .env

# JWT秘密鍵を生成して追加
python3 -c "import secrets; print('MKS_JWT_SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env
```

### 開発サーバーの起動（手動）

`backend` ディレクトリで以下のコマンドを実行します：

```bash
python app_v2.py
```

以下のような出力が表示されれば成功です：

```
============================================================
建設土木ナレッジシステム - サーバー起動中
============================================================
環境モード: development
アクセスURL: http://localhost:5100
============================================================
 * Serving Flask app 'app_v2'
 * Debug mode: off
 * Running on http://0.0.0.0:5100
```

> **注**: `app.py` は旧版（認証なし）、`app_v2.py` は新版（JWT認証 + RBAC対応）です。

### 本番サーバーの起動（systemd自動起動）

**Linux環境のみ**: systemdサービスとして登録することで、サーバー再起動時に自動起動できます：

```bash
# プロジェクトルートディレクトリで実行
./setup-systemd.sh
```

詳細は [SYSTEMD_SETUP.md](SYSTEMD_SETUP.md) を参照してください。

### ブラウザでアクセス

ブラウザを開いて、以下のURLにアクセスします：

```
http://localhost:5100/login.html
```

ログイン画面が表示されれば成功です！デモアカウント（admin / admin123など）でログインしてください。

## 動作確認

### 基本機能のテスト

#### 1. ダッシュボードの確認
- メトリクスカード（ナレッジ再利用率、事故ゼロ継続日数など）が表示されていることを確認
- 承認フロー一覧が表示されていることを確認

#### 2. 検索機能のテスト
1. 検索ボックスに「温度」と入力
2. 検索ボタンをクリック
3. 検索結果タブに関連するナレッジが表示されることを確認

#### 3. タブ切替のテスト
1. 「標準施工」タブをクリック
2. SOP一覧が表示されることを確認
3. 「事故・ヒヤリ」タブをクリック
4. 事故レポート一覧が表示されることを確認

#### 4. 新規登録のテスト
1. 画面右上の「新規ナレッジ登録」ボタンをクリック
2. タイトル、概要、カテゴリを入力
3. 登録完了のメッセージが表示されることを確認
4. 検索結果タブに新しいナレッジが表示されることを確認

### API動作確認

ブラウザの開発者ツール（F12キー）のコンソールを開き、以下のようなログが表示されていることを確認：

```
建設土木ナレッジシステム - 初期化中...
初期化完了！
```

エラーが表示されていないことを確認してください。

## トラブルシューティング

### ポート5100が既に使用されている

**エラーメッセージ:**
```
Address already in use
```

**解決方法:**

#### 方法1: ポートを変更する
`backend/app_v2.py` の最後の行を編集：
```python
app.run(host='0.0.0.0', port=5101, debug=False)  # 5100 → 5101に変更
```

その後、`http://localhost:5101` でアクセスしてください。

#### 方法2: 使用中のプロセスを終了する

**Windows:**
```bash
netstat -ano | findstr :5100
taskkill /PID <プロセスID> /F
```

**macOS/Linux:**
```bash
lsof -i :5100
kill -9 <PID>
```

**systemdサービスが起動している場合:**
```bash
sudo systemctl stop mirai-knowledge-system.service
```

### モジュールが見つからないエラー

**エラーメッセージ:**
```
ModuleNotFoundError: No module named 'flask'
```

**解決方法:**
```bash
pip install -r requirements.txt
```

それでも解決しない場合、仮想環境を作成してください：

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### CORS エラー

**エラーメッセージ（ブラウザコンソール）:**
```
Access to fetch at 'http://localhost:5100/api/...' has been blocked by CORS policy
```

**解決方法:**
- `backend/app_v2.py` で `Flask-CORS` が正しくインストールされていることを確認
- `.env` ファイルの `CORS_ORIGINS` 設定を確認
- サーバーを再起動してください

### データが表示されない

**確認事項:**
1. サーバーが正常に起動しているか確認
2. ブラウザのコンソールにエラーがないか確認
3. `backend/data/` ディレクトリにJSONファイルが存在するか確認
4. JSONファイルの形式が正しいか確認（JSONバリデータで検証）

### ブラウザキャッシュの問題

**解決方法:**
- ブラウザのキャッシュをクリア（Ctrl+Shift+Delete）
- スーパーリロード（Ctrl+Shift+R または Ctrl+F5）

## 開発モードでの起動

デバッグモードを有効にしている場合、コードを変更すると自動的にサーバーが再起動します。

変更を加えた後は、ブラウザをリロードしてください。

## 本番環境への移行

本番環境では以下の設定変更が必要です：

1. **systemdサービスとして設定** [SYSTEMD_SETUP.md](SYSTEMD_SETUP.md) を参照

2. **環境変数を本番用に設定** (`.env`ファイル):
   ```bash
   MKS_ENV=production
   MKS_DEBUG=false
   MKS_FORCE_HTTPS=true  # SSL/TLS証明書設定後
   ```

3. **SSL/TLS証明書の設定** (HTTPSを使用する場合)

4. **本番用WSGIサーバーの使用** (Gunicorn、uWSGI、Waitressなど)

5. **データベースへの移行** (PostgreSQLを推奨)

詳細は [Production-Deployment-Guide.md](docs/10_移行・展開(Deployment)/03_Production-Deployment-Guide.md) を参照してください。

4. HTTPS対応

5. 認証・認可の実装

## サポート

問題が解決しない場合は、以下の情報を添えてお問い合わせください：

- OSとバージョン
- Pythonのバージョン
- エラーメッセージの全文
- 実行したコマンド
- ブラウザの種類とバージョン

---

**Happy Coding! 🚀**
