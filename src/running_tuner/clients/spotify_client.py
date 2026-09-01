from __future__ import annotations

import time
from typing import Optional

import requests

from running_tuner.errors import ResolutionError, RateLimitError

TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"


class SpotifyClient:
    """Client-Credentials-only Spotify access: track lookup and search.

    Deliberately does NOT wrap Audio Features / Recommendations / Related
    Artists — those endpoints are no longer available to new apps.
    """

    def __init__(self, client_id: str, client_secret: str, session: Optional[requests.Session] = None):
        self._client_id = client_id
        self._client_secret = client_secret
        self._session = session or requests.Session()
        self._token: Optional[str] = None
        self._token_expiry: float = 0.0

    def _get_token(self, force_refresh: bool = False) -> str:
        if self._token and not force_refresh and time.time() < self._token_expiry:
            return self._token
        resp = self._session.post(
            TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(self._client_id, self._client_secret),
            timeout=10,
        )
        if resp.status_code != 200:
            raise ResolutionError(f"Spotify auth failed ({resp.status_code}): {resp.text[:200]}")
        payload = resp.json()
        self._token = payload["access_token"]
        self._token_expiry = time.time() + payload.get("expires_in", 3600) - 30
        return self._token

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        for attempt in range(2):
            token = self._get_token(force_refresh=attempt > 0)
            resp = self._session.request(method, url, headers={"Authorization": f"Bearer {token}"}, timeout=10, **kwargs)
            if resp.status_code == 401 and attempt == 0:
                continue
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", "1"))
                if attempt == 0:
                    time.sleep(retry_after)
                    continue
                raise RateLimitError("Spotify API rate-limited the request twice; giving up.")
            return resp
        return resp

    def get_track(self, track_id: str) -> dict:
        resp = self._request("GET", f"{API_BASE}/tracks/{track_id}")
        if resp.status_code != 200:
            raise ResolutionError(f"Spotify track lookup failed ({resp.status_code}) for id={track_id}")
        data = resp.json()
        return {
            "title": data["name"],
            "artist": data["artists"][0]["name"] if data.get("artists") else "",
            "album": (data.get("album") or {}).get("name"),
        }

    def search_track(self, artist: str, title: str) -> Optional[str]:
        try:
            resp = self._request(
                "GET",
                f"{API_BASE}/search",
                params={"q": f"track:{title} artist:{artist}", "type": "track", "limit": 1},
            )
        except (RateLimitError, ResolutionError):
            return None
        if resp.status_code != 200:
            return None
        items = (resp.json().get("tracks") or {}).get("items") or []
        if not items:
            return None
        return f"spotify:track:{items[0]['id']}"
