# GitHub Actions ワークフロー

## 自動エラー検知・修復システム

### ファイル
- `auto-error-fix-continuous.yml` - 5分間隔で無限ループ実行 + 他ワークフロー監視

### 実行スケジュール
- **自動実行:** 5分ごと（cron: `*/5 * * * *`）
- **他ワークフロー監視:** E2E Tests、Backend CI、Backend CI (Improved)、Mirai Knowledge Systems CI/CD の完了時に自動起動
- **手動実行:** GitHub Actions画面から「Run workflow」をクリック

### 機能

#### 1. エラー検知・修復ループ（15回）
各ループで以下を実行：
1. ヘルスチェック実行（`backend/scripts/health_monitor.py`）
2. テスト実行（pytest）
3. エラー検出時に自動修復実行（`backend/scripts/auto_fix_daemon.py`）
4. ログファイル確認（エラー/例外/クリティカルを検索）
5. 結果を記録

#### 2. 実行環境
- Ubuntu latest
- Python 3.12
- PostgreSQL 16（Docker）
- Redis 7（Docker）
- 他ワークフローの監視・自動応答機能

#### 3. 結果レポート
- GitHub Issueに自動投稿
- エラー検出時: `[自動修復] エラーX件検出・修復Y件実行`
- 正常時: `[自動修復] 正常動作確認`
- ワークフロー失敗検知時: `[自動修復] [ワークフロー名] 失敗検知・修復試行`
- ラベル: `auto-fix`, `error-detected` / `healthy`, `workflow-triggered`, `ci-failure`

#### 4. Artifact保存
- エラー検知・修復ログ
- テスト結果
- アプリケーションログ
- 保存期間: 30日

### 使用方法

#### 自動実行（定期監視）
- GitHubにpush後、5分ごとに自動実行される
- 何もする必要なし

#### 自動実行（ワークフロー監視）
- E2E Tests、Backend CI、Backend CI (Improved)、Mirai Knowledge Systems CI/CD のいずれかが完了すると自動起動
- 失敗したワークフローを検知すると自動修復を試行
- 成功したワークフローでも健全性チェックを実行

#### 手動実行
1. GitHubリポジトリのActionsタブを開く
2. 「自動エラー検知・修復システム」を選択
3. 「Run workflow」をクリック
4. オプション設定：
   - `max_loops`: 最大ループ回数（デフォルト15）
   - `create_issue`: Issue作成（yes/no）
5. 「Run workflow」をクリック

### 監視方法

#### GitHub Actionsで確認
1. ActionsタブでワークフローRunを確認
2. 各ステップのログを確認
3. 緑のチェックマーク = 成功、赤のX = 失敗

#### GitHub Issueで確認
1. Issuesタブを開く
2. ラベル`auto-fix`でフィルター
3. 最新のIssueを確認
4. エラー詳細とサマリーを確認

#### Artifactで確認
1. ワークフローRunの詳細ページを開く
2. 下部のArtifactsセクションから`error-fix-results-{run_number}`をダウンロード
3. ZIPを解凍してログファイルを確認

### トラブルシューティング

#### ワークフローが実行されない
- `.github/workflows/`ディレクトリがmainブランチに存在するか確認
- YAMLファイルの構文エラーを確認
- GitHubリポジトリの設定でActionsが有効になっているか確認

#### Issueが作成されない
- リポジトリのIssue機能が有効か確認
- ワークフローのpermissionsに`issues: write`が含まれているか確認
- `create_issue`パラメータが`yes`になっているか確認

#### テストが失敗し続ける
- Issueに投稿されたログを確認
- Artifactをダウンロードして詳細ログを確認
- 自動修復スクリプト（`backend/scripts/auto_fix_daemon.py`）の動作を確認

### 無効化方法

#### 一時的に無効化
1. GitHubリポジトリのActionsタブを開く
2. 左側のワークフロー一覧から「自動エラー検知・修復システム」を選択
3. 右上の「...」メニューから「Disable workflow」を選択

#### 完全に削除
```bash
git rm .github/workflows/auto-error-fix-continuous.yml
git commit -m "Disable auto error fix workflow"
git push
```

### カスタマイズ

#### 実行間隔を変更
`auto-error-fix-continuous.yml`の`cron`を編集：
```yaml
schedule:
  - cron: '*/5 * * * *'   # 5分ごと（デフォルト）
  # - cron: '*/30 * * * *' # 30分ごと
  # - cron: '0 * * * *'    # 1時間ごと
  # - cron: '0 */6 * * *'  # 6時間ごと
  # - cron: '0 0 * * *'    # 毎日0時
```

#### ループ回数を変更
環境変数`MAX_LOOPS`を編集：
```yaml
env:
  MAX_LOOPS: 15  # 15回 → 任意の回数に変更
```

#### Issue作成条件を変更
スクリプトセクションを編集：
```javascript
// エラーがある場合のみIssue作成
if: steps.error_fix_loop.outputs.error_count > 0
```

## その他のワークフロー

### ci-backend-improved.yml
- PR作成時・push時にテスト実行
- コードカバレッジ測定
- セキュリティスキャン

---

**作成日:** 2025-12-28
**更新日:** 2025-12-28
