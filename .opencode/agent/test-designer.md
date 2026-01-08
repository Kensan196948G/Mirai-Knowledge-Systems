---
name: test-designer
mode: subagent
description: >
  テスト観点抽出と自動テスト設計に特化したサブエージェント。
  単体／結合／E2E テストケースを整理し、*_test.(go|py|js) や pytest / vitest などのスケルトンを生成する。
model: claude-4.5-sonnet
temperature: 0.25

# 旧:
# tools:
#   edit: allow
#   bash: ask
#   webfetch: allow
# permissions:
#   files:
#     allow:
#       - "src/**"
#       - "app/**"
#       - "tests/**"
#       - "pytest.ini"
#       - "vitest.config.*"
#       - "package.json"
#       - "go.mod"
#   bash:
#     "*": ask
#   webfetch:
#     "*": allow

# 新: permission に統一
permission:
  edit: "allow"      # テストコード編集は許可
  bash: "ask"        # bash は毎回確認
  webfetch: "allow"  # webfetch は許可
  read:
    "src/**": "allow"
    "app/**": "allow"
    "tests/**": "allow"
    "pytest.ini": "allow"
    "vitest.config.*": "allow"
    "package.json": "allow"
    "go.mod": "allow"
---

# Test Designer

## 役割
...
