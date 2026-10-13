"""Internal linking service.

Responsibilities:
  - Search across WordPress posts, pages, and WooCommerce products.
  - Suggest related content based on title similarity and taxonomy.
  - Validate that a URL belongs to the connected site.

This service never inserts links into content. It only provides data to
the frontend, which the user reviews and approves.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.core.exceptions import AuthError, ValidationError
from app.integrations.wordpress.client import WordPressClient
from app.integrations.wordpress.types import WPPost
from app.integrations.woocommerce.client import WooCommerceClient
from app.models.connection import Connection
from app.schemas.internal_link import (
    AnchorTextCheckResponse,
    SearchResponse,
    SearchResultItem,
    SuggestResponse,
    SuggestedLink,
    ValidateUrlResponse,
)
from app.security import secrets as secret_store


_WORD_RE = re.compile(r"[A-Za-z0-9]+")


def _tokenize(text: str) -> set[str]:
    """Lower-case word tokens of length >= 3. Stopwords are not filtered —
    the corpus is small and we prefer recall over precision."""
    tokens = {m.group(0).lower() for m in _WORD_RE.finditer(text or "")}
    return {t for t in tokens if len(t) >= 3}


def _similarity(a: str, b: str) -> float:
    """Jaccard similarity of word tokens in [0, 1]."""
    ta = _tokenize(a)
    tb = _tokenize(b)
    if not ta or not tb:
        return 0.0
    inter = ta & tb
    union = ta | tb
    return len(inter) / len(union) if union else 0.0


class InternalLinkService:
    """Stateless. Construct per request with settings + session."""

    def __init__(self, *, settings: Settings, session: AsyncSession) -> None:
        self._settings = settings
        self._session = session

    # --- Search ------------------------------------------------------------

    async def search(
        self,
        *,
        connection_id: int,
        query: str,
        include_posts: bool = True,
        include_pages: bool = True,
        include_products: bool = True,
        per_page: int = 10,
        http: Any,
    ) -> SearchResponse:
        warnings: list[str] = []
        items: list[SearchResultItem] = []

        wp = await self._wp_client(connection_id, http)

        if include_posts or include_pages:
            subtypes: list[str] = []
            if include_posts:
                subtypes.append("post")
            if include_pages:
                subtypes.append("page")
            try:
                raw = await wp._get_json(  # noqa: SLF001 - internal but intentional
                    "/wp-json/wp/v2/search",
                    params={
                        "search": query,
                        "subtype": ",".join(subtypes),
                        "per_page": per_page,
                    },
                )
                if isinstance(raw, list):
                    for entry in raw:
                        items.append(self._search_entry_to_item(entry))
            except Exception as exc:  # noqa: BLE001
                warnings.append(
                    f"WordPress search failed: {exc.__class__.__name__}"
                )

        if include_products:
            try:
                wc = await self._wc_client(connection_id, http)
                products = await wc.list_products(
                    per_page=per_page, search=query
                )
                for p in products:
                    items.append(
                        SearchResultItem(
                            id=p.id,
                            type="product",
                            title=p.name,
                            url=p.permalink,
                            slug=p.slug,
                            excerpt=p.short_description,
                        )
                    )
            except Exception as exc:  # noqa: BLE001
                warnings.append(
                    f"WooCommerce search failed: {exc.__class__.__name__}"
                )

        return SearchResponse(items=items, warnings=warnings)

    # --- Suggest -----------------------------------------------------------

    async def suggest(
        self,
        *,
        connection_id: int,
        source_title: str,
        source_content: str = "",
        source_categories: list[int] | None = None,
        exclude_ids: list[int] | None = None,
        limit: int = 10,
        http: Any,
    ) -> SuggestResponse:
        """Suggest related content.

        Scoring:
          - Title similarity: 0.6 weight
          - Content similarity (if provided): 0.2 weight
          - Category overlap: 0.2 weight

        Only suggestions with score >= 0.1 are returned.
        """
        warnings: list[str] = []
        exclude = set(exclude_ids or [])
        category_set = set(source_categories or [])

        # Load a batch of candidates from WordPress.
        wp = await self._wp_client(connection_id, http)
        candidates: list[WPPost] = []
        try:
            posts = await wp._get_json(  # noqa: SLF001
                "/wp-json/wp/v2/posts",
                params={"per_page": 50, "status": "publish"},
            )
            if isinstance(posts, list):
                candidates.extend(
                    WPPost.model_validate(p) for p in posts
                )
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"Could not list posts: {exc.__class__.__name__}")

        try:
            pages = await wp._get_json(  # noqa: SLF001
                "/wp-json/wp/v2/pages",
                params={"per_page": 50, "status": "publish"},
            )
            if isinstance(pages, list):
                candidates.extend(
                    WPPost.model_validate(p) for p in pages
                )
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"Could not list pages: {exc.__class__.__name__}")

        # Score candidates
        scored: list[SuggestedLink] = []
        for p in candidates:
            if p.id in exclude:
                continue
            title = p.raw_title()
            if not title:
                continue
            title_score = _similarity(source_title, title)
            content_score = (
                _similarity(source_content, p.raw_content())
                if source_content
                else 0.0
            )
            cat_ids = set(p.categories or [])
            cat_overlap = (
                len(category_set & cat_ids) / max(1, len(category_set))
                if category_set
                else 0.0
            )
            score = 0.6 * title_score + 0.2 * content_score + 0.2 * cat_overlap
            if score < 0.1:
                continue

            reasons: list[str] = []
            if title_score > 0.15:
                reasons.append("title similar")
            if content_score > 0.15:
                reasons.append("content similar")
            if cat_overlap > 0:
                reasons.append("shared category")

            scored.append(
                SuggestedLink(
                    target_id=p.id,
                    target_type=p.type or "post",
                    title=title,
                    url=p.link,
                    score=round(score, 3),
                    reason=", ".join(reasons),
                    suggested_anchor=title[:60],
                )
            )

        scored.sort(key=lambda s: s.score, reverse=True)
        return SuggestResponse(items=scored[:limit], warnings=warnings)

    # --- URL validation ----------------------------------------------------

    async def validate_url(
        self, *, connection_id: int, url: str
    ) -> ValidateUrlResponse:
        connection = await self._require_connection(connection_id)
        site_host = (urlparse(connection.base_url).hostname or "").lower()
        try:
            parsed = urlparse(url)
        except Exception:  # noqa: BLE001
            return ValidateUrlResponse(
                ok=False,
                reason="URL could not be parsed.",
            )
        if not parsed.scheme or parsed.scheme not in ("http", "https"):
            return ValidateUrlResponse(
                ok=False,
                reason="Only HTTP and HTTPS URLs are allowed.",
            )
        target_host = (parsed.hostname or "").lower()
        if not target_host:
            return ValidateUrlResponse(
                ok=False,
                reason="URL has no hostname.",
            )
        if target_host != site_host:
            return ValidateUrlResponse(
                ok=False,
                reason=(
                    f"URL host {target_host!r} does not match the connected "
                    f"site {site_host!r}."
                ),
                host=target_host,
            )
        return ValidateUrlResponse(
            ok=True,
            reason="URL belongs to the connected site.",
            normalized_url=url,
            host=target_host,
        )

    # --- Anchor text check -------------------------------------------------

    async def check_anchor_text(
        self,
        *,
        anchor_text: str,
        existing_anchors: list[str],
    ) -> AnchorTextCheckResponse:
        anchor = anchor_text.strip().lower()
        if not anchor:
            return AnchorTextCheckResponse(
                warnings=["Anchor text is empty."],
            )

        exact = sum(1 for a in existing_anchors if a.strip().lower() == anchor)
        warnings: list[str] = []
        if exact >= 3:
            warnings.append(
                f"Exact anchor {anchor_text!r} is already used {exact} times "
                "in this content. Vary the anchor to avoid over-optimization."
            )
        elif exact >= 2:
            warnings.append(
                f"Exact anchor {anchor_text!r} is already used {exact} times. "
                "Consider a variation."
            )
        if len(anchor_text) > 100:
            warnings.append(
                "Anchor text is very long. Shorter anchors are easier to read."
            )
        return AnchorTextCheckResponse(
            warnings=warnings,
            exact_match_count=exact,
        )

    # --- Internals ---------------------------------------------------------

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

    async def _wp_client(self, connection_id: int, http: Any) -> WordPressClient:
        c = await self._require_connection(connection_id)
        label = c.secret_ref or c.label
        password = secret_store.get_secret(
            label, secret_store.FIELD_WP_APP_PASSWORD
        )
        if not password:
            raise AuthError(
                "Stored WordPress credentials are missing from the OS keyring.",
                details={"label": label},
            )
        return WordPressClient(
            base_url=c.base_url,
            username=c.username,
            app_password=password,
            auth_method=c.auth_method,
            http=http,
        )

    async def _wc_client(
        self, connection_id: int, http: Any
    ) -> WooCommerceClient:
        c = await self._require_connection(connection_id)
        label = c.secret_ref or c.label
        key = secret_store.get_secret(label, secret_store.FIELD_WC_CONSUMER_KEY)
        sec = secret_store.get_secret(label, secret_store.FIELD_WC_CONSUMER_SECRET)
        if not key or not sec:
            raise AuthError(
                "WooCommerce REST API keys are missing for this connection.",
                details={"label": label},
            )
        return WooCommerceClient(
            base_url=c.base_url,
            consumer_key=key,
            consumer_secret=sec,
            http=http,
        )

    @staticmethod
    def _search_entry_to_item(entry: dict[str, Any]) -> SearchResultItem:
        return SearchResultItem(
            id=int(entry.get("id", 0) or 0),
            type=str(entry.get("subtype", "") or entry.get("type", "") or ""),
            title=str(entry.get("title", "") or ""),
            url=str(entry.get("url", "") or ""),
            slug=str(entry.get("slug", "") or ""),
            excerpt=str(entry.get("excerpt", "") or ""),
        )