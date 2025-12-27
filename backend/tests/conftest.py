import json
import pathlib
import sys

import pytest

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

import app_v2


def _write_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )


@pytest.fixture()
def client(tmp_path):
    app = app_v2.app
    app.config['TESTING'] = True
    app.config['DATA_DIR'] = str(tmp_path)
    app.config['JWT_SECRET_KEY'] = 'test-secret'

    # テスト時はレート制限を無効化
    app_v2.limiter.enabled = False

    users = [
        {
            'id': 1,
            'username': 'admin',
            'password_hash': app_v2.hash_password('admin123'),
            'full_name': 'Admin User',
            'department': 'Admin',
            'roles': ['admin']
        }
    ]
    knowledge = [
        {
            'id': 1,
            'title': 'Test Knowledge',
            'summary': 'Test summary',
            'category': 'safety',
            'tags': ['test']
        }
    ]

    _write_json(tmp_path / 'users.json', users)
    _write_json(tmp_path / 'knowledge.json', knowledge)
    _write_json(tmp_path / 'access_logs.json', [])

    with app.test_client() as test_client:
        yield test_client
