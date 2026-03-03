# Phase G-3: APIゲートウェイ / Backend最適化 - 機能要件書

**バージョン**: 1.0.0
**作成日**: 2026-03-03
**作成者**: spec-planner SubAgent

---

## 1. 概要

### 1.1 目的

- `backend/app_v2.py`（7,112行）をFlask Blueprint構成に分割し、保守性・テスト性を向上させる
- N+1クエリ完全解消（joinedload/subqueryload/selectinload 適用）
- Redisキャッシュ戦略の体系化・拡張（検索・統計・関連データAPI）
- APIバージョニング（`/api/v2/`）への移行準備

### 1.2 現状分析（調査結果）

#### ファイル構成

| 項目 | 値 |
|------|-----|
| ファイル | `backend/app_v2.py` |
| 行数 | 7,112行 |
| Blueprint使用 | **なし**（全ルートが `@app.route` で直接定義） |
| Redisキャッシュ | **一部実装済み**（`cache_get` / `cache_set` 関数あり、CACHE_ENABLED フラグで制御） |
| ORM | SQLAlchemy 2.0（`data_access.py` 経由で selectinload 適用済み） |
| SocketIO | `flask_socketio` によるリアルタイム更新ハンドラー含む |

#### エンドポイントカテゴリ分類

| カテゴリ | パスプレフィックス | エンドポイント数 |
|----------|------------------|---------------|
| auth | `/api/v1/auth/` | 12 |
| ms365 | `/api/v1/integrations/microsoft365/` | 21 |
| knowledge | `/api/v1/knowledge/`, `/api/v1/regulations/`, `/api/v1/projects/`, `/api/v1/experts/`, `/api/v1/favorites/` | 17 |
| search | `/api/v1/search/` | 1 |
| notifications | `/api/v1/notifications/` | 3 |
| sop | `/api/v1/sop/` | 3 |
| incidents | `/api/v1/incidents/` | 2 |
| dashboard | `/api/v1/dashboard/` | 1 |
| approvals | `/api/v1/approvals/` | 3 |
| recommendations | `/api/v1/recommendations/` | 3 |
| consultations | `/api/v1/consultations/` | 5 |
| system | `/api/v1/health/`, `/api/v1/logs/`, `/api/v1/metrics`, `/api/metrics/`, `/metrics` | 8 |
| docs | `/api/docs`, `/api/openapi.yaml` | 2 |
| static | `/`, `/index.html`, `/<path:path>` | 3 |
| **合計** | | **84** |

#### 既存キャッシュ実装状況

現在 `app_v2.py` には Redis キャッシュが部分的に実装済みである。`CacheInvalidator` クラスも存在し、カテゴリ別の無効化ロジックが定義されている。

| キャッシュキープレフィックス | 対象エンドポイント | TTL |
|----------------------------|-----------------|----|
| `knowledge_list:*` | GET /knowledge | 3600秒（1時間） |
| `knowledge_popular:*` | GET /knowledge/popular | キャッシュあり |
| `knowledge_tags` | GET /knowledge/tags | キャッシュあり |
| `knowledge_recent:*` | GET /knowledge/recent | キャッシュあり |
| `knowledge_related:*` | GET /knowledge/{id}/related | キャッシュあり |
| `regulations_detail:*` | GET /regulations/{id} | 86400秒（24時間） |
| `projects_list:*` | GET /projects | 3600秒 |
| `projects_detail:*` | GET /projects/{id} | キャッシュあり |
| `projects_progress:*` | GET /projects/{id}/progress | キャッシュあり |
| `experts_list:*` | GET /experts | キャッシュあり |
| `experts_detail:*` | GET /experts/{id} | キャッシュあり |
| `experts_stats` | GET /experts/stats | キャッシュあり |
| `sop_list` | GET /sop | 3600秒 |
| `sop_related:*` | GET /sop/{id}/related | キャッシュあり |
| `dashboard_stats` | GET /dashboard/stats | 300秒（5分） |
| `search:*` | GET /search/unified | 3600秒 |

#### 既存N+1対応状況（data_access.py）

`data_access.py` では `selectinload` を用いた N+1 最適化が Knowledge, SOP に対して **部分的に実装済み**。しかし `app_v2.py` の一部エンドポイントでは `load_data()` によるJSONファイル直接読み込みを使用しており、PostgreSQL移行時にN+1が再発するリスクがある。

---

## 2. Blueprint分割設計

### 2.1 分割方針

- `backend/blueprints/` ディレクトリを新設
- `app_v2.py` の `@app.route` デコレータを各Blueprintの `@bp.route` に移植
- グローバル変数・ヘルパー関数は `backend/utils/` または `app_v2.py` の共通領域に分離
- SocketIOハンドラーは `backend/sockets/` に分離

### 2.2 Blueprint一覧

| Blueprint | ファイル | 担当エンドポイント | エンドポイント数 | 優先度 |
|-----------|---------|-----------------|---------------|--------|
| AuthAPI | `backend/blueprints/auth.py` | `/api/v1/auth/*` | 12 | High |
| KnowledgeAPI | `backend/blueprints/knowledge.py` | `/api/v1/knowledge/*`, `/api/v1/regulations/*`, `/api/v1/favorites/*` | 12 | High |
| ProjectAPI | `backend/blueprints/project.py` | `/api/v1/projects/*`, `/api/v1/experts/*` | 5 | High |
| SOPAPI | `backend/blueprints/sop.py` | `/api/v1/sop/*` | 3 | High |
| IncidentAPI | `backend/blueprints/incident.py` | `/api/v1/incidents/*` | 2 | High |
| ConsultationAPI | `backend/blueprints/consultation.py` | `/api/v1/consultations/*` | 5 | Medium |
| SearchAPI | `backend/blueprints/search.py` | `/api/v1/search/*` | 1 | High |
| NotificationAPI | `backend/blueprints/notification.py` | `/api/v1/notifications/*` | 3 | Medium |
| DashboardAPI | `backend/blueprints/dashboard.py` | `/api/v1/dashboard/*`, `/api/v1/approvals/*`, `/api/v1/recommendations/*` | 7 | Medium |
| MS365API | `backend/blueprints/ms365.py` | `/api/v1/integrations/microsoft365/*` | 21 | Low |
| SystemAPI | `backend/blueprints/system.py` | `/api/v1/health/*`, `/api/v1/logs/*`, `/metrics`, `/api/metrics/*`, `/api/v1/metrics`, `/api/docs`, `/api/openapi.yaml` | 10 | Medium |

### 2.3 ディレクトリ構造

```
backend/
├── app_v2.py                  # アプリ初期化・設定のみ残す（ルート登録を除く）
├── blueprints/                # 新設ディレクトリ
│   ├── __init__.py
│   ├── auth.py                # 認証・MFA
│   ├── knowledge.py           # ナレッジ・法令・お気に入り
│   ├── project.py             # プロジェクト・エキスパート
│   ├── sop.py                 # SOP
│   ├── incident.py            # インシデント
│   ├── consultation.py        # 専門家相談
│   ├── search.py              # 横断検索
│   ├── notification.py        # 通知
│   ├── dashboard.py           # ダッシュボード・承認・推薦
│   ├── ms365.py               # MS365連携
│   └── system.py              # ヘルス・メトリクス・ドキュメント
├── sockets/                   # SocketIOハンドラー（新設）
│   ├── __init__.py
│   └── handlers.py            # connect/disconnect/join_project等
└── utils/                     # 共通ユーティリティ（新設）
    ├── __init__.py
    ├── cache.py               # cache_get/cache_set/CacheInvalidator
    ├── auth_helpers.py        # check_permission/validate_request
    └── access_log.py          # log_access/_flush_access_logs
```

### 2.4 Blueprint登録方法（app_v2.py）

```python
# app_v2.py（Blueprint登録部分のみ）
from blueprints.auth import auth_bp
from blueprints.knowledge import knowledge_bp
from blueprints.project import project_bp
from blueprints.sop import sop_bp
from blueprints.incident import incident_bp
from blueprints.consultation import consultation_bp
from blueprints.search import search_bp
from blueprints.notification import notification_bp
from blueprints.dashboard import dashboard_bp
from blueprints.ms365 import ms365_bp
from blueprints.system import system_bp

app.register_blueprint(auth_bp)
app.register_blueprint(knowledge_bp)
app.register_blueprint(project_bp)
app.register_blueprint(sop_bp)
app.register_blueprint(incident_bp)
app.register_blueprint(consultation_bp)
app.register_blueprint(search_bp)
app.register_blueprint(notification_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(ms365_bp)
app.register_blueprint(system_bp)
```

---

## 3. N+1クエリ最適化対象

### 3.1 現状の問題点

`app_v2.py` 内の多くのエンドポイントは `load_data()` 関数でJSONファイルから直接読み込みを行っている。PostgreSQL環境（`MKS_USE_POSTGRESQL=true`）では `data_access.py` 経由になるが、以下の箇所では PostgreSQL移行後にN+1が発生するリスクがある。

### 3.2 最適化対象エンドポイント

| エンドポイント | 問題箇所 | 現状 | 修正方法 |
|--------------|---------|------|---------|
| `GET /api/v1/knowledge` | `Knowledge.created_by`, `Knowledge.updated_by` の各行取得 | `selectinload` 済み（data_access.py） | 維持・Blueprint移行時に確認 |
| `GET /api/v1/knowledge/<id>` | 同上 | `selectinload` 済み | 維持 |
| `GET /api/v1/knowledge/<id>/related` | タグ一致ナレッジのリレーション取得 | `selectinload` 済み | 維持 |
| `GET /api/v1/consultations` | `requester`, `expert`, `knowledge` の各行取得 | JSON直接読み込み（PostgreSQL時リスク） | `joinedload(Consultation.requester)`, `joinedload(Consultation.expert)` |
| `GET /api/v1/consultations/<id>` | 同上 | JSON直接読み込み | `joinedload` 適用 |
| `GET /api/v1/approvals` | `requester`, `approver` の各行取得 | JSON直接読み込み | `joinedload(Approval.requester)`, `joinedload(Approval.approver)` |
| `GET /api/v1/notifications` | `NotificationRead` の各通知取得 | JSON直接読み込み | `subqueryload(Notification.reads)` |
| `GET /api/v1/projects/<id>/progress` | `ProjectTask` 一覧取得後の `assigned_to` | JSON直接読み込み | `joinedload(ProjectTask.assigned_to)` |
| `GET /api/v1/experts/stats` | 全エキスパートの評価スコア取得 | JSON直接読み込み | `subqueryload(Expert.ratings)` または集計クエリ |
| `GET /api/v1/incidents` | `reporter` の各行取得 | JSON直接読み込み | `joinedload(Incident.reporter)` |
| `GET /api/v1/dashboard/stats` | 複数コレクション個別ロード | 4回のJSONロード | 集計SQLクエリへの統合 |

### 3.3 check_permissionデコレータのN+1問題

**重要**: 現在 `check_permission` デコレータは **リクエストごとに `load_users()` を呼び出し**、ユーザーリスト全件をスキャンしている。PostgreSQL環境では `users` テーブルへのクエリが毎リクエスト発行されるため、キャッシュまたはJWT claims内にロール情報を含める改修が必要。

| 問題 | 発生頻度 | 影響 | 対策 |
|------|--------|------|------|
| `check_permission` 内での `load_users()` 全件スキャン | 全保護エンドポイント（約60個） | 高 | JWTに `roles` claim を追加し、DB参照を排除 |

---

## 4. キャッシュ戦略

### 4.1 現状キャッシュ実装

`app_v2.py` には以下のRedisキャッシュ基盤がすでに実装されている：

- `cache_get(key)` / `cache_set(key, value, ttl)` 関数
- `CacheInvalidator` クラス（knowledge, sop, projects, experts, regulations の無効化メソッド）
- `CACHE_ENABLED` フラグ（Redis接続失敗時は自動無効化）
- デフォルトTTL: 300秒（環境変数 `CACHE_TTL` で変更可能）

### 4.2 キャッシュ適用一覧

| API | キャッシュキー | TTL | 実装状態 | Phase G-3での作業 |
|-----|-------------|-----|--------|----------------|
| GET /api/v1/knowledge | `knowledge_list:{params}` | 3600秒 | 実装済み | Blueprint移行時に維持 |
| GET /api/v1/knowledge/popular | `knowledge_popular:{params}` | 3600秒 | 実装済み | 維持 |
| GET /api/v1/knowledge/recent | `knowledge_recent:{params}` | 3600秒 | 実装済み | 維持 |
| GET /api/v1/knowledge/tags | `knowledge_tags` | 3600秒 | 実装済み | 維持 |
| GET /api/v1/knowledge/{id}/related | `knowledge_related:{id}:{params}` | 3600秒 | 実装済み | 維持 |
| GET /api/v1/regulations/{id} | `regulations_detail:{id}` | 86400秒 | 実装済み | 維持 |
| GET /api/v1/projects | `projects_list:{params}` | 3600秒 | 実装済み | 維持 |
| GET /api/v1/projects/{id} | `projects_detail:{id}` | 3600秒 | 実装済み | 維持 |
| GET /api/v1/projects/{id}/progress | `projects_progress:{id}` | 300秒 | 実装済み | 維持 |
| GET /api/v1/experts | `experts_list:{params}` | 3600秒 | 実装済み | 維持 |
| GET /api/v1/experts/{id} | `experts_detail:{id}` | 3600秒 | 実装済み | 維持 |
| GET /api/v1/experts/stats | `experts_stats` | 3600秒 | 実装済み | 維持 |
| GET /api/v1/sop | `sop_list` | 3600秒 | 実装済み | 維持 |
| GET /api/v1/sop/{id}/related | `sop_related:{id}:{params}` | 3600秒 | 実装済み | 維持 |
| GET /api/v1/dashboard/stats | `dashboard_stats` | 300秒 | 実装済み | 維持 |
| GET /api/v1/search/unified | `search:{params}` | 3600秒 | 実装済み | 維持 |
| GET /api/v1/consultations | `consultations_list:{params}` | 300秒 | **未実装** | Phase G-3-2 で実装 |
| GET /api/v1/incidents | `incidents_list:{params}` | 300秒 | **未実装** | Phase G-3-2 で実装 |

### 4.3 キャッシュ無効化戦略

| データ操作 | 無効化対象キャッシュ | 実装状態 |
|----------|----------------|--------|
| POST /knowledge（新規作成） | `knowledge_list:*`, `knowledge_popular:*`, `knowledge_tags`, `knowledge_recent:*` | CacheInvalidator.invalidate_knowledge() 実装済み |
| PUT /knowledge/{id}（更新） | 同上 + `knowledge_related:{id}:*` | 実装済み |
| DELETE /knowledge/{id}（削除） | 同上 | 実装済み |
| POST /consultations（新規） | `consultations_list:*` | **未実装** |
| POST /approvals/{id}/approve | `dashboard_stats` | **未実装** |

---

## 5. 実装計画（フェーズ分け）

### Phase G-3-1: Blueprint分割（最優先）

**目的**: 7,112行の単一ファイルを11個のBlueprintに分割し、可読性・保守性を向上させる

**対象**: auth, knowledge, project, sop, incident, search Blueprint（優先度High）

**作業内容**:
1. `backend/blueprints/__init__.py` 作成
2. 共通ユーティリティの抽出: `utils/cache.py`, `utils/auth_helpers.py`, `utils/access_log.py`
3. 各Blueprintファイルの作成と `@app.route` → `@bp.route` 移植
4. `app_v2.py` をBlueprint登録・初期化専用に簡素化
5. SocketIOハンドラーを `sockets/handlers.py` に分離

**期間**: 2-3日
**リスク**: 低（既存テストで動作確認可能）
**後方互換性**: URLパスは変更しない

**成功基準**:
- `app_v2.py` が 1,500行以下になること
- 既存テスト（591件）が全て PASS であること

---

### Phase G-3-2: N+1クエリ最適化

**目的**: PostgreSQL環境でのクエリ数削減（特に `check_permission` のN+1解消）

**作業内容**:
1. JWTトークンに `roles` claim を追加（ログイン時に設定）
2. `check_permission` デコレータを JWT claims からロールを読むよう改修（DB参照排除）
3. `consultations` / `approvals` / `notifications` の `data_access.py` メソッドに `joinedload` 追加
4. `dashboard/stats` の複数JSONロードを単一集計クエリに統合

**期間**: 1-2日
**リスク**: 中（JWT形式変更により既存トークンが無効化される。ユーザーの再ログインが必要）

**成功基準**:
- `check_permission` がDBクエリ0回で実行できること
- PostgreSQL環境でのレスポンスタイムが20%以上改善されること

---

### Phase G-3-3: キャッシュ拡張（オプション）

**目的**: `consultations`, `incidents` へのキャッシュ適用と無効化ロジック追加

**作業内容**:
1. `CacheInvalidator.invalidate_consultations()` メソッド追加
2. `CacheInvalidator.invalidate_incidents()` メソッド追加（将来のインシデント更新API向け）
3. `GET /consultations` / `GET /incidents` にキャッシュ実装（TTL 300秒）
4. `POST /consultations` / `PUT /consultations/{id}` での `invalidate_consultations()` 呼び出し

**期間**: 1日
**リスク**: 低

---

### Phase G-3-4: APIバージョニング準備（将来フェーズ）

**目的**: `/api/v2/` への移行準備

**設計方針**:
- Blueprint の `url_prefix` を `/api/v1` から `/api/v2` に変更可能な構成にする
- `app.register_blueprint(knowledge_bp, url_prefix="/api/v2")` の形式で多バージョン共存可能とする
- Phase G-3-1 完了後に実施

**期間**: 0.5日
**リスク**: 低

---

## 6. 後方互換性

| 変更内容 | 影響 | 対策 |
|---------|------|------|
| Blueprint分割 | URLパス変更なし | `url_prefix` を `/api/v1` に維持 |
| APIレスポンス形式 | 変更なし | 既存スキーマを維持 |
| JWT形式変更（N+1対策） | 既存トークンが無効化 | ドキュメントに記載、再ログイン案内 |
| キャッシュキー変更 | 旧キャッシュが無効化（自動期限切れ） | デプロイ時にキャッシュフラッシュ推奨 |
| SocketIOイベント名 | 変更なし | `sockets/handlers.py` に移動するだけ |

---

## 7. テスト計画

### 7.1 既存テスト流用

| テストスイート | 件数 | Blueprint移行後の確認事項 |
|-------------|------|----------------------|
| `tests/unit/test_totp_manager.py` | 19件 | auth Blueprint独立後も動作確認 |
| `tests/unit/test_ms365_sync_service.py` | 16件 | ms365 Blueprint独立後も動作確認 |
| `tests/integration/test_mfa_flow.py` | 17件 | auth Blueprint統合テスト |
| `tests/integration/test_ms365_sync_api.py` | 18件 | ms365 Blueprint統合テスト |

### 7.2 新規テスト追加

| テストファイル | 目的 | 優先度 |
|-------------|------|-------|
| `tests/unit/test_blueprints_register.py` | 全Blueprint登録確認・URLルーティング確認 | High |
| `tests/unit/test_cache_invalidation.py` | CacheInvalidator各メソッドの動作確認 | Medium |
| `tests/integration/test_knowledge_blueprint.py` | knowledge Blueprint エンドポイント統合テスト | High |
| `tests/integration/test_consultation_blueprint.py` | consultation Blueprint エンドポイント統合テスト | Medium |

### 7.3 カバレッジ目標

- **既存カバレッジ**: 91%
- **Phase G-3完了後目標**: 91%以上維持
- テスト件数: 591件 → 620件以上（新規テスト追加）

---

## 8. リスク評価

| リスク | 確率 | 影響 | 対策 |
|--------|------|------|------|
| Blueprint登録漏れ（エンドポイント欠落） | 低 | 高 | 84エンドポイントのチェックリスト作成、統合テストで全URL確認 |
| import循環参照 | 中 | 中 | `utils/` モジュールは他Blueprintをimportしない、`app_v2.py` の `app` インスタンスは `current_app` で参照 |
| JWTデコレータの動作変更 | 低 | 高 | Blueprint内でも `@jwt_required()` がそのまま動作することを確認（Flask-JWT-Extendedはapp-levelで設定済み） |
| SocketIO + Blueprint の相性 | 中 | 中 | SocketIOハンドラーは Blueprint外に分離（`sockets/handlers.py`）し、`socketio` インスタンスを `current_app.extensions` 経由で参照 |
| グローバル変数（`_dal`, `redis_client` 等）のスコープ変更 | 中 | 中 | `get_dal()` / `cache_get()` 等の関数インターフェースを維持し、Blueprint内は関数経由でアクセス |
| Limiter（Flask-Limiter）のBlueprint対応 | 低 | 中 | `@limiter.limit()` デコレータはBlueprint内でも動作確認済み（Flask-Limiter対応）。`limiter` インスタンスを `current_app` extensions経由で取得 |
| テスト環境のimportパス変更 | 中 | 低 | `conftest.py` のimportパスを更新 |
| セッション管理の変更 | 低 | 高 | JWT認証はステートレスのためセッションへの影響なし |

---

## 9. arch-reviewer確認事項

- [ ] Blueprint構成がFlask推奨パターン（Application Factory パターン）に沿っているか
- [ ] `models.py` のimport循環参照リスクはないか（Blueprint → models → Blueprint の循環がないか）
- [ ] テスト構造への影響は最小限か（既存テストのimportパス変更が必要な箇所の特定）
- [ ] 既存のJWT認証デコレータ（`@jwt_required()`, `@check_permission()`）は各Blueprintで正しく動作するか
- [ ] `flask_socketio` の SocketIO イベントハンドラーをBlueprintから分離する設計は適切か
- [ ] `CacheInvalidator` クラスを `utils/cache.py` に分離する際、`redis_client` のスコープは問題ないか
- [ ] Phase G-3-2 の JWT claim 拡張は既存の `mfa_token` フローと競合しないか
- [ ] `limiter` インスタンスの Blueprint内参照方法として `current_app.extensions['flask-limiter']` は適切か
- [ ] `app_v2.py` に残す「アプリ初期化・設定部分」と「Blueprint」の責務境界線は適切か
- [ ] N+1最適化のための `joinedload` 追加は既存の `data_access.py` パターンと一致しているか

---

## 付録A: エンドポイント完全一覧

### auth Blueprint（12エンドポイント）

| メソッド | パス | 関数名 | 優先度 |
|--------|------|-------|-------|
| POST | /api/v1/auth/login | login | High |
| POST | /api/v1/auth/login/mfa | login_mfa | High |
| POST | /api/v1/auth/refresh | refresh | High |
| POST | /api/v1/auth/logout | logout | High |
| GET | /api/v1/auth/me | get_current_user | High |
| POST | /api/v1/auth/mfa/setup | setup_mfa | High |
| POST | /api/v1/auth/mfa/enable | enable_mfa | High |
| POST | /api/v1/auth/mfa/verify | verify_mfa_login | High |
| POST | /api/v1/auth/mfa/validate | verify_mfa_login（エイリアス） | High |
| POST | /api/v1/auth/mfa/disable | disable_mfa | High |
| POST | /api/v1/auth/mfa/backup-codes/regenerate | regenerate_backup_codes | High |
| GET | /api/v1/auth/mfa/status | mfa_status | High |
| POST | /api/v1/auth/mfa/recovery | mfa_recovery | High |

### knowledge Blueprint（12エンドポイント）

| メソッド | パス | 関数名 |
|--------|------|-------|
| GET | /api/v1/knowledge | get_knowledge |
| POST | /api/v1/knowledge | create_knowledge |
| GET | /api/v1/knowledge/{id} | get_knowledge_detail |
| PUT | /api/v1/knowledge/{id} | update_knowledge |
| DELETE | /api/v1/knowledge/{id} | delete_knowledge |
| GET | /api/v1/knowledge/{id}/related | get_related_knowledge |
| GET | /api/v1/knowledge/popular | get_popular_knowledge |
| GET | /api/v1/knowledge/recent | get_recent_knowledge |
| GET | /api/v1/knowledge/favorites | get_favorite_knowledge |
| GET | /api/v1/knowledge/tags | get_knowledge_tags |
| DELETE | /api/v1/favorites/{id} | remove_favorite |
| GET | /api/v1/regulations/{id} | get_regulation_detail |

### project Blueprint（5エンドポイント）

| メソッド | パス | 関数名 |
|--------|------|-------|
| GET | /api/v1/projects | get_projects |
| GET | /api/v1/projects/{id} | get_project_detail |
| GET | /api/v1/projects/{id}/progress | get_project_progress |
| GET | /api/v1/experts | get_experts |
| GET | /api/v1/experts/{id} | get_expert_detail |
| GET | /api/v1/experts/stats | get_experts_stats |
| GET | /api/v1/experts/{id}/rating | calculate_expert_rating |

### sop Blueprint（3エンドポイント）

| メソッド | パス | 関数名 |
|--------|------|-------|
| GET | /api/v1/sop | get_sop |
| GET | /api/v1/sop/{id} | get_sop_detail |
| GET | /api/v1/sop/{id}/related | get_related_sop |

### incident Blueprint（2エンドポイント）

| メソッド | パス | 関数名 |
|--------|------|-------|
| GET | /api/v1/incidents | get_incidents |
| GET | /api/v1/incidents/{id} | get_incident_detail |

### ms365 Blueprint（21エンドポイント）

| メソッド | パス | 関数名 |
|--------|------|-------|
| GET | /api/v1/integrations/microsoft365/status | ms365_status |
| GET | /api/v1/integrations/microsoft365/sites | ms365_sites |
| GET | /api/v1/integrations/microsoft365/sites/{site_id}/drives | ms365_site_drives |
| GET | /api/v1/integrations/microsoft365/drives/{drive_id}/items | ms365_drive_items |
| POST | /api/v1/integrations/microsoft365/import | ms365_import |
| POST | /api/v1/integrations/microsoft365/sync | ms365_sync |
| GET | /api/v1/integrations/microsoft365/teams | ms365_teams |
| GET | /api/v1/integrations/microsoft365/teams/{team_id}/channels | ms365_team_channels |
| GET | /api/v1/integrations/microsoft365/sync/configs | ms365_sync_configs_list |
| POST | /api/v1/integrations/microsoft365/sync/configs | ms365_sync_configs_create |
| GET | /api/v1/integrations/microsoft365/sync/configs/{id} | ms365_sync_configs_get |
| PUT | /api/v1/integrations/microsoft365/sync/configs/{id} | ms365_sync_configs_update |
| DELETE | /api/v1/integrations/microsoft365/sync/configs/{id} | ms365_sync_configs_delete |
| POST | /api/v1/integrations/microsoft365/sync/configs/{id}/execute | ms365_sync_configs_execute |
| POST | /api/v1/integrations/microsoft365/sync/configs/{id}/test | ms365_sync_configs_test |
| GET | /api/v1/integrations/microsoft365/sync/configs/{id}/history | ms365_sync_configs_history |
| GET | /api/v1/integrations/microsoft365/sync/stats | ms365_sync_stats |
| GET | /api/v1/integrations/microsoft365/sync/status | ms365_sync_status |
| GET | /api/v1/integrations/microsoft365/files/{file_id}/preview | ms365_file_preview |
| GET | /api/v1/integrations/microsoft365/files/{file_id}/download | ms365_file_download |
| GET | /api/v1/integrations/microsoft365/files/{file_id}/thumbnail | ms365_file_thumbnail |

---

## 付録B: 注意事項・制約

### B.1 WindowsパスとBackslashの問題

`app_v2.py` の MS365 Blueprint には以下のようなWindowsバックスラッシュパスが含まれているため注意が必要:

```python
# 誤り（現状のapp_v2.py内）
@app.route("\api\v1\integrations\microsoft365\sync\configs\<int:config_id>", methods=["GET"])
```

Blueprint移行時に正しいフォワードスラッシュパスに修正すること:

```python
# 正しい
@bp.route("/api/v1/integrations/microsoft365/sync/configs/<int:config_id>", methods=["GET"])
```

### B.2 グローバル状態の管理

以下のグローバル変数は Blueprint 外（`app_v2.py` または新設の `state.py`）で管理する:

- `_dal`: `DataAccessLayer` インスタンス
- `_ms365_sync_service`: MS365同期サービス
- `_ms365_scheduler_service`: MS365スケジューラー
- `redis_client`: Redisクライアント
- `recommendation_engine`: 推薦エンジン
- `socketio`: SocketIOインスタンス
- `limiter`: Rate limiterインスタンス
- `metrics_storage`: メトリクスストレージ

### B.3 Application Factoryパターンへの将来移行

Phase G-3では `create_app()` Factory パターンへの完全移行は対象外とする（既存テストへの影響が大きいため）。Blueprint分割のみを実施し、Application Factory化は Phase G-4以降で検討する。
