from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import Iterator, Optional

import click

from running_tuner import output
from running_tuner.audio import analysis
from running_tuner.clients.getsongbpm_client import GetSongBPMClient
from running_tuner.clients.lastfm_client import LastfmClient
from running_tuner.clients.spotify_client import SpotifyClient
from running_tuner.config import load_settings
from running_tuner.errors import EnrichmentError, RateLimitError, ResolutionError
from running_tuner.models import ReferenceTrack, TrackRef
from running_tuner.pipeline import enrich, rank
from running_tuner.resolvers import local_file, spotify_link, youtube_link


@contextmanager
def _resolve_reference(
    file: Optional[str], spotify: Optional[str], youtube: Optional[str], spotify_client: SpotifyClient
) -> Iterator[TrackRef]:
    if file:
        click.echo("🎧  _resolve_reference: --file branch -> local_file.resolve()", err=True)
        yield local_file.resolve(file)
    elif spotify:
        click.echo("🎵  _resolve_reference: --spotify branch -> spotify_link.resolve()", err=True)
        yield spotify_link.resolve(spotify, spotify_client)
    elif youtube:
        click.echo("📺  _resolve_reference: --youtube branch -> youtube_link.resolve()", err=True)
        with youtube_link.resolve(youtube) as ref:
            yield ref
    else:
        raise ResolutionError("No reference input given.")


def _build_reference_features(ref: TrackRef, getsongbpm_client: GetSongBPMClient) -> ReferenceTrack:
    click.echo(f"🎚️  _build_reference_features: ref={ref.artist!r} - {ref.title!r} (source={ref.source})", err=True)
    if ref.local_audio_path is not None:
        click.echo("🎚️  _build_reference_features: analyzing local audio with librosa", err=True)
        features = analysis.analyze(ref.local_audio_path)
    else:
        if not ref.artist or not ref.title:
            raise EnrichmentError("Reference has no artist/title metadata to look up BPM with.")
        click.echo("🎚️  _build_reference_features: getsongbpm_client.lookup()", err=True)
        features = getsongbpm_client.lookup(ref.artist, ref.title)
        if features.bpm is None:
            raise EnrichmentError(
                f"No BPM found for reference '{ref.artist} - {ref.title}' via GetSongBPM; "
                "retry with --file if you have the audio locally."
            )
    return ReferenceTrack(ref=ref, features=features)


@click.group()
def main() -> None:
    """running-tuner: find songs with similar tempo/key to a reference track."""


@main.command()
@click.option("--file", "file_", type=click.Path(exists=False), help="Path to a local audio file.")
@click.option("--spotify", type=str, help="A Spotify track URL.")
@click.option("--youtube", type=str, help="A YouTube video URL.")
@click.option("--artist", type=str, default=None, help="Override the reference artist (e.g. when a local file has no tags).")
@click.option("--title", type=str, default=None, help="Override the reference title (e.g. when a local file has no tags).")
@click.option("--tolerance", type=float, default=4.0, show_default=True, help="BPM tolerance window.")
@click.option("--limit", type=int, default=10, show_default=True, help="Number of results to show.")
@click.option("--deep", is_flag=True, default=False, help="Enable yt-dlp+librosa fallback for candidates missing BPM data.")
@click.option("--deep-max", type=int, default=5, show_default=True, help="Max candidates to run the deep fallback on.")
@click.option("--output", "output_format", type=click.Choice(["table", "json"]), default="table", show_default=True)
def match(
    file_: Optional[str],
    spotify: Optional[str],
    youtube: Optional[str],
    artist: Optional[str],
    title: Optional[str],
    tolerance: float,
    limit: int,
    deep: bool,
    deep_max: int,
    output_format: str,
) -> None:
    """Find songs with a similar tempo (and key) to the given reference."""
    inputs_given = [x for x in (file_, spotify, youtube) if x]
    if len(inputs_given) != 1:
        raise click.UsageError("Exactly one of --file, --spotify, --youtube must be given.")

    click.echo(f"▶️  match: file={file_!r} spotify={spotify!r} youtube={youtube!r}", err=True)

    settings = load_settings()
    spotify_client = SpotifyClient(settings.spotify_client_id, settings.spotify_client_secret)
    getsongbpm_client = GetSongBPMClient(settings.getsongbpm_api_key)
    lastfm_client = LastfmClient(settings.lastfm_api_key)

    try:
        with _resolve_reference(file_, spotify, youtube, spotify_client) as ref:
            if artist:
                ref.artist = artist
            if title:
                ref.title = title
            click.echo(f"✅  resolved reference: {ref.artist!r} - {ref.title!r} (source_uri={ref.source_uri})", err=True)
            reference = _build_reference_features(ref, getsongbpm_client)
            click.echo(f"✅  reference BPM: {reference.features.bpm}", err=True)

            click.echo("📻  match: lastfm_client.get_similar()", err=True)
            raw_candidates = lastfm_client.get_similar(
                reference.ref.artist, reference.ref.title, limit=limit * 3
            )
            click.echo(f"📻  match: got {len(raw_candidates)} raw candidates from last.fm", err=True)

            click.echo("🧩  match: enrich.build_candidates() -- this also calls spotify_client.search_track() per candidate", err=True)
            candidates = enrich.build_candidates(
                raw_candidates, getsongbpm_client, spotify_client, deep=deep, deep_max=deep_max
            )
            click.echo(f"🧩  match: {len(candidates)}/{len(raw_candidates)} candidates enriched with BPM data", err=True)

            click.echo("🏆  match: rank.score_and_filter()", err=True)
            results = rank.score_and_filter(reference.features, candidates, tolerance=tolerance)[:limit]
            click.echo(f"🏆  match: {len(results)} results after ranking/filtering", err=True)

            skipped = len(raw_candidates) - len(candidates)
            if skipped > 0 and output_format == "table":
                click.echo(f"({skipped} of {len(raw_candidates)} candidates had no BPM data available.)", err=True)

            if output_format == "json":
                output.render_json(reference, results)
            else:
                output.render_table(reference, results)

    except (ResolutionError, EnrichmentError, RateLimitError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
