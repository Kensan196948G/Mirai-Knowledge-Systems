-- PostgreSQL初期化スクリプト
-- Docker Composeで自動実行される

-- 日本語対応の拡張機能をインストール
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- スキーマ作成
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS audit;

-- コメント追加
COMMENT ON SCHEMA public IS 'ナレッジドメイン';
COMMENT ON SCHEMA auth IS '認証・認可';
COMMENT ON SCHEMA audit IS '監査ログ';

-- データベース作成完了メッセージ
DO $$
BEGIN
  RAISE NOTICE 'PostgreSQL初期化が完了しました';
END $$;
