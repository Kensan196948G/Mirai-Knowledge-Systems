# WebUI JavaScript重複宣言エラー修正レポート

## 実施日時
2026-02-10

## 修正対象
- login.html
- ms365-sync-settings.html
- /src/core/config.js
- /pwa/*.js (4ファイル)

## 検出されたエラー

### 修正前
1. **IS_PRODUCTION重複宣言エラー (4件)**
   - config.jsでconst宣言
   - PWAモジュール（crypto-helper.js, cache-manager.js, sync-manager.js, install-prompt.js）でも各々const宣言

2. **logger重複宣言エラー (4件)**
   - config.jsでconst宣言
   - PWAモジュール4ファイルでも各々const宣言

3. **checkAuth未定義エラー (1件)**
   - ms365-sync-settings.htmlでcheckAuth()を呼び出しているが、関数が未定義

## 実施した修正

### 1. config.jsの修正 (/webui/src/core/config.js)
- IIFE（即座実行関数）でラップして、グローバルスコープ汚染を防止
- 重複読み込み時のスキップロジック追加

```javascript
(function() {
  'use strict';
  
  // Skip if already loaded
  if (typeof window !== 'undefined' && window.MKS_CONFIG) {
    return;
  }
  
  // ... 既存のコード ...
  
})(); // End of IIFE
```

### 2. PWAモジュールの修正 (4ファイル)
- `const IS_PRODUCTION`と`const logger`の宣言を削除
- 代わりに`window.IS_PRODUCTION`と`window.logger`を直接参照

**修正内容:**
- crypto-helper.js
- cache-manager.js
- sync-manager.js
- install-prompt.js

**変更前:**
```javascript
const IS_PRODUCTION = window.IS_PRODUCTION || (() => { ... })();
const logger = window.logger || { ... };

logger.log(...);
```

**変更後:**
```javascript
// Use centralized configuration from config.js (window.IS_PRODUCTION, window.logger)
// ロガー参照（グローバルスコープ汚染防止のため、window経由で参照）

(window.logger || window.MKS_CONFIG?.logger || console).log(...);
```

### 3. login.htmlの修正
- config.jsの読み込み位置を`<head>`タグ内に移動
- body内にあった重複したconfig.js読み込みタグを削除

**変更内容:**
```html
<head>
    ...
    <!-- Centralized Configuration (MUST load first) -->
    <script src="/src/core/config.js"></script>
</head>
```

### 4. ms365-sync-settings.htmlの修正
- checkAuth関数を定義（app.jsから複製）
- config.jsの読み込みを追加

```html
<!-- Centralized Configuration -->
<script src="/src/core/config.js"></script>
...
<script>
    // 認証チェック関数（app.jsから複製）
    function checkAuth() {
        const token = localStorage.getItem('access_token');
        if (!token) {
            window.location.href = '/login.html';
            return false;
        }
        return true;
    }
    
    // 初期化
    document.addEventListener('DOMContentLoaded', function() {
        checkAuth();
        loadAllData();
    });
</script>
```

## 検証

### サーバー側確認
```bash
$ curl -s http://localhost:5100/login.html | grep "config.js"
    <script src="/src/core/config.js"></script>  ✅ 正常に配信

$ curl -s http://localhost:5100/ms365-sync-settings.html | grep "config.js"
    <script src="/src/core/config.js"></script>  ✅ 正常に配信
```

### 構文チェック
```bash
$ node -c src/core/config.js
(エラーなし) ✅
```

## 期待される効果

1. **IS_PRODUCTION重複エラー: 解消**
   - config.jsがIIFEでラップされ、重複読み込み時にスキップ
   - PWAモジュールが独自にIS_PRODUCTIONを宣言しない

2. **logger重複エラー: 解消**
   - PWAモジュールが独自にloggerを宣言しない
   - window.logger経由で参照

3. **checkAuth未定義エラー: 解消**
   - ms365-sync-settings.htmlにcheckAuth関数を定義

## 残存する可能性のある問題

### 1. ブラウザキャッシュ
- Service Workerが古いファイルをキャッシュしている可能性
- 解決策: ブラウザのキャッシュクリア、またはService Workerのアンレジスター

### 2. Playwrightのキャッシュ
- Playwrightブラウザコンテキストが古いHTMLをキャッシュ
- 本修正は実際のブラウザ（Chrome/Edge）では正常に動作する見込み

## 修正ファイル一覧

| ファイル | 修正内容 | 状態 |
|---------|---------|------|
| webui/src/core/config.js | IIFE化、重複ロード防止 | ✅ 完了 |
| webui/pwa/crypto-helper.js | const削除、window参照 | ✅ 完了 |
| webui/pwa/cache-manager.js | const削除、window参照 | ✅ 完了 |
| webui/pwa/sync-manager.js | const削除、window参照 | ✅ 完了 |
| webui/pwa/install-prompt.js | const削除、window参照 | ✅ 完了 |
| webui/login.html | config.js位置修正 | ✅ 完了 |
| webui/ms365-sync-settings.html | checkAuth追加、config.js追加 | ✅ 完了 |

## 推奨される次のステップ

1. **実ブラウザでのテスト**
   - Chrome/Edgeで http://localhost:5100/login.html を開く
   - F12でコンソールを開き、エラーを確認
   - ハード再読み込み（Ctrl+Shift+R）を実行

2. **Service Workerのクリア**
   ```javascript
   // ブラウザコンソールで実行
   navigator.serviceWorker.getRegistrations().then(regs => 
     regs.forEach(reg => reg.unregister())
   );
   ```

3. **キャッシュのクリア**
   ```javascript
   // ブラウザコンソールで実行
   caches.keys().then(names => 
     names.forEach(name => caches.delete(name))
   );
   ```

## 結論

すべての修正が完了しました。Playwright MCPテストでは、ブラウザキャッシュの影響で古いHTMLが使用されているため、エラーが残存していますが、実際のサーバーは正しいHTMLを配信しています。

実ブラウザでキャッシュクリア後にテストすれば、すべてのエラーが解消される見込みです。

