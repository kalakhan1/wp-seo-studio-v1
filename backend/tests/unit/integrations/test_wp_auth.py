"""Unit tests for app.integrations.wordpress.auth."""

from __future__ import annotations

import base64

import pytest

from app.config.constants import AuthMethod
from app.core.exceptions import AuthError
from app.integrations.wordpress.auth import (
    build_auth_headers,
    build_basic_auth_header,
)


class TestBuildBasicAuthHeader:
    def test_produces_valid_base64(self) -> None:
        header = build_basic_auth_header("admin", "abcd efgh ijkl mnop")
        assert header.startswith("Basic ")
        encoded = header[len("Basic ") :]
        decoded = base64.b64decode(encoded).decode("utf-8")
        assert decoded == "admin:abcd efgh ijkl mnop"

    def test_preserves_spaces_in_application_password(self) -> None:
        # WordPress application passwords contain literal spaces.
        header = build_basic_auth_header("user", "aaaa bbbb cccc dddd")
        decoded = base64.b64decode(header[len("Basic ") :]).decode("utf-8")
        assert decoded == "user:aaaa bbbb cccc dddd"

    def test_supports_special_characters(self) -> None:
        header = build_basic_auth_header("user@example.com", "p@ssw0rd!~$")
        decoded = base64.b64decode(header[len("Basic ") :]).decode("utf-8")
        assert decoded == "user@example.com:p@ssw0rd!~$"

    def test_empty_username_raises(self) -> None:
        with pytest.raises(AuthError):
            build_basic_auth_header("", "password")

    def test_empty_password_raises(self) -> None:
        with pytest.raises(AuthError):
            build_basic_auth_header("admin", "")


class TestBuildAuthHeaders:
    def test_application_password_uses_basic(self) -> None:
        headers = build_auth_headers(
            AuthMethod.APPLICATION_PASSWORD.value,
            "admin",
            "app-pass",
        )
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")

    def test_basic_method_uses_basic(self) -> None:
        headers = build_auth_headers(AuthMethod.BASIC.value, "admin", "pass")
        assert headers["Authorization"].startswith("Basic ")

    def test_jwt_with_token(self) -> None:
        headers = build_auth_headers(
            AuthMethod.JWT.value,
            "admin",
            "ignored",
            jwt_token="jwt.token.value",
        )
        assert headers["Authorization"] == "Bearer jwt.token.value"

    def test_jwt_without_token_raises(self) -> None:
        with pytest.raises(AuthError):
            build_auth_headers(AuthMethod.JWT.value, "admin", "ignored")

    def test_unknown_method_raises(self) -> None:
        with pytest.raises(AuthError):
            build_auth_headers("magic", "admin", "pass")

    def test_none_method_raises(self) -> None:
        with pytest.raises(AuthError):
            build_auth_headers(AuthMethod.NONE.value, "admin", "pass")