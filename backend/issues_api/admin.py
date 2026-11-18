from django.contrib import admin

from issues_api.models import Issue


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    """Admin for issues.

    ``updated_at`` is maintained by the database layer, so it is shown but never
    edited by hand.
    """

    readonly_fields = ("updated_at",)
