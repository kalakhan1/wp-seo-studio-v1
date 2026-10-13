"""Schemas for WooCommerce settings and store profile."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


WCSettingType = Literal[
    "text",
    "textarea",
    "select",
    "multiselect",
    "checkbox",
    "radio",
    "email",
    "url",
    "number",
    "color",
    "password",
    "single_select_page",
]


class WCSetting(BaseModel):
    """A single WooCommerce setting as returned by the API.

    The `value` type varies by `type`:
      - checkbox:     "yes" or "no" (string, WC convention)
      - multiselect:  list of strings
      - select/radio: string
      - number:       string
      - text/email/url/color: string
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    label: str = ""
    description: str = ""
    type: str = "text"
    value: Any = None
    default: Any = None
    options: dict[str, str] = Field(default_factory=dict)
    tip: str = ""


class WCSettingsGroupResponse(BaseModel):
    """All settings in a group."""

    model_config = ConfigDict(extra="forbid")

    group: str
    settings: list[WCSetting] = Field(default_factory=list)


class WCSettingUpdateRequest(BaseModel):
    """Update a single setting. Value type depends on the setting's type."""

    model_config = ConfigDict(extra="forbid")

    value: Any = Field(
        ...,
        description=(
            "New value. Must match the setting's declared type. "
            "Checkboxes use 'yes'/'no'. Multiselect uses an array of strings."
        ),
    )


class WCSettingUpdateResponse(BaseModel):
    """Result of a setting update."""

    model_config = ConfigDict(extra="forbid")

    group: str
    setting: WCSetting


# --- Store profile ----------------------------------------------------------


class StoreAddress(BaseModel):
    model_config = ConfigDict(extra="forbid")

    address_1: str = ""
    address_2: str = ""
    city: str = ""
    postcode: str = ""
    country: str = ""  # e.g. "US"
    state: str = ""  # e.g. "CA"
    country_state_raw: str = ""  # raw value like "US:CA"


class StoreProfile(BaseModel):
    """Normalized subset of WooCommerce settings for the store."""

    model_config = ConfigDict(extra="forbid")

    address: StoreAddress
    currency: str = ""
    currency_symbol: str = ""
    currency_position: str = ""
    price_num_decimals: int = 2
    price_thousand_sep: str = ","
    price_decimal_sep: str = "."

    weight_unit: str = ""
    dimension_unit: str = ""

    selling_locations_type: str = ""  # all | specific | all_except
    selling_countries: list[str] = Field(default_factory=list)

    shipping_locations_type: str = ""  # "" (same) | all | specific | disabled
    shipping_countries: list[str] = Field(default_factory=list)

    tax_enabled: bool = False
    prices_include_tax: bool = False
    tax_based_on: str = ""
    default_customer_address: str = ""

    guest_checkout_enabled: bool = True
    coupons_enabled: bool = True
    account_creation_enabled: bool = False
    registration_generate_password: bool = False

    reviews_enabled: bool = True
    reviews_rating_enabled: bool = True
    reviews_verified_required: bool = True


class ChecklistItem(BaseModel):
    """One item in the store completeness checklist."""

    model_config = ConfigDict(extra="forbid")

    key: str
    label: str
    status: Literal["ok", "recommended", "missing"]
    message: str = ""
    current_value: str = ""
    suggested_value: str = ""


class StoreChecklist(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ChecklistItem] = Field(default_factory=list)
    complete: int = 0
    recommended: int = 0
    missing: int = 0


class StoreProfileResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile: StoreProfile
    checklist: StoreChecklist
    warnings: list[str] = Field(default_factory=list)