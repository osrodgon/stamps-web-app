from django.contrib import admin

from stamps_api.models import Stamp


@admin.register(Stamp)
class StampAdmin(admin.ModelAdmin):
    """Admin for stamps.

    ``updated_at`` is maintained by the database layer, so it is shown but never
    edited by hand.
    """

    readonly_fields = ("updated_at",)
