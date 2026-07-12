from tests.conftest import auth_header


class TestComments:
    def _create_post(self, client, token):
        res = client.post(
            "/api/v1/posts", json={"title": "Post"}, headers=auth_header(token))
        return res.json()["data"]["id"]

    def test_list_comments(self, client, user_token):
        post_id = self._create_post(client, user_token)
        client.post(f"/api/v1/posts/{post_id}/comments",
                    json={"content": "Comment 1"}, headers=auth_header(user_token))
        res = client.get(f"/api/v1/posts/{post_id}/comments")
        assert res.status_code == 200
        assert len(res.json()["data"]) == 1

    def test_list_comments_post_not_found(self, client, user_role):
        res = client.get("/api/v1/posts/nonexistent/comments")
        assert res.status_code == 404

    def test_create_comment(self, client, user_token):
        post_id = self._create_post(client, user_token)
        res = client.post(f"/api/v1/posts/{post_id}/comments", json={
                          "content": "Nice post!"}, headers=auth_header(user_token))
        assert res.status_code == 201
        assert res.json()["data"]["content"] == "Nice post!"

    def test_create_comment_no_content(self, client, user_token):
        post_id = self._create_post(client, user_token)
        res = client.post(
            f"/api/v1/posts/{post_id}/comments", json={}, headers=auth_header(user_token))
        assert res.status_code == 400

    def test_update_comment(self, client, user_token):
        post_id = self._create_post(client, user_token)
        create_res = client.post(f"/api/v1/posts/{post_id}/comments", json={
                                 "content": "Old"}, headers=auth_header(user_token))
        comment_id = create_res.json()["data"]["id"]
        res = client.patch(f"/api/v1/posts/{post_id}/comments/{comment_id}", json={
                           "content": "Updated"}, headers=auth_header(user_token))
        assert res.status_code == 200
        assert res.json()["data"]["content"] == "Updated"

    def test_update_comment_forbidden(self, client, user_token, second_user_token):
        post_id = self._create_post(client, user_token)
        create_res = client.post(f"/api/v1/posts/{post_id}/comments", json={
                                 "content": "Mine"}, headers=auth_header(user_token))
        comment_id = create_res.json()["data"]["id"]
        res = client.patch(f"/api/v1/posts/{post_id}/comments/{comment_id}", json={
                           "content": "Hacked"}, headers=auth_header(second_user_token))
        assert res.status_code == 403

    def test_delete_comment(self, client, user_token):
        post_id = self._create_post(client, user_token)
        create_res = client.post(f"/api/v1/posts/{post_id}/comments", json={
                                 "content": "Delete me"}, headers=auth_header(user_token))
        comment_id = create_res.json()["data"]["id"]
        res = client.delete(
            f"/api/v1/posts/{post_id}/comments/{comment_id}", headers=auth_header(user_token))
        assert res.status_code == 200

    def test_delete_comment_forbidden(self, client, user_token, second_user_token):
        post_id = self._create_post(client, user_token)
        create_res = client.post(f"/api/v1/posts/{post_id}/comments", json={
                                 "content": "Mine"}, headers=auth_header(user_token))
        comment_id = create_res.json()["data"]["id"]
        res = client.delete(
            f"/api/v1/posts/{post_id}/comments/{comment_id}", headers=auth_header(second_user_token))
        assert res.status_code == 403
