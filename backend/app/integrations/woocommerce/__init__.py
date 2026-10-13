"""WooCommerce REST API integration.

Phase 2 scope: capability probing only. Actual product/order management
arrives in Phase 3 and beyond.
"""

from app.integrations.woocommerce.client import WooCommerceClient
from app.integrations.woocommerce.exceptions import (
    WooAuthError,
    WooClientError,
    WooConnectionError,
    WooNotFoundError,
    WooResponseError,
)

__all__ = [
    "WooCommerceClient",
    "WooAuthError",
    "WooClientError",
    "WooConnectionError",
    "WooNotFoundError",
    "WooResponseError",
]