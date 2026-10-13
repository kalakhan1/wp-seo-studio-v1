"""Main v1 router. Mounts all routes."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import ai_prompts as ai_prompts_routes
from app.api.v1.routes import app_settings as app_settings_routes
from app.api.v1.routes import backup as backup_routes
from app.api.v1.routes import connection as connection_routes
from app.api.v1.routes import content as content_routes
from app.api.v1.routes import health as health_routes
from app.api.v1.routes import history as history_routes
from app.api.v1.routes import image_presets as image_presets_routes
from app.api.v1.routes import internal_links as internal_links_routes
from app.api.v1.routes import media as media_routes
from app.api.v1.routes import products as products_routes
from app.api.v1.routes import queue as queue_routes
from app.api.v1.routes import rankmath_settings as rankmath_settings_routes
from app.api.v1.routes import seo_audit as seo_audit_routes
from app.api.v1.routes import taxonomies as taxonomies_routes
from app.api.v1.routes import wc_gateways as wc_gateways_routes
from app.api.v1.routes import wc_settings as wc_settings_routes
from app.api.v1.routes import wc_shipping as wc_shipping_routes

api_v1_router = APIRouter()
api_v1_router.include_router(health_routes.router)
api_v1_router.include_router(app_settings_routes.router)
api_v1_router.include_router(connection_routes.router)
api_v1_router.include_router(media_routes.router)
api_v1_router.include_router(taxonomies_routes.router)
api_v1_router.include_router(content_routes.router)
api_v1_router.include_router(products_routes.router)
api_v1_router.include_router(wc_settings_routes.router)
api_v1_router.include_router(wc_gateways_routes.router)
api_v1_router.include_router(wc_shipping_routes.router)
api_v1_router.include_router(image_presets_routes.router)
api_v1_router.include_router(rankmath_settings_routes.router)
api_v1_router.include_router(internal_links_routes.router)
api_v1_router.include_router(ai_prompts_routes.router)
api_v1_router.include_router(seo_audit_routes.router)
api_v1_router.include_router(queue_routes.router)
api_v1_router.include_router(history_routes.router)
api_v1_router.include_router(backup_routes.router)