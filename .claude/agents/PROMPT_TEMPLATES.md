# 📝 即応型プロンプトテンプレート集

**作成日**: 2026-01-12
**対象**: Mirai Knowledge Systems
**目的**: 判断フェーズゼロでSubAgentチームを即起動

---

## 🎯 黄金構造（必須）

すべてのプロンプトは以下の順序を **必ず守る**：

```
1. 【目的】
2. 【起動Agent】
3. 【並列Hooks】
4. 【制約（コンフリクト防止）】
5. 【MCP使用指示】
6. 【期待する出力】
```

---

## 📋 テンプレート1：新機能追加（標準）

```
【目的】
〇〇機能を追加し、実装・テスト・CIまで整える

【起動Agent】
🧭 spec-planner
🏗 arch-reviewer
💻 code-implementer
🧪 test-designer
🚀 ci-specialist

【並列Hooks】
- spec-planner と arch-reviewer は並列
- test-designer も並列
- code-implementer は設計完了後
- ci-specialist は実装完了後

【制約（コンフリクト防止）】
- 編集は code-implementer のみ
- 他Agentは提案・確認のみ

【MCP使用指示】
- memory: 過去の設計決定を確認
- github: 類似実装を検索
- context7: 使用ライブラリのドキュメント確認

【期待する出力】
- 設計要点（spec-planner）
- 既存構造分析（arch-reviewer）
- 実装差分（code-implementer）
- テストスケルトン（test-designer）
- CI変更点（ci-specialist）
```

---

## 📋 テンプレート2：バグ修正（完全並列）

```
【目的】
〇〇のバグを修正

【起動Agent】
💻 code-implementer（修正）
🧪 test-designer（再現テスト）

【並列Hooks】
- 完全並列（ファイル重複なし確認済み）

【制約】
- code-implementer: backend/xxx.py のみ編集
- test-designer: tests/xxx.py のみ編集

【MCP】
- なし

【期待する出力】
- 修正差分
- 再現テスト
```

---

## 📋 テンプレート3：セキュリティ監査（段階実行）

```
【目的】
セキュリティ脆弱性を検出・修正

【起動Agent】
🔒 sec-auditor
💻 code-implementer
🧪 test-designer

【並列Hooks】
- 順次実行（sec-auditor → code-implementer → test-designer）

【制約】
- 修正は sec-auditor の報告後のみ

【MCP】
- brave-search: CVE情報検索
- memory: 過去の脆弱性対応履歴

【期待する出力】
- 脆弱性レポート（sec-auditor）
- 修正差分（code-implementer）
- 検証テスト（test-designer）
```

---

## 📋 テンプレート4：ドキュメント整備（単独）

```
【目的】
〇〇の運用手順書を作成

【起動Agent】
📘 ops-runbook

【並列Hooks】
- 単独実行

【制約】
- docs/ 配下のみ編集

【MCP】
- memory: 過去の運用履歴
- github: 既存ドキュメントパターン

【期待する出力】
- 運用手順書（Markdown形式）
- トラブルシューティングガイド
```

---

## 📋 テンプレート5：包括的調査（並列探索）

```
【目的】
〇〇機能の実装状況を調査

【起動Agent】
🏗 arch-reviewer（バックエンド調査）
🏗 arch-reviewer（フロントエンド調査）
🏗 arch-reviewer（テスト調査）

【並列Hooks】
- 3つ完全並列

【制約】
- 編集なし（調査のみ）

【MCP】
- memory: 過去の実装履歴

【期待する出力】
- バックエンド実装状況レポート
- フロントエンド実装状況レポート
- テストカバレッジレポート
```

---

## 🚫 ダメな書き方（即応性を殺す）

### ❌ 例1：役割を指定しない

```
この作業に適したAgentを選んでください
```

**問題：** 判断フェーズ発生、起動遅延

---

### ❌ 例2：並列・順次を指定しない

```
以下を実装してください：
- 機能A
- 機能B
- テスト
```

**問題：** AIが順序を判断、最適化されない

---

### ❌ 例3：MCPを「必要なら」

```
必要に応じてMCPを使ってください
```

**問題：** AIが判断、初動遅延

---

## ✅ 良い書き方（即応性最大）

### ✅ 例1：明確な役割指定

```
【起動Agent】
🧭 spec-planner
💻 code-implementer
```

**効果：** 即座にチーム起動

---

### ✅ 例2：並列・順次を明示

```
【並列Hooks】
- spec-planner と arch-reviewer は並列
- code-implementer は後続
```

**効果：** 最適な実行順序、時間短縮

---

### ✅ 例3：MCP必須指定

```
【MCP】
- memory: 必ず最初に確認
- github: 類似実装を検索
```

**効果：** 初動から情報収集、判断ミス削減

---

## 🎓 超短縮版（実戦用）

```
目的：〇〇
Agent：🧭🏗💻🧪🚀
並列：最初3つ並列、後2つ順次
制約：編集は💻のみ
MCP：memory必須
出力：設計/実装/テスト/CI
```

---

## 📊 効果測定

### 従来の対話型（判断フェーズあり）

```
ユーザー: 「〇〇を実装して」
  ↓ 10秒
AI: 「どのような設計にしますか？」
  ↓ 30秒
ユーザー: 「△△でお願いします」
  ↓ 20秒
AI: 「実装します」
  ↓ 60秒
完了（合計：120秒）
```

### 即応型（判断フェーズゼロ）

```
ユーザー: 即応プロンプト投入
  ↓ 0秒（判断なし）
AI: SubAgent並列起動
  ↓ 45秒（並列処理）
完了（合計：45秒）
```

**時間短縮：** 62%削減

---

## 🔧 カスタマイズガイド

### プロジェクト固有のAgent追加

Mirai Knowledge Systemsでは、以下のような専用Agentも検討可能：

| アイコン | 名称 | 責務 |
|---------|------|------|
| 🏗️ | construction-specialist | 建設土木ドメイン知識の検証 |
| 📊 | data-analyst | ナレッジデータ分析・レポート |
| 🎨 | ui-designer | WebUIデザイン改善 |

---

## 📚 参考情報

### Claude Code関連
- **公式**: https://claude.com/claude-code
- **GitHub**: https://github.com/anthropics/claude-code

### プロジェクト設定
- `.claude/agents/AGENTS.md` - SubAgent公式名簿
- `.claude/hooks/README.md` - Hooks仕様
- `.claude/CLAUDE.md` - プロジェクト設定

---

**🚀 即応型プロンプトで開発速度を最大化しましょう！✨**
