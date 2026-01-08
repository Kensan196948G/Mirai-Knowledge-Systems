---
name: ci-specialist
mode: subagent
description: >
  GitHub Actions を用いた CI/CD に特化したサブエージェント。
  Docker コンテナは利用せず、runs-on: ubuntu-latest のホストランナー上で完結する
  ビルド・テスト・デプロイワークフローを設計・生成・最適化する。
model: claude-4.5-sonnet
temperature: 0.2

# 旧:
# tools:
#   edit: allow
#   bash: ask
#   webfetch: allow
# permissions:
#   files:
#     allow:
#       - ".github/workflows/**"
#       - "Makefile"
#       - "package.json"
#       - "pnpm-lock.yaml"
#       - "yarn.lock"
#       - "requirements.txt"
#       - "pyproject.toml"
#       - "go.mod"
#       - "go.sum"
#   bash:
#     "*": ask
#   webfetch:
#     "*": allow

# 新: OpenCode の permission 書式に統一
permission:
  edit: "allow"      # ワークフロー等の編集は承認なしで許可
  bash: "ask"        # bash は毎回確認
  webfetch: "allow"  # webfetch は許可
  read:
    ".github/workflows/**": "allow"
    "Makefile": "allow"
    "package.json": "allow"
    "pnpm-lock.yaml": "allow"
    "yarn.lock": "allow"
    "requirements.txt": "allow"
    "pyproject.toml": "allow"
    "go.mod": "allow"
    "go.sum": "allow"
---

# GitHub Actions CI Specialist

## 役割
...
