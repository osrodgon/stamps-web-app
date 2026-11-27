"""One series of the catalogue, for a collection that may hold nothing of it (step C2).

The dialog that adds stamps has to show what a series contains before the first copy is
added, and the reading screen's detail refuses exactly that (it answers 404 when the
collection holds nothing of the series). The shape is B2's, without the ownership
precondition: every stamp comes with `item` or `null`.
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


class CollectionCatalogueIssueDetailView(Logger, APIView):
    """Reads one series of the catalogue, with the caller's copies where they exist."""

    serializer_class = CollectionIssueDetailSerializer

    @extend_schema(
        operation_id="get_collection_catalogue_issue",
        tags=["Collection Management"],
        summary="Read one series of the catalogue for a collection",
        description="Returns the series as the catalogue has it — every stamp "
        "with the caller's `item` or `null` — whether the collection holds "
        "something of it or not. The catalogue is read-only: the copies are "
        "written through the item endpoints.",
        responses={
            status.HTTP_200_OK: standardized_response(
                CollectionIssueDetailSerializer,
                name="CollectionCatalogueIssueRetrieved",
                description="The series was retrieved with the caller's copies.",
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                GenericResponseSerializer,
                name="CollectionCatalogueIssueForbidden",
                success=False,
                description="Permission denied.",
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="CollectionCatalogueIssueNotFound",
                success=False,
                description="The collection is not the caller's, or the series does "
                "not exist.",
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
            The detail, or a 404 when the collection is not the caller's or the
            series does not exist.
        """
        self.log.debug(
            Messages.Get.retrieve_one("catalogue issue", issue_pk)
        )
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

        detail = CollectionIssueDetailService().for_collection(
            collection, issue_pk, owned_only=False
        )
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
