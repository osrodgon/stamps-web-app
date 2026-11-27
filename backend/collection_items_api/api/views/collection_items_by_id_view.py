from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.current_user import CurrentUser
from common.core.schemas import standardized_response
from collection_items_api.models import CollectionItem
from collection_items_api.api.serializers.collection_items_response_serializer import CollectionItemsResponseSerializer
from collection_items_api.api.serializers.collection_items_update_serializer import CollectionItemsUpdateSerializer
from users_api.models import UserCollection


class CollectionItemsByIdView(Logger, APIView):
    """Manages API operations for a single CollectionItem instance.

    This view handles the retrieval (GET), update (PUT), and deletion (DELETE)
    of a specific `CollectionItem` object, identified by its primary key (`pk`)
    provided in the URL.

    It uses `CollectionItemsUpdateSerializer` for updates — the six fields of
    "Your copy" and nothing else — and `CollectionItemsResponseSerializer` for the
    outgoing response. Every operation is scoped to the user of the JWT (plan step
    A1): another user's item is reported as missing.
    """
    serializer_class = CollectionItemsResponseSerializer

    def __get_object(self, pk: int, user: UserCollection) -> CollectionItem:
        """Return the caller's collection item with that id, or None.

        Args:
            pk (int): The primary key of the collection item to retrieve.
            user (UserCollection): The user the JWT belongs to.

        Returns:
            CollectionItem: The found item, or None when it does not exist or
                belongs to somebody else.
        """
        try:
            self.log.debug(Messages.Database.querying("collection item", pk))
            return CollectionItem.objects.get(pk=pk, collection__user=user)
        except CollectionItem.DoesNotExist:
            self.log.warning(Messages.Database.not_found("collection item", pk))
            return None

    @extend_schema(
        operation_id="get_collection_item_by_id",
        tags=['Collection Management'],
        summary="Get Collection Item by ID",
        description="Retrieves a single collection item entry by its unique ID. A 404 Not Found response is returned if the item does not exist.",
        responses={
            status.HTTP_200_OK: standardized_response(
                CollectionItemsResponseSerializer,
                name="CollectionItemRetrieved",
                description="The collection item was retrieved successfully."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="CollectionItemNotFound",
                success=False,
                description="The collection item with the specified ID was not found."
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                CollectionItemsResponseSerializer,
                name="CollectionItemRetrieveForbidden",
                success=False,
                description="Permission denied. You're likely missing X-API-Key."
            )
        }
    )
    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """Handles GET requests to retrieve a single collection item.

        Args:
            request (Request): The incoming HTTP request.
            pk (int): The primary key of the collection item to retrieve.

        Returns:
            Response:   A DRF Response object containing the serialized collection
                        item data and a 200 OK status, or a 404 Not Found response.
        """
        self.log.debug(Messages.Get.retrieve_one("collection item", pk))
        collection_item = self.__get_object(pk, CurrentUser(request).get())

        if collection_item is None:
            message = Messages.Get.not_found("collection item", pk)
            self.log.warning(message)
            return Response(data=GenericResponseSerializer(GenericResponse(message)).data, status=status.HTTP_404_NOT_FOUND)

        response = CollectionItemsResponseSerializer(collection_item)
        self.log.debug(Messages.Get.retrieved_one("collection item", pk))
        return Response(data=response.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="update_collection_item",
        tags=['Collection Management'],
        summary="Update a Collection Item",
        description="Updates the caller's collection item identified by its ID. Only the six fields that describe the user's own copy can change: `collection` and `stamp` are refused.",
        request=CollectionItemsUpdateSerializer,
        responses={
            status.HTTP_200_OK: standardized_response(
                CollectionItemsResponseSerializer,
                name="CollectionItemUpdated",
                description="The collection item was updated successfully."
            ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="CollectionItemUpdateInvalidPayload",
                success=False,
                description="The request payload was invalid."
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                CollectionItemsResponseSerializer,
                name="CollectionItemUpdateForbidden",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="CollectionItemUpdateNotFound",
                success=False,
                description="The collection item with the specified ID was not found."
            )
        }
    )
    def put(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """Handles PUT requests to update the caller's collection item.

        The update is partial (`partial=True`), so the form can send only what
        changed, but the fields are the six of "Your copy": everything else is
        refused by the serializer.

        Args:
            request (Request): The incoming HTTP request containing update data.
            pk (int): The primary key of the collection item to update.

        Returns:
            Response:   A DRF Response with the updated item data and 200 OK status,
                        a 404 if not found, or a 400 on validation error.
        """
        self.log.debug(Messages.Put.update_one("collection item", pk, request.data))
        collection_item = self.__get_object(pk, CurrentUser(request).get())

        if collection_item is None:
            message = Messages.Put.not_found("collection item", pk)
            self.log.warning(message)
            return Response(data=GenericResponseSerializer(GenericResponse(message)).data, status=status.HTTP_404_NOT_FOUND)

        serializer = CollectionItemsUpdateSerializer(collection_item, data=request.data, partial=True)
        if serializer.is_valid():
            instance = serializer.save()
            self.log.info(Messages.Put.updated_one("collection item", pk))
            return Response(data=CollectionItemsResponseSerializer(instance).data, status=status.HTTP_200_OK)

        self.log.warning(Messages.Put.validation_failed("collection item", pk, serializer.errors))
        return Response(data=GenericResponseSerializer(GenericResponse(serializer.errors)).data, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        operation_id="delete_collection_item",
        tags=['Collection Management'],
        summary="Delete a Collection Item",
        description="Deletes a collection item entry by its unique ID. A successful deletion returns a 200 OK response.",
        responses={
            status.HTTP_200_OK: standardized_response(
                CollectionItemsResponseSerializer,
                name="CollectionItemDeleted",
                description="The collection item was deleted successfully."
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                CollectionItemsResponseSerializer,
                name="CollectionItemDeleteForbidden",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="CollectionItemDeleteNotFound",
                success=False,
                description="The collection item with the specified ID was not found."
            )
        }
    )
    def delete(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """Handles DELETE requests to remove a collection item.

        Args:
            request (Request): The incoming HTTP request.
            pk (int): The primary key of the collection item to delete.

        Returns:
            Response:   A DRF Response with a success message and 200 OK status,
                        or a 404 Not Found response if the item does not exist.
        """
        self.log.debug(Messages.Delete.delete_one("collection item", pk))
        collection_item = self.__get_object(pk, CurrentUser(request).get())
        if collection_item is None:
            message = Messages.Delete.not_found("collection item", pk)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data, 
                status=status.HTTP_404_NOT_FOUND
            )

        collection_item.delete()
        message = Messages.Delete.deleted_one("collection item", pk)
        self.log.info(message)
        return Response(
            data=GenericResponseSerializer(GenericResponse(message)).data,
            status=status.HTTP_200_OK
            )