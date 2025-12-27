# 負荷テスト・ストレステスト

## 概要

このディレクトリには、ナレッジシステムの負荷テストとストレステストが含まれています。

### 目標値

- **同時接続**: 300ユーザー
- **主要画面応答時間**: 3秒以内
- **検索応答時間**: 2秒以内
- **エラー率**: 1%未満

## ファイル構成

```
load/
├── locustfile.py              # Locust負荷テストシナリオ（5つのユーザーシナリオ）
├── stress_test.py             # ストレステスト（段階的負荷増加）
├── performance_benchmark.py   # パフォーマンスベンチマーク
├── run_load_tests.sh          # 統合実行スクリプト
└── README.md                  # このファイル
```

## セットアップ

### 1. 依存パッケージのインストール

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend
pip install -r requirements.txt
```

### 2. サーバーの起動

負荷テストを実行する前に、バックエンドサーバーを起動してください。

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend
python app.py
```

## 実行方法

### 統合スクリプトで実行（推奨）

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/tests/load
./run_load_tests.sh
```

実行するテストを選択できます:
1. 全て実行
2. パフォーマンスベンチマークのみ
3. Locust負荷テストのみ
4. ストレステストのみ

### 個別実行

#### 1. パフォーマンスベンチマーク

主要画面の応答時間を測定します。

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/tests/load
python3 performance_benchmark.py
```

**測定対象:**
- ダッシュボード（統計、アクティビティ、人気ナレッジ）
- ナレッジ一覧・詳細
- 検索機能（キーワード、横断、全文）
- 通知一覧・未読数
- 承認一覧
- ナレッジ作成・更新

**出力:**
- `reports/benchmark_YYYYMMDD_HHMMSS.json`
- `reports/benchmark_YYYYMMDD_HHMMSS.csv`

#### 2. Locust負荷テスト

5つのユーザーシナリオで負荷テストを実行します。

**ヘッドレスモード（コマンドライン）:**

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/tests/load
locust -f locustfile.py \
    --headless \
    --users 300 \
    --spawn-rate 10 \
    --run-time 5m \
    --host http://localhost:5000 \
    --html reports/locust_report.html \
    --csv reports/locust_report
```

**Webモード（ブラウザUI）:**

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/tests/load
locust -f locustfile.py --host http://localhost:5000
```

その後、ブラウザで http://localhost:8089 を開き、パラメータを設定して実行します。

**ユーザーシナリオ（重み付け）:**
1. ログイン → 検索 → 閲覧（重み: 50）
2. ナレッジ作成（重み: 20）
3. 承認操作（重み: 15）
4. 通知確認（重み: 10）
5. ダッシュボード更新（重み: 5）

#### 3. ストレステスト

段階的に負荷を増加させ、システムの限界値を測定します。

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/tests/load
python3 stress_test.py
```

**負荷レベル:**
- 10ユーザー → 50 → 100 → 200 → 300 → 400 → 500

**測定項目:**
- 応答時間（平均、中央値、P95、P99）
- エラー率
- システムリソース（CPU、メモリ）
- リクエスト/秒（RPS）

**出力:**
- `reports/stress_test_YYYYMMDD_HHMMSS.json`
- `reports/stress_test_YYYYMMDD_HHMMSS.csv`

## レポートの見方

### パフォーマンスベンチマーク

**JSON形式:**
```json
{
  "name": "ナレッジ一覧 - 全件",
  "endpoint": "/api/v1/knowledge",
  "avg_time": 1.234,
  "median_time": 1.200,
  "p95_time": 1.500,
  "success_count": 10,
  "error_count": 0
}
```

**CSV形式:**
各行が1つのエンドポイントの測定結果を表します。

### Locustレポート

**HTML:**
- リクエスト統計（平均応答時間、RPS、エラー率）
- チャート（応答時間、RPS、ユーザー数の推移）
- 失敗の詳細

**CSV:**
- `_stats.csv`: リクエスト統計
- `_failures.csv`: 失敗したリクエスト
- `_exceptions.csv`: 例外の詳細

### ストレステスト

**サマリー情報:**
- 最大安定ユーザー数（エラー率 <= 1%）
- 最も遅いエンドポイント
- 300ユーザー同時接続可能かどうか

## トラブルシューティング

### サーバーが起動していない

```
✗ サーバーが起動していません
```

**解決方法:**
バックエンドサーバーを起動してください。

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend
python app.py
```

### Locustがインストールされていない

```
✗ Locustがインストールされていません
```

**解決方法:**
スクリプトが自動的にインストールしますが、手動でもインストール可能です。

```bash
pip install locust
```

### 認証失敗

```
✗ 認証失敗
```

**解決方法:**
デフォルトの認証情報を確認してください。

- ユーザー名: `admin`
- パスワード: `admin123`

データベースに管理者ユーザーが存在することを確認してください。

### エラー率が高い

エラー率が目標値（1%未満）を超える場合:

1. サーバーのログを確認
2. データベースの接続数を確認
3. システムリソース（CPU、メモリ）を確認
4. ユーザー数を減らして再テスト

## ベストプラクティス

### 負荷テスト実施時の注意点

1. **本番環境では実行しない**
   - テスト環境または専用の負荷テスト環境で実行

2. **段階的に負荷を増加**
   - 突然大きな負荷をかけない
   - 段階的にユーザー数を増やす

3. **システムリソースを監視**
   - CPU、メモリ、ディスク、ネットワークを監視
   - ボトルネックを特定

4. **テストデータの準備**
   - 本番に近いデータ量を用意
   - テスト用のユーザーアカウントを準備

5. **結果の記録と分析**
   - 各テスト結果を保存
   - 過去の結果と比較
   - 改善点を特定

### パフォーマンス改善のヒント

1. **データベース最適化**
   - インデックスの追加
   - クエリの最適化
   - 接続プールの調整

2. **キャッシュの活用**
   - 頻繁にアクセスされるデータをキャッシュ
   - Redis/Memcachedの導入

3. **スケーリング**
   - 水平スケーリング（サーバー台数を増やす）
   - 垂直スケーリング（サーバーのスペックを上げる）

4. **非同期処理**
   - 重い処理は非同期化
   - バックグラウンドジョブの活用

## 継続的な負荷テスト

### CI/CDへの組み込み

定期的に負荷テストを実行し、パフォーマンスの劣化を早期発見します。

```yaml
# .github/workflows/load-test.yml の例
name: Load Test
on:
  schedule:
    - cron: '0 0 * * 0'  # 毎週日曜日
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Load Tests
        run: |
          ./backend/tests/load/run_load_tests.sh
```

### 監視とアラート

本番環境では、以下の指標を継続的に監視します:

- 応答時間（平均、P95、P99）
- エラー率
- スループット（RPS）
- システムリソース（CPU、メモリ）

## 参考資料

- [Locust公式ドキュメント](https://docs.locust.io/)
- [パフォーマンステストのベストプラクティス](https://www.blazemeter.com/blog/performance-testing-best-practices)
