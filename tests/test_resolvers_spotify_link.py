from unittest.mock import MagicMock

import pytest

from running_tuner.errors import ResolutionError
from running_tuner.resolvers import spotify_link


def test_resolve_extracts_id_and_calls_spotify():
    mock_client = MagicMock()
    mock_client.get_track.return_value = {"title": "Song", "artist": "Artist", "album": "Album"}

    ref = spotify_link.resolve("https://open.spotify.com/track/abc123?si=xyz", mock_client)

    mock_client.get_track.assert_called_once_with("abc123")
    assert ref.title == "Song"
    assert ref.artist == "Artist"
    assert ref.source == "spotify"
    assert ref.local_audio_path is None


def test_resolve_accepts_uri_form():
    mock_client = MagicMock()
    mock_client.get_track.return_value = {"title": "Song", "artist": "Artist", "album": None}

    spotify_link.resolve("spotify:track:abc123", mock_client)

    mock_client.get_track.assert_called_once_with("abc123")


def test_resolve_invalid_url_raises():
    with pytest.raises(ResolutionError):
        spotify_link.resolve("https://example.com/not-spotify", MagicMock())
