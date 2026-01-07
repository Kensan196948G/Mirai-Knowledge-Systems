# Claude Code プロンプトテンプレート集

## 概要

Mirai Knowledge Systems 本番開発用のプロンプトテンプレート集です。
開発・保守・トラブルシューティングの各シーンに対応したプロンプトを提供します。

## 使用方法

各プロンプトファイルの内容をClaude Codeセッション開始時に貼り付けて使用してください。

## テンプレート一覧

| ファイル | 用途 | 主な機能 |
|----------|------|----------|
| `development.md` | 機能開発 | 新機能実装、リファクタリング |
| `maintenance.md` | 保守作業 | バグ修正、依存関係更新 |
| `troubleshooting.md` | 障害対応 | エラー調査、復旧作業 |
| `database.md` | DB操作 | マイグレーション、データ移行 |
| `testing.md` | テスト | テスト作成、カバレッジ向上 |
| `deployment.md` | デプロイ | 本番リリース、ロールバック |

## ディレクトリ構造

```
.claude/prompts/
├── README.md           # このファイル
├── development.md      # 開発作業用
├── maintenance.md      # 保守作業用
├── troubleshooting.md  # 障害対応用
├── database.md         # データベース操作用
├── testing.md          # テスト作業用
└── deployment.md       # デプロイ作業用
```

## 更新履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|----------|
| 2026-01-07 | 1.0 | 初版作成 |
