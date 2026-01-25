# Claude Code MCP設定完了ガイド

## ✅ 完了した設定

### 環境変数（永続化済み）

以下の環境変数がWindowsユーザーレベルで設定されました：

- `BRAVE_API_KEY` - Brave Search API認証
- `GITHUB_TOKEN` - GitHub統合（repo権限のみ）
- `CONTEXT7_API_KEY` - Context7ドキュメント検索

### MCPサーバー設定

`.mcp.json`で以下のMCPサーバーが設定されています：

1. **brave-search** - Web検索機能
2. **github** - GitHub統合（PR、Issue管理）
3. **memory** - セッション間メモリ
4. **sqlite** - データベースクエリ
5. **playwright** - ブラウザ自動化
6. **sequential-thinking** - 段階的思考
7. **context7** - ドキュメント検索

### カスタムスキル

`.claude/skills/`で以下のスキルが設定されています：

1. **commit-push-pr** - コミット→プッシュ→PR作成
2. **commit-push-pr-merge** - コミット→プッシュ→PR作成→マージ

## 🔧 トラブルシューティング

### 「Found 3 invalid settings files」エラーが出る場合

**原因**: 環境変数が設定されていないか、読み込まれていない

**解決方法**:

1. PowerShellを**完全に再起動**
2. 環境変数を確認：
   ```powershell
   echo $env:BRAVE_API_KEY
   echo $env:GITHUB_TOKEN
   echo $env:CONTEXT7_API_KEY
   ```
3. 値が表示されない場合、再設定：
   ```powershell
   powershell -ExecutionPolicy Bypass -File set-env-permanent.ps1
   ```
4. PCを再起動（最終手段）

### 環境変数を手動で設定する方法

1. Windowsキー + `sysdm.cpl`を検索
2. 「詳細設定」→「環境変数」
3. ユーザー環境変数に追加：
   - 変数名: `BRAVE_API_KEY`, 値: `<your-brave-api-key>`
   - 変数名: `GITHUB_TOKEN`, 値: `<your-github-token>`
   - 変数名: `CONTEXT7_API_KEY`, 値: `<your-context7-api-key>`

### MCPサーバーが起動しない場合

```powershell
# Node.jsとnpmのバージョン確認
node --version  # v18.0.0以上が必要
npm --version   # v9.0.0以上が必要

# MCPサーバーを手動でテスト
npx -y @modelcontextprotocol/server-brave-search
```

## 📚 関連ファイル

- `.mcp.json` - MCPサーバー設定
- `.claude/settings.local.json` - ローカル設定（出力スタイル等）
- `.claude/CLAUDE.md` - プロジェクトコンテキスト
- `.claude/skills/*/SKILL.md` - カスタムスキル定義
- `fix-mcp-env.ps1` - 一時的な環境変数設定スクリプト
- `set-env-permanent.ps1` - 永続的な環境変数設定スクリプト
- `validate-settings.ps1` - 設定ファイル検証スクリプト

## 🎯 次のステップ

1. **環境変数の確認** - 新しいPowerShellで`echo $env:BRAVE_API_KEY`
2. **Claude Code起動** - `claude`コマンドでエラーなく起動
3. **MCP機能テスト** - 以下を試してみる：
   ```
   /mcp         # MCPサーバー一覧
   brave-searchを使ってWeb検索
   githubを使ってPR確認
   ```

## 🔐 セキュリティ注意事項

- **APIキーは機密情報** - `.env`や設定ファイルをGitにコミットしない
- **`.gitignore`で保護** - `.claude/settings.local.json`は既に除外済み
- **定期的なローテーション** - APIキーは定期的に再発行を推奨
- **最小権限の原則** - GitHub Tokenは`repo`権限のみに制限済み

## ✨ 完了！

これでClaude Codeの全機能が利用可能です！

- ✅ MCP統合（7サーバー）
- ✅ カスタムスキル（2スキル）
- ✅ 環境変数永続化
- ✅ 設定ファイル検証

問題があれば、上記のトラブルシューティングを参照してください。
