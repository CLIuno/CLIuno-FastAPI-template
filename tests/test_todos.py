from tests.conftest import auth_header


class TestTodos:
    def test_create_todo(self, client, user_token):
        res = client.post(
            "/api/v1/todos",
            json={
                "title": "Test Todo",
                "description": "Test desc",
            },
            headers=auth_header(user_token),
        )
        assert res.status_code == 201
        assert res.json()["data"]["todo"]["title"] == "Test Todo"
        assert res.json()["data"]["todo"]["completed"] is False

    def test_create_todo_no_title(self, client, user_token):
        res = client.post(
            "/api/v1/todos",
            json={
                "description": "No title",
            },
            headers=auth_header(user_token),
        )
        assert res.status_code == 400

    def test_list_todos(self, client, user_token):
        client.post("/api/v1/todos", json={"title": "Todo 1"}, headers=auth_header(user_token))
        client.post("/api/v1/todos", json={"title": "Todo 2"}, headers=auth_header(user_token))
        res = client.get("/api/v1/todos", headers=auth_header(user_token))
        assert res.status_code == 200
        assert len(res.json()["data"]["todos"]) == 2

    def test_current_user_todos(self, client, user_token, second_user_token):
        client.post("/api/v1/todos", json={"title": "My Todo"}, headers=auth_header(user_token))
        client.post(
            "/api/v1/todos", json={"title": "Their Todo"}, headers=auth_header(second_user_token)
        )
        res = client.get("/api/v1/todos/current-user", headers=auth_header(user_token))
        assert res.status_code == 200
        assert len(res.json()["data"]["todos"]) == 1

    def test_get_todo(self, client, user_token):
        create_res = client.post(
            "/api/v1/todos", json={"title": "Get Me"}, headers=auth_header(user_token)
        )
        todo_id = create_res.json()["data"]["todo"]["id"]
        res = client.get(f"/api/v1/todos/{todo_id}", headers=auth_header(user_token))
        assert res.status_code == 200
        assert res.json()["data"]["todo"]["title"] == "Get Me"

    def test_get_todo_not_found(self, client, user_token):
        res = client.get("/api/v1/todos/nonexistent", headers=auth_header(user_token))
        assert res.status_code == 404

    def test_update_todo(self, client, user_token):
        create_res = client.post(
            "/api/v1/todos", json={"title": "Old"}, headers=auth_header(user_token)
        )
        todo_id = create_res.json()["data"]["todo"]["id"]
        res = client.patch(
            f"/api/v1/todos/{todo_id}", json={"title": "New"}, headers=auth_header(user_token)
        )
        assert res.status_code == 200
        assert res.json()["data"]["todo"]["title"] == "New"

    def test_update_todo_forbidden(self, client, user_token, second_user_token):
        create_res = client.post(
            "/api/v1/todos", json={"title": "Mine"}, headers=auth_header(user_token)
        )
        todo_id = create_res.json()["data"]["todo"]["id"]
        res = client.patch(
            f"/api/v1/todos/{todo_id}",
            json={"title": "Hacked"},
            headers=auth_header(second_user_token),
        )
        assert res.status_code == 403

    def test_delete_todo(self, client, user_token):
        create_res = client.post(
            "/api/v1/todos", json={"title": "Delete Me"}, headers=auth_header(user_token)
        )
        todo_id = create_res.json()["data"]["todo"]["id"]
        res = client.delete(f"/api/v1/todos/{todo_id}", headers=auth_header(user_token))
        assert res.status_code == 200

    def test_delete_todo_forbidden(self, client, user_token, second_user_token):
        create_res = client.post(
            "/api/v1/todos", json={"title": "Mine"}, headers=auth_header(user_token)
        )
        todo_id = create_res.json()["data"]["todo"]["id"]
        res = client.delete(f"/api/v1/todos/{todo_id}", headers=auth_header(second_user_token))
        assert res.status_code == 403

    def test_toggle_todo(self, client, user_token):
        create_res = client.post(
            "/api/v1/todos", json={"title": "Toggle"}, headers=auth_header(user_token)
        )
        todo_id = create_res.json()["data"]["todo"]["id"]
        res = client.patch(f"/api/v1/todos/{todo_id}/toggle", headers=auth_header(user_token))
        assert res.status_code == 200
        assert res.json()["data"]["todo"]["completed"] is True
        # Toggle back
        res = client.patch(f"/api/v1/todos/{todo_id}/toggle", headers=auth_header(user_token))
        assert res.json()["data"]["todo"]["completed"] is False

    def test_toggle_todo_forbidden(self, client, user_token, second_user_token):
        create_res = client.post(
            "/api/v1/todos", json={"title": "Mine"}, headers=auth_header(user_token)
        )
        todo_id = create_res.json()["data"]["todo"]["id"]
        res = client.patch(
            f"/api/v1/todos/{todo_id}/toggle", headers=auth_header(second_user_token)
        )
        assert res.status_code == 403
