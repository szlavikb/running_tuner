from __future__ import annotations

import time
from typing import Optional

import requests

API_URL = "https://ws.audioscrobbler.com/2.0/"
MIN_INTERVAL_SECONDS = 0.25


class LastfmClient:
    """Discovers candidate similar tracks via Last.fm's track.getSimilar,
    falling back to artist.getSimilar + artist.getTopTracks when the
    reference track itself isn't in Last.fm's catalog.
    """

    def __init__(self, api_key: str, session: Optional[requests.Session] = None):
        self._api_key = api_key
        self._session = session or requests.Session()
        self._last_call = 0.0

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_call
        if elapsed < MIN_INTERVAL_SECONDS:
            time.sleep(MIN_INTERVAL_SECONDS - elapsed)
        self._last_call = time.time()

    def _get(self, params: dict) -> dict:
        self._throttle()
        params = {**params, "api_key": self._api_key, "format": "json"}
        try:
            resp = self._session.get(API_URL, params=params, timeout=10)
            return resp.json()
        except (requests.RequestException, ValueError):
            return {}

    def get_similar(self, artist: str, track: str, limit: int = 50) -> list[tuple[str, str, float]]:
        data = self._get({"method": "track.getsimilar", "artist": artist, "track": track, "limit": limit})
        if data.get("error"):
            return self._get_similar_via_artist(artist, limit)

        tracks = ((data.get("similartracks") or {}).get("track")) or []
        results = []
        for item in tracks:
            name = item.get("name")
            item_artist = (item.get("artist") or {}).get("name")
            match = item.get("match")
            if not name or not item_artist:
                continue
            try:
                match_score = float(match) if match is not None else 0.0
            except (TypeError, ValueError):
                match_score = 0.0
            results.append((item_artist, name, match_score))
        return results

    def _get_similar_via_artist(self, artist: str, limit: int) -> list[tuple[str, str, float]]:
        data = self._get({"method": "artist.getsimilar", "artist": artist, "limit": min(limit, 15)})
        if data.get("error"):
            return []
        similar_artists = ((data.get("similarartists") or {}).get("artist")) or []

        results: list[tuple[str, str, float]] = []
        for artist_entry in similar_artists:
            artist_name = artist_entry.get("name")
            if not artist_name:
                continue
            match = artist_entry.get("match")
            try:
                base_score = float(match) if match is not None else 0.0
            except (TypeError, ValueError):
                base_score = 0.0

            top_tracks_data = self._get({"method": "artist.gettoptracks", "artist": artist_name, "limit": 3})
            if top_tracks_data.get("error"):
                continue
            top_tracks = ((top_tracks_data.get("toptracks") or {}).get("track")) or []
            for track_entry in top_tracks:
                name = track_entry.get("name")
                if not name:
                    continue
                # lower confidence than a genuine track-level match, tagged via a discounted score
                results.append((artist_name, name, base_score * 0.5))
            if len(results) >= limit:
                break
        return results[:limit]
