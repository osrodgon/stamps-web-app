"""Errors the source layer raises, so the view can tell them apart (step A2).

Before this, every failure was wrapped into one exception and the endpoint
answered 500: a wrong key, a host we do not allow, a source that is down and a
source that simply has nothing all looked the same. Each class here maps to one
HTTP status in `SeriesExtractionView`.
"""


class SourceError(Exception):
    """Base class for anything that went wrong while asking a source."""


class SourceNotAllowed(SourceError):
    """The URL points at a host the client may not reach."""


class SourceUnavailable(SourceError):
    """The source could not be reached, timed out, or kept failing after retries."""


class SourceNotFound(SourceError):
    """The source answered, and the thing we asked for is not there."""


class SourceConfigurationError(SourceError):
    """A source is missing its URL or key: a deployment problem, not a miss."""
