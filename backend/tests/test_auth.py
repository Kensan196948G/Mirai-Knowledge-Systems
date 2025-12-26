
def _login(client, username='admin', password='admin123'):
    response = client.post(
        '/api/v1/auth/login',
        json={'username': username, 'password': password}
    )
    return response


def test_login_success(client):
    response = _login(client)
    assert response.status_code == 200
    payload = response.get_json()
    assert payload['success'] is True
    assert 'access_token' in payload['data']


def test_login_failure(client):
    response = _login(client, password='wrong')
    assert response.status_code == 401


def test_knowledge_requires_auth(client):
    response = client.get('/api/v1/knowledge')
    assert response.status_code == 401


def test_knowledge_list_with_auth(client):
    login_response = _login(client)
    token = login_response.get_json()['data']['access_token']

    response = client.get(
        '/api/v1/knowledge',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload['success'] is True
    assert payload['pagination']['total_items'] == 1
