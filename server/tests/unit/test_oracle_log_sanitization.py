"""Log-injection / clear-text helpers used by the Hathor climate oracle."""

from blockchain.hathor.oracle_service import _safe_log_float, _safe_log_token


def test_safe_log_token_strips_crlf_and_nul():
    assert _safe_log_token("precip\r\nINFO forged") == "precipINFO forged"
    assert _safe_log_token("ok\x00secret") == "oksecret"


def test_safe_log_token_truncates():
    assert _safe_log_token("abcdefghij", max_len=4) == "abcd…"


def test_safe_log_float_casts_and_rounds():
    assert _safe_log_float("-22.9068123") == "-22.9068"
    assert _safe_log_float("1.2345\r\n", digits=2) == "1.23"
