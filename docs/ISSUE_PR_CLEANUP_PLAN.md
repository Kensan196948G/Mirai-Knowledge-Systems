# GitHub Issue & PR クリーンアップ計画

**作成日**: 2026-02-10
**ステータス**: 実行待ち
**目的**: リポジトリの健全性向上、メンテナンス性改善

---

## 📊 現状サマリー

| 項目 | 数 | 状態 |
|------|-----|------|
| オープンIssue | 6件 | すべてrefinement-needed |
| オープンPR | 14件 | 7件は最近、7件は古い（2〜4週間前） |
| リモートブランチ | 20件+ | 多数の古いfeature/copilotブランチ |

---

## 🎯 Phase 1: Issue整理（優先度順）

### Critical - 即時対応推奨

#### 1. Issue #3093 - Round-trip基盤実装 [round-trip:1] ⚡

**優先度**: P0 - Critical
**作成日**: 2026-02-06
**Source-PR**: #3092
**Iteration**: 1 / 3
**変更ファイル**: 7ファイル（571行追加、19行削除）

**対応内容**:
- Round-trip Development Loop基盤実装の精製
- CI/CDワークフロー改善
- ドキュメント整備

**推奨アクション**:
```bash
# ブランチ作成: refinement/1/pr-3092
# コミットメッセージに [round-trip:1] を含める
# PRタイトルに [round-trip:1] を含める
```

**関連ファイル**:
- .claude/CLAUDE.md
- .github/copilot-instructions.md
- .github/workflows/ci-backend-improved.yml
- .github/workflows/ci-cd.yml
- .github/workflows/post-merge-notify.yml
- .github/workflows/pr-quality-gate.yml
- docs/CLAUDECODE_PROMPTS_TEMPLATE.md

**期待効果**: Round-tripループの安定化、CI/CD品質向上

---

### High - 継続作業

#### 2. Issue #3098 - auto-error-fix-continuous重複チェック実装 [round-trip:1] 🔄

**優先度**: P1 - High
**作成日**: 2026-02-06
**Source-PR**: #3095
**Iteration**: 1 / 3
**変更ファイル**: 1ファイル（49行追加、1行削除）

**対応内容**:
- .github/workflows/auto-error-fix-continuous.yml の重複チェック実装の精製

**推奨アクション**:
```bash
# ブランチ作成: refinement/1/pr-3095
# テストカバレッジ確認
# エラーハンドリング強化
```

**期待効果**: 自動修復ワークフローの安定性向上

---

#### 3. Issue #3115 - エラーハンドリング強化 [round-trip:2] 🔄

**優先度**: P1 - High
**作成日**: 2026-02-09
**Source-PR**: #3110
**Iteration**: 2 / 3 (継続精製)
**変更ファイル**: 1ファイル（56行追加、35行削除）

**対応内容**:
- auto-error-fix-continuous.yml のエラーハンドリング強化（2回目の精製）

**推奨アクション**:
```bash
# ブランチ作成: refinement/2/pr-3110
# Issue #3098 の成果を統合
# 最終品質チェック
```

**期待効果**: Round-trip 2回目の品質向上

---

#### 4. Issue #3116 - Round-trip基盤エラーハンドリング強化 [round-trip:2] 🔄

**優先度**: P1 - High
**作成日**: 2026-02-09
**Source-PR**: #3111
**Iteration**: 2 / 3 (継続精製)
**変更ファイル**: 1ファイル（30行追加、15行削除）

**対応内容**:
- post-merge-notify.yml のエラーハンドリング強化（2回目の精製）

**推奨アクション**:
```bash
# ブランチ作成: refinement/2/pr-3111
# Issue #3093 の成果を統合
# ループ防止機構の検証
```

**期待効果**: Round-trip 2回目の品質向上

---

#### 5. Issue #3117 - console.log削除（E-3） [round-trip:1] 🔄

**優先度**: P1 - High
**作成日**: 2026-02-09
**Source-PR**: #3113 (マージ済み)
**Iteration**: 1 / 3
**変更ファイル**: 5ファイル（PWA関連JS）

**対応内容**:
- PWAモジュールのconsole.log削除の精製
- セキュアロガー導入確認

**推奨アクション**:
```bash
# ブランチ作成: refinement/1/pr-3113
# セキュアロガー完全移行確認
# 本番環境デバッグ機能確認
```

**期待効果**: 本番環境セキュリティ向上

---

### Low - 情報確認

#### 6. Issue #3118 - 自動修復レポート（2026-02-09） 📊

**優先度**: P3 - Low
**作成日**: 2026-02-09
**タイプ**: 自動生成レポート
**ラベル**: auto-fix, error-detected

**対応内容**:
- エラー15件検出・修復15件実行
- ループ回数: 15 / 15

**推奨アクション**:
```bash
# アーティファクトダウンロード: error-fix-results-3184
# レポート確認後、Issueをクローズ
```

**期待効果**: 自動修復システムの動作確認

---

## 🔄 Phase 2: PR整理

### 即時マージ推奨（最新7件）

#### グループA: 緊急修正・最適化（CI/CD通過確認後マージ）

| PR# | タイトル | ブランチ | 作成日 | 優先度 | マージ条件 |
|-----|---------|----------|--------|--------|-----------|
| #3107 | Phase 0緊急止血 - pytest環境修復 | feature/phase-0-emergency-fix | 2026-02-09 | P0 | CI通過後即時 |
| #3108 | セキュリティ脆弱性修正 - shell=True | feature/phase-1-security-fix | 2026-02-09 | P0 | セキュリティ検証後 |
| #3109 | N+1クエリ最適化 - 96.7%改善 | feature/phase-2-n1-optimization | 2026-02-09 | P1 | パフォーマンステスト後 |

**マージ順序**: #3107 → #3108 → #3109（依存関係順）

**期待効果**:
- CI/CD成功率: 18% → 60%+
- セキュリティスコア: A- (92) → A+ (98)
- レスポンスタイム: 15-40秒 → 0.2-0.6秒

---

#### グループB: テスト改善（並行マージ可）

| PR# | タイトル | ブランチ | 作成日 | 優先度 | マージ条件 |
|-----|---------|----------|--------|--------|-----------|
| #3112 | E2Eテスト安定化 - 成功率100% | feature/phase-2-e2e-stabilization | 2026-02-09 | P1 | E2Eテスト確認後 |
| #3103 | E2Eテスト修正 + CSP violation解消 | feature/fix-e2e-tests | 2026-02-07 | P2 | #3112マージ後統合 |

**マージ順序**: #3112 → #3103（または#3103をクローズ）

**注意**: #3112が#3103の改善版の可能性あり。差分確認後、重複している場合は#3103をクローズ。

---

#### グループC: 機能追加（レビュー・テスト後マージ）

| PR# | タイトル | ブランチ | 作成日 | 優先度 | マージ条件 |
|-----|---------|----------|--------|--------|-----------|
| #3114 | MS365ファイルプレビューPWA統合 | feature/phase-3-ms365-file-preview | 2026-02-09 | P2 | E2Eテスト追加後 |
| #3106 | Phase E-2完了 - N+1最適化 | feature/e2-n-plus-1-detection | 2026-02-07 | P2 | #3109マージ後確認 |

**注意**: #3106と#3109は同じN+1最適化。差分確認後、重複している場合は片方をクローズ。

---

### 古いPR（2〜4週間前）- クローズ推奨

#### グループD: Copilot生成PR（クローズ候補）

| PR# | タイトル | 作成日 | 経過日数 | 推奨アクション | 理由 |
|-----|---------|--------|---------|---------------|------|
| #2843 | Update workflow name to 10min | 2026-02-02 | 8日 | クローズ | より新しいワークフロー修正済み |
| #2842 | Fix auto-error-fix concurrent | 2026-02-02 | 8日 | クローズ | より新しいワークフロー修正済み |
| #2650 | Add auto-error-detection spec | 2026-01-31 | 10日 | クローズ | ドキュメント既存または不要 |
| #2648 | Verify auto error detection | 2026-01-31 | 10日 | クローズ | 検証完了済み |
| #880 | Add workflow_run monitoring | 2026-01-12 | 29日 | クローズ | より新しいワークフロー実装済み |
| #585 | Store non-numeric resource IDs | 2026-01-09 | 32日 | クローズまたはマージ | 機能が必要か確認 |
| #580 | Remove npm cache config | 2026-01-09 | 32日 | クローズ | CI設定変更済み |

**推奨アクション**:
```bash
# 各PRをレビューして、以下のいずれかを実行:
# 1. 機能が既に実装済み → クローズ
# 2. 機能が不要 → クローズ
# 3. 機能が必要 → 最新mainにリベース後マージ
```

---

## 🌿 Phase 3: ブランチクリーンアップ

### 削除推奨ブランチ（マージ済みまたは不要）

#### カテゴリA: 古いCopilotブランチ（削除推奨）

```bash
# PRがクローズ済みまたは古いブランチ
origin/copilot/add-concurrent-execution-control
origin/copilot/fix-concurrent-execution-issues
origin/copilot/fix-log-access-function
origin/copilot/implement-auto-error-detection
origin/copilot/remove-npm-cache-step
origin/copilot/update-auto-error-detection-system
origin/copilot/update-error-detection-system
```

**削除コマンド**:
```bash
git push origin --delete copilot/add-concurrent-execution-control
git push origin --delete copilot/fix-concurrent-execution-issues
git push origin --delete copilot/fix-log-access-function
git push origin --delete copilot/implement-auto-error-detection
git push origin --delete copilot/remove-npm-cache-step
git push origin --delete copilot/update-auto-error-detection-system
git push origin --delete copilot/update-error-detection-system
```

---

#### カテゴリB: マージ済みfeatureブランチ（削除推奨）

```bash
# PR #3113がマージ済み
origin/feature/phase-2-console-log-removal
```

**削除コマンド**:
```bash
git push origin --delete feature/phase-2-console-log-removal
```

---

#### カテゴリC: 保留中featureブランチ（マージ後削除）

```bash
# 現在オープンなPRに紐づくブランチ（PRマージ後に削除）
origin/feature/phase-0-emergency-fix          # PR #3107
origin/feature/phase-1-security-fix           # PR #3108
origin/feature/phase-2-e2e-stabilization      # PR #3112
origin/feature/phase-2-n1-optimization        # PR #3109
origin/feature/phase-3-ms365-file-preview     # PR #3114
origin/feature/e2-n-plus-1-detection          # PR #3106
origin/feature/fix-e2e-tests                  # PR #3103
```

**削除タイミング**: 各PRマージ後

---

#### カテゴリD: 調査が必要なブランチ

```bash
# PRが存在しないまたは古いブランチ
origin/feature/notifications-tests-5100       # PR存在確認要
origin/feature/phase-d4.2-file-preview        # Phase D-4.2関連、確認要
origin/feature/phase-d6-security-performance-optimization  # Phase D-6関連、確認要
origin/feature/e4-ms365-file-preview          # MS365関連、#3114と重複？
```

**推奨アクション**:
```bash
# 各ブランチの内容を確認
git log origin/feature/notifications-tests-5100 --oneline -10
git log origin/feature/phase-d4.2-file-preview --oneline -10
git log origin/feature/phase-d6-security-performance-optimization --oneline -10
git log origin/feature/e4-ms365-file-preview --oneline -10

# 不要と判断した場合は削除
```

---

## 📋 実行チェックリスト

### Phase 1: Issue整理（1日目）

- [ ] Issue #3093 - Round-trip基盤実装 [round-trip:1] を着手
- [ ] Issue #3098 - auto-error-fix-continuous [round-trip:1] を着手
- [ ] Issue #3118 - 自動修復レポート確認・クローズ
- [ ] Issue #3115, #3116, #3117 を継続監視

### Phase 2: PR整理（2-3日目）

#### 緊急マージ（2日目午前）
- [ ] PR #3107 - Phase 0緊急止血（CI通過確認後マージ）
- [ ] PR #3108 - セキュリティ脆弱性修正（セキュリティ検証後マージ）
- [ ] PR #3109 - N+1クエリ最適化（パフォーマンステスト後マージ）

#### テスト改善（2日目午後）
- [ ] PR #3112 - E2Eテスト安定化（E2Eテスト確認後マージ）
- [ ] PR #3103 - E2Eテスト修正（#3112と差分確認、重複ならクローズ）

#### 機能追加（3日目）
- [ ] PR #3114 - MS365プレビューPWA統合（E2Eテスト追加後マージ）
- [ ] PR #3106 - Phase E-2完了（#3109と差分確認、重複ならクローズ）

#### 古いPRクローズ（3日目午後）
- [ ] PR #2843, #2842, #2650, #2648, #880, #585, #580 - レビュー後クローズまたはマージ

### Phase 3: ブランチクリーンアップ（4日目）

#### Copilotブランチ削除
- [ ] copilot/* ブランチ7本削除

#### マージ済みブランチ削除
- [ ] feature/phase-2-console-log-removal 削除

#### PRマージ後のブランチ削除
- [ ] feature/phase-0-emergency-fix 削除（PR #3107マージ後）
- [ ] feature/phase-1-security-fix 削除（PR #3108マージ後）
- [ ] feature/phase-2-e2e-stabilization 削除（PR #3112マージ後）
- [ ] feature/phase-2-n1-optimization 削除（PR #3109マージ後）
- [ ] feature/phase-3-ms365-file-preview 削除（PR #3114マージ後）
- [ ] feature/e2-n-plus-1-detection 削除（PR #3106マージ後またはクローズ後）
- [ ] feature/fix-e2e-tests 削除（PR #3103マージ後またはクローズ後）

#### 調査ブランチ
- [ ] feature/notifications-tests-5100 内容確認・削除判断
- [ ] feature/phase-d4.2-file-preview 内容確認・削除判断
- [ ] feature/phase-d6-security-performance-optimization 内容確認・削除判断
- [ ] feature/e4-ms365-file-preview 内容確認・削除判断

---

## 📊 期待効果

### 完了後の状態

| 項目 | 現状 | 目標 | 改善率 |
|------|------|------|--------|
| オープンIssue | 6件 | 2-3件 | 50-66%削減 |
| オープンPR | 14件 | 0-2件 | 86-100%削減 |
| リモートブランチ | 20件+ | 4-6件 | 70-80%削減 |

### 品質向上

- CI/CD成功率: 18% → 60%+（238%改善）
- セキュリティスコア: A- (92) → A+ (98)
- レスポンスタイム: 15-40秒 → 0.2-0.6秒（96.7%改善）
- E2Eテスト成功率: 73% → 100%

### メンテナンス性向上

- ブランチ一覧の可視性向上
- PRレビュー負荷軽減
- Round-tripループの安定稼働

---

## ⚠️ 注意事項

1. **マージ前の確認事項**
   - CI/CD全体が通過していること
   - コンフリクトが解消されていること
   - レビューが完了していること

2. **ブランチ削除前の確認事項**
   - PRが完全にマージまたはクローズされていること
   - ローカルブランチとリモートブランチの同期確認
   - 削除後の復旧が不要であることを確認

3. **Round-tripループの継続**
   - Issue #3093, #3098, #3115, #3116, #3117 は継続精製
   - 最大3イテレーションまで実行
   - 各イテレーションで品質向上を確認

4. **緊急時のロールバック**
   - マージ後に問題が発生した場合は即座にrevert
   - ブランチ削除は git reflog で復旧可能（30日間）

---

## 🔍 次回レビュー

**推奨日時**: 2026-02-14（4日後）
**確認項目**:
- Issue/PR数の推移
- CI/CD成功率の推移
- Round-tripループの進捗
- ブランチクリーンアップの完了状況

---

**作成者**: ClaudeCode
**最終更新**: 2026-02-10
**ステータス**: 実行待ち
