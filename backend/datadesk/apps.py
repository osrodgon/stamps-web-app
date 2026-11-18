from django.apps import AppConfig


class DataDeskConfig(AppConfig):
    """Configuration for the DataDesk internal DB-maintenance app.

    DataDesk is not part of the public API: it has no endpoints under
    ``/api/v1/`` and it is mounted on its own URL only when
    ``DATADESK_ENABLED`` is true. Keeping it as a normal Django app lets it
    reuse the project's models, settings, logging and database connection
    while staying outside the DRF surface.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "datadesk"
    verbose_name = "DataDesk"
