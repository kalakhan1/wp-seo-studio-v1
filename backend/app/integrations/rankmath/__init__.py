"""Rank Math integration.

Two responsibilities:
  - Probe what is safely discoverable (Phase 2).
  - Read/write per-post Rank Math meta via the companion plugin (Phase 3).
"""

from app.integrations.rankmath.client import RankMathClient
from app.integrations.rankmath.exceptions import (
    RankMathCompanionMissingError,
    RankMathInactiveError,
    RankMathMetaError,
)
from app.integrations.rankmath.probes import (
    RankMathProbeResult,
    probe_rankmath,
)
from app.integrations.rankmath.types import RankMathMeta

__all__ = [
    "RankMathClient",
    "RankMathMeta",
    "RankMathProbeResult",
    "RankMathCompanionMissingError",
    "RankMathInactiveError",
    "RankMathMetaError",
    "probe_rankmath",
]