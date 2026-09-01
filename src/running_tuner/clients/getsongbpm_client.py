from __future__ import annotations

import time
from typing import Optional

import requests

from running_tuner.models import TrackFeatures

SEARCH_URL = "https://api.getsong.co/search/"
MIN_INTERVAL_SECONDS = 1.0


class GetSongBPMClient:
    """Looks up BPM/key for a track by artist+title. Free-tier friendly:
    throttles requests and caches results for the lifetime of the client.
    """

    def __init__(self, api_key: str, session: Optional[requests.Session] = None):
        self._api_key = api_key
        self._session = session or requests.Session()
        self._cache: dict[tuple[str, str], TrackFeatures] = {}
        self._last_call = 0.0

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_call
        if elapsed < MIN_INTERVAL_SECONDS:
            time.sleep(MIN_INTERVAL_SECONDS - elapsed)
        self._last_call = time.time()

    def lookup(self, artist: str, title: str) -> TrackFeatures:
        cache_key = (artist.strip().lower(), title.strip().lower())
        if cache_key in self._cache:
            return self._cache[cache_key]

        self._throttle()
        try:
            resp = self._session.get(
                SEARCH_URL,
                params={
                    "type": "both",
                    "lookup": f"song:{title} artist:{artist}",
                    "api_key": self._api_key,
                },
                timeout=10,
            )
            data = resp.json() if resp.status_code == 200 else {}
        except (requests.RequestException, ValueError):
            data = {}

        results = data.get("search") if isinstance(data, dict) else None
        features = TrackFeatures()
        if results and isinstance(results, list):
            top = results[0]
            tempo = top.get("tempo")
            key_of = top.get("key_of")
            if tempo is not None:
                try:
                    features.bpm = float(tempo)
                    features.bpm_source = "getsongbpm"
                except (TypeError, ValueError):
                    pass
            if key_of:
                features.key = str(key_of)
                features.key_source = "getsongbpm"

        self._cache[cache_key] = features
        return features
