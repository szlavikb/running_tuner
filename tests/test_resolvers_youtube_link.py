from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from running_tuner.audio.ytdlp_fetch import FetchedAudio
from running_tuner.resolvers import youtube_link


@contextmanager
def _fake_fetch_audio(url):
    yield FetchedAudio(path=Path("/tmp/fake.wav"), title="Fake Title", uploader="Fake Uploader")


def test_resolve_builds_track_ref_from_fetched_audio():
    with patch("running_tuner.resolvers.youtube_link.fetch_audio", _fake_fetch_audio):
        with youtube_link.resolve("https://youtube.com/watch?v=xyz") as ref:
            assert ref.title == "Fake Title"
            assert ref.artist == "Fake Uploader"
            assert ref.source == "youtube"
            assert ref.local_audio_path == Path("/tmp/fake.wav")


def test_resolve_falls_back_to_url_when_no_title():
    @contextmanager
    def fake_fetch(url):
        yield FetchedAudio(path=Path("/tmp/fake.wav"), title=None, uploader=None)

    with patch("running_tuner.resolvers.youtube_link.fetch_audio", fake_fetch):
        with youtube_link.resolve("https://youtube.com/watch?v=xyz") as ref:
            assert ref.title == "https://youtube.com/watch?v=xyz"
            assert ref.artist == ""
