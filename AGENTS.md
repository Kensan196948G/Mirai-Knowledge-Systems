# AGENTS.md — Mirai Knowledge Systems 設計決定・修復履歴

最終更新: 2026-03-17

---

## 📋 プロジェクト概要

- **プロジェクト名**: Mirai Knowledge Systems
- **バージョン**: v1.8.0
- **フレームワーク**: Flask 3.1.2 + PostgreSQL + Vanilla JS
- **現在のフェーズ**: Phase I-2 完了（テストカバレッジ80%+達成）

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

**目標**: 60% ✅（要件達成）、現在 81.11% ✅

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
