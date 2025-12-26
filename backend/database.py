"""
データベース設定とセッション管理
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base

# 環境変数から接続文字列を取得
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/mirai_knowledge_db')

# エンジン作成
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # 接続の健全性チェック
    echo=False  # SQLログ出力（開発時はTrue）
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
