"""
Marshmallow schemas for request/response validation
リクエスト/レスポンスの検証スキーマ
"""
from marshmallow import Schema, fields, validate, ValidationError

# ============================================================
# Authentication Schemas
# ============================================================

class LoginSchema(Schema):
    """ログインリクエスト検証"""
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=50),
        error_messages={'required': 'ユーザー名は必須です'}
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=6, max=100),
        error_messages={'required': 'パスワードは必須です'}
    )

# ============================================================
# Knowledge Schemas
# ============================================================

class KnowledgeCreateSchema(Schema):
    """ナレッジ作成リクエスト検証"""
    title = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=200),
        error_messages={'required': 'タイトルは必須です'}
    )
    summary = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=500),
        error_messages={'required': '概要は必須です'}
    )
    content = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=50000),
        error_messages={'required': '内容は必須です'}
    )
    category = fields.Str(
        required=True,
        validate=validate.OneOf([
            '施工計画', '品質管理', '安全衛生', '環境対策',
            '原価管理', '出来形管理', 'その他'
        ]),
        error_messages={'required': 'カテゴリは必須です'}
    )
    tags = fields.List(
        fields.Str(validate=validate.Length(max=30)),
        validate=validate.Length(max=20),
        load_default=[]
    )
    owner = fields.Str(
        validate=validate.Length(max=100),
        load_default='unknown'
    )
    project = fields.Str(
        validate=validate.Length(max=100),
        allow_none=True
    )
    priority = fields.Str(
        validate=validate.OneOf(['low', 'medium', 'high']),
        load_default='medium'
    )

class KnowledgeUpdateSchema(Schema):
    """ナレッジ更新リクエスト検証"""
    title = fields.Str(validate=validate.Length(min=1, max=200))
    summary = fields.Str(validate=validate.Length(min=1, max=500))
    content = fields.Str(validate=validate.Length(min=1, max=50000))
    category = fields.Str(
        validate=validate.OneOf([
            '施工計画', '品質管理', '安全衛生', '環境対策',
            '原価管理', '出来形管理', 'その他'
        ])
    )
    tags = fields.List(
        fields.Str(validate=validate.Length(max=30)),
        validate=validate.Length(max=20)
    )
    status = fields.Str(
        validate=validate.OneOf(['draft', 'pending', 'approved', 'archived'])
    )

# ============================================================
# Incident Schemas
# ============================================================

class IncidentCreateSchema(Schema):
    """事故レポート作成リクエスト検証"""
    title = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=200),
        error_messages={'required': 'タイトルは必須です'}
    )
    description = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=5000),
        error_messages={'required': '説明は必須です'}
    )
    project = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=100),
        error_messages={'required': 'プロジェクトは必須です'}
    )
    date = fields.DateTime(required=True)
    severity = fields.Str(
        validate=validate.OneOf(['low', 'medium', 'high', 'critical']),
        load_default='medium'
    )
    corrective_actions = fields.List(
        fields.Str(validate=validate.Length(max=500)),
        load_default=[]
    )
    reporter = fields.Str(
        validate=validate.Length(max=100),
        allow_none=True
    )

# ============================================================
# Consultation Schemas
# ============================================================

class ConsultationCreateSchema(Schema):
    """専門家相談作成リクエスト検証"""
    title = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=500),
        error_messages={'required': 'タイトルは必須です'}
    )
    question = fields.Str(
        required=True,
        validate=validate.Length(min=10, max=5000),
        error_messages={'required': '相談内容は必須です（最小10文字）'}
    )
    category = fields.Str(
        required=True,
        validate=validate.OneOf([
            '技術相談', '安全対策', '品質管理', '工程計画',
            '法令規格', '資材調達', 'その他'
        ]),
        error_messages={'required': 'カテゴリは必須です'}
    )
    priority = fields.Str(
        validate=validate.OneOf(['緊急', '高', '通常', '低']),
        load_default='通常'
    )
    tags = fields.List(
        fields.Str(validate=validate.Length(max=30)),
        validate=validate.Length(max=20),
        load_default=[]
    )
    project = fields.Str(
        validate=validate.Length(max=100),
        allow_none=True
    )

class ConsultationUpdateSchema(Schema):
    """専門家相談更新リクエスト検証"""
    title = fields.Str(validate=validate.Length(min=1, max=500))
    question = fields.Str(validate=validate.Length(min=10, max=5000))
    category = fields.Str(
        validate=validate.OneOf([
            '技術相談', '安全対策', '品質管理', '工程計画',
            '法令規格', '資材調達', 'その他'
        ])
    )
    priority = fields.Str(
        validate=validate.OneOf(['緊急', '高', '通常', '低'])
    )
    tags = fields.List(
        fields.Str(validate=validate.Length(max=30)),
        validate=validate.Length(max=20)
    )
    status = fields.Str(
        validate=validate.OneOf(['pending', 'answered', 'resolved', 'closed'])
    )

class ConsultationAnswerSchema(Schema):
    """専門家相談回答投稿リクエスト検証"""
    content = fields.Str(
        required=True,
        validate=validate.Length(min=10, max=10000),
        error_messages={'required': '回答内容は必須です（最小10文字）'}
    )
    references = fields.Str(
        validate=validate.Length(max=1000),
        allow_none=True
    )
    is_best_answer = fields.Bool(load_default=False)
    attachments = fields.List(
        fields.Str(validate=validate.Length(max=500)),
        load_default=[]
    )
