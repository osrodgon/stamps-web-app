"""Language switch for DataDesk.

The switch accepts two languages, POST only, and delegates the cookie handling
to Django's ``set_language`` so ``next`` keeps its safe-URL validation.
"""
import logging

from django.conf import settings
from django.http import HttpRequest, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.views.i18n import set_language

logger = logging.getLogger(__name__)


@require_POST
def set_datadesk_language(request: HttpRequest):
    """Switches the DataDesk language and returns to the previous page.

    A language outside ``DATADESK_LANGUAGES`` is ignored, not stored: the caller
    is redirected back without the cookie changing.
    """
    language = request.POST.get("language", "")
    target = request.POST.get("next") or f"/{settings.DATADESK_URL}"

    if language not in settings.DATADESK_LANGUAGES:
        logger.warning("DataDesk rejected language %r", language)
        return HttpResponseRedirect(target)

    return set_language(request)
