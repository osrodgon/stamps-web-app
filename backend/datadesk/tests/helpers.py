"""Test helpers shared by the DataDesk tests."""

UNHASHED_STATIC_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
"""STORAGES override that resolves ``{% static %}`` without a manifest.

The real setting uses whitenoise's manifest backend outside DEBUG, and that
backend raises ``ValueError`` for any file missing from the collected manifest
(which CI never builds). Tests render the templates with this override and let
``collectstatic`` itself validate the manifest.
"""
