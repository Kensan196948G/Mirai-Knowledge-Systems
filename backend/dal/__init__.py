"""
DALパッケージ - DataAccessLayerを統合して提供

backend/dal/ パッケージ構成:
  base.py          - BaseDAL（インフラ: JSON/PostgreSQL切り替え）
  knowledge.py     - KnowledgeMixin（ナレッジCRUD）
  notifications.py - NotificationMixin（通知CRUD）
  operations.py    - OperationsMixin（SOP/Incidents/Approvals/Regulations）
  projects.py      - ProjectsMixin（プロジェクト・進捗）
  experts.py       - ExpertsMixin（専門家・統計）
  logs.py          - LogsMixin（アクセスログ）
  ms365.py         - MS365Mixin（MS365同期DAL）
"""

from .base import BaseDAL
from .experts import ExpertsMixin
from .knowledge import KnowledgeMixin
from .logs import LogsMixin
from .ms365 import MS365Mixin
from .notifications import NotificationMixin
from .operations import OperationsMixin
from .projects import ProjectsMixin


class DataAccessLayer(
    KnowledgeMixin,
    NotificationMixin,
    OperationsMixin,
    ProjectsMixin,
    ExpertsMixin,
    LogsMixin,
    MS365Mixin,
    BaseDAL,
):
    """データアクセス抽象化レイヤー（統合クラス）

    各Mixinクラスから全メソッドを継承し、BaseDALのインフラ（
    _use_postgresql, _load_json, _save_json 等）を共有する。
    """

    pass


__all__ = ["DataAccessLayer"]
