# PWA Testing Guide - Phase D-5 Week 1

**作成日**: 2026-01-31
**対象**: Week 1 PWA基盤実装の動作確認

---

## 1. テスト環境準備

### 1.1 開発サーバー起動

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems

# Flaskサーバー起動（開発環境）
cd backend
source ../venv_linux/bin/activate
export FLASK_APP=app_v2.py
export FLASK_ENV=development
export MKS_ENV=development
flask run --host=0.0.0.0 --port=5200
```

### 1.2 ブラウザアクセス

- **URL**: http://localhost:5200 または http://192.168.0.187:5200
- **推奨ブラウザ**: Chrome 90+ または Edge 90+
- **DevTools**: F12で開発者ツールを開く

---

## 2. Service Worker登録確認

### 2.1 手順

1. ブラウザで http://localhost:5200 にアクセス
2. F12 → **Application** タブを開く
3. 左サイドバーの **Service Workers** をクリック

### 2.2 確認項目

| 項目 | 期待値 | 結果 |
|------|--------|------|
| Service Worker URL | `/sw.js` | [ ] |
| Status | `activated and is running` | [ ] |
| Scope | `/` | [ ] |
| Update on reload | チェック推奨 | [ ] |

### 2.3 コンソール確認

**Console**タブで以下のログが表示されることを確認:

```
[SW] Service Worker script loaded: v1.3.0
[SW] Install event: v1.3.0
[SW] Caching static assets
[SW] Static cache complete
[SW] Installed, waiting for activation signal
[PWA] Service Worker registered successfully
[PWA] Feature detection: {serviceWorker: true, backgroundSync: true, ...}
[PWA] Initialization complete
```

### 2.4 エラー時の対応

**エラー**: `Service Worker registration failed`
- **原因**: HTTPSが必要（localhostは例外）
- **対策**: localhostでアクセスしているか確認

**エラー**: `sw.js not found`
- **原因**: ファイルパスが間違っている
- **対策**: `webui/sw.js`が存在するか確認

---

## 3. Manifest読み込み確認

### 3.1 手順

1. DevTools → **Application** タブ
2. 左サイドバーの **Manifest** をクリック

### 3.2 確認項目

| 項目 | 期待値 | 結果 |
|------|--------|------|
| Name | `Mirai Knowledge Systems - 建設土木ナレッジシステム` | [ ] |
| Short name | `MKS` | [ ] |
| Start URL | `/` | [ ] |
| Theme color | `#2f4b52` | [ ] |
| Background color | `#f1ece4` | [ ] |
| Display | `standalone` | [ ] |
| Icons | 9個表示される | [ ] |

### 3.3 アイコン確認

**注意**: アイコン画像は未生成のため、以下の警告が表示される可能性があります:

```
Warning: Failed to load resource: the server responded with a status of 404 (Not Found)
/icons/icon-192x192.png
```

**対策**: Week 2でアイコン生成予定（動作には影響なし）

---

## 4. キャッシュ動作確認

### 4.1 静的アセットキャッシュ（Cache First）

**手順**:
1. DevTools → **Application** → **Cache Storage**
2. `mks-static-v1.3.0`を展開
3. キャッシュされたファイルを確認

**期待値**: 以下のファイルがキャッシュされている
- `/`
- `/index.html`
- `/app.js`
- `/styles.css`
- `/sw.js`
- その他の静的アセット

### 4.2 2回目のページロード確認

**手順**:
1. DevTools → **Network** タブ
2. ページをリロード（Ctrl+R）
3. ファイルの読み込み元を確認

**期待値**: 静的アセットが`(ServiceWorker)`から配信される

### 4.3 パフォーマンス確認

**手順**:
1. DevTools → **Lighthouse** タブ
2. Categories: **Progressive Web App** のみ選択
3. **Analyze page load** をクリック

**期待値（暫定）**:
- PWA Score: 70-80点（アイコン未生成のため減点）
- Service Worker登録: ✅
- HTTPS使用: ⚠️ localhost（本番ではHTTPS）
- Manifest: ✅

---

## 5. オフラインモード確認

### 5.1 手順

1. ページを通常通り読み込む（Service Workerをアクティブ化）
2. DevTools → **Application** → **Service Workers**
3. **Offline** チェックボックスをON
4. 新しいページに移動（例: 存在しないURL `/test-offline`）

### 5.2 期待値

- **オフラインページ**（`offline.html`）が表示される
- タイトル: 「オフラインモード」
- アイコン: 📡（アニメーション付き）
- ボタン: 「再接続を試す」「キャッシュコンテンツを表示」

### 5.3 オフライン機能確認

**「キャッシュコンテンツを表示」ボタン**:
- クリックすると、キャッシュされたAPI応答が一覧表示される
- カテゴリ別（ナレッジ、SOP、規制情報など）に分類される

**「再接続を試す」ボタン**:
- クリックすると、`/api/health`へのリクエストを試行
- オフラインの場合: 「まだオフラインです」アラート表示

### 5.4 オフライン状態表示確認

**手順**:
1. ブラウザのネットワーク接続を物理的にOFF（WiFi無効化）
2. ページをリロード

**期待値**:
- ページ上部に**オフライン表示バー**が表示される
- 背景色: オレンジ（`#f59e0b`）
- テキスト: 「📡 オフラインモード - キャッシュされたコンテンツのみ利用可能」

---

## 6. インストールプロンプト確認

### 6.1 手順（Chrome/Edge）

1. 新しいシークレットウィンドウを開く
2. http://localhost:5200 にアクセス
3. 2分間待機、または3ページ閲覧

### 6.2 期待値

**インストールバナー**が画面下部に表示される:
- アイコン: 📱
- テキスト: 「アプリとしてインストール」「オフラインでも使用できます」
- ボタン: 「インストール」「後で」

### 6.3 インストール動作確認

**「インストール」ボタン**:
1. クリックすると、ブラウザネイティブのインストールプロンプトが表示される
2. 「インストール」を選択すると、スタンドアロンアプリとして起動
3. ブラウザのアドレスバーが非表示になる

**「後で」ボタン**:
1. クリックすると、バナーが消える
2. 7日間は再表示されない（`localStorage`に記録）

### 6.4 iOS Safari確認

**注意**: iOS Safariでは`beforeinstallprompt`イベントが未サポート

**手順**:
1. iPhone/iPadのSafariで http://192.168.0.187:5200 にアクセス
2. 共有ボタン → 「ホーム画面に追加」を手動選択

**期待値**:
- アプリアイコンがホーム画面に追加される
- タップすると、フルスクリーンで起動

---

## 7. JWT暗号化確認（開発者向け）

### 7.1 手順

1. ログイン画面でログイン実行
2. DevTools → **Console**
3. 以下のコードを実行:

```javascript
// CryptoHelperのテスト
const crypto = new CryptoHelper();

// 暗号化テスト
crypto.encrypt('test-token-12345').then(result => {
  console.log('Encrypted:', result);

  // 復号化テスト
  crypto.decrypt(result.encrypted, result.iv).then(decrypted => {
    console.log('Decrypted:', decrypted);
  });
});
```

### 7.2 期待値

**Console出力**:
```
Encrypted: {encrypted: Array(xxx), iv: Array(12)}
Decrypted: test-token-12345
```

### 7.3 IndexedDB確認

**手順**:
1. DevTools → **Application** → **IndexedDB**
2. `mks-pwa` → `tokens`を展開

**期待値**:
- `access_token`が暗号化された配列として保存される
- `iv`（初期化ベクトル）が保存される

---

## 8. Service Worker更新確認

### 8.1 手順

1. `webui/sw.js`を編集:
   ```javascript
   const SW_VERSION = 'v1.3.1'; // v1.3.0 → v1.3.1に変更
   ```
2. ファイルを保存
3. ブラウザでページをリロード

### 8.2 期待値

**更新バナー**が表示される:
- テキスト: 「新しいバージョンが利用可能です」
- ボタン: 「今すぐ更新」「後で」

**「今すぐ更新」ボタン**:
- クリックすると、新しいService Workerがアクティブ化
- ページが自動リロードされる

---

## 9. トラブルシューティング

### 9.1 Service Worker登録失敗

**症状**: `[PWA] Service Worker registration failed`

**原因と対策**:
| 原因 | 対策 |
|------|------|
| HTTPSが必要 | localhostでアクセス |
| sw.jsが404 | ファイルパス確認 |
| キャッシュ問題 | Ctrl+Shift+R（強制リロード） |
| CORS問題 | Flaskバックエンドで CORS設定確認 |

### 9.2 Manifest読み込み失敗

**症状**: `Manifest: Line: 1, column: 1, Syntax error.`

**対策**:
1. `webui/manifest.json`の構文エラーを確認
2. JSONバリデーター（jsonlint.com）で検証

### 9.3 オフラインページ表示されない

**症状**: オフライン時に「このサイトにアクセスできません」

**原因と対策**:
1. Service Workerが未登録 → ページをリロード
2. `offline.html`が404 → ファイル存在確認
3. キャッシュ未完了 → 1-2分待機してから再試行

---

## 10. テスト結果記録

### 10.1 チェックリスト

| テスト項目 | 結果 | 備考 |
|-----------|------|------|
| Service Worker登録 | [ ] PASS / [ ] FAIL |  |
| Manifest読み込み | [ ] PASS / [ ] FAIL |  |
| 静的アセットキャッシュ | [ ] PASS / [ ] FAIL |  |
| オフラインページ表示 | [ ] PASS / [ ] FAIL |  |
| オフライン状態検出 | [ ] PASS / [ ] FAIL |  |
| インストールプロンプト | [ ] PASS / [ ] FAIL |  |
| JWT暗号化/復号化 | [ ] PASS / [ ] FAIL |  |
| Service Worker更新 | [ ] PASS / [ ] FAIL |  |

### 10.2 Lighthouseスコア

| 指標 | 目標 | 実測 | 備考 |
|------|------|------|------|
| PWA Score | 70-80 |  | アイコン未生成 |
| Performance | 90+ |  |  |
| Accessibility | 90+ |  |  |

### 10.3 問題点と対応

| 問題 | 重要度 | 対応 |
|------|--------|------|
|  |  |  |

---

## 11. 次のステップ

**Week 1完了後**:
- ✅ 基本的なPWA機能が動作確認できた
- ⏳ Week 2: キャッシュ戦略完成（cache-manager.js, sync-manager.js）
- ⏳ Week 3: UI最適化、アイコン生成、本番デプロイ

**ブロッキング問題がある場合**:
- 実装修正が必要な場合は、Week 2開始前に対応
- 軽微な問題は Week 2-3で対応可能

---

**テスト実施者**: ________________
**実施日**: ________________
**承認**: ________________
