"""The DataDesk dashboard: what needs attention, and where to go next.

Six cards, one per "needs attention" queue, each one a link into the workbench
with that filter already applied. The three stamp-level queues also say how many
series hold those stamps, because the grid they open is a grid of series: a card
saying "1,177" in front of a grid saying "412" would look like a bug.
"""

from typing import Any

from django.utils.formats import number_format
from django.utils.translation import ngettext
from django.views.generic import TemplateView

from datadesk.mixins import DataDeskAccessMixin
from datadesk.service import STAMPS, QueueCard, dashboard_queues
from issues_api.models import Issue
from stamps_api.models import Stamp


class DashboardView(DataDeskAccessMixin, TemplateView):
    """Renders the landing page of DataDesk for staff users.

    Attributes:
        template_name (str): Template rendered by the view.
    """

    template_name = "datadesk/dashboard.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Adds the counters, the totals and the two groups of cards."""
        context = super().get_context_data(**kwargs)
        cards = [_card(row) for row in dashboard_queues()]

        context.update(
            cards=[card for card in cards if card["count"]],
            clear=[card for card in cards if not card["count"]],
            open_issues=sum(1 for card in cards if card["count"]),
            totals={
                "issues": _number(Issue.objects.count()),
                "stamps": _number(Stamp.objects.count()),
            },
        )
        return context


def _card(row: QueueCard) -> dict[str, Any]:
    """Turns one queue into what the template shows.

    The stamp rows carry a second line with the series they live in; the numbers
    are formatted by the active language, so Spanish reads 1.177 and English
    1,177 without the template knowing.
    """
    card: dict[str, Any] = {
        "key": row.key,
        "attention": row.attention,
        "label": row.label,
        "count": row.count,
        "count_text": _number(row.count),
    }
    if row.unit == STAMPS and row.issues is not None:
        card["issues"] = row.issues
        card["issues_text"] = ngettext(
            "in %(count)s series", "in %(count)s series", row.issues
        ) % {"count": _number(row.issues)}
    return card


def _number(value: int) -> str:
    """Returns a count grouped the way the active language groups numbers."""
    return number_format(value, force_grouping=True)
