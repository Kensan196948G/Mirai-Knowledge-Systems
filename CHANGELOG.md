# CHANGELOG

## [1.7.0] - 2026-03-10

### Added
- **Phase H-1**: Flask Blueprint完全移行完了（app_v2.py 7,155行→1,572行、78%削減）
  - `backend/blueprints/` 全7モジュール稼働（auth/knowledge/dashboard/ms365/operations/admin/recommendations）
  - `backend/app_helpers.py` 共有ヘルパー統合
- **Phase H-2**: DALテストカバレッジ大幅向上
  - `tests/unit/test_dal_knowledge_coverage.py`（新規）
  - `tests/unit/test_dal_ms365_coverage.py`（新規）
  - `tests/unit/test_dal_operations_coverage.py`（新規）
  - 新規テスト +196件、全体カバレッジ 66% → 75%
- **Phase I 基盤**: パフォーマンス最適化ロードマップ策定
  - `app_helpers.py`: CACHE_TTL機能別定数追加（SHORT/DEFAULT/LONG/VERY_LONG）
  - `docs/PHASE_I_PERFORMANCE_ROADMAP.md`: 82→150+ req/sec 目標設定
- **MS365ファイルプレビューPWA統合**（Phase 3）
  - Service Worker キャッシュ戦略実装（networkFirstMS365Preview）
  - `webui/styles.css`: プレビューUIスタイル追加

### Changed
- `backend/requirements.txt`: psutil 5.9.6→7.2.2、test依存分離
- `backend/tests/conftest.py`: app_helpers キャッシュ統合（Phase H-2対応）
- `.github/workflows/pr-quality-gate.yml`: Backend Tests タイムアウト30分化・並列実行（-n auto）
- `.github/copilot-instructions.md`: Version 1.4.0→1.6.0更新、CI修復履歴追加

### Fixed
- E731: `test_dal_postgresql_coverage.py` lambda→def 変換（50件）
- ruff: All checks passed（全体クリーン状態）

### Security
- bcrypt 4.1.2→5.0.0（Dependabot PR#3219）
- alembic 1.13.1→1.18.4（Dependabot PR#3218）
- prometheus-client 0.19.0→0.24.1（Dependabot PR#3215）
- faker 20.1.0→40.8.0（Dependabot PR#3217）

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
