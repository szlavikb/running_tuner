from __future__ import annotations

import re

import click

from running_tuner.clients.spotify_client import SpotifyClient
from running_tuner.errors import ResolutionError
from running_tuner.models import TrackRef

_TRACK_ID_PATTERNS = (
    re.compile(r"open\.spotify\.com/track/([A-Za-z0-9]+)"),
    re.compile(r"spotify:track:([A-Za-z0-9]+)"),
)


def _extract_track_id(url: str) -> str:
    for pattern in _TRACK_ID_PATTERNS:
        match = pattern.search(url)
        if match:
            return match.group(1)
    raise ResolutionError(f"Could not parse a Spotify track id out of: {url}")


def resolve(url: str, spotify_client: SpotifyClient) -> TrackRef:
    click.echo(f"🎵  spotify_link.resolve(): parsing url={url!r}", err=True)
    track_id = _extract_track_id(url)
    click.echo(f"🎵  spotify_link.resolve(): track_id={track_id!r} -> spotify_client.get_track()", err=True)
    info = spotify_client.get_track(track_id)
    click.echo(f"🎵  spotify_link.resolve(): got {info['artist']!r} - {info['title']!r}", err=True)
    return TrackRef(
        title=info["title"],
        artist=info["artist"],
        album=info.get("album"),
        source="spotify",
        source_uri=f"spotify:track:{track_id}",
        local_audio_path=None,
    )
