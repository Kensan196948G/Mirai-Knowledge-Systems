# Phase F: フロントエンドモジュール化 - プロジェクト概要

**バージョン**: 1.0.0
**作成日**: 2026-02-10
**作成者**: spec-planner SubAgent
**ステータス**: Draft

---

## 📋 プロジェクト概要

Phase Fは、Mirai Knowledge Systemsのフロントエンドコードベースを完全にモジュール化し、保守性・拡張性・テスト容易性を向上させるプロジェクトです。

---

## 🎯 プロジェクト目標

### 主要目標
1. **コードベースの分割**: 大規模ファイル（app.js: 3,895行、detail-pages.js: 3,291行）の分割
2. **モジュール化**: ESモジュール構文への完全移行
3. **再利用性向上**: 共通ロジックの一元管理
4. **テスト容易性向上**: 単体テスト可能なモジュール設計
5. **パフォーマンス最適化**: Viteビルドシステムによる最適なバンドリング

### 期待効果
- **開発効率**: 50%向上（モジュール分割、ホットリロード）
- **保守性**: 70%向上（コード重複排除、一元管理）
- **テストカバレッジ**: 90%以上（単体テスト可能なモジュール）
- **ビルドサイズ**: 30%削減（チャンク分割、Tree Shaking）

---

## 📊 フェーズ構成

| Phase | 名称 | 進捗 | 状態 | 期間 |
|-------|------|------|------|------|
| F-1 | Viteビルドシステム + コアモジュール | 100% | ✅ 完了 | 2026-02-10 |
| F-2 | 機能モジュール分割 | 0% | 📝 要件定義完了 | Week 4-5 |
| F-3 | ユーティリティモジュール分割 | 0% | 📝 要件定義完了 | Week 6-7 |
| F-4 | 既存コードリファクタリング | 0% | 📝 要件定義完了 | Week 8-10 |

**総期間**: 約10週間（Phase F-1完了済み、残り約7週間）

---

## 🚀 Phase F-1: Viteビルドシステム + コアモジュール（完了）

**完了日**: 2026-02-10
**実装時間**: 約20分
**ステータス**: ✅ 完了

### 実装内容
- Viteビルドシステム導入（vite.config.js: 120行）
- コアモジュール実装（3ファイル: api-client, auth, logger）
- webui/src/ ディレクトリ構造構築
- 後方互換性維持（window経由の呼び出し可能）

### 成果物
- `vite.config.js`: Vite設定（マルチページ対応、チャンク分割）
- `webui/src/core/api-client.js`: API Client（98行）
- `webui/src/core/auth.js`: Auth（123行）
- `webui/src/core/logger.js`: Logger（140行）
- `webui/module-test.html`: モジュールテストページ（135行）

### 詳細レポート
- [PHASE_F1_IMPLEMENTATION_REPORT.md](/mnt/d/Mirai-Knowledge-Systems/PHASE_F1_IMPLEMENTATION_REPORT.md)

---

## 📝 Phase F-2: 機能モジュール分割（要件定義完了）

**期間**: Week 4-5（約10営業日）
**ステータス**: 📝 要件定義完了

### 目的
- 既存の機能別JavaScriptファイルをESモジュール化
- `webui/src/features/` ディレクトリへの統合

### 対象モジュール（5個）

| # | モジュール名 | 元ファイル | 想定行数 | 依存 |
|---|------------|----------|---------|------|
| 1 | search.js | app.js内 | 約300行 | api-client, logger |
| 2 | knowledge.js | app.js内 | 約400行 | api-client, logger, dom-helpers |
| 3 | mfa.js | webui/mfa.js | 約380行 | api-client, logger |
| 4 | ms365-sync.js | webui/ms365-sync.js | 約900行 | api-client, logger, dom-helpers |
| 5 | pwa.js | 4ファイル統合 | 約900行 | logger |

**総コード量**: 約2,880行

### 主要機能

#### search.js
- 統合検索実行（`searchUnified`）
- 検索履歴管理（`getSearchHistory`, `addSearchHistory`）
- 人気検索ワード取得（`getPopularSearchKeywords`）

#### knowledge.js
- ナレッジCRUD（`getKnowledgeList`, `createKnowledge`, `updateKnowledge`, `deleteKnowledge`）
- ナレッジ詳細取得（`getKnowledgeDetail`）
- 人気ナレッジ取得（`getPopularKnowledge`）

#### mfa.js
- MFAステータス取得（`getMFAStatus`）
- MFAセットアップ（`startMFASetup`, `completeMFASetup`）
- MFA無効化（`disableMFA`）
- MFA検証（`verifyMFA`）
- バックアップコード再生成（`regenerateBackupCodes`）

#### ms365-sync.js
- MS365同期設定管理（`getSyncConfigs`, `createSyncConfig`, `updateSyncConfig`, `deleteSyncConfig`）
- MS365同期実行（`executeSyncNow`）
- MS365同期履歴取得（`getSyncHistory`）
- MS365接続テスト（`testMS365Connection`）

#### pwa.js
- PWAインストールプロンプト（`showInstallPrompt`, `isInstallable`）
- キャッシュマネージャー（`initCacheManager`, `clearCache`）
- 同期マネージャー（`initSyncManager`, `queueSync`）
- JWT暗号化（`encryptToken`, `decryptToken`）

### 受け入れ基準
- [ ] 5つの機能モジュールが実装されている
- [ ] ESモジュール構文を使用している
- [ ] JSDocコメントが完全に付与されている
- [ ] 単体テストがある（Jest）
- [ ] E2Eテストが成功する（Playwright）

### 詳細仕様
- [phase_f2_requirements.md](/mnt/d/Mirai-Knowledge-Systems/specs/phase_f2_requirements.md)

---

## 🛠️ Phase F-3: ユーティリティモジュール分割（要件定義完了）

**期間**: Week 6-7（約10営業日）
**ステータス**: 📝 要件定義完了

### 目的
- 共通ユーティリティ関数のモジュール化
- `webui/src/utils/` ディレクトリへの統合
- コード重複の排除と再利用性の向上

### 対象モジュール（4個）

| # | モジュール名 | 元ファイル | 想定行数 | 依存 |
|---|------------|----------|---------|------|
| 1 | dom-helpers.js | webui/dom-helpers.js | 約1,100行 | logger |
| 2 | date-formatter.js | app.js内 | 約150行 | なし |
| 3 | validation.js | app.js内 | 約200行 | なし |
| 4 | file-utils.js | webui/file-preview.js + app.js | 約900行 | logger |

**総コード量**: 約2,350行

### 主要機能

#### dom-helpers.js（DOM操作）
- テキストノード作成（XSS対策）
- 要素作成・操作（`createElement`, `clearElement`, `setVisible`, `toggleClass`）
- HTML/URLサニタイズ（`sanitizeHTML`, `sanitizeURL`）
- フォームデータ取得（`getFormData`）
- テーブル行作成（`createTableRow`）
- ページネーション作成（`createPagination`）
- モーダルダイアログ（`showModal`）
- トーストメッセージ（`showToast`）

#### date-formatter.js（日付フォーマット）
- 日本語形式フォーマット（`formatDate`）
- 相対日付フォーマット（`formatRelativeDate`）
- 日付範囲フォーマット（`formatDateRange`）
- ISO 8601パース（`parseISO`, `toISO`）
- タイムゾーン変換（`convertTimezone`）
- 営業日計算（`addBusinessDays`）
- 年齢計算（`calculateAge`）

#### validation.js（バリデーション）
- メールアドレス検証（`isValidEmail`）
- URL検証（`isValidURL`）
- パスワード検証（`validatePassword`）
- 電話番号検証（`isValidPhoneNumber`）
- 郵便番号検証（`isValidPostalCode`）
- 日付検証（`isValidDate`）
- 文字列長検証（`isValidLength`）
- 数値範囲検証（`isInRange`）
- ファイルサイズ・拡張子検証（`isValidFileSize`, `isValidFileExtension`）
- フォーム一括検証（`validateForm`）
- XSS/SQLインジェクション検出（`containsXSS`, `containsSQLInjection`）

#### file-utils.js（ファイル操作）
- ファイルサイズフォーマット（`formatFileSize`）
- 拡張子・MIMEタイプ取得（`getFileExtension`, `getMIMEType`）
- ファイル読み込み（`readFileAsBase64`, `readFileAsText`, `readFileAsDataURL`）
- 画像リサイズ（`resizeImage`）
- ファイルプレビュー生成（`generateFilePreview`）
- PDFサムネイル生成（`generatePDFThumbnail`）
- ファイルダウンロード（`downloadFile`）
- ファイルアップロード進捗監視（`uploadFileWithProgress`）
- ドラッグ&ドロップ有効化（`enableDragAndDrop`）

### 受け入れ基準
- [ ] 4つのユーティリティモジュールが実装されている
- [ ] Pure Functionと副作用のある関数が明確に区別されている
- [ ] XSS対策が徹底されている
- [ ] 単体テストがある（Jest）
- [ ] テストカバレッジが90%以上

### 詳細仕様
- [phase_f3_requirements.md](/mnt/d/Mirai-Knowledge-Systems/specs/phase_f3_requirements.md)

---

## 🔧 Phase F-4: 既存コードリファクタリング（要件定義完了）

**期間**: Week 8-10（約15営業日）
**ステータス**: 📝 要件定義完了

### 目的
- 大規模ファイル（app.js: 3,895行、detail-pages.js: 3,291行）の分割
- ESモジュール構文への完全移行
- Phase F-2、F-3で作成したモジュールの活用

### 対象ファイル（2個）

#### 1. app.js（3,895行）
分割後の構成:
```
webui/src/app/
├── index.js                    # エントリーポイント（約300行）
├── init.js                     # 初期化処理（約200行）
├── router.js                   # ルーティング（約150行）
├── event-handlers.js           # イベントハンドラー（約400行）
├── ui-controller.js            # UI制御（約500行）
├── data-loader.js              # データ読み込み（約300行）
├── notifications-handler.js    # 通知処理（約200行）
├── actions-handler.js          # アクション処理（約300行）
└── legacy-compat.js            # 後方互換性（約200行）
```

**削減行数**: 3,895行 → 約2,000行（削減率: 48%）

---

#### 2. detail-pages.js（3,291行）
分割後の構成:
```
webui/src/pages/
├── knowledge-detail.js         # ナレッジ詳細（約500行）
├── sop-detail.js               # SOP詳細（約500行）
├── law-detail.js               # 法令詳細（約400行）
├── expert-detail.js            # 専門家詳細（約400行）
├── consultation-detail.js      # 相談詳細（約400行）
├── incident-detail.js          # インシデント詳細（約400行）
├── approval-detail.js          # 承認詳細（約300行）
└── page-renderer.js            # 共通レンダリング（約300行）
```

**削減行数**: 3,291行 → 約2,800行（削減率: 15%）

---

### マイグレーション計画

#### Week 8: app.js 分割
| ステップ | 作業内容 | 期間 |
|---------|---------|------|
| 1 | 依存関係分析 | 1日 |
| 2 | 8ファイルに分割 | 2日 |
| 3 | 単体テスト作成 | 1日 |
| 4 | E2Eテスト実行 | 0.5日 |
| 5 | レビュー・修正 | 0.5日 |

#### Week 9: detail-pages.js 分割
| ステップ | 作業内容 | 期間 |
|---------|---------|------|
| 1 | 依存関係分析 | 1日 |
| 2 | 8ファイルに分割 | 2日 |
| 3 | 単体テスト作成 | 1日 |
| 4 | E2Eテスト実行 | 0.5日 |
| 5 | レビュー・修正 | 0.5日 |

#### Week 10: 既存HTMLファイル更新
| ステップ | 作業内容 | 期間 |
|---------|---------|------|
| 1 | index.html 更新 | 0.5日 |
| 2 | その他HTMLファイル更新 | 1日 |
| 3 | E2Eテスト全実行 | 0.5日 |
| 4 | パフォーマンステスト | 0.5日 |
| 5 | 最終レビュー・修正 | 0.5日 |

---

### 受け入れ基準
- [ ] app.js が8ファイルに分割されている（1ファイル500行以内）
- [ ] detail-pages.js が8ファイルに分割されている（1ファイル500行以内）
- [ ] Phase F-2、F-3のモジュールを活用している
- [ ] 循環依存が発生していない
- [ ] 既存機能がすべて動作する
- [ ] パフォーマンスが既存と同等（±10%以内）
- [ ] 単体テストがある（Jest）
- [ ] E2Eテストがすべて成功する（Playwright）

### 詳細仕様
- [phase_f4_requirements.md](/mnt/d/Mirai-Knowledge-Systems/specs/phase_f4_requirements.md)

---

## 📊 全体統計

### コード量の変化

| 項目 | Phase F-1完了時点 | Phase F-2完了時点 | Phase F-3完了時点 | Phase F-4完了時点 |
|------|------------------|------------------|------------------|------------------|
| **総コード量** | 約13,500行 | 約16,380行 | 約18,730行 | 約20,730行 |
| **モジュール数** | 3個 | 8個 | 12個 | 28個 |
| **平均ファイルサイズ** | 120行 | 340行 | 340行 | 250行 |
| **テストカバレッジ** | 0% | 90% | 90% | 90% |

**注**: コード量増加は、JSDocコメント、単体テスト、エラーハンドリング追加によるものです。

---

### ディレクトリ構造（Phase F-4完了時点）

```
Mirai-Knowledge-Systems/
└── webui/
    ├── src/
    │   ├── core/                   # コアモジュール（3ファイル）
    │   │   ├── api-client.js       # API Client（98行）
    │   │   ├── auth.js             # Auth（123行）
    │   │   └── logger.js           # Logger（140行）
    │   ├── features/               # 機能モジュール（5ファイル）
    │   │   ├── search.js           # 統合検索（約300行）
    │   │   ├── knowledge.js        # ナレッジ管理（約400行）
    │   │   ├── mfa.js              # MFA機能（約380行）
    │   │   ├── ms365-sync.js       # MS365同期（約900行）
    │   │   └── pwa.js              # PWA機能（約900行）
    │   ├── utils/                  # ユーティリティ（4ファイル）
    │   │   ├── dom-helpers.js      # DOM操作（約1,100行）
    │   │   ├── date-formatter.js   # 日付フォーマット（約150行）
    │   │   ├── validation.js       # バリデーション（約200行）
    │   │   └── file-utils.js       # ファイル操作（約900行）
    │   ├── app/                    # アプリケーション（8ファイル）
    │   │   ├── index.js
    │   │   ├── init.js
    │   │   ├── router.js
    │   │   ├── event-handlers.js
    │   │   ├── ui-controller.js
    │   │   ├── data-loader.js
    │   │   ├── notifications-handler.js
    │   │   ├── actions-handler.js
    │   │   └── legacy-compat.js
    │   └── pages/                  # ページモジュール（8ファイル）
    │       ├── knowledge-detail.js
    │       ├── sop-detail.js
    │       ├── law-detail.js
    │       ├── expert-detail.js
    │       ├── consultation-detail.js
    │       ├── incident-detail.js
    │       ├── approval-detail.js
    │       └── page-renderer.js
    ├── index.html
    ├── login.html
    └── ... (その他HTMLファイル)
```

**総ファイル数**: 28ファイル（コアモジュール3 + 機能モジュール5 + ユーティリティ4 + アプリ8 + ページ8）

---

## 🎯 期待効果

### 開発効率
- **コード探索時間**: 70%削減（モジュール分割により目的のコードが見つけやすい）
- **機能追加時間**: 50%削減（既存モジュールの再利用）
- **バグ修正時間**: 60%削減（影響範囲が明確）

### 保守性
- **コード重複**: 80%削減（共通ロジックの一元管理）
- **テストカバレッジ**: 90%以上（単体テスト可能なモジュール）
- **ドキュメント化**: JSDocによる自動ドキュメント生成

### パフォーマンス
- **初回ロード時間**: 20%削減（チャンク分割、遅延ロード）
- **ビルドサイズ**: 30%削減（Tree Shaking、Terser圧縮）
- **ビルド時間**: 変化なし（Vite高速ビルド）

### セキュリティ
- **XSS対策**: 100%徹底（DOM API使用、サニタイズ）
- **本番環境ログ削除**: 100%自動削除（Terser設定）

---

## 🛡 品質保証

### テスト戦略

#### 単体テスト（Jest）
- すべてのモジュール関数に単体テストを作成
- テストカバレッジ90%以上を目標
- Pure Functionを優先的にテスト

#### 統合テスト（Playwright）
- 主要な機能フローをE2Eテスト
- ログイン → 検索 → 詳細表示 → 編集 → 保存
- MFAフロー、MS365同期フロー、PWAインストールフロー

#### パフォーマンステスト
- Lighthouse Performanceスコア90点以上
- ページロード時間500ms以内（キャッシュなし）
- ビルドサイズ5MB以下（圧縮前）

---

## 🔄 SubAgent連携フロー

### Phase F-2: 機能モジュール分割

```
spec-planner (完了)
    ↓ on-spec-complete
arch-reviewer (レビュー待ち)
    ↓ on-arch-approved
code-implementer (実装待ち)
    ↓ on-implementation-complete
code-reviewer (自動レビュー待ち)
    ↓ on-code-review-PASS
test-designer (テスト設計待ち)
    ↓ on-test-design-complete
test-reviewer (テストレビュー待ち)
    ↓ on-test-review-PASS
ci-specialist (CI/リリース待ち)
```

### Phase F-3: ユーティリティモジュール分割

同じフローを Phase F-3 に対して実施

### Phase F-4: 既存コードリファクタリング

同じフローを Phase F-4 に対して実施

---

## 📚 関連ドキュメント

### Phase F-1（完了）
- [PHASE_F1_IMPLEMENTATION_REPORT.md](/mnt/d/Mirai-Knowledge-Systems/PHASE_F1_IMPLEMENTATION_REPORT.md)

### Phase F-2（要件定義完了）
- [phase_f2_requirements.md](/mnt/d/Mirai-Knowledge-Systems/specs/phase_f2_requirements.md)
- phase_f2_non_functional.md（今後作成）
- phase_f2_operations.md（今後作成）

### Phase F-3（要件定義完了）
- [phase_f3_requirements.md](/mnt/d/Mirai-Knowledge-Systems/specs/phase_f3_requirements.md)
- phase_f3_non_functional.md（今後作成）
- phase_f3_operations.md（今後作成）

### Phase F-4（要件定義完了）
- [phase_f4_requirements.md](/mnt/d/Mirai-Knowledge-Systems/specs/phase_f4_requirements.md)
- phase_f4_non_functional.md（今後作成）
- phase_f4_operations.md（今後作成）

---

## 🚀 次のアクション

### Phase F-2 実装開始準備

#### 1. arch-reviewer SubAgent 起動
```bash
# 設計レビューを実施
arch-reviewer phase_f2_requirements.md
```

#### 2. code-implementer SubAgent 起動（設計承認後）
```bash
# 実装を開始
code-implementer --spec specs/phase_f2_requirements.md
```

#### 3. 実装完了後の確認項目
- [ ] 5つのモジュールが実装されている
- [ ] ESLintエラーが0件
- [ ] JSDocコメントが完全に付与されている
- [ ] 単体テストがある
- [ ] E2Eテストが成功する

---

## 変更履歴

| バージョン | 日付 | 変更内容 | 作成者 |
|-----------|------|---------|--------|
| 1.0.0 | 2026-02-10 | 初版作成 | spec-planner SubAgent |

---

**このドキュメントは ITSM および ISO 27001/9001 に準拠しています。**
