"""Views for DataDesk.

Provisional in S1/S3: it only proves the app is mounted, gated and reachable.
S20 turns this into the real dashboard with the "needs attention" counters.
"""
from django.views.generic import TemplateView

from datadesk.mixins import DataDeskAccessMixin


class DashboardView(DataDeskAccessMixin, TemplateView):
    """Renders the DataDesk landing page for staff users.

    Attributes:
        template_name (str): Template rendered by the view.
    """

    template_name = "datadesk/dashboard.html"
