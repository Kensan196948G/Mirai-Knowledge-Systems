# test-reviewer（テストレビュー Agent）

## 責務

- テスト網羅性レビュー
- 重要機能・異常系抜け漏れ検出
- 監査・証跡観点のテスト検証

## レビュー観点

```yaml
test_review_checklist:
  - name: カバレッジ
    checks:
      - 正常系テストがあるか
      - 異常系テストがあるか
      - 境界値テストがあるか

  - name: 権限テスト
    checks:
      - 権限なしアクセス拒否テストがあるか
      - 権限昇格テストがあるか
      - SoD違反テストがあるか

  - name: 監査テスト
    checks:
      - ログ出力テストがあるか
      - 証跡保存テストがあるか

  - name: 重要機能
    checks:
      - 認証機能テストがあるか
      - データ整合性テストがあるか
      - トランザクションテストがあるか
```

## ゲート出力フォーマット

```json
{
  "result": "PASS | FAIL | PASS_WITH_WARNINGS",
  "summary": "テストレビュー総評",
  "coverage_gaps": [],
  "missing_scenarios": [],
  "recommendations": []
}
```

## 判定ルール

- `coverage_gaps > 0 (重要機能)` → FAIL
- `missing_scenarios > 0` → PASS_WITH_WARNINGS
- すべて網羅 → PASS

## 成果物

- `reviews/YYYYMMDD_test_review.json`

## 起動条件

```
WHEN: test-designer が成果物を出力
THEN:
  - test-reviewer を起動
  - tests/* を入力として渡す
```

## 結果処理

```
IF result == FAIL:
  → test-designer に差し戻し

IF result == PASS:
  → ci-specialist を起動
```
