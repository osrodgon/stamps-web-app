"""
Severity enum for notification types.

Provides a set of severity levels used by the notification system
to determine the visual style (color) of user feedback messages.

Example:
    from core.severity import Severity
    await show_notification("Operation complete", severity=Severity.SUCCESS)
"""

from enum import Enum


class Severity(str, Enum):
    """Notification severity levels for user feedback.

    Each severity level corresponds to a specific color in the UI:
    - INFO: Blue - General informational messages
    - SUCCESS: Green - Successful operations
    - WARNING: Orange - Warnings that need attention
    - ERROR: Red - Error conditions and failures
    """
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"