"""Schemas for WordPress/WooCommerce connection management."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.integrations.wordpress.types import SiteInfo, WPUser


# --- Test (no save) ---------------------------------------------------------


class ConnectionTestRequest(BaseModel):
    """Credentials for a dry-run connection test. Nothing is saved."""

    model_config = ConfigDict(extra="forbid")

    base_url: str = Field(
        ...,
        description="WordPress base URL without trailing slash.",
        examples=["https://example.com"],
    )
    username: str = Field(
        default="",
        description="WordPress username.",
        examples=["admin"],
    )
    wp_app_password: str = Field(
        default="",
        description="WordPress Application Password. Never logged or stored.",
        examples=["abcd efgh ijkl mnop"],
    )
    auth_method: str = Field(
        default="application_password",
        description="Authentication method.",
        examples=["application_password"],
    )
    require_https: bool = Field(
        default=True,
        description="Reject HTTP URLs.",
    )
    wc_consumer_key: str = Field(
        default="",
        description="Optional WooCommerce consumer key.",
        examples=["ck_..."],
    )
    wc_consumer_secret: str = Field(
        default="",
        description="Optional WooCommerce consumer secret.",
        examples=["cs_..."],
    )


class ConnectionTestResponse(BaseModel):
    """Result of a dry-run connection test."""

    model_config = ConfigDict(extra="forbid")

    ok: bool = Field(..., description="True if WordPress authentication succeeded.")
    site_info: SiteInfo | None = None
    current_user: WPUser | None = None
    wc_available: bool = Field(
        default=False,
        description="True if WooCommerce REST responded to a probe.",
    )
    message: str = ""
    warnings: list[str] = Field(default_factory=list)


# --- Save / list / get ------------------------------------------------------


class ConnectionSaveRequest(BaseModel):
    """Save a connection profile. Secrets go to the OS keyring."""

    model_config = ConfigDict(extra="forbid")

    label: str = Field(
        ...,
        description="Human-readable, unique label.",
        examples=["Production Store"],
        min_length=1,
        max_length=120,
    )
    base_url: str = Field(
        ...,
        description="WordPress base URL without trailing slash.",
        examples=["https://example.com"],
    )
    username: str = Field(
        ...,
        description="WordPress username.",
        examples=["admin"],
    )
    wp_app_password: str = Field(
        ...,
        description="WordPress Application Password. Stored only in OS keyring.",
    )
    auth_method: str = Field(
        default="application_password",
        description="Authentication method.",
    )
    require_https: bool = Field(default=True)
    wc_consumer_key: str = Field(default="")
    wc_consumer_secret: str = Field(default="")
    notes: str | None = Field(default=None)


class ConnectionResponse(BaseModel):
    """Non-secret view of a stored connection."""

    model_config = ConfigDict(extra="forbid")

    id: int
    label: str
    base_url: str
    username: str
    auth_method: str
    require_https: bool
    notes: str | None = None
    has_wc_credentials: bool = False
    last_verified_at: str | None = None
    last_verified_ok: bool = False
    created_at: str
    updated_at: str


class ConnectionListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    connections: list[ConnectionResponse] = Field(default_factory=list)