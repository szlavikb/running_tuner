from __future__ import annotations

from pathlib import Path

import mutagen

from running_tuner.errors import ResolutionError
from running_tuner.models import TrackRef

SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a", ".ogg"}


def resolve(path_str: str) -> TrackRef:
    path = Path(path_str)
    if not path.is_file():
        raise ResolutionError(f"Local audio file not found: {path}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ResolutionError(
            f"Unsupported audio file extension '{path.suffix}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    title, artist = path.stem, ""
    try:
        tags = mutagen.File(path, easy=True)
        if tags:
            title = (tags.get("title") or [title])[0]
            artist = (tags.get("artist") or [""])[0]
    except mutagen.MutagenError:
        pass

    return TrackRef(
        title=title,
        artist=artist,
        source="local",
        source_uri=str(path),
        local_audio_path=path,
    )
