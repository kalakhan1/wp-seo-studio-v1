"""Sample WooCommerce REST API JSON responses for tests."""

from __future__ import annotations

from typing import Any

# --- Products ---------------------------------------------------------------

WC_PRODUCT_JSON: dict[str, Any] = {
    "id": 501,
    "name": "Herbal Hair Oil",
    "slug": "herbal-hair-oil",
    "type": "simple",
    "status": "draft",
    "permalink": "https://example.test/product/herbal-hair-oil/",
    "sku": "HHO-001",
    "description": "<p>Natural herbal hair oil for daily care.</p>",
    "short_description": "<p>Daily care hair oil.</p>",
    "regular_price": "499.00",
    "sale_price": "",
    "price": "499.00",
    "date_on_sale_from": None,
    "date_on_sale_to": None,
    "tax_status": "taxable",
    "tax_class": "",
    "manage_stock": False,
    "stock_quantity": None,
    "stock_status": "instock",
    "backorders": "no",
    "low_stock_amount": None,
    "sold_individually": False,
    "weight": "",
    "dimensions": {"length": "", "width": "", "height": ""},
    "shipping_class": "",
    "featured": False,
    "catalog_visibility": "visible",
    "on_sale": False,
    "total_sales": 0,
    "average_rating": "0",
    "rating_count": 0,
    "reviews_allowed": True,
    "purchase_note": "",
    "categories": [{"id": 5, "name": "Hair Care", "slug": "hair-care"}],
    "tags": [{"id": 10, "name": "herbal", "slug": "herbal"}],
    "images": [
        {
            "id": 101,
            "src": "https://example.test/wp-content/uploads/hho.jpg",
            "alt": "Herbal Hair Oil",
        }
    ],
    "attributes": [],
    "meta_data": [],
    "related_ids": [],
    "upsell_ids": [],
    "cross_sell_ids": [],
    "menu_order": 0,
    "parent_id": 0,
}

WC_PRODUCT_MINIMAL_JSON: dict[str, Any] = {
    "id": 502,
    "name": "Simple Product",
    "slug": "simple-product",
    "type": "simple",
    "status": "publish",
    "permalink": "https://example.test/product/simple-product/",
    "sku": "",
    "description": "",
    "short_description": "",
    "regular_price": "100.00",
    "sale_price": "",
    "price": "100.00",
    "tax_status": "taxable",
    "tax_class": "",
    "manage_stock": False,
    "stock_status": "instock",
    "backorders": "no",
    "sold_individually": False,
    "weight": "",
    "dimensions": {"length": "", "width": "", "height": ""},
    "shipping_class": "",
    "featured": False,
    "catalog_visibility": "visible",
    "on_sale": False,
    "reviews_allowed": True,
    "purchase_note": "",
    "categories": [],
    "tags": [],
    "images": [],
    "attributes": [],
    "meta_data": [],
    "menu_order": 0,
    "parent_id": 0,
}

WC_PRODUCT_LIST_JSON: list[dict[str, Any]] = [
    WC_PRODUCT_JSON,
    WC_PRODUCT_MINIMAL_JSON,
]

WC_PRODUCT_CATEGORIES_JSON: list[dict[str, Any]] = [
    {
        "id": 5,
        "name": "Hair Care",
        "slug": "hair-care",
        "parent": 0,
        "description": "",
        "count": 12,
        "image": None,
    },
    {
        "id": 6,
        "name": "Skin Care",
        "slug": "skin-care",
        "parent": 0,
        "description": "",
        "count": 8,
        "image": None,
    },
]

WC_PRODUCT_TAGS_JSON: list[dict[str, Any]] = [
    {"id": 10, "name": "herbal", "slug": "herbal", "count": 20},
    {"id": 11, "name": "natural", "slug": "natural", "count": 15},
]

WC_DUPLICATE_SKU_ERROR_JSON: dict[str, Any] = {
    "code": "product_invalid_sku",
    "message": "Invalid or duplicated SKU.",
    "data": {"status": 400},
}

# --- Settings ---------------------------------------------------------------

WC_SETTINGS_GENERAL_JSON: list[dict[str, Any]] = [
    {
        "id": "woocommerce_store_address",
        "label": "Address",
        "description": "The street address for your business location.",
        "type": "text",
        "value": "123 Main Street",
        "default": "",
        "options": {},
        "tip": "This is used for invoices.",
    },
    {
        "id": "woocommerce_store_address_2",
        "label": "Address line 2",
        "description": "",
        "type": "text",
        "value": "",
        "default": "",
        "options": {},
        "tip": "",
    },
    {
        "id": "woocommerce_store_city",
        "label": "City",
        "description": "",
        "type": "text",
        "value": "Karachi",
        "default": "",
        "options": {},
        "tip": "",
    },
    {
        "id": "woocommerce_default_country",
        "label": "Country / State",
        "description": "",
        "type": "select",
        "value": "PK:SD",
        "default": "US:CA",
        "options": {
            "PK:SD": "Sindh",
            "PK:PB": "Punjab",
            "US:CA": "California",
        },
        "tip": "",
    },
    {
        "id": "woocommerce_store_postcode",
        "label": "Postcode / ZIP",
        "description": "",
        "type": "text",
        "value": "74200",
        "default": "",
        "options": {},
        "tip": "",
    },
    {
        "id": "woocommerce_currency",
        "label": "Currency",
        "description": "",
        "type": "select",
        "value": "PKR",
        "default": "USD",
        "options": {"PKR": "Pakistani rupee", "USD": "United States (US) dollar"},
        "tip": "",
    },
    {
        "id": "woocommerce_currency_symbol",
        "label": "Currency symbol",
        "description": "",
        "type": "text",
        "value": "Rs",
        "default": "$",
        "options": {},
        "tip": "",
    },
    {
        "id": "woocommerce_currency_pos",
        "label": "Currency position",
        "description": "",
        "type": "select",
        "value": "left",
        "default": "left",
        "options": {
            "left": "Left",
            "right": "Right",
            "left_space": "Left with space",
            "right_space": "Right with space",
        },
        "tip": "",
    },
    {
        "id": "woocommerce_price_thousand_sep",
        "label": "Thousand separator",
        "description": "",
        "type": "text",
        "value": ",",
        "default": ",",
        "options": {},
        "tip": "",
    },
    {
        "id": "woocommerce_price_decimal_sep",
        "label": "Decimal separator",
        "description": "",
        "type": "text",
        "value": ".",
        "default": ".",
        "options": {},
        "tip": "",
    },
    {
        "id": "woocommerce_price_num_decimals",
        "label": "Number of decimals",
        "description": "",
        "type": "number",
        "value": "2",
        "default": "2",
        "options": {},
        "tip": "",
    },
    {
        "id": "woocommerce_allowed_countries",
        "label": "Selling location(s)",
        "description": "",
        "type": "select",
        "value": "all",
        "default": "all",
        "options": {
            "all": "Sell to all countries",
            "specific": "Sell to specific countries",
            "all_except": "Sell to all countries, except for...",
        },
        "tip": "",
    },
    {
        "id": "woocommerce_specific_allowed_countries",
        "label": "Sell to specific countries",
        "description": "",
        "type": "multiselect",
        "value": [],
        "default": [],
        "options": {"PK": "Pakistan", "US": "United States"},
        "tip": "",
    },
    {
        "id": "woocommerce_all_except_countries",
        "label": "Sell to all countries, except for...",
        "description": "",
        "type": "multiselect",
        "value": [],
        "default": [],
        "options": {"PK": "Pakistan", "US": "United States"},
        "tip": "",
    },
    {
        "id": "woocommerce_ship_to_countries",
        "label": "Shipping location(s)",
        "description": "",
        "type": "select",
        "value": "",
        "default": "",
        "options": {
            "": "Ship to all countries you sell to",
            "all": "Ship to all countries",
            "specific": "Ship to specific countries only",
            "disabled": "Disable shipping & shipping calculations",
        },
        "tip": "",
    },
    {
        "id": "woocommerce_specific_ship_to_countries",
        "label": "Ship to specific countries",
        "description": "",
        "type": "multiselect",
        "value": [],
        "default": [],
        "options": {"PK": "Pakistan", "US": "United States"},
        "tip": "",
    },
]

WC_SETTINGS_PRODUCTS_JSON: list[dict[str, Any]] = [
    {
        "id": "woocommerce_weight_unit",
        "label": "Weight unit",
        "description": "",
        "type": "select",
        "value": "kg",
        "default": "kg",
        "options": {"kg": "kg", "g": "g", "lbs": "lbs", "oz": "oz"},
        "tip": "",
    },
    {
        "id": "woocommerce_dimension_unit",
        "label": "Dimensions unit",
        "description": "",
        "type": "select",
        "value": "cm",
        "default": "cm",
        "options": {"m": "m", "cm": "cm", "mm": "mm", "in": "in", "yd": "yd"},
        "tip": "",
    },
    {
        "id": "woocommerce_enable_reviews",
        "label": "Enable product reviews",
        "description": "",
        "type": "checkbox",
        "value": "yes",
        "default": "yes",
        "options": {},
        "tip": "",
    },
    {
        "id": "woocommerce_enable_review_rating",
        "label": "Enable star ratings",
        "description": "",
        "type": "checkbox",
        "value": "yes",
        "default": "yes",
        "options": {},
        "tip": "",
    },
    {
        "id": "woocommerce_review_rating_verification_required",
        "label": "Require verified owner",
        "description": "",
        "type": "checkbox",
        "value": "no",
        "default": "no",
        "options": {},
        "tip": "",
    },
]

WC_SETTINGS_TAX_JSON: list[dict[str, Any]] = [
    {
        "id": "woocommerce_calc_taxes",
        "label": "Enable taxes",
        "description": "",
        "type": "checkbox",
        "value": "no",
        "default": "no",
        "options": {},
        "tip": "",
    },
    {
        "id": "woocommerce_prices_include_tax",
        "label": "Prices entered with tax",
        "description": "",
        "type": "checkbox",
        "value": "no",
        "default": "no",
        "options": {},
        "tip": "",
    },
    {
        "id": "woocommerce_tax_based_on",
        "label": "Calculate tax based on",
        "description": "",
        "type": "select",
        "value": "shipping",
        "default": "shipping",
        "options": {
            "shipping": "Customer shipping address",
            "billing": "Customer billing address",
            "base": "Shop base address",
        },
        "tip": "",
    },
    {
        "id": "woocommerce_default_customer_address",
        "label": "Default customer location",
        "description": "",
        "type": "select",
        "value": "geolocation",
        "default": "geolocation",
        "options": {
            "base": "Shop base address",
            "geolocation": "Geolocate",
            "geolocation_ajax": "Geolocate (with page caching support)",
        },
        "tip": "",
    },
]

WC_SETTINGS_CHECKOUT_JSON: list[dict[str, Any]] = [
    {
        "id": "woocommerce_enable_guest_checkout",
        "label": "Guest checkout",
        "description": "",
        "type": "checkbox",
        "value": "yes",
        "default": "yes",
        "options": {},
        "tip": "",
    },
    {
        "id": "woocommerce_enable_coupons",
        "label": "Enable coupons",
        "description": "",
        "type": "checkbox",
        "value": "yes",
        "default": "yes",
        "options": {},
        "tip": "",
    },
    {
        "id": "woocommerce_enable_signup_and_login_from_checkout",
        "label": "Allow customers to create an account during checkout",
        "description": "",
        "type": "checkbox",
        "value": "no",
        "default": "no",
        "options": {},
        "tip": "",
    },
    {
        "id": "woocommerce_registration_generate_password",
        "label": "When creating an account, automatically generate a password",
        "description": "",
        "type": "checkbox",
        "value": "yes",
        "default": "yes",
        "options": {},
        "tip": "",
    },
]

# --- Payment gateways -------------------------------------------------------

WC_GATEWAY_COD_ENABLED_JSON: dict[str, Any] = {
    "id": "cod",
    "title": "Cash on delivery",
    "description": "Pay with cash upon delivery.",
    "order": 1,
    "enabled": True,
    "method_title": "Cash on delivery",
    "method_description": "Have the customer pay in cash upon delivery.",
    "method_supports": ["products"],
    "settings": {
        "title": {
            "id": "title",
            "label": "Title",
            "type": "text",
            "value": "Cash on delivery",
        },
        "description": {
            "id": "description",
            "label": "Description",
            "type": "textarea",
            "value": "Pay with cash upon delivery.",
        },
        "instructions": {
            "id": "instructions",
            "label": "Instructions",
            "type": "textarea",
            "value": "Please have exact change ready.",
        },
        "enable_for_virtual": {
            "id": "enable_for_virtual",
            "label": "Enable for virtual orders",
            "type": "checkbox",
            "value": "no",
        },
        "enable_for_methods": {
            "id": "enable_for_methods",
            "label": "Enable for shipping methods",
            "type": "multiselect",
            "value": [],
        },
    },
}


WC_GATEWAY_COD_DISABLED_JSON: dict[str, Any] = {
    "id": "cod",
    "title": "Cash on delivery",
    "description": "Pay with cash upon delivery.",
    "order": 1,
    "enabled": False,
    "method_title": "Cash on delivery",
    "method_description": "",
    "method_supports": ["products"],
    "settings": {
        "title": {"id": "title", "type": "text", "value": "Cash on delivery"},
        "description": {"id": "description", "type": "textarea", "value": ""},
        "instructions": {"id": "instructions", "type": "textarea", "value": ""},
        "enable_for_virtual": {
            "id": "enable_for_virtual",
            "type": "checkbox",
            "value": "no",
        },
        "enable_for_methods": {
            "id": "enable_for_methods",
            "type": "multiselect",
            "value": [],
        },
    },
}


WC_GATEWAY_BACS_JSON: dict[str, Any] = {
    "id": "bacs",
    "title": "Direct bank transfer",
    "description": "Make your payment directly into our bank account.",
    "order": 2,
    "enabled": False,
    "method_title": "Direct bank transfer",
    "method_description": "",
    "method_supports": ["products"],
    "settings": {},
}


WC_GATEWAY_LIST_JSON: list[dict[str, Any]] = [
    WC_GATEWAY_COD_ENABLED_JSON,
    WC_GATEWAY_BACS_JSON,
]

# --- Shipping zones ---------------------------------------------------------

WC_SHIPPING_ZONE_JSON: dict[str, Any] = {
    "id": 1,
    "name": "Pakistan",
    "order": 0,
}

WC_SHIPPING_ZONE_2_JSON: dict[str, Any] = {
    "id": 2,
    "name": "Rest of the world",
    "order": 1,
}

WC_SHIPPING_ZONES_LIST_JSON: list[dict[str, Any]] = [
    WC_SHIPPING_ZONE_JSON,
    WC_SHIPPING_ZONE_2_JSON,
]

WC_ZONE_LOCATIONS_JSON: list[dict[str, Any]] = [
    {"code": "PK", "type": "country"},
]

WC_ZONE_METHODS_JSON: list[dict[str, Any]] = [
    {
        "id": 10,
        "instance_id": 10,
        "title": "Flat rate",
        "method_id": "flat_rate",
        "method_title": "Flat rate",
        "method_description": "Standard flat rate shipping.",
        "enabled": True,
        "settings": {
            "cost": {"id": "cost", "type": "text", "value": "150"},
        },
    },
    {
        "id": 11,
        "instance_id": 11,
        "title": "Free shipping",
        "method_id": "free_shipping",
        "method_title": "Free shipping",
        "method_description": "Free shipping.",
        "enabled": False,
        "settings": {
            "min_amount": {"id": "min_amount", "type": "text", "value": "1000"},
        },
    },
]

WC_AVAILABLE_METHODS_JSON: list[dict[str, Any]] = [
    {
        "id": "flat_rate",
        "title": "Flat rate",
        "description": "Lets you charge a fixed rate for shipping.",
    },
    {
        "id": "free_shipping",
        "title": "Free shipping",
        "description": "Free shipping is a great way to attract customers.",
    },
    {
        "id": "local_pickup",
        "title": "Local pickup",
        "description": "Allow customers to pick up their order.",
    },
]