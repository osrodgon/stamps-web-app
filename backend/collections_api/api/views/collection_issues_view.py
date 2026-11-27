"""The series of one collection, paginated like the issues list (plan step B1).

The screen at `/collections/<id>` asks this endpoint for a page of the series in the
collection, with the progress, what the user paid and what the catalogue says. The
parameters, the defaults and the response shape mirror `/issues/`, so the frontend
reuses its pagination and parsing unchanged.
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


class CollectionIssuesView(Logger, APIView):
    """Lists the series of a collection, scoped to the JWT's user."""

    serializer_class = CollectionIssuePageSerializer

    @extend_schema(
        operation_id="list_collection_issues",
        tags=["Collection Management"],
        summary="List the series of a collection",
        description="Returns one page of the series the collection holds "
        "something of, with how many stamps each one has, how many the user owns, "
        "what they paid and the catalogue value. The parameters, the defaults and "
        "the pagination block are the ones `/issues/` uses.",
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
                description="Filter by year or year range (e.g. 2002 or 2000-2010).",
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
                name="CollectionIssuesRetrieved",
                description="The series of the collection were retrieved.",
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                GenericResponseSerializer,
                name="CollectionIssuesForbidden",
                success=False,
                description="Permission denied.",
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="CollectionIssuesNotFound",
                success=False,
                description="The collection does not exist or is not the caller's.",
            ),
        },
    )
    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """Return one page of the series of the caller's collection.

        Args:
            request: the incoming request, with the user's JWT.
            pk: the collection's id.

        Returns:
            The page, or a 404 when the collection is not the caller's.
        """
        self.log.debug(Messages.Get.retrieve_all(f"series of collection {pk}"))
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
        )

        return Response(
            data=CollectionIssuePageSerializer(page).data,
            status=status.HTTP_200_OK,
        )
