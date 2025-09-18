from django.urls import path
from stamps_api.api.views.stamps_view import StampsView
from stamps_api.api.views.stamps_by_id_view import StampsByIdView

urlpatterns = [
    path('', StampsView.as_view(), name='stamps'),
    path('<int:id>', StampsByIdView.as_view(), name='stamp-by-id'),
]