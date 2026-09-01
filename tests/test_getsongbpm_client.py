import responses

from running_tuner.clients.getsongbpm_client import SEARCH_URL, GetSongBPMClient


@responses.activate
def test_lookup_success():
    responses.add(
        responses.GET,
        SEARCH_URL,
        json={"search": [{"tempo": "128", "key_of": "C#m"}]},
        status=200,
    )
    client = GetSongBPMClient("key")
    client._last_call = 0  # skip throttle in tests
    features = client.lookup("Artist", "Song")
    assert features.bpm == 128.0
    assert features.bpm_source == "getsongbpm"
    assert features.key == "C#m"


@responses.activate
def test_lookup_no_results():
    responses.add(responses.GET, SEARCH_URL, json={"search": []}, status=200)
    client = GetSongBPMClient("key")
    features = client.lookup("Artist", "Unknown Song")
    assert features.bpm is None


@responses.activate
def test_lookup_malformed_json():
    responses.add(responses.GET, SEARCH_URL, body="not json", status=200)
    client = GetSongBPMClient("key")
    features = client.lookup("Artist", "Song")
    assert features.bpm is None


@responses.activate
def test_lookup_is_cached():
    responses.add(
        responses.GET,
        SEARCH_URL,
        json={"search": [{"tempo": "100", "key_of": "C"}]},
        status=200,
    )
    client = GetSongBPMClient("key")
    client.lookup("Artist", "Song")
    client.lookup("artist", "song")  # case-insensitive cache key
    assert len(responses.calls) == 1
