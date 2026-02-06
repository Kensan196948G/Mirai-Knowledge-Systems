# ClaudeCode Prompts Template - Round-trip Development Loop

往復開発ループの各フェーズでClaudeCodeが使用するプロンプトテンプレート集。

---

## 1. Issue解析テンプレート

Refinement Issueを受け取った際の初動解析に使用。

```
以下のRefinement Issueを解析してください。

Issue: #{issue_number}
タイトル: {issue_title}
イテレーション: {N} / 3

### 変更ファイル
{changed_files_list}

### チェックリスト
{checklist_items}

指示:
1. 変更ファイルを全て読み込み、現在の実装状態を把握
2. チェックリストの各項目について、対応が必要か判定
3. 対応が必要な項目をリストアップし、優先度順に並べ替え
4. 作業計画を提示（ファイルごとの変更概要）
```

---

## 2. テストカバレッジ改善テンプレート

テストカバレッジ不足を検出・改善する際に使用。

```
以下のファイルのテストカバレッジを改善してください。

対象ファイル: {target_files}
現在のカバレッジ: Python {python_coverage}%, JS {js_coverage}%
目標カバレッジ: Python 80%+, JS 70%+

指示:
1. pytest --cov で現在のカバレッジを確認
2. カバレッジが不足しているモジュール/関数を特定
3. 以下の優先順位でテストを追加:
   a. 未テストのエンドポイント/API
   b. エラーハンドリングパス
   c. 境界値・エッジケース
   d. 認証/権限チェック
4. 既存のconftest.pyのフィクスチャを活用
5. テスト命名規則: test_{対象機能}_{条件}_{期待結果}

テスト実行コマンド:
  pytest tests/ -v --tb=short --cov=. --cov-report=term-missing
  cd backend && npm run test:unit:coverage
```

---

## 3. コードリファインメントテンプレート

コード品質改善に使用。

```
以下のファイルのコード品質を改善してください。

対象ファイル: {target_files}
Source PR: #{source_pr_number}
イテレーション: [round-trip:{N}]

改善観点（優先度順）:
1. **セキュリティ**: XSS, SQLi, CSRF, 認証バイパスの可能性
2. **エラーハンドリング**: try/catch漏れ、不適切なエラーメッセージ
3. **命名・可読性**: 変数名、関数名の明確化
4. **重複排除**: DRY原則違反の解消
5. **型安全性**: 型ヒント追加（Python）、型チェック強化

注意事項:
- 機能変更は行わない（リファクタリングのみ）
- 既存テストが全てパスすることを確認
- ruff check . がクリーンであることを確認
- innerHTML は絶対に使わない（DOM API使用）
```

---

## 4. PR作成テンプレート

リファインメント完了後のPR作成に使用。

```
リファインメント作業が完了しました。PRを作成してください。

ブランチ名: refinement/{N}/pr-{source_pr_number}
ベースブランチ: main
イテレーション: [round-trip:{N}]

コミットメッセージ形式:
  {type}: {description} [round-trip:{N}]

  変更内容:
  - {change_1}
  - {change_2}

  Source: #{source_pr_number}

PRタイトル形式:
  [refinement] {original_pr_title} [round-trip:{N}]

PR本文テンプレート:
  ## Summary
  - Source PR: #{source_pr_number}
  - Iteration: {N} / 3
  - {1-3行の変更概要}

  ## Changes
  - {変更点リスト}

  ## Test Results
  - Python coverage: {python_coverage}%
  - JS coverage: {js_coverage}%
  - All tests passing: Yes/No

  ## Checklist
  - [ ] ruff check . passed
  - [ ] pytest passed (80%+ coverage)
  - [ ] Jest passed (70%+ coverage)
  - [ ] No security issues introduced
```

---

## 5. ループ終了判定テンプレート

イテレーション上限に近い場合の判定に使用。

```
現在のイテレーション: {N} / 3

以下を確認して、追加イテレーションが必要か判定してください:

1. 全てのチェックリスト項目が完了しているか
2. テストカバレッジが目標を達成しているか
3. Lintエラーが0件か
4. セキュリティ上の懸念が残っていないか

判定結果:
- 全て完了 → ループ終了（PRをマージ可能）
- 未完了項目あり & N < 3 → 次イテレーションで対応
- 未完了項目あり & N = 3 → 手動対応が必要な項目をIssueにまとめる
```

---

## 使用方法

1. GitHub上で `refinement-needed` ラベルのIssueを確認
2. テンプレート1（Issue解析）で初動解析
3. テンプレート2-3で実装作業
4. テンプレート4でPR作成
5. 必要に応じてテンプレート5でループ終了判定

## 関連ファイル

- `.github/workflows/pr-quality-gate.yml` - PR品質ゲート
- `.github/workflows/post-merge-notify.yml` - マージ後Issue自動作成
- `.github/copilot-instructions.md` - Copilot Agent指示書
- `.claude/CLAUDE.md` - 運用モード定義
