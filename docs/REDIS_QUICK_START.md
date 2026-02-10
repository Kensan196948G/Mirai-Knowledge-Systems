# Redis クイックスタートガイド

## 🚀 5分でRedis有効化

### 前提条件
- sudo権限のあるLinux/macOS環境
- Mirai Knowledge Systems Phase F-2実装済み

---

## インストール（1分）

### Ubuntu/Debian/WSL2
```bash
sudo apt update && sudo apt install -y redis-server
```

### CentOS/RHEL
```bash
sudo yum install -y redis
```

### macOS
```bash
brew install redis
```

---

## 起動（30秒）

```bash
# サービス有効化・起動
sudo systemctl enable redis-server
sudo systemctl start redis-server

# 動作確認
redis-cli ping
# 期待出力: PONG
```

---

## アプリケーション再起動（30秒）

```bash
# 開発環境
sudo systemctl restart mirai-knowledge-app-dev

# 本番環境
sudo systemctl restart mirai-knowledge-app
```

---

## 動作確認（1分）

### ログ確認
```bash
tail -f /var/log/mirai-knowledge-app/app.log | grep -i cache
```

期待出力:
```
[INFO] Cache set: search:建設:knowledge|sop|law:1:20:created_at:desc
[INFO] Cache hit: search:建設:knowledge|sop|law:1:20:created_at:desc
```

### パフォーマンステスト
```bash
# JWTトークン取得（ログイン）
TOKEN=$(curl -s -X POST http://localhost:5200/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access_token')

# 初回リクエスト（キャッシュミス）
time curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:5200/api/v1/search/unified?query=建設" > /dev/null
# 期待: 200ms前後

# 2回目リクエスト（キャッシュヒット）
time curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:5200/api/v1/search/unified?query=建設" > /dev/null
# 期待: 5ms前後（97.5%改善！）
```

---

## トラブルシューティング

### ❌ `redis-cli: command not found`
```bash
# Redisがインストールされていない
sudo apt install -y redis-server
```

### ❌ `Could not connect to Redis at 127.0.0.1:6379`
```bash
# Redisサービスが起動していない
sudo systemctl start redis-server
```

### ❌ アプリケーションログに `Cache` が表示されない
```bash
# アプリケーションを再起動していない
sudo systemctl restart mirai-knowledge-app-dev
```

---

## 本番環境推奨設定（オプション）

### `/etc/redis/redis.conf`
```conf
# メモリ上限（物理メモリの50%推奨）
maxmemory 2gb
maxmemory-policy allkeys-lru

# パスワード認証
requirepass your_secure_password_here

# バックグラウンド保存無効化（キャッシュ専用）
save ""
```

### `.env`
```env
REDIS_URL=redis://:your_secure_password@localhost:6379/0
CACHE_TTL=3600  # 1時間
```

設定反映:
```bash
sudo systemctl restart redis-server
sudo systemctl restart mirai-knowledge-app
```

---

## 📊 期待効果

| 指標 | 改善率 |
|------|--------|
| API応答時間 | 97.5% ↓ |
| データベース負荷 | 95% ↓ |
| 同時接続数 | 5倍 ↑ |
| スループット | 10倍 ↑ |

---

## 詳細ドキュメント

Phase F-2完了レポート: `docs/PHASE_F2_COMPLETION_REPORT.md`
