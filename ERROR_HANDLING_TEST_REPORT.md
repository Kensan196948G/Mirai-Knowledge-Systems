# エラーハンドリング強化 - 実装レポート

## 実施日時
2025-12-30

## タスク概要
バックエンド・フロントエンド両方のエラーハンドリングを強化し、システムの堅牢性と運用性を向上させる。

---

## 1. バックエンド: データ読み込み・保存関数の強化

### 1.1 backend/app_v2.py の `load_data()` 関数

#### 修正内容
- **JSON.JSONDecodeError**: 壊れたJSON形式を検出し、エラー内容（行番号・列番号）を詳細ログ出力
- **PermissionError**: ファイル読み込み権限がない場合のエラーハンドリング
- **UnicodeDecodeError**: エンコーディングエラーの検出
- **データ型検証**: リスト以外のデータ型を検出し、空リストを返す
- **汎用Exception**: 予期しないエラーをキャッチし、詳細ログ出力

#### 変更前
```python
def load_data(filename):
    filepath = os.path.join(get_data_dir(), filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    return []
                return [item for item in data if isinstance(item, dict)]
        except (json.JSONDecodeError, ValueError) as e:
            print(f'[WARN] Failed to decode {filepath}: {e}')
            return []
    return []
```

#### 変更後
```python
def load_data(filename):
    """
    JSONファイルを安全に読み込む

    Args:
        filename: 読み込むJSONファイル名

    Returns:
        list: 読み込んだデータ（失敗時は空リスト）
    """
    filepath = os.path.join(get_data_dir(), filename)

    try:
        if not os.path.exists(filepath):
            print(f'[INFO] File not found: {filename} (returning empty list)')
            return []

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

            # データ型検証
            if not isinstance(data, list):
                print(f'[WARN] {filename}: Expected list, got {type(data).__name__}. Returning empty list.')
                return []

            # dict型のアイテムのみをフィルタリング
            valid_items = [item for item in data if isinstance(item, dict)]
            if len(valid_items) != len(data):
                print(f'[WARN] {filename}: Filtered out {len(data) - len(valid_items)} non-dict items')

            return valid_items

    except json.JSONDecodeError as e:
        print(f'[ERROR] JSON decode error in {filename}: {e} (line {e.lineno}, col {e.colno})')
        return []
    except PermissionError as e:
        print(f'[ERROR] Permission denied reading {filename}: {e}')
        return []
    except UnicodeDecodeError as e:
        print(f'[ERROR] Encoding error reading {filename}: {e}')
        return []
    except Exception as e:
        print(f'[ERROR] Unexpected error reading {filename}: {type(e).__name__}: {e}')
        return []
```

#### 効果
- **運用性向上**: エラー発生時の原因特定が容易になる
- **データ整合性**: 不正なデータ型を自動的にフィルタリング
- **可用性向上**: エラー時も空リストを返すことでシステムダウンを防止

---

### 1.2 backend/app_v2.py の `save_data()` 関数

#### 修正内容
- **アトミック書き込み**: 一時ファイルを使用してデータ破損を防止
- **ディレクトリ作成**: 保存先ディレクトリが存在しない場合は自動作成
- **詳細エラーハンドリング**: PermissionError、OSError、汎用Exceptionを個別にキャッチ
- **一時ファイルクリーンアップ**: 失敗時も一時ファイルを確実に削除

#### 変更前
```python
def save_data(filename, data):
    """JSONファイルにデータを保存"""
    filepath = os.path.join(get_data_dir(), filename)
    dirpath = os.path.dirname(filepath)
    fd, tmp_path = tempfile.mkstemp(prefix=f".{filename}.", suffix=".tmp", dir=dirpath)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, filepath)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
```

#### 変更後
```python
def save_data(filename, data):
    """
    JSONファイルに安全にデータを保存（アトミック書き込み）

    Args:
        filename: 保存するJSONファイル名
        data: 保存するデータ

    Raises:
        Exception: 保存に失敗した場合
    """
    filepath = os.path.join(get_data_dir(), filename)
    dirpath = os.path.dirname(filepath)

    # ディレクトリの存在確認
    try:
        os.makedirs(dirpath, exist_ok=True)
    except Exception as e:
        print(f'[ERROR] Failed to create directory {dirpath}: {e}')
        raise

    tmp_path = None
    try:
        # 一時ファイルを作成
        fd, tmp_path = tempfile.mkstemp(prefix=f".{filename}.", suffix=".tmp", dir=dirpath)

        # データを一時ファイルに書き込み
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # アトミックに置き換え
        os.replace(tmp_path, filepath)
        tmp_path = None  # 成功したのでクリーンアップ不要

        print(f'[INFO] Successfully saved {filename} ({len(data)} items)')

    except PermissionError as e:
        print(f'[ERROR] Permission denied writing {filename}: {e}')
        raise
    except OSError as e:
        print(f'[ERROR] OS error writing {filename}: {e}')
        raise
    except Exception as e:
        print(f'[ERROR] Unexpected error writing {filename}: {type(e).__name__}: {e}')
        raise
    finally:
        # 一時ファイルのクリーンアップ
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception as e:
                print(f'[WARN] Failed to remove temp file {tmp_path}: {e}')
```

#### 効果
- **データ整合性**: アトミック書き込みにより、書き込み途中でのプロセス中断時もデータ破損を防止
- **デバッグ性向上**: 詳細なエラーログにより問題の原因特定が容易
- **リソースリーク防止**: 一時ファイルを確実にクリーンアップ

---

### 1.3 backend/app.py の修正

backend/app_v2.py と同様の修正を適用。簡易版のため、アトミック書き込みは実装せず、基本的なエラーハンドリングのみ追加。

---

## 2. バックエンド: 標準エラーレスポンス関数の実装

### 2.1 `error_response()` 関数の追加

#### 実装内容
全てのAPIエンドポイントで統一されたエラーレスポンス形式を返す共通関数を実装。

```python
def error_response(message, code='ERROR', status_code=400, details=None):
    """
    標準化されたエラーレスポンスを返す

    Args:
        message: エラーメッセージ
        code: エラーコード（例: 'NOT_FOUND', 'VALIDATION_ERROR'）
        status_code: HTTPステータスコード
        details: 追加のエラー詳細情報

    Returns:
        tuple: (JSONレスポンス, HTTPステータスコード)
    """
    response = {
        'success': False,
        'error': {
            'code': code,
            'message': message
        }
    }

    if details:
        response['error']['details'] = details

    print(f'[ERROR] {code}: {message} (status={status_code})')

    return jsonify(response), status_code
```

#### レスポンス形式
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found",
    "details": {  // オプション
      "field": "username",
      "reason": "too short"
    }
  }
}
```

#### 効果
- **API一貫性**: 全エンドポイントで統一されたエラーレスポンス形式
- **クライアント実装の簡素化**: エラーハンドリングロジックの共通化が可能
- **デバッグ性向上**: エラーコードによる分類で問題の特定が容易

---

### 2.2 グローバルエラーハンドラーの追加

#### 実装内容
Flask アプリケーションレベルで未処理の例外をキャッチするグローバルハンドラーを追加。

```python
@app.errorhandler(Exception)
def handle_unexpected_error(e):
    """全ての未処理例外をキャッチ"""
    import traceback
    print(f'[ERROR] Unexpected error: {type(e).__name__}: {e}')
    print(traceback.format_exc())
    return error_response('Internal server error', 'INTERNAL_ERROR', 500)

@app.errorhandler(404)
def not_found(error):
    return error_response('Resource not found', 'NOT_FOUND', 404)

@app.errorhandler(500)
def internal_error(error):
    return error_response('Internal server error', 'INTERNAL_ERROR', 500)

@app.errorhandler(429)
def ratelimit_handler(error):
    """レート制限エラーハンドラ"""
    retry_after = str(error.description) if hasattr(error, 'description') else '60 seconds'
    return error_response(
        'リクエストが多すぎます。しばらく待ってから再試行してください。',
        'RATE_LIMIT_EXCEEDED',
        429,
        {'retry_after': retry_after}
    )

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return error_response('Token has expired', 'TOKEN_EXPIRED', 401)

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return error_response('Invalid token', 'INVALID_TOKEN', 401)

@jwt.unauthorized_loader
def missing_token_callback(error):
    return error_response('Authorization token is missing', 'MISSING_TOKEN', 401)
```

#### 効果
- **システム安定性**: 予期しないエラーでもシステムダウンせず、適切なエラーレスポンスを返す
- **エラートラッキング**: スタックトレースを含む詳細なエラーログ
- **ユーザー体験向上**: 明確なエラーメッセージによりユーザーが適切な対応を取れる

---

## 3. フロントエンド: APIクライアント関数の強化

### 3.1 webui/app.js の `fetchAPI()` 関数

#### 修正内容
- **標準化されたエラー処理**: バックエンドの `error_response()` 形式に対応
- **ステータスコード別の処理**: 401, 403, 404, 429, 500 に対して適切なメッセージ表示
- **ネットワークエラー検出**: `Failed to fetch` エラーをキャッチし、ユーザーフレンドリーなメッセージを表示
- **エラートースト表示**: `showNotification()` 関数を使用してエラーを視覚的に表示

#### 変更前（一部抜粋）
```javascript
// 権限エラー（403）
if (response.status === 403) {
  console.error('[API] 403 Forbidden.');
  showNotification('この操作を実行する権限がありません。', 'error');
  throw new Error('Permission denied');
}

if (!response.ok) {
  throw new Error(`API Error: ${response.status}`);
}
```

#### 変更後
```javascript
// エラーレスポンスの処理
if (!response.ok) {
  let errorMessage = `HTTP ${response.status}`;
  let errorCode = 'UNKNOWN_ERROR';

  try {
    const errorData = await response.json();
    if (errorData.error) {
      errorMessage = errorData.error.message || errorMessage;
      errorCode = errorData.error.code || errorCode;
    }
  } catch (e) {
    console.error('[API] Failed to parse error response:', e);
  }

  // ステータスコード別の処理
  if (response.status === 403) {
    showNotification('この操作を実行する権限がありません。', 'error');
  } else if (response.status === 404) {
    showNotification('リソースが見つかりません。', 'error');
  } else if (response.status === 429) {
    showNotification('リクエストが多すぎます。しばらく待ってから再試行してください。', 'warning');
  } else if (response.status === 500) {
    showNotification('サーバーエラーが発生しました。管理者に連絡してください。', 'error');
  } else {
    showNotification(`エラー: ${errorMessage}`, 'error');
  }

  const error = new Error(errorMessage);
  error.code = errorCode;
  error.status = response.status;
  throw error;
}

// ネットワークエラーの場合
if (error.message === 'Failed to fetch' || error.name === 'TypeError') {
  showNotification('ネットワークエラー: サーバーに接続できません。', 'error');
}
```

#### 効果
- **ユーザー体験向上**: 技術的なエラーメッセージを日本語の分かりやすいメッセージに変換
- **デバッグ性向上**: エラーコードとステータスコードをエラーオブジェクトに保持
- **エラー通知**: トースト通知により、ユーザーが即座にエラーを認識可能

---

### 3.2 webui/detail-pages.js の `apiCall()` 関数

webui/app.js の fetchAPI() と同様の修正を適用。詳細ページ専用のエラーハンドリングを実装。

#### 追加機能
- **認証エラー時の遅延リダイレクト**: エラーメッセージを2秒間表示後、ログイン画面へリダイレクト
- **`showError()` 関数の活用**: 詳細ページ専用のエラー表示領域を使用

```javascript
// 認証エラー
if (response.status === 401) {
  console.error('[API] Unauthorized. Redirecting to login...');
  showError('セッションの有効期限が切れました。再度ログインしてください。');
  setTimeout(() => {
    window.location.href = '/login.html';
  }, 2000);
  return null;
}
```

---

## 4. テストケース

### 4.1 バックエンドテスト項目

| テスト項目 | 内容 | 期待結果 |
|-----------|------|---------|
| ファイル未存在 | 存在しないJSONファイルを読み込み | 空リストを返す |
| JSON形式エラー | 壊れたJSON形式のファイルを読み込み | エラーログ出力 + 空リストを返す |
| 非リスト型データ | 辞書型のJSONファイルを読み込み | 空リストを返す |
| Unicode文字 | 日本語を含むデータの保存・読み込み | 正しく保存・読み込みできる |
| アトミック書き込み | 既存ファイルへの上書き保存 | データ破損なく保存される |
| 権限エラー | 書き込み権限のないディレクトリへの保存 | PermissionError をキャッチしログ出力 |
| エラーレスポンス形式 | error_response() 関数の出力 | 標準形式のJSONレスポンス |

### 4.2 フロントエンドテスト項目

| テスト項目 | 内容 | 期待結果 |
|-----------|------|---------|
| 401エラー | 認証トークンが無効 | トークンリフレッシュ → 失敗時ログアウト |
| 403エラー | 権限のない操作を実行 | エラートースト表示「権限がありません」 |
| 404エラー | 存在しないリソースへアクセス | エラートースト表示「リソースが見つかりません」 |
| 429エラー | レート制限超過 | 警告トースト表示 + retry_after 情報 |
| 500エラー | サーバーエラー | エラートースト表示「サーバーエラー」 |
| ネットワークエラー | サーバー接続不可 | エラートースト表示「ネットワークエラー」 |

---

## 5. 修正ファイル一覧

### バックエンド
- `/mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/app_v2.py`
  - `load_data()` 関数の強化
  - `save_data()` 関数の強化
  - `error_response()` 関数の追加
  - グローバルエラーハンドラーの追加

- `/mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/app.py`
  - `load_data()` 関数の強化
  - `save_data()` 関数の強化

### フロントエンド
- `/mnt/LinuxHDD/Mirai-Knowledge-Systems/webui/app.js`
  - `fetchAPI()` 関数の強化
  - エラーメッセージの日本語化
  - ステータスコード別のエラーハンドリング

- `/mnt/LinuxHDD/Mirai-Knowledge-Systems/webui/detail-pages.js`
  - `apiCall()` 関数の強化
  - 詳細ページ専用のエラーハンドリング

### テスト・ドキュメント
- `/mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/test_error_handling.py` (新規作成)
  - 単体テストスクリプト

- `/mnt/LinuxHDD/Mirai-Knowledge-Systems/ERROR_HANDLING_TEST_REPORT.md` (このファイル)
  - 実装レポート

---

## 6. まとめ

### 達成内容
1. **バックエンド**: JSON読み込み・保存のエラーハンドリングを強化
2. **バックエンド**: 標準化されたエラーレスポンス関数とグローバルエラーハンドラーを実装
3. **フロントエンド**: APIクライアント関数のエラーハンドリングを強化
4. **ユーザー体験**: エラーメッセージの日本語化と視覚的なエラー通知

### 効果
- **システム安定性**: 予期しないエラーでもシステムダウンしない
- **運用性**: 詳細なエラーログによるトラブルシューティングの効率化
- **ユーザー体験**: 分かりやすいエラーメッセージと視覚的な通知
- **保守性**: 統一されたエラーハンドリングパターンによるコードの可読性向上

### 今後の拡張可能性
- エラーログの集約・分析ツールとの連携
- エラー発生時の自動通知（Slack, Email等）
- エラーレート監視とアラート
- リトライロジックの実装（ネットワークエラー時）

---

## 付録: エラーコード一覧

| エラーコード | 説明 | HTTPステータス |
|-------------|------|---------------|
| `NOT_FOUND` | リソースが見つからない | 404 |
| `UNAUTHORIZED` | 認証失敗 | 401 |
| `FORBIDDEN` | 権限不足 | 403 |
| `VALIDATION_ERROR` | 入力検証エラー | 400 |
| `RATE_LIMIT_EXCEEDED` | レート制限超過 | 429 |
| `INTERNAL_ERROR` | サーバー内部エラー | 500 |
| `TOKEN_EXPIRED` | トークン有効期限切れ | 401 |
| `INVALID_TOKEN` | 不正なトークン | 401 |
| `MISSING_TOKEN` | トークンが未提供 | 401 |

---

**実装者**: Claude Sonnet 4.5
**実施日**: 2025-12-30
