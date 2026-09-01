from __future__ import annotations

import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, NamedTuple, Optional

import yt_dlp

from running_tuner.errors import ResolutionError


class FetchedAudio(NamedTuple):
    path: Path
    title: Optional[str]
    uploader: Optional[str]


@contextmanager
def fetch_audio(youtube_url: str) -> Iterator[FetchedAudio]:
    """Downloads a YouTube URL's audio to a temp file, yields it, deletes it on exit.

    Requires ffmpeg on PATH for the extraction postprocessor.
    """
    with tempfile.TemporaryDirectory(prefix="running_tuner_yt_") as tmpdir:
        out_template = str(Path(tmpdir) / "%(id)s.%(ext)s")
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": out_template,
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "wav"}],
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
        except yt_dlp.utils.DownloadError as exc:
            raise ResolutionError(f"Could not download audio from '{youtube_url}': {exc}") from exc

        wav_files = list(Path(tmpdir).glob("*.wav"))
        if not wav_files:
            raise ResolutionError(
                f"Audio extraction produced no output for '{youtube_url}' "
                "(is ffmpeg installed and on PATH?)"
            )
        yield FetchedAudio(path=wav_files[0], title=info.get("title"), uploader=info.get("uploader"))


def search_youtube_url(artist: str, title: str) -> str:
    """Returns a yt-dlp search query string that resolves the top match, without downloading."""
    return f"ytsearch1:{artist} {title}"
