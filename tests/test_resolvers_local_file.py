import pytest

from running_tuner.errors import ResolutionError
from running_tuner.resolvers import local_file


def test_resolve_missing_file_raises(tmp_path):
    with pytest.raises(ResolutionError):
        local_file.resolve(str(tmp_path / "missing.mp3"))


def test_resolve_unsupported_extension_raises(tmp_path):
    path = tmp_path / "song.txt"
    path.write_text("not audio")
    with pytest.raises(ResolutionError):
        local_file.resolve(str(path))


def test_resolve_falls_back_to_filename_when_no_tags(tmp_path):
    path = tmp_path / "My Song.wav"
    path.write_bytes(b"RIFF....WAVEfmt ")  # not a real wav, just needs to exist with the right extension
    ref = local_file.resolve(str(path))
    assert ref.title == "My Song"
    assert ref.source == "local"
    assert ref.local_audio_path == path
