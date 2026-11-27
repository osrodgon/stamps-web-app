"""The catalogue a collection can still add from (plan step C2).

The dialog that adds stamps needs the opposite of the collection's own list: the series
it does not hold yet, with how much of each one it already has. The parameters, the
defaults, the pagination block and the figures are B1's — the same page, scoped to the
catalogue instead of to the collection.
"""

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema

from collections_api.api.serializers.collection_issue_summary_serializer import (
    CollectionIssuePageSerializer,
)
from collections_api.models import Collection
from collections_api.services.collection_issues_service import CollectionIssuesService
from common.api.messages import Messages
from common.api.serializers.generic_response import (
    GenericResponse,
    GenericResponseSerializer,
)
from common.core.current_user import CurrentUser
from common.core.query import Query
from common.core.schemas import standardized_response
from common.log.logger import Logger


class CollectionCatalogueIssuesView(Logger, APIView):
    """Lists the series of the catalogue, with what the collection holds of each."""

    serializer_class = CollectionIssuePageSerializer

    @extend_schema(
        operation_id="list_collection_catalogue",
        tags=["Collection Management"],
        summary="List the catalogue for a collection",
        description="Returns one page of the series of the catalogue — every "
        "series with stamps, held or not — with how many stamps each one has "
        "and how many the collection already owns. The parameters, the defaults "
        "and the pagination block are the ones the collection's own list uses.",
        parameters=[
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Page number, 1-based.",
                required=False,
            ),
            OpenApiParameter(
                name="pageSize",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Series per page (default 15). A value of 0 means all.",
                required=False,
            ),
            OpenApiParameter(
                name="name",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by series name.",
                required=False,
            ),
            OpenApiParameter(
                name="year",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by year or year range (e.g. 2002, 2000-2010, "
                "1850- or -1860).",
                required=False,
            ),
            OpenApiParameter(
                name="sortBy",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Order by `date` (default) or `name`.",
                required=False,
            ),
            OpenApiParameter(
                name="order",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="`asc` (default) or `desc`.",
                required=False,
            ),
        ],
        responses={
            status.HTTP_200_OK: standardized_response(
                CollectionIssuePageSerializer,
                name="CollectionCatalogueRetrieved",
                description="The catalogue page was retrieved.",
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                GenericResponseSerializer,
                name="CollectionCatalogueForbidden",
                success=False,
                description="Permission denied.",
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="CollectionCatalogueNotFound",
                success=False,
                description="The collection does not exist or is not the caller's.",
            ),
        },
    )
    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """Return one page of the catalogue for this collection.

        Args:
            request: the incoming request, with the user's JWT.
            pk: the collection's id.

        Returns:
            The page, or a 404 when the collection is not the caller's.
        """
        self.log.debug(Messages.Get.retrieve_all(f"catalogue of collection {pk}"))
        user = CurrentUser(request).get()

        try:
            collection = Collection.objects.get(pk=pk, user=user)
        except Collection.DoesNotExist:
            message = Messages.Get.not_found("collection", pk)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND,
            )

        page = CollectionIssuesService().page(
            collection,
            page=Query.int_param(request.query_params.get("page"), 1),
            page_size=Query.int_param(request.query_params.get("pageSize"), 15),
            name=(request.query_params.get("name") or "").strip(),
            year=(request.query_params.get("year") or "").strip(),
            sort_by=request.query_params.get("sortBy") or "date",
            order=request.query_params.get("order") or "asc",
            owned_only=False,
        )

        return Response(
            data=CollectionIssuePageSerializer(page).data,
            status=status.HTTP_200_OK,
        )
