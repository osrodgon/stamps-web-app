"""Severity enum for notification types."""

from enum import Enum


class Severity(str, Enum):
    """Notification severity levels for user feedback."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"