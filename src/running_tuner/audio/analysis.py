"""Local audio feature extraction via librosa: tempo, key, energy.

Used both for genuine local files and for temp files fetched from YouTube.
"""

from __future__ import annotations

import logging
from pathlib import Path

import librosa
import numpy as np

from running_tuner.models import TrackFeatures

logger = logging.getLogger(__name__)

# Krumhansl-Kessler key profiles (major starts on C, minor starts on A-relative-to-C == C).
_MAJOR_PROFILE = np.array(
    [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
)
_MINOR_PROFILE = np.array(
    [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
)
_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

_RUNNING_CADENCE_RANGE = (100.0, 180.0)


def estimate_key(y: np.ndarray, sr: int) -> str:
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_mean = chroma.mean(axis=1)

    best_score = -np.inf
    best_label = "C major"
    for shift in range(12):
        major_corr = np.corrcoef(np.roll(_MAJOR_PROFILE, shift), chroma_mean)[0, 1]
        minor_corr = np.corrcoef(np.roll(_MINOR_PROFILE, shift), chroma_mean)[0, 1]
        note = _NOTE_NAMES[shift]
        if major_corr > best_score:
            best_score, best_label = major_corr, f"{note} major"
        if minor_corr > best_score:
            best_score, best_label = minor_corr, f"{note} minor"
    return best_label


def _resolve_octave_ambiguity(tempo: float) -> tuple[float, bool]:
    """Prefer the tempo candidate (tempo, 2x, 0.5x) closest to a plausible running cadence."""
    low, high = _RUNNING_CADENCE_RANGE
    if low <= tempo <= high:
        return tempo, False
    candidates = [tempo, tempo * 2, tempo / 2]
    in_range = [c for c in candidates if low <= c <= high]
    if in_range:
        return min(in_range, key=lambda c: abs(c - tempo)), True
    return tempo, False


def analyze(path: Path) -> TrackFeatures:
    y, sr = librosa.load(str(path), sr=22050, mono=True)

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr, units="time")
    tempo = float(tempo[0]) if hasattr(tempo, "__len__") else float(tempo)
    tempo, octave_corrected = _resolve_octave_ambiguity(tempo)
    if octave_corrected:
        logger.info("Octave-corrected tempo for %s to %.1f BPM (running-cadence range)", path, tempo)

    key = estimate_key(y, sr)
    energy = float(librosa.feature.rms(y=y).mean())

    return TrackFeatures(
        bpm=round(tempo, 1),
        bpm_source="librosa",
        key=key,
        key_source="librosa",
        energy=energy,
        energy_source="librosa",
    )
