from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

REQUIRED_ENV_VARS = (
    "SPOTIFY_CLIENT_ID",
    "SPOTIFY_CLIENT_SECRET",
    "GETSONGBPM_API_KEY",
    "LASTFM_API_KEY",
)


@dataclass
class Settings:
    spotify_client_id: str
    spotify_client_secret: str
    getsongbpm_api_key: str
    lastfm_api_key: str


def load_settings() -> Settings:
    load_dotenv()
    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        raise SystemExit(
            "Missing required env vars: "
            + ", ".join(missing)
            + ". Copy .env.example to .env and fill in your API keys."
        )
    return Settings(
        spotify_client_id=os.environ["SPOTIFY_CLIENT_ID"],
        spotify_client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
        getsongbpm_api_key=os.environ["GETSONGBPM_API_KEY"],
        lastfm_api_key=os.environ["LASTFM_API_KEY"],
    )
