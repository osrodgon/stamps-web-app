"""One series of a collection with every stamp and the caller's copy (plan step B2).

The third screen needs the catalogue series read-only and, under each stamp, whether
the user owns it. The catalogue is never writable here: the only thing the screen
changes is the user's own copy, and that goes through the item endpoints.
"""

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from collections_api.api.serializers.collection_issue_detail_serializer import (
    CollectionIssueDetailSerializer,
)
from collections_api.models import Collection
from collections_api.services.collection_issue_detail_service import (
    CollectionIssueDetailService,
)
from common.api.messages import Messages
from common.api.serializers.generic_response import (
    GenericResponse,
    GenericResponseSerializer,
)
from common.core.current_user import CurrentUser
from common.core.schemas import standardized_response
from common.log.logger import Logger


class CollectionIssueDetailView(Logger, APIView):
    """Reads one series of the caller's collection, with their copies."""

    serializer_class = CollectionIssueDetailSerializer

    @extend_schema(
        operation_id="get_collection_issue",
        tags=["Collection Management"],
        summary="Read one series of a collection",
        description="Returns the series as the catalogue has it, every stamp with the "
        "caller's `item` or `null`, and the summary of how many are owned. The "
        "catalogue fields are read-only: the user only edits their own copy.",
        responses={
            status.HTTP_200_OK: standardized_response(
                CollectionIssueDetailSerializer,
                name="CollectionIssueRetrieved",
                description="The series was retrieved with the caller's copies.",
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                GenericResponseSerializer,
                name="CollectionIssueDetailForbidden",
                success=False,
                description="Permission denied.",
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="CollectionIssueDetailNotFound",
                success=False,
                description="The collection or the series is not the caller's.",
            ),
        },
    )
    def get(
        self, request: Request, pk: int, issue_pk: int, *args, **kwargs
    ) -> Response:
        """Return the series, its stamps and the summary.

        Args:
            request: the incoming request, with the user's JWT.
            pk: the collection's id.
            issue_pk: the series' id.

        Returns:
            The detail, or a 404 when the collection is not the caller's or holds
            nothing of that series.
        """
        self.log.debug(Messages.Get.retrieve_one("collection issue", issue_pk))
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

        detail = CollectionIssueDetailService().for_collection(collection, issue_pk)
        if detail is None:
            message = Messages.Get.not_found("issue", issue_pk)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            data=CollectionIssueDetailSerializer(detail).data,
            status=status.HTTP_200_OK,
        )
