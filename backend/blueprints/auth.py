"""
認証関連APIエンドポイント - Blueprint版
Phase G-3-1: app_v2.py auth エンドポイント分割準備

現状: app_v2.pyの@app.routeで定義された認証エンドポイントのコピー
将来: app_v2.pyから段階的に移行予定
"""
from flask import Blueprint

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

# Phase G-3-2で段階的にエンドポイントを移行予定
# 現在はapp_v2.pyの既存ルートが有効
# このBlueprint登録は app_v2.pyのルートと競合しないよう注意
