"""Add a copy of a stamp to one of the caller's collections (plan step B2).

The collection lives in the URL and the body only names the stamp, so the endpoint
cannot be used to write into somebody else's collection. Adding is not editing: a stamp
that is already there answers 409 and keeps the copy the user had.
"""

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from collection_items_api.models import CollectionItem
from collections_api.api.serializers.collection_item_add_serializer import (
    CollectionItemAddSerializer,
)
from collections_api.api.serializers.collection_issue_detail_serializer import (
    CollectionItemDetailSerializer,
)
from collections_api.models import Collection
from common.api.messages import Messages
from common.api.serializers.generic_response import (
    GenericResponse,
    GenericResponseSerializer,
)
from common.core.current_user import CurrentUser
from common.core.schemas import standardized_response
from common.log.logger import Logger
from stamps_api.models import Stamp


class CollectionIssueItemsView(Logger, APIView):
    """Adds the caller's copy of a catalogue stamp to their collection."""

    serializer_class = CollectionItemDetailSerializer

    @extend_schema(
        operation_id="add_collection_item",
        tags=["Collection Management"],
        summary="Add a copy to a collection",
        description="Adds the user's copy of a catalogue stamp to one of their "
        "collections. A stamp already in that collection answers 409: adding does not "
        "overwrite the copy that is there.",
        request=CollectionItemAddSerializer,
        responses={
            status.HTTP_201_CREATED: standardized_response(
                CollectionItemDetailSerializer,
                name="CollectionItemAdded",
                description="The copy was added.",
            ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="CollectionItemAddInvalidPayload",
                success=False,
                description="The payload does not carry a stamp id.",
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                GenericResponseSerializer,
                name="CollectionItemAddForbidden",
                success=False,
                description="Permission denied.",
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="CollectionItemAddNotFound",
                success=False,
                description="The collection is not the caller's or the stamp is "
                "not in the catalogue.",
            ),
            status.HTTP_409_CONFLICT: standardized_response(
                GenericResponseSerializer,
                name="CollectionItemAlreadyThere",
                success=False,
                description="The stamp is already in that collection.",
            ),
        },
    )
    def post(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """Add the copy.

        Args:
            request: the incoming request, with the user's JWT and `{stamp}`.
            pk: the collection's id.

        Returns:
            201 with the new item, or the 400/404/409 of the contract.
        """
        self.log.debug(Messages.Post.create_one("collection item", request.data))
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

        payload = CollectionItemAddSerializer(data=request.data)
        if not payload.is_valid():
            self.log.warning(
                Messages.Post.validation_failed("collection item", payload.errors)
            )
            return Response(
                data=GenericResponseSerializer(GenericResponse(payload.errors)).data,
                status=status.HTTP_400_BAD_REQUEST,
            )

        stamp_id = payload.validated_data["stamp"]
        stamp = Stamp.objects.filter(pk=stamp_id).first()
        if stamp is None:
            message = Messages.Database.not_found("stamp", stamp_id)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND,
            )

        if CollectionItem.objects.filter(collection=collection, stamp=stamp).exists():
            message = Messages.Post.already_exists("collection item", "stamp")
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_409_CONFLICT,
            )

        item = CollectionItem.objects.create(collection=collection, stamp=stamp)
        self.log.info(Messages.Post.created_one("collection item", item.pk))
        return Response(
            data=CollectionItemDetailSerializer(item).data,
            status=status.HTTP_201_CREATED,
        )
