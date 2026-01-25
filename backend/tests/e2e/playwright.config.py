"""
Playwright E2E Test Configuration
クロスブラウザテスト設定
"""

# ブラウザ設定
BROWSERS = {
    'chromium': {
        'name': 'Chromium',
        'channel': None,
        'headless': True,
    },
    'firefox': {
        'name': 'Firefox',
        'channel': None,
        'headless': True,
    },
    'webkit': {
        'name': 'WebKit (Safari)',
        'channel': None,
        'headless': True,
    },
}

# デバイス設定（レスポンシブテスト用）
DEVICES = {
    'desktop': {
        'viewport': {'width': 1920, 'height': 1080},
        'device_scale_factor': 1,
        'is_mobile': False,
    },
    'tablet': {
        'viewport': {'width': 768, 'height': 1024},
        'device_scale_factor': 2,
        'is_mobile': True,
    },
    'mobile': {
        'viewport': {'width': 375, 'height': 667},
        'device_scale_factor': 2,
        'is_mobile': True,
    },
}

# テスト設定
TEST_CONFIG = {
    'base_url': 'http://localhost:5100',
    'timeout': 30000,  # 30秒
    'retries': 2,
    'screenshot_on_failure': True,
    'video_on_failure': True,
    'trace_on_failure': True,
}

# レポート出力設定
REPORT_CONFIG = {
    'output_dir': 'tests/reports/e2e',
    'screenshots_dir': 'tests/reports/e2e/screenshots',
    'videos_dir': 'tests/reports/e2e/videos',
    'traces_dir': 'tests/reports/e2e/traces',
}
