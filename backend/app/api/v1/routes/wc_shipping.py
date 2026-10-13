"""WooCommerce shipping zone endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, Response, status

from app.api.deps import DBSessionDep, SettingsDep
from app.core.http_client import SafeHttpClient
from app.schemas.wc_shipping import (
    AvailableMethodsResponse,
    MethodAddRequest,
    MethodUpdateRequest,
    WCShippingMethod,
    WCShippingZoneDetail,
    ZoneCreateRequest,
    ZoneListResponse,
    ZoneLocationsUpdateRequest,
    ZoneUpdateRequest,
)
from app.services.wc_shipping_service import WCShippingService

router = APIRouter(prefix="/wc/shipping", tags=["wc-shipping"])


def _service(settings: SettingsDep, session: DBSessionDep) -> WCShippingService:
    return WCShippingService(settings=settings, session=session)


@router.get(
    "/zones",
    response_model=ZoneListResponse,
    summary="List shipping zones",
)
async def list_zones(
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> ZoneListResponse:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.list_zones(connection_id=connection_id, http=http)


@router.post(
    "/zones",
    response_model=WCShippingZoneDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create a shipping zone",
)
async def create_zone(
    payload: ZoneCreateRequest,
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> WCShippingZoneDetail:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.create_zone(
            connection_id=connection_id, payload=payload, http=http
        )


@router.get(
    "/zones/{zone_id}",
    response_model=WCShippingZoneDetail,
    summary="Get a shipping zone with locations and methods",
)
async def get_zone(
    zone_id: int,
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> WCShippingZoneDetail:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.get_zone_detail(
            connection_id=connection_id, zone_id=zone_id, http=http
        )


@router.put(
    "/zones/{zone_id}",
    response_model=WCShippingZoneDetail,
    summary="Update a shipping zone",
)
async def update_zone(
    zone_id: int,
    payload: ZoneUpdateRequest,
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> WCShippingZoneDetail:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.update_zone(
            connection_id=connection_id,
            zone_id=zone_id,
            payload=payload,
            http=http,
        )


@router.delete(
    "/zones/{zone_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete a shipping zone",
)
async def delete_zone(
    zone_id: int,
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> Response:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        await service.delete_zone(
            connection_id=connection_id, zone_id=zone_id, http=http
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/zones/{zone_id}/locations",
    response_model=WCShippingZoneDetail,
    summary="Replace zone locations",
)
async def update_zone_locations(
    zone_id: int,
    payload: ZoneLocationsUpdateRequest,
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> WCShippingZoneDetail:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.set_zone_locations(
            connection_id=connection_id,
            zone_id=zone_id,
            locations=payload.locations,
            http=http,
        )


@router.post(
    "/zones/{zone_id}/methods",
    response_model=WCShippingMethod,
    status_code=status.HTTP_201_CREATED,
    summary="Add a method to a zone",
)
async def add_method(
    zone_id: int,
    payload: MethodAddRequest,
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> WCShippingMethod:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.add_method(
            connection_id=connection_id,
            zone_id=zone_id,
            payload=payload,
            http=http,
        )


@router.put(
    "/zones/{zone_id}/methods/{instance_id}",
    response_model=WCShippingMethod,
    summary="Update a method in a zone",
)
async def update_method(
    zone_id: int,
    instance_id: int,
    payload: MethodUpdateRequest,
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> WCShippingMethod:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.update_method(
            connection_id=connection_id,
            zone_id=zone_id,
            instance_id=instance_id,
            payload=payload,
            http=http,
        )


@router.delete(
    "/zones/{zone_id}/methods/{instance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete a method from a zone",
)
async def delete_method(
    zone_id: int,
    instance_id: int,
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> Response:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        await service.delete_method(
            connection_id=connection_id,
            zone_id=zone_id,
            instance_id=instance_id,
            http=http,
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/methods",
    response_model=AvailableMethodsResponse,
    summary="List available shipping method types",
)
async def list_available_methods(
    settings: SettingsDep,
    session: DBSessionDep,
    connection_id: int = Query(..., ge=1),
) -> AvailableMethodsResponse:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.list_available_methods(
            connection_id=connection_id, http=http
        )