"""
データベースモデル定義
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Date,
    Boolean,
    ARRAY,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, INET
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()

# ============================================================
# Public Schema - ナレッジドメイン
# ============================================================


class Knowledge(Base):
    """ナレッジ"""

    __tablename__ = "knowledge"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=False)
    content = Column(Text)
    category = Column(String(100), nullable=False)
    tags = Column(ARRAY(String))
    status = Column(String(50), default="draft")
    priority = Column(String(20), default="medium")
    project = Column(String(100))
    owner = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("auth.users.id"))
    updated_by_id = Column(Integer, ForeignKey("auth.users.id"))

    # リレーション
    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])

    # インデックス（パフォーマンス最適化）
    __table_args__ = (
        Index("idx_knowledge_category", "category"),
        Index("idx_knowledge_status", "status"),
        Index("idx_knowledge_updated", "updated_at"),
        Index("idx_knowledge_title", "title"),  # タイトル検索用
        Index("idx_knowledge_owner", "owner"),  # 所有者検索用
        Index("idx_knowledge_project", "project"),  # プロジェクト検索用
        {"schema": "public"},
    )


class SOP(Base):
    """標準施工手順"""

    __tablename__ = "sop"

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    category = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    revision_date = Column(Date, nullable=False)
    target = Column(String(200))
    tags = Column(ARRAY(String))
    content = Column(Text, nullable=False)
    status = Column(String(50), default="active")
    supersedes_id = Column(Integer, ForeignKey("public.sop.id"))
    attachments = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("auth.users.id"))
    updated_by_id = Column(Integer, ForeignKey("auth.users.id"))

    # インデックス
    __table_args__ = (
        Index("idx_sop_category", "category"),
        Index("idx_sop_status", "status"),
        Index("idx_sop_title", "title"),
        Index("idx_sop_version", "version"),
        {"schema": "public"},
    )


class Regulation(Base):
    """法令・規格"""

    __tablename__ = "regulations"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    issuer = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    revision_date = Column(Date, nullable=False)
    applicable_scope = Column(ARRAY(String))
    summary = Column(Text, nullable=False)
    content = Column(Text)
    status = Column(String(50), default="active")
    effective_date = Column(Date)
    url = Column(String(1000))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Incident(Base):
    """事故・ヒヤリレポート"""

    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    project = Column(String(100), nullable=False)
    incident_date = Column(Date, nullable=False)
    severity = Column(String(50), nullable=False)
    status = Column(String(50), default="reported")
    corrective_actions = Column(JSONB)
    root_cause = Column(Text)
    tags = Column(ARRAY(String))
    location = Column(String(300))
    involved_parties = Column(ARRAY(String))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reporter_id = Column(Integer, ForeignKey("auth.users.id"))

    reporter = relationship("User", foreign_keys=[reporter_id])

    # インデックス
    __table_args__ = (
        Index("idx_incident_project", "project"),
        Index("idx_incident_severity", "severity"),
        Index("idx_incident_status", "status"),
        Index("idx_incident_date", "incident_date"),
        {"schema": "public"},
    )


class Consultation(Base):
    """専門家相談"""

    __tablename__ = "consultations"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    question = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    priority = Column(String(20), default="medium")
    status = Column(String(50), default="pending")
    requester_id = Column(Integer, ForeignKey("auth.users.id"))
    expert_id = Column(Integer, ForeignKey("auth.users.id"))
    answer = Column(Text)
    answered_at = Column(DateTime)
    knowledge_id = Column(Integer, ForeignKey("public.knowledge.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    requester = relationship("User", foreign_keys=[requester_id])
    expert = relationship("User", foreign_keys=[expert_id])
    knowledge = relationship("Knowledge")


class Approval(Base):
    """承認フロー"""

    __tablename__ = "approvals"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    type = Column(String(100), nullable=False)
    description = Column(Text)
    requester_id = Column(Integer, ForeignKey("auth.users.id"))
    status = Column(String(50), default="pending")
    priority = Column(String(20), default="medium")
    related_entity_type = Column(String(50))
    related_entity_id = Column(Integer)
    approval_flow = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = Column(DateTime)
    approver_id = Column(Integer, ForeignKey("auth.users.id"))

    requester = relationship("User", foreign_keys=[requester_id])
    approver = relationship("User", foreign_keys=[approver_id])


class Notification(Base):
    """通知配信"""

    __tablename__ = "notifications"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)
    target_users = Column(ARRAY(Integer))
    target_roles = Column(ARRAY(String))
    delivery_channels = Column(ARRAY(String))
    related_entity_type = Column(String(50))
    related_entity_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime)
    status = Column(String(50), default="pending")


class NotificationRead(Base):
    """通知既読管理"""

    __tablename__ = "notification_reads"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    notification_id = Column(Integer, ForeignKey("public.notifications.id"))
    user_id = Column(Integer, ForeignKey("auth.users.id"))
    read_at = Column(DateTime, default=datetime.utcnow)

    notification = relationship("Notification")
    user = relationship("User")


# ============================================================
# Auth Schema - 認証・認可
# ============================================================


class User(Base):
    """ユーザー"""

    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200))
    department = Column(String(100))
    position = Column(String(100))
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    mfa_secret = Column(String(32))  # TOTP secret for MFA
    mfa_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーション
    roles = relationship("UserRole", back_populates="user")

    def set_password(self, password):
        """パスワードをハッシュ化して設定"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """パスワードを検証"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """辞書形式に変換"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "department": self.department,
            "position": self.position,
            "is_active": self.is_active,
        }


class Role(Base):
    """役割"""

    __tablename__ = "roles"
    __table_args__ = {"schema": "auth"}

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # リレーション
    users = relationship("UserRole", back_populates="role")
    permissions = relationship("RolePermission", back_populates="role")


class Permission(Base):
    """権限"""

    __tablename__ = "permissions"
    __table_args__ = {"schema": "auth"}

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    resource = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)
    description = Column(Text)

    roles = relationship("RolePermission", back_populates="permission")


class UserRole(Base):
    """ユーザー役割関連"""

    __tablename__ = "user_roles"
    __table_args__ = {"schema": "auth"}

    user_id = Column(Integer, ForeignKey("auth.users.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("auth.roles.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")


class RolePermission(Base):
    """役割権限関連"""

    __tablename__ = "role_permissions"
    __table_args__ = {"schema": "auth"}

    role_id = Column(Integer, ForeignKey("auth.roles.id"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("auth.permissions.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="roles")


# ============================================================
# Project Schema - プロジェクト管理
# ============================================================


class Project(Base):
    """プロジェクト"""

    __tablename__ = "projects"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    type = Column(String(50), nullable=False)  # 橋梁, 道路, 河川, 砂防, トンネル
    status = Column(String(50), default="planning")
    start_date = Column(Date)
    end_date = Column(Date)
    budget = Column(Integer)  # 予算（万円）
    location = Column(String(200))
    manager_id = Column(Integer, ForeignKey("auth.users.id"))
    progress_percentage = Column(Integer, default=0)  # 進捗率（0-100）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーション
    manager = relationship("User", foreign_keys=[manager_id])

    # インデックス
    __table_args__ = (
        Index("idx_project_code", "code"),
        Index("idx_project_status", "status"),
        Index("idx_project_type", "type"),
        Index("idx_project_manager", "manager_id"),
        {"schema": "public"},
    )


class ProjectTask(Base):
    """プロジェクトタスク"""

    __tablename__ = "project_tasks"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("public.projects.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(
        String(50), default="pending"
    )  # pending, in_progress, completed, cancelled
    priority = Column(String(20), default="medium")
    assigned_to_id = Column(Integer, ForeignKey("auth.users.id"))
    start_date = Column(Date)
    end_date = Date
    estimated_hours = Column(Integer)
    actual_hours = Column(Integer)
    progress_percentage = Column(Integer, default=0)  # 進捗率（0-100）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーション
    project = relationship("Project")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])

    # インデックス
    __table_args__ = (
        Index("idx_task_project", "project_id"),
        Index("idx_task_status", "status"),
        Index("idx_task_assigned", "assigned_to_id"),
        {"schema": "public"},
    )


# ============================================================
# Expert Schema - 専門家管理
# ============================================================


class Expert(Base):
    """専門家"""

    __tablename__ = "experts"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth.users.id"), nullable=False)
    specialization = Column(String(100), nullable=False)  # 専門分野
    experience_years = Column(Integer, default=0)
    certifications = Column(ARRAY(String))  # 資格
    rating = Column(Integer, default=0)  # 評価（1-5）
    consultation_count = Column(Integer, default=0)  # 相談件数
    response_time_avg = Column(Integer)  # 平均応答時間（分）
    is_available = Column(Boolean, default=True)
    bio = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーション
    user = relationship("User")

    # インデックス
    __table_args__ = (
        Index("idx_expert_user", "user_id"),
        Index("idx_expert_specialization", "specialization"),
        Index("idx_expert_rating", "rating"),
        {"schema": "public"},
    )


class ExpertRating(Base):
    """専門家評価"""

    __tablename__ = "expert_ratings"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    expert_id = Column(Integer, ForeignKey("public.experts.id"), nullable=False)
    requester_id = Column(Integer, ForeignKey("auth.users.id"), nullable=False)
    consultation_id = Column(
        Integer, ForeignKey("public.consultations.id"), nullable=False
    )
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # リレーション
    expert = relationship("Expert")
    requester = relationship("User", foreign_keys=[requester_id])
    consultation = relationship("Consultation")

    # インデックス
    __table_args__ = (
        Index("idx_rating_expert", "expert_id"),
        Index("idx_rating_consultation", "consultation_id"),
        {"schema": "public"},
    )


# ============================================================
# Audit Schema - 監査
# ============================================================


class AccessLog(Base):
    """アクセスログ"""

    __tablename__ = "access_logs"
    __table_args__ = {"schema": "audit"}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth.users.id"))
    username = Column(String(100))
    action = Column(String(100), nullable=False)
    resource = Column(String(100))
    resource_id = Column(Integer)
    ip_address = Column(INET)
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class ChangeLog(Base):
    """変更ログ"""

    __tablename__ = "change_logs"
    __table_args__ = {"schema": "audit"}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth.users.id"))
    username = Column(String(100))
    table_name = Column(String(100), nullable=False)
    record_id = Column(Integer)
    action = Column(String(50), nullable=False)
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class DistributionLog(Base):
    """配信ログ"""

    __tablename__ = "distribution_logs"
    __table_args__ = {"schema": "audit"}

    id = Column(Integer, primary_key=True)
    notification_id = Column(Integer, ForeignKey("public.notifications.id"))
    user_id = Column(Integer, ForeignKey("auth.users.id"))
    delivery_channel = Column(String(50))
    status = Column(String(50))
    sent_at = Column(DateTime)
    read_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    notification = relationship("Notification")
    user = relationship("User")
