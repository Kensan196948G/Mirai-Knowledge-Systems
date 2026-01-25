# Hooks 連携ルール（工程強制・並列・衝突防止）

## 工程遷移フロー

```
spec-planner → arch-reviewer → code-implementer → code-reviewer
                                                       ↓
                               ←←← FAIL ←←← [判定]
                                                       ↓ PASS
                                               test-designer → test-reviewer
                                                                      ↓
                                               ←←← FAIL ←←← [判定]
                                                                      ↓ PASS
                                                              ci-specialist
```

---

## Hook定義

### ① on-spec-complete

```yaml
trigger: spec-planner が成果物を出力
action:
  - arch-reviewer を自動起動
  - specs/* を入力として渡す
```

### ② on-arch-approved

```yaml
trigger: arch-reviewer が PASS を返却
action:
  - code-implementer を起動
  - design/* を入力として渡す
```

### ③ on-implementation-complete

```yaml
trigger: code-implementer が「実装完了」と宣言
action:
  - code-reviewer を起動
  - 変更ファイル / specs / design を渡す
```

### ④ on-code-review-result

```yaml
trigger: code-reviewer がレビュー結果を出力
actions:
  - IF result == FAIL:
      → code-implementer に自動差し戻し
  - IF result == PASS_WITH_WARNINGS:
      → 人に通知
      → test-designer 起動可
  - IF result == PASS:
      → test-designer を自動起動
```

### ⑤ on-test-design-complete

```yaml
trigger: test-designer が成果物を出力
action:
  - test-reviewer を起動
```

### ⑥ on-test-review-result

```yaml
trigger: test-reviewer がレビュー結果を出力
actions:
  - IF result == FAIL:
      → test-designer に差し戻し
  - IF result == PASS:
      → ci-specialist を起動
```

---

## 並列開発ルール（コンフリクト防止）

### 基本原則

- 各 SubAgent は **1ファイルツリーのみ** を担当
- 同一ファイルへの同時書き込みは **禁止**
- 共有設定は `config/*` に集約
- 競合発生時は `spec-planner` に強制エスカレーション

### ファイルツリー割り当て

| SubAgent | 担当ディレクトリ |
|----------|------------------|
| spec-planner | `specs/`, `requirements/` |
| arch-reviewer | `design/`, `docs/architecture/` |
| code-implementer | `src/`, `backend/`, `webui/` |
| code-reviewer | `reviews/` (読み取り: 全体) |
| test-designer | `tests/`, `test-cases/` |
| test-reviewer | `reviews/` (読み取り: `tests/`) |
| ci-specialist | `ci/`, `.github/workflows/` |
| sec-auditor | `security/`, `audits/` |
| ops-runbook | `runbook/`, `docs/operations/` |

### 並列実行時の必須ルール

**CRITICAL**: 並列実行時は必ず単一メッセージで複数Task tool呼び出しを実行

```
✅ 正しい例:
  1つのメッセージで3つのTask toolを同時呼び出し

❌ 間違った例:
  3つの連続メッセージでそれぞれTask toolを呼び出し
```

---

## 運用ポリシー（絶対ルール）

1. **工程スキップ禁止** - Hook を通らない遷移は禁止
2. **レビュー FAIL は必ず差し戻す** - 例外なし
3. **仕様外実装は禁止** - 設計に書いていないことは未実装扱い
4. **証跡保存必須** - すべての判断はログとして残す
5. **設計変更禁止** - 実装中の設計変更は spec-planner に戻す
