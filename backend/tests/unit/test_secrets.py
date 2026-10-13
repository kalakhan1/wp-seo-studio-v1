"""Unit tests for app.security.secrets.

Uses a monkeypatched in-memory backend so tests do not touch the real OS
keyring.
"""

from __future__ import annotations

import pytest

from app.security import secrets as secret_store


class _MemoryKeyring:
    def __init__(self) -> None:
        self.store: dict[tuple[str, str], str] = {}

    def set(self, service: str, key: str, value: str) -> None:
        self.store[(service, key)] = value

    def get(self, service: str, key: str) -> str | None:
        return self.store.get((service, key))

    def delete(self, service: str, key: str) -> None:
        self.store.pop((service, key), None)


@pytest.fixture
def memory_keyring(monkeypatch: pytest.MonkeyPatch) -> _MemoryKeyring:
    mem = _MemoryKeyring()
    monkeypatch.setattr(secret_store, "set_password", mem.set)
    monkeypatch.setattr(secret_store, "get_password", mem.get)

    from keyring import delete_password  # noqa: F401  (ensure import path)

    def _delete(service: str, key: str) -> None:
        mem.delete(service, key)

    monkeypatch.setattr("app.security.secrets.delete_secret",
                        lambda label, field: _delete(
                            secret_store._SERVICE_NAME,
                            secret_store._key(label, field),  # noqa: SLF001
                        ))
    return mem


def test_set_and_get_roundtrip(memory_keyring: _MemoryKeyring) -> None:
    secret_store.set_secret("prod", secret_store.FIELD_WP_APP_PASSWORD, "abcd efgh")
    assert (
        secret_store.get_secret("prod", secret_store.FIELD_WP_APP_PASSWORD)
        == "abcd efgh"
    )


def test_get_missing_returns_none() -> None:
    assert secret_store.get_secret("does-not-exist", "wp_app_password") is None


def test_empty_label_returns_none() -> None:
    assert secret_store.get_secret("", "wp_app_password") is None


def test_set_empty_value_deletes(memory_keyring: _MemoryKeyring) -> None:
    secret_store.set_secret("prod", secret_store.FIELD_WP_APP_PASSWORD, "value")
    secret_store.set_secret("prod", secret_store.FIELD_WP_APP_PASSWORD, "")
    # After setting empty, get should return None
    assert secret_store.get_secret("prod", secret_store.FIELD_WP_APP_PASSWORD) is None


def test_set_without_label_raises() -> None:
    with pytest.raises(ValueError):
        secret_store.set_secret("", secret_store.FIELD_WP_APP_PASSWORD, "value")