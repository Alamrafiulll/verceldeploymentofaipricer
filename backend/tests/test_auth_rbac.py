from fastapi.testclient import TestClient


def _token(client: TestClient, email: str, password: str) -> str:
    response = client.post('/api/auth/login', json={'email': email, 'password': password})
    assert response.status_code == 200
    return response.json()['access_token']


def test_auth_login_and_me(client: TestClient, seeded_users):
    access_token = _token(client, 'salesmanager@gmail.com', '123456')

    me = client.get('/api/auth/me', headers={'Authorization': f'Bearer {access_token}'})
    assert me.status_code == 200
    assert me.json()['role'] == 'sales'
    assert me.json()['account_status'] == 'active'


def test_invalid_login_rejected(client: TestClient, seeded_users):
    response = client.post(
        '/api/auth/login',
        json={'email': 'salesmanager@gmail.com', 'password': 'bad-password'},
    )
    assert response.status_code == 401


def test_inactive_user_is_blocked_until_admin_activates(client: TestClient, seeded_users):
    admin_token = _token(client, 'admin@gmail.com', '123456')

    create_user = client.post(
        '/api/admin/users',
        json={
            'name': 'Inactive User',
            'email': 'inactive@test.local',
            'password': '123456',
            'role': 'sales',
            'account_status': 'inactive',
        },
        headers={'Authorization': f'Bearer {admin_token}'},
    )
    assert create_user.status_code == 201
    created_user_id = create_user.json()['id']

    blocked = client.post(
        '/api/auth/login',
        json={'email': 'inactive@test.local', 'password': '123456'},
    )
    assert blocked.status_code == 403
    assert 'inactive' in blocked.json()['detail'].lower()

    activate = client.patch(
        f'/api/admin/users/{created_user_id}/status',
        json={'account_status': 'active'},
        headers={'Authorization': f'Bearer {admin_token}'},
    )
    assert activate.status_code == 200
    assert activate.json()['account_status'] == 'active'

    now_allowed = client.post(
        '/api/auth/login',
        json={'email': 'inactive@test.local', 'password': '123456'},
    )
    assert now_allowed.status_code == 200


def test_admin_can_reset_and_delete_user(client: TestClient, seeded_users):
    admin_token = _token(client, 'admin@gmail.com', '123456')

    created = client.post(
        '/api/admin/users',
        json={
            'name': 'Ops User',
            'email': 'ops@test.local',
            'password': '123456',
            'role': 'approver',
            'account_status': 'active',
        },
        headers={'Authorization': f'Bearer {admin_token}'},
    )
    assert created.status_code == 201
    user_id = created.json()['id']

    reset = client.post(
        f'/api/admin/users/{user_id}/reset-password',
        json={'new_password': 'New123456'},
        headers={'Authorization': f'Bearer {admin_token}'},
    )
    assert reset.status_code == 200
    assert reset.json()['message']
    assert 'generated_password' not in reset.json()

    login_new_password = client.post(
        '/api/auth/login',
        json={'email': 'ops@test.local', 'password': 'New123456'},
    )
    assert login_new_password.status_code == 200

    delete_resp = client.delete(
        f'/api/admin/users/{user_id}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )
    assert delete_resp.status_code == 204

    login_after_delete = client.post(
        '/api/auth/login',
        json={'email': 'ops@test.local', 'password': 'New123456'},
    )
    assert login_after_delete.status_code == 401


def test_admin_cannot_deactivate_own_account(client: TestClient, seeded_users):
    admin_token = _token(client, 'admin@gmail.com', '123456')
    me = client.get('/api/auth/me', headers={'Authorization': f'Bearer {admin_token}'})
    assert me.status_code == 200
    admin_id = me.json()['id']

    response = client.patch(
        f'/api/admin/users/{admin_id}/status',
        json={'account_status': 'inactive'},
        headers={'Authorization': f'Bearer {admin_token}'},
    )
    assert response.status_code == 400
    assert 'cannot deactivate own account' in response.json()['detail'].lower()


def test_admin_reset_requires_explicit_new_password(client: TestClient, seeded_users):
    admin_token = _token(client, 'admin@gmail.com', '123456')
    users = client.get('/api/admin/users', headers={'Authorization': f'Bearer {admin_token}'})
    assert users.status_code == 200
    target = next(user for user in users.json() if user['email'] == 'salesmanager@gmail.com')

    reset = client.post(
        f"/api/admin/users/{target['id']}/reset-password",
        json={'new_password': None},
        headers={'Authorization': f'Bearer {admin_token}'},
    )
    assert reset.status_code == 400
    assert 'required' in reset.json()['detail'].lower()


def test_rbac_blocks_sales_from_admin_routes(client: TestClient, seeded_users):
    sales_token = _token(client, 'salesmanager@gmail.com', '123456')

    blocked = client.get(
        '/api/admin/audit-logs',
        headers={'Authorization': f'Bearer {sales_token}'},
    )
    assert blocked.status_code == 403

