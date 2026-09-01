import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yt_dlp

from running_tuner.audio import ytdlp_fetch
from running_tuner.errors import ResolutionError


class _CapturingTemporaryDirectory(tempfile.TemporaryDirectory):
    """Same as tempfile.TemporaryDirectory, but stashes the created path for assertions."""

    captured: list = []

    def __enter__(self):
        path = super().__enter__()
        _CapturingTemporaryDirectory.captured.append(Path(path))
        return path


def _fake_extract_info_writing_wav(self, url, download=True):
    out_dir = _CapturingTemporaryDirectory.captured[-1]
    (out_dir / "abc.wav").write_bytes(b"fake wav data")
    return {"title": "Song", "uploader": "Uploader"}


def test_fetch_audio_cleans_up_temp_dir_after_success():
    _CapturingTemporaryDirectory.captured.clear()
    with patch.object(yt_dlp.YoutubeDL, "extract_info", _fake_extract_info_writing_wav), patch.object(
        tempfile, "TemporaryDirectory", _CapturingTemporaryDirectory
    ):
        with ytdlp_fetch.fetch_audio("https://youtube.com/watch?v=abc") as fetched:
            assert fetched.path.exists()
            assert fetched.title == "Song"

    assert not _CapturingTemporaryDirectory.captured[-1].exists()


def test_fetch_audio_cleans_up_temp_dir_even_when_consumer_raises():
    _CapturingTemporaryDirectory.captured.clear()
    with patch.object(yt_dlp.YoutubeDL, "extract_info", _fake_extract_info_writing_wav), patch.object(
        tempfile, "TemporaryDirectory", _CapturingTemporaryDirectory
    ):
        with pytest.raises(RuntimeError):
            with ytdlp_fetch.fetch_audio("https://youtube.com/watch?v=abc"):
                raise RuntimeError("boom")

    assert not _CapturingTemporaryDirectory.captured[-1].exists()


def test_fetch_audio_wraps_download_error():
    def fake_extract_info(self, url, download=True):
        raise yt_dlp.utils.DownloadError("video unavailable")

    with patch.object(yt_dlp.YoutubeDL, "extract_info", fake_extract_info):
        with pytest.raises(ResolutionError):
            with ytdlp_fetch.fetch_audio("https://youtube.com/watch?v=gone"):
                pass


def test_fetch_audio_raises_when_no_wav_produced():
    def fake_extract_info(self, url, download=True):
        return {"title": "Song", "uploader": "Uploader"}

    with patch.object(yt_dlp.YoutubeDL, "extract_info", fake_extract_info):
        with pytest.raises(ResolutionError):
            with ytdlp_fetch.fetch_audio("https://youtube.com/watch?v=abc"):
                pass
