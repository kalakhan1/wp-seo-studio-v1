"""Pydantic schemas for API requests and responses.

All wire formats are defined here. Services and routes import from this
package so that request/response shapes stay consistent across the app.
"""

from app.schemas.app_settings import (
    AppSettingsResponse,
    AppSettingsUpdateRequest,
)
from app.schemas.error import ErrorBody, ErrorResponse
from app.schemas.health import (
    ComponentHealthSchema,
    HealthResponse,
)

__all__ = [
    "AppSettingsResponse",
    "AppSettingsUpdateRequest",
    "ComponentHealthSchema",
    "ErrorBody",
    "ErrorResponse",
    "HealthResponse",
]