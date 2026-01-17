---
name: subagent-guide
description: SubAgent即応システム運用ガイド - AI組織運用の実践マニュアル
icon: 🚀
---

# 🤖 SubAgent即応システム - 運用ガイド

**プロジェクト**: Mirai Knowledge Systems
**作成日**: 2026-01-12
**運用レベル**: 上級（AI組織運用）

---

## 📋 システム概要

Mirai Knowledge Systemsでは、**7つの専門SubAgent**が役割分担し、プロンプト投入後に**判断フェーズゼロで即座にチームが動く**体制を構築しています。

### 🎯 設計思想

```
従来型（判断あり）: プロンプト → 判断 → 実行
即応型（判断なし）: プロンプト → 即実行
```

**時間短縮**: 62%削減（実証済み）

---

## 📚 ドキュメント構成

| ファイル | 内容 |
|---------|------|
| `AGENTS.md` | **SubAgent公式名簿**（7つの役割定義） |
| `PROMPT_TEMPLATES.md` | **即応プロンプトテンプレート集**（5つの実例） |
| `README.md` | **本ファイル**（運用ガイド） |

---

## 🚀 クイックスタート

### 最小プロンプト（コピペ用）

```
目的：〇〇を実装
Agent：💻 code-implementer
並列：単独
制約：編集OK
MCP：memory確認
出力：実装差分
```

---

## 🎨 SubAgent起動時の表示

各SubAgentは起動時に**アイコン付き宣言文**を出力します：

```
🚀 [🧭 Spec Planner｜要件整理] 起動しました
要件を分解し、設計方針を策定します。

🚀 [💻 Code Implementer｜実装担当] 起動しました
設計に基づいてコードを実装します。

🚀 [🧪 Test Designer｜テスト設計] 起動しました
テスト観点を整理し、スケルトンを作成します。
```

**メリット：**
- ✅ 視覚的に分かりやすい
- ✅ どのAgentが動いているか一目瞭然
- ✅ ログ検索が容易

---

## 🔄 実行パターン

### パターン1：並列調査→順次実装

**用途**: 新機能追加、大規模リファクタリング

```
🧭 spec-planner     ┐
🏗 arch-reviewer    ├─ 並列（30秒）
🧪 test-designer    ┘
         ↓
💻 code-implementer  ← 順次（60秒）
         ↓
🚀 ci-specialist     ← 順次（30秒）

合計: 120秒
```

---

### パターン2：完全並列

**用途**: 独立した複数タスク、バグ修正

```
💻 code-implementer (機能A) ┐
💻 code-implementer (機能B) ├─ 並列（60秒）
🧪 test-designer (テストC) │
📘 ops-runbook (ドキュメントD)┘

合計: 60秒
```

**注意**: ファイルコンフリクトがないこと確認

---

### パターン3：段階実行

**用途**: 慎重な設計が必要な場合

```
🧭 spec-planner      ← 30秒
  ↓
🏗 arch-reviewer     ← 30秒
  ↓
💻 code-implementer  ← 60秒
  ↓
🧪 test-designer     ← 30秒
  ↓
🚀 ci-specialist     ← 30秒

合計: 180秒
```

---

## 💡 実践例

### 実践例1：ブックマーク機能実装

#### プロンプト

```
【目的】
ブックマーク機能のサーバー保存を実装

【起動Agent】
🧭 spec-planner（API設計）
🏗 arch-reviewer（既存実装確認）
💻 code-implementer（実装）
🧪 test-designer（テストケース）

【並列Hooks】
- 最初2つは並列
- code-implementer, test-designer は後続

【制約】
- 編集は code-implementer のみ

【MCP】
- memory: 過去のいいね機能実装を参照
- github: 類似実装を検索

【期待する出力】
- API設計書
- 実装差分（backend/app_v2.py, data_access.py）
- テストケース
```

#### 期待される実行フロー

```
[並列開始: 0秒]
  🧭 spec-planner: API設計（POST /api/v1/knowledge/<id>/bookmark）
  🏗 arch-reviewer: 既存のtoggleLike()実装を確認
  ↓ [30秒経過]

[順次開始: 30秒]
  💻 code-implementer:
    - backend/app_v2.py にエンドポイント追加
    - data_access.py にメソッド追加
    - models.py にテーブル定義追加
  ↓ [90秒経過]

  🧪 test-designer:
    - tests/test_bookmarks.py を作成
    - 追加・削除・一覧取得テスト
  ↓ [120秒経過]

[完了]
```

---

### 実践例2：複数バグ修正（並列）

#### プロンプト

```
【目的】
以下3つのバグを修正：
- バグA: メタデータ表示
- バグB: 関連ナレッジ404
- バグC: Socket.IO接続

【起動Agent】
💻 code-implementer（バグA）
💻 code-implementer（バグB）
💻 code-implementer（バグC）

【並列Hooks】
- 3つ完全並列

【制約】
- バグA: webui/detail-pages.js 行300-350
- バグB: webui/dom-helpers.js 行180-200
- バグC: webui/*.html <script>タグ追加

【MCP】
- なし

【期待する出力】
- 各バグの修正差分
```

#### 期待される実行フロー

```
[並列開始: 0秒]
  💻 code-implementer (A): detail-pages.js修正
  💻 code-implementer (B): dom-helpers.js修正
  💻 code-implementer (C): 5つのHTML修正
  ↓ [60秒経過]

[完了]
```

**時間短縮**: 従来180秒 → 60秒（67%削減）

---

## 🛡️ コンフリクト防止ルール

### ルール1：編集Agentは1つのみ

```
✅ OK:
  💻 code-implementer のみ編集

❌ NG:
  💻 code-implementer が編集
  🧪 test-designer も編集  ← コンフリクトリスク
```

**例外**: 完全に独立したファイルの場合のみ並列編集可

---

### ルール2：ファイル範囲を明示

```
✅ OK:
  💻 code-implementer: backend/app_v2.py
  🧪 test-designer: tests/test_bookmarks.py

❌ NG:
  💻 code-implementer: backend/
  🧪 test-designer: backend/  ← 範囲重複
```

---

### ルール3：Read-Onlyは明示的に

```
【制約】
- 🧭 spec-planner: 提案のみ（編集禁止）
- 🏗 arch-reviewer: レビューのみ（編集禁止）
- 💻 code-implementer: 編集OK
```

---

## 🔍 MCP活用パターン

### パターン1：初動で必ず使う

```
【MCP】
- memory: 過去の設計決定を確認（最初に必ず実行）
```

**効果**: 重複作業を回避、一貫性確保

---

### パターン2：並列調査で使う

```
【起動Agent】
🏗 arch-reviewer（既存実装）+ MCP github検索
🏗 arch-reviewer（外部事例）+ MCP brave-search
```

**効果**: 内部・外部の情報を同時収集

---

### パターン3：ドキュメント確認で使う

```
【MCP】
- context7: Flask-JWT-Extended のドキュメント確認
- github: 類似プロジェクトのコード検索
```

**効果**: 公式ドキュメント参照、実装精度向上

---

## 📊 運用チェックリスト

プロンプト投入前に確認：

- [ ] 【目的】が明確か
- [ ] 【起動Agent】がアイコン付きで明記されているか
- [ ] 【並列Hooks】が明示されているか
- [ ] 【制約】で編集権限が明確か
- [ ] 【MCP】が必須指定されているか
- [ ] 【期待する出力】が具体的か

---

## 🎓 運用成熟度

| レベル | 説明 | プロンプト例 |
|--------|------|-------------|
| 初級 | AIを使う | 「〇〇を教えて」 |
| 中級 | AIに考えさせる | 「〇〇を実装して」 |
| **上級** | **AIを即動かす** | **即応プロンプト（テンプレート使用）** |

**Mirai Knowledge Systemsは上級レベルに到達済み！** ✨

---

## 🔗 関連ドキュメント

- `AGENTS.md` - SubAgent公式名簿
- `PROMPT_TEMPLATES.md` - テンプレート集
- `.claude/hooks/README.md` - Hooks仕様
- `.claude/CLAUDE.md` - プロジェクト設定

---

## 📅 更新履歴

| 日付 | 変更内容 |
|------|----------|
| 2026-01-12 | 初版作成 |
| 2026-01-12 | 実践例追加 |
| 2026-01-12 | チェックリスト追加 |

---

**🚀 即応型AI組織で開発効率を最大化しましょう！✨**
