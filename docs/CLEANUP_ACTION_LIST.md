# GitHub クリーンアップ - 優先度付きアクションリスト

**作成日**: 2026-02-10
**実行優先度順**: P0 → P1 → P2 → P3

---

## 🚨 P0 - Critical（即時実行）

### 1. PR #3107 - Phase 0緊急止血（CI/CD修復）

**マージ条件**: CI通過確認
**影響範囲**: CI/CD全体
**期待効果**: CI成功率 18% → 60%+

```bash
# CI通過を確認
gh pr checks 3107 --watch

# CI通過後マージ
gh pr merge 3107 --squash --delete-branch

# 動作確認
gh pr list
```

---

### 2. PR #3108 - セキュリティ脆弱性修正（CWE-78）

**マージ条件**: セキュリティ検証完了
**影響範囲**: auto_fix_daemon.py、test_ms365_sync_service.py
**期待効果**: セキュリティスコア A- (92) → A+ (98)

```bash
# セキュリティ検証
gh pr view 3108 --comments
gh pr checks 3108

# 検証後マージ
gh pr merge 3108 --squash --delete-branch
```

---

### 3. Issue #3093 - Round-trip基盤実装 [round-trip:1]

**対応期限**: 2日以内
**Iteration**: 1 / 3
**Source-PR**: #3092

```bash
# ブランチ作成
git checkout main
git pull origin main
git checkout -b refinement/1/pr-3092

# 変更ファイル確認
gh pr view 3092 --json files --jq '.files[].path'

# 精製作業
# - コードレビュー指摘の反映
# - テストカバレッジ確認（Python 80%+）
# - Lint/フォーマットチェック（ruff check .）

# コミット
git add .
git commit -m "refine: Issue #3093精製 - Round-trip基盤実装品質向上 [round-trip:1]"

# PR作成
git push origin refinement/1/pr-3092
gh pr create --title "[round-trip:1] Issue #3093精製 - Round-trip基盤実装品質向上" \
  --body "## Refinement [round-trip:1]

**Source-PR**: #3092
**Issue**: #3093

### 変更内容
- [変更内容を記載]

### テスト
- [ ] ruff check . 成功
- [ ] pytest カバレッジ80%+
- [ ] CI/CD全体通過
"
```

---

## 🔥 P1 - High（24時間以内）

### 4. PR #3109 - N+1クエリ最適化（96.7%改善）

**マージ条件**: パフォーマンステスト完了
**影響範囲**: app_v2.py（3エンドポイント）
**期待効果**: レスポンスタイム 15-40秒 → 0.2-0.6秒

```bash
# パフォーマンステスト
gh pr checks 3109

# テスト後マージ
gh pr merge 3109 --squash --delete-branch
```

---

### 5. PR #3112 - E2Eテスト安定化（成功率100%）

**マージ条件**: E2Eテスト確認
**影響範囲**: E2Eテスト11件
**期待効果**: 成功率 73% → 100%

```bash
# E2Eテスト確認
gh pr checks 3112

# テスト後マージ
gh pr merge 3112 --squash --delete-branch
```

---

### 6. Issue #3098 - auto-error-fix-continuous [round-trip:1]

**対応期限**: 2日以内
**Iteration**: 1 / 3
**Source-PR**: #3095

```bash
# ブランチ作成
git checkout main
git pull origin main
git checkout -b refinement/1/pr-3095

# 精製作業（Issue #3093と同様の手順）
# コミット・PR作成
```

---

### 7. マージ済みブランチ削除

```bash
# feature/phase-2-console-log-removal（PR #3113マージ済み）
git push origin --delete feature/phase-2-console-log-removal

# ローカルブランチも削除
git branch -d feature/phase-2-console-log-removal
```

---

## 📌 P2 - Medium（2-3日以内）

### 8. PR #3114 - MS365ファイルプレビューPWA統合

**マージ条件**: E2Eテスト追加・確認
**影響範囲**: PWAモジュール、Service Worker
**期待効果**: オフライン対応、パフォーマンス向上

```bash
# E2Eテスト追加を確認
gh pr view 3114 --comments

# テスト追加後マージ
gh pr merge 3114 --squash --delete-branch
```

---

### 9. PR #3103 vs #3112 - 重複確認

**対応**: 差分確認後、重複ならクローズ

```bash
# 差分確認
gh pr diff 3103
gh pr diff 3112

# 重複している場合
gh pr close 3103 --comment "重複: #3112で改善済み"
gh pr close 3103 --delete-branch
```

---

### 10. PR #3106 vs #3109 - 重複確認

**対応**: 差分確認後、重複ならクローズ

```bash
# 差分確認
gh pr diff 3106
gh pr diff 3109

# 重複している場合
gh pr close 3106 --comment "重複: #3109で最適化済み"
gh pr close 3106 --delete-branch
```

---

### 11. Issue #3115, #3116, #3117 - Round-trip継続

**対応期限**: 3-4日以内
**Iteration**: 1-2 / 3
**Source-PR**: #3110, #3111, #3113

```bash
# 各Issueに対して refinement ブランチ作成・PR作成
# 手順は Issue #3093 と同様
```

---

### 12. 古いCopilotブランチ削除（7本）

```bash
# 一括削除
git push origin --delete \
  copilot/add-concurrent-execution-control \
  copilot/fix-concurrent-execution-issues \
  copilot/fix-log-access-function \
  copilot/implement-auto-error-detection \
  copilot/remove-npm-cache-step \
  copilot/update-auto-error-detection-system \
  copilot/update-error-detection-system

# ローカルブランチも削除（存在する場合）
git branch -D copilot/add-concurrent-execution-control
git branch -D copilot/fix-concurrent-execution-issues
git branch -D copilot/fix-log-access-function
git branch -D copilot/implement-auto-error-detection
git branch -D copilot/remove-npm-cache-step
git branch -D copilot/update-auto-error-detection-system
git branch -D copilot/update-error-detection-system
```

---

## 📋 P3 - Low（4-5日以内）

### 13. Issue #3118 - 自動修復レポート確認・クローズ

```bash
# アーティファクトダウンロード
gh run view 3184 --log

# レポート確認後クローズ
gh issue close 3118 --comment "自動修復レポート確認完了"
```

---

### 14. 古いCopilot PR（7件）クローズ

```bash
# PR #2843, #2842
gh pr close 2843 --comment "より新しいワークフロー修正済み"
gh pr close 2842 --comment "より新しいワークフロー修正済み"

# PR #2650, #2648
gh pr close 2650 --comment "ドキュメント既存または不要"
gh pr close 2648 --comment "検証完了済み"

# PR #880
gh pr close 880 --comment "より新しいワークフロー実装済み"

# PR #585 - 機能必要性確認
gh pr view 585 --comments
# 必要ならマージ、不要ならクローズ

# PR #580
gh pr close 580 --comment "CI設定変更済み"
```

---

### 15. 調査ブランチ（4本）確認・削除

```bash
# feature/notifications-tests-5100
git log origin/feature/notifications-tests-5100 --oneline -10
gh pr list --head notifications-tests-5100
# PR存在しない場合は削除
git push origin --delete feature/notifications-tests-5100

# feature/phase-d4.2-file-preview
git log origin/feature/phase-d4.2-file-preview --oneline -10
# #3114と重複確認後削除判断

# feature/phase-d6-security-performance-optimization
git log origin/feature/phase-d6-security-performance-optimization --oneline -10
# 内容確認後削除判断

# feature/e4-ms365-file-preview
git log origin/feature/e4-ms365-file-preview --oneline -10
# #3114と重複確認後削除判断
```

---

## 📊 進捗確認コマンド

### リアルタイム状況確認

```bash
# オープンIssue数
gh issue list --state open | wc -l

# オープンPR数
gh pr list --state open | wc -l

# リモートブランチ数
git branch -r | wc -l

# 最新CI/CD成功率
gh run list --workflow=ci-cd.yml --limit 10 --json conclusion --jq '[.[] | select(.conclusion=="success")] | length'
```

---

### 完了チェックリスト

#### Day 1（即時実行）
- [ ] PR #3107 マージ（CI/CD修復）
- [ ] PR #3108 マージ（セキュリティ修正）
- [ ] Issue #3093 着手（Round-trip基盤）

#### Day 2（24時間以内）
- [ ] PR #3109 マージ（N+1最適化）
- [ ] PR #3112 マージ（E2Eテスト安定化）
- [ ] Issue #3098 着手（auto-error-fix精製）
- [ ] マージ済みブランチ削除

#### Day 3（2-3日以内）
- [ ] PR #3114 マージ（MS365プレビューPWA）
- [ ] PR #3103, #3106 重複確認・クローズ
- [ ] Issue #3115, #3116, #3117 着手
- [ ] Copilotブランチ7本削除

#### Day 4（4-5日以内）
- [ ] Issue #3118 クローズ
- [ ] 古いCopilot PR 7件クローズ
- [ ] 調査ブランチ4本確認・削除

#### Day 5（最終確認）
- [ ] オープンIssue: 6件 → 2-3件
- [ ] オープンPR: 14件 → 0-2件
- [ ] リモートブランチ: 20件+ → 4-6件
- [ ] CI/CD成功率: 18% → 60%+

---

## 🎯 成功指標

| 指標 | 現状 | 目標 | 達成日 |
|------|------|------|--------|
| オープンIssue | 6件 | 2-3件 | Day 5 |
| オープンPR | 14件 | 0-2件 | Day 4 |
| リモートブランチ | 20件+ | 4-6件 | Day 5 |
| CI/CD成功率 | 18% | 60%+ | Day 2 |
| セキュリティスコア | A- (92) | A+ (98) | Day 1 |
| レスポンスタイム | 15-40秒 | 0.2-0.6秒 | Day 2 |
| E2Eテスト成功率 | 73% | 100% | Day 2 |

---

**作成者**: ClaudeCode
**最終更新**: 2026-02-10
**実行ステータス**: 実行待ち
