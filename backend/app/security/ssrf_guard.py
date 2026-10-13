"""SSRF guard.

Blocks requests to private, loopback, link-local, multicast, reserved, and
unspecified IP addresses, and disallows non-HTTP(S) schemes. Redirects must
be re-validated by the caller (the HTTP client does this).
"""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from urllib.parse import urlparse

from app.config.constants import BLOCKED_HOSTNAMES, BLOCKED_SCHEMES
from app.core.exceptions import SSRFBlockedError


def _is_blocked_ip(ip_str: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return True  # unparseable => treat as unsafe

    # IPv4-mapped IPv6 (e.g. ::ffff:127.0.0.1)
    if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped is not None:
        addr = addr.ipv4_mapped

    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
    )


def _resolve_ips(host: str) -> list[str]:
    """Resolve a hostname to a list of IP strings. Blocking."""
    infos = socket.getaddrinfo(host, None)
    ips: list[str] = []
    for info in infos:
        sockaddr = info[4]
        if isinstance(sockaddr, tuple) and len(sockaddr) >= 1:
            ips.append(str(sockaddr[0]))
    return ips


async def _resolve_ips_async(host: str) -> list[str]:
    """Async wrapper around getaddrinfo."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _resolve_ips, host)


def _validate_url_shape(url: str) -> tuple[str, str]:
    """Return (scheme, hostname). Raise SSRFBlockedError if unsafe shape."""
    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()
    host = (parsed.hostname or "").lower()

    if scheme not in ("http", "https"):
        raise SSRFBlockedError(
            "Only HTTP and HTTPS URLs are allowed",
            details={"scheme": scheme, "url": url},
        )
    if scheme in BLOCKED_SCHEMES:
        raise SSRFBlockedError(
            "Scheme is not allowed",
            details={"scheme": scheme},
        )
    if not host:
        raise SSRFBlockedError("URL has no hostname", details={"url": url})
    if host in BLOCKED_HOSTNAMES:
        raise SSRFBlockedError(
            "Hostname is blocked",
            details={"hostname": host},
        )
    return scheme, host


def is_safe_url(url: str, *, allow_private: bool = False) -> bool:
    """Synchronous check. Returns True if URL passes all SSRF checks.

    Note: resolves DNS synchronously. Prefer `is_safe_url_async` in async code.
    """
    if allow_private:
        try:
            _validate_url_shape(url)
            return True
        except SSRFBlockedError:
            return False
    try:
        _, host = _validate_url_shape(url)
        # If host is a literal IP, check directly; otherwise resolve.
        try:
            ipaddress.ip_address(host)
            return not _is_blocked_ip(host)
        except ValueError:
            pass
        ips = _resolve_ips(host)
        if not ips:
            return False
        return not any(_is_blocked_ip(ip) for ip in ips)
    except SSRFBlockedError:
        return False
    except (socket.gaierror, OSError):
        return False


async def is_safe_url_async(url: str, *, allow_private: bool = False) -> bool:
    """Async check. Returns True if URL passes all SSRF checks."""
    if allow_private:
        try:
            _validate_url_shape(url)
            return True
        except SSRFBlockedError:
            return False
    try:
        _, host = _validate_url_shape(url)
        try:
            ipaddress.ip_address(host)
            return not _is_blocked_ip(host)
        except ValueError:
            pass
        ips = await _resolve_ips_async(host)
        if not ips:
            return False
        return not any(_is_blocked_ip(ip) for ip in ips)
    except SSRFBlockedError:
        return False
    except (socket.gaierror, OSError):
        return False


async def assert_safe_url_async(url: str, *, allow_private: bool = False) -> None:
    """Raise SSRFBlockedError if URL is unsafe. Async version."""
    if allow_private:
        _validate_url_shape(url)
        return

    _, host = _validate_url_shape(url)

    # Literal IP fast path.
    try:
        ipaddress.ip_address(host)
        if _is_blocked_ip(host):
            raise SSRFBlockedError(
                "Target IP is private, loopback, or reserved",
                details={"url": url, "host": host},
            )
        return
    except ValueError:
        pass

    ips = await _resolve_ips_async(host)
    if not ips:
        raise SSRFBlockedError(
            "Could not resolve hostname",
            details={"url": url, "host": host},
        )
    for ip in ips:
        if _is_blocked_ip(ip):
            raise SSRFBlockedError(
                "Target resolves to a private, loopback, or reserved address",
                details={"url": url, "host": host, "resolved_ip": ip},
            )