# running-tuner

Find songs with a similar tempo (and, where possible, key) to a reference track — for building pace-matched running playlists.

The reference can be:
- a local audio file (`--file`)
- a Spotify track link (`--spotify`)
- a YouTube video link (`--youtube`)

## How it works

- **Local files and YouTube links** are analyzed directly with `librosa` (tempo, key, energy). YouTube audio is downloaded to a temp file with `yt-dlp` and deleted immediately after analysis — never kept.
- **Spotify links** are resolved to title/artist via the Spotify API (Client Credentials), then looked up in the [GetSongBPM](https://getsongbpm.com/api) database for BPM/key. Spotify's Audio Features and Recommendations endpoints were deprecated for new apps in late 2024, so Spotify is only used for identification and for resolving result tracks back to playable links — never for tempo data or "similar tracks."
- **Candidate discovery** uses [Last.fm](https://www.last.fm/api)'s `track.getSimilar` (falling back to `artist.getSimilar` + top tracks when the reference isn't in Last.fm's catalog). Each candidate's BPM is looked up via GetSongBPM; candidates GetSongBPM doesn't know about are dropped unless `--deep` is passed, in which case a slower YouTube-search + `librosa` fallback runs (capped by `--deep-max`).
- Results are ranked primarily by BPM closeness to the reference (within `--tolerance`), with key compatibility (Camelot wheel) and Last.fm's own match score as tie-breakers. Energy/mood scoring is only available for candidates that went through `--deep` analysis — GetSongBPM has no energy field, and it's never faked.

## Setup

Requires Python 3.10+ and **ffmpeg on PATH** (needed by `yt-dlp` to extract audio — on Windows, `winget install ffmpeg` or download from ffmpeg.org and add it to PATH).

```bash
python -m venv .venv
.venv/Scripts/activate
pip install -e ".[dev]"
cp .env.example .env
```

Fill in `.env` with API keys from:
- **Spotify**: [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) — create an app, use the Client ID/Secret (Client Credentials flow, no redirect URI approval needed beyond a placeholder value).
- **GetSongBPM**: [getsongbpm.com/api](https://getsongbpm.com/api) — register for a free API key. Their terms require displaying an attribution link to GetSongBPM wherever results are shown publicly.
- **Last.fm**: [last.fm/api/account/create](https://www.last.fm/api/account/create) — get an API key.

## Usage

```bash
running-tuner match --file "C:\Music\song.mp3"
running-tuner match --spotify https://open.spotify.com/track/<id>
running-tuner match --youtube https://youtube.com/watch?v=<id>

# options
--artist "Beast in Black"   # override the resolved reference artist (e.g. --file with no/incomplete ID3 tags)
--title "Blind and Frozen"  # override the resolved reference title (same use case)
--tolerance 4     # BPM window around the reference (default 4)
--limit 10        # number of results (default 10)
--deep            # enable yt-dlp+librosa fallback for candidates missing BPM data (slow, ~5-15s/candidate)
--deep-max 5      # cap how many candidates get the deep fallback
--output json     # machine-readable output instead of a table
```

`--file` reads artist/title from the audio file's ID3 tags; if the file has none, both come back empty and Last.fm's similarity search — which requires an artist — silently returns 0 candidates. Use `--artist`/`--title` to supply them manually in that case.

## Testing

```bash
pytest                    # unit tests, mocked HTTP, no network calls
pytest -m slow             # also run the real librosa audio-decoding test
```

### Manual end-to-end smoke test

1. `running-tuner match --file <known_song.mp3> --limit 5` — BPM roughly matches a known reference tempo.
2. `running-tuner match --spotify <link> --limit 5` — GetSongBPM lookup succeeds, results are BPM-plausible.
3. `running-tuner match --youtube <link> --deep --limit 3` — after the run, no `running_tuner_yt_*` folders remain under your temp directory; at least one candidate's notes/source show the deep path engaged.
4. Failure paths: missing `.env` var, malformed Spotify URL, and a private/deleted YouTube video should all produce a clean error message, not a raw traceback.

## Known limitations

- GetSongBPM's catalog still has real gaps (verified: e.g. "Beast in Black" is indexed as an artist but not every one of their tracks is) — those candidates are silently dropped unless `--deep` is used.
- `librosa`'s key estimation is a heuristic (Krumhansl-Schmuckler correlation), not ground truth — treated as a secondary tie-breaker only, never the primary ranking signal.
- `yt-dlp` requires periodic updates (`pip install -U yt-dlp`) as YouTube changes internals; failures there surface as a clean error rather than a crash.
- Free-tier rate limits on GetSongBPM/Last.fm are handled with in-process caching and throttling, but very large `--limit`/`--deep-max` values will still take a while.
