from __future__ import annotations

from running_tuner.audio import analysis
from running_tuner.audio.ytdlp_fetch import fetch_audio, search_youtube_url
from running_tuner.clients.getsongbpm_client import GetSongBPMClient
from running_tuner.clients.spotify_client import SpotifyClient
from running_tuner.errors import ResolutionError
from running_tuner.models import Candidate, TrackFeatures


def deep_analyze_candidate(artist: str, title: str) -> TrackFeatures:
    """Slow, opt-in fallback: search YouTube, download temp audio, run librosa."""
    query = search_youtube_url(artist, title)
    try:
        with fetch_audio(query) as fetched:
            return analysis.analyze(fetched.path)
    except ResolutionError:
        return TrackFeatures()


def build_candidates(
    raw_candidates: list[tuple[str, str, float]],
    getsongbpm_client: GetSongBPMClient,
    spotify_client: SpotifyClient,
    deep: bool,
    deep_max: int,
) -> list[Candidate]:
    candidates: list[Candidate] = []
    deep_used = 0

    for artist, title, lastfm_score in raw_candidates:
        features = getsongbpm_client.lookup(artist, title)

        if features.bpm is None and deep and deep_used < deep_max:
            deep_used += 1
            features = deep_analyze_candidate(artist, title)

        if features.bpm is None:
            continue

        spotify_uri = spotify_client.search_track(artist, title)
        candidates.append(
            Candidate(
                title=title,
                artist=artist,
                features=features,
                lastfm_match=lastfm_score,
                spotify_uri=spotify_uri,
            )
        )

    return candidates
