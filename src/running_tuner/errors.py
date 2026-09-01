class RunningTunerError(Exception):
    """Base class for all running-tuner errors."""


class ResolutionError(RunningTunerError):
    """Raised when a reference input (file/Spotify link/YouTube link) can't be resolved."""


class EnrichmentError(RunningTunerError):
    """Raised when required BPM/feature data can't be obtained for the reference track."""


class RateLimitError(RunningTunerError):
    """Raised when an external API rate-limits us and retries are exhausted."""
