import responses

from running_tuner.clients.lastfm_client import API_URL, LastfmClient


@responses.activate
def test_get_similar_success():
    responses.add(
        responses.GET,
        API_URL,
        json={
            "similartracks": {
                "track": [
                    {"name": "Song B", "artist": {"name": "Artist B"}, "match": "0.9"},
                    {"name": "Song C", "artist": {"name": "Artist C"}, "match": "0.5"},
                ]
            }
        },
        status=200,
    )
    client = LastfmClient("key")
    results = client.get_similar("Artist A", "Song A")
    assert results == [("Artist B", "Song B", 0.9), ("Artist C", "Song C", 0.5)]


@responses.activate
def test_get_similar_error_falls_back_to_artist_similar():
    responses.add(responses.GET, API_URL, json={"error": 6, "message": "not found"}, status=200)
    responses.add(
        responses.GET,
        API_URL,
        json={"similarartists": {"artist": [{"name": "Artist B", "match": "0.8"}]}},
        status=200,
    )
    responses.add(
        responses.GET,
        API_URL,
        json={"toptracks": {"track": [{"name": "Top Song"}]}},
        status=200,
    )
    client = LastfmClient("key")
    results = client.get_similar("Unknown Artist", "Unknown Song")
    assert results == [("Artist B", "Top Song", 0.4)]


@responses.activate
def test_get_similar_returns_empty_on_total_failure():
    responses.add(responses.GET, API_URL, json={"error": 6}, status=200)
    responses.add(responses.GET, API_URL, json={"error": 6}, status=200)
    client = LastfmClient("key")
    results = client.get_similar("Unknown", "Unknown")
    assert results == []
