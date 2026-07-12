from tests.conftest import auth_header


class TestCurrentUser:
    def test_get_current_user(self, client, user_token, regular_user):
        res = client.get("/api/v1/users/current",
                         headers=auth_header(user_token))
        assert res.status_code == 200
        assert res.json()["data"]["user"]["username"] == "testuser"

    def test_get_current_user_unauthenticated(self, client):
        res = client.get("/api/v1/users/current")
        assert res.status_code == 401

    def test_update_current_user(self, client, user_token):
        res = client.patch("/api/v1/users/current", json={
            "first_name": "Updated",
            "last_name": "Name",
        }, headers=auth_header(user_token))
        assert res.status_code == 200
        assert res.json()["data"]["user"]["first_name"] == "Updated"

    def test_update_current_user_phone(self, client, user_token):
        res = client.patch("/api/v1/users/current", json={
            "phone": "1234567890",
        }, headers=auth_header(user_token))
        assert res.status_code == 200
        assert res.json()["data"]["user"]["phone"] == "1234567890"

    def test_delete_current_user(self, client, user_token):
        res = client.delete("/api/v1/users/current",
                            headers=auth_header(user_token))
        assert res.status_code == 200
        assert res.json()["status"] == "success"


class TestUserByUsername:
    def test_get_by_username(self, client, regular_user, user_token):
        res = client.get("/api/v1/users/username/testuser")
        assert res.status_code == 200
        assert res.json()["data"]["user"]["email"] == "test@test.com"

    def test_get_by_username_not_found(self, client, user_role):
        res = client.get("/api/v1/users/username/nobody")
        assert res.status_code == 404


class TestUserPosts:
    def test_get_user_posts(self, client, user_token, regular_user):
        res = client.get(f"/api/v1/users/{regular_user.id}/posts",
                         headers=auth_header(user_token))
        assert res.status_code == 200

    def test_get_user_role(self, client, user_token, regular_user):
        res = client.get(
            f"/api/v1/users/{regular_user.id}/roles", headers=auth_header(user_token))
        assert res.status_code == 200
        assert res.json()["data"]["role"]["name"] == "user"


class TestAdminUserOps:
    def test_list_users(self, client, admin_token, regular_user):
        res = client.get("/api/v1/users", headers=auth_header(admin_token))
        assert res.status_code == 200
        assert isinstance(res.json()["data"]["users"], list)

    def test_list_users_as_regular_user(self, client, user_token):
        # Any authenticated user may list users (the frontend users page relies on it)
        res = client.get("/api/v1/users", headers=auth_header(user_token))
        assert res.status_code == 200

    def test_get_user_by_id(self, client, admin_token, regular_user):
        res = client.get(
            f"/api/v1/users/{regular_user.id}", headers=auth_header(admin_token))
        assert res.status_code == 200
        assert res.json()["data"]["user"]["username"] == "testuser"

    def test_get_user_not_found(self, client, admin_token):
        res = client.get("/api/v1/users/nonexistent-id",
                         headers=auth_header(admin_token))
        assert res.status_code == 404

    def test_admin_update_user(self, client, admin_token, regular_user):
        res = client.patch(f"/api/v1/users/{regular_user.id}", json={
            "first_name": "AdminUpdated",
        }, headers=auth_header(admin_token))
        assert res.status_code == 200
        assert res.json()["data"]["user"]["first_name"] == "AdminUpdated"

    def test_admin_delete_user(self, client, admin_token, regular_user):
        res = client.delete(
            f"/api/v1/users/{regular_user.id}", headers=auth_header(admin_token))
        assert res.status_code == 200
