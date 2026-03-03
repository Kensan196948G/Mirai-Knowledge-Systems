# CHANGELOG

## [1.6.0] - 2026-03-03

### Added
- **Phase F**: フロントエンドESMモジュール化完了
  - `webui/src/core/` - APIクライアント・認証・ロガー（F-1）
  - `webui/src/features/` - MFA/MS365/PWA/Search/Knowledge モジュール（F-2）
  - `webui/src/utils/` - DOM操作/日付/バリデーション/ファイル操作（F-3）
  - `webui/src/app/` - アプリ初期化・ルーター・UIコントローラー等（F-4）
  - `webui/src/pages/` - 詳細ページモジュール群（F-4）
- **Phase G-2**: Jestテスト195件追加（date-formatter/validation/dom-helpers）
- **Phase G-3**: Flask Blueprint基盤構築（auth_bp, knowledge_bp）
- **E2Eテスト**: Phase FモジュールのPlaywright検証（27件）

### Changed
- **Phase G-1**: CSP強化（worker-src/manifest-src/object-src 追加）
- **Phase G-3-2**: `check_permission` デコレータをJWT claims依存に変更（N+1解消、48エンドポイント対応）
- `vite.config.js`: @app/@pagesエイリアス追加、utils/app/pagesチャンク最適化
- `backend/app_v2.py`: JWT refreshエンドポイントのrolesクレーム引き継ぎ修正

### Fixed
- W-001: `createTableRowWithHTML` でHTML文字列をDOMElementに変換（XSS防止、5箇所）
- JWT refresh後のrolesクレーム欠落バグ修正

### Security
- rollup GHSA-mw96-cpmx-2vgc (HIGH Path Traversal) → v4.59.0で解消
- CSPに`worker-src 'self'`, `manifest-src 'self'`, `object-src 'none'`追加
- セキュリティ監査評価: **A**（ブロッキング問題0件）

## [1.5.0] - 2026-03-03

### Added
- Phase F-2〜F-4: フロントエンドESMモジュール化（33ファイル）
- N+1クエリ最適化（data_access.py: try-except-finally、ロガー追加）

## [1.4.0] - 2026-01-31

### Added
- Phase D-5: PWA対応（Service Worker、オフライン機能、モバイル最適化）
- Phase D-4: Microsoft 365連携
- Phase D-3: 2要素認証（TOTP）
