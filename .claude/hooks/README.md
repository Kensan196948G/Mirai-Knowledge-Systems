# 🪝 Claude Code Hooks ドキュメント

**作成日**: 2026-01-09
**プロジェクト**: Mirai Knowledge Systems

---

## 📋 概要

Claude Code Hooksは、特定のイベント発生時に自動的に実行されるスクリプトや処理です。

### 🎯 利用可能なHookイベント

| Hook名 | トリガー | 実行タイミング |
|--------|---------|--------------|
| **SessionStart** | セッション開始時 | Claude Codeが起動したとき |
| **UserPromptSubmit** | プロンプト送信時 | ユーザーがメッセージを送信したとき |
| **ToolCall** | ツール呼び出し時 | Read、Edit、Bashなどのツールが呼ばれる前 |
| **ToolResult** | ツール結果受信時 | ツールの実行結果を受け取った後 |
| **SessionEnd** | セッション終了時 | Claude Codeを終了するとき |

---

## 🔍 現在のプロジェクトで確認されたHooks

### ✅ 動作確認済み

#### 1. SessionStart Hook
```
<system-reminder>
SessionStart:startup hook success: Success
</system-reminder>
```

**実行内容**:
- Claude Codeの基本初期化
- プロジェクト設定の読み込み（`.claude/settings.json`）
- Output Style設定の適用（Explanatory mode）
- claude-memプラグインからのコンテキスト取得

**並列実行の証拠**:
- 同じHookが2回実行されている
- 異なる処理（基本初期化 + コンテキスト取得）を並行して実行

#### 2. UserPromptSubmit Hook
```
<system-reminder>
UserPromptSubmit hook success: Success
</system-reminder>
```

**実行内容**:
- ユーザー入力の前処理
- コンテキストの準備
- 権限チェック

---

## 🔄 並列実行機能

### 検証結果

#### ✅ 並列実行が確認された点

1. **SessionStart Hookの重複実行**
   ```
   SessionStart:startup hook success: Success  (1回目)
   SessionStart:startup hook success: Success  (2回目)
   ```
   - 同じHook名で異なる処理を実行
   - 初期化とコンテキスト取得を分離

2. **追加コンテキストの並列取得**
   ```
   SessionStart hook additional context: You are in 'explanatory' output style mode...
   # 同時に
   UserPromptSubmit hook success: Success
   ```

### 並列実行のメリット

✅ **起動時間の短縮**
- 複数の初期化処理を同時に実行
- ブロッキングを最小化

✅ **モジュール化**
- 各Hookが独立した責任を持つ
- 拡張が容易

✅ **柔軟性**
- プラグイン（claude-mem等）が独自のHookを追加可能
- 処理の優先順位を制御可能

---

## 📁 Hook設定ファイル構造

### プロジェクト設定

```
.claude/
├── hooks/                      # カスタムHooks定義
│   ├── README.md              # このファイル
│   ├── session-start.sh       # SessionStart Hook（予定）
│   └── user-prompt-submit.sh  # UserPromptSubmit Hook（予定）
├── settings.json               # 基本設定
└── settings.local.json         # ローカル設定
```

### グローバル設定

```
~/.config/claude-code/
├── config.json                # グローバル設定
└── hooks/                     # グローバルHooks
```

---

## 🛠️ カスタムHookの作成（計画）

### サンプル: SessionStart Hook

```bash
#!/bin/bash
# .claude/hooks/session-start.sh

echo "🚀 Mirai Knowledge Systems セッション開始"
echo "プロジェクト: $(basename $(pwd))"
echo "日時: $(date '+%Y-%m-%d %H:%M:%S')"

# プロジェクト状態確認
if [ -f "backend/app_v2.py" ]; then
    echo "✅ バックエンド: 正常"
else
    echo "⚠️ バックエンド: app_v2.py が見つかりません"
fi

# Git状態確認
if [ -d ".git" ]; then
    BRANCH=$(git branch --show-current)
    echo "📍 Gitブランチ: $BRANCH"
fi

# サービス状態確認
if systemctl is-active --quiet mirai-knowledge-app; then
    echo "✅ アプリサービス: 稼働中"
else
    echo "⚠️ アプリサービス: 停止中"
fi
```

### サンプル: UserPromptSubmit Hook

```bash
#!/bin/bash
# .claude/hooks/user-prompt-submit.sh

# プロンプトの内容を分析（セキュリティチェック）
# （実装は今後）

echo "✅ UserPromptSubmit Hook実行完了"
```

---

## 🧪 並列実行テストプラン

### Phase 1: 基本動作確認

1. **単一Hook実行**
   ```bash
   # SessionStart Hookのみを定義
   # 実行時間を計測
   ```

2. **複数Hook実行**
   ```bash
   # SessionStart + UserPromptSubmit を定義
   # 順次実行 vs 並列実行の違いを確認
   ```

### Phase 2: 並列実行検証

1. **タイムスタンプ記録**
   ```bash
   # 各Hookに開始・終了タイムスタンプを追加
   # 並列実行の証明
   ```

2. **依存関係テスト**
   ```bash
   # Hook間の依存関係を定義
   # 並列実行時の同期確認
   ```

### Phase 3: パフォーマンス測定

1. **起動時間測定**
   - Hooksなし: X秒
   - Hooks順次実行: Y秒
   - Hooks並列実行: Z秒

2. **リソース使用量**
   - CPU使用率
   - メモリ使用量

---

## 📊 現状の分析結果

### ✅ 確認できたこと

1. **組み込みHooksが動作している**
   - SessionStart（2回実行）
   - UserPromptSubmit（毎回実行）

2. **並列実行の可能性**
   - SessionStartが重複実行されている
   - 異なる処理内容（初期化 + コンテキスト）

3. **Plugin統合**
   - claude-memがHooksを通じてコンテキスト提供
   - 拡張可能なアーキテクチャ

### ⚠️ 未確認の点

1. **真の並列実行**
   - タイムスタンプがないため確実ではない
   - 順次実行の可能性も残る

2. **Hook設定ファイルの場所**
   - プロジェクト内に明示的な定義が見つからない
   - Claude Code内部で管理されている可能性

3. **カスタムHookの作成方法**
   - 公式ドキュメントの確認が必要
   - 実装形式（Shell、Python、Node.js等）

---

## 🎯 次のステップ

### 即座に実施可能

1. ✅ **ドキュメント整備**
   - このREADMEの作成（完了）
   - Hooks分析レポートの作成

2. 📝 **既存Hooksの動作確認**
   - システムメッセージの継続監視
   - 実行パターンの記録

### 実装が必要

3. 🔧 **カスタムHook作成**
   - サンプルHookスクリプトの実装
   - `.claude/hooks/`に配置してテスト

4. 🧪 **並列実行テスト**
   - タイムスタンプ計測機能の追加
   - 並列実行の定量的検証

5. 📚 **公式ドキュメント確認**
   - Claude Code Hooksの仕様確認
   - ベストプラクティスの学習

---

## 📚 参考情報

### Claude Code関連

- **Claude Code公式**: https://claude.com/claude-code
- **GitHub**: https://github.com/anthropics/claude-code
- **ドキュメント**: `.claude/CLAUDE.md`

### Plugin関連

- **claude-mem**: セッション間メモリ管理プラグイン
- **ralph-loop**: 有効化済み（`.claude/settings.json`）

---

## 📅 更新履歴

| 日付 | 変更内容 |
|------|----------|
| 2026-01-09 | Hooks READMEの初版作成 |
| 2026-01-09 | 並列実行機能の分析結果を追加 |
| 2026-01-09 | カスタムHook実装計画を追加 |

---

**🚀 Hooksを活用してMirai Knowledge Systemsの開発効率を向上させましょう！✨**
