import numpy as np
import pytest
import soundfile as sf

from running_tuner.audio import analysis


def _make_click_track(bpm: float, duration_s: float = 8.0, sr: int = 22050) -> np.ndarray:
    n_samples = int(duration_s * sr)
    y = np.zeros(n_samples, dtype=np.float32)
    beat_interval = 60.0 / bpm
    click_len = int(0.02 * sr)
    t_click = np.linspace(0, 0.02, click_len, endpoint=False)
    click = (np.sin(2 * np.pi * 1000 * t_click) * np.exp(-t_click * 200)).astype(np.float32)

    beat_time = 0.0
    while beat_time < duration_s:
        start = int(beat_time * sr)
        end = min(start + click_len, n_samples)
        y[start:end] += click[: end - start]
        beat_time += beat_interval
    return y


@pytest.mark.slow
def test_analyze_detects_120_bpm_click_track(tmp_path):
    y = _make_click_track(bpm=120.0)
    path = tmp_path / "click_120bpm.wav"
    sf.write(str(path), y, 22050)

    features = analysis.analyze(path)

    assert features.bpm is not None
    assert abs(features.bpm - 120.0) <= 3.0
    assert features.bpm_source == "librosa"
    assert features.key_source == "librosa"
    assert features.energy_source == "librosa"


def test_estimate_key_returns_a_valid_label():
    y = _make_click_track(bpm=100.0, duration_s=2.0)
    key = analysis.estimate_key(y, 22050)
    note, quality = key.split(" ")
    assert quality in ("major", "minor")
