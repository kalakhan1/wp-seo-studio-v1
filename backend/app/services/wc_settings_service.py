"""WooCommerce store settings service.

Reads and updates WooCommerce settings by group, and builds a normalized
store profile with a completeness checklist.

Design principles:
  - Never assume a setting's type. Fetch it, look at `type`, and validate
    the update value against it.
  - Update one setting at a time (WC API is per-setting).
  - Preserve unrelated settings untouched.
  - Warnings are actionable, not decorative.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.core.exceptions import AuthError, ValidationError
from app.integrations.woocommerce.client import WooCommerceClient
from app.models.connection import Connection
from app.schemas.wc_settings import (
    ChecklistItem,
    StoreAddress,
    StoreChecklist,
    StoreProfile,
    StoreProfileResponse,
    WCSetting,
    WCSettingsGroupResponse,
)
from app.security import secrets as secret_store

_log = logging.getLogger(__name__)


# Known WC setting groups. WC API does not expose a "list groups" endpoint,
# so we hardcode the known groups and let the caller fetch any of them.
KNOWN_GROUPS: tuple[str, ...] = (
    "general",
    "products",
    "tax",
    "checkout",
    "shipping",
    "account",
    "advanced",
)


class WCSettingsService:
    """Stateless. Construct per request with settings + session."""

    def __init__(self, *, settings: Settings, session: AsyncSession) -> None:
        self._settings = settings
        self._session = session

    # --- Settings CRUD -----------------------------------------------------

    async def list_groups(self) -> list[str]:
        return list(KNOWN_GROUPS)

    async def get_group(
        self,
        *,
        connection_id: int,
        group: str,
        http: Any,  # SafeHttpClient
    ) -> WCSettingsGroupResponse:
        self._validate_group(group)
        wc = await self._wc_client(connection_id, http)
        raw = await wc.get_settings_group(group)
        settings = [WCSetting.model_validate(item) for item in raw]
        return WCSettingsGroupResponse(group=group, settings=settings)

    async def get_setting(
        self,
        *,
        connection_id: int,
        group: str,
        setting_id: str,
        http: Any,
    ) -> WCSetting:
        self._validate_group(group)
        wc = await self._wc_client(connection_id, http)
        raw = await wc.get_setting(group, setting_id)
        return WCSetting.model_validate(raw)

    async def update_setting(
        self,
        *,
        connection_id: int,
        group: str,
        setting_id: str,
        value: Any,
        http: Any,
    ) -> WCSetting:
        self._validate_group(group)
        wc = await self._wc_client(connection_id, http)

        # Fetch the setting first to know its declared type, then validate.
        current_raw = await wc.get_setting(group, setting_id)
        current = WCSetting.model_validate(current_raw)
        coerced = self._coerce_value_for_type(current.type, value, current.id)

        updated_raw = await wc.update_setting(group, setting_id, coerced)
        return WCSetting.model_validate(updated_raw)

    # --- Store profile -----------------------------------------------------

    async def get_store_profile(
        self,
        *,
        connection_id: int,
        http: Any,
    ) -> StoreProfileResponse:
        wc = await self._wc_client(connection_id, http)
        general = self._index_by_id(await wc.get_settings_group("general"))
        products = self._index_by_id(await wc.get_settings_group("products"))
        tax = self._index_by_id(await wc.get_settings_group("tax"))
        checkout = self._index_by_id(await wc.get_settings_group("checkout"))

        profile = self._build_profile(general, products, tax, checkout)
        checklist, warnings = self._build_checklist(profile)

        return StoreProfileResponse(
            profile=profile,
            checklist=checklist,
            warnings=warnings,
        )

    # --- Internals ---------------------------------------------------------

    @staticmethod
    def _validate_group(group: str) -> None:
        if group not in KNOWN_GROUPS:
            raise ValidationError(
                f"Unknown settings group: {group!r}.",
                details={"allowed": list(KNOWN_GROUPS)},
            )

    async def _require_connection(self, connection_id: int) -> Connection:
        result = await self._session.execute(
            select(Connection).where(Connection.id == connection_id)
        )
        c = result.scalar_one_or_none()
        if c is None:
            raise ValidationError(
                "Connection not found.",
                details={"connection_id": connection_id},
            )
        return c

    async def _wc_client(
        self,
        connection_id: int,
        http: Any,
    ) -> WooCommerceClient:
        c = await self._require_connection(connection_id)
        label = c.secret_ref or c.label
        wc_key = secret_store.get_secret(label, secret_store.FIELD_WC_CONSUMER_KEY)
        wc_secret = secret_store.get_secret(
            label, secret_store.FIELD_WC_CONSUMER_SECRET
        )
        if not wc_key or not wc_secret:
            raise AuthError(
                "WooCommerce REST API keys are missing for this connection.",
                details={"label": label},
            )
        return WooCommerceClient(
            base_url=c.base_url,
            consumer_key=wc_key,
            consumer_secret=wc_secret,
            http=http,
        )

    @staticmethod
    def _index_by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for row in rows:
            rid = row.get("id")
            if isinstance(rid, str):
                out[rid] = row
        return out

    @staticmethod
    def _coerce_value_for_type(wc_type: str, value: Any, setting_id: str) -> Any:
        """Validate and normalize a value against the setting's type.

        WC uses strings for checkboxes ("yes"/"no") and for numbers.
        Multiselect uses a list of strings.
        """
        if wc_type == "checkbox":
            # Accept bool or "yes"/"no" strings.
            if isinstance(value, bool):
                return "yes" if value else "no"
            if isinstance(value, str):
                if value.lower() in ("yes", "true", "1"):
                    return "yes"
                if value.lower() in ("no", "false", "0", ""):
                    return "no"
            raise ValidationError(
                f"Setting {setting_id!r} expects a boolean (yes/no).",
                details={"received": value, "type": wc_type},
            )
        if wc_type == "multiselect":
            if not isinstance(value, list):
                raise ValidationError(
                    f"Setting {setting_id!r} expects a list of strings.",
                    details={"received_type": type(value).__name__},
                )
            if not all(isinstance(v, str) for v in value):
                raise ValidationError(
                    f"Setting {setting_id!r} list must contain only strings.",
                )
            return list(value)
        if wc_type in ("number", "text", "email", "url", "color", "textarea"):
            if value is None:
                return ""
            if isinstance(value, (int, float, bool)):
                return str(value)
            if isinstance(value, str):
                return value
            raise ValidationError(
                f"Setting {setting_id!r} expects a string value.",
                details={"received_type": type(value).__name__},
            )
        if wc_type in ("select", "radio", "single_select_page"):
            if value is None:
                return ""
            if isinstance(value, str):
                return value
            if isinstance(value, (int, float)):
                return str(value)
            raise ValidationError(
                f"Setting {setting_id!r} expects a single string value.",
            )
        # Unknown type — pass through.
        return value

    # --- Profile extraction ------------------------------------------------

    @staticmethod
    def _str_value(rows: dict[str, dict[str, Any]], setting_id: str) -> str:
        row = rows.get(setting_id)
        if row is None:
            return ""
        v = row.get("value")
        return v if isinstance(v, str) else ("" if v is None else str(v))

    @staticmethod
    def _list_value(rows: dict[str, dict[str, Any]], setting_id: str) -> list[str]:
        row = rows.get(setting_id)
        if row is None:
            return []
        v = row.get("value")
        if isinstance(v, list):
            return [str(x) for x in v]
        return []

    @staticmethod
    def _bool_value(rows: dict[str, dict[str, Any]], setting_id: str) -> bool:
        return WCSettingsService._str_value(rows, setting_id) == "yes"

    @staticmethod
    def _int_value(rows: dict[str, dict[str, Any]], setting_id: str, default: int = 0) -> int:
        v = WCSettingsService._str_value(rows, setting_id)
        try:
            return int(v)
        except (TypeError, ValueError):
            return default

    def _build_profile(
        self,
        general: dict[str, dict[str, Any]],
        products: dict[str, dict[str, Any]],
        tax: dict[str, dict[str, Any]],
        checkout: dict[str, dict[str, Any]],
    ) -> StoreProfile:
        raw_country_state = self._str_value(general, "woocommerce_default_country")
        country = ""
        state = ""
        if raw_country_state:
            if ":" in raw_country_state:
                country, _, state = raw_country_state.partition(":")
            else:
                country = raw_country_state

        address = StoreAddress(
            address_1=self._str_value(general, "woocommerce_store_address"),
            address_2=self._str_value(general, "woocommerce_store_address_2"),
            city=self._str_value(general, "woocommerce_store_city"),
            postcode=self._str_value(general, "woocommerce_store_postcode"),
            country=country,
            state=state,
            country_state_raw=raw_country_state,
        )

        selling_type = self._str_value(general, "woocommerce_allowed_countries")
        selling_countries: list[str] = []
        if selling_type == "specific":
            selling_countries = self._list_value(
                general, "woocommerce_specific_allowed_countries"
            )
        elif selling_type == "all_except":
            selling_countries = self._list_value(
                general, "woocommerce_all_except_countries"
            )

        shipping_type = self._str_value(general, "woocommerce_ship_to_countries")
        shipping_countries: list[str] = []
        if shipping_type == "specific":
            shipping_countries = self._list_value(
                general, "woocommerce_specific_ship_to_countries"
            )

        return StoreProfile(
            address=address,
            currency=self._str_value(general, "woocommerce_currency"),
            currency_symbol=self._str_value(general, "woocommerce_currency_symbol"),
            currency_position=self._str_value(general, "woocommerce_currency_pos"),
            price_num_decimals=self._int_value(
                general, "woocommerce_price_num_decimals", 2
            ),
            price_thousand_sep=self._str_value(general, "woocommerce_price_thousand_sep"),
            price_decimal_sep=self._str_value(general, "woocommerce_price_decimal_sep"),
            weight_unit=self._str_value(products, "woocommerce_weight_unit"),
            dimension_unit=self._str_value(products, "woocommerce_dimension_unit"),
            selling_locations_type=selling_type,
            selling_countries=selling_countries,
            shipping_locations_type=shipping_type,
            shipping_countries=shipping_countries,
            tax_enabled=self._bool_value(tax, "woocommerce_calc_taxes"),
            prices_include_tax=self._bool_value(
                tax, "woocommerce_prices_include_tax"
            ),
            tax_based_on=self._str_value(tax, "woocommerce_tax_based_on"),
            default_customer_address=self._str_value(
                tax, "woocommerce_default_customer_address"
            ),
            guest_checkout_enabled=self._bool_value(
                checkout, "woocommerce_enable_guest_checkout"
            ),
            coupons_enabled=self._bool_value(checkout, "woocommerce_enable_coupons"),
            account_creation_enabled=self._bool_value(
                checkout, "woocommerce_enable_signup_and_login_from_checkout"
            ),
            registration_generate_password=self._bool_value(
                checkout, "woocommerce_registration_generate_password"
            ),
            reviews_enabled=self._bool_value(products, "woocommerce_enable_reviews"),
            reviews_rating_enabled=self._bool_value(
                products, "woocommerce_enable_review_rating"
            ),
            reviews_verified_required=self._bool_value(
                products, "woocommerce_review_rating_verification_required"
            ),
        )

    def _build_checklist(
        self,
        profile: StoreProfile,
    ) -> tuple[StoreChecklist, list[str]]:
        items: list[ChecklistItem] = []
        warnings: list[str] = []

        # --- Required for a functional store --------------------------------

        # Store address line 1
        if not profile.address.address_1:
            items.append(
                ChecklistItem(
                    key="store_address",
                    label="Store address",
                    status="missing",
                    message="Buyers see this on invoices and emails.",
                    suggested_value="Example: 123 Main Street",
                )
            )
        else:
            items.append(
                ChecklistItem(
                    key="store_address",
                    label="Store address",
                    status="ok",
                    current_value=profile.address.address_1,
                )
            )

        # City
        if not profile.address.city:
            items.append(
                ChecklistItem(
                    key="store_city",
                    label="Store city",
                    status="missing",
                    suggested_value="Example: Karachi",
                )
            )
        else:
            items.append(
                ChecklistItem(
                    key="store_city",
                    label="Store city",
                    status="ok",
                    current_value=profile.address.city,
                )
            )

        # Country
        if not profile.address.country:
            items.append(
                ChecklistItem(
                    key="store_country",
                    label="Country / State",
                    status="missing",
                    message="Required for tax and shipping rules.",
                    suggested_value="Example: PK:SD",
                )
            )
        else:
            items.append(
                ChecklistItem(
                    key="store_country",
                    label="Country / State",
                    status="ok",
                    current_value=profile.address.country_state_raw,
                )
            )

        # Currency
        if not profile.currency:
            items.append(
                ChecklistItem(
                    key="currency",
                    label="Store currency",
                    status="missing",
                    suggested_value="Example: PKR",
                )
            )
        else:
            items.append(
                ChecklistItem(
                    key="currency",
                    label="Store currency",
                    status="ok",
                    current_value=profile.currency,
                )
            )

        # Weight unit
        if not profile.weight_unit:
            items.append(
                ChecklistItem(
                    key="weight_unit",
                    label="Weight unit",
                    status="recommended",
                    message="Needed if you sell physical products with weight.",
                    suggested_value="Example: kg",
                )
            )
        else:
            items.append(
                ChecklistItem(
                    key="weight_unit",
                    label="Weight unit",
                    status="ok",
                    current_value=profile.weight_unit,
                )
            )

        # Dimension unit
        if not profile.dimension_unit:
            items.append(
                ChecklistItem(
                    key="dimension_unit",
                    label="Dimension unit",
                    status="recommended",
                    suggested_value="Example: cm",
                )
            )
        else:
            items.append(
                ChecklistItem(
                    key="dimension_unit",
                    label="Dimension unit",
                    status="ok",
                    current_value=profile.dimension_unit,
                )
            )

        # --- Recommendations -----------------------------------------------

        if not profile.coupons_enabled:
            items.append(
                ChecklistItem(
                    key="coupons_enabled",
                    label="Coupons",
                    status="recommended",
                    message="Enable coupons if you plan promotions.",
                )
            )
        else:
            items.append(
                ChecklistItem(
                    key="coupons_enabled",
                    label="Coupons",
                    status="ok",
                    current_value="enabled",
                )
            )

        if not profile.guest_checkout_enabled:
            items.append(
                ChecklistItem(
                    key="guest_checkout",
                    label="Guest checkout",
                    status="recommended",
                    message=(
                        "Many buyers abandon carts if forced to create an account."
                    ),
                )
            )
        else:
            items.append(
                ChecklistItem(
                    key="guest_checkout",
                    label="Guest checkout",
                    status="ok",
                    current_value="enabled",
                )
            )

        # --- Warnings -------------------------------------------------------

        # Country/state consistency
        if (
            profile.address.country
            and profile.address.country.upper() in ("US", "CA", "AU", "IN", "PK")
            and not profile.address.state
        ):
            warnings.append(
                f"Store country is set to {profile.address.country} but no state "
                "is selected. This may break tax and shipping rules."
            )

        if profile.address.postcode and not profile.address.country:
            warnings.append(
                "Store postcode is set but country is empty."
            )

        if profile.prices_include_tax and not profile.tax_enabled:
            warnings.append(
                "Prices include tax is on but tax calculation is disabled. "
                "This is usually unintended."
            )

        complete = sum(1 for i in items if i.status == "ok")
        recommended = sum(1 for i in items if i.status == "recommended")
        missing = sum(1 for i in items if i.status == "missing")

        return (
            StoreChecklist(
                items=items,
                complete=complete,
                recommended=recommended,
                missing=missing,
            ),
            warnings,
        )