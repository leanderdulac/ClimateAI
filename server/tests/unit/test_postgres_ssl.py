"""Verified Postgres SSL context for the Supabase pooler."""

from __future__ import annotations

import socket
import ssl
import struct
import pytest

from config.database import (
    BUNDLED_SUPABASE_CA_PATH,
    build_postgres_ssl_context,
    resolve_postgres_ssl_root_cert,
)

POOLER_HOST = "aws-1-sa-east-1.pooler.supabase.com"
POOLER_PORT = 6543
POSTGRES_SSL_REQUEST_CODE = 80877103


@pytest.mark.unit
def test_bundled_supabase_ca_is_committed_and_valid():
    assert BUNDLED_SUPABASE_CA_PATH.is_file()
    pem = BUNDLED_SUPABASE_CA_PATH.read_text()
    assert pem.startswith("-----BEGIN CERTIFICATE-----")
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
        names = [
            value
            for rdn in peer.get("subject", ())
            for key, value in rdn
            if key == "commonName"
        ]
        assert any(name.endswith("pooler.supabase.com") for name in names)
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
