"""WooCommerce payment gateway endpoints.

Read-only for all gateways; COD update is supported.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DBSessionDep, SettingsDep
from app.core.http_client import SafeHttpClient
from app.schemas.wc_gateway import (
    CODSettings,
    CODStatus,
    WCGateway,
    WCGatewayListResponse,
)
from app.services.wc_gateway_service import WCGatewayService

router = APIRouter(prefix="/wc/gateways", tags=["wc-gateways"])


def _service(settings: SettingsDep, session: DBSessionDep) -> WCGatewayService:
    return WCGatewayService(settings=settings, session=session)


@router.get(
    "",
    response_model=WCGatewayListResponse,
    summary="List payment gateways",
)
async def list_gateways(
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> WCGatewayListResponse:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.list_gateways(
            connection_id=connection_id,
            http=http,
        )


@router.get(
    "/cod",
    response_model=CODStatus,
    summary="Get Cash on Delivery status",
    description=(
        "Returns COD availability, enabled state, and actionable warnings."
    ),
)
async def get_cod_status(
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> CODStatus:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.get_cod_status(
            connection_id=connection_id,
            http=http,
        )


@router.put(
    "/cod",
    response_model=WCGateway,
    summary="Update Cash on Delivery settings",
    description=(
        "Update COD fields. Only provided fields are sent. Never disables "
        "or enables other gateways."
    ),
)
async def update_cod(
    payload: CODSettings,
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> WCGateway:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.update_cod(
            connection_id=connection_id,
            payload=payload,
            http=http,
        )


@router.get(
    "/{gateway_id}",
    response_model=WCGateway,
    summary="Get a single gateway",
)
async def get_gateway(
    gateway_id: str,
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> WCGateway:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.get_gateway(
            connection_id=connection_id,
            gateway_id=gateway_id,
            http=http,
        )