---
name: commit-push-pr
description: 変更をコミットし、リモートにプッシュし、プルリクエストを作成します。ユーザーが「コミットしてPR作成」「変更をプッシュしてPR」などと指示した際に使用します。
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

# Commit-Push-PR Skill

このスキルは、Git操作のワークフロー（コミット→プッシュ→PR作成）を自動化します。

## 実行手順

### 1. 変更の確認

まず、現在の変更状況を確認します：

```bash
git status
git diff
git log -3 --oneline
```

### 2. 変更のステージングとコミット

変更をステージングし、適切なコミットメッセージでコミットします：

```bash
# 変更をステージング
git add <変更されたファイル>

# コミット（適切なメッセージで）
git commit -m "$(cat <<'EOF'
<コミットメッセージ>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 (1M context) <noreply@anthropic.com>
EOF
)"
```

### 3. リモートへプッシュ

現在のブランチをリモートにプッシュします：

```bash
# 新しいブランチの場合は -u オプションを付ける
git push -u origin <branch-name>

# 既存のブランチの場合
git push
```

### 4. プルリクエストの作成

GitHub CLIを使用してPRを作成します：

```bash
gh pr create --title "<PR タイトル>" --body "$(cat <<'EOF'
## 概要
<変更内容の要約>

## 変更詳細
<詳細な説明>

## テスト計画
- [ ] <テスト項目1>
- [ ] <テスト項目2>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

## 重要な注意事項

### コミットメッセージの作成

- 変更の「なぜ」を重視した簡潔なメッセージ（1-2文）
- プロジェクトの既存のコミットスタイルに従う
- 日本語または英語（プロジェクトの慣例に合わせる）

### PR本文の作成

- 全ての関連コミット（最新だけでなく）を分析してPR全体の概要を作成
- `git log [base-branch]...HEAD`と`git diff [base-branch]...HEAD`で変更範囲を確認
- 概要は1-3箇条書き
- テスト計画をチェックリストで提供

### セキュリティ

- `.env`、`credentials.json`などの機密ファイルはコミットしない
- pre-commitフックが失敗した場合は、修正後に新しいコミットを作成（amendは使用しない）
- force pushは使用しない（ユーザーが明示的に要求した場合を除く）

## 使用例

```
ユーザー: 「変更をコミットしてPR作成して」
→ このスキルが自動的に適用され、上記の手順を実行
```

## 実行後

PRのURLをユーザーに提示します。
