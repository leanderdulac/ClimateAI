#!/usr/bin/env python3
"""
Diagnóstico rápido de conectividade com Supabase.
- Resolve DNS
- Testa porta 5432 (Postgres)
- Testa HTTPS (REST) na URL do projeto

Uso:
  python scripts/check_supabase_connectivity.py

Requer variáveis no .env:
  SUPABASE_URL
  SUPABASE_DB_HOST
  SUPABASE_DB_PORT (opcional, padrão 5432)
  SUPABASE_ANON_KEY (para teste REST)
"""
import os
import socket
import ssl
import http.client
from urllib.parse import urlparse

from dotenv import load_dotenv


def log(status: str, message: str):
    icon = "✅" if status == "ok" else "❌" if status == "fail" else "⚠️"
    print(f"{icon} {message}")


def check_dns(host: str):
    try:
        infos = socket.getaddrinfo(host, None)
        addrs = {info[4][0] for info in infos}
        log("ok", f"DNS {host} -> {', '.join(addrs)}")
        return True
    except Exception as e:
        log("fail", f"DNS {host} falhou: {e}")
        return False


def check_port(host: str, port: int, timeout: float = 5.0):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            log("ok", f"TCP {host}:{port} conectado")
            return True
    except Exception as e:
        log("fail", f"TCP {host}:{port} falhou: {e}")
        return False


def check_https(url: str, apikey: str | None = None, timeout: float = 8.0):
    try:
        parsed = urlparse(url)
        conn = http.client.HTTPSConnection(parsed.netloc, timeout=timeout, context=ssl.create_default_context())
        headers = {"apikey": apikey} if apikey else {}
        # endpoint minimal: OPTIONS /rest/v1/
        conn.request("OPTIONS", "/rest/v1/", headers=headers)
        resp = conn.getresponse()
        log("ok", f"HTTPS {parsed.netloc} resposta {resp.status}")
        conn.close()
        return True
    except Exception as e:
        log("fail", f"HTTPS {url} falhou: {e}")
        return False


def main():
    # Carrega .env local
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"), override=False)

    supabase_url = os.getenv("SUPABASE_URL", "")
    db_host = os.getenv("SUPABASE_DB_HOST", "")
    db_port = int(os.getenv("SUPABASE_DB_PORT", "5432"))
    anon_key = os.getenv("SUPABASE_ANON_KEY")

    if not supabase_url or not db_host:
        log("fail", "Defina SUPABASE_URL e SUPABASE_DB_HOST no .env")
        return

    print("\n=== Supabase Connectivity Check ===")
    print(f"URL:  {supabase_url}")
    print(f"DB:   {db_host}:{db_port}")

    dns_ok = check_dns(db_host)
    port_ok = check_port(db_host, db_port) if dns_ok else False
    https_ok = check_https(supabase_url, anon_key)

    print("\nResumo:")
    print(f"  DNS:   {'OK' if dns_ok else 'FAIL'}")
    print(f"  TCP:   {'OK' if port_ok else 'FAIL'}")
    print(f"  HTTPS: {'OK' if https_ok else 'FAIL'}")

    if not (dns_ok and port_ok):
        print("\nSugestões:")
        print("- Verifique firewall/VPN bloqueando saídas para 5432.")
        print("- Se DNS falhar, tente resolver pelo IP e setar SUPABASE_DB_HOST=<ip>.")
        print("- Confirme que a rede permite tráfego outbound.")


if __name__ == "__main__":
    main()
