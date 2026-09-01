from __future__ import annotations

from running_tuner import camelot
from running_tuner.models import Candidate, MatchResult, TrackFeatures


def score_and_filter(
    reference: TrackFeatures, candidates: list[Candidate], tolerance: float
) -> list[MatchResult]:
    results: list[MatchResult] = []

    for candidate in candidates:
        if reference.bpm is None or candidate.features.bpm is None:
            continue
        delta = abs(candidate.features.bpm - reference.bpm)
        if delta > tolerance:
            continue

        key_compat = None
        if reference.key and candidate.features.key:
            key_compat = camelot.is_compatible(reference.key, candidate.features.key)

        bpm_score = 1.0 - (delta / max(tolerance, 0.01))
        key_bonus = 0.15 if key_compat else 0.0
        lastfm_weight = (candidate.lastfm_match or 0.0) * 0.1
        score = bpm_score + key_bonus + lastfm_weight

        notes = []
        if candidate.features.energy is None:
            notes.append("energy unavailable (GetSongBPM has no energy field; rerun with --deep for energy)")

        results.append(
            MatchResult(
                candidate=candidate,
                bpm_delta=delta,
                key_compatible=key_compat,
                score=score,
                notes=notes,
            )
        )

    return sorted(results, key=lambda r: r.score, reverse=True)
