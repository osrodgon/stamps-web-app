from django.urls import path

from condition_types_api.api.views.condition_types_by_id_view import ConditionTypesByIdView
from condition_types_api.api.views.condition_types_view import ConditionTypesView
from condition_types_api.models import ConditionType


base_url = ""

urlpatterns = [
    path(base_url, ConditionTypesView.as_view(), name="condition_types"),
    path(base_url + "<int:pk>", ConditionTypesByIdView.as_view(), name="condition_types_by_id"),   
]