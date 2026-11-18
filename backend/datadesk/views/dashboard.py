"""Views for DataDesk.

Provisional in S1: it only proves the app is mounted and reachable. S3 adds the
``is_staff`` gate and S20 turns this into the real dashboard with the
"needs attention" counters.
"""
from django.views.generic import TemplateView


class DashboardView(TemplateView):
    """Renders the DataDesk landing page.

    Attributes:
        template_name (str): Template rendered by the view.
    """

    template_name = "datadesk/dashboard.html"
