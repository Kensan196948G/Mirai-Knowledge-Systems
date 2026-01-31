# MCP サーバー使い分けガイド

**作成日**: 2026-01-31
**プロジェクト**: Mirai Knowledge Systems

---

## 📋 MCPサーバー一覧と使い分け

### 🧠 メモリ管理系（2種類）

#### 1. memory（基本メモリ）
**パッケージ**: `@modelcontextprotocol/server-memory`
**ストレージ**: `~/.claude/memory.json`（グローバル）

**用途**:
- セッション間の簡易的な情報保存
- キー・バリュー形式のデータ保存
- 全プロジェクト共通の記憶

**使用例**:
```typescript
// 簡易的な情報保存
mcp_memory_save({
  key: "user_preference_language",
  value: "ja"
});

// グローバルな設定情報
mcp_memory_save({
  key: "default_test_framework",
  value: "pytest"
});
```

**推奨用途**:
- ✅ ユーザー設定・好み
- ✅ よく使うコマンド
- ✅ グローバルな開発規約
- ❌ プロジェクト固有の状態管理（→ memory-keeper使用）

---

#### 2. memory-keeper（永続的コンテキスト管理）
**パッケージ**: `mcp-memory-keeper`
**ストレージ**: プロジェクトルート `.mcp-memory/`（推測）

**用途**:
- プロジェクト固有のコンテキスト管理
- チェックポイント作成・復元
- ファイル状態、Git状態の保存
- 長期開発セッションの状態管理

**使用例**:
```typescript
// チェックポイント作成（リファクタリング前）
mcp_context_checkpoint({
  name: "before-security-refactor",
  description: "XSS脆弱性修正前の状態",
  includeFiles: true,
  includeGitStatus: true
});

// 複雑な作業の途中経過を保存
mcp_context_checkpoint({
  name: "phase-d1-oauth-implementation",
  description: "Microsoft 365 OAuth実装途中",
  includeFiles: true,
  includeGitStatus: true
});

// チェックポイント復元
mcp_context_restore_checkpoint({
  name: "before-security-refactor",
  restoreFiles: true
});

// 直近のチェックポイントを復元
mcp_context_restore_checkpoint({});
```

**推奨用途**:
- ✅ 大規模リファクタリング前の状態保存
- ✅ フェーズごとの開発状態記録
- ✅ 複雑な実装の中間状態保存
- ✅ デバッグ時の状態巻き戻し
- ❌ 簡易的なメモ（→ memory使用）

---

## 🎯 使い分けフローチャート

```
保存したい情報は？
  │
  ├─ グローバル設定・ユーザー好み
  │   → memory 使用
  │
  ├─ プロジェクト固有の状態
  │   │
  │   ├─ 簡易的な記憶（キー・バリュー）
  │   │   → memory 使用
  │   │
  │   └─ チェックポイント・ファイル状態含む
  │       → memory-keeper 使用
  │
  └─ 一時的なメモ（セッション内のみ）
      → 変数・コメントで管理
```

---

## 📊 性能設定（memory-keeper）

### 環境変数

| 変数名 | デフォルト | 範囲 | 説明 |
|--------|-----------|------|------|
| `MCP_MAX_TOKENS` | 25000 | 1000-100000 | レスポンスの最大トークン数 |
| `MCP_TOKEN_SAFETY_BUFFER` | 0.8 | 0.1-1.0 | 安全マージンの割合 |
| `MCP_MIN_ITEMS` | 1 | 1-100 | レスポンス内の最小アイテム数 |
| `MCP_MAX_ITEMS` | 100 | 1-1000 | レスポンス内の最大アイテム数 |

**現在の設定**:
- MCP_MAX_TOKENS: 25000（デフォルト）
- MCP_TOKEN_SAFETY_BUFFER: 0.8（デフォルト）
- MCP_MIN_ITEMS: 1（デフォルト）
- MCP_MAX_ITEMS: 100（デフォルト）

---

## 🔧 実践的な使用例

### Phase D開発でのチェックポイント戦略

```typescript
// Phase D-1開始前
mcp_context_checkpoint({
  name: "phase-c-complete",
  description: "Phase C本番運用完了時点の安定状態",
  includeFiles: true,
  includeGitStatus: true
});

// Microsoft 365連携の各段階で保存
mcp_context_checkpoint({
  name: "oauth-implementation-done",
  description: "OAuth 2.0認証フロー実装完了",
  includeFiles: true,
  includeGitStatus: true
});

mcp_context_checkpoint({
  name: "sharepoint-sync-working",
  description: "SharePoint自動同期が動作した状態",
  includeFiles: true,
  includeGitStatus: true
});

// 問題発生時、安定版に戻す
mcp_context_restore_checkpoint({
  name: "oauth-implementation-done",
  restoreFiles: true
});
```

### セキュリティ修正での活用

```typescript
// XSS脆弱性修正前の状態保存
mcp_context_checkpoint({
  name: "before-xss-fix",
  description: "innerHTML使用箇所20件修正前",
  includeFiles: true,
  includeGitStatus: true
});

// 修正中に問題が発生したら復元
mcp_context_restore_checkpoint({
  name: "before-xss-fix",
  restoreFiles: true
});
```

---

## 📁 ストレージ構造

### memory（グローバル）
```
~/.claude/
└── memory.json          # 全プロジェクト共通のメモリ
    ├── user_preference_language: "ja"
    ├── default_test_framework: "pytest"
    └── coding_style: "PEP8"
```

### memory-keeper（プロジェクト固有）
```
/mnt/LinuxHDD/Mirai-Knowledge-Systems/
└── .mcp-memory/         # プロジェクト固有のメモリ（推測）
    ├── checkpoints/
    │   ├── phase-c-complete/
    │   ├── oauth-implementation-done/
    │   └── before-xss-fix/
    └── context.json
```

---

## ⚠️ ベストプラクティス

### ✅ Do（推奨）

1. **重要なマイルストーンでチェックポイント作成**
   - Phase完了時
   - 大規模リファクタリング前
   - 本番デプロイ前

2. **わかりやすい命名規則**
   - `phase-X-Y-milestone`: フェーズ区切り
   - `before-feature-X`: 機能実装前
   - `working-state-X`: 動作確認済み状態

3. **チェックポイント説明を詳細に**
   ```typescript
   mcp_context_checkpoint({
     name: "oauth-v1-working",
     description: "OAuth 2.0認証フロー実装完了。テスト3件パス。未実装: トークンリフレッシュ",
     includeFiles: true,
     includeGitStatus: true
   });
   ```

### ❌ Don't（非推奨）

1. **チェックポイントの乱立**
   - 5分ごとにチェックポイントを作るのは避ける
   - Git commitと併用し、重要ポイントのみ

2. **曖昧な命名**
   - ❌ `test1`, `backup`, `temp`
   - ✅ `before-db-migration`, `oauth-working`

3. **機密情報の保存**
   - パスワード、APIキーを含むチェックポイントは避ける
   - 環境変数ファイル（.env）は除外

---

## 🔄 Claude Code再起動後の確認

```bash
# MCPサーバー一覧確認
claude mcp list

# memory の状態確認
claude mcp get memory

# memory-keeper の状態確認
claude mcp get memory-keeper
```

---

**作成者**: Claude Sonnet 4.5
**更新日**: 2026-01-31
**バージョン**: 1.0
