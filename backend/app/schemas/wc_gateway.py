"""Schemas for WooCommerce payment gateways and COD configuration.

Cash on Delivery (COD) is the primary gateway feature. Other gateways
are exposed read-only for the current phase.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class WCGateway(BaseModel):
    """A payment gateway as returned by WooCommerce.

    `settings` is a dict of setting-id -> { value, label, type, ... }.
    We only expose the safe subset the UI needs.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    title: str = ""
    description: str = ""
    order: int = 0
    enabled: bool = False
    method_title: str = ""
    method_description: str = ""
    method_supports: list[str] = Field(default_factory=list)

    # COD-specific fields. Present only if WooCommerce returns them.
    instructions: str = ""
    enable_for_virtual: bool = False
    enable_for_methods: list[str] = Field(default_factory=list)


class WCGatewayListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[WCGateway] = Field(default_factory=list)


class CODSettings(BaseModel):
    """Editable Cash on Delivery configuration.

    Fields that map directly to WooCommerce's COD gateway API.
    All fields are optional — only provided fields are sent.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool | None = Field(
        default=None,
        description="Whether COD is enabled on checkout.",
    )
    title: str | None = Field(
        default=None,
        max_length=200,
        description="Gateway title shown to the customer.",
        examples=["Cash on delivery"],
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Description shown at checkout.",
        examples=["Pay with cash upon delivery."],
    )
    instructions: str | None = Field(
        default=None,
        max_length=2000,
        description="Instructions shown on the thank-you page and email.",
        examples=["Please have exact change ready."],
    )
    enable_for_virtual: bool | None = Field(
        default=None,
        description="If true, COD is available for virtual products too.",
    )


class CODStatus(BaseModel):
    """Summary of COD availability for the store."""

    model_config = ConfigDict(extra="forbid")

    available: bool = Field(
        ...,
        description="True if the COD gateway exists in WooCommerce.",
    )
    enabled: bool = Field(
        ...,
        description="True if the COD gateway is enabled.",
    )
    title: str = ""
    description: str = ""
    instructions: str = ""
    enable_for_virtual: bool = False

    shipping_zones_available: bool = Field(
        default=False,
        description="True if at least one shipping zone exists.",
    )
    warnings: list[str] = Field(default_factory=list)