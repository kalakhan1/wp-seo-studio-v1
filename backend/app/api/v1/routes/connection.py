"""Connection endpoints: test, save, list, delete, verify, discover."""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.api.deps import DBSessionDep, SettingsDep
from app.core.http_client import SafeHttpClient
from app.schemas.capability import CapabilityReport
from app.schemas.connection import (
    ConnectionListResponse,
    ConnectionResponse,
    ConnectionSaveRequest,
    ConnectionTestRequest,
    ConnectionTestResponse,
)
from app.services.connection_service import ConnectionService

router = APIRouter(prefix="/connection", tags=["connection"])


def _service(settings: SettingsDep, session: DBSessionDep) -> ConnectionService:
    return ConnectionService(settings=settings, session=session)


@router.post(
    "/test",
    response_model=ConnectionTestResponse,
    summary="Test credentials without saving",
    description=(
        "Attempts to authenticate to WordPress with the provided credentials. "
        "Nothing is persisted. Secrets are not logged."
    ),
)
async def test_connection(
    payload: ConnectionTestRequest,
    settings: SettingsDep,
    session: DBSessionDep,
) -> ConnectionTestResponse:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.test_credentials(payload, http=http)


@router.post(
    "",
    response_model=ConnectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a new connection",
    description=(
        "Saves connection metadata in the database and credentials in the "
        "OS keyring. The response never includes secrets."
    ),
)
async def save_connection(
    payload: ConnectionSaveRequest,
    settings: SettingsDep,
    session: DBSessionDep,
) -> ConnectionResponse:
    service = _service(settings, session)
    return await service.save(payload)


@router.get(
    "",
    response_model=ConnectionListResponse,
    summary="List all connections",
)
async def list_connections(
    settings: SettingsDep,
    session: DBSessionDep,
) -> ConnectionListResponse:
    service = _service(settings, session)
    return ConnectionListResponse(connections=await service.list_all())


@router.get(
    "/{connection_id}",
    response_model=ConnectionResponse,
    summary="Get a single connection",
)
async def get_connection(
    connection_id: int,
    settings: SettingsDep,
    session: DBSessionDep,
) -> ConnectionResponse:
    service = _service(settings, session)
    return await service.get(connection_id)


@router.delete(
    "/{connection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete a connection",
    description=(
        "Deletes the metadata and removes associated credentials from the "
        "OS keyring. Best-effort secret cleanup is always attempted."
    ),
)
async def delete_connection(
    connection_id: int,
    settings: SettingsDep,
    session: DBSessionDep,
) -> Response:
    service = _service(settings, session)
    await service.delete(connection_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{connection_id}/verify",
    response_model=ConnectionTestResponse,
    summary="Re-verify a stored connection",
)
async def verify_connection(
    connection_id: int,
    settings: SettingsDep,
    session: DBSessionDep,
) -> ConnectionTestResponse:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.verify(connection_id, http=http)


@router.post(
    "/{connection_id}/discover",
    response_model=CapabilityReport,
    summary="Run capability discovery",
    description=(
        "Probes the site and returns a truthful capability report. "
        "Requires stored WordPress credentials."
    ),
)
async def discover_connection(
    connection_id: int,
    settings: SettingsDep,
    session: DBSessionDep,
) -> CapabilityReport:
    service = _service(settings, session)
    async with SafeHttpClient(settings) as http:
        return await service.discover(connection_id, http=http)