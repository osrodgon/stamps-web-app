"""Adding many stamps to one of the caller's collections (plan step C1).

The collection lives in the URL and is scoped by the token, and the body names
the scope. Nothing about the copy can be written here — only that the stamps
belong to the user's collection — because adding is not editing.
"""

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from collections_api.api.serializers.collection_items_bulk_serializer import (
    CollectionItemsBulkResponseSerializer,
    CollectionItemsBulkSerializer,
)
from collections_api.models import Collection
from collections_api.services.collection_items_bulk_service import (
    CollectionItemsBulkService,
)
from common.api.messages import Messages
from common.api.serializers.generic_response import (
    GenericResponse,
    GenericResponseSerializer,
)
from common.core.current_user import CurrentUser
from common.core.schemas import standardized_response
from common.log.logger import Logger


class CollectionItemsBulkView(Logger, APIView):
    """Adds a stamp, a series or a year to one of the caller's collections."""

    serializer_class = CollectionItemsBulkResponseSerializer

    @extend_schema(
        operation_id="add_collection_items_bulk",
        tags=["Collection Management"],
        summary="Add many stamps to a collection",
        description="Adds the stamps of one scope — the ids in the body, a whole "
        "series or every stamp of a year — in one transaction. A stamp already in "
        "the collection is skipped, not refused, and a scope over 500 stamps "
        "answers 400 without writing anything. The copies are created with the "
        "collection and the stamp only.",
        request=CollectionItemsBulkSerializer,
        responses={
            status.HTTP_201_CREATED: standardized_response(
                CollectionItemsBulkResponseSerializer,
                name="CollectionItemsBulkAdded",
                description="The stamps of the scope were added; `skipped` counts the "
                "ones the collection already had.",
            ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="CollectionItemsBulkInvalidPayload",
                success=False,
                description="The scope is unknown, its key is missing, another scope's "
                "key came along, or the scope holds more than 500 stamps.",
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                GenericResponseSerializer,
                name="CollectionItemsBulkForbidden",
                success=False,
                description="Permission denied.",
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="CollectionItemsBulkNotFound",
                success=False,
                description="The collection is not the caller's, or the series or the "
                "year names no stamp of the catalogue.",
            ),
        },
    )
    def post(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """Add the stamps the body's scope names.

        Args:
            request: the incoming request, with the user's JWT and the scope.
            pk: the collection's id.

        Returns:
            201 with `created`, `skipped` and `total`, or the 400/404/403 of the
            contract.
        """
        self.log.debug(Messages.Post.create_one("collection items", request.data))
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

        payload = CollectionItemsBulkSerializer(data=request.data)
        if not payload.is_valid():
            self.log.warning(
                Messages.Post.validation_failed("collection items", payload.errors)
            )
            return Response(
                data=GenericResponseSerializer(GenericResponse(payload.errors)).data,
                status=status.HTTP_400_BAD_REQUEST,
            )

        scope = payload.validated_data["scope"]
        try:
            result = CollectionItemsBulkService().add(
                collection, scope, payload.validated_data
            )
        except CollectionItemsBulkService.NothingFound:
            message = Messages.Post.nothing_matched("collection items", scope)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND,
            )
        except CollectionItemsBulkService.TooMany as error:
            message = Messages.Post.too_many(
                "stamps", error.total, error.limit
            )
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_400_BAD_REQUEST,
            )

        self.log.info(
            Messages.Post.created_many("collection items", result["created"])
        )
        return Response(
            data=CollectionItemsBulkResponseSerializer(result).data,
            status=status.HTTP_201_CREATED,
        )
