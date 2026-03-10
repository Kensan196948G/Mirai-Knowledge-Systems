/**
 * env-indicator.js
 * WebUI 環境インジケーター
 *
 * ブラウザタブのファビコンとタイトルを環境（開発/本番）に応じて設定します。
 * - 開発環境: オレンジ背景「開」アイコン + タイトルに「[開発]」プレフィックス
 * - 本番環境: グリーン背景「本」アイコン + タイトルに「[本番]」プレフィックス
 *
 * 環境判定の優先順位:
 *   1. window.IS_PRODUCTION（config.js が先に読み込まれた場合）
 *   2. URLパラメータ ?env=production / ?env=development
 *   3. localStorage['MKS_ENV']
 *   4. ポート番号（開発: 5200/5243, 本番: 9100/9443）
 *   5. ホスト名（localhost/127.0.0.1 → 開発, それ以外 → 本番）
 */
(function () {
  'use strict';

  var ENV_PORTS = {
    development: { http: 5200, https: 5243 },
    production: { http: 9100, https: 9443 }
  };

  function detectEnvironment() {
    // 1. config.js の IS_PRODUCTION を優先
    if (typeof window !== 'undefined' && typeof window.IS_PRODUCTION !== 'undefined') {
      return window.IS_PRODUCTION;
    }

    // 2. URL パラメータ
    try {
      var urlParams = new URLSearchParams(window.location.search);
      var envParam = urlParams.get('env');
      if (envParam === 'production') return true;
      if (envParam === 'development') return false;
    } catch (e) {}

    // 3. localStorage
    try {
      var stored = localStorage.getItem('MKS_ENV');
      if (stored === 'production') return true;
      if (stored === 'development') return false;
    } catch (e) {}

    // 4. ポート番号
    var port = parseInt(window.location.port || '0', 10);
    if (port === ENV_PORTS.production.http || port === ENV_PORTS.production.https) return true;
    if (port === ENV_PORTS.development.http || port === ENV_PORTS.development.https) return false;

    // 5. ホスト名フォールバック
    var hostname = window.location.hostname;
    return hostname !== 'localhost' && hostname !== '127.0.0.1';
  }

  function createEnvFavicon(isProduction) {
    var color = isProduction ? '#27ae60' : '#e67e22';
    var char = isProduction ? '本' : '開';
    var svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
      + '<rect width="32" height="32" rx="6" fill="' + color + '"/>'
      + '<text x="16" y="23" font-family="Arial,sans-serif" font-size="15"'
      + ' font-weight="bold" text-anchor="middle" fill="white">' + char + '</text>'
      + '</svg>';
    return 'data:image/svg+xml,' + encodeURIComponent(svg);
  }

  function applyEnvIndicators() {
    var isProduction = detectEnvironment();
    var envName = isProduction ? '本番' : '開発';
    var faviconUri = createEnvFavicon(isProduction);

    // ファビコンを更新（apple-touch-icon 以外）
    var links = document.querySelectorAll('link[rel*="icon"]');
    var updated = false;
    for (var i = 0; i < links.length; i++) {
      var rel = links[i].getAttribute('rel') || '';
      if (rel.indexOf('apple') === -1) {
        links[i].type = 'image/svg+xml';
        links[i].href = faviconUri;
        updated = true;
      }
    }

    // link 要素がなければ head に追加
    if (!updated) {
      var link = document.createElement('link');
      link.rel = 'icon';
      link.type = 'image/svg+xml';
      link.href = faviconUri;
      document.head.appendChild(link);
    }

    // タイトルにプレフィックスを追加（重複防止）
    var prefix = '[' + envName + ']';
    if (document.title && !document.title.startsWith('[開発]') && !document.title.startsWith('[本番]')) {
      document.title = prefix + ' ' + document.title;
    } else if (!document.title) {
      document.title = prefix + ' 建設土木ナレッジシステム';
    }

    // 他のモジュールから参照できるようにグローバルに保存
    window.MKS_ENV_INDICATOR = { isProduction: isProduction, envName: envName };
  }

  // DOM が利用可能な状態で実行
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyEnvIndicators);
  } else {
    applyEnvIndicators();
  }
})();
