from unittest.mock import MagicMock

from running_tuner.models import TrackFeatures
from running_tuner.pipeline import enrich


def _client_returning(bpm):
    client = MagicMock()
    client.lookup.return_value = TrackFeatures(bpm=bpm, bpm_source="getsongbpm")
    return client


def test_build_candidates_drops_ones_without_bpm():
    getsongbpm = _client_returning(None)
    spotify = MagicMock()
    spotify.search_track.return_value = None

    candidates = enrich.build_candidates(
        [("Artist", "Song", 0.5)], getsongbpm, spotify, deep=False, deep_max=5
    )
    assert candidates == []


def test_build_candidates_keeps_ones_with_bpm():
    getsongbpm = _client_returning(120.0)
    spotify = MagicMock()
    spotify.search_track.return_value = "spotify:track:xyz"

    candidates = enrich.build_candidates(
        [("Artist", "Song", 0.5)], getsongbpm, spotify, deep=False, deep_max=5
    )
    assert len(candidates) == 1
    assert candidates[0].features.bpm == 120.0
    assert candidates[0].spotify_uri == "spotify:track:xyz"


def test_build_candidates_uses_deep_fallback_when_enabled():
    getsongbpm = _client_returning(None)
    spotify = MagicMock()
    spotify.search_track.return_value = None

    import running_tuner.pipeline.enrich as enrich_module

    original = enrich_module.deep_analyze_candidate
    enrich_module.deep_analyze_candidate = lambda artist, title: TrackFeatures(bpm=140.0, bpm_source="librosa")
    try:
        candidates = enrich.build_candidates(
            [("Artist", "Song", 0.5)], getsongbpm, spotify, deep=True, deep_max=5
        )
    finally:
        enrich_module.deep_analyze_candidate = original

    assert len(candidates) == 1
    assert candidates[0].features.bpm == 140.0


def test_build_candidates_respects_deep_max():
    getsongbpm = _client_returning(None)
    spotify = MagicMock()
    spotify.search_track.return_value = None

    import running_tuner.pipeline.enrich as enrich_module

    call_count = {"n": 0}

    def fake_deep(artist, title):
        call_count["n"] += 1
        return TrackFeatures(bpm=140.0, bpm_source="librosa")

    original = enrich_module.deep_analyze_candidate
    enrich_module.deep_analyze_candidate = fake_deep
    try:
        raw = [("Artist", f"Song {i}", 0.5) for i in range(5)]
        enrich.build_candidates(raw, getsongbpm, spotify, deep=True, deep_max=2)
    finally:
        enrich_module.deep_analyze_candidate = original

    assert call_count["n"] == 2
