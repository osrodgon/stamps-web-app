from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.schemas import standardized_response
from collection_items_api.models import CollectionItem
from collection_items_api.api.serializers.collection_items_response_serializer import CollectionItemsResponseSerializer
from collection_items_api.api.serializers.collection_items_request_serializer import CollectionItemsRequestSerializer


class CollectionItemsByIdView(Logger, APIView):
    serializer_class = CollectionItemsResponseSerializer

    def _get_object(self, pk: int) -> CollectionItem:
        try:
            self.debug(Messages.Database.querying("collection item", pk))
            return CollectionItem.objects.get(pk=pk)
        except CollectionItem.DoesNotExist:
            self.warning(Messages.Database.not_found("collection item", pk))
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
        self.debug(Messages.Get.retrieve_one("collection item", pk))
        collection_item = self._get_object(pk)

        if collection_item is None:
            message = Messages.Get.not_found("collection item", pk)
            self.warning(message)
            return Response(data=GenericResponseSerializer(GenericResponse(message)).data, status=status.HTTP_404_NOT_FOUND)

        response = CollectionItemsResponseSerializer(collection_item)
        self.debug(Messages.Get.retrieved_one("collection item", pk))
        return Response(data=response.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="update_collection_item",
        tags=['Collection Management'],
        summary="Update a Collection Item",
        description="Updates an existing collection item entry identified by its ID. The request body can contain a partial update. A successful update returns the modified collection item object.",
        request=CollectionItemsRequestSerializer,
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
        self.debug(Messages.Put.update_one("collection item", pk, request.data))
        collection_item = self._get_object(pk)

        if collection_item is None:
            message = Messages.Put.not_found("collection item", pk)
            self.warning(message)
            return Response(data=GenericResponseSerializer(GenericResponse(message)).data, status=status.HTTP_404_NOT_FOUND)

        serializer = CollectionItemsRequestSerializer(collection_item, data=request.data, partial=True)
        if serializer.is_valid():
            instance = serializer.save()
            self.info(Messages.Put.updated_one("collection item", pk))
            return Response(data=CollectionItemsResponseSerializer(instance).data, status=status.HTTP_200_OK)

        self.warning(Messages.Put.validation_failed("collection item", pk, serializer.errors))
        return Response(data=GenericResponseSerializer(GenericResponse(serializer.errors)).data, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        operation_id="delete_collection_item",
        tags=['Collection Management'],
        summary="Delete a Collection Item",
        description="Deletes a collection item entry by its unique ID. A successful deletion returns a 204 No Content response.",
        responses={
            status.HTTP_204_NO_CONTENT: standardized_response(
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
        self.debug(Messages.Delete.delete_one("collection item", pk))
        collection_item = self._get_object(pk)
        if collection_item is None:
            message = Messages.Delete.not_found("collection item", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data, 
                status=status.HTTP_404_NOT_FOUND
            )

        collection_item.delete()
        message = Messages.Delete.deleted_one("collection item", pk)
        self.info(message)
        return Response(
            data=GenericResponseSerializer(GenericResponse(message)).data,
            status=status.HTTP_200_OK
            )