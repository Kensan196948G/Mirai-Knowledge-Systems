import { defineConfig } from 'vite';
import legacy from '@vitejs/plugin-legacy';
import { resolve } from 'path';

export default defineConfig({
  // ルートディレクトリ設定
  root: 'webui',

  // マルチページアプリケーション対応
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'webui', 'index.html'),
        login: resolve(__dirname, 'webui', 'login.html'),
        admin: resolve(__dirname, 'webui', 'admin.html'),
        'search-detail': resolve(__dirname, 'webui', 'search-detail.html'),
        'sop-detail': resolve(__dirname, 'webui', 'sop-detail.html'),
        'law-detail': resolve(__dirname, 'webui', 'law-detail.html'),
        'incident-detail': resolve(__dirname, 'webui', 'incident-detail.html'),
        'expert-consult': resolve(__dirname, 'webui', 'expert-consult.html'),
        'mfa-setup': resolve(__dirname, 'webui', 'mfa-setup.html'),
        'mfa-settings': resolve(__dirname, 'webui', 'mfa-settings.html'),
        'ms365-sync-settings': resolve(__dirname, 'webui', 'ms365-sync-settings.html'),
        'offline': resolve(__dirname, 'webui', 'offline.html'),
        'module-test': resolve(__dirname, 'webui', 'module-test.html'),
      },
      output: {
        // チャンク分割（vendor、pwa）
        manualChunks(id) {
          // Node modules → サブチャンクに分割（大きなvendorチャンク防止）
          if (id.includes('node_modules')) {
            // Viteコアライブラリ
            if (id.includes('vite') || id.includes('@vitejs')) {
              return 'vendor-vite';
            }
            // その他のnode_modules
            return 'vendor';
          }
          // PWA関連 → pwa chunk
          if (id.includes('/pwa/') || id.includes('sw.js')) {
            return 'pwa';
          }
          // Core modules → core chunk
          if (id.includes('/src/core/')) {
            return 'core';
          }
          // Features → feature chunk
          if (id.includes('/src/features/')) {
            return 'features';
          }
          // Utils → utils chunk
          if (id.includes('/src/utils/')) {
            return 'utils';
          }
          // App modules → app chunk
          if (id.includes('/src/app/')) {
            return 'app';
          }
          // Pages → pages chunk
          if (id.includes('/src/pages/')) {
            return 'pages';
          }
        },
      },
    },
    outDir: '../dist',
    assetsDir: 'assets',
    sourcemap: true,
    // 本番ビルド最適化
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
    // Phase I-5: チャンクサイズ警告閾値を設定（デフォルト500KB→1000KB）
    chunkSizeWarningLimit: 1000,
    // Phase I-5: ターゲット設定でTree-shaking強化
    target: 'es2015',
    // Phase I-5: CSS最適化
    cssCodeSplit: true,
  },

  // 開発サーバー設定
  server: {
    port: 5173,
    strictPort: false,
    host: true,
    // Flask API プロキシ設定
    proxy: {
      '/api': {
        target: 'http://localhost:5200',
        changeOrigin: true,
        secure: false,
      },
      '/static': {
        target: 'http://localhost:5200',
        changeOrigin: true,
      },
    },
    // CORS設定
    cors: true,
  },

  // プレビューサーバー設定（本番ビルドのプレビュー）
  preview: {
    port: 4173,
    strictPort: false,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5200',
        changeOrigin: true,
        secure: false,
      },
    },
  },

  // レガシーブラウザ対応
  plugins: [
    legacy({
      targets: ['defaults', 'not IE 11'],
    }),
  ],

  // パスエイリアス設定
  resolve: {
    alias: {
      '@': resolve(__dirname, 'webui/src'),
      '@core': resolve(__dirname, 'webui/src/core'),
      '@features': resolve(__dirname, 'webui/src/features'),
      '@utils': resolve(__dirname, 'webui/src/utils'),
      '@app': resolve(__dirname, 'webui/src/app'),
      '@pages': resolve(__dirname, 'webui/src/pages'),
    },
  },

  // CSS設定
  css: {
    devSourcemap: true,
  },

  // ログレベル
  logLevel: 'info',

  // 環境変数の接頭辞
  envPrefix: 'MKS_',
});
