# AGENTS.md — Mirai Knowledge Systems 設計決定・修復履歴

最終更新: 2026-03-17（PR #3255）

---

## 📋 プロジェクト概要

- **プロジェクト名**: Mirai Knowledge Systems
- **バージョン**: v1.9.0
- **フレームワーク**: Flask 3.1.3 + PostgreSQL + Vanilla JS
- **現在のフェーズ**: Phase G-3-4 / I-3 / I-4 / Phase L 完了（2026-03-17）

---

## 🏗 アーキテクチャ決定

### Blueprint 移行（Phase H）

**決定**: app_v2.py のモノリシック構造を Blueprint に分割

- `blueprints/auth.py` (1025行): 認証・MFA エンドポイント
- `blueprints/knowledge.py` (867行): ナレッジ管理エンドポイント
- `blueprints/health.py`: ヘルスチェック
- `blueprints/ms365.py`: MS365同期
- `blueprints/recommendations.py`: 推薦エンジン
- `blueprints/admin.py`: 管理者機能
- `blueprints/dashboard.py`: ダッシュボード
- `app_v2.py`: 1572行（Blueprint登録のみに縮小）

**理由**: 可読性・テスト容易性・並列開発の向上

### DAL 層導入（Phase I）

**決定**: dal/ ディレクトリにデータアクセス層を集約

- `dal/json_mode.py`: JSON ファイルバックエンド（開発環境）
- `dal/postgresql_mode.py`: PostgreSQL バックエンド（本番環境）
- `dal/knowledge.py`, `dal/experts.py` 等: エンティティ別 DAL

**理由**: JSON/PostgreSQL 両モード対応の一元管理

---

## 🧪 テストカバレッジ履歴

| フェーズ | カバレッジ | テスト数 | 日付 |
|---------|-----------|---------|------|
| Phase G-2 完了 | 75% | ~750 | 2026-03-03 |
| Phase J-3 完了 | 77.28% | 849 | 2026-03-10 |
| Phase K 完了 | 76% → 78% | 900+ | 2026-03-10 |
| Phase K-2 完了 | 77.28% | 849 | 2026-03-10 |
| Phase I-2 完了 | **81.11%** | **1151** | 2026-03-16 |
| Phase I-5 + L 完了 | **87.76%** | **1681** | 2026-03-17 |
| Phase Prometheus 完了 | **87.26%** | **1708** | 2026-03-17 |

**目標**: 60% ✅（要件達成）、現在 87.26% ✅

---

## 🔧 2026-03-17 実装記録

### Dependabot PR 全7件マージ
- jest 30.3.0, chardet 7.1.0, jest-environment-jsdom 30.3.0, **flask 3.1.3**（セキュリティ）
- python-docx 1.2.0, qrcode 8.2, redis 7.3.0

### Phase G-3-4: Blueprint最終クリーンアップ
- `app_v2.py`: 重複Redis/Cache設定除去（app_helpers.pyに一元化）
- `app_v2.py`: 重複`get_data_dir()`関数定義除去
- `blueprints/auth.py`, `knowledge.py`: `strict_slashes=False`（Flask 3.1.x互換方式に修正）

### Phase I-3: Blueprint ルーティング最適化
- auth_bp / knowledge_bp に `strict_slashes=False` 設定（末尾スラッシュ柔軟対応）
- Blueprint登録順コメント整備（高頻度→低頻度）

### Phase I-4: DB接続プール最適化
- `config.py`: SQLALCHEMY_POOL_SIZE 10→**20**
- `config.py`: SQLALCHEMY_MAX_OVERFLOW 20→**10**
- `config.py`: SQLALCHEMY_POOL_RECYCLE 3600→**1800**

### Phase L: テストカバレッジ強化（Issue #3233）
- `test_error_handlers.py`: 9→38テスト、coverage 78%→**100%**
- `test_socketio_handlers.py`: 5→24テスト、coverage 58%→**100%**

### Phase I-5: フロントエンド最適化（PR #3253）
- `vite.config.js`: vendor-viteサブチャンク追加、ES2015ターゲット、CSS分割有効化
- `webui/sw.js`: Service Worker バージョンを日付ベースに更新（`v2026-03-17`）
- `webui/src/utils/debounce.js`: `debounce()` / `batchDebounce()` ユーティリティ追加

### Phase Prometheus: メトリクス定義モジュール分離（PR #3255）
- `blueprints/metrics_defs.py` 新規作成（14メトリクス定義 + _NoOpMetric）
- `app_v2.py`: ~130行のPrometheus定義をimportに変更（循環import解消）
- `test_dal_base_coverage.py`: 27テスト追加、dal/base.py **100%** 達成
- `.github/workflows/lighthouse-ci.yml`: Lighthouse CI 自動化追加
- `CHANGELOG.md`: v1.9.0 エントリ追加

---

## 🔧 CI 修復履歴

| 日付 | 問題 | 修復内容 |
|------|------|---------|
| 2026-03-10 | requirements.txt 依存競合 | requirements-test.txt 新設 |
| 2026-03-10 | pytest-playwright バージョン制約 | 0.4.4→0.7.2 に更新 |
| 2026-03-10 | jsdom 26 location mock エラー | jest-location-env.js でパッチ |
| 2026-03-10 | MS365テスト 空リスト判定 | assert isinstance に修正 |
| 2026-03-16 | dal/knowledge.py 循環インポート | 遅延インポートに修正 |

---

## 📂 主要ファイル

| ファイル | 説明 |
|---------|------|
| `backend/app_v2.py` | メインアプリ (1572行) |
| `backend/app_helpers.py` | CSRF・パスワードポリシー統合 |
| `backend/blueprints/auth.py` | 認証BP (1025行) |
| `backend/blueprints/knowledge.py` | ナレッジBP (867行) |
| `backend/dal/` | DAL層（JSON/PostgreSQL両対応）|
| `backend/pytest.ini` | pytest設定（cov: blueprints, dal, app_v2...）|
| `backend/.coveragerc` | カバレッジ設定（scripts/, migrations/ 除外）|
| `.github/workflows/ci.yml` | CI設定 |
| `webui/src/` | ESMモジュール群 (33ファイル 14,508行) |

---

## 🚀 次フェーズ候補

| 候補 | 内容 | 優先度 |
|------|------|--------|
| Phase G-3-4 | Blueprint実移行（auth 13ep + knowledge 12ep） | 高 |
| Phase I-3+ | パフォーマンス最適化（N+1対策） | 中 |
| Phase L | フロントエンドモジュール最終統合 | 中 |

---

## 🔐 セキュリティ決定

- JWT Secret Key: 環境変数 `MKS_JWT_SECRET_KEY`（起動時必須チェック）
- CSRF保護: `app_helpers.py` に統合
- パスワードポリシー: `app_helpers.py` に統合
- MFA: TOTP（RFC 6238） + バックアップコード（bcrypt）
- Rate limiting: MFA 5回/15分、本番環境のみ有効
