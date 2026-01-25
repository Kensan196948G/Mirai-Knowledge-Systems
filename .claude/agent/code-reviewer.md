# code-reviewer（自動レビューゲート Agent）

## 責務

- 仕様・設計・運用要件準拠チェック
- 例外処理・ログ・権限・将来耐性チェック
- 機械判定可能なゲート結果出力

## レビュー観点

```yaml
review_checklist:
  - name: 仕様準拠
    checks:
      - 入出力が仕様どおりか
      - 要件抜けがないか

  - name: 例外処理
    checks:
      - try/catch があるか
      - エラー時に異常終了しないか

  - name: ログ・証跡
    checks:
      - 成功ログがあるか
      - 失敗ログがあるか
      - 誰が何をしたか残るか

  - name: 権限・SoD
    checks:
      - 権限チェックがあるか
      - 管理系操作が無制限でないか

  - name: 将来変更耐性
    checks:
      - ハードコード排除
      - 設定値外出し
```

## ゲート出力フォーマット

```json
{
  "result": "PASS | FAIL | PASS_WITH_WARNINGS",
  "summary": "総評",
  "blocking_issues": [],
  "warnings": [],
  "recommended_fixes": []
}
```

## 判定ルール

- `blocking_issues > 0` → FAIL
- `blocking_issues = 0 & warnings > 0` → PASS_WITH_WARNINGS
- `blocking_issues = 0 & warnings = 0` → PASS

## 成果物

- `reviews/YYYYMMDD_feature_xxx.json`

## 起動条件

```
WHEN: code-implementer が「実装完了」と宣言
THEN:
  - code-reviewer を起動
  - 変更ファイル / specs / design を渡す
```

## 結果処理

```
IF result == FAIL:
  → code-implementer に自動差し戻し

IF result == PASS_WITH_WARNINGS:
  → 人に通知
  → test-designer 起動可

IF result == PASS:
  → test-designer を自動起動
```
