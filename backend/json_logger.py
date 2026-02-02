"""
JSON形式の構造化ログ実装
Mirai Knowledge System

このモジュールはアプリケーションのログをJSON形式で出力し、
ログ分析・監視システムとの統合を容易にします。

機能:
- JSON形式のログフォーマット
- リクエストID追跡
- ユーザーID記録
- タイムスタンプ（ISO 8601形式）
- ログレベル管理
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional

from flask import g, has_request_context, request


class JSONFormatter(logging.Formatter):
    """
    JSON形式でログを出力するカスタムフォーマッタ

    出力例:
    {
        "timestamp": "2026-01-09T09:30:00.123456",
        "level": "ERROR",
        "logger": "app_v2",
        "message": "Failed to authenticate user",
        "module": "app_v2",
        "function": "login",
        "line": 142,
        "user_id": 5,
        "request_id": "abc-def-123",
        "ip_address": "192.168.1.100",
        "method": "POST",
        "path": "/api/v1/auth/login",
        "exception": "ValueError: Invalid credentials"
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        ログレコードをJSON形式に変換

        Args:
            record: ログレコード

        Returns:
            JSON形式の文字列
        """
        # 基本情報
        log_data: Dict[str, Any] = {
            "timestamp": self._format_timestamp(record.created),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # リクエストコンテキスト情報
        if has_request_context():
            log_data.update(self._get_request_context())

        # カスタムフィールド（record に設定された追加情報）
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        # 例外情報
        if record.exc_info:
            log_data["exception"] = self._format_exception(record.exc_info)
            log_data["stack_trace"] = self._format_stack_trace(record.exc_info)

        # JSON文字列に変換（日本語を保持）
        return json.dumps(log_data, ensure_ascii=False, default=str)

    def _format_timestamp(self, created: float) -> str:
        """
        タイムスタンプをISO 8601形式に変換

        Args:
            created: UNIX タイムスタンプ

        Returns:
            ISO 8601形式のタイムスタンプ
        """
        dt = datetime.fromtimestamp(created)
        return dt.isoformat()

    def _get_request_context(self) -> Dict[str, Any]:
        """
        Flaskリクエストコンテキストから情報を取得

        Returns:
            リクエスト情報の辞書
        """
        context = {}

        try:
            # リクエストID（g.request_id があれば使用）
            if hasattr(g, "request_id"):
                context["request_id"] = g.request_id

            # ユーザーID（g.current_user があれば使用）
            if hasattr(g, "current_user") and g.current_user:
                context["user_id"] = g.current_user.get("id")

            # IPアドレス
            if request.remote_addr:
                context["ip_address"] = request.remote_addr

            # HTTPメソッド
            context["method"] = request.method

            # リクエストパス
            context["path"] = request.path

            # User-Agent
            if request.user_agent:
                context["user_agent"] = request.user_agent.string

            # Referer
            if request.referrer:
                context["referer"] = request.referrer

        except Exception:
            # コンテキスト取得失敗時は無視
            pass

        return context

    def _format_exception(self, exc_info) -> str:
        """
        例外情報を文字列に変換

        Args:
            exc_info: sys.exc_info() の戻り値

        Returns:
            例外の文字列表現
        """
        exc_type, exc_value, _ = exc_info
        return f"{exc_type.__name__}: {exc_value}"

    def _format_stack_trace(self, exc_info) -> str:
        """
        スタックトレースを文字列に変換

        Args:
            exc_info: sys.exc_info() の戻り値

        Returns:
            スタックトレースの文字列
        """
        return "".join(traceback.format_exception(*exc_info))


class ContextualLogger:
    """
    コンテキスト情報を自動的に付加するロガーラッパー

    使用例:
        logger = ContextualLogger('my_module')
        logger.info('User logged in')  # user_id, request_id が自動付加
    """

    def __init__(self, name: str):
        """
        初期化

        Args:
            name: ロガー名
        """
        self.logger = logging.getLogger(name)

    def _add_context(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        コンテキスト情報を追加

        Args:
            extra: 追加のコンテキスト情報

        Returns:
            コンテキスト情報を含む辞書
        """
        context = extra or {}

        if has_request_context():
            if hasattr(g, "request_id"):
                context["request_id"] = g.request_id

            if hasattr(g, "current_user") and g.current_user:
                context["user_id"] = g.current_user.get("id")

        return context

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """DEBUGレベルのログ出力"""
        self.logger.debug(message, extra=self._add_context(extra))

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """INFOレベルのログ出力"""
        self.logger.info(message, extra=self._add_context(extra))

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """WARNINGレベルのログ出力"""
        self.logger.warning(message, extra=self._add_context(extra))

    def error(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
    ):
        """ERRORレベルのログ出力"""
        self.logger.error(message, extra=self._add_context(extra), exc_info=exc_info)

    def critical(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
    ):
        """CRITICALレベルのログ出力"""
        self.logger.critical(message, extra=self._add_context(extra), exc_info=exc_info)


def setup_json_logging(
    app,
    log_file: str = "/var/log/mirai-knowledge/app.log",
    log_level: str = "INFO",
    enable_console: bool = False,
):
    """
    FlaskアプリケーションにJSON形式のログを設定

    Args:
        app: Flaskアプリケーション
        log_file: ログファイルパス
        log_level: ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        enable_console: コンソール出力を有効化
    """
    # ログレベル設定
    level = getattr(logging, log_level.upper(), logging.INFO)
    app.logger.setLevel(level)

    # 既存のハンドラをクリア
    app.logger.handlers.clear()

    # ファイルハンドラ（JSON形式）
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(JSONFormatter())
    app.logger.addHandler(file_handler)

    # コンソールハンドラ（開発環境用）
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(JSONFormatter())
        app.logger.addHandler(console_handler)

    # propagate を無効化（重複ログ防止）
    app.logger.propagate = False

    app.logger.info(
        "JSON logging configured", extra={"log_file": log_file, "log_level": log_level}
    )


def log_request_info(logger: logging.Logger):
    """
    リクエスト開始時にログ出力（デコレーター用）

    使用例:
        @app.before_request
        def before_request():
            log_request_info(app.logger)
    """
    if has_request_context():
        logger.info(
            "Request started",
            extra={
                "method": request.method,
                "path": request.path,
                "ip_address": request.remote_addr,
            },
        )


def log_response_info(logger: logging.Logger, response, duration_ms: float):
    """
    レスポンス送信時にログ出力（デコレーター用）

    使用例:
        @app.after_request
        def after_request(response):
            log_response_info(app.logger, response, duration)
            return response
    """
    if has_request_context():
        logger.info(
            "Request completed",
            extra={
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "content_length": response.content_length,
            },
        )
