"""Serves the stamp pictures to DataDesk (S10).

The images are not public assets: they are streamed through this staff-only
view, so turning the folder into a mount does not publish it. A missing file is
a 404 and the grid falls back to its hollow marker.
"""
from django.http import FileResponse, Http404, HttpRequest
from django.utils.cache import get_conditional_response
from django.utils.http import http_date
from django.views import View

from datadesk.images import image_path
from datadesk.mixins import DataDeskAccessMixin
from stamps_api.models import Stamp

CACHE_CONTROL = "private, max-age=604800"
"""A week: the files change when someone drops a new one, not per request."""


class StampImageView(DataDeskAccessMixin, View):
    """Returns the webp of one stamp, or 404 when it has no picture."""

    def get(self, request: HttpRequest, *args, **kwargs) -> FileResponse:
        """Streams the file with an ETag so revisits are a 304."""
        stamp = (
            Stamp.objects.select_related("issue__year")
            .filter(pk=kwargs["pk"])
            .first()
        )
        if stamp is None:
            raise Http404("Stamp not found.")

        path = image_path(stamp.issue.year.year, stamp.fesofi_code)
        if path is None:
            raise Http404("Stamp has no picture.")
        if not path.is_file():
            raise Http404("Stamp picture disappeared.")

        stat = path.stat()
        etag = f'"{int(stat.st_mtime)}-{stat.st_size}"'
        response = FileResponse(path.open("rb"), content_type="image/webp")
        response["ETag"] = etag
        response["Last-Modified"] = http_date(stat.st_mtime)
        response["Cache-Control"] = CACHE_CONTROL

        return get_conditional_response(
            request,
            etag=etag,
            last_modified=int(stat.st_mtime),
            response=response,
        )
