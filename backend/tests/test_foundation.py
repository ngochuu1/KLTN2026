import os
import secrets
import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

import jwt
from pydantic import SecretStr, ValidationError

from app.core.config import Settings, get_settings
from app.core.security import (
    create_access_token, decode_access_token, generate_refresh_token,
    hash_password, hash_refresh_token, refresh_token_expires_at, verify_password,
)
from app.models.enums import AccountStatus, SystemRole
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, RegisterResponse
from app.schemas.user import ChangePasswordRequest, UserProfileResponse, UserUpdateRequest


class SecurityTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.environment = patch.dict(os.environ, {
            "JWT_SECRET_KEY": secrets.token_urlsafe(48),
            "ACCESS_TOKEN_EXPIRE_MINUTES": "15", "REFRESH_TOKEN_EXPIRE_DAYS": "7",
        })
        self.environment.start()
        get_settings.cache_clear()
        self.addCleanup(self.environment.stop)
        self.addCleanup(get_settings.cache_clear)

    async def test_argon2id_salted_hash_and_verification(self) -> None:
        password = " secret with spaces "
        first = await hash_password(password)
        second = await hash_password(password)
        self.assertTrue(first.startswith("$argon2id$"))
        self.assertNotEqual(first, second)
        self.assertTrue(await verify_password(password, first))
        self.assertFalse(await verify_password(password.strip(), first))
        self.assertFalse(await verify_password("wrong-password", first))
        self.assertFalse(await verify_password(password, "invalid-hash"))

    async def test_password_length_boundaries_without_complexity_rules(self) -> None:
        for length in (8, 128):
            password = "a" * length
            self.assertTrue(await verify_password(password, await hash_password(password)))
        for length in (7, 129):
            with self.assertRaises(ValueError):
                await hash_password("a" * length)

    def test_access_token_claims_and_lifetime(self) -> None:
        user_id, session_id = uuid4(), uuid4()
        claims = decode_access_token(create_access_token(user_id, session_id))
        self.assertEqual(claims.sub, user_id)
        self.assertEqual(claims.sid, session_id)
        self.assertEqual(claims.type, "access")
        self.assertEqual(claims.exp - claims.iat, 900)
        self.assertEqual(set(claims.model_dump()), {"sub", "sid", "type", "iat", "exp"})

    def test_jwt_rejects_bad_claims_signature_algorithm_and_expiry(self) -> None:
        now = int(datetime.now(UTC).timestamp())
        valid = {"sub": str(uuid4()), "sid": str(uuid4()), "type": "access", "iat": now, "exp": now + 900}
        key = get_settings().jwt_secret_key.get_secret_value()
        cases = [
            {**valid, "type": "refresh"}, {**valid, "sub": "not-uuid"},
            {**valid, "sid": "not-uuid"}, {**valid, "iat": now - 100, "exp": now - 1},
            {**valid, "iat": now + 100}, {**valid, "iat": str(now)},
            {**valid, "exp": True}, {**valid, "password_hash": "forbidden"},
        ]
        cases.extend({k: v for k, v in valid.items() if k != required} for required in valid)
        for payload in cases:
            with self.subTest(claims=list(payload)), self.assertRaises(jwt.InvalidTokenError):
                decode_access_token(jwt.encode(payload, key, algorithm="HS256"))
        for token in (
            jwt.encode(valid, secrets.token_urlsafe(48), algorithm="HS256"),
            jwt.encode(valid, key, algorithm="HS384"), "not-a-token",
        ):
            with self.assertRaises(jwt.InvalidTokenError):
                decode_access_token(token)

    def test_refresh_token_randomness_hash_and_lifetime(self) -> None:
        first, second = generate_refresh_token(), generate_refresh_token()
        self.assertNotEqual(first, second)
        self.assertGreaterEqual(len(first), 43)
        self.assertEqual(len(hash_refresh_token(first)), 64)
        self.assertEqual(hash_refresh_token(first), hash_refresh_token(first))
        self.assertNotEqual(hash_refresh_token(first), hash_refresh_token(second))
        self.assertEqual(hash_refresh_token("abc"), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
        before = datetime.now(UTC) + timedelta(days=7)
        expires = refresh_token_expires_at()
        self.assertGreaterEqual(expires, before)
        self.assertLess(expires - before, timedelta(seconds=2))


class SchemaTests(unittest.TestCase):
    def registration(self, **changes: object) -> dict[str, object]:
        return {"full_name": " Nguyen Van A ", "email": " User@Example.COM ",
                "password": "aaaaaaaa", "confirm_password": "aaaaaaaa", **changes}

    def test_registration_normalizes_email_name_and_masks_password(self) -> None:
        request = RegisterRequest.model_validate(self.registration())
        self.assertEqual(request.email, "user@example.com")
        self.assertEqual(request.full_name, "Nguyen Van A")
        self.assertIsInstance(request.password, SecretStr)
        self.assertNotIn("aaaaaaaa", repr(request))
        self.assertEqual(LoginRequest(email=" User@Example.COM ", password="aaaaaaaa").email, request.email)

    def test_registration_rejects_invalid_missing_and_privileged_fields(self) -> None:
        for changes in ({"email": "invalid"}, {"full_name": "   "}, {"full_name": "a" * 101},
                        {"password": "short"}, {"password": "a" * 129},
                        {"confirm_password": "different"}, {"role": "ADMIN"},
                        {"system_role": "ADMIN"}, {"status": "LOCKED"}):
            with self.subTest(fields=list(changes)), self.assertRaises(ValidationError):
                RegisterRequest.model_validate(self.registration(**changes))
        for required in self.registration():
            payload = self.registration()
            del payload[required]
            with self.subTest(missing=required), self.assertRaises(ValidationError):
                RegisterRequest.model_validate(payload)

    def test_update_only_allows_full_name(self) -> None:
        self.assertEqual(UserUpdateRequest(full_name=" Valid name ").full_name, "Valid name")
        for payload in ({}, {"full_name": " "}, {"full_name": "a" * 101},
                        {"full_name": "Name", "email": "other@example.com"},
                        {"full_name": "Name", "system_role": "ADMIN"}):
            with self.assertRaises(ValidationError):
                UserUpdateRequest.model_validate(payload)

    def test_change_password_confirmation(self) -> None:
        request = ChangePasswordRequest(current_password="old-password", new_password="new-password", confirm_new_password="new-password")
        self.assertNotIn("old-password", repr(request))
        with self.assertRaises(ValidationError) as error:
            ChangePasswordRequest(current_password="old-password", new_password="new-password", confirm_new_password="wrong-password")
        self.assertEqual(error.exception.errors()[0]["type"], "PASSWORD_CONFIRMATION_MISMATCH")
        self.assertEqual(error.exception.errors()[0]["loc"], ("confirm_new_password",))

    def test_public_schemas_exclude_secrets(self) -> None:
        now = datetime.now(UTC)
        user = User(id=uuid4(), full_name="Name", email=" User@Example.COM ",
                    password_hash="private-hash", status=AccountStatus.ACTIVE,
                    system_role=SystemRole.USER, created_at=now, updated_at=now)
        self.assertEqual(user.email, "user@example.com")
        for schema in (UserProfileResponse, RegisterResponse):
            output = schema.model_validate(user).model_dump(mode="json")
            self.assertNotIn("password_hash", output)
            self.assertNotIn("password", output)
            self.assertNotIn("refresh_token", output)

    def test_settings_require_secret_and_secure_production_cookie(self) -> None:
        settings = get_settings().model_dump()
        settings["jwt_secret_key"] = SecretStr(secrets.token_urlsafe(48))
        with self.assertRaises(ValidationError):
            Settings(**{**settings, "jwt_secret_key": "short"})
        with self.assertRaises(ValidationError):
            Settings(**{**settings, "app_env": "production", "cookie_secure": False})
        self.assertTrue(Settings(**{**settings, "app_env": "production", "cookie_secure": True}).cookie_secure)
