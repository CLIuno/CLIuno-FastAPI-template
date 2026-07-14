from tests.conftest import auth_header


class TestRegister:
    def test_register_success(self, client, user_role):
        res = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "new@test.com",
                "first_name": "New",
                "last_name": "User",
                "password": "password123",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["status"] == "success"
        assert data["data"]["access_token"]
        assert data["data"]["refresh_token"]
        assert data["data"]["user"]["username"] == "newuser"

    def test_register_duplicate_username(self, client, regular_user, user_role):
        res = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "other@test.com",
                "first_name": "New",
                "last_name": "User",
                "password": "password123",
            },
        )
        assert res.status_code == 400

    def test_register_duplicate_email(self, client, regular_user, user_role):
        res = client.post(
            "/api/v1/auth/register",
            json={
                "username": "otheruser",
                "email": "test@test.com",
                "first_name": "New",
                "last_name": "User",
                "password": "password123",
            },
        )
        assert res.status_code == 400

    def test_register_short_password(self, client, user_role):
        res = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "new@test.com",
                "first_name": "New",
                "last_name": "User",
                "password": "12345",
            },
        )
        assert res.status_code == 400


class TestLogin:
    def test_login_with_username(self, client, regular_user):
        res = client.post(
            "/api/v1/auth/login",
            json={
                "login": "testuser",
                "password": "password",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["data"]["access_token"]

    def test_login_with_email(self, client, regular_user):
        res = client.post(
            "/api/v1/auth/login",
            json={
                "login": "test@test.com",
                "password": "password",
            },
        )
        assert res.status_code == 200

    def test_login_invalid_credentials(self, client, regular_user):
        res = client.post(
            "/api/v1/auth/login",
            json={
                "login": "testuser",
                "password": "wrongpassword",
            },
        )
        assert res.status_code == 401

    def test_login_nonexistent_user(self, client, user_role):
        res = client.post(
            "/api/v1/auth/login",
            json={
                "login": "nobody",
                "password": "password",
            },
        )
        assert res.status_code == 401


class TestLogout:
    def test_logout(self, client, user_token):
        res = client.post("/api/v1/auth/logout", headers=auth_header(user_token))
        assert res.status_code == 200
        assert res.json()["status"] == "success"

    def test_logout_unauthenticated(self, client):
        res = client.post("/api/v1/auth/logout")
        assert res.status_code == 401

    def test_token_blacklisted_after_logout(self, client, user_token):
        client.post("/api/v1/auth/logout", headers=auth_header(user_token))
        res = client.get("/api/v1/users/current", headers=auth_header(user_token))
        assert res.status_code == 401


class TestRefreshToken:
    def test_refresh_token(self, client, regular_user, db):
        # Login first to get a refresh token
        login_res = client.post(
            "/api/v1/auth/login",
            json={
                "login": "testuser",
                "password": "password",
            },
        )
        refresh = login_res.json()["data"]["refresh_token"]
        res = client.post("/api/v1/auth/refresh-token", json={"refresh_token": refresh})
        assert res.status_code == 200
        assert res.json()["data"]["access_token"]

    def test_refresh_invalid_token(self, client):
        res = client.post("/api/v1/auth/refresh-token", json={"refresh_token": "invalid"})
        assert res.status_code == 401


class TestCheckToken:
    def test_check_valid_token(self, client, user_token, regular_user):
        res = client.post("/api/v1/auth/check-token", json={"token": user_token})
        assert res.status_code == 200
        assert res.json()["data"]["user"]["username"] == "testuser"

    def test_check_invalid_token(self, client):
        res = client.post("/api/v1/auth/check-token", json={"token": "invalid"})
        assert res.status_code == 401


class TestChangePassword:
    def test_change_password(self, client, user_token):
        res = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "password",
                "new_password": "newpassword123",
            },
            headers=auth_header(user_token),
        )
        assert res.status_code == 200

    def test_change_password_wrong_current(self, client, user_token):
        res = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword123",
            },
            headers=auth_header(user_token),
        )
        assert res.status_code == 400

    def test_change_password_too_short(self, client, user_token):
        res = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "password",
                "new_password": "12345",
            },
            headers=auth_header(user_token),
        )
        assert res.status_code == 400
