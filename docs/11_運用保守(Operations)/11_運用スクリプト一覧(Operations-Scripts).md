# 運用スクリプト一覧 (Operations Scripts Reference)

**最終更新**: 2026-01-08  
**バージョン**: 1.0.0

## スクリプト配置場所

```
backend/scripts/
├── create_production_users.py  # 本番ユーザー作成
├── import_data.py               # データインポート
├── migrate_json_to_postgres.py  # PostgreSQL移行
├── backup.sh                    # バックアップ
├── setup_postgres.sh            # PostgreSQL設定
├── setup_ssl_selfsigned.sh      # SSL証明書生成
├── health_monitor.py            # ヘルスチェック
├── auto_fix_daemon.py           # 自動修復
└── security_scan.sh             # セキュリティスキャン
```

## 主要スクリプト

### create_production_users.py
本番ユーザー3件（system_admin, project_manager, engineer01）を作成。bcryptハッシュ化。

### import_data.py
CSVからデータインポート。--dry-run でテスト可能。

### backup.sh
JSON/PostgreSQL/完全バックアップを実行。cron設定推奨（毎日2時）。

### setup_postgres.sh
PostgreSQL初期化（DB/ユーザー/スキーマ/テーブル作成）。

### health_monitor.py
システムヘルスチェック。--interval 60 で継続監視。

詳細は各スクリプトの --help を参照してください。

---

**全スクリプトは backend/scripts/ に格納されています。**
