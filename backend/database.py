"""
データベース設定とセッション管理
Mirai Knowledge Systems - Phase B-10

PostgreSQLとJSON両方のバックエンドをサポート

環境変数:
    DATABASE_URL: PostgreSQL接続URL
    MKS_USE_JSON: 'true'でJSONモードを強制
    MKS_DATA_DIR: JSONデータディレクトリ
    MKS_DB_POOL_SIZE: コネクションプールサイズ
    MKS_DB_MAX_OVERFLOW: プール超過時の追加接続数
    MKS_DB_POOL_TIMEOUT: 接続タイムアウト（秒）
    MKS_DB_POOL_RECYCLE: 接続再利用時間（秒）
    MKS_DB_ECHO: SQLログ出力
"""

import json
import os
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Generator, Optional

from models import (SOP, AccessLog, Approval, Base, Consultation, Incident,
                    Knowledge, Notification, Regulation, User)
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

# ============================================================
# 設定クラス
# ============================================================


class DatabaseConfig:
    """データベース設定クラス"""

    def __init__(self):
        self.database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:password@localhost:5432/mirai_knowledge_db",
        )
        self.use_json = os.getenv("MKS_USE_JSON", "false").lower() == "true"
        self.json_data_dir = Path(
            os.getenv("MKS_DATA_DIR", Path(__file__).parent / "data")
        )
        self.pool_size = int(os.getenv("MKS_DB_POOL_SIZE", "10"))
        self.max_overflow = int(os.getenv("MKS_DB_MAX_OVERFLOW", "20"))
        self.pool_timeout = int(os.getenv("MKS_DB_POOL_TIMEOUT", "30"))
        self.pool_recycle = int(os.getenv("MKS_DB_POOL_RECYCLE", "3600"))
        self.echo = os.getenv("MKS_DB_ECHO", "false").lower() in ("true", "1", "yes")
        self._postgres_available = None

    def is_postgres_available(self) -> bool:
        """PostgreSQL接続が利用可能かチェック"""
        if self.use_json:
            return False

        if self._postgres_available is not None:
            return self._postgres_available

        try:
            test_engine = create_engine(
                self.database_url,
                poolclass=NullPool,
                connect_args={"connect_timeout": 3},
            )
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self._postgres_available = True
        except Exception:
            self._postgres_available = False

        return self._postgres_available

    def reset_availability_cache(self):
        """可用性キャッシュをリセット"""
        self._postgres_available = None


# グローバル設定インスタンス
config = DatabaseConfig()


# ============================================================
# SQLAlchemyエンジンとセッション（PostgreSQLモード用）
# ============================================================

_engine = None
_session_factory = None
db_session = None


def get_engine():
    """SQLAlchemyエンジンを取得"""
    global _engine
    if _engine is None and not config.use_json:
        _engine = create_engine(
            config.database_url,
            poolclass=QueuePool,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_timeout=config.pool_timeout,
            pool_recycle=config.pool_recycle,
            pool_pre_ping=True,
            echo=config.echo,
        )

        @event.listens_for(_engine, "connect")
        def set_search_path(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("SET search_path TO public, auth, audit")
            cursor.close()

    return _engine


def get_session_factory():
    """セッションファクトリを取得"""
    global _session_factory
    if _session_factory is None and not config.use_json:
        engine = get_engine()
        if engine:
            _session_factory = sessionmaker(
                autocommit=False, autoflush=False, bind=engine
            )
    return _session_factory


# 後方互換性のため
engine = property(lambda self: get_engine())
SessionLocal = property(lambda self: get_session_factory())


def _init_scoped_session():
    """スコープドセッションを初期化"""
    global db_session
    factory = get_session_factory()
    if factory:
        db_session = scoped_session(factory)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """データベースセッションのコンテキストマネージャ"""
    factory = get_session_factory()
    if factory is None:
        raise RuntimeError(
            "Database not configured. Use JSON mode or configure PostgreSQL."
        )

    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db():
    """
    データベースセッションを取得（依存性注入用）
    後方互換性のために維持
    """
    factory = get_session_factory()
    if factory is None:
        raise RuntimeError("Database not configured")

    db = factory()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """データベース初期化"""
    if config.use_json:
        config.json_data_dir.mkdir(parents=True, exist_ok=True)
        print("✅ JSONデータディレクトリを確認しました")
        return

    engine = get_engine()
    if engine:
        with engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS auth"))
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS audit"))
            conn.commit()

        Base.metadata.create_all(bind=engine)
        _init_scoped_session()
        print("✅ データベーステーブルを作成しました")


# ============================================================
# JSONバックエンド（開発・フォールバック用）
# ============================================================


class JSONBackend:
    """JSON形式のデータバックエンド"""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_filepath(self, filename: str) -> Path:
        return self.data_dir / filename

    def load(self, filename: str) -> list:
        """JSONファイルを読み込む"""
        filepath = self._get_filepath(filename)
        if not filepath.exists():
            return []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def save(self, filename: str, data: list) -> None:
        """JSONファイルに保存（アトミック書き込み）"""
        filepath = self._get_filepath(filename)
        temp_path = filepath.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            temp_path.replace(filepath)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

    def find_by_id(self, filename: str, id: int) -> Optional[dict]:
        """IDでアイテムを検索"""
        data = self.load(filename)
        for item in data:
            if item.get("id") == id:
                return item
        return None

    def insert(self, filename: str, item: dict) -> dict:
        """アイテムを挿入"""
        data = self.load(filename)
        max_id = max((d.get("id", 0) for d in data), default=0)
        item["id"] = max_id + 1
        item["created_at"] = datetime.now().isoformat()
        item["updated_at"] = datetime.now().isoformat()
        data.append(item)
        self.save(filename, data)
        return item

    def update(self, filename: str, id: int, updates: dict) -> Optional[dict]:
        """アイテムを更新"""
        data = self.load(filename)
        for i, item in enumerate(data):
            if item.get("id") == id:
                updates["updated_at"] = datetime.now().isoformat()
                data[i].update(updates)
                self.save(filename, data)
                return data[i]
        return None

    def delete(self, filename: str, id: int) -> bool:
        """アイテムを削除"""
        data = self.load(filename)
        initial_len = len(data)
        data = [d for d in data if d.get("id") != id]
        if len(data) < initial_len:
            self.save(filename, data)
            return True
        return False


# グローバルJSONバックエンドインスタンス
json_backend = JSONBackend(config.json_data_dir)


# ============================================================
# 統合データアクセス関数
# ============================================================

# テーブル名とモデルのマッピング
TABLE_MODEL_MAP = {
    "knowledge.json": ("public.knowledge", Knowledge),
    "sop.json": ("public.sop", SOP),
    "regulations.json": ("public.regulations", Regulation),
    "incidents.json": ("public.incidents", Incident),
    "consultations.json": ("public.consultations", Consultation),
    "approvals.json": ("public.approvals", Approval),
    "notifications.json": ("public.notifications", Notification),
    "users.json": ("auth.users", User),
    "access_logs.json": ("audit.access_logs", AccessLog),
}


def item_to_dict(item) -> dict:
    """SQLAlchemyモデルを辞書に変換"""
    if item is None:
        return {}

    result = {}
    for column in item.__table__.columns:
        value = getattr(item, column.name)
        if isinstance(value, datetime):
            value = value.isoformat()
        elif isinstance(value, date):
            value = value.isoformat()
        result[column.name] = value
    return result


def load_data(filename: str) -> list:
    """データを読み込む（PostgreSQLまたはJSON）"""
    if config.use_json or not config.is_postgres_available():
        return json_backend.load(filename)

    if filename not in TABLE_MODEL_MAP:
        return json_backend.load(filename)

    table_name, model_class = TABLE_MODEL_MAP[filename]

    try:
        with get_db_session() as session:
            items = session.query(model_class).all()
            return [item_to_dict(item) for item in items]
    except Exception:
        return json_backend.load(filename)


def save_data(filename: str, data: list) -> None:
    """データを保存（常にJSONにも保存してバックアップ）"""
    json_backend.save(filename, data)


def get_storage_mode() -> str:
    """現在のストレージモードを取得"""
    if config.use_json:
        return "json"
    if config.is_postgres_available():
        return "postgresql"
    return "json_fallback"


# ============================================================
# ヘルスチェック
# ============================================================


def check_database_health() -> dict:
    """データベースの健全性をチェック"""
    mode = get_storage_mode()
    status = {"mode": mode, "healthy": False, "details": {}}

    if mode in ("json", "json_fallback"):
        status["healthy"] = config.json_data_dir.exists()
        status["details"]["data_dir"] = str(config.json_data_dir)
        status["details"]["files"] = len(list(config.json_data_dir.glob("*.json")))
        if mode == "json_fallback":
            status["details"]["fallback_reason"] = "PostgreSQL unavailable"
    else:
        try:
            with get_db_session() as session:
                result = session.execute(text("SELECT version()")).fetchone()
                status["healthy"] = True
                status["details"]["version"] = result[0] if result else "unknown"
                status["details"]["pool_size"] = config.pool_size
        except Exception as e:
            status["healthy"] = False
            status["details"]["error"] = str(e)

    return status
