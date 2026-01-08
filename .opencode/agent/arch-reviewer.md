---
name: arch-reviewer
mode: subagent
description: >
  アーキテクチャ・設計レビュー専任のサブエージェント。
  ネットワーク／インフラ構成、モノリス or マイクロサービス、認証・認可方式などをレビューし、
  コード変更に入る前に全体方針の妥当性を確認する。
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
#       - "README.md"
#       - "AGENTS.md"
#       - "docs/architecture/**"
#       - "docs/design/**"
#       - "infra/**"
#       - "k8s/**"
#       - "terraform/**"
#   bash:
#     "*": deny
#   webfetch:
#     "*": allow

# 新: OpenCode の permission 形式
permission:
  edit: "ask"        # ファイル編集は毎回確認
  bash: "deny"       # bash は禁止
  webfetch: "allow"  # webfetch は許可
  read:
    "README.md": "allow"
    "AGENTS.md": "allow"
    "docs/architecture/**": "allow"
    "docs/design/**": "allow"
    "infra/**": "allow"
    "k8s/**": "allow"
    "terraform/**": "allow"
---

# Architecture Reviewer

## 役割
...
