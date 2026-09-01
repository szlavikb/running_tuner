import responses

from running_tuner.clients.spotify_client import SpotifyClient

TOKEN_URL = "https://accounts.spotify.com/api/token"
TRACK_URL = "https://api.spotify.com/v1/tracks/abc123"
SEARCH_URL = "https://api.spotify.com/v1/search"


def _mock_token():
    responses.add(responses.POST, TOKEN_URL, json={"access_token": "tok1", "expires_in": 3600}, status=200)


@responses.activate
def test_get_track_success():
    _mock_token()
    responses.add(
        responses.GET,
        TRACK_URL,
        json={"name": "Song", "artists": [{"name": "Artist"}], "album": {"name": "Album"}},
        status=200,
    )
    client = SpotifyClient("id", "secret")
    result = client.get_track("abc123")
    assert result == {"title": "Song", "artist": "Artist", "album": "Album"}


@responses.activate
def test_token_is_cached_across_calls():
    _mock_token()
    responses.add(
        responses.GET,
        TRACK_URL,
        json={"name": "Song", "artists": [{"name": "Artist"}], "album": None},
        status=200,
    )
    responses.add(
        responses.GET,
        TRACK_URL,
        json={"name": "Song", "artists": [{"name": "Artist"}], "album": None},
        status=200,
    )
    client = SpotifyClient("id", "secret")
    client.get_track("abc123")
    client.get_track("abc123")
    token_calls = [c for c in responses.calls if c.request.url == TOKEN_URL]
    assert len(token_calls) == 1


@responses.activate
def test_401_triggers_reauth_retry():
    responses.add(responses.POST, TOKEN_URL, json={"access_token": "expired", "expires_in": 3600}, status=200)
    responses.add(responses.GET, TRACK_URL, status=401)
    responses.add(responses.POST, TOKEN_URL, json={"access_token": "fresh", "expires_in": 3600}, status=200)
    responses.add(
        responses.GET,
        TRACK_URL,
        json={"name": "Song", "artists": [{"name": "Artist"}], "album": None},
        status=200,
    )
    client = SpotifyClient("id", "secret")
    result = client.get_track("abc123")
    assert result["title"] == "Song"


@responses.activate
def test_search_track_returns_none_on_no_results():
    _mock_token()
    responses.add(responses.GET, SEARCH_URL, json={"tracks": {"items": []}}, status=200)
    client = SpotifyClient("id", "secret")
    assert client.search_track("Artist", "Song") is None


@responses.activate
def test_search_track_returns_uri():
    _mock_token()
    responses.add(responses.GET, SEARCH_URL, json={"tracks": {"items": [{"id": "xyz"}]}}, status=200)
    client = SpotifyClient("id", "secret")
    assert client.search_track("Artist", "Song") == "spotify:track:xyz"
