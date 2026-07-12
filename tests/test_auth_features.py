import pyotp

from tests.conftest import auth_header


class TestPasswordReset:
    def test_forgot_password_known_email(self, client, regular_user, db):
        res = client.post("/api/v1/auth/forgot-password",
                          json={"email": "test@test.com"})
        assert res.status_code == 200
        db.refresh(regular_user)
        assert regular_user.reset_token

    def test_forgot_password_unknown_email_is_silent(self, client):
        res = client.post("/api/v1/auth/forgot-password",
                          json={"email": "nobody@test.com"})
        assert res.status_code == 200

    def test_reset_password_with_valid_token(self, client, regular_user, db):
        client.post("/api/v1/auth/forgot-password",
                    json={"email": "test@test.com"})
        db.refresh(regular_user)
        res = client.post(
            "/api/v1/auth/reset-password",
            json={"password": "NewPass123", "token": regular_user.reset_token},
        )
        assert res.status_code == 200

        login = client.post(
            "/api/v1/auth/login",
            json={"login": "testuser", "password": "NewPass123"},
        )
        assert login.status_code == 200

    def test_reset_password_invalid_token(self, client):
        res = client.post(
            "/api/v1/auth/reset-password",
            json={"password": "NewPass123", "token": "bogus"},
        )
        assert res.status_code == 400


class TestEmailVerification:
    def test_send_and_verify_email(self, client, user_token, regular_user, db):
        res = client.post("/api/v1/auth/send-verify-email",
                          headers=auth_header(user_token))
        assert res.status_code == 200
        db.refresh(regular_user)
        assert regular_user.verify_token

        res = client.post("/api/v1/auth/verify-email",
                          json={"token": regular_user.verify_token})
        assert res.status_code == 200
        db.refresh(regular_user)
        assert regular_user.is_verified
        assert regular_user.verify_token is None

    def test_verify_email_invalid_token(self, client):
        res = client.post("/api/v1/auth/verify-email", json={"token": "bogus"})
        assert res.status_code == 400


class TestOtp:
    def test_full_otp_lifecycle(self, client, user_token, regular_user, db):
        res = client.post("/api/v1/auth/otp/generate",
                          headers=auth_header(user_token))
        assert res.status_code == 200
        secret = res.json()["data"]["secret"]
        assert "otpauth" in res.json()["data"]["otpauth_url"]

        code = pyotp.TOTP(secret).now()
        res = client.post("/api/v1/auth/otp/verify",
                          json={"otp": code}, headers=auth_header(user_token))
        assert res.status_code == 200
        db.refresh(regular_user)
        assert regular_user.is_otp_enabled

        res = client.post("/api/v1/auth/otp/validate",
                          json={"otp": pyotp.TOTP(secret).now()},
                          headers=auth_header(user_token))
        assert res.status_code == 200

        res = client.post("/api/v1/auth/otp/disable",
                          headers=auth_header(user_token))
        assert res.status_code == 200
        db.refresh(regular_user)
        assert not regular_user.is_otp_enabled
        assert regular_user.otp_secret is None

    def test_verify_with_wrong_code(self, client, user_token):
        client.post("/api/v1/auth/otp/generate",
                    headers=auth_header(user_token))
        res = client.post("/api/v1/auth/otp/verify",
                          json={"otp": "000000"}, headers=auth_header(user_token))
        assert res.status_code == 401

    def test_validate_without_setup(self, client, user_token):
        res = client.post("/api/v1/auth/otp/validate",
                          json={"otp": "123456"}, headers=auth_header(user_token))
        assert res.status_code == 400
