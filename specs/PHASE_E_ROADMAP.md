# Phase E 開発ロードマップ v1.0.0

**策定日**: 2026-02-06
**策定者**: roadmap-planner SubAgent
**プロジェクト**: Mirai Knowledge Systems
**現行バージョン**: v1.4.0 (Phase D完了)

---

## 📊 現状分析（Phase D完了時点）

### 実装済み機能（v1.0.0 → v1.4.0）

| Phase | 機能名 | コード量 | テスト件数 | 完了日 | 状態 |
|-------|--------|----------|------------|--------|------|
| A | 基盤構築 | ~50,000行 | 538件 | 2025-12 | ✅ |
| B-1〜B-11 | 本番環境開発 | ~20,000行 | 591件 | 2026-01-25 | ✅ |
| D-3 | 2要素認証（TOTP/MFA） | ~2,930行 | 36件 | 2026-01-31 | ✅ |
| D-4 | MS365連携基盤 | ~12,730行 | 34件 | 2026-01-31 | ✅ |
| **D-4.2** | **ファイルプレビュー基盤** | **~670行** | **10件** | **2026-02-02** | **🟡 Week 1/3** |
| D-5 | PWA対応 | ~8,500行 | 11件 | 2026-01-31 | ✅ |
| D-6 | 往復開発ループ | ~571行 | 6件 | 2026-02-03 | ✅ |

### Phase D-4.2実装状況（コミット `8115d94`）

#### ✅ 完了項目（Week 1/3: バックエンド基盤）

**microsoft_graph.py 拡張（+150行）**:
- `get_file_preview_url()`: プレビューURL生成
  - Office形式（.docx/.xlsx/.pptx）→ Office Online Embed
  - PDF形式 → SharePoint Embed
  - 画像形式（.jpg/.png）→ Direct Download URL
- `get_file_thumbnail()`: サムネイル取得（small/medium/large/custom）
- `get_file_mime_type()`: MIMEタイプ判定

**app_v2.py エンドポイント（+267行）**:
- `GET /api/v1/integrations/microsoft365/files/{file_id}/preview`
- `GET /api/v1/integrations/microsoft365/files/{file_id}/download`
- `GET /api/v1/integrations/microsoft365/files/{file_id}/thumbnail`

**schemas.py バリデーション（+38行）**:
- MS365FilePreviewSchema
- MS365FileThumbnailSchema

**テスト（+215行、10件）**:
- test_file_preview.py
  - Office/PDF/画像の3種類カバー
  - エラーケース検証完備

#### ⬜ 未実装項目（Week 2-3）

**Week 2: フロントエンド実装**:
- file-preview.js（推定400行）
  - プレビューモーダルUI
  - サムネイル画像表示
  - ダウンロード機能
- ms365-sync-settings.html 統合（推定100行）

**Week 3: PWA統合・E2Eテスト**:
- Service Workerキャッシュ対応
- オフラインプレビュー
- E2Eテスト（Playwright、5件）

### 技術的負債（既知の問題）

| 優先度 | 問題 | 影響範囲 | 対応Phase | 見積工数 |
|--------|------|----------|-----------|----------|
| **Medium** | フロントエンドモジュール化 | webui/*.js（13,625行） | E-1 | 40-60h |
| **Medium** | N+1クエリ最適化 | app_v2.py（6,699行） | E-2 | 24-32h |
| Low | TODO残留（9箇所） | app_v2.py, ms365_sync_service.py | E-3 | 8-12h |
| Low | innerHTML使用（27箇所） | webui/*.js（10ファイル） | E-1 | 含む |

### コードベース統計

| 項目 | 数値 | 備考 |
|------|------|------|
| バックエンド総行数 | 約80,000行 | app_v2.py（6,699行）+ サービス層 + テスト |
| フロントエンド総行数 | 約13,625行 | webui/*.js（11ファイル） |
| テスト総件数 | 591件 | カバレッジ91% |
| APIエンドポイント | 56個 | 46個（core）+ 10個（MS365） |
| データベーステーブル | 17個 | 14個（core）+ 3個（MS365） |

---

## 🎯 Phase E 開発戦略

### 基本方針

1. **技術的負債の計画的返済**: Medium優先度問題を優先的に解決
2. **段階的リファクタリング**: 機能追加と並行した漸進的改善
3. **往復開発ループ活用**: SubAgent 9体による自動レビューゲート適用
4. **後方互換性維持**: 既存機能を破壊しない安全な変更

### 開発体制

- **並列開発**: Agent Teams（最大3-5 SubAgent同時起動）
- **自動レビュー**: code-reviewer → test-reviewer → ci-specialist
- **MCP統合**: memory-keeper（設計記憶）、github（類似実装検索）、context7（仕様確認）

---

## 📋 Phase E フェーズ定義

### Phase E-1: フロントエンドアーキテクチャ刷新（優先度: High）

**目的**: モジュール化・保守性向上・XSS完全排除

#### 実装内容

**1. ES6モジュール分割（Week 1-2、24-32h）**:
- app.js（2,500行）→ 8モジュールに分割
  - core/router.js: ルーティング
  - core/state-manager.js: 状態管理
  - api/client.js: API通信（fetch wrapper）
  - ui/components.js: 再利用可能コンポーネント
  - ui/modal.js: モーダルダイアログ
  - ui/table.js: テーブル描画
  - ui/form.js: フォーム処理
  - utils/validators.js: バリデーション

**2. innerHTML完全排除（Week 2、8-12h）**:
- 27箇所のinnerHTML → DOM API置換
  - createElement + textContent
  - DocumentFragment使用（パフォーマンス最適化）
  - XSS脆弱性完全排除

**3. TypeScript型定義導入（Week 3、8h）**:
- JSDoc → TypeScript型定義ファイル（*.d.ts）
- IDE補完強化
- 型安全性向上

**4. テスト整備（Week 3-4、16h）**:
- Jest単体テスト: 50件追加
- Playwright E2E: 10件追加

#### 成果物

- `webui/core/*.js`（8ファイル、推定3,000行）
- `webui/types/*.d.ts`（型定義、推定500行）
- テスト60件追加
- `docs/frontend/MODULE_ARCHITECTURE.md`（アーキテクチャ文書）

#### 依存関係

- 前提: なし（独立実施可能）
- ブロック: E-3（TODO残留削除がE-1と重複する可能性）

#### 工数見積

| タスク | 工数 | 担当SubAgent |
|--------|------|--------------|
| モジュール分割 | 24-32h | code-implementer x2（並列） |
| innerHTML排除 | 8-12h | code-implementer |
| TypeScript型定義 | 8h | spec-planner |
| テスト整備 | 16h | test-designer |
| **合計** | **56-68h** | **約7-9営業日** |

---

### Phase E-2: バックエンドパフォーマンス最適化（優先度: High）

**目的**: N+1クエリ排除・レスポンス時間50%短縮

#### 実装内容

**1. N+1クエリ検出（Week 1、8h）**:
- SQLAlchemy lazy loading分析
- Flask-SQLAlchemy debug toolbar導入
- クエリ実行回数プロファイリング

**2. Eager Loading導入（Week 1-2、16-24h）**:
- `joinedload()` / `selectinload()` 適用
- 主要エンドポイント最適化:
  - `GET /api/v1/knowledge`: ナレッジ一覧（想定N+1: カテゴリ・タグ）
  - `GET /api/v1/projects`: プロジェクト一覧（想定N+1: ナレッジ関連）
  - `GET /api/v1/experts`: 専門家一覧（想定N+1: スキル・所属）

**3. キャッシュ戦略導入（Week 2-3、16h）**:
- Redis統合（Flask-Caching）
- キャッシュ対象:
  - カテゴリマスタ（TTL: 1h）
  - タグマスタ（TTL: 30min）
  - ユーザー権限（TTL: 5min）

**4. データベースインデックス最適化（Week 3、8h）**:
- 検索クエリのINDEX追加
- EXPLAIN ANALYZE分析
- マイグレーションスクリプト作成

**5. パフォーマンステスト（Week 4、8h）**:
- Locust負荷テスト（1,000 req/s目標）
- レスポンス時間計測
- Before/After比較レポート

#### 成果物

- `backend/cache_config.py`（キャッシュ設定、推定150行）
- `backend/migrations/versions/add_performance_indexes.py`（マイグレーション）
- Locust負荷テストスクリプト（推定200行）
- `docs/performance/OPTIMIZATION_REPORT.md`（最適化レポート）

#### 依存関係

- 前提: なし（独立実施可能）
- 推奨: Phase Cの本番運用データ蓄積後が理想

#### 工数見積

| タスク | 工数 | 担当SubAgent |
|--------|------|--------------|
| N+1クエリ検出 | 8h | arch-reviewer（Explore） |
| Eager Loading導入 | 16-24h | code-implementer |
| キャッシュ戦略 | 16h | code-implementer |
| インデックス最適化 | 8h | code-implementer |
| パフォーマンステスト | 8h | test-designer |
| **合計** | **56-64h** | **約7-8営業日** |

---

### Phase E-3: 技術的負債返済（優先度: Medium）

**目的**: コード品質向上・保守性強化

#### 実装内容

**1. TODO残留削除（Week 1、8-12h）**:
- app_v2.py:
  - Line 1446: `roles` 取得実装（データベーステーブル作成）
  - Line 2355: メール送信実装（SendGrid統合）
  - Line 4402: お気に入り機能実装（users_favoritesテーブル）
  - Line 5134: Socket.IO接続数取得
- ms365_sync_service.py:
  - Line 464: MetadataExtractor詳細抽出（Phase D-4完了時に実装済みの可能性）
  - Line 611: cron次回実行時刻計算（croniter導入）

**2. デッドコード削除（Week 1、4h）**:
- 未使用関数・変数の削除
- flake8 unused-imports 警告解消

**3. Logging標準化（Week 2、8h）**:
- structlog導入（構造化ログ）
- JSON形式ログ出力
- ELK Stack連携準備

**4. エラーハンドリング統一（Week 2、8h）**:
- カスタム例外クラス導入
- エラーレスポンス形式統一
- RFC 7807（Problem Details）準拠

#### 成果物

- 9箇所のTODO実装完了
- `backend/logging_config.py`（ログ設定、推定100行）
- `backend/exceptions.py`（カスタム例外、推定200行）

#### 依存関係

- 前提: E-1（フロントエンドモジュール化）と一部重複する可能性
- ブロック: なし

#### 工数見積

| タスク | 工数 | 担当SubAgent |
|--------|------|--------------|
| TODO残留削除 | 8-12h | code-implementer |
| デッドコード削除 | 4h | code-reviewer（自動検出） |
| Logging標準化 | 8h | code-implementer |
| エラーハンドリング統一 | 8h | code-implementer |
| **合計** | **28-32h** | **約4営業日** |

---

### Phase E-4: MS365ファイルプレビュー完成（優先度: High）

**目的**: Phase D-4.2（Week 1/3完了）の完成

#### 実装内容

**Week 2: フロントエンド実装（16-24h）**:
- file-preview.js（推定400行）
  - プレビューモーダルUI
    - Office形式 → iframe埋め込み
    - PDF → pdfjs-dist統合
    - 画像 → img要素表示
  - サムネイル画像表示
  - ダウンロード機能
  - エラーハンドリング（プレビュー不可時のフォールバック）

**Week 3: PWA統合・E2Eテスト（8-12h）**:
- Service Worker対応
  - プレビューURL/サムネイルキャッシュ（7日間）
  - オフライン時のキャッシュ表示
- Playwright E2Eテスト（5件）
  - プレビューモーダル表示
  - サムネイル読み込み
  - ダウンロード機能
  - オフライン動作
  - エラーケース

**Week 4: ドキュメント整備（4h）**:
- ユーザーガイド更新（MS365_SYNC_GUIDE.md）
- API仕様書更新

#### 成果物

- `webui/file-preview.js`（400行）
- `webui/sw.js`修正（+50行）
- Playwright E2Eテスト（5件、推定250行）
- `docs/user-guide/MS365_SYNC_GUIDE.md`更新

#### 依存関係

- 前提: Phase D-4.2 Week 1完了（✅ 完了済み）
- ブロック: E-1（file-preview.jsがモジュール化の対象になる可能性）

#### 工数見積

| タスク | 工数 | 担当SubAgent |
|--------|------|--------------|
| フロントエンド実装 | 16-24h | code-implementer |
| PWA統合 | 4-6h | code-implementer |
| E2Eテスト | 4-6h | test-designer |
| ドキュメント整備 | 4h | ops-runbook |
| **合計** | **28-40h** | **約4-5営業日** |

---

### Phase E-5: セキュリティ強化（優先度: Medium）

**目的**: OWASP Top 10対策完全化

#### 実装内容

**1. CSP（Content Security Policy）強化（Week 1、8h）**:
- CSPヘッダー設定厳格化
  - `script-src 'self'`（inline script完全排除）
  - `style-src 'self'`（inline style完全排除）
  - `connect-src 'self' https://graph.microsoft.com`
- Nonce/Hash方式導入

**2. SAST（Static Application Security Testing）導入（Week 1-2、8h）**:
- Bandit（Python）統合
- ESLint security plugin統合
- CI/CD自動実行

**3. 依存関係脆弱性スキャン（Week 2、4h）**:
- Dependabot有効化
- Snyk統合（週次スキャン）
- 自動PR作成

**4. セキュリティ監査（Week 3、16h）**:
- sec-auditor SubAgent起動
- OWASP ZAP動的スキャン
- 脆弱性診断レポート作成

**5. セキュリティヘッダー追加（Week 2、4h）**:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy設定

#### 成果物

- `backend/security_headers.py`（推定100行）
- `.github/workflows/security-scan.yml`（GitHub Actions）
- `docs/security/SECURITY_AUDIT_REPORT.md`（監査レポート）

#### 依存関係

- 前提: E-1（inline script排除がCSP強化の前提）
- 推奨: sec-auditor SubAgent使用

#### 工数見積

| タスク | 工数 | 担当SubAgent |
|--------|------|--------------|
| CSP強化 | 8h | code-implementer |
| SAST導入 | 8h | ci-specialist |
| 依存関係スキャン | 4h | ci-specialist |
| セキュリティ監査 | 16h | sec-auditor |
| セキュリティヘッダー | 4h | code-implementer |
| **合計** | **40h** | **約5営業日** |

---

## 📊 Phase E 優先度マトリクス

### 優先順位判定基準

| 軸 | 高 | 中 | 低 |
|----|----|----|-----|
| **ビジネス価値** | 既存機能完成・UX改善 | 保守性向上 | 将来拡張準備 |
| **技術的負債** | 深刻（セキュリティ/パフォーマンス） | 中程度（保守性） | 軽微 |
| **リスク** | 本番環境影響大 | 影響限定的 | 影響なし |

### フェーズ別優先度

| Phase | 優先度 | ビジネス価値 | 技術的負債 | リスク | 推奨開始時期 |
|-------|--------|--------------|------------|--------|--------------|
| **E-4** | **P0（最優先）** | **高**（Phase D-4.2完成） | 低 | 低 | **即時** |
| **E-1** | **P1（高）** | 中（保守性向上） | **高**（XSS/モジュール化） | 中 | Week 2 |
| **E-2** | **P1（高）** | **高**（パフォーマンス） | **高**（N+1クエリ） | 中 | Week 3 |
| **E-5** | **P2（中）** | 中（セキュリティ） | 中 | 高 | Week 6 |
| **E-3** | **P3（低）** | 低 | 中（コード品質） | 低 | Week 8 |

---

## 🗓️ Phase E 実装スケジュール

### 推奨実装順序（理由付き）

```
Week 1-2:   E-4（MS365プレビュー完成）
            → 理由: 既存機能の完成・ユーザー価値最大化

Week 2-4:   E-1（フロントエンドモジュール化）
            → 理由: E-5（CSP強化）の前提条件

Week 4-6:   E-2（パフォーマンス最適化）
            → 理由: E-1と独立・並列実施可能

Week 6-8:   E-5（セキュリティ強化）
            → 理由: E-1完了後が理想（inline script排除完了後）

Week 8-10:  E-3（技術的負債返済）
            → 理由: 影響範囲限定的・後回し可能
```

### 並列開発戦略

**Week 2-4**: E-1（フロントエンド） + E-4（MS365完成）並列実施
- E-4は独立したファイル（file-preview.js）
- E-1はapp.js等の既存ファイルリファクタリング
- **ファイルコンフリクトなし** → 安全に並列化可能

**Week 4-6**: E-2（バックエンド）単独実施
- データベーススキーマ変更の可能性 → 並列化リスク高

### Agent Teams並列実行計画

#### Week 1-2: 2 SubAgent並列

```yaml
agents:
  - name: file-preview-implementer
    type: code-implementer
    task: E-4 Week 2（フロントエンド実装）
    files: [webui/file-preview.js, webui/sw.js]

  - name: module-architect
    type: spec-planner
    task: E-1仕様策定（モジュール分割設計）
    files: [specs/FRONTEND_MODULE_ARCHITECTURE.md]
```

#### Week 2-4: 3 SubAgent並列

```yaml
agents:
  - name: module-implementer-1
    type: code-implementer
    task: E-1（core/router.js, core/state-manager.js）
    files: [webui/core/router.js, webui/core/state-manager.js]

  - name: module-implementer-2
    type: code-implementer
    task: E-1（api/client.js, ui/*.js）
    files: [webui/api/client.js, webui/ui/components.js, webui/ui/modal.js]

  - name: pwa-tester
    type: test-designer
    task: E-4 Week 3（PWA統合・E2Eテスト）
    files: [backend/tests/e2e/ms365-file-preview.spec.js]
```

---

## 📈 Phase E 完了時の目標KPI

### コード品質

| 指標 | 現状 | 目標 | 改善率 |
|------|------|------|--------|
| フロントエンドモジュール数 | 1（app.js） | 8モジュール | - |
| innerHTML使用箇所 | 27箇所 | 0箇所 | **-100%** |
| TODO残留 | 9箇所 | 0箇所 | **-100%** |
| TypeScript型定義 | なし | 500行 | - |

### パフォーマンス

| 指標 | 現状 | 目標 | 改善率 |
|------|------|------|--------|
| ナレッジ一覧レスポンス時間 | 未計測 | 200ms以下 | - |
| N+1クエリ数 | 未検出 | 0件 | **-100%** |
| Redisキャッシュヒット率 | - | 80%以上 | - |
| Locust負荷テスト（1,000 req/s） | - | 成功 | - |

### セキュリティ

| 指標 | 現状 | 目標 | 改善率 |
|------|------|------|--------|
| CSP違反（inline script） | あり | なし | **-100%** |
| OWASP ZAP脆弱性 | 未検出 | 0件 | - |
| 依存関係脆弱性 | 未検出 | 0件（週次スキャン） | - |
| セキュリティヘッダースコア | 未計測 | A+（Mozilla Observatory） | - |

### テスト

| 指標 | 現状 | 目標 | 改善率 |
|------|------|------|--------|
| フロントエンド単体テスト | 0件 | 50件 | - |
| E2Eテスト | 19件 | 34件 | **+79%** |
| テストカバレッジ | 91% | 93%以上 | +2% |

---

## 🔄 往復開発ループ適用戦略

### SubAgent 9体の工程遷移フロー

```
[E-4 MS365プレビュー完成例]

spec-planner (Week 0, 4h)
  ↓ specs/MS365_FILE_PREVIEW_SPEC.md 出力
  ↓ Hook: on-spec-complete
arch-reviewer (Week 0, 2h)
  ↓ design/MS365_FILE_PREVIEW_DESIGN.md レビュー
  ↓ Hook: on-arch-approved
code-implementer (Week 1-2, 20h)
  ↓ webui/file-preview.js 実装
  ↓ Hook: on-implementation-complete
code-reviewer (Week 2, 1h)
  ↓ 判定: PASS_WITH_WARNINGS（minor: JSDoc不足）
  ↓ Hook: on-code-review-result
test-designer (Week 2-3, 6h)
  ↓ tests/e2e/ms365-file-preview.spec.js 作成
  ↓ Hook: on-test-design-complete
test-reviewer (Week 3, 1h)
  ↓ 判定: PASS
  ↓ Hook: on-test-review-result
ci-specialist (Week 3, 2h)
  ↓ GitHub Actions実行・GO/NO-GO判定
  ↓ 結果: GO → PRマージ
```

### 自動レビューゲート設計

#### code-reviewer判定基準（E-1向け）

```yaml
review_checklist:
  - name: モジュール分割妥当性
    checks:
      - Single Responsibility Principleに準拠しているか
      - 循環依存がないか
      - export/import が正しいか

  - name: XSS対策
    checks:
      - innerHTML/outerHTMLを使用していないか
      - textContent/createElementを使用しているか
      - ユーザー入力をエスケープしているか

  - name: 型安全性
    checks:
      - JSDocまたはTypeScript型定義があるか
      - null/undefined チェックがあるか
```

#### test-reviewer判定基準（E-2向け）

```yaml
test_coverage_checklist:
  - name: パフォーマンステスト網羅性
    checks:
      - N+1クエリ修正前後の比較テストがあるか
      - キャッシュヒット/ミスのテストがあるか
      - Locust負荷テストスクリプトがあるか

  - name: 境界値テスト
    checks:
      - 大量データ（10,000件）の検索テストがあるか
      - キャッシュTTL期限切れのテストがあるか
```

---

## 🛡️ リスク管理

### 高リスク項目

| Phase | リスク | 影響 | 対策 | 緊急度 |
|-------|--------|------|------|--------|
| E-1 | app.js大規模リファクタリングで既存機能破壊 | 高 | ①段階的移行（1モジュールずつ）<br>②E2E回帰テスト必須 | 高 |
| E-2 | Eager Loading導入でメモリ使用量増加 | 中 | ①selectinload優先（N+1回避）<br>②本番環境メモリ監視 | 中 |
| E-5 | CSP厳格化でサードパーティスクリプト動作不可 | 高 | ①Nonce方式導入<br>②段階的ロールアウト | 高 |

### 中リスク項目

| Phase | リスク | 影響 | 対策 | 緊急度 |
|-------|--------|------|------|--------|
| E-4 | Office Online Embed API制限（未ログインアクセス不可） | 中 | ①ドキュメント明記<br>②代替プレビュー（サムネイル）提供 | 低 |
| E-3 | メール送信実装（SendGrid）でコスト増加 | 低 | ①無料枠確認<br>②送信数制限実装 | 低 |

---

## 📚 参考資料

### 技術仕様

- [Frontend Module Architecture Best Practices](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules)
- [SQLAlchemy Eager Loading](https://docs.sqlalchemy.org/en/20/orm/loading_relationships.html)
- [OWASP Content Security Policy Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html)

### 社内ドキュメント

- [CLAUDE.md](../.claude/CLAUDE.md): プロジェクト概要
- [PHASE_D5_PWA_COMPLETION_REPORT.md](../docs/PHASE_D5_PWA_COMPLETION_REPORT.md): PWA実装完了レポート
- [MS365_SYNC_COMPLETION_SUMMARY.md](../docs/MS365_SYNC_COMPLETION_SUMMARY.md): MS365完了サマリー

---

## 🎓 今後の展望（Phase F以降）

### Phase F候補（優先度順）

1. **Phase F-1: リアルタイム通知（WebSocket/SSE）**
   - ナレッジ更新通知
   - MS365ファイル変更通知
   - 専門家相談チャット
   - 工数: 60-80h

2. **Phase F-2: AI支援機能（GPT-4統合）**
   - ナレッジ自動分類
   - 関連ナレッジ推薦
   - 専門家マッチング
   - 工数: 80-120h

3. **Phase F-3: モバイルアプリ（React Native）**
   - iOS/Androidネイティブアプリ
   - オフライン同期強化
   - プッシュ通知
   - 工数: 120-160h

4. **Phase F-4: データ分析ダッシュボード（BI）**
   - ナレッジ活用状況分析
   - 専門家稼働率分析
   - プロジェクト進捗可視化
   - 工数: 60-80h

---

## ✅ Phase E 完了定義（Definition of Done）

### 技術的完了条件

- [ ] E-1: フロントエンド8モジュール分割完了、innerHTML 0件
- [ ] E-2: N+1クエリ 0件、キャッシュヒット率80%以上
- [ ] E-3: TODO残留 0件、structlog導入完了
- [ ] E-4: ファイルプレビュー機能完全動作、E2Eテスト 5/5件成功
- [ ] E-5: OWASP ZAP脆弱性 0件、CSP違反 0件

### ドキュメント完了条件

- [ ] 各フェーズの完了レポート作成（Markdown形式）
- [ ] APIドキュメント更新（OpenAPI 3.0）
- [ ] ユーザーガイド更新

### テスト完了条件

- [ ] ユニットテスト: 50件追加（フロントエンド）
- [ ] E2Eテスト: 15件追加（Playwright）
- [ ] 負荷テスト: 1,000 req/s成功（Locust）
- [ ] セキュリティスキャン: 脆弱性 0件（OWASP ZAP）
- [ ] テストカバレッジ: 93%以上

### デプロイ完了条件

- [ ] 本番環境デプロイ成功
- [ ] ロールバック手順確認
- [ ] 監視アラート設定（Prometheus/Grafana）
- [ ] 運用手順書更新

---

**次のアクション**:
1. team-leadによるPhase E-4即時着手判断
2. E-1仕様書策定（spec-planner起動）
3. memory-keeper保存（本ロードマップをproject_decisionsチャネルに保存）

**策定者**: roadmap-planner SubAgent
**レビュー**: 未実施（team-leadレビュー待ち）
**承認**: 未承認
