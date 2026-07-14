from tests.conftest import auth_header


class TestFollows:
    def test_follow_user(self, client, user_token, second_user):
        res = client.post(
            f"/api/v1/follows/{second_user.id}/follow", headers=auth_header(user_token)
        )
        assert res.status_code == 201

    def test_follow_self(self, client, user_token, regular_user):
        res = client.post(
            f"/api/v1/follows/{regular_user.id}/follow", headers=auth_header(user_token)
        )
        assert res.status_code == 400

    def test_follow_nonexistent_user(self, client, user_token):
        res = client.post("/api/v1/follows/nonexistent/follow", headers=auth_header(user_token))
        assert res.status_code == 404

    def test_follow_already_following(self, client, user_token, second_user):
        client.post(f"/api/v1/follows/{second_user.id}/follow", headers=auth_header(user_token))
        res = client.post(
            f"/api/v1/follows/{second_user.id}/follow", headers=auth_header(user_token)
        )
        assert res.status_code == 400

    def test_unfollow_user(self, client, user_token, second_user):
        client.post(f"/api/v1/follows/{second_user.id}/follow", headers=auth_header(user_token))
        res = client.delete(
            f"/api/v1/follows/{second_user.id}/follow", headers=auth_header(user_token)
        )
        assert res.status_code == 200

    def test_unfollow_not_following(self, client, user_token, second_user):
        res = client.delete(
            f"/api/v1/follows/{second_user.id}/follow", headers=auth_header(user_token)
        )
        assert res.status_code == 404

    def test_get_followers(self, client, user_token, second_user_token, regular_user, second_user):
        client.post(f"/api/v1/follows/{second_user.id}/follow", headers=auth_header(user_token))
        res = client.get(f"/api/v1/follows/{second_user.id}/followers")
        assert res.status_code == 200
        assert len(res.json()["data"]["followers"]) == 1
        assert res.json()["data"]["followers"][0]["username"] == "testuser"

    def test_get_following(self, client, user_token, second_user, regular_user):
        client.post(f"/api/v1/follows/{second_user.id}/follow", headers=auth_header(user_token))
        res = client.get(f"/api/v1/follows/{regular_user.id}/following")
        assert res.status_code == 200
        assert len(res.json()["data"]["following"]) == 1

    def test_is_following_true(self, client, user_token, second_user):
        client.post(f"/api/v1/follows/{second_user.id}/follow", headers=auth_header(user_token))
        res = client.get(
            f"/api/v1/follows/{second_user.id}/is-following", headers=auth_header(user_token)
        )
        assert res.status_code == 200
        assert res.json()["data"]["isFollowing"] is True

    def test_is_following_false(self, client, user_token, second_user):
        res = client.get(
            f"/api/v1/follows/{second_user.id}/is-following", headers=auth_header(user_token)
        )
        assert res.status_code == 200
        assert res.json()["data"]["isFollowing"] is False
