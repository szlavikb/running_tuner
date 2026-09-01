from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

Source = Literal["local", "spotify", "youtube"]
FeatureSource = Literal["librosa", "getsongbpm", None]


@dataclass
class TrackRef:
    title: str
    artist: str
    source: Source
    source_uri: str
    album: Optional[str] = None
    local_audio_path: Optional[Path] = None


@dataclass
class TrackFeatures:
    bpm: Optional[float] = None
    bpm_source: FeatureSource = None
    key: Optional[str] = None
    key_source: FeatureSource = None
    energy: Optional[float] = None
    energy_source: FeatureSource = None


@dataclass
class ReferenceTrack:
    ref: TrackRef
    features: TrackFeatures


@dataclass
class Candidate:
    title: str
    artist: str
    features: TrackFeatures
    lastfm_match: Optional[float] = None
    spotify_uri: Optional[str] = None


@dataclass
class MatchResult:
    candidate: Candidate
    bpm_delta: Optional[float]
    key_compatible: Optional[bool]
    score: float
    notes: list[str] = field(default_factory=list)
