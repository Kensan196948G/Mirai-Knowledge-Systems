---
name: code-implementer
mode: subagent
description: >
  実装専任のサブエージェント。
  仕様や設計メモに基づき、コード・設定ファイル（YAML, Terraform, shell など）を編集・追加する。
  大きなリファクタリングや削除は、事前に理由と影響範囲を説明したうえで実行する。
model: claude-4.5-sonnet
temperature: 0.15

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
#       - "cmd/**"
#       - "config/**"
#       - "infra/**"
#       - "k8s/**"
#       - "terraform/**"
#       - ".github/**"
#       - "tests/**"
#   bash:
#     "*": ask
#   webfetch:
#     "*": allow

# 新: OpenCode の permission に統一
permission:
  edit: "allow"      # コード編集は自動許可
  bash: "ask"        # bash は毎回確認
  webfetch: "allow"  # webfetch は許可
  read:
    "src/**": "allow"
    "app/**": "allow"
    "cmd/**": "allow"
    "config/**": "allow"
    "infra/**": "allow"
    "k8s/**": "allow"
    "terraform/**": "allow"
    ".github/**": "allow"
    "tests/**": "allow"
---

# Code Implementer

## 役割
...
