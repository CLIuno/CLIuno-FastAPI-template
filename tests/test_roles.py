from tests.conftest import auth_header


class TestRoles:
    def test_list_roles(self, client, admin_token, admin_role, user_role):
        res = client.get("/api/v1/roles", headers=auth_header(admin_token))
        assert res.status_code == 200
        assert len(res.json()["data"]) == 2

    def test_list_roles_forbidden(self, client, user_token):
        res = client.get("/api/v1/roles", headers=auth_header(user_token))
        assert res.status_code == 403

    def test_create_role(self, client, admin_token):
        res = client.post(
            "/api/v1/roles", json={"name": "moderator"}, headers=auth_header(admin_token)
        )
        assert res.status_code == 201
        assert res.json()["data"]["name"] == "moderator"

    def test_create_role_duplicate(self, client, admin_token, admin_role):
        res = client.post("/api/v1/roles", json={"name": "admin"}, headers=auth_header(admin_token))
        assert res.status_code == 400

    def test_get_role(self, client, admin_token, admin_role):
        res = client.get(f"/api/v1/roles/{admin_role.id}", headers=auth_header(admin_token))
        assert res.status_code == 200
        assert res.json()["data"]["name"] == "admin"

    def test_get_role_not_found(self, client, admin_token):
        res = client.get("/api/v1/roles/nonexistent", headers=auth_header(admin_token))
        assert res.status_code == 404

    def test_update_role(self, client, admin_token, user_role):
        res = client.patch(
            f"/api/v1/roles/{user_role.id}",
            json={"name": "member"},
            headers=auth_header(admin_token),
        )
        assert res.status_code == 200
        assert res.json()["data"]["name"] == "member"

    def test_delete_role(self, client, admin_token):
        # Create a role to delete
        create_res = client.post(
            "/api/v1/roles", json={"name": "temp"}, headers=auth_header(admin_token)
        )
        role_id = create_res.json()["data"]["id"]
        res = client.delete(f"/api/v1/roles/{role_id}", headers=auth_header(admin_token))
        assert res.status_code == 200

    def test_get_role_users(self, client, admin_token, admin_role, admin_user):
        res = client.get(f"/api/v1/roles/{admin_role.id}/users", headers=auth_header(admin_token))
        assert res.status_code == 200
        assert len(res.json()["data"]) == 1
