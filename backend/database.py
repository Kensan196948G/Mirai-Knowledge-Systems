"""
データベース設定とセッション管理
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base

# 設定を環境変数から取得
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/mirai_knowledge_db')
POOL_SIZE = int(os.getenv('MKS_DB_POOL_SIZE', '10'))
MAX_OVERFLOW = int(os.getenv('MKS_DB_MAX_OVERFLOW', '20'))
POOL_TIMEOUT = int(os.getenv('MKS_DB_POOL_TIMEOUT', '30'))
POOL_RECYCLE = int(os.getenv('MKS_DB_POOL_RECYCLE', '3600'))
ECHO = os.getenv('MKS_DB_ECHO', 'false').lower() in ('true', '1', 'yes')

# エンジン作成（コネクションプーリング設定）
engine = create_engine(
    DATABASE_URL,
    pool_size=POOL_SIZE,          # プールに維持する接続数
    max_overflow=MAX_OVERFLOW,    # プール超過時の追加接続数
    pool_timeout=POOL_TIMEOUT,    # 接続取得のタイムアウト（秒）
    pool_recycle=POOL_RECYCLE,    # 接続の再利用時間（秒）
    pool_pre_ping=True,            # 接続の健全性チェック
    echo=ECHO                      # SQLログ出力（開発時はTrue）
)

# セッションファクトリ
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# スレッドセーフなセッション
db_session = scoped_session(SessionLocal)

def init_db():
    """データベース初期化"""
    # スキーマ作成 (SQLAlchemy 2.0互換)
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS auth"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS audit"))
        conn.commit()

    # テーブル作成
    Base.metadata.create_all(bind=engine)
    print("✅ データベーステーブルを作成しました")

def get_db():
    """
    データベースセッションを取得（依存性注入用）
    
    使用例:
        db = next(get_db())
        try:
            # データベース操作
            ...
        finally:
            db.close()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
