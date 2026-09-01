from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from running_tuner.audio.ytdlp_fetch import fetch_audio
from running_tuner.models import TrackRef


@contextmanager
def resolve(url: str) -> Iterator[TrackRef]:
    """Yields a TrackRef whose local_audio_path is only valid inside this `with` block —
    the underlying temp file is deleted on exit.
    """
    with fetch_audio(url) as fetched:
        title = fetched.title or url
        artist = fetched.uploader or ""
        yield TrackRef(
            title=title,
            artist=artist,
            source="youtube",
            source_uri=url,
            local_audio_path=fetched.path,
        )
