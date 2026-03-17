# CHANGELOG

## [1.9.0] - 2026-03-17

### Added
- **Phase Prometheus**: `blueprints/metrics_defs.py` 新規作成（app_v2.py から ~130行のPrometheusメトリクス定義を分離）
  - `REQUEST_COUNT`, `REQUEST_DURATION`, `ERROR_COUNT`, `API_CALLS` 等14メトリクスを共有モジュール化
  - テスト環境用 `_NoOpMetric` クラスを同モジュールに統合
- **Lighthouse CI**: `.github/workflows/lighthouse-ci.yml` 新規追加
  - フロントエンド変更時に自動でパフォーマンス/アクセシビリティ/SEO 計測
  - `.lighthouserc.json` 閾値設定（Performance≥80, Accessibility≥90, SEO≥90）
- **Phase I-5 フロントエンド最適化**:
  - `vite.config.js`: vendor-vite サブチャンク分割、ES2015ターゲット、CSS分割有効化
  - `webui/sw.js`: Service Worker バージョンを `v2026-03-17`（日付ベース）に更新
  - `webui/src/utils/debounce.js`: `debounce()` / `batchDebounce()` ユーティリティ追加
- **Phase I-4 DB接続プール最適化**:
  - `config.py`: pool_size 10→20、max_overflow 20→10、recycle 3600→1800、pre_ping 有効
- **Phase I-3 Blueprint ルーティング最適化**:
  - `auth_bp` / `knowledge_bp`: `strict_slashes = False`（Flask 3.1.x 互換修正）
- **Phase G-3-4 Blueprint実移行**:
  - `blueprints/ms365_integration.py` 新規作成（672行）: ms365_integration_bp 分離
  - `blueprints/ms365.py`: 1143行→484行（ms365_bp のみに縮小）
- **Phase L テストカバレッジ強化**:
  - `test_error_handlers.py`: 9→38テスト、coverage 100%
  - `test_socketio_handlers.py`: 5→24テスト、coverage 100%
  - `test_dal_base_coverage.py`: 新規作成 27テスト、dal/base.py 100% 達成
  - `test_dal_notifications_operations_coverage.py`: 58テスト追加
  - notifications 100%、operations 100%、projects 100%
- **ベンチマーク基盤**: `backend/scripts/benchmark.py` 新規作成（JWT認証対応HTTPベンチマーク）
- **CI最適化** (Issue #3235):
  - `auto-error-fix-continuous.yml`: Playwright/Docker削除、unit testsのみ実行、concurrency設定

### Changed
- `app_v2.py`: Prometheusメトリクス定義を `blueprints/metrics_defs.py` からimportに変更
- テストカバレッジ: **81.11%** → **87.76%** （テスト数: 1,151 → 1,681 +530件）
- CI実行時間最適化（Playwright依存削除による高速化）

### Fixed
- Flask 3.1.x 非互換: `Blueprint(strict_slashes=False)` → `bp.strict_slashes = False`
- `app_v2.py`: 重複 `get_data_dir()` 関数定義除去
- `app_v2.py`: 重複 Redis/Cache 設定ブロック除去
- `dal/knowledge.py`: 循環インポートを遅延インポートに修正

### Security
- `flask` 3.0.0→**3.1.3**（Dependabot PR #3242 — セキュリティ修正含む）
- `jest` 29.7.0→**30.3.0**（Dependabot）
- `jest-environment-jsdom` 29.7.0→**30.3.0**（Dependabot）
- `python-docx` 1.1.0→**1.2.0**（Dependabot）
- `qrcode` 7.4.2→**8.2**（Dependabot）
- `redis` 4.5.5→**7.3.0**（Dependabot）
- `chardet` 5.2.0→**7.1.0**（Dependabot）

## [1.8.0] - 2026-03-10

### Added
- **Phase I 基盤**: パフォーマンス最適化ロードマップ策定
  - `app_helpers.py`: CACHE_TTL機能別定数（SHORT/DEFAULT/LONG/VERY_LONG）
  - `docs/PHASE_I_PERFORMANCE_ROADMAP.md`: 82→150+ req/sec 目標設定
- **DAL N+1最適化**: dal/knowledge.py・dal/experts.py にキャッシュ層追加

### Fixed
- dal/knowledge.py・dal/experts.py: 循環インポートを遅延インポートに修正
- CI Pipeline: `data_access→dal→app_helpers→data_access` 循環チェーン解消
- `.gitignore`: `backend/data/*.json` 除外（テスト副作用防止）

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
- **MS365ファイルプレビューPWA統合**（Phase 3）
  - Service Worker キャッシュ戦略実装（networkFirstMS365Preview）

### Changed
- `backend/requirements.txt`: psutil 5.9.6→7.2.2、test依存分離
- `.github/workflows/pr-quality-gate.yml`: Backend Testsタイムアウト30分化・並列実行（-n auto）
- `.github/copilot-instructions.md`: Version 1.4.0→1.6.0更新

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
