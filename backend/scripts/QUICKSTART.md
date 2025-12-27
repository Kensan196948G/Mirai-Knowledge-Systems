# クイックスタートガイド - エラー自動検知・自動修復システム

## 即座に使い始める

### 1. 基本的な動作確認

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/scripts

# ヘルスチェックを実行
python3 health_monitor.py
```

**期待される出力:**
```json
{
  "timestamp": "2025-12-28T00:06:33",
  "checks": {
    "database_connection": {"status": "healthy"},
    "disk_space": {"status": "healthy", "usage_percent": 57.9},
    "memory_usage": {"status": "healthy", "usage_percent": 19.8}
  },
  "overall_status": "healthy"
}
```

### 2. 1回だけエラー検知を実行

```bash
# 現在のログをスキャンしてエラーを検出
python3 auto_fix_daemon.py
```

**実行内容:**
- ログファイルをスキャン
- エラーパターンを検出
- 検出されたエラーに対して自動修復を実行
- 結果を `logs/auto_fix.log` に記録

### 3. 継続的な監視を開始（推奨）

```bash
# 永続的な監視モードで起動
python3 auto_fix_daemon.py --continuous
```

**動作:**
```
15回のエラー検知ループ実行
  ↓
5分間待機
  ↓
再び15回のループ実行
  ↓
永続的に繰り返す...
```

**停止方法:** `Ctrl+C` を押す

### 4. バックグラウンドで実行

```bash
# nohupで実行
nohup python3 auto_fix_daemon.py --continuous > /dev/null 2>&1 &

# プロセス確認
ps aux | grep auto_fix_daemon

# 停止
pkill -f auto_fix_daemon
```

### 5. systemdサービスとして起動（本番環境推奨）

```bash
# サービスファイルをインストール
sudo cp auto-fix-daemon.service /etc/systemd/system/
sudo systemctl daemon-reload

# サービス起動
sudo systemctl start auto-fix-daemon

# 起動時に自動起動を設定
sudo systemctl enable auto-fix-daemon

# ステータス確認
sudo systemctl status auto-fix-daemon

# ログをリアルタイムで確認
sudo journalctl -u auto-fix-daemon -f
```

## 実用例

### 例1: サーバー起動時のエラー検知

```bash
# サーバー起動
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend
python3 app.py &

# エラー検知デーモンを起動
cd scripts
python3 auto_fix_daemon.py --continuous &

# 両方のログを同時に確認
tail -f ../logs/app.log ../logs/auto_fix.log
```

### 例2: カスタムループ設定

```bash
# 30回ループ、10分待機
python3 auto_fix_daemon.py --continuous --loop-count 30 --wait-minutes 10

# 5回ループ、1分待機（テスト用）
python3 auto_fix_daemon.py --continuous --loop-count 5 --wait-minutes 1
```

### 例3: 定期的なヘルスチェックのみ

```bash
# cronで5分ごとにヘルスチェック
crontab -e

# 以下を追加
*/5 * * * * cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/scripts && python3 health_monitor.py >> ../logs/health_check.log 2>&1
```

### 例4: テストスイート実行

```bash
# すべてのテストを実行
python3 test_auto_fix.py
```

**テスト内容:**
- ヘルスモニター動作確認
- エラー検知機能確認
- 自動修復アクション確認
- 検知サイクル動作確認

## よくある使用パターン

### パターン1: 開発環境

```bash
# 短いループで頻繁にチェック
python3 auto_fix_daemon.py --continuous --loop-count 10 --wait-minutes 2
```

### パターン2: 本番環境

```bash
# systemdサービスとして起動
sudo systemctl start auto-fix-daemon
sudo systemctl enable auto-fix-daemon
```

### パターン3: 一時的な監視

```bash
# 1時間だけ監視（12回ループ × 5分 = 60分）
timeout 1h python3 auto_fix_daemon.py --continuous --loop-count 12 --wait-minutes 5
```

### パターン4: デバッグモード

```bash
# ログを標準出力に表示しながら実行
python3 auto_fix_daemon.py --continuous 2>&1 | tee debug.log
```

## ログの確認方法

### 自動修復ログ

```bash
# リアルタイム表示
tail -f /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/logs/auto_fix.log

# 最新100行を表示
tail -n 100 /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/logs/auto_fix.log

# エラーのみ表示
grep ERROR /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/logs/auto_fix.log

# 修復成功のみ表示
grep "自動修復完了" /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/logs/auto_fix.log
```

### アラートログ

```bash
# アラート一覧
cat /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/logs/alerts.log | jq .

# クリティカルアラートのみ
cat /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/logs/alerts.log | jq 'select(.severity=="critical")'

# 今日のアラート数
grep $(date +%Y-%m-%d) /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/logs/alerts.log | wc -l
```

### systemdログ

```bash
# 最新ログ
sudo journalctl -u auto-fix-daemon -n 50

# リアルタイム表示
sudo journalctl -u auto-fix-daemon -f

# 今日のログ
sudo journalctl -u auto-fix-daemon --since today

# エラーのみ
sudo journalctl -u auto-fix-daemon -p err
```

## トラブルシューティング

### Q1: デーモンが起動しない

```bash
# 手動実行でエラー確認
python3 auto_fix_daemon.py

# 設定ファイル確認
python3 -c "import json; print(json.load(open('error_patterns.json')))"

# 権限確認
ls -la auto_fix_daemon.py health_monitor.py
```

### Q2: エラーが検出されない

```bash
# ログファイルが存在するか確認
ls -la ../logs/

# エラーパターン確認
grep -E "ERROR|Exception|Traceback" ../logs/app.log
```

### Q3: 自動修復が実行されない

```bash
# auto_fix設定確認
python3 -c "
import json
config = json.load(open('error_patterns.json'))
for p in config['error_patterns']:
    print(f'{p[\"id\"]}: auto_fix={p.get(\"auto_fix\")}')"

# クールダウン期間確認（デフォルト300秒）
grep "クールダウン期間中" ../logs/auto_fix.log
```

### Q4: メモリ使用量が多い

```bash
# プロセス確認
ps aux | grep auto_fix_daemon

# メモリ使用量確認
top -p $(pgrep -f auto_fix_daemon)

# ループ回数を減らす
python3 auto_fix_daemon.py --continuous --loop-count 5 --wait-minutes 10
```

## 推奨設定

### 小規模環境（開発・テスト）

```bash
python3 auto_fix_daemon.py --continuous --loop-count 10 --wait-minutes 3
```

- メモリ: 約50MB
- CPU: 1-3%
- チェック頻度: 10回/3分 = 約18秒/回

### 中規模環境（ステージング）

```bash
python3 auto_fix_daemon.py --continuous --loop-count 15 --wait-minutes 5
```

- メモリ: 約70MB
- CPU: 1-5%
- チェック頻度: 15回/5分 = 約20秒/回

### 大規模環境（本番）

```bash
# systemdサービス（推奨）
sudo systemctl start auto-fix-daemon
```

- メモリ制限: 512MB
- CPU制限: 50%
- チェック頻度: 15回/5分 = 約20秒/回
- 自動再起動: 有効

## 次のステップ

1. **設定をカスタマイズ**: `error_patterns.json` を編集してエラーパターンを追加
2. **通知を設定**: メール/Slack通知を実装
3. **監視ダッシュボード**: Grafana等で可視化
4. **アラートルール**: クリティカルエラー時の対応フロー整備

詳細は `README.md` を参照してください。

## サポート

問題が発生した場合:
1. `logs/auto_fix.log` を確認
2. `python3 test_auto_fix.py` でテスト実行
3. `python3 health_monitor.py` でヘルスチェック
4. GitHub Issueを作成
