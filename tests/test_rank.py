from running_tuner.models import Candidate, TrackFeatures
from running_tuner.pipeline import rank


def _candidate(bpm, key=None, lastfm_match=0.5, energy=None):
    return Candidate(
        title="Song",
        artist="Artist",
        features=TrackFeatures(bpm=bpm, bpm_source="getsongbpm", key=key, energy=energy),
        lastfm_match=lastfm_match,
    )


def test_filters_out_of_tolerance_candidates():
    reference = TrackFeatures(bpm=120.0, key="C major")
    candidates = [_candidate(bpm=123.0), _candidate(bpm=140.0)]
    results = rank.score_and_filter(reference, candidates, tolerance=4.0)
    assert len(results) == 1
    assert results[0].candidate.features.bpm == 123.0


def test_sorts_closer_bpm_higher():
    reference = TrackFeatures(bpm=120.0)
    candidates = [_candidate(bpm=123.5), _candidate(bpm=120.5)]
    results = rank.score_and_filter(reference, candidates, tolerance=4.0)
    assert results[0].candidate.features.bpm == 120.5
    assert results[1].candidate.features.bpm == 123.5


def test_missing_energy_note_appears():
    reference = TrackFeatures(bpm=120.0)
    candidates = [_candidate(bpm=121.0, energy=None)]
    results = rank.score_and_filter(reference, candidates, tolerance=4.0)
    assert any("energy unavailable" in note for note in results[0].notes)


def test_no_bpm_reference_yields_no_results():
    reference = TrackFeatures(bpm=None)
    candidates = [_candidate(bpm=120.0)]
    results = rank.score_and_filter(reference, candidates, tolerance=4.0)
    assert results == []


def test_key_compatible_candidate_ranks_above_incompatible_at_same_delta():
    reference = TrackFeatures(bpm=120.0, key="C major")
    compatible = _candidate(bpm=121.0, key="G major", lastfm_match=0.5)
    incompatible = _candidate(bpm=119.0, key="F# major", lastfm_match=0.5)
    results = rank.score_and_filter(reference, [incompatible, compatible], tolerance=4.0)
    assert results[0].candidate.features.key == "G major"
