"""Verified Postgres SSL context for the Supabase pooler."""

from __future__ import annotations

import socket
import ssl
import struct
from urllib.parse import urlparse

import pytest

from config.database import (
    BUNDLED_SUPABASE_CA_PATH,
    build_postgres_ssl_context,
    resolve_postgres_ssl_root_cert,
)

POOLER_HOST = "aws-1-sa-east-1.pooler.supabase.com"
POOLER_PORT = 6543
POSTGRES_SSL_REQUEST_CODE = 80877103
_POOLER_DNS_SUFFIX = "pooler.supabase.com"


def _parsed_hostname(value: str) -> str | None:
    """Hostname via urlparse so suffix checks cannot treat a URL path as a host."""
    parsed = urlparse(value if "://" in value else f"//{value}")
    host = parsed.hostname
    return host.rstrip(".").lower() if host else None


def _hostname_equals_pooler(name: str) -> bool:
    """Exact pooler host, or a subdomain of pooler.supabase.com (leading-dot suffix)."""
    host = _parsed_hostname(name)
    if host is None:
        return False
    return host == "pooler.supabase.com" or host.endswith(".pooler.supabase.com")


def _peer_dns_names(peer: dict) -> list[str]:
    names = [
        value
        for rdn in peer.get("subject", ())
        for key, value in rdn
        if key == "commonName"
    ]
    names.extend(
        san_value
        for san_type, san_value in peer.get("subjectAltName", ())
        if san_type == "DNS"
    )
    return names


@pytest.mark.unit
def test_pooler_hostname_equality_rejects_suffix_bypass():
    assert _hostname_equals_pooler(POOLER_HOST)
    assert _hostname_equals_pooler(_POOLER_DNS_SUFFIX)
    assert _hostname_equals_pooler(f"https://{POOLER_HOST}/postgres")
    assert not _hostname_equals_pooler("evilpooler.supabase.com")
    assert not _hostname_equals_pooler("pooler.supabase.com.evil.com")
    assert not _hostname_equals_pooler(f"https://evil.example/{POOLER_HOST}")


@pytest.mark.unit
def test_bundled_supabase_ca_is_committed_and_valid():
    assert BUNDLED_SUPABASE_CA_PATH.is_file()
    pem = BUNDLED_SUPABASE_CA_PATH.read_text()
    pem_lines = pem.splitlines()
    assert "-----BEGIN CERTIFICATE-----" in pem_lines
    assert "-----END CERTIFICATE-----" in pem_lines
    ctx = ssl.create_default_context()
    ctx.load_verify_locations(cafile=str(BUNDLED_SUPABASE_CA_PATH))
    common_names = [
        value
        for cert in ctx.get_ca_certs()
        for rdn in cert.get("subject", ())
        for key, value in rdn
        if key == "commonName"
    ]
    assert "Supabase Root 2021 CA" in common_names


@pytest.mark.unit
def test_resolve_root_cert_defaults_to_bundled_file():
    cafile, cadata = resolve_postgres_ssl_root_cert()
    assert cadata is None
    assert cafile == str(BUNDLED_SUPABASE_CA_PATH)


@pytest.mark.unit
def test_verified_context_keeps_hostname_and_cert_checks():
    ctx = build_postgres_ssl_context(
        is_localhost=False, environment="production", insecure_override=False
    )
    assert ctx is not None
    assert ctx.verify_mode == ssl.CERT_REQUIRED
    assert ctx.check_hostname is True


def _postgres_starttls(host: str, port: int, timeout: float = 8.0) -> socket.socket:
    raw = socket.create_connection((host, port), timeout=timeout)
    raw.sendall(struct.pack("!II", 8, POSTGRES_SSL_REQUEST_CODE))
    raw.settimeout(timeout)
    response = raw.recv(1)
    if response != b"S":
        raw.close()
        raise OSError(f"Postgres server refused SSL: {response!r}")
    return raw


@pytest.mark.unit
def test_bundled_ca_validates_supabase_pooler_chain():
    """Live verify-full against the production pooler host when reachable."""
    ctx = build_postgres_ssl_context(
        is_localhost=False, environment="production", insecure_override=False
    )
    assert ctx is not None
    try:
        raw = _postgres_starttls(POOLER_HOST, POOLER_PORT)
    except OSError as exc:
        pytest.skip(f"pooler unreachable: {exc}")

    try:
        tls = ctx.wrap_socket(raw, server_hostname=POOLER_HOST)
    except ssl.SSLCertVerificationError:
        raw.close()
        raise
    try:
        peer = tls.getpeercert()
        assert peer is not None
        names = _peer_dns_names(peer)
        assert any(_hostname_equals_pooler(name) for name in names)
    finally:
        tls.close()


@pytest.mark.unit
def test_system_cas_alone_reject_pooler_chain():
    """Reproduce the production failure: default context cannot verify Supabase."""
    ctx = ssl.create_default_context()
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.check_hostname = True
    try:
        raw = _postgres_starttls(POOLER_HOST, POOLER_PORT)
    except OSError as exc:
        pytest.skip(f"pooler unreachable: {exc}")

    with pytest.raises(ssl.SSLCertVerificationError, match="self-signed certificate"):
        try:
            tls = ctx.wrap_socket(raw, server_hostname=POOLER_HOST)
        except ssl.SSLCertVerificationError:
            raw.close()
            raise
        else:
            tls.close()
