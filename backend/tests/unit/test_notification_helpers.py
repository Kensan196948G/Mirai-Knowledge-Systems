import json
import pathlib

import app_v2


def _write_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )


def test_env_bool_parsing(monkeypatch):
    monkeypatch.delenv('MKS_TEST_BOOL', raising=False)
    assert app_v2._env_bool('MKS_TEST_BOOL', default=True) is True

    monkeypatch.setenv('MKS_TEST_BOOL', 'true')
    assert app_v2._env_bool('MKS_TEST_BOOL') is True

    monkeypatch.setenv('MKS_TEST_BOOL', '0')
    assert app_v2._env_bool('MKS_TEST_BOOL') is False


def test_external_notification_types(monkeypatch):
    monkeypatch.delenv('MKS_EXTERNAL_NOTIFICATION_TYPES', raising=False)
    assert app_v2._external_notification_types() is None

    monkeypatch.setenv('MKS_EXTERNAL_NOTIFICATION_TYPES', ' approval_required, incident ')
    assert app_v2._external_notification_types() == {'approval_required', 'incident'}


def test_should_send_external(monkeypatch):
    monkeypatch.delenv('MKS_EXTERNAL_NOTIFICATION_TYPES', raising=False)
    assert app_v2._should_send_external('approval_required') is True

    monkeypatch.setenv('MKS_EXTERNAL_NOTIFICATION_TYPES', 'incident')
    assert app_v2._should_send_external('approval_required') is False
    assert app_v2._should_send_external('incident') is True


def test_get_notification_recipients(client):
    data_dir = pathlib.Path(app_v2.app.config['DATA_DIR'])
    users_file = data_dir / 'users.json'

    users = [
        {'id': 1, 'roles': ['admin'], 'email': 'admin@example.com'},
        {'id': 2, 'roles': ['partner_company'], 'email': 'partner@example.com'},
        {'id': 3, 'roles': ['admin'], 'email': 'admin@example.com'},
        {'id': 4, 'roles': ['admin']}
    ]
    _write_json(users_file, users)

    recipients = app_v2._get_notification_recipients(
        target_users=[2],
        target_roles=['admin']
    )

    assert recipients == ['admin@example.com', 'partner@example.com']


def test_get_notification_recipients_empty():
    assert app_v2._get_notification_recipients([], []) == []
