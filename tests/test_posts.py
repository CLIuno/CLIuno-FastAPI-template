from tests.conftest import auth_header


class TestPosts:
    def test_create_post(self, client, user_token):
        res = client.post(
            "/api/v1/posts",
            json={
                "title": "Test Post",
                "content": "Test content",
            },
            headers=auth_header(user_token),
        )
        assert res.status_code == 201
        assert res.json()["data"]["post"]["title"] == "Test Post"

    def test_create_post_no_title(self, client, user_token):
        res = client.post(
            "/api/v1/posts",
            json={
                "content": "No title",
            },
            headers=auth_header(user_token),
        )
        assert res.status_code == 400

    def test_list_posts(self, client, user_token):
        client.post("/api/v1/posts", json={"title": "Post 1"}, headers=auth_header(user_token))
        client.post("/api/v1/posts", json={"title": "Post 2"}, headers=auth_header(user_token))
        res = client.get("/api/v1/posts")
        assert res.status_code == 200
        assert len(res.json()["data"]["posts"]) == 2

    def test_list_posts_includes_user_and_comments(self, client, user_token):
        client.post("/api/v1/posts", json={"title": "Post"}, headers=auth_header(user_token))
        res = client.get("/api/v1/posts")
        post = res.json()["data"]["posts"][0]
        assert "user" in post
        assert "comments" in post

    def test_current_user_posts(self, client, user_token):
        client.post("/api/v1/posts", json={"title": "My Post"}, headers=auth_header(user_token))
        res = client.get("/api/v1/posts/current-user", headers=auth_header(user_token))
        assert res.status_code == 200
        assert len(res.json()["data"]["posts"]) == 1

    def test_get_post(self, client, user_token):
        create_res = client.post(
            "/api/v1/posts", json={"title": "Get Me"}, headers=auth_header(user_token)
        )
        post_id = create_res.json()["data"]["post"]["id"]
        res = client.get(f"/api/v1/posts/{post_id}")
        assert res.status_code == 200
        assert res.json()["data"]["post"]["title"] == "Get Me"

    def test_get_post_not_found(self, client):
        res = client.get("/api/v1/posts/nonexistent")
        assert res.status_code == 404

    def test_update_post(self, client, user_token):
        create_res = client.post(
            "/api/v1/posts", json={"title": "Old"}, headers=auth_header(user_token)
        )
        post_id = create_res.json()["data"]["post"]["id"]
        res = client.patch(
            f"/api/v1/posts/{post_id}", json={"title": "New"}, headers=auth_header(user_token)
        )
        assert res.status_code == 200
        assert res.json()["data"]["post"]["title"] == "New"

    def test_update_post_forbidden(self, client, user_token, second_user_token):
        create_res = client.post(
            "/api/v1/posts", json={"title": "Mine"}, headers=auth_header(user_token)
        )
        post_id = create_res.json()["data"]["post"]["id"]
        res = client.patch(
            f"/api/v1/posts/{post_id}",
            json={"title": "Hacked"},
            headers=auth_header(second_user_token),
        )
        assert res.status_code == 403

    def test_delete_post(self, client, user_token):
        create_res = client.post(
            "/api/v1/posts", json={"title": "Delete Me"}, headers=auth_header(user_token)
        )
        post_id = create_res.json()["data"]["post"]["id"]
        res = client.delete(f"/api/v1/posts/{post_id}", headers=auth_header(user_token))
        assert res.status_code == 200

    def test_delete_post_forbidden(self, client, user_token, second_user_token):
        create_res = client.post(
            "/api/v1/posts", json={"title": "Mine"}, headers=auth_header(user_token)
        )
        post_id = create_res.json()["data"]["post"]["id"]
        res = client.delete(f"/api/v1/posts/{post_id}", headers=auth_header(second_user_token))
        assert res.status_code == 403

    def test_get_post_author(self, client, user_token, regular_user):
        create_res = client.post(
            "/api/v1/posts", json={"title": "Author"}, headers=auth_header(user_token)
        )
        post_id = create_res.json()["data"]["post"]["id"]
        res = client.get(f"/api/v1/posts/{post_id}/user")
        assert res.status_code == 200
        assert res.json()["data"]["user"]["username"] == "testuser"

    def test_admin_can_update_any_post(self, client, user_token, admin_token):
        create_res = client.post(
            "/api/v1/posts", json={"title": "User Post"}, headers=auth_header(user_token)
        )
        post_id = create_res.json()["data"]["post"]["id"]
        res = client.patch(
            f"/api/v1/posts/{post_id}",
            json={"title": "Admin Edit"},
            headers=auth_header(admin_token),
        )
        assert res.status_code == 200
