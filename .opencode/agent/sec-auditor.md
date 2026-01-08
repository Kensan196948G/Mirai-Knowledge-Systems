---
name: sec-auditor
mode: subagent
description: >
  セキュリティ・Lint・権限レビューに特化したサブエージェント。
  IAM・シークレット管理・危険なコマンド・GitHub Actions の permissions 設定などを重点的にチェックする。
model: claude-4.5-opus
temperature: 0.2

# 旧:
# tools:
#   edit: ask
#   bash: deny
#   webfetch: allow
# permissions:
#   files:
#     allow:
#       - ".github/**"
#       - "infra/**"
#       - "k8s/**"
#       - "terraform/**"
#       - "config/**"
#       - "**/*.tf"
#       - "**/*.yml"
#       - "**/*.yaml"
#       - "README.md"
#   bash:
#     "*": deny
#   webfetch:
#     "*": allow

# 新: OpenCode の permission 形式に集約
permission:
  edit: "ask"        # ファイル編集は毎回確認
  bash: "deny"       # bash は原則禁止
  webfetch: "allow"  # webfetch は許可
  read:
    ".github/**": "allow"
    "infra/**": "allow"
    "k8s/**": "allow"
    "terraform/**": "allow"
    "config/**": "allow"
    "**/*.tf": "allow"
    "**/*.yml": "allow"
    "**/*.yaml": "allow"
    "README.md": "allow"
---

# Security Auditor
...
