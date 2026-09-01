"""Key-string normalization and Camelot-wheel compatibility scoring.

Accepts key strings in either librosa's "C# minor" style or GetSongBPM's
"C#m" / "Dbm" style, normalizes enharmonic spelling, and maps to Camelot
notation (e.g. "8B") for compatibility comparisons.
"""

from __future__ import annotations

import re
from typing import Optional

_ENHARMONIC = {
    "Db": "C#",
    "D#": "Eb",
    "Gb": "F#",
    "G#": "Ab",
    "A#": "Bb",
}

# (normalized note, is_minor) -> Camelot code
_CAMELOT: dict[tuple[str, bool], str] = {
    ("C", False): "8B",
    ("G", False): "9B",
    ("D", False): "10B",
    ("A", False): "11B",
    ("E", False): "12B",
    ("B", False): "1B",
    ("F#", False): "2B",
    ("C#", False): "3B",
    ("Ab", False): "4B",
    ("Eb", False): "5B",
    ("Bb", False): "6B",
    ("F", False): "7B",
    ("A", True): "8A",
    ("E", True): "9A",
    ("B", True): "10A",
    ("F#", True): "11A",
    ("C#", True): "12A",
    ("Ab", True): "1A",
    ("Eb", True): "2A",
    ("Bb", True): "3A",
    ("F", True): "4A",
    ("C", True): "5A",
    ("G", True): "6A",
    ("D", True): "7A",
}

_NOTE_RE = re.compile(r"^([A-Ga-g])([#b]?)\s*")


def _normalize_note(raw_note: str) -> Optional[str]:
    match = _NOTE_RE.match(raw_note.strip())
    if not match:
        return None
    letter, accidental = match.group(1).upper(), match.group(2)
    note = letter + ("#" if accidental == "#" else "b" if accidental == "b" else "")
    return _ENHARMONIC.get(note, note)


def normalize_key(raw: str) -> Optional[str]:
    """Return a canonical "<Note> major"/"<Note> minor" string, or None if unparseable."""
    if not raw:
        return None
    text = raw.strip()
    is_minor = bool(re.search(r"\bmin(or)?\b", text, re.IGNORECASE)) or text.rstrip().endswith("m") and not text.rstrip().endswith("maj")
    is_major = bool(re.search(r"\bmaj(or)?\b", text, re.IGNORECASE))
    if is_major:
        is_minor = False

    note_part = re.split(r"\s|min|maj", text, flags=re.IGNORECASE)[0]
    note_part = note_part[:-1] if note_part.endswith("m") and len(note_part) > 1 else note_part
    note = _normalize_note(note_part)
    if note is None:
        return None
    return f"{note} {'minor' if is_minor else 'major'}"


def to_camelot(raw: str) -> Optional[str]:
    normalized = normalize_key(raw)
    if normalized is None:
        return None
    note, quality = normalized.rsplit(" ", 1)
    return _CAMELOT.get((note, quality == "minor"))


def is_compatible(key_a: Optional[str], key_b: Optional[str]) -> Optional[bool]:
    """True if the two Camelot codes are the same, adjacent (+-1), or relative major/minor."""
    if not key_a or not key_b:
        return None
    camelot_a, camelot_b = to_camelot(key_a), to_camelot(key_b)
    if camelot_a is None or camelot_b is None:
        return None
    num_a, letter_a = int(camelot_a[:-1]), camelot_a[-1]
    num_b, letter_b = int(camelot_b[:-1]), camelot_b[-1]
    if camelot_a == camelot_b:
        return True
    if num_a == num_b and letter_a != letter_b:
        return True
    if letter_a == letter_b and abs(num_a - num_b) % 12 in (1, 11):
        return True
    return False
