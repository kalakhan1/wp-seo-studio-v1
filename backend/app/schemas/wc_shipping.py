"""Schemas for WooCommerce shipping zones and methods."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


ZoneType = Literal["continent", "country", "state", "postcode"]


class ZoneLocation(BaseModel):
    """A single zone location entry.

    `code` format depends on `type`:
      - continent:  e.g. "EU", "NA"
      - country:    e.g. "PK", "US"
      - state:      e.g. "PK:SD", "US:CA"
      - postcode:   e.g. "74200", "74*"
    """

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1, max_length=50)
    type: ZoneType = Field(
        ...,
        description="Location type.",
        examples=["country"],
    )


class ZoneMethodSettings(BaseModel):
    """Free-form settings for a shipping method.

    Shape varies by method_id (flat_rate, free_shipping, local_pickup).
    Common keys:
      - cost (flat_rate)
      - min_amount (free_shipping)
      - requires (free_shipping)
    """

    model_config = ConfigDict(extra="allow")

    cost: str | None = None
    min_amount: str | None = None
    requires: str | None = None


class WCShippingZone(BaseModel):
    """A shipping zone returned by WooCommerce."""

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str = ""
    order: int = 0


class WCShippingZoneDetail(BaseModel):
    """Zone plus its locations and methods."""

    model_config = ConfigDict(extra="forbid")

    zone: WCShippingZone
    locations: list[ZoneLocation] = Field(default_factory=list)
    methods: list["WCShippingMethod"] = Field(default_factory=list)


class WCShippingMethod(BaseModel):
    """A shipping method instance inside a zone."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    instance_id: int | None = None
    title: str = ""
    method_id: str = ""
    method_title: str = ""
    method_description: str = ""
    enabled: bool = False
    settings: dict[str, Any] = Field(default_factory=dict)


class WCAvailableMethod(BaseModel):
    """A shipping method type available on this store."""

    model_config = ConfigDict(extra="ignore")

    id: str
    title: str = ""
    description: str = ""


# --- Requests --------------------------------------------------------------


class ZoneCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Zone name.",
        examples=["Pakistan"],
    )
    order: int = Field(default=0, ge=0, le=999)
    locations: list[ZoneLocation] = Field(
        default_factory=list,
        description="Locations to assign to this zone after creation.",
    )


class ZoneUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    order: int | None = Field(default=None, ge=0, le=999)
    locations: list[ZoneLocation] | None = Field(
        default=None,
        description="If provided, replaces the zone's locations entirely.",
    )


class ZoneLocationsUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    locations: list[ZoneLocation] = Field(default_factory=list)


class MethodAddRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Method type, e.g. flat_rate, free_shipping, local_pickup.",
        examples=["flat_rate"],
    )
    title: str | None = Field(default=None, max_length=200)
    enabled: bool = True
    settings: dict[str, Any] = Field(default_factory=dict)


class MethodUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, max_length=200)
    enabled: bool | None = None
    settings: dict[str, Any] | None = None


# --- Responses -------------------------------------------------------------


class ZoneListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[WCShippingZone] = Field(default_factory=list)


class AvailableMethodsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[WCAvailableMethod] = Field(default_factory=list)


# Forward ref resolution
WCShippingZoneDetail.model_rebuild()