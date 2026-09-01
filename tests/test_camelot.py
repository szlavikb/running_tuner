from running_tuner import camelot


def test_normalize_key_librosa_style():
    assert camelot.normalize_key("C# minor") == "C# minor"
    assert camelot.normalize_key("Db major") == "C# major"


def test_normalize_key_getsongbpm_style():
    assert camelot.normalize_key("C#m") == "C# minor"
    assert camelot.normalize_key("F") == "F major"


def test_normalize_key_unparseable_returns_none():
    assert camelot.normalize_key("") is None
    assert camelot.normalize_key("not a key") is None


def test_to_camelot_known_keys():
    assert camelot.to_camelot("C major") == "8B"
    assert camelot.to_camelot("A minor") == "8A"


def test_is_compatible_same_key():
    assert camelot.is_compatible("C major", "C major") is True


def test_is_compatible_relative_minor():
    assert camelot.is_compatible("C major", "A minor") is True


def test_is_compatible_adjacent_on_wheel():
    assert camelot.is_compatible("C major", "G major") is True


def test_is_compatible_incompatible():
    assert camelot.is_compatible("C major", "F# major") is False


def test_is_compatible_missing_key_returns_none():
    assert camelot.is_compatible(None, "C major") is None
    assert camelot.is_compatible("C major", None) is None
