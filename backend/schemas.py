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
        missing=[]
    )
    owner = fields.Str(
        validate=validate.Length(max=100),
        missing='unknown'
    )
    project = fields.Str(
        validate=validate.Length(max=100),
        allow_none=True
    )
    priority = fields.Str(
        validate=validate.OneOf(['low', 'medium', 'high']),
        missing='medium'
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
        missing='medium'
    )
    corrective_actions = fields.List(
        fields.Str(validate=validate.Length(max=500)),
        missing=[]
    )
    reporter = fields.Str(
        validate=validate.Length(max=100),
        allow_none=True
    )
