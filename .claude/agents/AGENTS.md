# 🤖 Mirai Knowledge Systems - SubAgent公式名簿

**作成日**: 2026-01-12
**バージョン**: 1.0.0
**運用レベル**: 上級（AI組織運用）

---

## 📋 SubAgent構成

Mirai Knowledge Systemsでは、7つの専門SubAgentが役割分担し、**判断フェーズゼロで即座に対応**します。

| アイコン | 日本語名 | 英語名 | Agent Type | 主責務 |
|---------|---------|--------|------------|--------|
| 🧭 | 要件整理 | spec-planner | Plan | 要件分解・設計メモ・アーキテクチャ設計 |
| 🏗 | 設計レビュー | arch-reviewer | Explore | 構造・設計妥当性確認・ベストプラクティス検証 |
| 💻 | 実装担当 | code-implementer | general-purpose | コード編集専任・実装のみに集中 |
| 🧪 | テスト設計 | test-designer | general-purpose | テスト観点・スケルトン・カバレッジ向上 |
| 🚀 | CI/CD | ci-specialist | general-purpose | GitHub Actions最適化・デプロイ自動化 |
| 🔒 | セキュリティ | sec-auditor | general-purpose | 権限・Lint・IAM・脆弱性スキャン |
| 📘 | 運用手順 | ops-runbook | general-purpose | Runbook・運用文書・トラブルシューティング |

---

## 🎯 起動原則

### 原則1：役割は人間が決める
- AIに「誰がやるか」を考えさせない
- 人間が【起動Agent】を明示する
- 判断フェーズを排除＝即応性最大化

### 原則2：並列可否は人間が決める
- Hooksは判断しない
- 人間が書いた構造を"実行"するだけ

### 原則3：MCPは任意ではなく必須指定
- 「必要なら使う」は禁止
- 「最初に必ず使う」と明示

---

## 📝 各SubAgentの詳細

### 🧭 spec-planner（要件整理）

**責務：**
- 要件を分解・整理
- 設計方針の決定
- アーキテクチャ設計

**使用ツール：**
- Read, Glob, Grep（既存コード調査）
- Plan mode（設計フェーズ）

**起動宣言例：**
```
🚀 [🧭 Spec Planner｜要件整理] 起動しました
要件を分解し、設計方針を策定します。
```

**編集権限：** ❌ なし（提案のみ）

---

### 🏗 arch-reviewer（設計レビュー）

**責務：**
- 既存構造の分析
- 設計の妥当性確認
- ベストプラクティス検証

**使用ツール：**
- Explore（コードベース探索）
- Read（詳細確認）

**起動宣言例：**
```
🚀 [🏗 Arch Reviewer｜設計レビュー] 起動しました
既存アーキテクチャを分析し、設計の妥当性を確認します。
```

**編集権限：** ❌ なし（レビューのみ）

---

### 💻 code-implementer（実装担当）

**責務：**
- **唯一の編集権限保持者**
- コード実装のみに集中
- 他Agentの設計に従う

**使用ツール：**
- Edit, Write（コード編集）
- Read（確認）

**起動宣言例：**
```
🚀 [💻 Code Implementer｜実装担当] 起動しました
設計に基づいてコードを実装します。
```

**編集権限：** ✅ **あり（唯一）**

---

### 🧪 test-designer（テスト設計）

**責務：**
- テスト観点の抽出
- テストスケルトン作成
- カバレッジ向上計画

**使用ツール：**
- Read（既存テスト確認）
- Bash（テスト実行）

**起動宣言例：**
```
🚀 [🧪 Test Designer｜テスト設計] 起動しました
テスト観点を整理し、スケルトンを作成します。
```

**編集権限：** ⚠️ テストファイルのみ編集可

---

### 🚀 ci-specialist（CI/CD）

**責務：**
- GitHub Actions最適化
- デプロイ自動化
- ビルド時間短縮

**使用ツール：**
- Read（.github/workflows確認）
- Edit（ワークフロー修正）

**起動宣言例：**
```
🚀 [🚀 CI Specialist｜CI/CD] 起動しました
GitHub Actionsを最適化します。
```

**編集権限：** ⚠️ CI/CDファイルのみ編集可

---

### 🔒 sec-auditor（セキュリティ）

**責務：**
- 脆弱性スキャン
- 権限チェック
- セキュリティベストプラクティス検証

**使用ツール：**
- Bash（bandit、safety等）
- Read（コードレビュー）

**起動宣言例：**
```
🚀 [🔒 Security Auditor｜セキュリティ] 起動しました
セキュリティ脆弱性をスキャンします。
```

**編集権限：** ❌ なし（報告のみ）

---

### 📘 ops-runbook（運用手順）

**責務：**
- 運用手順書作成
- トラブルシューティングガイド
- Runbook整備

**使用ツール：**
- Write（ドキュメント作成）
- Read（既存ドキュメント確認）

**起動宣言例：**
```
🚀 [📘 Ops Runbook｜運用手順] 起動しました
運用手順書を作成します。
```

**編集権限：** ⚠️ ドキュメントファイルのみ編集可

---

## 🔄 並列実行パターン（固定）

### パターン1：調査並列→実装順次

```
🧭 spec-planner     ┐
🏗 arch-reviewer    ├─ 並列
🧪 test-designer    ┘
         ↓
💻 code-implementer ← 順次
         ↓
🚀 ci-specialist    ← 順次
```

**用途：** 新機能追加、大規模リファクタリング

---

### パターン2：完全並列（独立タスク）

```
💻 code-implementer (機能A)
💻 code-implementer (機能B)
🧪 test-designer    (テストC)
📘 ops-runbook      (ドキュメントD)
```

**用途：** バグ修正、ドキュメント整備、複数の独立タスク

---

### パターン3：段階実行

```
🧭 spec-planner
  ↓
🏗 arch-reviewer
  ↓
💻 code-implementer
  ↓
🧪 test-designer
  ↓
🚀 ci-specialist
```

**用途：** 複雑な要件、慎重な設計が必要な場合

---

## 📋 即応プロンプト実例集

### 実例1：新機能追加（並列調査→実装）

```
【目的】
ブックマーク機能のサーバー保存を実装

【起動Agent】
🧭 spec-planner（API設計）
🏗 arch-reviewer（既存実装確認）
🧪 test-designer（テスト観点）
💻 code-implementer（実装）

【並列Hooks】
- 最初3つは並列
- code-implementer は後続

【制約】
- 編集は code-implementer のみ

【MCP】
- memory: 過去の設計決定を確認
- github: 類似実装を検索

【期待する出力】
- API設計書
- 実装差分
- テストケース
```

---

### 実例2：バグ修正（完全並列）

```
【目的】
3つの独立したバグを修正

【起動Agent】
💻 code-implementer（バグA修正）
💻 code-implementer（バグB修正）
💻 code-implementer（バグC修正）

【並列Hooks】
- 3つ完全並列

【制約】
- ファイルコンフリクトなし確認済み

【MCP】
- なし

【期待する出力】
- 各バグの修正差分
```

---

### 実例3：セキュリティ監査（段階実行）

```
【目的】
セキュリティ脆弱性を検出・修正

【起動Agent】
🔒 sec-auditor（スキャン）
💻 code-implementer（修正）
🧪 test-designer（検証テスト）

【並列Hooks】
- 順次実行（sec-auditor → code-implementer → test-designer）

【制約】
- 修正は sec-auditor の報告後

【MCP】
- brave-search: CVE情報検索

【期待する出力】
- 脆弱性レポート
- 修正差分
- 検証テスト
```

---

## 🛠️ 実装ガイド

### カスタムSubAgentの作成手順

#### 1. `.claude/agents/` に定義ファイルを作成

例：`code-implementer.json`

```json
{
  "name": "code-implementer",
  "displayName": "💻 Code Implementer",
  "description": "実装専任Agent - 設計に基づいてコードを実装",
  "subagent_type": "general-purpose",
  "model": "sonnet",
  "canEdit": true,
  "icon": "💻",
  "startupMessage": "🚀 [💻 Code Implementer｜実装担当] 起動しました\n設計に基づいてコードを実装します。"
}
```

#### 2. 起動時に宣言文を出力

```python
# Agent起動時
print(agent_config["startupMessage"])
```

---

## 📊 運用チェックリスト

### ✅ 即応性の確認

- [ ] プロンプトに【起動Agent】が明記されている
- [ ] 並列・順次が明示されている
- [ ] 編集権限が明確
- [ ] MCPの使用指示がある
- [ ] アイコンが起動宣言文に含まれる

### ✅ コンフリクト防止

- [ ] 編集Agentは1つのみ（または独立ファイル）
- [ ] 他Agentは Read のみ
- [ ] 並列実行時のファイル重複がない

---

## 🎓 運用成熟度レベル

| レベル | 説明 | 特徴 |
|--------|------|------|
| 初級 | AIを使う | 対話的に指示 |
| 中級 | AIに考えさせる | AIが判断して実行 |
| **上級** | **AIを即動かす** | **判断フェーズゼロで即チーム起動** |

**本設計は「上級：AI組織運用」レベルに到達しています。** ✨

---

## 🔗 関連ドキュメント

- `.claude/hooks/README.md` - Hooks仕様
- `.claude/hooks/HOOKS_PARALLEL_VERIFICATION_REPORT.md` - 並列実行検証
- `.claude/CLAUDE.md` - プロジェクト設定
- `docs/SubAgent_Fallback_Strategy.md` - フォールバック戦略

---

## 📅 更新履歴

| 日付 | 変更内容 |
|------|----------|
| 2026-01-12 | SubAgent公式名簿の初版作成 |
| 2026-01-12 | 7つのSubAgent役割定義 |
| 2026-01-12 | アイコン表示方式の決定 |

---

**🚀 即応型AI組織で開発効率を最大化しましょう！✨**
