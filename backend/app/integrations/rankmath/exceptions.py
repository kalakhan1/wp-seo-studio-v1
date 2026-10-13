"""Rank Math-specific exceptions."""

from __future__ import annotations

from app.core.exceptions import AppError


class RankMathError(AppError):
    """Base class for Rank Math integration errors."""

    code = "RANKMATH_ERROR"
    http_status = 502


class RankMathCompanionMissingError(RankMathError):
    """The companion plugin is not installed or not active."""

    code = "RANKMATH_COMPANION_MISSING"
    http_status = 409


class RankMathInactiveError(RankMathError):
    """The companion plugin is present but Rank Math is not active."""

    code = "RANKMATH_INACTIVE"
    http_status = 409


class RankMathMetaError(RankMathError):
    """An error occurred reading or writing Rank Math meta."""

    code = "RANKMATH_META_ERROR"
    http_status = 502