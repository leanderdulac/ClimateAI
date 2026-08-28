"""PyTorch climate pricing math — no fake weather series for product paths."""

import numpy as np
import pytest


def _real_torch():
    from services import lstm_attention_service as mod

    torch_mod = getattr(mod, "torch", None)
    if torch_mod is None or type(torch_mod).__name__ == "MagicMock":
        return False
    return bool(getattr(mod, "HAS_TORCH", False))


@pytest.mark.unit
def test_torch_device_is_mps_or_cpu():
    from services.lstm_attention_service import select_torch_device

    if not _real_torch():
        pytest.skip("real PyTorch not available in this test process")
    device = select_torch_device()
    assert device is not None
    assert str(device) in {"mps", "cpu"}


@pytest.mark.unit
def test_exceedance_multipliers_scale_with_heavier_tail():
    from services.pytorch_climate_pricing_service import climate_exceedance_multipliers

    rng = np.random.default_rng(0)
    historical = rng.gamma(1.2, 2.0, size=400)
    simulated = historical * 1.4
    out = climate_exceedance_multipliers(historical, simulated, quantile=0.9)
    assert out["frequency_multiplier"] >= 1.0
    assert 0.7 <= out["severity_multiplier"] <= 1.8
    assert out["threshold_mm"] > 0


@pytest.mark.unit
def test_lstm_trains_on_device_without_network():
    from services.lstm_attention_service import LSTMAttentionService

    if not _real_torch():
        pytest.skip("real PyTorch not available in this test process")
    n = 80
    t = list(np.linspace(20, 28, n))
    p = list(np.abs(np.sin(np.linspace(0, 8, n))) * 6)
    pr = list(np.linspace(1010, 1018, n))
    w = list(np.abs(np.cos(np.linspace(0, 6, n))) * 4)
    e = [0.2] * n
    svc = LSTMAttentionService()
    metrics = svc.train_model(t, p, pr, w, e, p, sequence_length=8, epochs=2, batch_size=16)
    assert svc.is_trained
    assert metrics["device"] in {"mps", "cpu"}
    pred = svc.predict(t, p, pr, w, e, sequence_length=8)
    assert len(pred["predictions"]) == 1
    assert np.isfinite(pred["predictions"][0])
