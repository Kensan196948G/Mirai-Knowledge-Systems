---
name: commit-push-pr-merge
description: 変更をコミットし、リモートにプッシュし、プルリクエストを作成して、即座にマージします。ユーザーが「コミットしてPR作成してマージ」「変更をマージまで完了」などと指示した際に使用します。緊急修正やホットフィックスに便利です。
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

# Commit-Push-PR-Merge Skill

このスキルは、Git操作のワークフロー全体（コミット→プッシュ→PR作成→マージ）を自動化します。

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

### 5. PRのマージ

**⚠️ マージ前の確認事項：**

PRを作成した後、以下を確認してからマージします：

```bash
# PRの状態を確認
gh pr view

# CIチェックの状態を確認
gh pr checks
```

**マージ実行：**

全てのチェックが通過していることを確認後、マージを実行：

```bash
# マージ実行
gh pr merge --merge --delete-branch

# または、squash mergeの場合
# gh pr merge --squash --delete-branch

# または、rebase mergeの場合
# gh pr merge --rebase --delete-branch
```

**マージ後のクリーンアップ：**

```bash
# メインブランチに切り替え
git checkout main

# メインブランチを更新
git pull
```

## 重要な注意事項

### マージ戦略

プロジェクトのマージ戦略に従ってください：
- **Merge commit**: 履歴を保持（デフォルト）
- **Squash merge**: コミットを1つにまとめる
- **Rebase merge**: 線形履歴を維持

### セキュリティと安全性

- **main/masterブランチへの直接マージは慎重に**
- CI/CDチェックが失敗している場合はマージしない
- レビューが必要なプロジェクトでは、このスキルの使用前にユーザーに確認
- force pushは絶対に使用しない

### このスキルを使うべきケース

✅ **適切な使用例：**
- ホットフィックス（緊急バグ修正）
- タイポ修正
- ドキュメント更新
- 単純な設定変更
- 個人プロジェクト

❌ **避けるべきケース：**
- 複雑な機能追加（レビューが必要）
- 破壊的な変更
- チームレビューが必須のプロジェクト
- 本番環境に影響する重要な変更

### コミットメッセージの作成

- 変更の「なぜ」を重視した簡潔なメッセージ（1-2文）
- プロジェクトの既存のコミットスタイルに従う
- 日本語または英語（プロジェクトの慣例に合わせる）

### PR本文の作成

- 全ての関連コミット（最新だけでなく）を分析してPR全体の概要を作成
- `git log [base-branch]...HEAD`と`git diff [base-branch]...HEAD`で変更範囲を確認
- 概要は1-3箇条書き
- テスト計画をチェックリストで提供

## 使用例

```
ユーザー: 「タイポを修正してマージまで完了して」
→ このスキルが自動的に適用され、コミット→プッシュ→PR作成→マージを実行
```

## 実行後

マージ完了のメッセージとPRのURLをユーザーに提示します。
