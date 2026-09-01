from __future__ import annotations

import json

from rich.console import Console
from rich.table import Table

from running_tuner.models import MatchResult, ReferenceTrack


def render_table(reference: ReferenceTrack, results: list[MatchResult]) -> None:
    console = Console()
    console.print(
        f"[bold]Reference:[/bold] {reference.ref.artist} - {reference.ref.title} "
        f"({reference.features.bpm} BPM, {reference.features.key or 'key unknown'}, "
        f"source: {reference.features.bpm_source})"
    )

    if not results:
        console.print("[yellow]No candidates found within tolerance.[/yellow]")
        return

    table = Table(show_lines=False)
    table.add_column("Artist")
    table.add_column("Title")
    table.add_column("BPM", justify="right")
    table.add_column("ΔBPM", justify="right")
    table.add_column("Key")
    table.add_column("Key match")
    table.add_column("BPM source")
    table.add_column("Score", justify="right")
    table.add_column("Spotify")

    for result in results:
        candidate = result.candidate
        table.add_row(
            candidate.artist,
            candidate.title,
            f"{candidate.features.bpm:.1f}" if candidate.features.bpm is not None else "-",
            f"{result.bpm_delta:.1f}" if result.bpm_delta is not None else "-",
            candidate.features.key or "-",
            "yes" if result.key_compatible else ("no" if result.key_compatible is False else "-"),
            candidate.features.bpm_source or "-",
            f"{result.score:.2f}",
            candidate.spotify_uri or "-",
        )
    console.print(table)

    for result in results:
        for note in result.notes:
            console.print(f"[dim]  {result.candidate.artist} - {result.candidate.title}: {note}[/dim]")


def render_json(reference: ReferenceTrack, results: list[MatchResult]) -> None:
    payload = {
        "reference": {
            "artist": reference.ref.artist,
            "title": reference.ref.title,
            "bpm": reference.features.bpm,
            "bpm_source": reference.features.bpm_source,
            "key": reference.features.key,
            "key_source": reference.features.key_source,
        },
        "results": [
            {
                "artist": r.candidate.artist,
                "title": r.candidate.title,
                "bpm": r.candidate.features.bpm,
                "bpm_delta": r.bpm_delta,
                "key": r.candidate.features.key,
                "key_compatible": r.key_compatible,
                "bpm_source": r.candidate.features.bpm_source,
                "lastfm_match": r.candidate.lastfm_match,
                "spotify_uri": r.candidate.spotify_uri,
                "score": r.score,
                "notes": r.notes,
            }
            for r in results
        ],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
