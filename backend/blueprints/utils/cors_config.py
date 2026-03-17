"""
blueprints/utils/cors_config.py - CORS設定・IP検出ユーティリティ

Phase M-1: app_v2.py から抽出（~85行）
"""

import logging
import os
import socket

logger = logging.getLogger(__name__)


def get_local_ip_addresses():
    """ローカルネットワークのIPアドレスを自動検出"""
    ips = set()

    # 標準的なlocalhostアドレス
    ips.add("127.0.0.1")
    ips.add("localhost")

    try:
        # ホスト名からIPを取得
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
            ips.add(local_ip)
        except socket.gaierror:
            pass

        # 全ネットワークインターフェースのIPを取得
        try:
            for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
                ips.add(info[4][0])
        except socket.gaierror:
            pass

        # UDPソケットを使用した外部接続経由でのIP検出
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.1)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            ips.add(local_ip)
            s.close()
        except Exception as e:
            logger.debug(
                "Failed to determine local IP via 8.8.8.8 connection: %s", str(e)
            )

        # 一般的なプライベートIPレンジのプレフィックス
        for ip in list(ips):
            if (
                ip.startswith("192.168.")
                or ip.startswith("10.")
                or ip.startswith("172.")
            ):
                pass  # 既に追加済み

    except Exception as e:
        logger.warning("Failed to detect local IPs: %s", e)

    return list(ips)


def build_cors_origins(app_config):
    """CORS許可オリジンリストを構築（動的IP対応）

    Args:
        app_config: get_config() で取得したAppConfigオブジェクト
    """
    base_origins = getattr(app_config, "CORS_ORIGINS", ["http://localhost:5200"])
    if isinstance(base_origins, str):
        base_origins = [base_origins]

    origins = set(base_origins)

    if os.environ.get("MKS_ENV", "development").lower() == "development":
        port = os.environ.get("MKS_HTTP_PORT", "5200")
        https_port = os.environ.get("MKS_HTTPS_PORT", "5243")

        for ip in get_local_ip_addresses():
            origins.add(f"http://{ip}:{port}")
            origins.add(f"https://{ip}:{https_port}")
            origins.add(f"http://{ip}")
            origins.add(f"https://{ip}")
    else:
        port = os.environ.get("MKS_HTTP_PORT", "9100")
        https_port = os.environ.get("MKS_HTTPS_PORT", "9443")
        for ip in get_local_ip_addresses():
            origins.add(f"http://{ip}:{port}")
            origins.add(f"https://{ip}:{https_port}")

    return list(origins)
